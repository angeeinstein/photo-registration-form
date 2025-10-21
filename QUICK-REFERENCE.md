# Quick Reference Guide

## 🚀 Installation

```bash
git clone https://github.com/angeeinstein/photo-registration-form.git
cd photo-registration-form
sudo bash install.sh
# Choose option 1 for fresh installation
```

## 🔄 Update

```bash
cd photo-registration-form
git pull
sudo bash install.sh
# Select option 1 (Update)
```

## ⚙️ Configure Settings

```bash
sudo bash install.sh
# Select option 3 (Configure settings)
# Then choose:
#   1) Change hostname for Nginx
#   2) Install/Update Nginx configuration
#   3) Edit .env file
#   4) Change SECRET_KEY
```

## 📊 View Status

```bash
sudo bash install.sh
# Select option 5 (View status)
# Shows service status, database info, nginx config, and recent logs
```

## ❌ Uninstall

```bash
sudo bash install.sh
# Select option 4 (Complete removal)
# Optionally backup database before removal
```

## 🔧 Service Management

```bash
# Start service
sudo systemctl start photo-registration

# Stop service
sudo systemctl stop photo-registration

# Restart service
sudo systemctl restart photo-registration

# Check status
sudo systemctl status photo-registration

# Enable on boot
sudo systemctl enable photo-registration

# Disable on boot
sudo systemctl disable photo-registration
```

## 📊 Logs

```bash
# Service logs (live)
sudo journalctl -u photo-registration -f

# Service logs (last 100 lines)
sudo journalctl -u photo-registration -n 100

# Access logs
sudo tail -f /var/log/photo-registration/access.log

# Error logs
sudo tail -f /var/log/photo-registration/error.log
```

## 🗄️ Database

```bash
# Backup database
sudo cp /opt/photo-registration-form/registrations.db \
    /opt/photo-registration-form/registrations.db.backup.$(date +%Y%m%d)

# View registrations (SQLite CLI)
sudo sqlite3 /opt/photo-registration-form/registrations.db
sqlite> SELECT * FROM registration;
sqlite> .exit

# Export to CSV
sudo sqlite3 /opt/photo-registration-form/registrations.db \
    "SELECT * FROM registration;" \
    -header -csv > registrations.csv
```

## 🌐 Testing

```bash
# Run test suite
sudo bash test-installation.sh

# Health check
curl http://127.0.0.1:5000/health

# Test registration
curl -X POST http://127.0.0.1:5000/register \
  -d "first_name=John&last_name=Doe&email=john@example.com"

# View all registrations
curl http://127.0.0.1:5000/registrations | python3 -m json.tool
```

## ⚙️ Configuration

```bash
# Edit environment variables
sudo nano /opt/photo-registration-form/.env

# After editing, restart service
sudo systemctl restart photo-registration

# Generate new SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 📁 Important Paths

| Item | Path |
|------|------|
| Application | `/opt/photo-registration-form/` |
| Database | `/opt/photo-registration-form/registrations.db` |
| Environment | `/opt/photo-registration-form/.env` |
| Service File | `/etc/systemd/system/photo-registration.service` |
| Logs | `/var/log/photo-registration/` |
| PID File | `/var/run/photo-registration/gunicorn.pid` |

## 🔒 Permissions

```bash
# Fix permissions
sudo chown -R www-data:www-data /opt/photo-registration-form
sudo chown -R www-data:www-data /var/log/photo-registration
sudo chown -R www-data:www-data /var/run/photo-registration

# Verify permissions
ls -la /opt/photo-registration-form
```

## 🌐 Nginx Configuration

```bash
# Configure via install script (recommended)
sudo bash install.sh
# Choose option 3 → Configure settings
# Choose option 1 → Change hostname for Nginx

# Manual configuration
sudo nano /etc/nginx/sites-available/photo-registration

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Check nginx status
sudo systemctl status nginx

# View nginx logs
sudo tail -f /var/log/nginx/photo-registration-access.log
sudo tail -f /var/log/nginx/photo-registration-error.log
```

## 🌐 Cloudflare Tunnel

```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Login
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create photo-registration

# Configure tunnel
sudo nano /etc/cloudflared/config.yml

# Route DNS
cloudflared tunnel route dns photo-registration photos.yourdomain.com

# Install as service
sudo cloudflared service install

# Start tunnel
sudo systemctl start cloudflared

# Check tunnel status
sudo systemctl status cloudflared
```

## 🐛 Troubleshooting

### Service won't start

```bash
# Check detailed logs
sudo journalctl -u photo-registration -n 100 --no-pager

# Check if port is in use
sudo lsof -i :5000

# Verify Python environment
ls -la /opt/photo-registration-form/venv/

# Test manually
cd /opt/photo-registration-form
source venv/bin/activate
python app.py
```

### Database locked

```bash
# Check for processes using database
sudo lsof /opt/photo-registration-form/registrations.db

# Restart service
sudo systemctl restart photo-registration
```

### Permission denied errors

```bash
# Fix ownership
sudo chown -R www-data:www-data /opt/photo-registration-form

# Fix log directory
sudo chown -R www-data:www-data /var/log/photo-registration
```

### Can't access from browser

```bash
# Check service is running
sudo systemctl status photo-registration

# Test locally
curl http://127.0.0.1:5000/health

# Check firewall (if applicable)
sudo ufw status
```

## 📊 Monitoring

```bash
# Check resource usage
sudo systemctl status photo-registration

# Check worker processes
ps aux | grep gunicorn

# Monitor logs in real-time
sudo journalctl -u photo-registration -f
```

## 🔄 Backup & Restore

### Backup

```bash
# Create backup directory
mkdir -p ~/photo-registration-backup

# Backup database
sudo cp /opt/photo-registration-form/registrations.db \
    ~/photo-registration-backup/registrations.db.$(date +%Y%m%d_%H%M%S)

# Backup configuration
sudo cp /opt/photo-registration-form/.env \
    ~/photo-registration-backup/.env.$(date +%Y%m%d_%H%M%S)
```

### Restore

```bash
# Stop service
sudo systemctl stop photo-registration

# Restore database
sudo cp ~/photo-registration-backup/registrations.db.TIMESTAMP \
    /opt/photo-registration-form/registrations.db

# Fix permissions
sudo chown www-data:www-data /opt/photo-registration-form/registrations.db

# Start service
sudo systemctl start photo-registration
```

## 📱 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Registration form |
| `/register` | POST | Submit registration |
| `/registrations` | GET | List all registrations (JSON) |
| `/health` | GET | Health check |

## 🔐 Security Checklist

- [ ] Changed SECRET_KEY in `.env`
- [ ] Firewall configured (only allow necessary ports)
- [ ] Regular database backups
- [ ] SSL/TLS via Cloudflare Tunnel
- [ ] Service running as www-data (not root)
- [ ] Log files secured (owned by www-data)

## 💡 Tips

- Backup database before updates
- Monitor logs after updates
- Test locally before configuring tunnel
- Keep SECRET_KEY secure
- Regular backups recommended
- Check service status after server reboot

---

For detailed documentation, see [README.md](README.md)
