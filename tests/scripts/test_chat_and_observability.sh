#!/bin/bash
# Test script for chat interface and observability dashboard
# Tests all main components after Phase 1.5 implementation

set -e

echo "🧪 Testing Aperture Assist - Chat & Observability"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local auth=$3

    echo -n "Testing $name... "

    if [ -n "$auth" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $auth" "$url")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    fi

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response)"
        ((TESTS_FAILED++))
    fi
}

echo "📡 Testing Backend Endpoints"
echo "----------------------------"

# Test main API
test_endpoint "Main API root" "http://localhost:8000/"
test_endpoint "Main API health" "http://localhost:8000/health"

# Test Observability API
test_endpoint "Observability health" "http://localhost:8000/api/v1/health"
test_endpoint "List users" "http://localhost:8000/api/v1/users" "dev_token_12345"
test_endpoint "Get user details" "http://localhost:8000/api/v1/users/user_justin" "dev_token_12345"
test_endpoint "List chapters" "http://localhost:8000/api/v1/story/chapters?user_id=user_justin" "dev_token_12345"
test_endpoint "User memories" "http://localhost:8000/api/v1/memory/users/user_justin" "dev_token_12345"

echo ""
echo "🌐 Testing Frontend"
echo "-------------------"

# Test frontend is serving
test_endpoint "Frontend server" "http://localhost:5173/"

echo ""
echo "📊 Test Summary"
echo "==============="
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "🎉 Your system is ready to use!"
    echo ""
    echo "📍 URLs:"
    echo "   • Chat Interface: http://localhost:5173/"
    echo "   • Observability Dashboard: http://localhost:5173/observability"
    echo "   • API Docs: http://localhost:8000/docs"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
