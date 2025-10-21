#!/bin/bash

#############################################
# Photo Registration Form - Installation Script
# Handles: Fresh install, updates, settings, and removal
#############################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="photo-registration-form"
INSTALL_DIR="/opt/${APP_NAME}"
SERVICE_NAME="photo-registration"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
LOG_DIR="/var/log/${SERVICE_NAME}"
RUN_DIR="/var/run/${SERVICE_NAME}"
VENV_DIR="${INSTALL_DIR}/venv"
DB_FILE="${INSTALL_DIR}/registrations.db"
ENV_FILE="${INSTALL_DIR}/.env"
NGINX_CONF="/etc/nginx/sites-available/${SERVICE_NAME}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${SERVICE_NAME}"
SYSTEM_USER="www-data"
SYSTEM_GROUP="www-data"
MIN_PYTHON_VERSION="3.8"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${CYAN}======================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}======================================${NC}\n"
}

print_menu() {
    echo -e "${BLUE}$1${NC}"
}

# Check if script is run as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Detect OS
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    else
        print_error "Cannot detect OS. /etc/os-release not found."
        exit 1
    fi
    print_info "Detected OS: $OS $OS_VERSION"
}

# Check Python version
check_python() {
    print_info "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed!"
        return 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    print_info "Found Python version: $PYTHON_VERSION"
    
    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 8 ]]; then
        print_error "Python 3.8 or higher is required. Current: $PYTHON_VERSION"
        return 1
    fi
    
    return 0
}

# Install system dependencies
install_dependencies() {
    print_header "Installing System Dependencies"
    
    case $OS in
        ubuntu|debian)
            print_info "Updating package lists..."
            apt-get update -qq
            
            print_info "Installing required packages (Python, Nginx, etc.)..."
            apt-get install -y \
                python3 \
                python3-pip \
                python3-venv \
                python3-dev \
                build-essential \
                git \
                curl \
                wget \
                sqlite3 \
                nginx \
                || { print_error "Failed to install dependencies"; exit 1; }
            ;;
        centos|rhel|fedora)
            print_info "Installing required packages (Python, Nginx, etc.)..."
            if command -v dnf &> /dev/null; then
                dnf install -y \
                    python3 \
                    python3-pip \
                    python3-devel \
                    gcc \
                    git \
                    curl \
                    wget \
                    sqlite \
                    nginx \
                    || { print_error "Failed to install dependencies"; exit 1; }
            else
                yum install -y \
                    python3 \
                    python3-pip \
                    python3-devel \
                    gcc \
                    git \
                    curl \
                    wget \
                    sqlite \
                    nginx \
                    || { print_error "Failed to install dependencies"; exit 1; }
            fi
            ;;
        *)
            print_warning "Unsupported OS: $OS. Attempting to continue..."
            ;;
    esac
    
    print_success "System dependencies installed (including Nginx)"
}

# Check if installation exists
check_existing_installation() {
    if [[ -d "$INSTALL_DIR" ]] || [[ -f "$SERVICE_FILE" ]]; then
        return 0  # Installation exists
    else
        return 1  # No installation
    fi
}

# Show main menu
show_main_menu() {
    if check_existing_installation; then
        print_header "Photo Registration Form - Management Menu"
        print_info "Installation detected at: $INSTALL_DIR"
        
        # Check if git repo
        if [[ -d "${INSTALL_DIR}/.git" ]]; then
            print_success "Git repository detected - updates available"
        else
            print_warning "Not a git repository - only dependency updates available"
        fi
        
        echo ""
        print_menu "1) Update installation (dependencies + restart)"
        print_menu "2) Reinstall (keep database and .env)"
        print_menu "3) Configure settings (hostname, nginx, etc.)"
        print_menu "4) Complete removal (uninstall everything)"
        print_menu "5) View status"
        print_menu "6) Cancel"
        echo ""
        read -p "Enter your choice [1-6]: " choice
        
        case $choice in
            1)
                update_installation
                ;;
            2)
                reinstall_installation
                ;;
            3)
                configure_settings
                ;;
            4)
                remove_installation
                ;;
            5)
                show_status
                ;;
            6)
                print_info "Cancelled"
                exit 0
                ;;
            *)
                print_error "Invalid choice"
                exit 1
                ;;
        esac
    else
        print_header "Photo Registration Form - Installation"
        print_menu "1) Fresh installation"
        print_menu "2) Cancel"
        echo ""
        read -p "Enter your choice [1-2]: " choice
        
        case $choice in
            1)
                fresh_installation
                ;;
            2)
                print_info "Installation cancelled"
                exit 0
                ;;
            *)
                print_error "Invalid choice"
                exit 1
                ;;
        esac
    fi
}

