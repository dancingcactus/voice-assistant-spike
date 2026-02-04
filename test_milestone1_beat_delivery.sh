#!/bin/bash
#
# Milestone 1: Beat Delivery & UI Updates - Manual Test Script
#
# This script tests the fixes for beat delivery and UI updates.
# Run this after starting the backend server.
#

set -e

API_URL="http://localhost:8000/api/v1"
AUTH_TOKEN="dev_token_12345"
TEST_USER="test_user_milestone1"

echo "================================"
echo "Milestone 1: Beat Delivery Tests"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3

    if [ -n "$data" ]; then
        curl -s -X "$method" "$API_URL$endpoint" \
            -H "Authorization: Bearer $AUTH_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data"
    else
        curl -s -X "$method" "$API_URL$endpoint" \
            -H "Authorization: Bearer $AUTH_TOKEN"
    fi
}

# Test 1: Create test user
echo -e "${YELLOW}Test 1: Create test user${NC}"
echo "Creating user: $TEST_USER"
api_call POST "/users/test" "{\"user_id\": \"$TEST_USER\", \"starting_chapter\": 1, \"tags\": [\"milestone1\", \"testing\"]}" | jq '.'
echo ""

# Test 2: Check initial progress
echo -e "${YELLOW}Test 2: Check initial progress${NC}"
echo "Getting initial progress for $TEST_USER"
PROGRESS=$(api_call GET "/story/users/$TEST_USER/progress")
echo "$PROGRESS" | jq '.'
INITIAL_BEATS=$(echo "$PROGRESS" | jq -r '.beats_delivered')
echo "Initial beats delivered: $INITIAL_BEATS"
echo ""

# Test 3: Get Chapter 1 beats list
echo -e "${YELLOW}Test 3: Get Chapter 1 beats list${NC}"
echo "Fetching Chapter 1 beats for $TEST_USER"
BEATS=$(api_call GET "/story/chapters/1/beats?user_id=$TEST_USER")
echo "$BEATS" | jq '.'
echo ""

# Test 4: Trigger awakening_confusion (baseline - should always work)
echo -e "${YELLOW}Test 4: Trigger awakening_confusion beat${NC}"
echo "This is the first beat - should work even before fix"
RESPONSE=$(api_call POST "/story/users/$TEST_USER/beats/awakening_confusion/trigger" '{"variant": "standard"}')
echo "$RESPONSE" | jq '.'

if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1 || echo "$RESPONSE" | jq -e '.message' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ awakening_confusion triggered successfully${NC}"
else
    echo -e "${RED}✗ awakening_confusion failed to trigger${NC}"
fi
echo ""

# Give time for state to persist
sleep 2

# Test 5: Check progress after first beat
echo -e "${YELLOW}Test 5: Check progress after awakening_confusion${NC}"
PROGRESS=$(api_call GET "/story/users/$TEST_USER/progress")
echo "$PROGRESS" | jq '.'
BEATS_DELIVERED=$(echo "$PROGRESS" | jq -r '.beats_delivered')
echo "Beats delivered: $BEATS_DELIVERED"
echo ""

# Test 6: Trigger first_timer (was broken - should now work due to prerequisite fix)
echo -e "${YELLOW}Test 6: Trigger first_timer beat${NC}"
echo "This beat requires awakening_confusion to be delivered"
echo "This was BROKEN before the fix - should now work"
RESPONSE=$(api_call POST "/story/users/$TEST_USER/beats/first_timer/trigger" '{"variant": "standard"}')
echo "$RESPONSE" | jq '.'

if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1 || echo "$RESPONSE" | jq -e '.message' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ first_timer triggered successfully (FIX VERIFIED!)${NC}"
else
    echo -e "${RED}✗ first_timer failed to trigger (still broken?)${NC}"
fi
echo ""

sleep 2

# Test 7: Trigger recipe_help stage 1 (was broken - should now work)
echo -e "${YELLOW}Test 7: Trigger recipe_help beat (stage 1)${NC}"
echo "This is a progression beat with multiple stages"
echo "This was BROKEN before the fix - should now work"
RESPONSE=$(api_call POST "/story/users/$TEST_USER/beats/recipe_help/trigger" '{"variant": "standard", "stage": 1}')
echo "$RESPONSE" | jq '.'

if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1 || echo "$RESPONSE" | jq -e '.message' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ recipe_help stage 1 triggered successfully (FIX VERIFIED!)${NC}"
else
    echo -e "${RED}✗ recipe_help stage 1 failed to trigger (still broken?)${NC}"
fi
echo ""

sleep 2

# Test 8: Check final progress
echo -e "${YELLOW}Test 8: Check final progress${NC}"
PROGRESS=$(api_call GET "/story/users/$TEST_USER/progress")
echo "$PROGRESS" | jq '.'
BEATS_DELIVERED=$(echo "$PROGRESS" | jq -r '.beats_delivered')
echo "Total beats delivered: $BEATS_DELIVERED"
echo ""

# Test 9: Get user-specific diagram
echo -e "${YELLOW}Test 9: Get user-specific diagram${NC}"
echo "Fetching Chapter 1 diagram with user progress"
DIAGRAM=$(api_call GET "/story/chapters/1/diagram?user_id=$TEST_USER")
echo "$DIAGRAM" | jq '.'
echo ""
echo "Diagram (first 10 lines):"
echo "$DIAGRAM" | jq -r '.diagram' | head -n 10
echo ""

# Test 10: Verify atomic state updates (check user file)
echo -e "${YELLOW}Test 10: Verify state persistence${NC}"
echo "Checking backend/data/users/$TEST_USER.json"
if [ -f "backend/data/users/$TEST_USER.json" ]; then
    echo "User file exists:"
    cat "backend/data/users/$TEST_USER.json" | jq '.story_progress'
    echo -e "${GREEN}✓ State file created successfully${NC}"
else
    echo -e "${RED}✗ State file not found (persistence may be broken)${NC}"
fi
echo ""

# Summary
echo "================================"
echo "Test Summary"
echo "================================"
echo ""
echo "Expected Results:"
echo "  - All 3 beats should trigger successfully"
echo "  - beats_delivered should be 3 or more"
echo "  - User state file should exist with beats_delivered data"
echo "  - Diagram should contain user-specific coloring"
echo ""
echo -e "${YELLOW}Frontend Testing Instructions:${NC}"
echo "1. Open http://localhost:5173 in browser"
echo "2. Navigate to Story Beat Tool"
echo "3. Select user: $TEST_USER"
echo "4. Verify beats show as 'Completed' status"
echo "5. Check diagram has legend with 4 status colors"
echo "6. Verify real-time polling (trigger beat via curl, watch UI update within 5s)"
echo ""
echo -e "${GREEN}Backend testing complete!${NC}"
echo "Check backend logs for detailed trigger evaluation steps"
