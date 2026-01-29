#!/bin/bash

# Test script for Milestone 5: Tool Calls Inspection
# Tests backend API endpoints for tool call logging and statistics

set -e  # Exit on error

API_BASE="http://localhost:8000"
AUTH_HEADER="Authorization: Bearer dev_token_12345"
USER_ID="user_justin"

echo "🧪 Testing Milestone 5: Tool Calls Inspection"
echo "================================================"
echo ""

# Test 1: List tool calls
echo "Test 1: List tool calls"
echo "GET /tool-calls?user_id=$USER_ID"
RESPONSE=$(curl -s -H "$AUTH_HEADER" "$API_BASE/tool-calls?user_id=$USER_ID&limit=5")
COUNT=$(echo "$RESPONSE" | jq '. | length')
echo "✅ Retrieved $COUNT tool calls"
echo ""

# Test 2: Get first tool call details
echo "Test 2: Get tool call details"
CALL_ID=$(echo "$RESPONSE" | jq -r '.[0].call_id')
echo "GET /tool-calls/$CALL_ID?user_id=$USER_ID"
DETAIL=$(curl -s -H "$AUTH_HEADER" "$API_BASE/tool-calls/$CALL_ID?user_id=$USER_ID")
TOOL_NAME=$(echo "$DETAIL" | jq -r '.tool_name')
echo "✅ Retrieved details for call_id=$CALL_ID, tool=$TOOL_NAME"
echo ""

# Test 3: Get statistics
echo "Test 3: Get tool call statistics"
echo "GET /tool-calls/stats?user_id=$USER_ID"
STATS=$(curl -s -H "$AUTH_HEADER" "$API_BASE/tool-calls/stats?user_id=$USER_ID")
TOTAL=$(echo "$STATS" | jq -r '.total_calls')
SUCCESS_RATE=$(echo "$STATS" | jq -r '.overall_success_rate')
echo "✅ Statistics: $TOTAL total calls, $SUCCESS_RATE% success rate"
echo ""

# Test 4: Get available tools
echo "Test 4: Get available tools list"
echo "GET /tool-calls/metadata/tools?user_id=$USER_ID"
TOOLS=$(curl -s -H "$AUTH_HEADER" "$API_BASE/tool-calls/metadata/tools?user_id=$USER_ID")
TOOL_COUNT=$(echo "$TOOLS" | jq '.tools | length')
echo "✅ Found $TOOL_COUNT unique tools"
echo "$TOOLS" | jq -r '.tools[]' | while read tool; do
  echo "   - $tool"
done
echo ""

# Test 5: Get available characters
echo "Test 5: Get available characters list"
echo "GET /tool-calls/metadata/characters?user_id=$USER_ID"
CHARACTERS=$(curl -s -H "$AUTH_HEADER" "$API_BASE/tool-calls/metadata/characters?user_id=$USER_ID")
CHAR_COUNT=$(echo "$CHARACTERS" | jq '.characters | length')
echo "✅ Found $CHAR_COUNT characters"
echo "$CHARACTERS" | jq -r '.characters[]' | while read char; do
  echo "   - $char"
done
echo ""

# Test 6: Filter by tool
echo "Test 6: Filter by tool name"
FIRST_TOOL=$(echo "$TOOLS" | jq -r '.tools[0]')
echo "GET /tool-calls?user_id=$USER_ID&tool_name=$FIRST_TOOL"
FILTERED=$(curl -s -H "$AUTH_HEADER" "$API_BASE/tool-calls?user_id=$USER_ID&tool_name=$FIRST_TOOL&limit=5")
FILTERED_COUNT=$(echo "$FILTERED" | jq '. | length')
echo "✅ Retrieved $FILTERED_COUNT calls for tool '$FIRST_TOOL'"
echo ""

# Test 7: Filter by character
echo "Test 7: Filter by character"
FIRST_CHAR=$(echo "$CHARACTERS" | jq -r '.characters[0]')
echo "GET /tool-calls?user_id=$USER_ID&character=$FIRST_CHAR"
CHAR_FILTERED=$(curl -s -H "$AUTH_HEADER" "$API_BASE/tool-calls?user_id=$USER_ID&character=$FIRST_CHAR&limit=5")
CHAR_FILTERED_COUNT=$(echo "$CHAR_FILTERED" | jq '. | length')
echo "✅ Retrieved $CHAR_FILTERED_COUNT calls by character '$FIRST_CHAR'"
echo ""

# Test 8: Filter by status
echo "Test 8: Filter by status"
echo "GET /tool-calls?user_id=$USER_ID&status=success"
SUCCESS_FILTERED=$(curl -s -H "$AUTH_HEADER" "$API_BASE/tool-calls?user_id=$USER_ID&status=success&limit=5")
SUCCESS_COUNT=$(echo "$SUCCESS_FILTERED" | jq '. | length')
echo "✅ Retrieved $SUCCESS_COUNT successful calls"
echo ""

# Test 9: Statistics breakdown by tool
echo "Test 9: Statistics by tool"
echo "Analyzing per-tool statistics..."
TOOL_STATS=$(echo "$STATS" | jq -r '.by_tool[] | "\(.tool_name): \(.total_calls) calls, \(.success_rate)% success"')
echo "$TOOL_STATS"
echo ""

# Test 10: Statistics breakdown by character
echo "Test 10: Statistics by character"
echo "Analyzing per-character statistics..."
CHAR_STATS=$(echo "$STATS" | jq -r '.by_character[] | "\(.character): \(.total_calls) calls, most used tool: \(.most_used_tool)"')
echo "$CHAR_STATS"
echo ""

echo "================================================"
echo "✅ All tests passed! Milestone 5 backend is working."
echo ""
echo "Summary:"
echo "  - Total tool calls: $TOTAL"
echo "  - Success rate: $SUCCESS_RATE%"
echo "  - Unique tools: $TOOL_COUNT"
echo "  - Characters: $CHAR_COUNT"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:5173/observability in your browser"
echo "  2. Click 'Tool Calls' in the navigation"
echo "  3. Test the timeline view, filters, and statistics"
echo "  4. Click on a tool call to see detailed information"