# Update existing installation
update_installation() {
    print_header "Updating Installation"
    
    # Stop service if running
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        print_info "Stopping service..."
        systemctl stop ${SERVICE_NAME}
    fi
    
    # Backup database if exists
    if [[ -f "$DB_FILE" ]]; then
        BACKUP_FILE="${DB_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        print_info "Backing up database to ${BACKUP_FILE}..."
        cp "$DB_FILE" "$BACKUP_FILE"
        print_success "Database backed up"
    fi
    
    # Update from git
    print_info "Pulling latest changes from git..."
    
    # Get the directory where the script is running from (source directory)
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    # Preserve .env from install directory
    cd "$INSTALL_DIR"
    if [[ -f ".env" ]]; then
        print_info "Preserving .env file..."
        cp .env .env.backup
    fi
    
    # Check if the SCRIPT directory (where we're running from) is a git repository
    cd "$SCRIPT_DIR"
    if [[ -d ".git" ]]; then
        print_info "Git repository detected at source directory, pulling updates..."
        git pull || {
            print_error "Git pull failed. Check your repository."
            cd "$INSTALL_DIR"
            if [[ -f ".env.backup" ]]; then
                mv .env.backup .env
            fi
            exit 1
        }
        
        # Copy updated files to install directory (excluding .git, db, venv)
        print_info "Copying updated files to installation directory..."
        rsync -av --exclude='.git' --exclude='*.db' --exclude='venv' --exclude='__pycache__' "$SCRIPT_DIR/" "$INSTALL_DIR/" || {
            cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/" 2>/dev/null || true
        }
    else
        print_warning "Not running from a git repository. Skipping git pull."
        print_info "To enable git updates:"
        print_info "  1. Clone the repository: git clone <your-repo-url> ~/photo-registration-form"
        print_info "  2. Run updates from there: cd ~/photo-registration-form && sudo ./install.sh"
        echo ""
        read -p "Continue with dependency updates only? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            cd "$INSTALL_DIR"
            if [[ -f ".env.backup" ]]; then
                rm .env.backup
            fi
            exit 0
        fi
    fi
    
    # Restore .env
    cd "$INSTALL_DIR"
    if [[ -f ".env.backup" ]]; then
        mv .env.backup .env
        print_success ".env file restored"
    fi
    
    # Update Python dependencies
    print_info "Updating Python dependencies..."
    source "${VENV_DIR}/bin/activate"
    pip install --upgrade pip
    pip install -r requirements.txt --upgrade
    deactivate
    
    # Restart service
    print_info "Restarting service..."
    systemctl daemon-reload
    systemctl start ${SERVICE_NAME}
    systemctl status ${SERVICE_NAME} --no-pager
    
    print_success "Update completed successfully!"
    print_info "Service status:"
    systemctl status ${SERVICE_NAME} --no-pager -l
    
    exit 0
}

# Reinstall keeping data
reinstall_installation() {
    print_header "Reinstalling (Keeping Database and Configuration)"
    
    # Backup important files
    BACKUP_DIR="/tmp/${APP_NAME}_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    if [[ -f "$DB_FILE" ]]; then
        print_info "Backing up database..."
        cp "$DB_FILE" "$BACKUP_DIR/"
    fi
    
    if [[ -f "${INSTALL_DIR}/.env" ]]; then
        print_info "Backing up .env file..."
        cp "${INSTALL_DIR}/.env" "$BACKUP_DIR/"
    fi
    
    print_success "Backups created in $BACKUP_DIR"
    
    # Remove installation
    remove_installation_silent
    
    # Fresh install
    fresh_installation
    
    # Restore backups
    if [[ -f "${BACKUP_DIR}/registrations.db" ]]; then
        print_info "Restoring database..."
        cp "${BACKUP_DIR}/registrations.db" "$DB_FILE"
        chown ${SYSTEM_USER}:${SYSTEM_GROUP} "$DB_FILE"
    fi
    
    if [[ -f "${BACKUP_DIR}/.env" ]]; then
        print_info "Restoring .env file..."
        cp "${BACKUP_DIR}/.env" "${INSTALL_DIR}/.env"
        chown ${SYSTEM_USER}:${SYSTEM_GROUP} "${INSTALL_DIR}/.env"
    fi
    
    # Restart service
    systemctl restart ${SERVICE_NAME}
    
    print_success "Reinstallation completed with data preserved!"
    exit 0
}

# Configure settings (hostname, nginx, etc.)
configure_settings() {
    print_header "Configure Settings"
    
    echo "Available settings to configure:"
    echo ""
    print_menu "1) Configure network binding (localhost vs network access)"
    print_menu "2) Change hostname for Nginx"
    print_menu "3) Install/Update Nginx configuration"
    print_menu "4) Edit .env file"
    print_menu "5) Change SECRET_KEY"
    print_menu "6) Back to main menu"
    echo ""
    read -p "Enter your choice [1-6]: " choice
    
    case $choice in
        1)
            configure_network_binding
            ;;
        2)
            configure_hostname
            ;;
        3)
            install_nginx_config
            ;;
        4)
            edit_env_file
            ;;
        5)
            change_secret_key
            ;;
        6)
            main
            ;;
        *)
            print_error "Invalid choice"
            configure_settings
            ;;
    esac
}

