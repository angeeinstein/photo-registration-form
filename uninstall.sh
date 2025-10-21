#!/bin/bash

#############################################
# Photo Registration Form - Uninstall Script
# Removes the application completely
#############################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="photo-registration-form"
INSTALL_DIR="/opt/${APP_NAME}"
SERVICE_NAME="photo-registration"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
LOG_DIR="/var/log/${SERVICE_NAME}"
RUN_DIR="/var/run/${SERVICE_NAME}"

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

echo -e "\n${RED}========================================${NC}"
echo -e "${RED}Photo Registration Form - Uninstaller${NC}"
echo -e "${RED}========================================${NC}\n"

print_warning "This will COMPLETELY REMOVE the application and all its data!"
print_warning "Including:"
echo "  - Application files in $INSTALL_DIR"
echo "  - Database (all registrations)"
echo "  - Service configuration"
echo "  - Log files"
echo ""

read -p "Are you sure you want to continue? Type 'yes' to confirm: " confirm

if [[ "$confirm" != "yes" ]]; then
    print_info "Uninstall cancelled"
    exit 0
fi

echo ""
read -p "Do you want to backup the database before removing? (y/n): " backup

if [[ "$backup" == "y" ]] || [[ "$backup" == "Y" ]]; then
    if [[ -f "${INSTALL_DIR}/registrations.db" ]]; then
        BACKUP_FILE="${HOME}/${APP_NAME}_backup_$(date +%Y%m%d_%H%M%S).db"
        print_info "Backing up database to ${BACKUP_FILE}..."
        cp "${INSTALL_DIR}/registrations.db" "$BACKUP_FILE"
        print_success "Database backed up to $BACKUP_FILE"
    else
        print_info "No database file found to backup"
    fi
fi

echo ""
print_info "Starting uninstall process..."

# Stop service
if systemctl is-active --quiet ${SERVICE_NAME}; then
    print_info "Stopping service..."
    systemctl stop ${SERVICE_NAME}
    print_success "Service stopped"
fi

# Disable service
if systemctl is-enabled --quiet ${SERVICE_NAME} 2>/dev/null; then
    print_info "Disabling service..."
    systemctl disable ${SERVICE_NAME}
    print_success "Service disabled"
fi

# Remove service file
if [[ -f "$SERVICE_FILE" ]]; then
    print_info "Removing service file..."
    rm -f "$SERVICE_FILE"
    systemctl daemon-reload
    print_success "Service file removed"
fi

# Remove installation directory
if [[ -d "$INSTALL_DIR" ]]; then
    print_info "Removing installation directory..."
    rm -rf "$INSTALL_DIR"
    print_success "Installation directory removed"
fi

# Remove log directory
if [[ -d "$LOG_DIR" ]]; then
    print_info "Removing log directory..."
    rm -rf "$LOG_DIR"
    print_success "Log directory removed"
fi

# Remove run directory
if [[ -d "$RUN_DIR" ]]; then
    print_info "Removing run directory..."
    rm -rf "$RUN_DIR"
    print_success "Run directory removed"
fi

echo ""
print_success "Uninstall completed successfully!"

if [[ -f "${HOME}/${APP_NAME}_backup_"*.db ]]; then
    echo ""
    print_info "Database backup(s) saved in: ${HOME}/"
    ls -lh "${HOME}/${APP_NAME}_backup_"*.db 2>/dev/null
fi

exit 0
