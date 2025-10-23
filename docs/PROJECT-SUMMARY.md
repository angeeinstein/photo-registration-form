# Photo Registration Form - Project Summary

## 📋 Project Overview

A production-ready Flask web application for collecting photo registration information at fair events. Features a fully automated installation system, database management, and public access via Cloudflare Tunnel.

**Version**: 1.0.0  
**Date**: October 21, 2025  
**Status**: Production Ready ✅

## 🎯 Purpose

Event photographers can use this system to:
1. Collect visitor information (first name, last name, email)
2. Manage registrations in a database
3. Access registration data for photo delivery

## 🏗️ Architecture

```
┌─────────────────┐
│  Cloudflare     │
│    Tunnel       │ (HTTPS)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Gunicorn      │ (127.0.0.1:5000)
│   WSGI Server   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Flask App      │
│   (app.py)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQLite DB      │
│ (registrations) │
└─────────────────┘
```

## 📁 Project Structure

```
photo-registration-form/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── gunicorn_config.py          # Gunicorn WSGI configuration
├── photo-registration.service  # systemd service template
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
│
├── templates/
│   └── index.html             # Registration form HTML
│
├── install.sh                 # Automated installation script ⭐
├── uninstall.sh              # Removal script
├── test-installation.sh      # Testing script
│
├── README.md                  # Main documentation
├── QUICK-REFERENCE.md        # Command reference
├── CONTRIBUTING.md           # Contribution guidelines
├── CHANGELOG.md              # Version history
└── PROJECT-SUMMARY.md        # This file
```

## 🔑 Key Features

### Application Features
- ✅ Simple registration form (3 fields)
- ✅ Real-time form validation
- ✅ Responsive mobile-friendly design
- ✅ Success/error notifications
- ✅ Admin view for all registrations
- ✅ Health check endpoint
- ✅ Timestamp tracking

### Installation Features
- ✅ Interactive menu system
- ✅ One-command installation
- ✅ Automatic dependency installation
- ✅ Update mechanism with data preservation
- ✅ Database backup during updates
- ✅ Automatic SECRET_KEY generation
- ✅ systemd service integration
- ✅ **Nginx configuration automation**
- ✅ **Hostname setup wizard**
- ✅ **Settings management menu**
- ✅ **Integrated uninstall with backup**
- ✅ **System status viewer**
- ✅ Complete removal option
- ✅ OS detection (Ubuntu, Debian, CentOS, RHEL, Fedora)

### Deployment Features
- ✅ Production-ready with Gunicorn
- ✅ systemd service management
- ✅ Automatic restart on failure
- ✅ Log rotation support
- ✅ Cloudflare Tunnel compatible
- ✅ Runs as non-root user (www-data)

## 🚀 Installation

### Quick Install
```bash
git clone https://github.com/angeeinstein/photo-registration-form.git
cd photo-registration-form
sudo bash install.sh
# Choose option 1 for fresh installation
```

### Interactive Menu

The install script provides an interactive menu system:

**Fresh Installation Menu:**
```
1) Fresh installation
2) Cancel
```

**Existing Installation Menu:**
```
1) Update installation (git pull + restart service)
2) Reinstall (keep database and .env)
3) Configure settings (hostname, nginx, etc.)
4) Complete removal (uninstall everything)
5) View status
6) Cancel
```

**Settings Configuration Menu:**
```
1) Change hostname for Nginx
2) Install/Update Nginx configuration
3) Edit .env file
4) Change SECRET_KEY
5) Back to main menu
```

### What Happens During Installation

1. **System Check**: Validates OS and Python version
2. **Dependencies**: Installs required system packages
3. **Application**: Copies files to `/opt/photo-registration-form/`
4. **Virtual Environment**: Creates Python venv with packages
5. **Database**: Initializes SQLite database
6. **Configuration**: Creates `.env` with secure SECRET_KEY
7. **Service**: Installs and starts systemd service
8. **Verification**: Checks service status

**Time**: ~2-5 minutes depending on system

## 🔄 Update Process

```bash
cd photo-registration-form
git pull
sudo bash install.sh  # Option 1: Update
```

### What Happens During Update

1. **Service Stop**: Gracefully stops the application
2. **Database Backup**: Creates timestamped backup
3. **Config Preservation**: Backs up `.env` file
4. **Git Pull**: Fetches latest changes
5. **Config Restore**: Restores `.env` file
6. **Dependencies**: Updates Python packages
7. **Service Restart**: Starts updated application
8. **Verification**: Checks service status

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | Flask | 3.0.0 |
| Database | SQLite | 3.x |
| ORM | SQLAlchemy | 3.1.1 |
| WSGI Server | Gunicorn | 21.2.0 |
| Service | systemd | - |
| Tunnel | Cloudflare | Latest |
| Frontend | HTML/CSS/JS | Vanilla |

## 📊 Database Schema

### Registration Table

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary Key, Auto-increment |
| first_name | String(100) | NOT NULL |
| last_name | String(100) | NOT NULL |
| email | String(120) | NOT NULL |
| registered_at | DateTime | NOT NULL, Default: UTC Now |