# Configure network binding
configure_network_binding() {
    print_header "Configure Network Binding"
    
    echo "Current binding configuration:"
    if [[ -f "$ENV_FILE" ]]; then
        CURRENT_BIND=$(grep "^GUNICORN_BIND=" "$ENV_FILE" | cut -d= -f2)
        if [[ -z "$CURRENT_BIND" ]]; then
            CURRENT_BIND="127.0.0.1:5000 (default)"
        fi
        echo "  $CURRENT_BIND"
    else
        echo "  127.0.0.1:5000 (default)"
    fi
    
    echo ""
    echo "Choose binding configuration:"
    echo ""
    print_menu "1) Localhost only - 127.0.0.1:5000 (Most secure, for Cloudflare Tunnel on same server)"
    print_menu "2) Network access - 0.0.0.0:5000 (For Cloudflare Tunnel on different server)"
    print_menu "3) Network on port 80 - 0.0.0.0:80 (For direct access without port, requires nginx or privileges)"
    print_menu "4) Custom binding"
    print_menu "5) Back to settings menu"
    echo ""
    read -p "Enter your choice [1-5]: " bind_choice
    
    case $bind_choice in
        1)
            NEW_BIND="127.0.0.1:5000"
            print_info "Setting to localhost only (127.0.0.1:5000)"
            ;;
        2)
            NEW_BIND="0.0.0.0:5000"
            print_info "Setting to network access (0.0.0.0:5000)"
            print_warning "Application will be accessible from LAN"
            ;;
        3)
            NEW_BIND="0.0.0.0:80"
            print_info "Setting to network port 80 (0.0.0.0:80)"
            print_warning "Running on port 80 requires special configuration"
            print_warning "Consider using nginx as reverse proxy instead"
            ;;
        4)
            read -p "Enter custom bind address (e.g., 192.168.1.104:5000): " NEW_BIND
            if [[ -z "$NEW_BIND" ]]; then
                print_error "Binding cannot be empty"
                read -p "Press Enter to continue..."
                configure_network_binding
                return 1
            fi
            ;;
        5)
            configure_settings
            return 0
            ;;
        *)
            print_error "Invalid choice"
            configure_network_binding
            return 1
            ;;
    esac
    
    # Update .env file
    if [[ ! -f "$ENV_FILE" ]]; then
        print_error ".env file not found at $ENV_FILE"
        read -p "Press Enter to continue..."
        configure_settings
        return 1
    fi
    
    # Update or add GUNICORN_BIND
    if grep -q "^GUNICORN_BIND=" "$ENV_FILE"; then
        sed -i "s|^GUNICORN_BIND=.*|GUNICORN_BIND=$NEW_BIND|" "$ENV_FILE"
    else
        echo "GUNICORN_BIND=$NEW_BIND" >> "$ENV_FILE"
    fi
    
    print_success "Binding updated to: $NEW_BIND"
    
    # If using port 80, check for privileges
    if [[ "$NEW_BIND" == *":80" ]]; then
        echo ""
        print_warning "Port 80 requires special privileges!"
        echo "Option 1: Run with CAP_NET_BIND_SERVICE capability (recommended)"
        echo "Option 2: Use nginx as reverse proxy (recommended)"
        echo "Option 3: Run as root (NOT recommended)"
        echo ""
        echo "The service file needs to be updated. Do you want to add CAP_NET_BIND_SERVICE?"
        read -p "Add capability? (y/n): " add_cap
        
        if [[ "$add_cap" == "y" ]] || [[ "$add_cap" == "Y" ]]; then
            # Add capability to service file
            if grep -q "^AmbientCapabilities=" "$SERVICE_FILE"; then
                sed -i "s|^AmbientCapabilities=.*|AmbientCapabilities=CAP_NET_BIND_SERVICE|" "$SERVICE_FILE"
            else
                sed -i "/^\[Service\]/a AmbientCapabilities=CAP_NET_BIND_SERVICE" "$SERVICE_FILE"
            fi
            systemctl daemon-reload
            print_success "Added CAP_NET_BIND_SERVICE capability"
        fi
    fi
    
    # Show Cloudflare Tunnel config suggestion
    echo ""
    print_info "For Cloudflare Tunnel configuration:"
    if [[ "$NEW_BIND" == "127.0.0.1:5000" ]]; then
        echo "  service: http://127.0.0.1:5000"
        echo "  (Tunnel must run on this server)"
    elif [[ "$NEW_BIND" == "0.0.0.0:5000" ]]; then
        # Try to detect server IP
        SERVER_IP=$(hostname -I | awk '{print $1}')
        if [[ -n "$SERVER_IP" ]]; then
            echo "  service: http://$SERVER_IP:5000"
        else
            echo "  service: http://YOUR-SERVER-IP:5000"
        fi
        echo "  (Tunnel can run on different server)"
    elif [[ "$NEW_BIND" == "0.0.0.0:80" ]]; then
        SERVER_IP=$(hostname -I | awk '{print $1}')
        if [[ -n "$SERVER_IP" ]]; then
            echo "  service: http://$SERVER_IP"
        else
            echo "  service: http://YOUR-SERVER-IP"
        fi
        echo "  (No port needed - using port 80)"
    else
        echo "  service: http://$NEW_BIND"
    fi
    
    echo ""
    print_info "Restarting service to apply changes..."
    systemctl restart ${SERVICE_NAME}
    
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        print_success "Service restarted successfully"
        
        # Test the new binding
        echo ""
        print_info "Testing new configuration..."
        sleep 2
        
        if [[ "$NEW_BIND" == "127.0.0.1:5000" ]]; then
            TEST_URL="http://127.0.0.1:5000/health"
        else
            SERVER_IP=$(hostname -I | awk '{print $1}')
            if [[ "$NEW_BIND" == *":80" ]]; then
                TEST_URL="http://${SERVER_IP}/health"
            else
                PORT=$(echo "$NEW_BIND" | cut -d: -f2)
                TEST_URL="http://${SERVER_IP}:${PORT}/health"
            fi
        fi
        
        if curl -s "$TEST_URL" > /dev/null 2>&1; then
            print_success "Application is responding at: $TEST_URL"
        else
            print_warning "Could not test $TEST_URL (this may be normal)"
        fi
    else
        print_error "Service failed to start. Check logs:"
        journalctl -u ${SERVICE_NAME} -n 20 --no-pager
    fi
    
    echo ""
    read -p "Press Enter to continue..."
    configure_settings
}

