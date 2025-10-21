# Photo Registration Form

A Flask-based web application for collecting photo registration information at fair events. Participants can register with their name and email to receive their event photos.

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/angeeinstein/photo-registration-form.git
cd photo-registration-form

# 2. Run the installer (automatic + configuration wizard)
sudo bash install.sh

# The script will:
# - Automatically install ALL dependencies (Python, Nginx, etc.)
# - Set up the application and database
# - Ask you to configure network binding and Nginx
# - Guide you through the entire setup interactively

# 3. Test the application
curl http://127.0.0.1:5000/health
```

**That's it!** The installation is fully automated with an interactive configuration wizard. No manual editing of config files needed!

## Features

- 📝 Simple registration form (first name, last name, email)
- 💾 SQLite database for storing registrations
- 🎨 Responsive, modern UI design
- 🚀 Production-ready with Gunicorn
- 🔄 Systemd service for automatic startup
- 🌐 Cloudflare tunnel compatible for public access
- ✅ Form validation (client and server-side)
- 📊 Admin endpoint to view all registrations

## Tech Stack

- **Backend**: Flask 3.0
- **Database**: SQLite with SQLAlchemy ORM
- **WSGI Server**: Gunicorn
- **Service Management**: systemd
- **Tunnel**: Cloudflare Tunnel

## Project Structure

```
photo-registration-form/
├── app.py                      # Main Flask application
├── gunicorn_config.py          # Gunicorn configuration
├── requirements.txt            # Python dependencies
├── photo-registration.service  # systemd service file
├── templates/
│   └── index.html             # Registration form template
├── registrations.db           # SQLite database (auto-created)
└── README.md                  # This file
```

## Installation

### Prerequisites

- Linux server (Ubuntu/Debian recommended)
- Python 3.8 or higher
- sudo access
- git
- Cloudflare account (for tunnel)

### Quick Installation (Recommended)

The easiest way to install is using the automated install script:

```bash
# Clone the repository
git clone https://github.com/angeeinstein/photo-registration-form.git
cd photo-registration-form

# Run the install script (fully automated + interactive wizard)
sudo bash install.sh
```

The install script will **automatically**:
- ✅ Install **ALL** system dependencies (Python, Nginx, git, etc.)
- ✅ Create Python virtual environment
- ✅ Install Python packages
- ✅ Initialize the database
- ✅ Set up systemd service
- ✅ Generate secure SECRET_KEY
- ✅ Start the application

Then the **post-installation wizard** will ask you to configure:
1. **Network Binding** - Choose between:
   - Localhost only (127.0.0.1:5000) - for Nginx reverse proxy
   - Network access (0.0.0.0:5000) - for Cloudflare Tunnel on separate server
   - Skip (configure later)

2. **Nginx Reverse Proxy** (optional) - Automatic setup for:
   - Port 80 access (no :5000 in URL)
   - SSL/HTTPS support
   - Better performance and security
   - Enter your domain/hostname and it's configured!

3. **Port conflict detection** - Automatically checks port 80 availability

**For updates:**
```bash
cd photo-registration-form
git pull
sudo bash install.sh
# Choose option 1 to update
```

**For complete reinstall:**
```bash
cd photo-registration-form
sudo bash install.sh
# Choose option 2 to reinstall (keeps database)
# Choose option 3 to remove everything
```

### Manual Installation (Alternative)

If you prefer to install manually, follow these steps:

### Step 1: Clone the Project

```bash
# Clone repository
git clone https://github.com/angeeinstein/photo-registration-form.git
cd photo-registration-form
```

### Step 2: Install to System

```bash
# Copy to installation directory
sudo mkdir -p /opt/photo-registration-form
sudo cp -r * /opt/photo-registration-form/
cd /opt/photo-registration-form

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Create .env file from example
cp .env.example .env

# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Edit .env and set the SECRET_KEY
sudo nano .env
```

### Step 4: Initialize the Database

```bash
# Still in virtual environment
python app.py
# This will create the database and then exit (Ctrl+C after "Database initialized successfully!")
```

### Step 6: Set Up Systemd Service

```bash
# Copy service file
sudo cp photo-registration.service /etc/systemd/system/

# Edit the service file to set a secure SECRET_KEY
sudo nano /etc/systemd/system/photo-registration.service
# Change: Environment="SECRET_KEY=your-secret-key-change-me"
# To:     Environment="SECRET_KEY=<your-generated-secret-key>"

# Create log directory
sudo mkdir -p /var/log/photo-registration
sudo chown www-data:www-data /var/log/photo-registration

