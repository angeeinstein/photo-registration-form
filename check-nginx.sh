#!/bin/bash
# Check nginx configuration for file upload limits

echo "============================================"
echo "Nginx Configuration Checker"
echo "============================================"
echo ""

echo "1. Finding nginx configuration files..."
echo ""

# Main nginx config
echo "Main nginx.conf:"
if [ -f /etc/nginx/nginx.conf ]; then
    echo "✓ Found /etc/nginx/nginx.conf"
    echo ""
    echo "Checking for client_max_body_size..."
    grep -n "client_max_body_size" /etc/nginx/nginx.conf || echo "  ⚠ Not found in main config"
    echo ""
else
    echo "✗ /etc/nginx/nginx.conf not found"
fi

# Site-specific configs
echo "Site configurations:"
if [ -d /etc/nginx/sites-available ]; then
    echo "✓ Found /etc/nginx/sites-available/"
    ls -1 /etc/nginx/sites-available/
    echo ""
    
    for config in /etc/nginx/sites-available/*; do
        if [ -f "$config" ]; then
            echo "Checking $(basename $config):"
            grep -n "client_max_body_size\|proxy_read_timeout\|proxy_send_timeout" "$config" || echo "  ⚠ No upload limits configured"
            echo ""
        fi
    done
fi

echo ""
echo "2. Currently active settings:"
nginx -T 2>/dev/null | grep -E "client_max_body_size|proxy_read_timeout|proxy_send_timeout" | head -20

echo ""
echo "============================================"
echo "Recommended Settings"
echo "============================================"
echo ""
echo "Add these to your server block:"
echo ""
echo "  server {"
echo "    # Allow large file uploads"
echo "    client_max_body_size 100M;"
echo "    client_body_timeout 300s;"
echo "    client_header_timeout 300s;"
echo ""
echo "    location / {"
echo "      # Increased timeouts"
echo "      proxy_connect_timeout 300s;"
echo "      proxy_send_timeout 300s;"
echo "      proxy_read_timeout 300s;"
echo "      proxy_buffering off;"
echo "      proxy_request_buffering off;"
echo "    }"
echo "  }"
echo ""
echo "After editing, run:"
echo "  nginx -t"
echo "  systemctl reload nginx"
echo ""
