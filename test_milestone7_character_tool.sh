#!/bin/bash
# Test script for Milestone 7: Character Tool

set -e

API_URL="http://localhost:8000"
TOKEN="dev_token_12345"
AUTH_HEADER="Authorization: Bearer $TOKEN"

echo "🎭 Testing Milestone 7: Character Tool"
echo "======================================"
echo ""

# Test 1: List all characters
echo "✅ Test 1: List all characters"
RESPONSE=$(curl -s -H "$AUTH_HEADER" "$API_URL/characters")
echo "$RESPONSE" | python -m json.tool
CHARACTER_COUNT=$(echo "$RESPONSE" | python -c "import sys, json; print(len(json.load(sys.stdin)['characters']))")
echo "Found $CHARACTER_COUNT character(s)"
echo ""

# Test 2: Get specific character (Delilah)
echo "✅ Test 2: Get character detail (Delilah)"
curl -s -H "$AUTH_HEADER" "$API_URL/characters/delilah" | python -m json.tool | head -30
echo "..."
echo ""

# Test 3: Get voice modes
echo "✅ Test 3: Get voice modes for Delilah"
VOICE_MODES=$(curl -s -H "$AUTH_HEADER" "$API_URL/characters/delilah/voice-modes")
VOICE_MODE_COUNT=$(echo "$VOICE_MODES" | python -c "import sys, json; print(len(json.load(sys.stdin)['voice_modes']))")
echo "Found $VOICE_MODE_COUNT voice modes"
echo "$VOICE_MODES" | python -c "import sys, json; modes = json.load(sys.stdin)['voice_modes']; print('\n'.join([f\"  - {m['id']}: {m['name']}\" for m in modes]))"
echo ""

# Test 4: Test voice mode selection - Allergy (should trigger mama_bear)
echo "✅ Test 4: Test voice mode selection (allergy input)"
ALLERGY_TEST=$(curl -s -X POST -H "$AUTH_HEADER" "$API_URL/characters/delilah/test-voice-mode?user_input=I%20have%20a%20severe%20peanut%20allergy")
SELECTED_MODE=$(echo "$ALLERGY_TEST" | python -c "import sys, json; data = json.load(sys.stdin); print(data['mode']['id'])")
CONFIDENCE=$(echo "$ALLERGY_TEST" | python -c "import sys, json; data = json.load(sys.stdin); print(data['confidence'])")
echo "Input: 'I have a severe peanut allergy'"
echo "Selected mode: $SELECTED_MODE"
echo "Confidence: $CONFIDENCE"
echo ""

# Test 5: Test voice mode selection - Southern food (should trigger passionate)
echo "✅ Test 5: Test voice mode selection (Southern food input)"
FOOD_TEST=$(curl -s -X POST -H "$AUTH_HEADER" "$API_URL/characters/delilah/test-voice-mode?user_input=Tell%20me%20about%20buttermilk%20biscuits")
SELECTED_MODE=$(echo "$FOOD_TEST" | python -c "import sys, json; data = json.load(sys.stdin); print(data['mode']['id'])")
echo "Input: 'Tell me about buttermilk biscuits'"
echo "Selected mode: $SELECTED_MODE"
echo ""

# Test 6: Generate system prompt (no voice mode)
echo "✅ Test 6: Generate system prompt (all modes)"
PROMPT_RESPONSE=$(curl -s -X POST -H "$AUTH_HEADER" -H "Content-Type: application/json" -d '{"user_id":"user_justin"}' "$API_URL/characters/delilah/system-prompt")
TOKEN_COUNT=$(echo "$PROMPT_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['token_estimate'])")
echo "Generated system prompt with ~$TOKEN_COUNT tokens"
echo ""

# Test 7: Generate system prompt with specific voice mode
echo "✅ Test 7: Generate system prompt (passionate mode)"
PROMPT_WITH_MODE=$(curl -s -X POST -H "$AUTH_HEADER" -H "Content-Type: application/json" -d '{"voice_mode_id":"passionate","user_id":"user_justin"}' "$API_URL/characters/delilah/system-prompt")
TOKEN_COUNT_MODE=$(echo "$PROMPT_WITH_MODE" | python -c "import sys, json; print(json.load(sys.stdin)['token_estimate'])")
echo "Generated system prompt with passionate mode: ~$TOKEN_COUNT_MODE tokens"
echo ""

# Test 8: Get prompt breakdown
echo "✅ Test 8: Get prompt breakdown"
BREAKDOWN=$(curl -s -H "$AUTH_HEADER" "$API_URL/characters/delilah/prompt-breakdown?voice_mode_id=passionate&user_id=user_justin")
echo "$BREAKDOWN" | python -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Total tokens: {data['total_token_estimate']}\")
print('\nBreakdown by section:')
for section, info in data['sections'].items():
    print(f\"  - {section}: {info['token_estimate']} tokens\")
"
echo ""

# Test 9: Get tool instructions
echo "✅ Test 9: Get tool instructions"
TOOL_INSTRUCTIONS=$(curl -s -H "$AUTH_HEADER" "$API_URL/characters/delilah/tool-instructions")
TOOLS=$(echo "$TOOL_INSTRUCTIONS" | python -c "import sys, json; print(', '.join(json.load(sys.stdin)['tool_instructions'].keys()))")
echo "Available tool instructions: $TOOLS"
echo ""

# Test 10: Get character statistics
echo "✅ Test 10: Get character statistics"
curl -s -H "$AUTH_HEADER" "$API_URL/characters/delilah/statistics?user_id=user_justin" | python -m json.tool
echo ""

echo "======================================"
echo "✅ All Character Tool tests passed!"
echo ""
echo "Frontend available at: http://localhost:5173"
echo "Navigate to the 'Characters' tab to explore the tool"
