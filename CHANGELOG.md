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
- **Post-installation configuration wizard** - Interactive setup after installation
- **Automatic Nginx installation** - No prompts, installed with system dependencies
- **Port conflict detection** - Checks port 80 availability automatically
- Interactive menu system in `install.sh` for better user experience
- Settings configuration menu in `install.sh`
- **Network binding configuration option** in install script
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
- **Separate server tunnel setup guide** (`TUNNEL-ON-SEPARATE-SERVER.md`)
- **GUNICORN_BIND environment variable support** in gunicorn_config.py
- **EnvironmentFile support** in systemd service

### Changed
- `install.sh` now shows interactive menu instead of command-line arguments
- **Nginx is now installed automatically during fresh installation** (no prompts)
- **Post-installation wizard runs automatically** after installation
- **Smart binding detection** - Warns if Flask binds to network when using Nginx
- Uninstall functionality integrated into main install script
- Enhanced user prompts with better descriptions
- Improved menu navigation with numbered options
- **gunicorn_config.py now reads GUNICORN_BIND from environment** (default: 127.0.0.1:5000)
- **systemd service now loads .env file** for configuration

### Features
- **Zero-prompt installation** - All dependencies installed automatically
- **Post-installation wizard** guides configuration:
  - Network binding setup (localhost vs network access)
  - Nginx configuration with hostname
  - Port conflict detection and resolution
  - Flask binding validation for Nginx setup
- **Configurable network binding** (localhost only, network access, port 80, custom)
- **Automatic Cloudflare Tunnel configuration suggestions** based on binding
- **Port 80 support** with CAP_NET_BIND_SERVICE capability
- **Full systemd service lifecycle management** (install, enable, start, stop, disable, remove)
- **Complete Nginx configuration management** (install package, configure, enable, reload, remove)
- Nginx configuration with automatic hostname setup
- One-script management for all operations (install, update, configure, uninstall)
- View system status without checking multiple locations
- Change settings without editing files manually

### Documentation
- Added comprehensive systemd and Nginx management guide
- Added separate server Cloudflare Tunnel setup guide
- Documented automated installation process
- Clarified network binding options
- Added security considerations for network exposure
- Updated README with zero-configuration installation instructions

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
