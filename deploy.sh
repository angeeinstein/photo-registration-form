#!/bin/bash
# Deployment script for photo-registration-form
# Run this on your server to update the service

echo "============================================"
echo "Photo Registration Form - Deployment Script"
echo "============================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Please run as root (sudo ./deploy.sh)"
    exit 1
fi

# Define paths
APP_DIR="/opt/photo-registration-form"
SERVICE_FILE="/etc/systemd/system/photo-registration.service"

echo "1. Stopping service..."
systemctl stop photo-registration

echo ""
echo "2. Copying new service file..."
cp "$APP_DIR/photo-registration.service" "$SERVICE_FILE"
chmod 644 "$SERVICE_FILE"

echo ""
echo "3. Creating necessary directories..."
mkdir -p /var/log/photo-registration
mkdir -p "$APP_DIR/instance"
chown www-data:www-data /var/log/photo-registration
chown www-data:www-data "$APP_DIR/instance"

echo ""
echo "4. Reloading systemd daemon..."
systemctl daemon-reload

echo ""
echo "5. Starting service..."
systemctl start photo-registration

echo ""
echo "6. Checking service status..."
sleep 2
systemctl status photo-registration --no-pager

echo ""
echo "============================================"
echo "Deployment complete!"
echo "============================================"
echo ""
echo "⚠️  IMPORTANT: You still need to update nginx!"
echo ""
echo "Run this to check your nginx config:"
echo "  ./check-nginx.sh"
echo ""
echo "To monitor logs, run:"
echo "  journalctl -u photo-registration -f"
echo ""
