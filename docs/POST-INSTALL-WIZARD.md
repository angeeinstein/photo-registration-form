# Post-Installation Configuration Wizard

After running `sudo bash install.sh` for a fresh installation, the **Post-Installation Configuration Wizard** automatically starts to help you configure your system.

## 🎯 Overview

The wizard guides you through:
1. **Network Binding Configuration** - How the Flask app should be accessible
2. **Nginx Reverse Proxy Setup** - Optional port 80 access with SSL support

## 📋 Step-by-Step Guide

### Step 1: Network Binding

The wizard asks how you want to access the application:

```
Step 1: Network Binding
How do you want to access the application?

1) Local access only (localhost) - Recommended with Nginx reverse proxy
2) Network access (LAN) - For Cloudflare Tunnel on separate server
3) Skip for now (configure later)

Enter your choice [1-3]:
```

#### Option 1: Local Access Only (Recommended with Nginx)
- **Use case**: You want to use Nginx as a reverse proxy
- **Binding**: `127.0.0.1:5000` (localhost)
- **Access**: Only from the local machine
- **Best for**: Production setups with Nginx handling external traffic

#### Option 2: Network Access
- **Use case**: Cloudflare Tunnel running on a separate server
- **Binding**: `0.0.0.0:5000` (all network interfaces)
- **Access**: From any machine on your LAN
- **Configuration**: Automatically detects your server IP (e.g., `192.168.1.104`)
- **Cloudflare Config**: Tunnel should point to `http://YOUR_SERVER_IP:5000`

#### Option 3: Skip
- Keeps default configuration (`127.0.0.1:5000`)
- You can configure later via the settings menu

### Step 2: Nginx Reverse Proxy

The wizard asks if you want to set up Nginx:

```
Step 2: Nginx Reverse Proxy
Do you want to configure Nginx as a reverse proxy?

Benefits:
  - Access on port 80 (no :5000 in URL)
  - SSL/HTTPS support
  - Better performance and security

Configure Nginx now? (y/n):
```

#### If you choose Yes:
1. **Port Check**: Wizard checks if port 80 is available
   - If port 80 is in use, it warns you and shows which service is using it
   
2. **Binding Validation**: If Flask is bound to network (0.0.0.0), it recommends changing to localhost
   ```
   WARNING: For Nginx reverse proxy, Flask should bind to localhost (127.0.0.1:5000)
   Change binding now? (recommended) (y/n):
   ```
   
3. **Hostname Input**: Enter your domain or hostname
   ```
   Enter your domain/hostname (e.g., photos.example.com)
   Or enter 'localhost' for local testing
   Hostname: photo-form.example.com
   ```
   
4. **Configuration**: Creates and activates Nginx configuration
   - Tests the configuration
   - Starts or reloads Nginx
   - Shows access URL

#### If you choose No:
- Skips Nginx configuration
- You can set it up later via the settings menu

## 🎬 Example Session

### Example 1: Using Nginx (Recommended)

```bash
sudo bash install.sh

# ... installation process ...

======================================
Post-Installation Configuration
======================================

The basic installation is complete!
Let's configure your system for production use.

======================================
Step 1: Network Binding
======================================
How do you want to access the application?

1) Local access only (localhost) - Recommended with Nginx reverse proxy
2) Network access (LAN) - For Cloudflare Tunnel on separate server
3) Skip for now (configure later)

Enter your choice [1-3]: 1
[INFO] Keeping default: localhost only (127.0.0.1:5000)

======================================
Step 2: Nginx Reverse Proxy
======================================
Do you want to configure Nginx as a reverse proxy?

Benefits:
  - Access on port 80 (no :5000 in URL)
  - SSL/HTTPS support
  - Better performance and security

Configure Nginx now? (y/n): y

Enter your domain/hostname (e.g., photos.example.com)
Or enter 'localhost' for local testing
Hostname: photos.example.com

[INFO] Creating Nginx configuration for photos.example.com...
[SUCCESS] Nginx site enabled
[INFO] Testing Nginx configuration...
[SUCCESS] Nginx configuration is valid
[INFO] Starting Nginx...
[SUCCESS] Nginx is running!

======================================
Configuration Complete!
======================================

Your Photo Registration Form is ready!

Quick Reference:
  Service status:  sudo systemctl status photo-registration
  View logs:       sudo journalctl -u photo-registration -f
  Reconfigure:     sudo bash install.sh (choose option 3)

Access URLs:
  Local:    http://127.0.0.1:5000
  Domain:   http://photos.example.com

Documentation:
  Main README:              /opt/photo-registration-form/README.md
  Tunnel Setup:             /opt/photo-registration-form/TUNNEL-ON-SEPARATE-SERVER.md
  systemd & Nginx Guide:    /opt/photo-registration-form/SYSTEMD-NGINX-MANAGEMENT.md
```

### Example 2: Cloudflare Tunnel on Separate Server

