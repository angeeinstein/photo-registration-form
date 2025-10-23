# Photo Registration Form - Complete File Index

## 📦 Project Files (18 files)

### Core Application Files (5)
```
app.py                      # Main Flask application with routes, database models, and API endpoints
requirements.txt            # Python dependencies (Flask, SQLAlchemy, Gunicorn, etc.)
gunicorn_config.py          # Gunicorn WSGI server configuration
photo-registration.service  # systemd service template for automatic startup
nginx.conf.template         # Nginx reverse proxy configuration template
```

### Template Files (1)
```
templates/
  └── index.html           # Responsive registration form with validation and modern UI
```

### Installation & Maintenance Scripts (3)
```
install.sh                 # ⭐ Main installation script - interactive menu for install, update, configure, uninstall
uninstall.sh              # Standalone removal script (also integrated in install.sh)
test-installation.sh      # Automated testing script to verify installation
```

### Configuration Files (2)
```
.env.example              # Environment variables template (SECRET_KEY, DATABASE_URI, etc.)
.gitignore                # Git ignore rules (excludes venv, .db, .env, logs, etc.)
```

### Documentation Files (6)
```
README.md                 # Main documentation with installation and usage instructions
QUICK-REFERENCE.md        # Command reference guide for daily operations
CONTRIBUTING.md           # Guidelines for contributing while maintaining install.sh compatibility
CHANGELOG.md              # Version history and release notes
PROJECT-SUMMARY.md        # Comprehensive project overview and architecture
LICENSE                   # MIT License
```

## 📁 Runtime Files (Created During Installation)

These files are created when you run `install.sh` and are excluded from git:

### Application Runtime
```
/opt/photo-registration-form/
  ├── venv/                              # Python virtual environment
  ├── registrations.db                   # SQLite database
  ├── .env                               # Environment configuration (from .env.example)
  └── (all project files copied here)
```

### System Integration
```
/etc/systemd/system/
  └── photo-registration.service         # Installed systemd service

/etc/nginx/
  └── sites-available/
      └── photo-registration             # Nginx configuration (if configured)
  └── sites-enabled/
      └── photo-registration             # Symlink to sites-available

/var/log/photo-registration/
  ├── access.log                         # Gunicorn access logs
  └── error.log                          # Gunicorn error logs

/var/log/nginx/
  ├── photo-registration-access.log      # Nginx access logs (if using nginx)
  └── photo-registration-error.log       # Nginx error logs (if using nginx)

/var/run/photo-registration/
  └── gunicorn.pid                       # Process ID file
```

## 🗂️ File Categories by Purpose

### Installation System
- `install.sh` - Main installation automation
- `uninstall.sh` - Removal automation
- `test-installation.sh` - Verification automation

### Application Code
- `app.py` - Backend application
- `templates/index.html` - Frontend UI
- `requirements.txt` - Dependencies

### Configuration
- `gunicorn_config.py` - WSGI server config
- `photo-registration.service` - Service config
- `.env.example` - Environment template
- `nginx.conf.template` - Nginx proxy template

### Documentation
- `README.md` - Main docs
- `QUICK-REFERENCE.md` - Quick commands
- `CONTRIBUTING.md` - Dev guidelines
- `PROJECT-SUMMARY.md` - Project overview
- `CHANGELOG.md` - Version history

### Repository Management
- `.gitignore` - Git exclusions
- `LICENSE` - MIT License

## 📊 File Statistics

| Category | Files | Lines (approx) |
|----------|-------|----------------|
| Application | 5 | 450 |
| Templates | 1 | 250 |
| Scripts | 3 | 1200 |
| Config | 2 | 150 |
| Documentation | 6 | 1500 |
| Total | 18 | ~3550 |

## 🔄 File Lifecycle

### Fresh Installation
1. Clone repository → Get all 17 files
2. Run `install.sh` → Creates runtime files
3. Service starts → Creates logs and PID

