# 🔧 Fixing Your Current Nginx Port 80 Conflict

## Your Situation

You ran the old version of `install.sh` and now have:
- ✅ Flask app installed and running
- ✅ Nginx installed
- ❌ Nginx failing to start with error: **"Port 80 is already in use"**

## Problem Analysis

Based on your logs:
```
Not attempting to start NGINX, port 80 is already in use.
nginx.service is not active, cannot reload.
Job for nginx.service failed because the control process exited with error code.
```

Something else is using port 80. Let's find out what and fix it.

## 🔍 Step 1: Find What's Using Port 80

Run these commands:

```bash
# Check what's using port 80
sudo ss -tulpn | grep :80
# OR
sudo netstat -tulpn | grep :80
```

**Likely causes:**

### Cause A: Your Flask App is Bound to 0.0.0.0:80
If you see something like:
```
tcp   LISTEN 0   511   0.0.0.0:80   0.0.0.0:*   users:(("gunicorn",pid=1234))
```

**This means:** Your Flask app is bound to port 80 instead of port 5000.

**Solution:** Change Flask binding to localhost:5000

### Cause B: Another Web Server (Apache, etc.)
If you see:
```
tcp   LISTEN 0   511   0.0.0.0:80   0.0.0.0:*   users:(("apache2",pid=5678))
```

**This means:** Apache (or another web server) is running.

**Solution:** Stop the other web server

### Cause C: Old Nginx Configuration
If you see:
```
tcp   LISTEN 0   511   0.0.0.0:80   0.0.0.0:*   users:(("nginx",pid=9012))
```

**This means:** Nginx is actually running (ignore the error message).

**Solution:** Just reload Nginx configuration

## 🛠️ Step 2: Fix Based on Cause

### Fix for Cause A: Flask on Port 80

**Option 1: Use the new install script (Recommended)**

```bash
cd /root/photo-registration-form  # Or wherever you cloned it
git pull
sudo bash install.sh
# Choose: 3) Configure settings
# Choose: 1) Configure network binding
# Choose: 1) Local access only (localhost)
```

**Option 2: Manual fix**

```bash
# Edit .env file
sudo nano /opt/photo-registration-form/.env

# Change this line to:
GUNICORN_BIND=127.0.0.1:5000

# Save and exit (Ctrl+X, Y, Enter)

# Restart Flask service
sudo systemctl restart photo-registration

# Verify Flask is now on port 5000
sudo ss -tulpn | grep :5000
```

### Fix for Cause B: Apache (or other web server)

```bash
# Stop Apache
sudo systemctl stop apache2
# OR for RHEL/CentOS
sudo systemctl stop httpd

# Disable Apache from starting on boot
sudo systemctl disable apache2
# OR
sudo systemctl disable httpd

# Now start Nginx
sudo systemctl start nginx
```

### Fix for Cause C: Nginx Already Running

```bash
# Nginx is actually running, just reload config
sudo nginx -t  # Test configuration
sudo systemctl reload nginx

# Check status
sudo systemctl status nginx
```

## 🎯 Step 3: Configure Nginx for Your Flask App

Once port 80 is available and Flask is on localhost:5000:

```bash
cd /root/photo-registration-form  # Or wherever you cloned it
git pull  # Get latest version with wizard
sudo bash install.sh
```

Choose:
- **3)** Configure settings
- **2)** Change hostname for Nginx
- Enter your hostname: `photo-form.angeeinstein.stream`

The script will:
1. ✅ Check if Flask is bound to localhost
2. ✅ Create Nginx configuration
3. ✅ Test the configuration
4. ✅ Start/reload Nginx
5. ✅ Verify it's working

## 🧪 Step 4: Verify Everything Works

```bash
# Check Flask service
sudo systemctl status photo-registration

# Check Nginx service
sudo systemctl status nginx

# Test Flask directly
curl http://127.0.0.1:5000/health

# Test through Nginx
curl http://photo-form.angeeinstein.stream/health
# OR if DNS not set up yet
curl -H "Host: photo-form.angeeinstein.stream" http://localhost/health
```

## 📊 Expected Final State

