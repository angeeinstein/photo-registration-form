# 🔄 Update Guide for Photo Registration Form

## Understanding Your Installation Type

Your installation can be one of two types:

### 1. **Git-based Installation** ✅
- Installed by cloning from a git repository
- Can use `git pull` to get updates
- Best for receiving automatic code updates

### 2. **Manual Installation** 📦
- Installed by copying files directly
- No git repository connection
- Updates require manual file replacement

## Check Your Installation Type

Run this command on your server:

```bash
cd /opt/photo-registration-form
ls -la .git
```

**If you see:** `.git directory` → You have a **Git-based installation**  
**If you see:** `No such file or directory` → You have a **Manual installation**

---

## For Git-Based Installations

### Update Process

1. **Run the install script:**
   ```bash
   cd /opt/photo-registration-form
   sudo ./install.sh
   ```

2. **Select option 1:** "Update installation"

3. **What happens:**
   - ✅ Your `.env` file is preserved
   - ✅ Code is updated via `git pull`
   - ✅ Dependencies are updated
   - ✅ Service is restarted
   - ✅ Database is kept intact

### Troubleshooting Git Updates

**If git pull fails:**

```bash
# Check git status
cd /opt/photo-registration-form
sudo -u www-data git status

# If you have local changes, stash them
sudo -u www-data git stash

# Pull updates
sudo -u www-data git pull

# Reapply your changes if needed
sudo -u www-data git stash pop

# Restart the service
sudo systemctl restart photo-registration
```

---

## For Manual Installations

### Option 1: Convert to Git Installation (Recommended)

This allows automatic updates in the future:

```bash
#!/bin/bash
# Run this script to convert to git installation

# 1. Backup your data
sudo cp /opt/photo-registration-form/.env ~/photo-reg-backup.env
sudo cp /opt/photo-registration-form/registrations.db ~/photo-reg-backup.db

# 2. Stop the service
sudo systemctl stop photo-registration

# 3. Remove old installation (keep nginx and systemd configs)
sudo rm -rf /opt/photo-registration-form

# 4. Clone from your repository
cd /opt
sudo git clone https://github.com/YOUR-USERNAME/photo-registration-form.git
# Or if you forked the original:
sudo git clone https://github.com/angeeinstein/photo-registration-form.git

# 5. Set permissions
sudo chown -R www-data:www-data /opt/photo-registration-form

# 6. Restore your data
sudo cp ~/photo-reg-backup.env /opt/photo-registration-form/.env
sudo cp ~/photo-reg-backup.db /opt/photo-registration-form/registrations.db
sudo chown www-data:www-data /opt/photo-registration-form/.env
sudo chown www-data:www-data /opt/photo-registration-form/registrations.db

# 7. Create virtual environment
cd /opt/photo-registration-form
sudo -u www-data python3 -m venv venv
sudo -u www-data venv/bin/pip install -r requirements.txt

# 8. Start the service
sudo systemctl start photo-registration
sudo systemctl status photo-registration
```

### Option 2: Manual Update

If you want to keep manual installation:

```bash
#!/bin/bash
# Manual update process

# 1. Backup everything
sudo cp /opt/photo-registration-form/.env ~/photo-reg-backup.env
sudo cp /opt/photo-registration-form/registrations.db ~/photo-reg-backup.db

# 2. Stop service
sudo systemctl stop photo-registration

# 3. Download latest version
cd ~
wget https://github.com/angeeinstein/photo-registration-form/archive/refs/heads/main.zip
unzip main.zip

# 4. Backup old installation
sudo mv /opt/photo-registration-form /opt/photo-registration-form.old

# 5. Move new files
sudo mv photo-registration-form-main /opt/photo-registration-form

# 6. Restore your data
sudo cp ~/photo-reg-backup.env /opt/photo-registration-form/.env
sudo cp ~/photo-reg-backup.db /opt/photo-registration-form/registrations.db

# 7. Set permissions
sudo chown -R www-data:www-data /opt/photo-registration-form

# 8. Update dependencies
cd /opt/photo-registration-form
sudo -u www-data python3 -m venv venv
sudo -u www-data venv/bin/pip install -r requirements.txt

# 9. Start service
sudo systemctl start photo-registration

# 10. Verify
sudo systemctl status photo-registration

# 11. If successful, remove old installation
sudo rm -rf /opt/photo-registration-form.old
```

