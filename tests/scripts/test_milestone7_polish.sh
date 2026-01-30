#!/bin/bash
# Milestone 7: Polish & Integration - Verification Script
# Tests keyboard shortcuts, loading states, and dashboard enhancements

set -e  # Exit on error

echo "=========================================="
echo "Milestone 7: Polish & Integration Tests"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"
AUTH_HEADER="Authorization: Bearer dev_token_12345"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
test_endpoint() {
    local description=$1
    local endpoint=$2
    local expected_status=${3:-200}

    echo -n "Testing: $description..."

    response=$(curl -s -w "\n%{http_code}" -H "$AUTH_HEADER" "$API_URL$endpoint")
    status_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')

    if [ "$status_code" = "$expected_status" ]; then
        echo -e " ${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e " ${RED}✗ FAIL${NC} (Expected $expected_status, got $status_code)"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "${BLUE}[1/5] Backend API Health${NC}"
echo "----------------------------"
test_endpoint "Health check" "/health"
test_endpoint "List users" "/users"
echo ""

echo "${BLUE}[2/5] Frontend Files${NC}"
echo "----------------------------"
echo -n "Checking LoadingSpinner component..."
if [ -f "frontend/src/components/LoadingSpinner.tsx" ]; then
    echo -e " ${GREEN}✓ EXISTS${NC}"
    ((TESTS_PASSED++))
else
    echo -e " ${RED}✗ MISSING${NC}"
    ((TESTS_FAILED++))
fi

echo -n "Checking KeyboardShortcutsModal component..."
if [ -f "frontend/src/components/KeyboardShortcutsModal.tsx" ]; then
    echo -e " ${GREEN}✓ EXISTS${NC}"
    ((TESTS_PASSED++))
else
    echo -e " ${RED}✗ MISSING${NC}"
    ((TESTS_FAILED++))
fi

echo -n "Checking useKeyboardShortcuts hook..."
if [ -f "frontend/src/hooks/useKeyboardShortcuts.ts" ]; then
    echo -e " ${GREEN}✓ EXISTS${NC}"
    ((TESTS_PASSED++))
else
    echo -e " ${RED}✗ MISSING${NC}"
    ((TESTS_FAILED++))
fi
echo ""

echo "${BLUE}[3/5] CSS Files${NC}"
echo "----------------------------"
echo -n "Checking LoadingSpinner.css..."
if [ -f "frontend/src/components/LoadingSpinner.css" ]; then
    echo -e " ${GREEN}✓ EXISTS${NC}"
    ((TESTS_PASSED++))
else
    echo -e " ${RED}✗ MISSING${NC}"
    ((TESTS_FAILED++))
fi

echo -n "Checking KeyboardShortcutsModal.css..."
if [ -f "frontend/src/components/KeyboardShortcutsModal.css" ]; then
    echo -e " ${GREEN}✓ EXISTS${NC}"
    ((TESTS_PASSED++))
else
    echo -e " ${RED}✗ MISSING${NC}"
    ((TESTS_FAILED++))
fi

echo -n "Checking Dashboard.css enhancements..."
if grep -q "quick-actions" frontend/src/components/Dashboard.css; then
    echo -e " ${GREEN}✓ ENHANCED${NC}"
    ((TESTS_PASSED++))
else
    echo -e " ${RED}✗ NOT FOUND${NC}"
    ((TESTS_FAILED++))
fi
echo ""

echo "${BLUE}[4/5] Documentation${NC}"
echo "----------------------------"
echo -n "Checking USER_GUIDE.md..."
if [ -f "docs/technical/phase1.5/USER_GUIDE.md" ]; then
    line_count=$(wc -l < docs/technical/phase1.5/USER_GUIDE.md)
    if [ $line_count -gt 800 ]; then
        echo -e " ${GREEN}✓ EXISTS (${line_count} lines)${NC}"
        ((TESTS_PASSED++))
    else
        echo -e " ${RED}✗ TOO SHORT (${line_count} lines)${NC}"
        ((TESTS_FAILED++))
    fi
else
    echo -e " ${RED}✗ MISSING${NC}"
    ((TESTS_FAILED++))
fi

echo -n "Checking MILESTONE_7 completion report..."
if [ -f "docs/technical/phase1.5/MILESTONE_7_POLISH_INTEGRATION.md" ]; then
    echo -e " ${GREEN}✓ EXISTS${NC}"
    ((TESTS_PASSED++))
else
    echo -e " ${RED}✗ MISSING${NC}"
    ((TESTS_FAILED++))
fi
echo ""

echo "${BLUE}[5/5] React Query Configuration${NC}"
echo "----------------------------"
echo -n "Checking staleTime configuration..."
if grep -q "staleTime: 30000" frontend/src/main.tsx; then
    echo -e " ${GREEN}✓ CONFIGURED${NC}"
    ((TESTS_PASSED++))
else
    echo -e " ${RED}✗ NOT FOUND${NC}"
    ((TESTS_FAILED++))
fi

echo -n "Checking gcTime configuration..."
if grep -q "gcTime: 300000" frontend/src/main.tsx; then
    echo -e " ${GREEN}✓ CONFIGURED${NC}"
    ((TESTS_PASSED++))
else
    echo -e " ${RED}✗ NOT FOUND${NC}"
    ((TESTS_FAILED++))
fi
echo ""

echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! Milestone 7 complete.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Review above output.${NC}"
    exit 1
fi