```
[Flask Service]
- Binding: 127.0.0.1:5000
- Status: Active (running)
- Accessible from: localhost only

        ↓ (proxies to)

[Nginx Service]
- Listening: Port 80
- Status: Active (running)
- Proxies to: 127.0.0.1:5000
- Accessible from: All network interfaces

        ↓

[Users]
- Access via: http://photo-form.angeeinstein.stream
```

## 🚨 Quick Reset Option

If things are really messed up, you can reset everything:

```bash
# Stop all services
sudo systemctl stop photo-registration
sudo systemctl stop nginx

# Remove configurations
sudo rm -f /etc/nginx/sites-enabled/photo-registration
sudo rm -f /etc/nginx/sites-available/photo-registration

# Get latest code
cd /root/photo-registration-form
git pull

# Reconfigure
sudo bash install.sh
# Choose: 3) Configure settings
# Choose: 1) Configure network binding → Option 1 (localhost)
# Choose: 2) Change hostname for Nginx → Enter your hostname
```

## 🎓 Understanding the Setup

### Why Flask Should Bind to Localhost When Using Nginx

```
WITHOUT Nginx:
Internet/LAN → [Flask on 0.0.0.0:5000]
Problem: Flask directly exposed, no SSL, must specify port

WITH Nginx (Correct):
Internet/LAN → [Nginx on 0.0.0.0:80] → [Flask on 127.0.0.1:5000]
Benefits: SSL, port 80, caching, security
```

### Your Nginx Configuration

Location: `/etc/nginx/sites-available/photo-registration`

```nginx
server {
    listen 80;
    server_name photo-form.angeeinstein.stream;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔍 Diagnostic Commands

```bash
# See all services
sudo systemctl status photo-registration nginx

# Check all listening ports
sudo ss -tulpn | grep LISTEN

# Check Flask binding
sudo cat /opt/photo-registration-form/.env | grep GUNICORN_BIND

# Check Flask logs
sudo journalctl -u photo-registration -n 50

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Test Nginx config
sudo nginx -t
```

## 💡 Pro Tips

### Tip 1: Always Check Binding First
```bash
# Check current binding
grep GUNICORN_BIND /opt/photo-registration-form/.env

# If it shows 0.0.0.0:80 and you want Nginx, change it to:
# GUNICORN_BIND=127.0.0.1:5000
```

### Tip 2: Test Configuration Before Applying
```bash
# Test Nginx config without restarting
sudo nginx -t
```

### Tip 3: Use Firewall
```bash
# If Flask is on localhost, block direct access to port 5000 from outside
sudo ufw deny 5000/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

## 📞 Still Having Issues?

1. **Check the full logs:**
   ```bash
   sudo journalctl -u photo-registration -n 100 --no-pager
   sudo journalctl -u nginx -n 100 --no-pager
   ```

2. **Verify file permissions:**
   ```bash
   ls -la /opt/photo-registration-form/
   ls -la /etc/nginx/sites-available/
   ```

3. **Check DNS:**
   ```bash
   nslookup photo-form.angeeinstein.stream
   ping photo-form.angeeinstein.stream
   ```

4. **Test locally first:**
   ```bash
   # Test Flask
   curl http://127.0.0.1:5000/health
   
   # Test Nginx (if hostname DNS not set)
   curl -H "Host: photo-form.angeeinstein.stream" http://localhost/health
   ```

## ✅ Success Checklist

- [ ] Flask service is running: `sudo systemctl status photo-registration`
- [ ] Flask is bound to `127.0.0.1:5000`: `grep GUNICORN_BIND /opt/photo-registration-form/.env`
- [ ] Port 5000 shows Flask: `sudo ss -tulpn | grep :5000`
- [ ] Nginx service is running: `sudo systemctl status nginx`
- [ ] Port 80 shows Nginx: `sudo ss -tulpn | grep :80`
- [ ] Nginx config is valid: `sudo nginx -t`
- [ ] Flask health check works: `curl http://127.0.0.1:5000/health`
- [ ] Nginx proxy works: `curl -H "Host: photo-form.angeeinstein.stream" http://localhost/health`
- [ ] Domain works (if DNS set): `curl http://photo-form.angeeinstein.stream/health`

---

**Once you fix this**, your new installation with the updated script will have the **post-installation wizard** that prevents these issues from happening again! 🎉
