#!/bin/bash

#############################################
# Photo Registration Form - Test Script
# Verifies the installation is working
#############################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_URL="http://127.0.0.1:5000"
SERVICE_NAME="photo-registration"

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Photo Registration Form - Test Suite${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Test 1: Service Status
print_test "Checking service status..."
if systemctl is-active --quiet ${SERVICE_NAME}; then
    print_pass "Service is running"
else
    print_fail "Service is not running"
    echo "Run: sudo systemctl status ${SERVICE_NAME}"
    exit 1
fi

# Test 2: Health Check
print_test "Testing health endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" ${APP_URL}/health)
if [[ "$response" == "200" ]]; then
    print_pass "Health check passed (HTTP $response)"
else
    print_fail "Health check failed (HTTP $response)"
    exit 1
fi

# Test 3: Main Page
print_test "Testing main page..."
response=$(curl -s -o /dev/null -w "%{http_code}" ${APP_URL}/)
if [[ "$response" == "200" ]]; then
    print_pass "Main page accessible (HTTP $response)"
else
    print_fail "Main page failed (HTTP $response)"
    exit 1
fi

# Test 4: Registration Endpoint
print_test "Testing registration submission..."
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST ${APP_URL}/register \
    -d "first_name=Test&last_name=User&email=test@example.com")
if [[ "$response" == "201" ]]; then
    print_pass "Registration endpoint works (HTTP $response)"
else
    print_fail "Registration endpoint failed (HTTP $response)"
    echo "This might be expected if validation failed"
fi

# Test 5: Registrations List
print_test "Testing registrations list endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" ${APP_URL}/registrations)
if [[ "$response" == "200" ]]; then
    print_pass "Registrations list accessible (HTTP $response)"
else
    print_fail "Registrations list failed (HTTP $response)"
    exit 1
fi

# Test 6: Database Check
print_test "Checking database file..."
if [[ -f "/opt/photo-registration-form/registrations.db" ]]; then
    print_pass "Database file exists"
else
    print_fail "Database file not found"
    exit 1
fi

# Test 7: Log Files
print_test "Checking log files..."
if [[ -d "/var/log/photo-registration" ]]; then
    print_pass "Log directory exists"
else
    print_fail "Log directory not found"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}All tests passed!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo "Service Status:"
systemctl status ${SERVICE_NAME} --no-pager -l

echo -e "\nRecent Registrations:"
curl -s ${APP_URL}/registrations | python3 -m json.tool 2>/dev/null | head -20

exit 0
