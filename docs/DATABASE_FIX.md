# Database Not Created - Fix Instructions

## The Problem

After running `install.sh`, the database file `instance/photo_registration.db` was not created, causing registration failures.

## Quick Fix (Run on your Proxmox server)

```bash
# 1. Pull the latest changes
cd /root/photo-registration-form  # or wherever you cloned the repo
git pull

# 2. Run the quick fix script
chmod +x quickfix_db.sh
./quickfix_db.sh
```

That's it! The script will:
- Create the `instance` directory
- Initialize the database
- Set proper permissions
- Restart the service
- Verify everything works

## Manual Fix (if needed)

If the quick fix doesn't work, do this manually:

```bash
cd /opt/photo-registration-form  # or your installation directory

# Create instance directory
mkdir -p instance
chown www-data:www-data instance

# Activate virtual environment and initialize database
source venv/bin/activate
python3 init_database.py
deactivate

# Verify database was created
ls -lh instance/photo_registration.db

# Set permissions
chown www-data:www-data instance/photo_registration.db
chmod 644 instance/photo_registration.db

# Restart service
systemctl restart photo-registration

# Check status
systemctl status photo-registration
```

## What Was Fixed

### 1. Updated `install.sh`
- Now creates `instance` directory **before** database initialization
- Better error handling for database creation
- Uses proper Flask app context for initialization
- Verifies database exists after installation

### 2. Created `init_database.py`
- Standalone script to initialize the database
- Used by systemd service before starting Gunicorn
- Provides clear success/error messages

### 3. Updated `photo-registration.service`
- Added `ExecStartPre` to create `instance` directory
- Runs `init_database.py` before starting Gunicorn
- Ensures database exists before app starts

### 4. Improved error handling in `app.py`
- `AdminSettings.get_setting()` won't crash if table missing
- `EmailAccount.get_default()` returns None gracefully
- Better error messages in registration route

## Verify It's Working

```bash
# 1. Check database exists
ls -lh /opt/photo-registration-form/instance/photo_registration.db

# 2. Check service is running
systemctl status photo-registration

# 3. Check for errors in logs
journalctl -u photo-registration -n 50

# 4. Test the application
curl http://localhost:5000/health
```

## For New Installations

The fix is now in `install.sh`, so new installations will work correctly:

```bash
# Fresh installation will now work properly
sudo ./install.sh
```

The installer will:
1. Create the `instance` directory
2. Initialize the database with proper context
3. Verify database was created
4. Start the service with database initialization

## Troubleshooting

### Database still not created?

Check directory permissions:
```bash
ls -ld /opt/photo-registration-form/instance
# Should show: drwxr-xr-x www-data www-data
```

### Service won't start?

Check the logs:
```bash
journalctl -u photo-registration -n 100 --no-pager
```

Look for errors in the database initialization section.

### Registration still fails?

1. **Check if database has tables:**
   ```bash
   cd /opt/photo-registration-form
   source venv/bin/activate
   python3 diagnose_db.py
   deactivate
   ```

2. **Check email accounts:**
   - Login to admin panel
   - Go to "Email Accounts"
   - Add at least one email account
   - Set it as active and default

## Prevention

This issue is now fixed in the codebase. Future steps:

1. ✅ Database is created during installation
2. ✅ Database is verified before service starts
3. ✅ Service recreates database if missing
4. ✅ Better error messages if something fails

## Need Help?

If you're still having issues:

1. Run the diagnostic:
   ```bash
   cd /opt/photo-registration-form
   source venv/bin/activate
   python3 diagnose_db.py
   deactivate
   ```

2. Share the output along with:
   ```bash
   systemctl status photo-registration
   journalctl -u photo-registration -n 100
   ```
