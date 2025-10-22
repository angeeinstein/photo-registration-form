#!/bin/bash
#
# Quick fix script for database migration issue
# Run this if you see "Database error" or "no such column" errors
#
# Usage:
#   sudo bash quick_fix_migration.sh
#

set -e

echo "=========================================="
echo "Quick Fix: Database Migration"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

INSTALL_DIR="/opt/photo-registration-form"
VENV_DIR="${INSTALL_DIR}/venv"

# Check if installation exists
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Error: Installation not found at $INSTALL_DIR"
    exit 1
fi

cd "$INSTALL_DIR"

echo "[1/4] Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

echo "[2/4] Running database migration..."
if [ -f "migrate_photo_workflow.py" ]; then
    python3 migrate_photo_workflow.py || {
        echo "Warning: Migration script had warnings (may be normal if already migrated)"
    }
else
    echo "Error: Migration script not found!"
    exit 1
fi

echo "[3/4] Verifying database..."
python3 -c "
from app import app, db, Registration
with app.app_context():
    try:
        # Try to query with new fields
        test = Registration.query.first()
        if test:
            _ = test.qr_token
            _ = test.photo_count
        print('✓ Database schema verified')
    except Exception as e:
        print(f'✗ Database verification failed: {e}')
        exit(1)
" || {
    echo "Error: Database verification failed"
    exit 1
}

echo "[4/4] Restarting service..."
systemctl restart photo-registration

echo ""
echo "=========================================="
echo "✓ Migration completed successfully!"
echo "=========================================="
echo ""
echo "You can now access the admin page:"
echo "  https://your-domain.com/admin"
echo ""