# Create run directory for PID
sudo mkdir -p /var/run/photo-registration
sudo chown www-data:www-data /var/run/photo-registration

# Ensure www-data can access the application
sudo chown -R www-data:www-data /opt/photo-registration-form

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable photo-registration

# Start the service
sudo systemctl start photo-registration

# Check status
sudo systemctl status photo-registration
```

## 🌐 Web Server Configuration

### Option 1: Nginx (Recommended for Production)

The install script can automatically configure Nginx as a reverse proxy:

```bash
sudo bash install.sh
# Choose option 3: Configure settings
# Choose option 1 or 2: Configure Nginx

# Or use the automated hostname configuration:
# Enter your domain when prompted (e.g., photos.example.com)
```

This will:
- Install Nginx (if not present)
- Create configuration from template
- Set up reverse proxy to port 5000
- Enable the site
- Reload Nginx

**Manual Nginx Setup:**

```bash
# Edit the nginx configuration
sudo nano /etc/nginx/sites-available/photo-registration

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Option 2: Cloudflare Tunnel (For Public Access)

**Important:** The Flask app runs on **port 5000** and binds to **127.0.0.1** (localhost only) by default.

For Cloudflare Tunnel setup, you have two options:

#### Option A: Tunnel on Same Server (Recommended - No Config Changes)

Install cloudflared **on the same server** (e.g., 192.168.1.104) and tunnel to localhost:

```yaml
service: http://127.0.0.1:5000  # ← Connects locally
```

**Advantages:** More secure, no network exposure, no changes needed.

#### Option B: Tunnel from Different Machine (Requires Config Change)

If cloudflared runs on a **different machine**, you need to:

1. Change Flask to listen on all interfaces:
```bash
# Edit gunicorn_config.py
sudo nano /opt/photo-registration-form/gunicorn_config.py
# Change: bind = "127.0.0.1:5000"
# To:     bind = "0.0.0.0:5000"

# Restart service
sudo systemctl restart photo-registration
```

2. Configure tunnel to your server's LAN IP:
```yaml
service: http://192.168.1.104:5000  # ← Your server IP
```

**See [PORT-AND-TUNNEL-CONFIG.md](PORT-AND-TUNNEL-CONFIG.md) for detailed comparison.**

---

#### Install Cloudflared

```bash
# Download and install cloudflared (Debian/Ubuntu)
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

#### Authenticate with Cloudflare

```bash
cloudflared tunnel login
# This will open a browser to authenticate
```

#### Create and Configure Tunnel

```bash
# Create a tunnel
cloudflared tunnel create photo-registration

# Note the Tunnel ID from the output

# Create config file
sudo mkdir -p /etc/cloudflared
sudo nano /etc/cloudflared/config.yml
```

Add the following configuration (replace with your tunnel ID and domain):

```yaml
tunnel: <YOUR-TUNNEL-ID>
credentials-file: /root/.cloudflared/<YOUR-TUNNEL-ID>.json

ingress:
  - hostname: photos.yourdomain.com
    service: http://127.0.0.1:5000
  - service: http_status:404
```

#### Route the Tunnel to Your Domain

```bash
# Add DNS record
cloudflared tunnel route dns photo-registration photos.yourdomain.com
```

#### Install Tunnel as a Service

```bash
# Install cloudflared as a service
sudo cloudflared service install

# Start the tunnel
sudo systemctl start cloudflared

# Enable on boot
sudo systemctl enable cloudflared

# Check status
sudo systemctl status cloudflared
```

## Usage

### Access the Application

- **Local**: `http://127.0.0.1:5000`
- **Public**: `https://photos.yourdomain.com` (after Cloudflare tunnel setup)

### Registration Form

Users can access the main page and fill in:
- First Name
- Last Name (Second Name)
- Email Address

### API Endpoints

- `GET /` - Display registration form
- `POST /register` - Submit registration (form data)
- `GET /registrations` - List all registrations (JSON)
- `GET /health` - Health check endpoint

### View Registrations

Access the registrations endpoint to see all submissions:
```
https://photos.yourdomain.com/registrations
```

## Testing Installation

After installation, verify everything is working:

```bash
# Run the test script
sudo bash test-installation.sh
```

This will test:
- ✅ Service status
- ✅ Health endpoint
- ✅ Main page
- ✅ Registration endpoint
- ✅ Database connectivity
- ✅ Log files

Or test manually:

```bash
# Check service status
sudo systemctl status photo-registration

# Test health endpoint
curl http://127.0.0.1:5000/health

# View registrations
curl http://127.0.0.1:5000/registrations
```