## 🌐 API Endpoints

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/` | GET | Registration form | HTML |
| `/register` | POST | Submit registration | JSON (201) |
| `/registrations` | GET | List all registrations | JSON (200) |
| `/health` | GET | Health check | JSON (200) |

## 📦 Installation Locations

| Item | Path |
|------|------|
| Application | `/opt/photo-registration-form/` |
| Database | `/opt/photo-registration-form/registrations.db` |
| Virtual Environment | `/opt/photo-registration-form/venv/` |
| Configuration | `/opt/photo-registration-form/.env` |
| Service File | `/etc/systemd/system/photo-registration.service` |
| Access Logs | `/var/log/photo-registration/access.log` |
| Error Logs | `/var/log/photo-registration/error.log` |
| PID File | `/var/run/photo-registration/gunicorn.pid` |

## 🔒 Security Features

- ✅ Automatic SECRET_KEY generation (64-char hex)
- ✅ Non-root service user (www-data)
- ✅ Environment variable configuration
- ✅ Input validation (client & server)
- ✅ HTTPS via Cloudflare Tunnel
- ✅ Email format validation
- ✅ Private log directories
- ✅ Secure default permissions

## 🎨 User Interface

- **Design**: Modern gradient theme (purple)
- **Layout**: Centered card-based
- **Responsive**: Mobile-first approach
- **Validation**: Real-time error messages
- **Feedback**: Success/error notifications
- **Accessibility**: Semantic HTML, ARIA labels
- **Animation**: Smooth transitions

## 📈 Scalability Notes

### Current Setup (SQLite)
- **Good for**: Small to medium events (< 1000 registrations/hour)
- **Concurrent writes**: Limited (SQLite limitation)
- **Storage**: Single file, easy backup

### Scaling Options (Future)
- **PostgreSQL**: For high-traffic scenarios
- **Load Balancer**: Multiple Gunicorn instances
- **Redis**: Session management, caching
- **Nginx**: Reverse proxy, static files
- **Docker**: Containerization

## 🧪 Testing

### Automated Tests
```bash
sudo bash test-installation.sh
```

Tests:
- Service status
- Health endpoint
- Main page
- Registration submission
- Registrations list
- Database file
- Log directories

### Manual Testing
```bash
# Health check
curl http://127.0.0.1:5000/health

# Test registration
curl -X POST http://127.0.0.1:5000/register \
  -d "first_name=Test&last_name=User&email=test@example.com"

# View registrations
curl http://127.0.0.1:5000/registrations
```

## 📝 Maintenance

### Regular Tasks
- **Daily**: Monitor logs for errors
- **Weekly**: Check service status, disk space
- **Monthly**: Database backup, log rotation
- **As Needed**: Software updates

### Backup Strategy
```bash
# Manual backup
sudo cp /opt/photo-registration-form/registrations.db \
    ~/backup/registrations.db.$(date +%Y%m%d)

# Automated (add to cron)
0 2 * * * sudo cp /opt/photo-registration-form/registrations.db \
    /backup/registrations.db.$(date +\%Y\%m\%d)
```

## 🔮 Future Enhancements

### Planned Features (See CHANGELOG.md)
- Rate limiting
- Admin authentication
- CSV export
- Email confirmations
- PostgreSQL support
- Docker deployment
- Multi-language support
- Duplicate detection

## 📞 Support Resources

| Resource | Link/Command |
|----------|--------------|
| Documentation | `README.md` |
| Quick Reference | `QUICK-REFERENCE.md` |
| Contributing | `CONTRIBUTING.md` |
| Changelog | `CHANGELOG.md` |
| Service Logs | `sudo journalctl -u photo-registration -f` |
| Application Logs | `sudo tail -f /var/log/photo-registration/error.log` |

## 🎯 Use Cases

1. **Fair/Event Photography**
   - Visitors register at photo booth
   - Photographers collect emails for delivery
   - Simple, quick registration process

2. **Festival Photo Distribution**
   - Multiple photo stations
   - Centralized registration
   - Easy data export

3. **Corporate Event Photos**
   - Attendee registration
   - Professional photo delivery
   - Data management

## ⚡ Performance

### Expected Performance
- **Response Time**: < 100ms (local)
- **Throughput**: 100+ registrations/minute
- **Database**: Handles 10,000+ registrations efficiently
- **Memory**: ~50-100MB RAM usage
- **Workers**: Auto-calculated (CPU cores × 2 + 1)

### Optimization Tips
- Enable log rotation
- Regular database vacuuming
- Monitor worker count
- Consider PostgreSQL for high traffic

## 🏆 Best Practices

1. **Backup**: Regular database backups
2. **Monitoring**: Check logs regularly
3. **Updates**: Use install.sh for updates
4. **Security**: Keep SECRET_KEY secure
5. **Testing**: Test locally before production
6. **Documentation**: Document custom changes

## 📋 Compatibility

### Operating Systems
- ✅ Ubuntu 18.04+
- ✅ Debian 10+
- ✅ CentOS 7+
- ✅ RHEL 7+
- ✅ Fedora 30+

### Python Versions
- ✅ Python 3.8
- ✅ Python 3.9
- ✅ Python 3.10
- ✅ Python 3.11
- ✅ Python 3.12

## 🎓 Learning Resources

### For Flask Development
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)

### For Deployment
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [systemd Service Management](https://systemd.io/)

### For Tunneling
- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

---

**Last Updated**: October 21, 2025  
**Maintainer**: angeeinstein  
**Repository**: https://github.com/angeeinstein/photo-registration-form
