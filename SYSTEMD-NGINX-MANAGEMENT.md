# Install.sh - systemd and Nginx Management Guide

## Overview

**Yes!** The `install.sh` script fully manages both **systemd** and **nginx** configuration, installation, and removal.

## What install.sh Manages

### ✅ systemd Service Management

#### Installation (Fresh Install)
```bash
sudo bash install.sh
# Choose option 1 (Fresh installation)
```

**What it does:**
1. ✅ Copies `photo-registration.service` to `/etc/systemd/system/`
2. ✅ Configures SECRET_KEY in service file
3. ✅ Sets proper User/Group (www-data)
4. ✅ Sets WorkingDirectory to installation path
5. ✅ Configures ExecStart with correct paths
6. ✅ Runs `systemctl daemon-reload`
7. ✅ Runs `systemctl enable photo-registration`
8. ✅ Runs `systemctl start photo-registration`
9. ✅ Verifies service is running

**Service Features Configured:**
- Automatic restart on failure
- Starts after network
- Environment variables
- Log directory creation
- PID file management
- Proper permissions

#### Uninstallation
```bash
sudo bash install.sh
# Choose option 4 (Complete removal)
```

**What it does:**
1. ✅ Runs `systemctl stop photo-registration`
2. ✅ Runs `systemctl disable photo-registration`
3. ✅ Removes `/etc/systemd/system/photo-registration.service`
4. ✅ Runs `systemctl daemon-reload`
5. ✅ Cleans up completely

---

### ✅ Nginx Configuration Management

#### Installation via Settings Menu
```bash
sudo bash install.sh
# Choose option 3 (Configure settings)
# Choose option 1 or 2 (Nginx configuration)
```

**Option 1: Change hostname for Nginx**
1. ✅ Prompts for hostname/domain
2. ✅ Checks if nginx is installed
3. ✅ Offers to install nginx if missing
4. ✅ Installs nginx package (`apt-get install nginx` or `yum install nginx`)
5. ✅ Reads `nginx.conf.template`
6. ✅ Replaces `SERVER_NAME` with your hostname
7. ✅ Saves to `/etc/nginx/sites-available/photo-registration`
8. ✅ Creates symlink in `/etc/nginx/sites-enabled/` (if directory exists)
9. ✅ Runs `nginx -t` to test configuration
10. ✅ Runs `systemctl reload nginx`
11. ✅ Runs `systemctl enable nginx` (if not already enabled)

**Option 2: Install/Update Nginx configuration**
- Same as Option 1, but more explicit about nginx installation

**Nginx Features Configured:**
- Reverse proxy to 127.0.0.1:5000
- Proper proxy headers (Host, X-Real-IP, X-Forwarded-For, X-Forwarded-Proto)
- Access and error log files
- Timeout settings
- SSL/HTTPS template (commented, ready to enable)
- Best practice security settings

#### Uninstallation
```bash
sudo bash install.sh
# Choose option 4 (Complete removal)
```

**What it does:**
1. ✅ Removes `/etc/nginx/sites-available/photo-registration`
2. ✅ Removes `/etc/nginx/sites-enabled/photo-registration`
3. ✅ Runs `systemctl reload nginx` (if nginx is running)
4. ✅ Cleans up completely

**Note:** Nginx package itself is NOT removed (since other sites might be using it)

---

## Complete Lifecycle Management

### Fresh Installation Flow

```
1. User runs: sudo bash install.sh
2. Script creates:
   ├── Application files in /opt/photo-registration-form/
   ├── Python virtual environment
   ├── SQLite database
   ├── .env file with SECRET_KEY
   ├── Log directories
   └── systemd service file
3. systemd service is:
   ├── Configured with proper paths
   ├── Enabled (starts on boot)
   └── Started immediately
4. Service runs Gunicorn on 127.0.0.1:5000
5. User optionally configures nginx via menu
6. Nginx proxies external traffic to Gunicorn
```

### Update Flow

```
1. User runs: sudo bash install.sh → Option 1
2. Script:
   ├── Stops systemd service
   ├── Backs up database
   ├── Pulls latest code
   ├── Updates Python packages
   ├── Restarts systemd service
   └── Nginx config remains unchanged
```

### Nginx Configuration Flow

```
1. User runs: sudo bash install.sh → Option 3 → Option 1
2. Script prompts for hostname
3. Checks if nginx installed
4. Installs nginx if missing:
   ├── apt-get install nginx (Ubuntu/Debian)
   └── yum install nginx (CentOS/RHEL)
5. Creates config from template
6. Enables site
7. Tests config: nginx -t
8. Reloads nginx
9. systemd service (already running) now accessible via nginx
```

### Complete Removal Flow