## Management Commands

### Service Management

```bash
# Start service
sudo systemctl start photo-registration

# Stop service
sudo systemctl stop photo-registration

# Restart service
sudo systemctl restart photo-registration

# View status
sudo systemctl status photo-registration

# View logs
sudo journalctl -u photo-registration -f
```

### Application Logs

```bash
# Access logs
sudo tail -f /var/log/photo-registration/access.log

# Error logs
sudo tail -f /var/log/photo-registration/error.log
```

### Database Backup

```bash
# Backup database
sudo cp /opt/photo-registration-form/registrations.db /opt/photo-registration-form/registrations.db.backup

# Or with timestamp
sudo cp /opt/photo-registration-form/registrations.db /opt/photo-registration-form/registrations.db.$(date +%Y%m%d_%H%M%S)
```

## Uninstallation

To completely remove the application:

```bash
sudo bash install.sh
# Choose option 4 (Complete removal)
# Optionally backup database before removal
```

This will:
- Stop and disable the service
- Optionally backup the database
- Remove all application files
- Remove nginx configuration (if installed)
- Remove logs and runtime files
- Clean the system completely

## Security Considerations

1. **SECRET_KEY**: The install script automatically generates a strong secret key.
   To manually generate one:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```
   Update this in `/opt/photo-registration-form/.env`

2. **HTTPS**: Cloudflare tunnel automatically provides HTTPS

3. **Rate Limiting**: Consider adding Flask-Limiter for production

4. **Database**: For production with high traffic, consider PostgreSQL instead of SQLite

5. **Firewall**: Ensure only localhost can access port 5000:
   ```bash
   sudo ufw allow 22/tcp  # SSH
   sudo ufw enable
   # Port 5000 should only be accessible via localhost (Cloudflare tunnel)
   ```

## Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u photo-registration -n 50

# Check permissions
ls -la /opt/photo-registration-form
sudo chown -R www-data:www-data /opt/photo-registration-form
```

### Cloudflare tunnel issues

```bash
# Check tunnel status
sudo systemctl status cloudflared

# Check tunnel logs
sudo journalctl -u cloudflared -f

# Test local connection
curl http://127.0.0.1:5000/health
```

### Database locked error

SQLite doesn't handle concurrent writes well. If you get database locked errors:
- Restart the service
- Consider migrating to PostgreSQL for production

## Development

### Local Development

```bash
# Activate virtual environment
source venv/bin/activate

# Run development server
python app.py

# Access at http://localhost:5000
```

### Testing

```bash
# Test health endpoint
curl http://localhost:5000/health

# Test registration (with form data)
curl -X POST http://localhost:5000/register \
  -d "first_name=John&last_name=Doe&email=john@example.com"

# View registrations
curl http://localhost:5000/registrations
```

## 📚 Documentation

### 🚀 Getting Started
- **[Installation Summary](INSTALLATION-SUMMARY.md)** - 📦 **READ THIS FIRST** - What happens during installation
- **[Post-Installation Wizard Guide](POST-INSTALL-WIZARD.md)** - 🎯 Step-by-step configuration guide

### 📧 Email System
- **[Email System Documentation](EMAIL-SYSTEM.md)** - ✉️ **Complete email guide** - Confirmation emails, photos delivery, admin panel

### 🌐 Network & Tunnel Setup
- **[Tunnel on Separate Server Guide](TUNNEL-ON-SEPARATE-SERVER.md)** - Setup for Cloudflare Tunnel on different machine
- **[Port & Tunnel Configuration](PORT-AND-TUNNEL-CONFIG.md)** - Server port and Cloudflare Tunnel setup guide

### ⚙️ System Management
- **[systemd & Nginx Management](SYSTEMD-NGINX-MANAGEMENT.md)** - Complete guide to service configuration
- **[Install Menu Guide](INSTALL-MENU-GUIDE.md)** - Visual guide to the interactive installation menu
- **[Quick Reference Guide](QUICK-REFERENCE.md)** - Common commands and operations

### 📝 Contributing
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute and maintain compatibility
- **[Changelog](CHANGELOG.md)** - Version history and changes

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) to understand how to make changes while maintaining compatibility with the installation system.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues with:
- **Flask application**: Check application logs and error.log
- **Systemd service**: Check `journalctl -u photo-registration`
- **Cloudflare tunnel**: Check `journalctl -u cloudflared`

**Quick troubleshooting**: See [QUICK-REFERENCE.md](QUICK-REFERENCE.md#-troubleshooting)

---

Made with ❤️ for your fair event photography
