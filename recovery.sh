#!/bin/bash
# Recovery script for photo-registration service
# Run this when the service becomes unresponsive

echo "============================================"
echo "Photo Registration Service Recovery"
echo "============================================"
echo ""

# Check current status
echo "1. Checking service status..."
systemctl status photo-registration --no-pager | head -20

echo ""
echo "2. Checking for hung processes..."
ps aux | grep -E 'gunicorn|python.*app.py' | grep -v grep

echo ""
echo "3. Checking resource usage..."
free -h
df -h /opt/photo-registration-form
df -h /tmp

echo ""
echo "4. Checking if port 5000 is in use..."
netstat -tulpn | grep :5000 || ss -tulpn | grep :5000

echo ""
read -p "Kill any hung processes and restart service? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo ""
    echo "5. Stopping service..."
    systemctl stop photo-registration
    
    echo ""
    echo "6. Killing any remaining gunicorn/python processes..."
    pkill -9 -f "gunicorn.*app:app"
    pkill -9 -f "python.*app.py"
    
    sleep 2
    
    echo ""
    echo "7. Cleaning up temporary files..."
    rm -f /var/run/photo-registration/gunicorn.pid
    find /tmp -name 'tmp*' -user www-data -mtime +1 -delete 2>/dev/null
    
    echo ""
    echo "8. Starting service..."
    systemctl start photo-registration
    
    sleep 3
    
    echo ""
    echo "9. Checking new status..."
    systemctl status photo-registration --no-pager
    
    echo ""
    echo "10. Testing if service responds..."
    curl -I http://localhost:5000/ 2>&1 | head -10
fi

echo ""
echo "============================================"
echo "Recovery complete!"
echo "============================================"
echo ""
echo "Monitor logs with:"
echo "  journalctl -u photo-registration -f"
echo ""
