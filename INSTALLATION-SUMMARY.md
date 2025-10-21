# Installation Summary

## What Happens When You Run `sudo bash install.sh`

This document explains exactly what happens during a fresh installation of the Photo Registration Form.

## 📦 Phase 1: Automatic Installation (No User Input)

### 1. System Preparation
```
[INFO] Detected OS: ubuntu 25.04
[INFO] Updating package lists...
```

### 2. Dependency Installation
The script automatically installs **ALL** required software:
```
[INFO] Installing required packages (Python, Nginx, etc.)...
```

**Installed automatically:**
- ✅ Python 3.8+
- ✅ Python pip
- ✅ Python venv
- ✅ Python dev tools
- ✅ Build essential tools
- ✅ Git
- ✅ curl & wget
- ✅ SQLite3
- ✅ **Nginx** (web server)

**No prompts** - Everything installs automatically!

### 3. Application Setup
```
[INFO] Creating installation directory: /opt/photo-registration-form
[INFO] Copying application files...
[INFO] Creating Python virtual environment...
[INFO] Installing Python dependencies...
```

Installs Python packages:
- Flask 3.0.0
- SQLAlchemy 2.0.25
- Gunicorn 21.2.0
- python-dotenv 1.0.0

### 4. Database Initialization
```
[INFO] Initializing database...
```

Creates SQLite database with `Registration` table.

### 5. Service Configuration
```
[INFO] Creating log directory: /var/log/photo-registration
[INFO] Creating run directory: /var/run/photo-registration
[INFO] Setting permissions...
[INFO] Installing systemd service...
[INFO] Enabling service...
[INFO] Starting service...
[SUCCESS] Service is running!
```

Sets up systemd service that:
- Starts automatically on boot
- Restarts on failure
- Runs as `www-data` user
- Logs to `/var/log/photo-registration/`

### 6. Installation Complete
```
[SUCCESS] Installation completed successfully!

======================================
Installation Information
======================================

Installation Directory: /opt/photo-registration-form
Service Name: photo-registration
Log Directory: /var/log/photo-registration
Database File: /opt/photo-registration-form/registrations.db
Configuration: /opt/photo-registration-form/.env
```

## 🎯 Phase 2: Post-Installation Wizard (Interactive)

After automatic installation, the **Configuration Wizard** starts automatically.

### Step 1: Network Binding Choice

```
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

Enter your choice [1-3]:
```

**You choose one of:**

#### ➡️ Option 1: Local Access Only
- Flask binds to `127.0.0.1:5000`
- Best for: Using Nginx as reverse proxy
- Result: Application only accessible from local machine

#### ➡️ Option 2: Network Access
- Flask binds to `0.0.0.0:5000`
- Best for: Cloudflare Tunnel on separate server
- Result: Application accessible from any machine on LAN
- **Bonus**: Script automatically detects your server IP and shows Cloudflare config:
  ```
  [INFO] Your server IP appears to be: 192.168.1.104
  [INFO] Configure Cloudflare Tunnel with: http://192.168.1.104:5000
  ```

#### ➡️ Option 3: Skip
- Keeps default (localhost)
- Configure later

### Step 2: Nginx Setup

```
======================================
Step 2: Nginx Reverse Proxy
======================================
Do you want to configure Nginx as a reverse proxy?

Benefits:
  - Access on port 80 (no :5000 in URL)
  - SSL/HTTPS support
  - Better performance and security

Configure Nginx now? (y/n):
```

#### ➡️ If you choose "y" (Yes):

1. **Binding Check** (if needed):
   ```
   WARNING: For Nginx reverse proxy, Flask should bind to localhost (127.0.0.1:5000)
   Change binding now? (recommended) (y/n):
   ```
   - If Flask is bound to network, suggests changing to localhost
   - This is recommended for security

2. **Hostname Input**:
   ```
   Enter your domain/hostname (e.g., photos.example.com)
   Or enter 'localhost' for local testing
   Hostname: photos.example.com
   ```
   - Enter your domain
   - Or type `localhost` for testing

3. **Configuration & Testing**:
   ```
   [INFO] Creating Nginx configuration for photos.example.com...
   [SUCCESS] Nginx site enabled
   [INFO] Testing Nginx configuration...
   [SUCCESS] Nginx configuration is valid
   [INFO] Starting Nginx...
   [SUCCESS] Nginx is running!
   ```

4. **Port Conflict Detection**:
   - If port 80 is already in use:
     ```
     [ERROR] Failed to start Nginx
     [INFO] Checking what's using port 80...
     tcp  0  0  0.0.0.0:80  0.0.0.0:*  LISTEN  1234/photo-registration
     ```
   - Script helps you identify and resolve conflicts

#### ➡️ If you choose "n" (No):
```
[INFO] Skipped Nginx configuration
```
- No Nginx setup
- Can configure later via menu

### Final Summary

```
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
  Network:  http://192.168.1.104:5000  (if configured)
  Domain:   http://photos.example.com   (if Nginx configured)

Documentation:
  Main README:              /opt/photo-registration-form/README.md
  Tunnel Setup:             /opt/photo-registration-form/TUNNEL-ON-SEPARATE-SERVER.md
  systemd & Nginx Guide:    /opt/photo-registration-form/SYSTEMD-NGINX-MANAGEMENT.md
```

