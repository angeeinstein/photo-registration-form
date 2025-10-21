# 🎯 Quick Fix for Your Current Issue

## Your Current Problem

Nginx is failing to start with: **"Port 80 is already in use"**

## 🚀 Fastest Solution

### Step 1: Find What's on Port 80

```bash
sudo ss -tulpn | grep :80
```

### Step 2: Most Likely It's Your Flask App

Check your Flask binding:
```bash
cat /opt/photo-registration-form/.env | grep GUNICORN_BIND
```

If it shows `0.0.0.0:80` or `0.0.0.0:5000`, that's your issue.

### Step 3: Use the New Script to Fix Everything

```bash
# Pull latest changes
cd /root/photo-registration-form
git pull

# Run the install script
sudo bash install.sh
```

You'll see the **main menu** (because it detects existing installation):
```
1) Update installation (git pull + restart service)
2) Reinstall (keep database and .env)
3) Configure settings (hostname, nginx, etc.)  ← Choose this
4) Complete removal (uninstall everything)
5) View status
6) Cancel
```

Choose **3** (Configure settings)

Then you'll see:
```
1) Configure network binding (localhost vs network access)  ← Choose this first
2) Change hostname for Nginx
3) Install/Update Nginx configuration
4) Edit .env file
5) Change SECRET_KEY
6) Back to main menu
```

Choose **1** (Configure network binding), then **Option 1** (Localhost)

This will:
- ✅ Change Flask to bind to `127.0.0.1:5000`
- ✅ Restart the Flask service
- ✅ Free up port 80

Then go back and choose **2** (Change hostname for Nginx):
- Enter: `photo-form.angeeinstein.stream`
- Script will configure and start Nginx
- Everything will work! 🎉

## 📊 What You'll See

```bash
$ sudo bash install.sh
[INFO] Detected OS: ubuntu 25.04

======================================
Photo Registration Form - Management Menu
======================================

[INFO] Installation detected at: /opt/photo-registration-form

1) Update installation (git pull + restart service)
2) Reinstall (keep database and .env)
3) Configure settings (hostname, nginx, etc.)
4) Complete removal (uninstall everything)
5) View status
6) Cancel

Enter your choice [1-6]: 3  ← You type this

======================================
Configure Settings
======================================

Available settings to configure:

1) Configure network binding (localhost vs network access)
2) Change hostname for Nginx
3) Install/Update Nginx configuration
4) Edit .env file
5) Change SECRET_KEY
6) Back to main menu

Enter your choice [1-6]: 1  ← You type this

======================================
Configure Network Binding
======================================

Current binding: 0.0.0.0:80  ← Shows your current setting

Choose network binding configuration:

1) Localhost only (127.0.0.1:5000) - Recommended for reverse proxy
2) Allow network access on port 5000 (0.0.0.0:5000)
3) Allow network access on port 80 (0.0.0.0:80) - Requires privileges
4) Custom binding (advanced)
5) Back to settings menu

Enter your choice [1-5]: 1  ← You type this

[INFO] Updating .env file with: 127.0.0.1:5000...
[SUCCESS] Network binding updated
[INFO] Restarting service...
[SUCCESS] Service restarted successfully

Current configuration:
- Binding: 127.0.0.1:5000
- Access: Localhost only
- Status: Running

[INFO] For Nginx reverse proxy, use this binding (recommended)
[INFO] For Cloudflare Tunnel, use network binding instead

Test the configuration:
- Local access: curl http://127.0.0.1:5000/health

Press Enter to continue...
```

Then press Enter, choose **2** (Change hostname), and enter your domain:

```bash
======================================
Configure Hostname
======================================

Enter your domain/hostname (e.g., photos.example.com)
Or enter 'localhost' for local access only
Hostname: photo-form.angeeinstein.stream  ← You type this

[INFO] Creating nginx configuration...
[SUCCESS] Nginx site enabled
[INFO] Testing Nginx configuration...
[SUCCESS] Nginx configuration is valid
[INFO] Starting Nginx...
[SUCCESS] Nginx is running!

[SUCCESS] Hostname configured: photo-form.angeeinstein.stream

You can now access the application at: http://photo-form.angeeinstein.stream
Make sure DNS is pointing to this server's IP address

Press Enter to continue...
```

## ✅ Verify It's Working

```bash
# Check Flask (should be on localhost:5000)
curl http://127.0.0.1:5000/health

# Check Nginx (should respond)
curl http://photo-form.angeeinstein.stream/health
```

## 🎉 That's It!

Your installation will now:
- ✅ Flask runs on `127.0.0.1:5000`
- ✅ Nginx runs on port `80`
- ✅ Nginx proxies to Flask
- ✅ Everything accessible via your domain

## 🔮 Future Installations

When you do fresh installations on new servers, the new **post-installation wizard** will automatically:
1. Install everything (including Nginx) without prompts
2. Ask you how to configure network binding
3. Ask you about Nginx setup
4. Configure everything perfectly

No more port conflicts! 🎊

---

**Quick commands if something goes wrong:**
```bash
# See what's on what port
sudo ss -tulpn | grep -E ':80|:5000'

# Check service status
sudo systemctl status photo-registration nginx

# View logs
sudo journalctl -u photo-registration -n 50
sudo journalctl -u nginx -n 50
```
