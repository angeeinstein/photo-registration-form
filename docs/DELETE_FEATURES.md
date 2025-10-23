# Database Permission Issue & Delete Features

## Issues Fixed

### 1. SQLite Read-Only Database Error

**Problem:** 
```
sqlite3.OperationalError: attempt to write a readonly database
```

**Causes:**
- Database file permissions are read-only
- Database file doesn't exist yet and can't be created
- Parent directory doesn't have write permissions
- File is opened by another process with exclusive lock

**Solutions Implemented:**

1. **Improved `init_db()` function** - Added checks for:
   - Database directory creation
   - Write permission verification
   - Better error messages

2. **Test script created** - `test_db.py` to diagnose permission issues

**How to Fix:**

```powershell
# Option 1: If database exists but is read-only
attrib -r registrations.db

# Option 2: Delete and recreate (WARNING: This deletes all data!)
Remove-Item registrations.db -Force
python test_db.py

# Option 3: Check directory permissions
Get-Acl . | Format-List
```

---

## New Features Added

### 1. Delete Individual Registration

**Location:** Admin Dashboard → Actions column

**Features:**
- 🗑️ Delete button for each registration
- Confirmation dialog before deletion
- Shows which registration will be deleted (name)
- Flash message confirmation after deletion

**Usage:**
1. Find the registration in the table
2. Click the 🗑️ Delete button
3. Confirm the deletion
4. Registration is permanently removed

---

### 2. Delete All Registrations (Bulk Delete)

**Location:** Admin Dashboard → Bottom of page (Danger Zone)

**Features:**
- ⚠️ Clear warning section with red border
- **Two-step confirmation process:**
  1. Must type "DELETE ALL" exactly
  2. Secondary confirmation dialog with count
- Shows total number of registrations to be deleted
- Cannot be undone warning

**Usage:**
1. Scroll to bottom of dashboard
2. Find the "Danger Zone" section (red border)
3. Type "DELETE ALL" in the text field (exactly, case-sensitive)
4. Click "🗑️ Delete All Registrations"
5. Confirm in the dialog that shows the total count
6. All registrations are permanently deleted

**Safety Features:**
- Must type exact text: "DELETE ALL"
- Shows warning about permanent deletion
- Displays total count before confirming
- Two confirmation steps prevent accidents
- Cannot be triggered accidentally

---

## Routes Added

### `POST /admin/delete-registration/<id>`
Deletes a single registration by ID.

**Parameters:**
- `registration_id`: ID of the registration to delete

**Response:**
- Success: Flash message and redirect to dashboard
- Error: Error message and redirect to dashboard

### `POST /admin/delete-all-registrations`
Deletes all registrations (requires confirmation).

**Parameters:**
- `confirm`: Must be exactly "DELETE ALL"

**Response:**
- Success: Flash message with count and redirect
- Error: Flash message if confirmation doesn't match

---

## Testing

### Test Database Permissions

```powershell
python test_db.py
```

This will:
- Check if database exists
- Verify write permissions
- Test database initialization
- Show detailed error messages if issues found

### Test Delete Features

1. **Test Single Delete:**
   - Create a test registration
   - Click delete button
   - Cancel confirmation → registration remains
   - Click delete again → confirm → registration deleted

2. **Test Bulk Delete:**
   - Create multiple registrations
   - Type wrong text → shows error
   - Type "DELETE ALL" → click button
   - Cancel confirmation → nothing deleted
   - Try again → confirm → all deleted

---

## Database Backup Recommendation

Before using delete features on production data:

```powershell
# Backup database
Copy-Item registrations.db registrations.db.backup

# If you need to restore
Copy-Item registrations.db.backup registrations.db -Force
```

---

## Usage Scenario: After Fair Completion

**Typical Workflow:**

1. **During Fair:**
   - Collect registrations
   - Send photos to participants

2. **After Fair Ends:**
   - Verify all photos have been sent
   - Download/backup database for records
   ```powershell
   Copy-Item registrations.db "backups/fair-2025-10-21.db"
   ```

3. **Clean Up for Next Fair:**
   - Go to Admin Dashboard
   - Scroll to "Danger Zone"
   - Type "DELETE ALL"
   - Confirm deletion
   - Database is now empty and ready for next fair

4. **Verify:**
   - Check dashboard shows 0 registrations
   - Ready for next event!

---

## Email Account Settings

**New Feature:** Select default email accounts for different purposes

**Location:** Admin → Settings

**Options:**
1. **Confirmation Emails Account:** Used for automatic confirmation emails
2. **Photo Emails Account:** Default account for sending photos

**How It Works:**
- Select account from dropdown (shows all active accounts)
- Choose "Use System Default" to use the default marked account
- Settings are stored in database
- Can still override on dashboard when sending individual emails

**Priority Order:**
1. Manually selected account (on dashboard)
2. Account selected in settings
3. System default account (marked with ★)
4. First active account

---

## Troubleshooting

### "readonly database" error

1. Check file exists and permissions:
```powershell
Get-ChildItem registrations.db | Select-Object Name, IsReadOnly
```

2. Remove read-only attribute:
```powershell
attrib -r registrations.db
```

3. Check directory permissions:
```powershell
Get-Acl . | Format-List
```

### Delete button doesn't work

- Check JavaScript console for errors (F12)
- Verify route is registered in `app.py`
- Check that form submission isn't blocked

### Confirmation dialog not showing

- Check browser console for JavaScript errors
- Verify `confirmDeleteAll()` function is defined
- Make sure script tag is closed properly

---

## Code Changes Summary

### `app.py`
- Fixed duplicate `init_db()` function
- Added database directory and permission checks
- Added route: `admin_delete_registration()`
- Added route: `admin_delete_all_registrations()`
- Updated settings to include email account selection
- Updated email sending to use default accounts from settings

### `admin_dashboard.html`
- Added delete button to each registration row
- Added "Danger Zone" section for bulk delete
- Added `confirmDeleteAll()` JavaScript function
- Updated `createTableRow()` to include delete button for live updates
- Added `.btn-danger` CSS class

### `admin_settings.html`
- Added email account dropdowns
- Shows confirmation and photos account selection
- Displays account names with email addresses
- Shows default indicator (★)

### `test_db.py` (new file)
- Database permission testing script
- Checks file existence and write access
- Tests database initialization
- Provides helpful error messages

---

## Security Notes

⚠️ **Important Security Considerations:**

1. **No Undo:** Deleted registrations cannot be recovered (unless you have backups)
2. **Login Required:** All admin routes require authentication
3. **Confirmation Required:** Delete all requires exact text match
4. **Two-Step Process:** Both text input AND dialog confirmation needed
5. **Audit Log:** Consider adding logging for deletions (future enhancement)

---

## Future Enhancements

Possible improvements:

1. **Soft Delete:** Mark as deleted instead of permanent removal
2. **Audit Log:** Track who deleted what and when
3. **Export Before Delete:** Automatically backup before bulk delete
4. **Recycle Bin:** Temporarily store deleted items for recovery
5. **Scheduled Cleanup:** Auto-delete after certain time period
6. **Bulk Operations:** Select specific registrations to delete

---

## Questions?

If you encounter any issues:

1. Run `python test_db.py` to diagnose database problems
2. Check file permissions with PowerShell commands above
3. Look at Flask error logs
4. Check browser console (F12) for JavaScript errors
