# Deployment Guide - Fix Large File Upload Issues

## Problem Summary
- Service file has old `ExecStartPre` lines causing startup failures
- Nginx timeouts are too short (60s) for large file uploads
- Need to ensure all configuration is properly deployed

## Solution: Deploy Updated Configuration

### Step 1: Upload Files to Server
```bash
# From your local machine (PowerShell), upload the updated files:
scp photo-registration.service root@YOUR_SERVER:/opt/photo-registration-form/
scp nginx.conf.template root@YOUR_SERVER:/opt/photo-registration-form/
scp deploy.sh root@YOUR_SERVER:/opt/photo-registration-form/
```

### Step 2: On the Server, Run Deployment Script
```bash
# SSH into your server
ssh root@YOUR_SERVER

# Navigate to the app directory
cd /opt/photo-registration-form

# Make the deploy script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

### Step 3: Update Nginx Configuration
```bash
# Find your nginx site config file (it might be in /etc/nginx/sites-available/)
# Let's check what you have:
ls -la /etc/nginx/sites-available/
ls -la /etc/nginx/sites-enabled/

# Once you find your config file, update it with the new settings:
# Option A: If you have a specific site config file
nano /etc/nginx/sites-available/photo-registration

# Or Option B: If it's in the main nginx.conf
nano /etc/nginx/nginx.conf

# Add these settings to the server block:
#   client_max_body_size 100M;
#   client_body_timeout 300s;
#   client_header_timeout 300s;
#   
#   And in the location / block:
#   proxy_connect_timeout 300s;
#   proxy_send_timeout 300s;
#   proxy_read_timeout 300s;
#   proxy_buffering off;
#   proxy_request_buffering off;

# Test nginx configuration
nginx -t

# If test passes, reload nginx
systemctl reload nginx
```

### Step 4: Verify Service is Running
```bash
# Check service status
systemctl status photo-registration

# Monitor logs in real-time
journalctl -u photo-registration -f
```

### Step 5: Test Large File Upload
1. Open your browser to the admin panel
2. Try uploading a 7.7MB file
3. Watch the logs in another terminal: `journalctl -u photo-registration -f`
4. Also check nginx logs: `tail -f /var/log/nginx/photo-registration-error.log`

## What Changed

### 1. Service File (`photo-registration.service`)
- ✅ Uses `RuntimeDirectory=photo-registration` (systemd creates /var/run/photo-registration)
- ✅ Removed the failing `ExecStartPre=/bin/mkdir -p /var/run/photo-registration`
- ✅ Only creates directories that systemd won't create automatically

### 2. Nginx Configuration
- ✅ `client_max_body_size 100M` - allows files up to 100MB
- ✅ `client_body_timeout 300s` - 5 minutes to receive the entire upload
- ✅ `proxy_read_timeout 300s` - 5 minutes for the backend to process
- ✅ `proxy_buffering off` - streams large uploads instead of buffering

### 3. Gunicorn Configuration (already updated)
- ✅ `timeout = 300` - 5 minutes for request processing
- ✅ `worker_class = 'sync'` - stable for file uploads
- ✅ `pidfile` uses proper path

### 4. Flask Configuration (already updated in app.py)
- ✅ `MAX_CONTENT_LENGTH = 100 * 1024 * 1024` - 100MB limit

## Troubleshooting

### If service still won't start:
```bash
# Check full error details
journalctl -u photo-registration -n 100 --no-pager

# Check if directories exist
ls -la /var/run/ | grep photo-registration
ls -la /var/log/ | grep photo-registration
ls -la /opt/photo-registration-form/instance/

# Manually test the app
cd /opt/photo-registration-form
sudo -u www-data /opt/photo-registration-form/venv/bin/gunicorn --config gunicorn_config.py app:app
```

### If uploads still hang:
```bash
# Monitor all logs simultaneously:
# Terminal 1: Application logs
journalctl -u photo-registration -f

# Terminal 2: Nginx error log
tail -f /var/log/nginx/photo-registration-error.log

# Terminal 3: Nginx access log
tail -f /var/log/nginx/photo-registration-access.log

# Check system resources during upload
htop
# or
top
```

### Check for disk space:
```bash
df -h
```

### Check for memory issues:
```bash
free -h
```

## Expected Behavior After Fix
- Service should start cleanly without mkdir errors
- 7.7MB file upload should complete in under 1 minute
- No timeouts in nginx or gunicorn logs
- Photos should appear in the upload folder and Google Drive