### Update Process
1. Git pull → Updates source files
2. Run `install.sh` → Preserves `.env` and `.db`
3. Service restarts → Updates application

### Removal
1. Run `uninstall.sh` → Optionally backs up database
2. Removes runtime files → Cleans system
3. Repository intact → Can reinstall anytime

## 📝 File Descriptions

### app.py (Main Application)
- Flask app initialization
- Database model (Registration)
- Routes: /, /register, /registrations, /health
- Form validation and error handling
- Database initialization function

### templates/index.html (Frontend)
- Responsive registration form
- Client-side validation
- AJAX form submission
- Success/error notifications
- Modern gradient design

### install.sh (Installation Script)
- OS detection (Ubuntu, Debian, CentOS, RHEL, Fedora)
- System dependency installation
- Python version checking
- Virtual environment creation
- Database initialization
- Service installation
- **Interactive menu system**
- **Settings configuration wizard**
- **Nginx installation and setup**
- **Hostname configuration**
- Update mechanism
- Reinstall option
- **Integrated uninstall**
- **System status viewer**

### gunicorn_config.py (WSGI Config)
- Worker configuration (CPU-based)
- Binding to 127.0.0.1:5000
- Log file paths
- Process naming
- Timeout settings

### photo-registration.service (systemd Service)
- Service configuration
- User/group (www-data)
- Environment variables
- Auto-restart policy
- Dependencies

### nginx.conf.template (Nginx Template)
- Reverse proxy configuration
- Hostname placeholder (SERVER_NAME)
- HTTP configuration
- HTTPS configuration (commented)
- Proxy headers
- SSL settings template
- Log file paths

### requirements.txt (Dependencies)
- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- gunicorn 21.2.0
- python-dotenv 1.0.0
- email-validator 2.1.0

### .env.example (Environment Template)
- SECRET_KEY placeholder
- FLASK_ENV setting
- DATABASE_URI options
- Gunicorn settings

### test-installation.sh (Test Suite)
- Service status check
- Health endpoint test
- Main page test
- Registration endpoint test
- Database verification
- Log directory check

### uninstall.sh (Removal Script)
- Service stop/disable
- Database backup option
- File removal
- Cleanup verification

## 🎯 Key Features by File

| Feature | Primary File | Supporting Files |
|---------|--------------|------------------|
| Web UI | templates/index.html | app.py |
| Registration Logic | app.py | requirements.txt |
| Database | app.py | (registrations.db runtime) |
| Production Server | gunicorn_config.py | photo-registration.service |
| Installation | install.sh | uninstall.sh, test-installation.sh |
| Documentation | README.md | All .md files |

## 🔐 Security-Sensitive Files

| File | Security Concern | Mitigation |
|------|------------------|------------|
| .env | Contains SECRET_KEY | In .gitignore, created from example |
| registrations.db | Contains user emails | In .gitignore, proper permissions |
| photo-registration.service | May contain secrets | SECRET_KEY auto-generated |

## 🚀 File Usage Workflow

### Developer Workflow
1. Edit `app.py` or `templates/index.html`
2. Update `requirements.txt` if needed
3. Update `CHANGELOG.md`
4. Test with `test-installation.sh`
5. Commit and push

### User Workflow
1. Clone repository
2. Run `install.sh`
3. (Optional) Edit `.env`
4. Access application

### Update Workflow
1. Git pull
2. Run `install.sh` → Choose "Update"
3. Service restarts automatically

## 📌 Important Notes

- **Never commit**: `.env`, `*.db`, `venv/`
- **Always backup**: `registrations.db` before updates
- **Keep secure**: SECRET_KEY in `.env`
- **Test locally**: Before deploying updates
- **Read CONTRIBUTING.md**: Before making changes

---

**Total Project Size**: ~50KB (source files only)  
**With Dependencies**: ~30MB (including venv)  
**With Runtime Data**: Varies by usage

**Last Updated**: October 21, 2025