# Configure hostname
configure_hostname() {
    print_header "Configure Hostname"
    
    # Check if nginx is installed
    if ! command -v nginx &> /dev/null; then
        print_warning "Nginx is not installed!"
        print_info "Installing Nginx..."
        case $OS in
            ubuntu|debian)
                apt-get update -qq
                apt-get install -y nginx
                ;;
            centos|rhel|fedora)
                if command -v dnf &> /dev/null; then
                    dnf install -y nginx
                else
                    yum install -y nginx
                fi
                ;;
        esac
        
        if command -v nginx &> /dev/null; then
            print_success "Nginx installed successfully"
            systemctl enable nginx
        else
            print_error "Failed to install Nginx"
            read -p "Press Enter to continue..."
            configure_settings
            return 1
        fi
    fi
    
    echo "Enter your domain/hostname (e.g., photos.example.com)"
    echo "Or enter 'localhost' for local access only"
    read -p "Hostname: " hostname
    
    if [[ -z "$hostname" ]]; then
        print_error "Hostname cannot be empty"
        return 1
    fi
    
    # Ensure Flask is bound to localhost when using Nginx
    if [[ -f "$ENV_FILE" ]]; then
        CURRENT_BIND=$(grep "^GUNICORN_BIND=" "$ENV_FILE" | cut -d= -f2)
        if [[ "$CURRENT_BIND" != "127.0.0.1:5000" ]]; then
            print_warning "For Nginx reverse proxy, Flask should bind to localhost (127.0.0.1:5000)"
            read -p "Change binding now? (recommended) (y/n): " change_bind
            if [[ "$change_bind" == "y" ]] || [[ "$change_bind" == "Y" ]]; then
                sed -i "s/^GUNICORN_BIND=.*/GUNICORN_BIND=127.0.0.1:5000/" "$ENV_FILE"
                print_info "Restarting Flask service..."
                systemctl restart ${SERVICE_NAME}
                sleep 2
                print_success "Flask now bound to localhost"
            fi
        fi
    fi
    
    # Update or create nginx config
    if [[ -f "${INSTALL_DIR}/nginx.conf.template" ]]; then
        print_info "Creating nginx configuration..."
        sed "s/SERVER_NAME/$hostname/g" "${INSTALL_DIR}/nginx.conf.template" > /tmp/nginx-photo-reg.conf
        
        # Install nginx config
        print_info "Installing nginx configuration..."
        cp /tmp/nginx-photo-reg.conf "$NGINX_CONF"
        
        # Create symlink if sites-enabled directory exists
        if [[ -d "/etc/nginx/sites-enabled" ]]; then
            ln -sf "$NGINX_CONF" "$NGINX_ENABLED"
            print_success "Nginx configuration enabled"
        fi
        
        # Test nginx config
        if nginx -t 2>/dev/null; then
            print_success "Nginx configuration is valid"
            
            # Check if nginx is running
            if systemctl is-active --quiet nginx; then
                print_info "Reloading nginx..."
                systemctl reload nginx 2>&1
            else
                print_info "Starting nginx..."
                systemctl start nginx 2>&1 || {
                    print_error "Failed to start Nginx"
                    print_info "Checking port 80 availability..."
                    ss -tulpn | grep ":80 " || netstat -tulpn | grep ":80 " || true
                }
            fi
            
            if systemctl is-active --quiet nginx; then
                print_success "Nginx is running!"
            else
                print_warning "Nginx service is not running. Check: sudo systemctl status nginx"
            fi
        else
            print_error "Nginx configuration test failed"
            nginx -t
        fi
        
        rm -f /tmp/nginx-photo-reg.conf
        
        print_success "Hostname configured: $hostname"
        echo ""
        print_info "You can now access the application at: http://$hostname"
        if [[ "$hostname" != "localhost" ]]; then
            print_info "Make sure DNS is pointing to this server's IP address"
        fi
    else
        print_warning "nginx.conf.template not found. Skipping nginx configuration."
    fi
    
    echo ""
    read -p "Press Enter to continue..."
    configure_settings
}

# Install/Update Nginx configuration
install_nginx_config() {
    print_header "Install/Update Nginx Configuration"
    
    if [[ ! -f "${INSTALL_DIR}/nginx.conf.template" ]]; then
        print_error "nginx.conf.template not found in $INSTALL_DIR"
        read -p "Press Enter to continue..."
        configure_settings
        return 1
    fi
    
    # Check if nginx is installed
    if ! command -v nginx &> /dev/null; then
        print_warning "Nginx is not installed!"
        print_info "Installing Nginx..."
        case $OS in
            ubuntu|debian)
                apt-get update -qq
                apt-get install -y nginx
                ;;
            centos|rhel|fedora)
                if command -v dnf &> /dev/null; then
                    dnf install -y nginx
                else
                    yum install -y nginx
                fi
                ;;
        esac
        
        if command -v nginx &> /dev/null; then
            print_success "Nginx installed successfully"
            systemctl enable nginx
        else
            print_error "Failed to install Nginx"
            read -p "Press Enter to continue..."
            configure_settings
            return 1
        fi
    fi
    
    echo "Enter your domain/hostname (e.g., photos.example.com)"
    read -p "Hostname: " hostname
    
    if [[ -z "$hostname" ]]; then
        print_error "Hostname cannot be empty"
        read -p "Press Enter to continue..."
        configure_settings
        return 1
    fi
    
    # Ensure Flask is bound to localhost when using Nginx
    if [[ -f "$ENV_FILE" ]]; then
        CURRENT_BIND=$(grep "^GUNICORN_BIND=" "$ENV_FILE" | cut -d= -f2)
        if [[ "$CURRENT_BIND" != "127.0.0.1:5000" ]]; then
            print_warning "For Nginx reverse proxy, Flask should bind to localhost (127.0.0.1:5000)"
            read -p "Change binding now? (recommended) (y/n): " change_bind
            if [[ "$change_bind" == "y" ]] || [[ "$change_bind" == "Y" ]]; then
                sed -i "s/^GUNICORN_BIND=.*/GUNICORN_BIND=127.0.0.1:5000/" "$ENV_FILE"
                print_info "Restarting Flask service..."
                systemctl restart ${SERVICE_NAME}
                sleep 2
                print_success "Flask now bound to localhost"
            fi
        fi
    fi
    
    # Create nginx config
    print_info "Creating nginx configuration for $hostname..."
    sed "s/SERVER_NAME/$hostname/g" "${INSTALL_DIR}/nginx.conf.template" > "$NGINX_CONF"
    
    # Enable site if sites-enabled exists
    if [[ -d "/etc/nginx/sites-enabled" ]]; then
        ln -sf "$NGINX_CONF" "$NGINX_ENABLED"
        print_success "Nginx site enabled"
    fi
    
    # Test configuration
    print_info "Testing nginx configuration..."
    if nginx -t 2>/dev/null; then
        print_success "Configuration is valid"
        
        # Check if nginx is running
        if systemctl is-active --quiet nginx; then
            print_info "Reloading nginx..."
            systemctl reload nginx 2>&1
        else
            print_info "Starting nginx..."
            systemctl start nginx 2>&1 || {
                print_error "Failed to start Nginx"
                print_info "Checking port 80 availability..."
                ss -tulpn | grep ":80 " || netstat -tulpn | grep ":80 " || true
            }
        fi
        
        if systemctl is-active --quiet nginx; then
            print_success "Nginx configuration activated!"
        else
            print_warning "Nginx service is not running. Check: sudo systemctl status nginx"
        fi
    else
        print_error "Nginx configuration test failed"
        print_info "Running nginx -t to show errors:"
        nginx -t
    fi
    
    print_success "Nginx configuration installed"
    echo ""
    print_info "Configuration file: $NGINX_CONF"
    print_info "Access your application at: http://$hostname"
    
    echo ""
    read -p "Press Enter to continue..."
    configure_settings
}

