# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-21

### Added
- Initial release
- Flask web application with registration form
- SQLite database integration with SQLAlchemy
- Responsive HTML/CSS registration form
- Email validation (client and server-side)
- Gunicorn WSGI server configuration
- systemd service integration
- Automated installation script (`install.sh`)
- Support for installation, updates, and removal
- Database backup during updates
- Health check endpoint (`/health`)
- Admin registrations view endpoint (`/registrations`)
- Environment variable configuration via `.env` file
- Comprehensive README with setup instructions
- Cloudflare Tunnel compatibility
- Auto-generated SECRET_KEY during installation

### Features
- Registration fields: first name, last name, email
- Timestamp tracking for each registration
- Form validation with error messages
- Success/error notifications
- Mobile-responsive design
- Automatic service restart on failure
- Log rotation support
- Production-ready configuration

### Installation Script Features
- Automatic dependency installation
- OS detection (Ubuntu, Debian, CentOS, RHEL, Fedora)
- Python version validation (3.8+)
- Virtual environment creation
- Database initialization
- Service installation and configuration
- Update mechanism with database backup
- Reinstall option (preserving data)
- Complete removal option
- Interactive menus for existing installations

## [Unreleased]

### Added
- Interactive menu system in `install.sh` for better user experience
- Settings configuration menu in `install.sh`
- Hostname configuration option
- Automated Nginx installation and configuration
- Nginx reverse proxy template (`nginx.conf.template`)
- Ability to edit .env file from install script
- SECRET_KEY regeneration feature
- System status view in install script
- Integrated uninstall functionality in main script
- Database backup prompt before uninstall
- Color-coded menu system for better readability
- **Complete systemd service management documentation** (`SYSTEMD-NGINX-MANAGEMENT.md`)

### Changed
- `install.sh` now shows interactive menu instead of command-line arguments
- Uninstall functionality integrated into main install script
- Enhanced user prompts with better descriptions
- Improved menu navigation with numbered options

### Features
- **Full systemd service lifecycle management** (install, enable, start, stop, disable, remove)
- **Complete Nginx configuration management** (install package, configure, enable, reload, remove)
- Nginx configuration with automatic hostname setup
- One-script management for all operations (install, update, configure, uninstall)
- View system status without checking multiple locations
- Change settings without editing files manually

### Documentation
- Added comprehensive systemd and Nginx management guide
- Documented all automated configuration steps
- Clarified what install.sh manages vs. manual configuration

## [1.0.0] - 2025-10-21
- Rate limiting for form submissions
- Admin authentication for `/registrations` endpoint
- Export registrations to CSV
- Email confirmation for registrants
- PostgreSQL support for high-traffic scenarios
- Docker containerization
- Nginx reverse proxy configuration
- SSL certificate management with Let's Encrypt
- Multi-language support
- Custom theming options
- Registration search and filtering
- Duplicate email detection