---

## What install.sh Now Does

### For Git Installations:
- ✅ Detects `.git` directory
- ✅ Runs `git pull` to update code
- ✅ Updates dependencies
- ✅ Preserves your `.env` and database
- ✅ Restarts service

### For Manual Installations:
- ⚠️ Detects no `.git` directory
- ⚠️ Shows warning and instructions
- ✅ Still updates Python dependencies if you continue
- ✅ Preserves your `.env` and database
- ✅ Restarts service
- ℹ️ Provides instructions to convert to git

---

## Using install.sh After Fix

The updated `install.sh` now handles both cases gracefully:

```bash
cd /opt/photo-registration-form
sudo ./install.sh
```

**What you'll see:**

### Git Installation:
```
[INFO] Installation detected at: /opt/photo-registration-form
[SUCCESS] Git repository detected - updates available

1) Update installation (dependencies + restart)
```

### Manual Installation:
```
[INFO] Installation detected at: /opt/photo-registration-form
[WARNING] Not a git repository - only dependency updates available

1) Update installation (dependencies + restart)
```

When you select option 1 on manual installation:
```
[WARNING] Not a git repository. Skipping git pull.
[INFO] To enable git updates, install from git repository:
  1. Backup your .env and database
  2. Remove current installation: sudo rm -rf /opt/photo-registration-form
  3. Clone from git: sudo git clone <your-repo-url> /opt/photo-registration-form
  4. Restore .env and database
  5. Run install.sh again

Continue with dependency updates only? (y/n):
```

---

## Recommended Approach

### ✅ Best Practice: Git-Based Installation

**Advantages:**
- Easy updates with `git pull`
- Track changes and history
- Revert to previous versions if needed
- Automatic dependency management

**Setup:**
1. Fork or clone the repository
2. Install from git URL
3. Use `install.sh` for all updates

### 📦 Manual Installation: When to Use

**Use when:**
- No internet access on production server
- Corporate firewall blocks git
- Testing specific snapshot
- Highly controlled environment

---

## Getting Latest Features

This installation now includes:

✅ **Multi-account email system** - Manage multiple SMTP accounts  
✅ **Live dashboard updates** - Real-time registration monitoring  
✅ **Email account dropdowns** - Choose which account to use  
✅ **Simplified settings** - Clean admin interface  
✅ **Cache prevention** - Always load latest CSS  

**To get these features:**
1. Follow update instructions above
2. Restart the service
3. Clear browser cache (Ctrl+Shift+Delete)
4. Reload admin panel

---

## Troubleshooting

### "Git pull failed" Error
**Cause:** Not a git repository  
**Solution:** Follow "Convert to Git Installation" above

### "Permission denied" Error
**Cause:** Wrong file ownership  
**Solution:**
```bash
sudo chown -R www-data:www-data /opt/photo-registration-form
```

### "Service failed to start" Error
**Cause:** Python dependency issue  
**Solution:**
```bash
cd /opt/photo-registration-form
sudo -u www-data venv/bin/pip install -r requirements.txt --upgrade
sudo systemctl restart photo-registration
```

### Database Issues After Update
**Cause:** Schema changes  
**Solution:**
```bash
# Backup first
sudo cp /opt/photo-registration-form/registrations.db ~/backup.db

# Let app recreate tables
cd /opt/photo-registration-form
sudo -u www-data venv/bin/python3 -c "from app import db, app; app.app_context().push(); db.create_all()"

sudo systemctl restart photo-registration
```

---

## Support

- **Documentation:** Check `EMAIL-ACCOUNTS.md`, `EMAIL-SYSTEM.md`
- **GitHub Issues:** https://github.com/angeeinstein/photo-registration-form/issues
- **Logs:** `sudo journalctl -u photo-registration -f`

---

## Quick Reference

### Check installation type:
```bash
cd /opt/photo-registration-form && ls .git
```

### Update (git-based):
```bash
cd /opt/photo-registration-form && sudo ./install.sh
```

### Manual update:
```bash
# See "Option 2: Manual Update" section above
```

### View logs:
```bash
sudo journalctl -u photo-registration -n 50
```

### Restart service:
```bash
sudo systemctl restart photo-registration
```
