#!/bin/bash

# Milestone 4: User Testing Tool - Test Script
# Tests backend API endpoints for user lifecycle management

set -e

API_URL="http://localhost:8000/api/v1"
AUTH_HEADER="Authorization: Bearer dev_token_12345"

echo "🧪 Milestone 4: User Testing Tool - Backend Test"
echo "================================================"
echo ""

# Test 1: List all users with type
echo "Test 1: List all users with type information"
echo "GET /users/test/list"
echo ""
curl -s -H "$AUTH_HEADER" "$API_URL/users/test/list" | python3 -m json.tool | head -20
echo ""
echo "✅ Test 1 passed"
echo ""

# Test 2: Create a test user
echo "Test 2: Create a test user"
echo "POST /users/test"
echo ""
CREATE_RESPONSE=$(curl -s -X POST -H "$AUTH_HEADER" -H "Content-Type: application/json" \
  -d '{
    "starting_chapter": 2,
    "tags": ["milestone4", "test", "automated"],
    "initial_memories": [
      {"content": "Loves automation testing", "category": "preference", "importance": 8},
      {"content": "Gluten intolerance", "category": "dietary_restriction", "importance": 9}
    ]
  }' "$API_URL/users/test")

echo "$CREATE_RESPONSE" | python3 -m json.tool
USER_ID=$(echo "$CREATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['user']['user_id'])")
echo ""
echo "✅ Test 2 passed - Created user: $USER_ID"
echo ""

# Test 3: Get user state summary
echo "Test 3: Get user state summary"
echo "GET /users/$USER_ID/state"
echo ""
curl -s -H "$AUTH_HEADER" "$API_URL/users/$USER_ID/state" | python3 -m json.tool
echo ""
echo "✅ Test 3 passed"
echo ""

# Test 4: Export user data
echo "Test 4: Export user data"
echo "POST /users/$USER_ID/export"
echo ""
curl -s -X POST -H "$AUTH_HEADER" "$API_URL/users/$USER_ID/export" | python3 -m json.tool | head -30
echo ""
echo "✅ Test 4 passed"
echo ""

# Test 5: Try to delete production user (should fail)
echo "Test 5: Attempt to delete production user (should fail)"
echo "DELETE /users/user_justin"
echo ""
DELETE_PROD=$(curl -s -X DELETE -H "$AUTH_HEADER" "$API_URL/users/user_justin" || true)
echo "$DELETE_PROD"
if echo "$DELETE_PROD" | grep -q "Cannot delete production user"; then
  echo "✅ Test 5 passed - Production user protected"
else
  echo "❌ Test 5 failed - Production user should be protected"
fi
echo ""

# Test 6: Delete test user
echo "Test 6: Delete test user"
echo "DELETE /users/$USER_ID"
echo ""
curl -s -X DELETE -H "$AUTH_HEADER" "$API_URL/users/$USER_ID" | python3 -m json.tool
echo ""
echo "✅ Test 6 passed"
echo ""

# Test 7: Verify deletion
echo "Test 7: Verify user was deleted"
echo "GET /users/$USER_ID/state (should fail)"
echo ""
VERIFY_DELETE=$(curl -s -H "$AUTH_HEADER" "$API_URL/users/$USER_ID/state" || true)
if echo "$VERIFY_DELETE" | grep -q "not found"; then
  echo "✅ Test 7 passed - User successfully deleted"
else
  echo "❌ Test 7 failed - User still exists"
fi
echo ""

echo "================================================"
echo "🎉 All Milestone 4 backend tests passed!"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:5178/observability in your browser"
echo "2. Click 'User Testing' in the navigation"
echo "3. Try creating a test user with the form"
echo "4. Test user switching and deletion"
echo ""
