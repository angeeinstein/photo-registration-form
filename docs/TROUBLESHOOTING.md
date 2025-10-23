# Troubleshooting: "Registration failed. Please try again" Error

## Quick Fix

Run these commands in order:

```powershell
# 1. Check database status
python diagnose_db.py

# 2. If database has issues, reset it
python fix_db.py

# 3. Start the application
python app.py
```

## Common Causes & Solutions

### 1. Database Not Initialized

**Symptoms:**
- Registration fails immediately
- No specific error in console
- Database file doesn't exist

**Solution:**
```powershell
python fix_db.py
```

### 2. Missing Database Tables

**Symptoms:**
- Database exists but tables are missing
- Error mentions "no such table"

**Solution:**
```powershell
# Reset and recreate tables
python fix_db.py
```

### 3. No Email Account Configured

**Symptoms:**
- Registration works but error occurs
- Log shows "No email account configured"

**Solution:**
1. Login to admin panel (http://localhost:5000/admin/login)
2. Go to "Email Accounts"
3. Click "Add New Account"
4. Configure SMTP settings:
   - Name: "Main Account"
   - SMTP Server: smtp.gmail.com (for Gmail)
   - SMTP Port: 587
   - Username: your-email@gmail.com
   - Password: your-app-password
   - From Email: your-email@gmail.com
   - Enable TLS: ✓
5. Save and set as default

### 4. Database Permission Issues

**Symptoms:**
- Error: "attempt to write a readonly database"
- Database exists but can't write

**Solution (Windows PowerShell):**
```powershell
# Check current permissions
Get-Acl instance\photo_registration.db | Format-List

# Give full permissions to current user
$acl = Get-Acl instance\photo_registration.db
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule($identity, "FullControl", "Allow")
$acl.SetAccessRule($rule)
Set-Acl instance\photo_registration.db $acl
```

### 5. Nested Transaction Error

**Symptoms:**
- Error mentions "SAVEPOINT" or "transaction"
- Intermittent failures

**Solution:**
This has been fixed in the latest code. Update your `app.py`:
- `AdminSettings.get_setting()` now has try/except
- `EmailAccount.get_default()` now has try/except

### 6. .env File Issues

**Symptoms:**
- Application can't find configuration
- SMTP errors

**Solution:**
Check your `.env` file exists and has correct format:

```env
# Required
SECRET_KEY=your-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-password

# Optional (if using env-based email config)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_USE_TLS=true
```

## Detailed Diagnostic Steps

### Step 1: Check Database

```powershell
python diagnose_db.py
```

Expected output:
```
✅ Database file exists
✅ Database is readable
✅ Database is writable
✅ Found 4 tables:
   - registration: X records
   - email_account: X records
   - admin_settings: X records
   - user: X records
```

### Step 2: Check Application Logs

Look for specific errors in the console when you try to register:

```python
# You should see detailed errors now like:
Registration error: <specific error message>
<full traceback>
```

### Step 3: Test Registration Manually

```powershell
# Start app in debug mode
python app.py

# In another terminal, test registration
curl -X POST http://localhost:5000/register `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "first_name=Test&last_name=User&email=test@example.com"
```

### Step 4: Check Email Configuration

1. Login to admin panel
2. Go to "Email Accounts"
3. Verify:
   - ✅ At least one account exists
   - ✅ At least one account is "Active"
   - ✅ One account is marked as "Default"

If no accounts exist:
```
Go to Settings → Check email account selections
Both dropdowns should have accounts to select
```

## Error Messages Decoded

### "Registration failed. Please try again."
**Generic error - check logs for details**

Now shows actual error in response: `Registration failed: <specific reason>`

### "All fields are required"
**Missing first name, last name, or email**

Check your form submission includes all fields.

### "attempt to write a readonly database"
**Database permission issue**

Run the permission fix script (see #4 above).

### "no such table: admin_settings"
**Database not initialized**

Run `python fix_db.py`

### "No email account configured for confirmations"
**No email accounts in database**

Add email account via admin panel.

## Prevention

To prevent this error in the future:

1. **Always run `install.sh` or `install.bat` for initial setup**
2. **Configure at least one email account before testing**
3. **Check database permissions after deployment**
4. **Keep `.env` file in sync with documentation**
5. **Run `python fix_db.py` after code updates that change database schema**

## Still Not Working?

If you've tried all the above and still getting errors:

1. **Check Python version:**
   ```powershell
   python --version  # Should be 3.8+
   ```

2. **Reinstall dependencies:**
   ```powershell
   pip install -r requirements.txt --force-reinstall
   ```

3. **Start fresh:**
   ```powershell
   # Backup current database
   Copy-Item instance\photo_registration.db instance\photo_registration.db.backup

   # Delete and recreate
   Remove-Item instance\photo_registration.db
   python fix_db.py
   ```

4. **Enable detailed logging:**
   
   In `app.py`, add at the top:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

5. **Share the full error:**
   
   Copy the complete error message from console including the traceback.

## Quick Reference Commands

```powershell
# Diagnose issues
python diagnose_db.py

# Fix database
python fix_db.py

# Start app
python app.py

# Check logs (if using systemd/supervisor)
tail -f app.log

# Test email config
# Login to admin → Email Accounts → Test Account
```