# Edit .env file
edit_env_file() {
    print_header "Edit Environment Configuration"
    
    if [[ ! -f "$ENV_FILE" ]]; then
        print_error ".env file not found at $ENV_FILE"
        read -p "Press Enter to continue..."
        configure_settings
        return 1
    fi
    
    print_info "Opening .env file in editor..."
    ${EDITOR:-nano} "$ENV_FILE"
    
    print_info "Restarting service to apply changes..."
    systemctl restart ${SERVICE_NAME}
    
    print_success "Configuration updated and service restarted"
    
    echo ""
    read -p "Press Enter to continue..."
    configure_settings
}

# Change SECRET_KEY
change_secret_key() {
    print_header "Change SECRET_KEY"
    
    if [[ ! -f "$ENV_FILE" ]]; then
        print_error ".env file not found at $ENV_FILE"
        read -p "Press Enter to continue..."
        configure_settings
        return 1
    fi
    
    # Generate new secret key
    NEW_SECRET=$(openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
    
    print_info "New SECRET_KEY generated: ${NEW_SECRET:0:16}..."
    print_warning "This will replace your current SECRET_KEY"
    read -p "Continue? (y/n): " confirm
    
    if [[ "$confirm" != "y" ]] && [[ "$confirm" != "Y" ]]; then
        print_info "Cancelled"
        read -p "Press Enter to continue..."
        configure_settings
        return 0
    fi
    
    # Update .env file
    if grep -q "^SECRET_KEY=" "$ENV_FILE"; then
        sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$NEW_SECRET|" "$ENV_FILE"
    else
        echo "SECRET_KEY=$NEW_SECRET" >> "$ENV_FILE"
    fi
    
    # Update service file if it contains SECRET_KEY
    if [[ -f "$SERVICE_FILE" ]] && grep -q "Environment=\"SECRET_KEY=" "$SERVICE_FILE"; then
        sed -i "s|Environment=\"SECRET_KEY=.*\"|Environment=\"SECRET_KEY=$NEW_SECRET\"|" "$SERVICE_FILE"
        systemctl daemon-reload
    fi
    
    print_info "Restarting service..."
    systemctl restart ${SERVICE_NAME}
    
    print_success "SECRET_KEY updated and service restarted"
    print_warning "Keep this SECRET_KEY secure!"
    
    echo ""
    read -p "Press Enter to continue..."
    configure_settings
}

# Show status
show_status() {
    print_header "System Status"
    
    echo -e "${BLUE}Service Status:${NC}"
    systemctl status ${SERVICE_NAME} --no-pager -l || true
    
    echo ""
    echo -e "${BLUE}Application Files:${NC}"
    ls -lh "$INSTALL_DIR" 2>/dev/null | head -10 || echo "Directory not found"
    
    echo ""
    echo -e "${BLUE}Database:${NC}"
    if [[ -f "$DB_FILE" ]]; then
        echo "  Location: $DB_FILE"
        echo "  Size: $(du -h "$DB_FILE" | cut -f1)"
        echo "  Registrations: $(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM registration;" 2>/dev/null || echo "Unable to query")"
    else
        echo "  Database not found"
    fi
    
    echo ""
    echo -e "${BLUE}Nginx Configuration:${NC}"
    if [[ -f "$NGINX_CONF" ]]; then
        echo "  Config: $NGINX_CONF"
        echo "  Enabled: $([ -L "$NGINX_ENABLED" ] && echo "Yes" || echo "No")"
        if command -v nginx &> /dev/null; then
            echo "  Nginx Status: $(systemctl is-active nginx 2>/dev/null || echo "not running")"
        fi
    else
        echo "  Nginx not configured"
    fi
    
    echo ""
    echo -e "${BLUE}Recent Logs:${NC}"
    journalctl -u ${SERVICE_NAME} -n 5 --no-pager 2>/dev/null || echo "  No logs available"
    
    echo ""
    read -p "Press Enter to return to menu..."
    main
}

# Remove installation completely
remove_installation() {
    print_header "Complete Uninstall"
    print_warning "This will remove ALL data including the database!"
    echo ""
    print_error "Files that will be deleted:"
    echo "  - $INSTALL_DIR (all application files)"
    echo "  - $DB_FILE (all registration data)"
    echo "  - $SERVICE_FILE (systemd service)"
    echo "  - $LOG_DIR (all logs)"
    echo "  - $NGINX_CONF (nginx configuration)"
    echo ""
    read -p "Are you sure? Type 'yes' to confirm: " confirm
    
    if [[ "$confirm" != "yes" ]]; then
        print_info "Removal cancelled"
        echo ""
        read -p "Press Enter to return to menu..."
        main
        return 0
    fi
    
    echo ""
    read -p "Do you want to backup the database before removing? (y/n): " backup
    
    if [[ "$backup" == "y" ]] || [[ "$backup" == "Y" ]]; then
        if [[ -f "$DB_FILE" ]]; then
            BACKUP_FILE="${HOME}/${APP_NAME}_backup_$(date +%Y%m%d_%H%M%S).db"
            print_info "Backing up database to ${BACKUP_FILE}..."
            cp "$DB_FILE" "$BACKUP_FILE"
            print_success "Database backed up to $BACKUP_FILE"
        else
            print_info "No database file found to backup"
        fi
    fi
    
    remove_installation_silent
    
    print_success "Installation removed completely"
    
    if [[ -f "${HOME}/${APP_NAME}_backup_"*.db ]]; then
        echo ""
        print_info "Database backup(s) saved in: ${HOME}/"
        ls -lh "${HOME}/${APP_NAME}_backup_"*.db 2>/dev/null
    fi
    
    exit 0
}

