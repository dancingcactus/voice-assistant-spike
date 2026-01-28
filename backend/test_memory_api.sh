#!/bin/bash

# Test Memory API Endpoints

BASE_URL="http://localhost:8000/api/v1"
AUTH="Authorization: Bearer dev_token_12345"

echo "Testing Memory API Endpoints..."
echo ""

# 1. List all memories
echo "1. List all memories for user_justin:"
curl -s -H "$AUTH" "$BASE_URL/memory/users/user_justin" | python -m json.tool | head -30
echo ""

# 2. Get context preview
echo "2. Get context preview (min_importance=5):"
curl -s -H "$AUTH" "$BASE_URL/memory/users/user_justin/context?min_importance=5" | python -m json.tool
echo ""

# 3. Create a new memory
echo "3. Create new memory:"
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"category\":\"preference\",\"content\":\"Prefers detailed error messages\",\"source\":\"manual_test\",\"importance\":7,\"verified\":true}" \
  "$BASE_URL/memory/users/user_justin" | python -m json.tool
echo ""

# 4. List memories again to see the new one
echo "4. List memories again (should see 8 now):"
curl -s -H "$AUTH" "$BASE_URL/memory/users/user_justin" | python -m json.tool | grep -E '"memory_id"|"content"' | head -20
echo ""

echo "✅ Memory API tests complete!"