```bash
sudo bash install.sh

# ... installation process ...

======================================
Step 1: Network Binding
======================================
How do you want to access the application?

1) Local access only (localhost) - Recommended with Nginx reverse proxy
2) Network access (LAN) - For Cloudflare Tunnel on separate server
3) Skip for now (configure later)

Enter your choice [1-3]: 2

[INFO] Configuring for network access...
[SUCCESS] Configured for network access on 0.0.0.0:5000
[INFO] Your server IP appears to be: 192.168.1.104
[INFO] Configure Cloudflare Tunnel with: http://192.168.1.104:5000
[INFO] Restarting service...
[SUCCESS] Service restarted successfully

======================================
Step 2: Nginx Reverse Proxy
======================================
Do you want to configure Nginx as a reverse proxy?

Benefits:
  - Access on port 80 (no :5000 in URL)
  - SSL/HTTPS support
  - Better performance and security

Configure Nginx now? (y/n): n
[INFO] Skipped Nginx configuration

======================================
Configuration Complete!
======================================

Your Photo Registration Form is ready!

Quick Reference:
  Service status:  sudo systemctl status photo-registration
  View logs:       sudo journalctl -u photo-registration -f
  Reconfigure:     sudo bash install.sh (choose option 3)

Access URLs:
  Local:    http://127.0.0.1:5000
  Network:  http://192.168.1.104:5000

Documentation:
  Main README:              /opt/photo-registration-form/README.md
  Tunnel Setup:             /opt/photo-registration-form/TUNNEL-ON-SEPARATE-SERVER.md
  systemd & Nginx Guide:    /opt/photo-registration-form/SYSTEMD-NGINX-MANAGEMENT.md
```

## 🔧 Reconfiguring Later

You can always run the configuration again:

```bash
sudo bash install.sh
# Choose: 3) Configure settings
# Then: 1) Configure network binding
# Or:   2) Change hostname for Nginx
# Or:   3) Install/Update Nginx configuration
```

## ⚠️ Common Issues & Solutions

### Issue 1: Port 80 Already in Use

**Symptom:**
```
WARNING: Port 80 is already in use!
```

**Solution:**
1. Check what's using port 80:
   ```bash
   sudo ss -tulpn | grep :80
   ```

2. If it's your Flask app (bound to 0.0.0.0:80):
   - Choose option to change binding to localhost
   - Or stop Flask: `sudo systemctl stop photo-registration`

3. If it's another web server (Apache, old Nginx):
   ```bash
   sudo systemctl stop apache2  # or httpd
   ```

### Issue 2: Nginx Configuration Test Failed

**Symptom:**
```
[ERROR] Nginx configuration test failed
```

**Solution:**
1. Check the error details:
   ```bash
   sudo nginx -t
   ```

2. Common causes:
   - Syntax error in `/etc/nginx/sites-available/photo-registration`
   - Port conflict with another site
   - Missing SSL certificates (if SSL is enabled)

3. Fix manually or remove and reconfigure:
   ```bash
   sudo rm /etc/nginx/sites-enabled/photo-registration
   sudo rm /etc/nginx/sites-available/photo-registration
   sudo bash install.sh  # Choose option 3 → 3
   ```

### Issue 3: Cannot Access from Network

**Symptom:**
- Configured for network access (0.0.0.0:5000)
- Cannot access from another machine

**Solution:**
1. Check firewall:
   ```bash
   sudo ufw status
   sudo ufw allow 5000/tcp
   ```

2. Verify binding:
   ```bash
   sudo systemctl status photo-registration
   sudo cat /opt/photo-registration-form/.env | grep GUNICORN_BIND
   ```

3. Test locally first:
   ```bash
   curl http://127.0.0.1:5000/health
   curl http://YOUR_SERVER_IP:5000/health
   ```

## 📚 Related Documentation

- **[Main README](README.md)** - Complete project documentation
- **[Tunnel on Separate Server](TUNNEL-ON-SEPARATE-SERVER.md)** - Detailed Cloudflare Tunnel setup
- **[systemd & Nginx Management](SYSTEMD-NGINX-MANAGEMENT.md)** - Service management guide
- **[Port & Tunnel Configuration](PORT-AND-TUNNEL-CONFIG.md)** - Network binding details

## 🎓 Best Practices

### For Production with Domain:
1. Choose **Option 1** (localhost binding)
2. Configure **Nginx** with your domain
3. Set up **SSL/HTTPS** (see Nginx config template)
4. Configure Cloudflare Tunnel to point to `http://localhost` or `http://YOUR_DOMAIN`

### For Cloudflare Tunnel on Separate Server:
1. Choose **Option 2** (network binding)
2. **Skip Nginx** configuration
3. Note your server IP
4. Configure Cloudflare Tunnel on the separate server to `http://YOUR_SERVER_IP:5000`

### For Development/Testing:
1. Choose **Option 1** (localhost) or **Skip**
2. **Skip Nginx** for now
3. Access locally at `http://127.0.0.1:5000`
4. Configure later when needed

## 🔄 Automation Tips

If you want to automate the installation without interaction, you can:

1. Skip the wizard by exiting after installation completes
2. Use the menu system for scripted configuration:
   ```bash
   # Example: Configure for network access
   echo "3" | sudo bash install.sh  # Choose "Configure settings"
   # Then manually select options
   ```

3. Edit `.env` and restart:
   ```bash
   sudo nano /opt/photo-registration-form/.env
   # Set GUNICORN_BIND=0.0.0.0:5000
   sudo systemctl restart photo-registration
   ```

---

**Need Help?** Check the [troubleshooting section](README.md#troubleshooting) in the main README or review the detailed guides linked above.