## ⏱️ Total Installation Time

**Typical installation time:** 2-5 minutes

- Automatic installation: 1-3 minutes
- Configuration wizard: 1-2 minutes (depending on your choices)

## 📊 Installation Decision Tree

```
Start: sudo bash install.sh
    |
    v
[Automatic Installation]
    |
    v
Step 1: Network Binding?
    |
    ├─> Option 1 (localhost) ──> Best for Nginx setup
    |                             |
    ├─> Option 2 (network) ────> Best for separate tunnel
    |                             |
    └─> Option 3 (skip) ────────> Configure later
    |
    v
Step 2: Nginx Setup?
    |
    ├─> Yes ─┬─> Binding OK? ──> Enter hostname ──> Done!
    |        |                                      |
    |        └─> Fix binding? ──> Enter hostname ──> Done!
    |                                               |
    └─> No ──────────────────────────────────────> Done!
```

## 🎯 Common Scenarios

### Scenario 1: Production with Your Own Domain
**Goal:** Access at `http://photos.yourdomain.com`

**Choose:**
1. Step 1: **Option 1** (localhost)
2. Step 2: **Yes** (Nginx)
3. Hostname: `photos.yourdomain.com`

**Result:**
- Flask: `127.0.0.1:5000`
- Nginx: Port 80, proxies to Flask
- Access: `http://photos.yourdomain.com`

### Scenario 2: Cloudflare Tunnel on Same Server
**Goal:** Access via Cloudflare domain, tunnel on same server

**Choose:**
1. Step 1: **Option 1** (localhost)
2. Step 2: **No** (skip Nginx)

**Then configure Cloudflare Tunnel:**
```yaml
ingress:
  - hostname: photos.yourdomain.com
    service: http://localhost:5000
```

**Result:**
- Flask: `127.0.0.1:5000`
- Cloudflare Tunnel connects to localhost
- Access: `https://photos.yourdomain.com`

### Scenario 3: Cloudflare Tunnel on Different Server
**Goal:** Tunnel runs on separate machine (192.168.1.100), Flask on 192.168.1.104

**Choose:**
1. Step 1: **Option 2** (network access)
   - Note the server IP shown
2. Step 2: **No** (skip Nginx)

**Then on tunnel server (192.168.1.100):**
```yaml
ingress:
  - hostname: photos.yourdomain.com
    service: http://192.168.1.104:5000
```

**Result:**
- Flask: `0.0.0.0:5000` on 192.168.1.104
- Tunnel server: Connects to 192.168.1.104:5000
- Access: `https://photos.yourdomain.com`

### Scenario 4: Development/Testing
**Goal:** Just want to test locally

**Choose:**
1. Step 1: **Option 3** (skip) or **Option 1**
2. Step 2: **No** (skip Nginx)

**Result:**
- Flask: `127.0.0.1:5000`
- Access: `http://127.0.0.1:5000`

## 🔧 After Installation

### Test the Application
```bash
# Health check
curl http://127.0.0.1:5000/health

# Open in browser
# Visit: http://127.0.0.1:5000 (or your configured URL)
```

### Check Service Status
```bash
sudo systemctl status photo-registration
```

### View Logs
```bash
# Follow live logs
sudo journalctl -u photo-registration -f

# View recent logs
sudo journalctl -u photo-registration -n 50
```

### Reconfigure
```bash
sudo bash install.sh
# Choose: 3) Configure settings
```

## 📚 Next Steps

After installation:

1. **Test the application** - Visit the URL shown in the summary
2. **Configure Cloudflare Tunnel** (if applicable) - See [TUNNEL-ON-SEPARATE-SERVER.md](TUNNEL-ON-SEPARATE-SERVER.md)
3. **Set up SSL** (if using Nginx) - Edit nginx config for SSL certificates
4. **Review security** - Check firewall rules, update packages

## 🆘 Troubleshooting

### Installation Failed
Check logs:
```bash
sudo journalctl -u photo-registration -n 100
```

### Service Won't Start
```bash
# Check status
sudo systemctl status photo-registration

# Check logs
sudo journalctl -xe

# Test manually
cd /opt/photo-registration-form
source venv/bin/activate
python app.py
```

### Nginx Issues
```bash
# Test config
sudo nginx -t

# Check what's on port 80
sudo ss -tulpn | grep :80

# Restart nginx
sudo systemctl restart nginx
```

### Port Conflicts
```bash
# Find what's using port 5000
sudo ss -tulpn | grep :5000

# Find what's using port 80
sudo ss -tulpn | grep :80
```

## 📖 Full Documentation

- **[Post-Installation Wizard Guide](POST-INSTALL-WIZARD.md)** - Detailed wizard walkthrough
- **[Main README](README.md)** - Complete project documentation
- **[Tunnel Setup Guide](TUNNEL-ON-SEPARATE-SERVER.md)** - Cloudflare Tunnel configuration
- **[systemd & Nginx Guide](SYSTEMD-NGINX-MANAGEMENT.md)** - Service management

---

**Questions?** Open an issue on GitHub or check the documentation files listed above.
