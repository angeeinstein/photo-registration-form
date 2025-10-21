#!/bin/bash
#
# Quick Fix Script for Missing Database
# Run this on your Proxmox server to fix the database issue
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Photo Registration Form - Database Quick Fix${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Detect installation directory
if [[ -d "/opt/photo-registration-form" ]]; then
    INSTALL_DIR="/opt/photo-registration-form"
elif [[ -d "$(pwd)" ]] && [[ -f "$(pwd)/app.py" ]]; then
    INSTALL_DIR="$(pwd)"
else
    echo -e "${RED}Error: Cannot find installation directory${NC}"
    exit 1
fi

echo -e "${GREEN}Installation directory: ${INSTALL_DIR}${NC}"
cd "$INSTALL_DIR"

# Create instance directory
echo ""
echo -e "${YELLOW}Creating instance directory...${NC}"
mkdir -p instance
chown www-data:www-data instance
echo -e "${GREEN}✓ Created: ${INSTALL_DIR}/instance${NC}"

# Initialize database
echo ""
echo -e "${YELLOW}Initializing database...${NC}"

if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
    python3 init_database.py
    deactivate
    echo -e "${GREEN}✓ Database initialized${NC}"
else
    echo -e "${RED}Error: Virtual environment not found${NC}"
    exit 1
fi

# Verify database exists
echo ""
if [[ -f "instance/photo_registration.db" ]]; then
    echo -e "${GREEN}✓ Database verified: instance/photo_registration.db${NC}"
    DB_SIZE=$(du -h instance/photo_registration.db | cut -f1)
    echo -e "${BLUE}  Size: ${DB_SIZE}${NC}"
    
    # Set permissions
    chown www-data:www-data instance/photo_registration.db
    chmod 644 instance/photo_registration.db
    echo -e "${GREEN}✓ Permissions set${NC}"
else
    echo -e "${RED}✗ Database file not found!${NC}"
    echo -e "${YELLOW}  It should be created automatically on first request${NC}"
fi

# Restart service
echo ""
echo -e "${YELLOW}Restarting service...${NC}"
systemctl restart photo-registration

sleep 2

if systemctl is-active --quiet photo-registration; then
    echo -e "${GREEN}✓ Service restarted successfully${NC}"
else
    echo -e "${RED}✗ Service failed to start${NC}"
    echo ""
    echo -e "${YELLOW}Last 20 log lines:${NC}"
    journalctl -u photo-registration -n 20 --no-pager
    exit 1
fi

# Final verification
echo ""
if [[ -f "instance/photo_registration.db" ]]; then
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}✓ Database fix completed successfully!${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    echo -e "${BLUE}Database location:${NC} ${INSTALL_DIR}/instance/photo_registration.db"
    echo -e "${BLUE}Service status:${NC} systemctl status photo-registration"
    echo -e "${BLUE}View logs:${NC} journalctl -u photo-registration -f"
    echo ""
    echo -e "${YELLOW}You can now try registering again!${NC}"
else
    echo -e "${YELLOW}============================================================${NC}"
    echo -e "${YELLOW}Database will be created on first request${NC}"
    echo -e "${YELLOW}============================================================${NC}"
    echo ""
    echo -e "${BLUE}Try accessing the registration form to trigger creation${NC}"
fi

echo ""