# Silent removal (for internal use)
remove_installation_silent() {
    print_info "Removing installation..."
    
    # Stop and disable service
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        print_info "Stopping service..."
        systemctl stop ${SERVICE_NAME}
    fi
    
    if systemctl is-enabled --quiet ${SERVICE_NAME} 2>/dev/null; then
        print_info "Disabling service..."
        systemctl disable ${SERVICE_NAME}
    fi
    
    # Remove service file
    if [[ -f "$SERVICE_FILE" ]]; then
        print_info "Removing service file..."
        rm -f "$SERVICE_FILE"
        systemctl daemon-reload
    fi
    
    # Remove nginx configuration
    if [[ -f "$NGINX_CONF" ]]; then
        print_info "Removing nginx configuration..."
        rm -f "$NGINX_CONF"
        rm -f "$NGINX_ENABLED"
        if command -v nginx &> /dev/null && systemctl is-active --quiet nginx; then
            print_info "Reloading nginx..."
            systemctl reload nginx 2>/dev/null || true
        fi
    fi
    
    # Remove installation directory
    if [[ -d "$INSTALL_DIR" ]]; then
        print_info "Removing installation directory..."
        rm -rf "$INSTALL_DIR"
    fi
    
    # Remove log directory
    if [[ -d "$LOG_DIR" ]]; then
        print_info "Removing log directory..."
        rm -rf "$LOG_DIR"
    fi
    
    # Remove run directory
    if [[ -d "$RUN_DIR" ]]; then
        print_info "Removing run directory..."
        rm -rf "$RUN_DIR"
    fi
    
    print_success "Removal completed"
}

