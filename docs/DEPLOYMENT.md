# Deployment Guide - Fix 1MB Upload Limit

## Problem
✗ Uploads under 1MB work fine  
✗ Uploads over 1MB fail immediately  
✗ Empty batches are created when all uploads fail  

**Root Cause:** Nginx default `client_max_body_size` is 1MB

## Solution: 3-Step Fix

### Step 1: Update Application Code (Pull from Git)
```bash
# On your server
cd /opt/photo-registration-form
git pull
chmod +x *.sh

# Deploy the updated app
sudo ./deploy.sh
```

**What this fixes:**
- ✅ Service startup issues
- ✅ Empty batch creation (now returns error if 0 photos uploaded)
- ✅ Better error messages

### Step 2: Check Current Nginx Configuration
```bash
# Run the checker script
sudo ./check-nginx.sh
```

This will show you:
- Where your nginx config files are
- Current `client_max_body_size` setting (probably 1MB or missing)
- What settings need to be added

### Step 3: Update Nginx Configuration

#### Find Your Config File:
```bash
# Usually one of these:
ls -la /etc/nginx/sites-available/
ls -la /etc/nginx/conf.d/

# Common locations:
# - /etc/nginx/sites-available/default
# - /etc/nginx/sites-available/photo-registration
# - /etc/nginx/conf.d/photo-registration.conf
```

#### Edit the Config:
```bash
# Replace with your actual config file path
sudo nano /etc/nginx/sites-available/YOUR_CONFIG_FILE
```

#### Add These Settings:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # ⭐ ADD THESE LINES - Allow large file uploads
    client_max_body_size 100M;
    client_body_timeout 300s;
    client_header_timeout 300s;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # ⭐ ADD THESE LINES - Increased timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
```

#### Test and Apply:
```bash
# Test configuration (MUST show "syntax is ok")
sudo nginx -t

# If test passes, reload nginx
sudo systemctl reload nginx

# Check nginx status
sudo systemctl status nginx
```

### Step 4: Test Uploads

1. **Go to your admin panel**
2. **Try uploading files in this order:**
   - ✓ 0.5 MB file (should work as before)
   - ✓ 1.5 MB file (should now work!)
   - ✓ 5 MB file (should work!)
   - ✓ 10 MB file (should work!)

3. **Monitor logs while testing:**
```bash
# Terminal 1: Application logs
journalctl -u photo-registration -f

# Terminal 2: Nginx error log
sudo tail -f /var/log/nginx/error.log
```

## What Changed

### 1. Application (`app.py`)
```python
# Now checks if any photos uploaded successfully
if actual_count == 0:
    return jsonify({
        'success': False,
        'error': 'No photos were successfully uploaded. Check server file size limits.'
    }), 400
```

### 2. Nginx Configuration (YOU NEED TO ADD)
```nginx
# Before (DEFAULT):
# client_max_body_size 1m;  # Only 1MB allowed!

# After (REQUIRED):
client_max_body_size 100M;    # Allow up to 100MB
proxy_read_timeout 300s;      # 5 minute timeout
proxy_buffering off;          # Stream large files
```

## Troubleshooting

### Still getting 1MB limit?
```bash
# Check what nginx is actually using
sudo nginx -T | grep client_max_body_size

# If it shows "1m", you edited the wrong file or didn't reload
sudo systemctl reload nginx

# Check nginx error log for details
sudo tail -50 /var/log/nginx/error.log
```

### Uploads still fail?
```bash
# Check if it's hitting Flask limit (should be 100MB)
grep MAX_CONTENT_LENGTH /opt/photo-registration-form/app.py

# Check gunicorn timeout (should be 300s)
grep timeout /opt/photo-registration-form/gunicorn_config.py

# Restart everything
sudo systemctl restart photo-registration
sudo systemctl reload nginx
```

### Empty batches still being created?
```bash
# Make sure you pulled the latest code
cd /opt/photo-registration-form
git log -1 --oneline
# Should show recent commit about batch upload validation

# If not, pull again
git pull
sudo ./deploy.sh
```

## Expected Results After Fix

✅ Files under 1MB: Work (fast)  
✅ Files over 1MB: Now work!  
✅ Files up to 10MB: Work  
✅ Files up to 50MB: Work (with Flask limit)  
✅ Empty batches: Prevented, show error message  
✅ Upload speed: Fast (no buffering)  

## Quick Reference

```bash
# Update app
cd /opt/photo-registration-form && git pull && sudo ./deploy.sh

# Check nginx config
sudo ./check-nginx.sh

# Edit nginx (find your config file first)
sudo nano /etc/nginx/sites-available/YOUR_CONFIG

# Apply nginx changes
sudo nginx -t && sudo systemctl reload nginx

# Monitor logs
journalctl -u photo-registration -f
```

## The Key Setting You Need

**This is what fixes the 1MB limit:**

```nginx
client_max_body_size 100M;
```

Add it to your nginx server block, test with `nginx -t`, reload with `systemctl reload nginx`, done!
