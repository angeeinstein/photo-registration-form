# Database Concurrency Fix

## Problem
When processing large photo batches (350+ photos), the system experienced "database is locked" errors. This occurred when:
- Multiple gunicorn workers were running
- Photo processor (background thread) was writing to database
- Dashboard polling endpoints were trying to read from database concurrently
- SQLite's single-writer limitation was being hit

## Root Cause
SQLite by default uses rollback journal mode, which blocks all readers when a writer has the database locked. With multiple gunicorn workers and frequent dashboard polling (every 5 seconds), concurrent access caused lock contention.

## Solution Implemented

### 1. **SQLite WAL Mode** (`app.py`)
Enabled Write-Ahead Logging (WAL) mode for SQLite:
- Allows concurrent readers while a writer is active
- Writers don't block readers (except during checkpointing)
- Significantly improves concurrent access performance

```python
@app.before_request
def _db_enable_wal():
    """Enable WAL mode on SQLite database for better concurrent access"""
    if database_uri.startswith('sqlite:'):
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text('PRAGMA journal_mode=WAL'))
                conn.execute(db.text('PRAGMA busy_timeout=30000'))  # 30 second timeout
                conn.commit()
        except Exception as e:
            app.logger.warning(f"Could not enable WAL mode: {e}")
    # Only run once
    app.before_request_funcs[None].remove(_db_enable_wal)
```

### 2. **Connection Pool Configuration** (`app.py`)
Enhanced SQLAlchemy engine options:
```python
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'connect_args': {
        'timeout': 30,  # 30 second timeout for lock acquisition
        'check_same_thread': False  # Allow SQLite across threads
    }
}
```

### 3. **Retry Decorator for Routes** (`app.py`)
Added `@db_retry` decorator to critical read endpoints:
- `get_registration_updates()` - Dashboard live polling
- `admin_dashboard()` - Dashboard page load
- `get_processing_status()` - Photo processing status polling

The decorator automatically retries database operations with exponential backoff:
```python
@db_retry(max_attempts=3, delay=0.3)
def get_registration_updates():
    # ... endpoint code ...
```

### 4. **Retry Helper for Photo Processor** (`photo_processor.py`)
Created `db_commit_with_retry()` function for all database commits during photo processing:
- 5 retry attempts with exponential backoff (0.5s, 1s, 2s, 4s, 8s)
- Automatic rollback on failure
- Detailed logging of retry attempts

All `db.session.commit()` calls replaced with `db_commit_with_retry()` in:
- `_log_action()` - Processing log entries
- `_update_batch_status()` - Batch status updates
- `_save_current_person()` - Photo copying and metadata
- `_start_new_person()` - QR code detection
- `_assign_to_current_person()` - Photo assignment
- Drive upload operations

## Benefits

1. **Better Concurrency**: WAL mode allows multiple readers while photo processing writes
2. **Automatic Recovery**: Retry logic handles transient lock contention
3. **No User Impact**: Dashboard polling continues smoothly during processing
4. **Graceful Degradation**: Exponential backoff prevents thundering herd
5. **Better Logging**: Retry attempts are logged for monitoring

## Testing Recommendations

1. Test with large batch (350+ photos)
2. Monitor for "Database locked, retrying" messages in logs
3. Verify dashboard polling remains responsive during processing
4. Check that no errors occur during concurrent operations

## Migration to PostgreSQL (Future)

If you need to scale beyond SQLite's capabilities, consider migrating to PostgreSQL:
- No single-writer limitation
- Better concurrent access performance
- More robust transaction handling
- Simple migration with SQLAlchemy

For now, these fixes should handle your production workload effectively.

## Files Modified

- `app.py`:
  - Added WAL mode initialization
  - Enhanced database connection configuration
  - Added `@db_retry` decorator
  - Applied decorator to polling endpoints

- `photo_processor.py`:
  - Added `db_commit_with_retry()` function
  - Replaced all `db.session.commit()` calls
  - Added proper error handling and logging

## Expected Behavior

With these changes:
- ✅ Photo processing runs smoothly without blocking dashboard
- ✅ Dashboard polling continues without errors
- ✅ Large batches (675 photos) process without database locks
- ✅ Multiple gunicorn workers coexist peacefully
- ✅ Automatic retry handles any remaining contention