```
1. User runs: sudo bash install.sh → Option 4
2. User confirms: yes
3. User chooses database backup: y
4. Script:
   ├── Backs up database to ~/
   ├── Stops systemd service
   ├── Disables systemd service
   ├── Removes /etc/systemd/system/photo-registration.service
   ├── Runs systemctl daemon-reload
   ├── Removes nginx config files
   ├── Reloads nginx
   ├── Removes /opt/photo-registration-form/
   ├── Removes /var/log/photo-registration/
   ├── Removes /var/run/photo-registration/
   └── System completely clean
```

---

## Configuration Files Created

### systemd Service File
**Location:** `/etc/systemd/system/photo-registration.service`

**Content:**
```ini
[Unit]
Description=Photo Registration Form Flask Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/photo-registration-form
Environment="PATH=/opt/photo-registration-form/venv/bin"
Environment="SECRET_KEY=<auto-generated>"
ExecStartPre=/bin/mkdir -p /var/log/photo-registration
ExecStartPre=/bin/mkdir -p /var/run/photo-registration
ExecStartPre=/bin/chown www-data:www-data /var/log/photo-registration
ExecStartPre=/bin/chown www-data:www-data /var/run/photo-registration
ExecStart=/opt/photo-registration-form/venv/bin/gunicorn --config gunicorn_config.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Nginx Configuration File
**Location:** `/etc/nginx/sites-available/photo-registration`

**Content:**
```nginx
server {
    listen 80;
    server_name your-hostname.com;  # Set by install.sh

    access_log /var/log/nginx/photo-registration-access.log;
    error_log /var/log/nginx/photo-registration-error.log;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

---

## Command Reference

### systemd Commands (Managed by install.sh)

```bash
# These are automated by install.sh:
systemctl start photo-registration      # Start service
systemctl stop photo-registration       # Stop service
systemctl restart photo-registration    # Restart service
systemctl enable photo-registration     # Enable on boot
systemctl disable photo-registration    # Disable on boot
systemctl status photo-registration     # Check status
systemctl daemon-reload                 # Reload after changes
journalctl -u photo-registration -f     # View logs

# All of these are handled automatically during install/uninstall
```

### Nginx Commands (Managed by install.sh)

```bash
# These are automated by install.sh:
nginx -t                                # Test configuration
systemctl reload nginx                  # Reload config
systemctl start nginx                   # Start nginx
systemctl enable nginx                  # Enable on boot
systemctl status nginx                  # Check status

# All of these are handled automatically during nginx setup/removal
```

---

## Manual Verification

After installation, verify everything:

```bash
# Check systemd service
sudo systemctl status photo-registration
# Should show: active (running)

# Check if enabled
sudo systemctl is-enabled photo-registration
# Should show: enabled

# Check nginx config (if configured)
sudo nginx -t
# Should show: configuration file ... syntax is ok

# Check nginx status (if configured)
sudo systemctl status nginx
# Should show: active (running)

# Test the application
curl http://localhost:5000/health
# Should return: {"status":"healthy","timestamp":"..."}

# If nginx configured, test via hostname
curl http://your-hostname.com/health
```

---

## Troubleshooting

### systemd Service Won't Start

```bash
# Check logs
sudo journalctl -u photo-registration -n 50

# Common issues:
# - Python path wrong: Check WorkingDirectory in service file
# - Permissions: Check /opt/photo-registration-form ownership
# - Port in use: Check if port 5000 is available

# Reinstall systemd service
sudo bash install.sh
# Choose option 2 (Reinstall)
```

### Nginx Configuration Issues

```bash
# Test configuration
sudo nginx -t

# Common issues:
# - Syntax error: Check /etc/nginx/sites-available/photo-registration
# - Port conflict: Check if port 80 is available
# - Service not running: Check Flask service is on 5000

# Reconfigure nginx
sudo bash install.sh
# Choose option 3 → Configure settings
# Choose option 2 → Install/Update Nginx configuration
```

---

## Summary

**The install.sh script provides complete lifecycle management:**

| Action | systemd | Nginx | Database | App Files |
|--------|---------|-------|----------|-----------|
| **Fresh Install** | ✅ Creates & enables | ⚙️ Optional setup | ✅ Initializes | ✅ Installs |
| **Update** | ✅ Restarts | ⚙️ Preserves | ✅ Backs up | ✅ Updates |
| **Configure** | ⚙️ Manages | ✅ Full setup | ⚙️ Preserves | ⚙️ Preserves |
| **Uninstall** | ✅ Removes & disables | ✅ Removes config | ⚙️ Optional backup | ✅ Removes |

**Legend:**
- ✅ Automatically handled
- ⚙️ User choice or preserved

---

**You don't need to manually configure systemd or nginx!**  
The `install.sh` script handles everything automatically with smart defaults and interactive prompts.

---

**Last Updated:** October 21, 2025
