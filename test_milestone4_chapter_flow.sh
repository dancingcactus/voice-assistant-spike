#!/bin/bash

# Test script for Milestone 4: Chapter 1 content flow
# - Creates a Chapter 1 user
# - Verifies auto-advance for silent_period
# - Triggers required Chapter 1 beats in order
# - Triggers 2 optional beats
# - Verifies beat delivery statuses

set -euo pipefail

API_URL="http://localhost:8000/api/v1"
AUTH_TOKEN="dev_token_12345"
TEST_USER="m4_$(date +%s)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

api_call() {
  local method=$1; shift
  local endpoint=$1; shift
  local data=${1:-}
  if [ -z "$data" ]; then
    curl -s -X "$method" \
      -H "Authorization: Bearer $AUTH_TOKEN" \
      -H "Content-Type: application/json" \
      "$API_URL$endpoint"
  else
    curl -s -X "$method" \
      -H "Authorization: Bearer $AUTH_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$data" \
      "$API_URL$endpoint"
  fi
}

echo "========================================="
echo "Milestone 4: Chapter 1 Content Flow Test"
echo "========================================="

echo "Creating test user at Chapter 1..."
CREATE_JSON=$(printf '{"starting_chapter":1,"user_id":"%s","tags":["milestone4_test"]}' "$TEST_USER")
CREATE_RESP=$(api_call POST "/users/test" "$CREATE_JSON")
echo "$CREATE_RESP" | python3 -m json.tool || true

echo "Checking auto-advance ready (expect silent_period)..."
READY_RESP=$(api_call GET "/story/auto-advance-ready/$TEST_USER")
echo "$READY_RESP" | python3 -m json.tool || true
HAS_SILENT=$(echo "$READY_RESP" | python3 - "$TEST_USER" << 'PY'
import sys, json
data=json.load(sys.stdin)
print(any(x.get('beat_id')=='silent_period' for x in data))
PY
)
if [ "$HAS_SILENT" != "True" ]; then
  echo -e "${RED}✗ FAIL: silent_period not in auto-advance queue${NC}"
  exit 1
fi
echo -e "${GREEN}✓ PASS: silent_period ready${NC}"

echo "Delivering silent_period..."
DELIVER_RESP=$(api_call POST "/story/auto-advance/$TEST_USER/silent_period")
echo "$DELIVER_RESP" | python3 -m json.tool || true

echo "Triggering required Chapter 1 beats in order..."
api_call POST "/story/users/$TEST_USER/beats/first_words/trigger" '{"variant":"standard"}' > /dev/null
api_call POST "/story/users/$TEST_USER/beats/discovery_of_knowledge/trigger" '{"variant":"standard"}' > /dev/null
api_call POST "/story/users/$TEST_USER/beats/non_food_request/trigger" '{"variant":"standard"}' > /dev/null
api_call POST "/story/users/$TEST_USER/beats/anchor_discovery/trigger" '{"variant":"full"}' > /dev/null
api_call POST "/story/users/$TEST_USER/beats/first_successful_help/trigger" '{"variant":"standard"}' > /dev/null

echo "Triggering two optional beats..."
api_call POST "/story/users/$TEST_USER/beats/the_math_moment/trigger" '{"variant":"brief"}' > /dev/null
api_call POST "/story/users/$TEST_USER/beats/the_silence_between/trigger" '{"variant":"standard"}' > /dev/null

echo "Fetching Chapter 1 beat statuses..."
BEATS_RESP=$(api_call GET "/story/chapters/1/beats?user_id=$TEST_USER")
echo "$BEATS_RESP" | python3 -m json.tool | sed -n '1,100p' || true

echo "Validating delivered beats..."
VALIDATION=$(echo "$BEATS_RESP" | python3 - << 'PY'
import sys, json
beats=json.load(sys.stdin)
status={b['id']:b['status'] for b in beats}
req=[
  'silent_period','first_words','discovery_of_knowledge',
  'non_food_request','anchor_discovery','first_successful_help'
]
opt=['the_math_moment','the_silence_between','sensory_limitation','timer_anxiety']
missing=[b for b in req if status.get(b)!='delivered']
opt_count=sum(1 for b in opt if status.get(b)=='delivered')
print(json.dumps({
  'missing_required': missing,
  'opt_delivered_count': opt_count
}))
PY
)
echo "$VALIDATION" | python3 -m json.tool

MISSING_COUNT=$(echo "$VALIDATION" | python3 -c 'import sys,json; print(len(json.load(sys.stdin)["missing_required"]))')
OPT_COUNT=$(echo "$VALIDATION" | python3 -c 'import sys,json; print(json.load(sys.stdin)["opt_delivered_count"])')

if [ "$MISSING_COUNT" -ne 0 ]; then
  echo -e "${RED}✗ FAIL: Missing required delivered beats${NC}"
  exit 1
fi

if [ "$OPT_COUNT" -lt 2 ]; then
  echo -e "${RED}✗ FAIL: Expected at least 2 optional beats delivered (got $OPT_COUNT)${NC}"
  exit 1
fi

echo -e "${GREEN}✓ PASS: Chapter 1 beats delivered as expected${NC}"

echo "Done. Test user: $TEST_USER"

