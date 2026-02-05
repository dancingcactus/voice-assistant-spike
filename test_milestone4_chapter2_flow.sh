#!/bin/bash

# Test script for Milestone 4: Chapter 2 content flow
# - Creates a Chapter 2 user
# - Verifies auto-advance for hank_arrival
# - Triggers progression beat first_coordination stages 1→3
# - Triggers 1 optional beat
# - Verifies delivery statuses

set -euo pipefail

API_URL="http://localhost:8000/api/v1"
AUTH_TOKEN="dev_token_12345"
TEST_USER="m4c2_$(date +%s)"

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

echo "============================================="
echo "Milestone 4: Chapter 2 Content Flow Test"
echo "============================================="

echo "Creating test user at Chapter 2..."
CREATE_JSON=$(printf '{"starting_chapter":2,"user_id":"%s","tags":["milestone4_test_c2"]}' "$TEST_USER")
CREATE_RESP=$(api_call POST "/users/test" "$CREATE_JSON")
echo "$CREATE_RESP" | python3 -m json.tool || true

echo "Checking auto-advance ready (expect hank_arrival)..."
READY_RESP=$(api_call GET "/story/auto-advance-ready/$TEST_USER")
echo "$READY_RESP" | python3 -m json.tool || true
HAS_HANK=$(echo "$READY_RESP" | python3 - << 'PY'
import sys, json
data=json.load(sys.stdin)
print(any(x.get('beat_id')=='hank_arrival' for x in data))
PY
)
if [ "$HAS_HANK" != "True" ]; then
  echo -e "${RED}✗ FAIL: hank_arrival not in auto-advance queue${NC}"
  exit 1
fi
echo -e "${GREEN}✓ PASS: hank_arrival ready${NC}"

echo "Delivering hank_arrival..."
DELIVER_RESP=$(api_call POST "/story/auto-advance/$TEST_USER/hank_arrival")
echo "$DELIVER_RESP" | python3 -m json.tool || true

echo "Triggering first_coordination stages 1→3..."
api_call POST "/story/users/$TEST_USER/beats/first_coordination/trigger" '{"variant":"standard","stage":1}' > /dev/null
api_call POST "/story/users/$TEST_USER/beats/first_coordination/trigger" '{"variant":"standard","stage":2}' > /dev/null
api_call POST "/story/users/$TEST_USER/beats/first_coordination/trigger" '{"variant":"full","stage":3}' > /dev/null

echo "Triggering one optional beat..."
api_call POST "/story/users/$TEST_USER/beats/delilah_questions_hank/trigger" '{"variant":"standard"}' > /dev/null || true

echo "Fetching Chapter 2 beat statuses..."
BEATS_RESP=$(api_call GET "/story/chapters/2/beats?user_id=$TEST_USER")
echo "$BEATS_RESP" | python3 -m json.tool | sed -n '1,100p' || true

echo "Validating delivered beats..."
VALIDATION=$(echo "$BEATS_RESP" | python3 - << 'PY'
import sys, json
beats=json.load(sys.stdin)
status={b['id']:b['status'] for b in beats}
req=['hank_arrival','first_coordination']
opt=['delilah_questions_hank','hank_protective_moment']
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

if [ "$OPT_COUNT" -lt 1 ]; then
  echo -e "${RED}✗ FAIL: Expected at least 1 optional beat delivered (got $OPT_COUNT)${NC}"
  exit 1
fi

echo -e "${GREEN}✓ PASS: Chapter 2 beats delivered as expected${NC}"

echo "Done. Test user: $TEST_USER"