# Fresh installation
fresh_installation() {
    print_header "Starting Fresh Installation"
    
    # Install system dependencies
    install_dependencies
    
    # Verify Python
    if ! check_python; then
        print_error "Python check failed"
        exit 1
    fi
    
    # Create system user if doesn't exist
    if ! id -u $SYSTEM_USER &>/dev/null; then
        print_info "Creating system user: $SYSTEM_USER"
        useradd -r -s /bin/false $SYSTEM_USER
    fi
    
    # Create installation directory
    print_info "Creating installation directory: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    
    # Copy files from current directory to install directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    print_info "Copying application files..."
    
    # Check if we're already in the install directory
    if [[ "$SCRIPT_DIR" == "$INSTALL_DIR" ]]; then
        print_info "Already in installation directory"
    else
        # Copy all files except .git
        rsync -av --exclude='.git' --exclude='*.db' --exclude='venv' --exclude='__pycache__' "$SCRIPT_DIR/" "$INSTALL_DIR/" || {
            cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/" 2>/dev/null || true
        }
    fi
    
    # Create Python virtual environment
    print_info "Creating Python virtual environment..."
    cd "$INSTALL_DIR"
    $PYTHON_CMD -m venv "$VENV_DIR" || {
        print_error "Failed to create virtual environment"
        exit 1
    }
    
    # Activate virtual environment and install dependencies
    print_info "Installing Python dependencies..."
    source "${VENV_DIR}/bin/activate"
    pip install --upgrade pip
    pip install -r requirements.txt || {
        print_error "Failed to install Python dependencies"
        exit 1
    }
    deactivate
    
    # Initialize database
    print_info "Initializing database..."
    source "${VENV_DIR}/bin/activate"
    $PYTHON_CMD -c "from app import init_db; init_db()" || {
        print_warning "Database initialization may have failed, but continuing..."
    }
    deactivate
    
    # Create log directory
    print_info "Creating log directory: $LOG_DIR"
    mkdir -p "$LOG_DIR"
    
    # Create run directory
    print_info "Creating run directory: $RUN_DIR"
    mkdir -p "$RUN_DIR"
    
    # Set permissions
    print_info "Setting permissions..."
    chown -R ${SYSTEM_USER}:${SYSTEM_GROUP} "$INSTALL_DIR"
    chown -R ${SYSTEM_USER}:${SYSTEM_GROUP} "$LOG_DIR"
    chown -R ${SYSTEM_USER}:${SYSTEM_GROUP} "$RUN_DIR"
    
    # Check if .env exists, if not create from example
    if [[ ! -f "${INSTALL_DIR}/.env" ]] && [[ -f "${INSTALL_DIR}/.env.example" ]]; then
        print_info "Creating .env file from example..."
        cp "${INSTALL_DIR}/.env.example" "${INSTALL_DIR}/.env"
        
        # Generate random secret key
        SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
        sed -i "s/your-secret-key-change-me-in-production/$SECRET_KEY/" "${INSTALL_DIR}/.env"
        
        # Interactive setup for admin credentials
        print_header "Admin Panel Setup"
        echo ""
        print_info "Let's configure your admin credentials for the web interface."
        echo ""
        
        # Ask for admin username
        read -p "Enter admin username (default: admin): " ADMIN_USER
        ADMIN_USER=${ADMIN_USER:-admin}
        
        # Ask for admin password (with confirmation)
        while true; do
            read -s -p "Enter admin password: " ADMIN_PASS1
            echo ""
            read -s -p "Confirm admin password: " ADMIN_PASS2
            echo ""
            
            if [[ "$ADMIN_PASS1" == "$ADMIN_PASS2" ]]; then
                if [[ -z "$ADMIN_PASS1" ]]; then
                    print_error "Password cannot be empty. Please try again."
                    echo ""
                else
                    break
                fi
            else
                print_error "Passwords do not match. Please try again."
                echo ""
            fi
        done
        
        # Update .env file with admin credentials
        sed -i "s/ADMIN_USERNAME=admin/ADMIN_USERNAME=$ADMIN_USER/" "${INSTALL_DIR}/.env"
        sed -i "s/ADMIN_PASSWORD=change-me-in-production/ADMIN_PASSWORD=$ADMIN_PASS1/" "${INSTALL_DIR}/.env"
        
        print_success "Admin credentials configured successfully!"
        print_info "Username: $ADMIN_USER"
        print_info "Password: [hidden]"
        echo ""
        
        print_info "You can change these later by editing: ${INSTALL_DIR}/.env"
        echo ""
        
        chown ${SYSTEM_USER}:${SYSTEM_GROUP} "${INSTALL_DIR}/.env"
        chmod 600 "${INSTALL_DIR}/.env"  # Secure the .env file
    fi
    
    # Install systemd service
    print_info "Installing systemd service..."
    
    # Check if SECRET_KEY needs to be set in service file
    if [[ -f "${INSTALL_DIR}/.env" ]]; then
        SOURCE_SECRET=$(grep "^SECRET_KEY=" "${INSTALL_DIR}/.env" | cut -d= -f2)
    else
        SOURCE_SECRET=$(openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
    fi
    
    # Copy and update service file
    cp "${INSTALL_DIR}/photo-registration.service" "$SERVICE_FILE"
    sed -i "s|your-secret-key-change-me|$SOURCE_SECRET|" "$SERVICE_FILE"
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable and start service
    print_info "Enabling service..."
    systemctl enable ${SERVICE_NAME}
    
    print_info "Starting service..."
    systemctl start ${SERVICE_NAME}
    
    # Wait a moment for service to start
    sleep 2
    
    # Check service status
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        print_success "Service is running!"
    else
        print_error "Service failed to start. Checking logs..."
        journalctl -u ${SERVICE_NAME} -n 50 --no-pager
        exit 1
    fi
    
    print_success "Installation completed successfully!"
    print_installation_info
    
    # Run post-installation configuration wizard
    post_installation_wizard
}

# Print installation information
print_installation_info() {
    print_header "Installation Information"
    
    echo -e "${GREEN}Installation Directory:${NC} $INSTALL_DIR"
    echo -e "${GREEN}Service Name:${NC} $SERVICE_NAME"
    echo -e "${GREEN}Log Directory:${NC} $LOG_DIR"
    echo -e "${GREEN}Database File:${NC} $DB_FILE"
    echo -e "${GREEN}Configuration:${NC} ${INSTALL_DIR}/.env"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo -e "  Start service:   ${YELLOW}sudo systemctl start ${SERVICE_NAME}${NC}"
    echo -e "  Stop service:    ${YELLOW}sudo systemctl stop ${SERVICE_NAME}${NC}"
    echo -e "  Restart service: ${YELLOW}sudo systemctl restart ${SERVICE_NAME}${NC}"
    echo -e "  Service status:  ${YELLOW}sudo systemctl status ${SERVICE_NAME}${NC}"
    echo -e "  View logs:       ${YELLOW}sudo journalctl -u ${SERVICE_NAME} -f${NC}"
    echo -e "  Access logs:     ${YELLOW}sudo tail -f ${LOG_DIR}/access.log${NC}"
    echo -e "  Error logs:      ${YELLOW}sudo tail -f ${LOG_DIR}/error.log${NC}"
    echo ""
    echo -e "${BLUE}Application Access:${NC}"
    echo -e "  Local:           ${YELLOW}http://127.0.0.1:5000${NC}"
    echo -e "  Health Check:    ${YELLOW}http://127.0.0.1:5000/health${NC}"
    echo -e "  Registrations:   ${YELLOW}http://127.0.0.1:5000/registrations${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo -e "  1. Review configuration: ${YELLOW}sudo nano ${INSTALL_DIR}/.env${NC}"
    echo -e "  2. Set up Cloudflare Tunnel (see README.md)"
    echo -e "  3. Test the application: ${YELLOW}curl http://127.0.0.1:5000/health${NC}"
    echo ""
    
    # Show service status
    print_header "Current Service Status"
    systemctl status ${SERVICE_NAME} --no-pager -l
}

# Post-installation configuration wizard
post_installation_wizard() {
    print_header "Post-Installation Configuration"
    
    echo -e "${CYAN}The basic installation is complete!${NC}"
    echo -e "${CYAN}Let's configure your system for production use.${NC}"
    echo ""
    
    # Step 1: Network binding configuration
    print_header "Step 1: Network Binding"
    echo "How do you want to access the application?"
    echo ""
    echo "1) Local access only (localhost) - Recommended with Nginx reverse proxy"
    echo "2) Network access (LAN) - For Cloudflare Tunnel on separate server"
    echo "3) Skip for now (configure later)"
    echo ""
    read -p "Enter your choice [1-3]: " binding_choice
    
    case $binding_choice in
        1)
            print_info "Keeping default: localhost only (127.0.0.1:5000)"
            ;;
        2)
            print_info "Configuring for network access..."
            if [[ -f "$ENV_FILE" ]]; then
                # Detect server IP
                SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
                if [[ -z "$SERVER_IP" ]]; then
                    SERVER_IP="192.168.1.104"
                fi
                
                # Update .env with network binding
                if grep -q "^GUNICORN_BIND=" "$ENV_FILE"; then
                    sed -i "s/^GUNICORN_BIND=.*/GUNICORN_BIND=0.0.0.0:5000/" "$ENV_FILE"
                else
                    echo "GUNICORN_BIND=0.0.0.0:5000" >> "$ENV_FILE"
                fi
                
                print_success "Configured for network access on 0.0.0.0:5000"
                print_info "Your server IP appears to be: ${YELLOW}$SERVER_IP${NC}"
                print_info "Configure Cloudflare Tunnel with: ${YELLOW}http://$SERVER_IP:5000${NC}"
                
                # Restart service
                print_info "Restarting service..."
                systemctl restart ${SERVICE_NAME}
                sleep 2
                
                if systemctl is-active --quiet ${SERVICE_NAME}; then
                    print_success "Service restarted successfully"
                else
                    print_warning "Service may need attention. Check: sudo systemctl status ${SERVICE_NAME}"
                fi
            fi
            ;;
        3)
            print_info "Skipped network binding configuration"
            ;;
        *)
            print_warning "Invalid choice. Keeping default configuration."
            ;;
    esac
    
    echo ""
    
    # Step 2: Nginx configuration
    print_header "Step 2: Nginx Reverse Proxy"
    echo "Do you want to configure Nginx as a reverse proxy?"
    echo ""
    echo "Benefits:"
    echo "  - Access on port 80 (no :5000 in URL)"
    echo "  - SSL/HTTPS support"
    echo "  - Better performance and security"
    echo ""
    
    # Check if nginx is running and if port 80 is available
    PORT_80_IN_USE=false
    if ss -tuln 2>/dev/null | grep -q ":80 " || netstat -tuln 2>/dev/null | grep -q ":80 "; then
        if ! systemctl is-active --quiet nginx; then
            PORT_80_IN_USE=true
            print_warning "Port 80 is in use by another service (not Nginx)"
        fi
    fi
    
    if [[ "$PORT_80_IN_USE" == "true" ]]; then
        echo -e "${RED}WARNING: Port 80 is already in use!${NC}"
        echo "You may need to:"
        echo "  1. Stop the conflicting service"
        echo "  2. Configure Flask to use localhost binding (Step 1, option 1)"
        echo ""
    fi
    
    read -p "Configure Nginx now? (y/n): " nginx_choice
    
    if [[ "$nginx_choice" == "y" ]] || [[ "$nginx_choice" == "Y" ]]; then
        # Ensure Flask is bound to localhost if using Nginx
        if [[ -f "$ENV_FILE" ]]; then
            CURRENT_BIND=$(grep "^GUNICORN_BIND=" "$ENV_FILE" | cut -d= -f2)
            if [[ "$CURRENT_BIND" != "127.0.0.1:5000" ]]; then
                print_warning "For Nginx reverse proxy, Flask should bind to localhost"
                read -p "Change binding to 127.0.0.1:5000? (recommended) (y/n): " change_bind
                if [[ "$change_bind" == "y" ]] || [[ "$change_bind" == "Y" ]]; then
                    sed -i "s/^GUNICORN_BIND=.*/GUNICORN_BIND=127.0.0.1:5000/" "$ENV_FILE"
                    systemctl restart ${SERVICE_NAME}
                    sleep 2
                    print_success "Flask now bound to localhost"
                fi
            fi
        fi
        
        # Get hostname
        echo ""
        echo "Enter your domain/hostname (e.g., photos.example.com)"
        echo "Or enter 'localhost' for local testing"
        read -p "Hostname: " hostname
        
        if [[ -n "$hostname" ]]; then
            # Create nginx config
            print_info "Creating Nginx configuration for $hostname..."
            
            if [[ -f "${INSTALL_DIR}/nginx.conf.template" ]]; then
                sed "s/SERVER_NAME/$hostname/g" "${INSTALL_DIR}/nginx.conf.template" > "$NGINX_CONF"
                
                # Enable site if sites-enabled exists
                if [[ -d "/etc/nginx/sites-enabled" ]]; then
                    ln -sf "$NGINX_CONF" "$NGINX_ENABLED"
                    print_success "Nginx site enabled"
                fi
                
                # Test configuration
                print_info "Testing Nginx configuration..."
                if nginx -t 2>&1; then
                    print_success "Nginx configuration is valid"
                    
                    # Start nginx if not running
                    if ! systemctl is-active --quiet nginx; then
                        print_info "Starting Nginx..."
                        systemctl start nginx 2>&1 || {
                            print_error "Failed to start Nginx"
                            print_info "Checking what's using port 80..."
                            ss -tulpn | grep ":80 " || netstat -tulpn | grep ":80 " || true
                        }
                    else
                        print_info "Reloading Nginx..."
                        systemctl reload nginx 2>&1
                    fi
                    
                    # Enable nginx
                    systemctl enable nginx 2>/dev/null || true
                    
                    if systemctl is-active --quiet nginx; then
                        print_success "Nginx is running!"
                        echo ""
                        print_info "Access your application at: ${YELLOW}http://$hostname${NC}"
                    else
                        print_warning "Nginx configuration created but service is not running"
                        print_info "Check status with: sudo systemctl status nginx"
                    fi
                else
                    print_error "Nginx configuration test failed"
                    nginx -t
                fi
            else
                print_error "nginx.conf.template not found"
            fi
        else
            print_info "Skipped Nginx configuration"
        fi
    else
        print_info "Skipped Nginx configuration"
    fi
    
    echo ""
    print_header "Configuration Complete!"
    
    echo -e "${GREEN}Your Photo Registration Form is ready!${NC}"
    echo ""
    echo -e "${BLUE}Quick Reference:${NC}"
    echo -e "  Service status:  ${YELLOW}sudo systemctl status ${SERVICE_NAME}${NC}"
    echo -e "  View logs:       ${YELLOW}sudo journalctl -u ${SERVICE_NAME} -f${NC}"
    echo -e "  Reconfigure:     ${YELLOW}sudo bash install.sh${NC} (choose option 3)"
    echo ""
    
    # Show access URLs
    CURRENT_BIND=$(grep "^GUNICORN_BIND=" "$ENV_FILE" 2>/dev/null | cut -d= -f2)
    if [[ "$CURRENT_BIND" == "0.0.0.0:5000" ]]; then
        SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
        echo -e "${BLUE}Access URLs:${NC}"
        echo -e "  Local:    ${YELLOW}http://127.0.0.1:5000${NC}"
        if [[ -n "$SERVER_IP" ]]; then
            echo -e "  Network:  ${YELLOW}http://$SERVER_IP:5000${NC}"
        fi
    else
        echo -e "${BLUE}Access URL:${NC}"
        echo -e "  Local:    ${YELLOW}http://127.0.0.1:5000${NC}"
    fi
    
    if [[ -n "$hostname" ]] && systemctl is-active --quiet nginx; then
        echo -e "  Domain:   ${YELLOW}http://$hostname${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo -e "  Main README:              ${INSTALL_DIR}/README.md"
    echo -e "  Tunnel Setup:             ${INSTALL_DIR}/TUNNEL-ON-SEPARATE-SERVER.md"
    echo -e "  systemd & Nginx Guide:    ${INSTALL_DIR}/SYSTEMD-NGINX-MANAGEMENT.md"
    echo ""
}

# Main script execution
main() {
    # Check if running as root
    check_root
    
    # Detect OS
    detect_os
    
    # Show menu
    show_main_menu
}

# Run main function
main
