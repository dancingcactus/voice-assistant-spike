# Phase 4.5: Multi-Character Coordination - Testing Guide

**Version:** 1.0
**Last Updated:** February 11, 2026
**Status:** Draft

---

## Overview

This guide provides step-by-step manual testing procedures for Phase 4.5. Use this to validate intent detection, character planning, inter-character dialogue, and coordination tracking.

**Note:** Full Chapter 2 narrative story beats are deferred to a future story-focused phase. This phase focuses on coordination mechanics.

**Purpose:**

- Validate multi-character coordination works naturally
- Verify story beats trigger at appropriate moments
- Ensure handoffs feel conversational, not robotic
- Catch edge cases in intent classification
- Document Chapter 2 narrative arc experience

**Who Uses This:**

- Developers completing milestones
- AI assistants validating implementations
- Family members testing naturalness
- Future developers understanding feature behavior

---

## Prerequisites

### Required Services

Before starting any tests, ensure these services are running:

**Backend API:**

```bash
cd backend
source venv/bin/activate
python -m uvicorn src.main:app --reload --port 8000
```

- Should see: "Application startup complete"
- Health check: `curl http://localhost:8000/api/health`
- Expected: `{"status": "healthy"}`

**Frontend (includes Observability Dashboard):**

```bash
cd frontend
npm run dev
```

- Should see: "Local: http://localhost:5173"
- Open in browser: `http://localhost:5173`
- Observability: `http://localhost:5173/observability`
- No console errors should appear

---

### Test Data

**Required Data:**

- Test user with both Delilah and Hank active
- Clean story state (no beats delivered)
- Both Delilah and Hank characters enabled

**Setup Commands:**

```bash
# Create fresh test user for Chapter 2
cd backend
python scripts/create_test_user.py --chapter 2 --user-id "test_phase45"

# Verify user created
cat data/users/test_phase45.json
```

**Expected User State:**

```json
{
  "user_id": "test_phase45",
  "current_chapter": 2,
  "delivered_beats": [],
  "chapter_progress": {
    "2": {
      "chapter": 2,
      "started_at": "2026-02-11T...",
      "completed_at": null,
      "required_beats_delivered": [],
      "optional_beats_delivered": [],
      "interaction_count": 0
    }
  }
}
```

---

### Environment Configuration

**Environment Variables:**

```bash
# Backend .env
ENV=development
API_BASE_URL=http://localhost:8000
LOG_LEVEL=DEBUG
CLAUDE_API_KEY=your_api_key_here

# TTS Configuration
TTS_PROVIDER=piper  # or "elevenlabs"
```

**Browser:**

- Chrome or Firefox (latest version)
- JavaScript enabled
- Clear browser cache if testing UI changes
- Open Developer Console for debugging

---

## Milestone 1: Intent Detection System

### Test 1: Single Cooking Intent

**Objective:** Verify cooking queries are correctly classified

**Prerequisites:**

- Backend running with debug endpoint active
- Test user: `test_phase45`

**Steps:**

1. **Test Intent Detection via Debug Endpoint**

   ```bash
   curl -X POST http://localhost:8000/api/debug/detect-intent \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Set a timer for 30 minutes",
       "user_id": "test_phase45"
     }'
   ```

   - **Expected:**
     ```json
     {
       "intent_result": {
         "intent": "cooking",
         "confidence": 0.95,
         "classification_method": "llm",
         "sub_tasks": null
       },
       "character_plan": null,
       "processing_time_ms": 250
     }
     ```
   - **Actual:** _[Fill in during testing]_
   - **Pass/Fail:** _[Mark after testing]_
   - **Note:** LLM classification may take 200-500ms

2. **Test Another Cooking Query**

   ```bash
   curl -X POST http://localhost:8000/api/debug/detect-intent \
     -H "Content-Type: application/json" \
     -d '{
       "query": "How do I make cornbread?",
       "user_id": "test_phase45"
     }'
   ```

   - **Expected:** `intent: "cooking"`, `confidence: > 0.90`
   - **Actual:** _[Fill in during testing]_

3. **Test Edge Case - Ambiguous Timer**

   ```bash
   curl -X POST http://localhost:8000/api/debug/detect-intent \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Set a timer",
       "user_id": "test_phase45"
     }'
   ```

   - **Expected:** `intent: "cooking"` (timer defaults to cooking)
   - **Confidence:** May be lower (0.7-0.8)
   - **Actual:** _[Fill in during testing]_

**Expected Results Summary:**

- ✅ Cooking queries classified as "cooking"
- ✅ Confidence scores > 0.90 for clear queries
- ✅ Confidence 0.7-0.9 for ambiguous queries
- ✅ Processing time < 200ms

**Troubleshooting:**

- **Low confidence:** Check intent pattern definitions in `backend/src/config/intent_patterns.json`
- **Wrong classification:** Verify pattern matching logic in `IntentDetector._apply_rules()`
- **High latency:** Check if loading patterns on every call (should be cached)

---

### Test 2: Single Household Intent

**Objective:** Verify household/list queries are correctly classified

**Steps:**

1. **Test Shopping List Intent**

   ```bash
   curl -X POST http://localhost:8000/api/debug/detect-intent \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Add milk to my shopping list",
       "user_id": "test_phase45"
     }'
   ```

   - **Expected:** `intent: "household"`, `confidence: > 0.90`
   - **Actual:** _[Fill in during testing]_

2. **Test Calendar Intent**

   ```bash
   curl -X POST http://localhost:8000/api/debug/detect-intent \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What's on my calendar tomorrow?",
       "user_id": "test_phase45"
     }'
   ```

   - **Expected:** `intent: "household"`, `confidence: > 0.90`
   - **Actual:** _[Fill in during testing]_

---

### Test 3: Multi-Task Intent

**Objective:** Verify multi-part queries are parsed into separate tasks

**Steps:**

1. **Test Multi-Task Parsing**

   ```bash
   curl -X POST http://localhost:8000/api/debug/detect-intent \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Set a timer for 30 minutes and add milk to my shopping list",
       "user_id": "test_phase45"
     }'
   ```

   - **Expected:**
     ```json
     {
       "intent_result": {
         "intent": "multi_task",
         "confidence": 0.90,
         "sub_tasks": [
           {
             "text": "set a timer for 30 minutes",
             "intent": "cooking",
             "confidence": 0.95
           },
           {
             "text": "add milk to my shopping list",
             "intent": "household",
             "confidence": 0.92
           }
         ]
       }
     }
     ```
   - **Actual:** _[Fill in during testing]_

2. **Test Complex Multi-Task**

   ```bash
   curl -X POST http://localhost:8000/api/debug/detect-intent \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Find me a recipe for lasagna, set a timer for 45 minutes, and add pasta to my list",
       "user_id": "test_phase45"
     }'
   ```

   - **Expected:** `intent: "multi_task"` with 3 sub_tasks (all cooking-related, may stay as single cooking intent)
   - **Actual:** _[Fill in during testing]_

---

### Test 4: Ambiguous/General Intent

**Objective:** Verify unclear queries default to general intent

**Steps:**

1. **Test General Knowledge Query**

   ```bash
   curl -X POST http://localhost:8000/api/debug/detect-intent \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What's the capital of France?",
       "user_id": "test_phase45"
     }'
   ```

   - **Expected:** `intent: "general"`, `confidence: < 0.6`
   - **Actual:** _[Fill in during testing]_

2. **Test Empty Query**

   ```bash
   curl -X POST http://localhost:8000/api/debug/detect-intent \
     -H "Content-Type: application/json" \
     -d '{
       "query": "",
       "user_id": "test_phase45"
     }'
   ```

   - **Expected:** `intent: "general"`, `confidence: 0.0` or error handling
   - **Actual:** _[Fill in during testing]_

**Milestone 1 Completion Criteria:**

- ✅ All single intent tests pass (cooking, household, smart_home, general)
- ✅ Multi-task parsing works for 2-3 task queries
- ✅ Confidence scores reflect classification certainty
- ✅ Processing time < 200ms for all queries
- ✅ Edge cases handled gracefully (empty query, ambiguous)

---

## Milestone 2: Character Planning System

### Test 5: Single Character Assignment

**Objective:** Verify intents are correctly mapped to characters

**Prerequisites:**

- Milestone 1 complete and passing
- Character planner integrated with intent detector

**Steps:**

1. **Test Cooking → Delilah Assignment**

   ```bash
   curl -X POST http://localhost:8000/api/debug/create-plan \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Set a timer for 30 minutes",
       "user_id": "test_phase45"
     }'
   ```

   - **Expected:**
     ```json
     {
       "intent_result": {
         "intent": "cooking",
         "confidence": 0.95
       },
       "character_plan": {
         "tasks": [
           {
             "character": "delilah",
             "task_description": "set timer for 30 minutes",
             "intent": "cooking",
             "confidence": 0.95,
             "requires_handoff": false
           }
         ],
         "execution_mode": "single",
         "total_confidence": 0.95
       }
     }
     ```
   - **Actual:** _[Fill in during testing]_

2. **Test Household → Hank Assignment**

   ```bash
   curl -X POST http://localhost:8000/api/debug/create-plan \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Add eggs to my shopping list",
       "user_id": "test_phase45"
     }'
   ```

   - **Expected:** `character: "hank"`, `execution_mode: "single"`
   - **Actual:** _[Fill in during testing]_

---

### Test 6: Multi-Character Sequential Plan

**Objective:** Verify multi-task queries create sequential character plans

**Steps:**

1. **Test Sequential Task Assignment**

   ```bash
   curl -X POST http://localhost:8000/api/debug/create-plan \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Set a timer for 30 minutes and add milk to my list",
       "user_id": "test_phase45"
     }'
   ```

   - **Expected:**
     ```json
     {
       "character_plan": {
         "tasks": [
           {
             "character": "delilah",
             "task_description": "set timer for 30 minutes",
             "requires_handoff": true,
             "handoff_from": null
           },
           {
             "character": "hank",
             "task_description": "add milk to shopping list",
             "requires_handoff": false,
             "handoff_from": "delilah"
           }
         ],
         "execution_mode": "sequential",
         "total_confidence": 0.935
       }
     }
     ```
   - **Actual:** _[Fill in during testing]_
   - **Verify:** First task requires_handoff=true, second task handoff_from="delilah"

---

### Test 7: Fallback Handling

**Objective:** Verify low-confidence queries fall back to Delilah

**Steps:**

1. **Test Low Confidence Query**

   ```bash
   curl -X POST http://localhost:8000/api/debug/create-plan \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What is this?",
       "user_id": "test_phase45"
     }'
   ```

   - **Expected:** `character: "delilah"` (default fallback)
   - **Confidence:** Low (< 0.6)
   - **Actual:** _[Fill in during testing]_

**Milestone 2 Completion Criteria:**

- ✅ Cooking intents assigned to Delilah
- ✅ Household intents assigned to Hank
- ✅ Multi-task queries create sequential plans
- ✅ Handoff flags set correctly
- ✅ Fallback to Delilah for low confidence
- ✅ Planning completes in < 100ms

---

## Milestone 3: Inter-Character Dialogue System

### Test 8: Handoff Generation

**Objective:** Verify natural handoff dialogue is generated

**Prerequisites:**

- Milestone 2 complete
- Handoff templates loaded
- Character relationships defined

**Steps:**

1. **Test Delilah → Hank Handoff (via full conversation)**

   ```bash
   # Send multi-task query via conversation API
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test_phase45",
       "message": "Set a timer for 30 minutes and add flour to my list"
     }'
   ```

   - **Expected Response Structure:**
     ```
     Delilah: "Sugar, I've got that timer set for 30 minutes. [HANDOFF] Hank, can you add flour to the list?"
     Hank: "Aye, Cap'n. Flour's on the list."
     ```
   - **Actual:** _[Fill in during testing]_
   - **Verify:**
     - Delilah completes her task
     - Handoff directly addresses Hank (not third-person reference)
     - Hank acknowledges and completes his task
     - Both responses feel natural and conversational

2. **Test Handoff Template Variety**

   Repeat the same query 3 times in sequence:

   ```bash
   # Query 1
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_phase45", "message": "Set timer for 20 minutes and add milk to list"}'

   # Query 2 (same pattern)
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_phase45", "message": "Set timer for 15 minutes and add eggs to list"}'

   # Query 3 (same pattern)
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_phase45", "message": "Set timer for 25 minutes and add butter to list"}'
   ```

   - **Expected:** Different handoff templates used (no immediate repeats)
   - **Actual:** _[Record handoff text for each]_
     - Query 1: _[handoff text]_
     - Query 2: _[handoff text]_
     - Query 3: _[handoff text]_
   - **Verify:** At least 2 different templates used across 3 queries

---

### Test 9: Character References

**Objective:** Verify characters can reference each other naturally

**Steps:**

1. **Test Single Character Mentioning Other**

   ```bash
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test_phase45",
       "message": "Who should help me with my shopping list?"
     }'
   ```

   - **Expected:** Hank responds (household intent) and may reference Delilah:
     - "That'd be me, Cap'n. Lists and such. Miss Lila handles the recipes."
   - **Actual:** _[Fill in during testing]_

2. **Test Character Expertise Deference**

   ```bash
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test_phase45",
       "message": "Who should help me cook dinner?"
     }'
   ```

   - **Expected:** Delilah responds (cooking intent):
     - "Oh honey, that's what I do best! Hank's wonderful with lists and schedules, but cooking? That's my lane."
   - **Actual:** _[Fill in during testing]_

**Milestone 3 Completion Criteria:**

- ✅ Handoffs feel natural and character-appropriate
- ✅ Delilah uses warm Southern terms in handoffs
- ✅ Hank uses gruff maritime terms in handoffs
- ✅ Handoff templates rotate (variety achieved)
- ✅ Character references appear naturally
- ✅ Multi-character responses combine smoothly

---

## Milestone 4: Coordination Tracking

### Test 10: Coordination Event Logging

**Objective:** Verify coordination events log correctly

**Prerequisites:**

- Fresh test user
- Both Delilah and Hank active

**Steps:**

1. **Verify Initial State**

   ```bash
   curl http://localhost:8000/api/coordination/metrics/test_phase45
   ```

   - **Expected:**
     ```json
     {
       "user_id": "test_phase45",
       "metrics": {
         "total_handoffs": 0,
         "handoff_success_rate": 0.0,
         "delilah_to_hank_count": 0,
         "hank_to_delilah_count": 0,
         "multi_task_completions": 0,
         "sign_up_pattern_count": 0,
         "template_usage": {},
         "average_handoff_latency_ms": 0.0
       }
     }
     ```
   - **Actual:** _[Fill in during testing]_

2. **Execute Multi-Task with Handoff**

   ```bash
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test_phase45",
       "message": "Set a timer for 30 minutes and add milk to my list"
     }'
   ```

   - **Expected Response:**
     - Delilah sets timer
     - Delilah hands off to Hank: "Hank, can you add milk to the list?"
     - Hank completes task: "Aye, Cap'n. Milk's on the list."
   - **Actual:** _[Fill in during testing]_

3. **Verify Event Logged**

   ```bash
   curl http://localhost:8000/api/coordination/events/test_phase45?limit=5
   ```

   - **Expected:**
     ```json
     {
       "user_id": "test_phase45",
       "events": [
         {
           "event_type": "handoff",
           "from_character": "delilah",
           "to_character": "hank",
           "intent": "household",
           "template_used": "delilah_to_hank_...",
           "success": true
         },
         {
           "event_type": "multi_task",
           "success": true,
           "metadata": {
             "tasks": 2,
             "characters": ["delilah", "hank"]
           }
         }
       ]
     }
     ```
   - **Actual:** _[Fill in during testing]_

4. **Verify Metrics Updated**

   ```bash
   curl http://localhost:8000/api/coordination/metrics/test_phase45
   ```

   - **Expected:**
     - `total_handoffs: 1`
     - `delilah_to_hank_count: 1`
     - `multi_task_completions: 1`
     - `handoff_success_rate: 1.0`
   - **Actual:** _[Fill in during testing]_

---

### Test 11: Sign-Up Pattern Tracking

**Objective:** Verify sign-up pattern events are logged

**Prerequisites:**

- Test user with some coordination history

**Steps:**

1. **Trigger Sign-Up Pattern**

   ```bash
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test_phase45",
       "message": "Help me plan dinner tonight"
     }'
   ```

   - **Expected Response:**
     - Delilah: "Sugar, I got you. Let me come up with a plan."
     - Hank: "Aye, and I be gettin' the list."
   - **Actual:** _[Fill in during testing]_

2. **Verify Sign-Up Event Logged**

   ```bash
   curl http://localhost:8000/api/coordination/events/test_phase45?limit=5
   ```

   - **Expected:**
     - Event with `event_type: "sign_up"`
     - Both characters claimed work at beginning
   - **Actual:** _[Fill in during testing]_

3. **Verify Metrics Updated**

   ```bash
   curl http://localhost:8000/api/coordination/metrics/test_phase45
   ```

   - **Expected:** `sign_up_pattern_count: 1`
   - **Actual:** _[Fill in during testing]_

---

### Test 12: Template Variety Tracking

**Objective:** Verify handoff template usage is tracked

**Prerequisites:**

- Test user with coordination history

**Steps:**

1. **Execute Multiple Handoffs**

   Send 5 multi-task queries in sequence to generate multiple handoffs:

   ```bash
   for i in {1..5}; do
     curl -X POST http://localhost:8000/api/conversation/message \
       -H "Content-Type: application/json" \
       -d "{\"user_id\": \"test_phase45\", \"message\": \"Set timer for $((i*10)) minutes and add item$i to list\"}"
     sleep 2
   done
   ```

2. **Verify Template Variety**

   ```bash
   curl http://localhost:8000/api/coordination/metrics/test_phase45
   ```

   - **Expected:**
     - `template_usage` object shows multiple templates used
     - No single template used > 3 times (shows variety)
     - Multiple templates in `delilah_to_hank` category
   - **Actual:** _[Fill in during testing]_

3. **Check Recent Events**

   ```bash
   curl http://localhost:8000/api/coordination/events/test_phase45?limit=10
   ```

   - **Expected:**
     - Different `template_used` values across events
     - Natural variety in handoff phrasing
   - **Actual:** _[Fill in during testing]_

---

### Test 13: Coordination Milestones

**Objective:** Verify milestone detection

**Prerequisites:**

- Fresh test user

**Steps:**

1. **Check Initial Milestones**

   ```bash
   curl http://localhost:8000/api/coordination/milestones/test_phase45
   ```

   - **Expected:** All milestones false
   - **Actual:** _[Fill in during testing]_

2. **Complete First Handoff**

   ```bash
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test_phase45",
       "message": "Set timer and add flour to list"
     }'
   ```

3. **Verify First Handoff Milestone**

   ```bash
   curl http://localhost:8000/api/coordination/milestones/test_phase45
   ```

   - **Expected:**
     ```json
     {
       "first_handoff": true,
       "first_multi_task": true,
       "first_sign_up": false,
       "five_handoffs": false,
       "all_templates_used": false
     }
     ```
   - **Actual:** _[Fill in during testing]_

4. **Complete 5 Handoffs**

   Execute 4 more multi-task queries, then check milestones:

   ```bash
   curl http://localhost:8000/api/coordination/milestones/test_phase45
   ```

   - **Expected:** `five_handoffs: true`
   - **Actual:** _[Fill in during testing]_

**Milestone 4 Completion Criteria:**

- ✅ All coordination events log correctly
- ✅ Metrics calculate accurately
- ✅ Sign-up patterns detected
- ✅ Template variety tracked
- ✅ Milestones detected correctly
- ✅ Data visible in observability dashboard

---

## Milestone 5: Integration & Polish

### Test 14: Full E2E Multi-Character Conversation

**Objective:** Test complete pipeline from query to multi-character response with coordination tracking

**Prerequisites:**

- All systems integrated
- Fresh test user

**Steps:**

1. **Complete Natural Multi-Character Interactions**

   Send the following queries in sequence, pausing between each to simulate natural conversation:

   ```bash
   # Query 1: Trigger Hank's entrance
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_phase45", "message": "Set a timer for 30 minutes and add milk to my list"}'
   
   # Query 2: Delilah introduces herself
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_phase45", "message": "How do I make biscuits?"}'
   
   # Query 3: Existence question (trigger clash)
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_phase45", "message": "What are you? Are you conscious?"}'
   
   # Query 4: Multi-task (trigger first collaboration)
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_phase45", "message": "Help me plan tonight'\''s dinner and make a shopping list"}'
   
   # Query 5: Verify normal operation after chapter complete
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_phase45", "message": "Set a timer for 45 minutes and add eggs to my list"}'
   ```

   - **Expected:** All handoffs work naturally, coordination events logged, observability dashboard shows metrics
   - **Actual:** _[Document experience for each query]_

2. **Verify Response Times**

   Measure end-to-end latency for multi-character query:

   ```bash
   # Use time command
   time curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_phase45", "message": "Set timer and add butter to list"}'
   ```

   - **Expected:** < 3s total response time (95th percentile)
   - **Actual:** _[Record time]_

---

### Test 15: Observability Dashboard Verification

**Objective:** Verify all Phase 4.5 tools display correctly

**Prerequisites:**

- Previous tests completed (data exists)
- Frontend running

**Steps:**

1. **Open Observability Dashboard**

   - Navigate to: `http://localhost:5173/observability`
   - **Expected:** Dashboard loads without errors
   - **Actual:** _[Pass/Fail]_

2. **Intent Detection Log Tool**

   - Click "Intent Detection" tab
   - **Expected:**
     - See list of all previous queries
     - Each entry shows: query, intent, confidence, timestamp
     - Can filter by intent category
     - Can see multi-task breakdown
   - **Actual:** _[Fill in during testing]_

3. **Character Plan Viewer Tool**

   - Click "Character Plans" tab
   - **Expected:**
     - See list of all character plans
     - Each plan shows: query, assigned characters, execution mode
     - Sequential plans show handoff points
     - Can expand plan to see task details
   - **Actual:** _[Fill in during testing]_

4. **Chapter 2 Progress Tool**

   - Click "Story" tab → "Chapter 2 Progress"
   - **Expected:**
     - See Chapter 2 beat timeline
     - Shows which beats delivered (checkmarks)
     - Shows which beats remain
     - Displays chapter completion status
     - Can preview beat variants
   - **Actual:** _[Fill in during testing]_

---

### Test 16: Error Handling & Graceful Degradation

**Objective:** Verify system handles failures gracefully

**Steps:**

1. **Test Intent Detection Failure**

   Temporarily break intent detection (modify code to throw error):

   ```python
   # In IntentDetector.detect()
   raise Exception("Test error")
   ```

   Send query:

   ```bash
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_phase45", "message": "Set a timer"}'
   ```

   - **Expected:**
     - System falls back to Delilah (default)
     - User still gets a response (doesn't crash)
     - Error logged for debugging
   - **Actual:** _[Fill in during testing]_

   **Restore code after testing**

2. **Test Character Planning Failure**

   Temporarily break character planner:

   ```python
   # In CharacterPlanner.create_plan()
   raise Exception("Test error")
   ```

   Send query:

   ```bash
   curl -X POST http://localhost:8000/api/conversation/message \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test_phase45", "message": "Add milk to list"}'
   ```

   - **Expected:**
     - System falls back to single character (Delilah)
     - User gets response
     - Error logged
   - **Actual:** _[Fill in during testing]_

   **Restore code after testing**

**Milestone 5 Completion Criteria:**

- ✅ Full E2E pipeline functional
- ✅ Response latency < 3s for 95% of queries
- ✅ Observability tools display all Phase 4.5 data
- ✅ Error handling gracefully degrades to single character
- ✅ No regressions in Phase 1-4 features
- ✅ Manual testing confirms natural experience

---

## Performance Benchmarks

### Latency Targets

Measure latency for 20+ test queries and calculate percentiles:

| Metric | Target | Actual | Pass/Fail |
|--------|--------|--------|-----------|
| Intent Detection (p50) | < 100ms | _[measure]_ | _[ ]_ |
| Intent Detection (p95) | < 200ms | _[measure]_ | _[ ]_ |
| Character Planning (p50) | < 50ms | _[measure]_ | _[ ]_ |
| Character Planning (p95) | < 100ms | _[measure]_ | _[ ]_ |
| Single-char Response (p50) | < 1.5s | _[measure]_ | _[ ]_ |
| Single-char Response (p95) | < 2.5s | _[measure]_ | _[ ]_ |
| Multi-char Response (p50) | < 2.5s | _[measure]_ | _[ ]_ |
| Multi-char Response (p95) | < 3.5s | _[measure]_ | _[ ]_ |

**Measurement Script:**

```bash
cd backend
python scripts/measure_phase45_performance.py --iterations 20 --user test_phase45
```

---

## User Acceptance Testing

### Family Member Testing

**Participants:** 2-3 family members

**Scenario:** Natural kitchen interaction over 2-3 days

**Instructions:**

"Use the voice assistant normally for cooking and household tasks. We're testing if the two characters (Delilah and Hank) work well together."

**Feedback Questions:**

1. **Naturalness:** Did the handoffs between characters feel natural? (1-5 scale)
2. **Helpfulness:** Did the right character respond to your questions? (1-5 scale)
3. **Story Experience:** Did you enjoy discovering Hank as a new character? (1-5 scale)
4. **Confusion:** Were you ever confused about which character was talking? (Yes/No)
5. **Preference:** Do you prefer having two characters or just one? (Open-ended)

**Success Criteria:**

- Average naturalness rating: > 4.0
- Average helpfulness rating: > 4.0
- Confusion rate: < 20% of interactions

---

## Troubleshooting

### Common Issues

**Issue:** Intent classification incorrect

- **Check:** `backend/src/config/intent_patterns.json` - Are patterns comprehensive?
- **Check:** Logs in `backend/data/tool_logs/intent_logs.jsonl` - What confidence scores?
- **Fix:** Add more patterns or adjust existing patterns

**Issue:** No handoff dialogue generated

- **Check:** `backend/src/config/handoff_templates.json` - Are templates loaded?
- **Check:** Character plan has `requires_handoff: true` for first task
- **Fix:** Verify `DialogueSynthesizer.synthesize_handoff()` is called

**Issue:** Story beat not triggering

- **Check:** User's story state - Is chapter active? Is previous beat delivered?
- **Check:** Beat trigger conditions in `story/beats/chapter2.json`
- **Check:** Story event detection logic in `StoryEngine`
- **Fix:** Verify trigger conditions are met, check beat loading

**Issue:** Response latency too high (> 3s)

- **Check:** Logs for component timings
- **Check:** Is caching enabled for configs and beat definitions?
- **Check:** Is LLM call taking too long?
- **Fix:** Enable caching, optimize LLM prompt, consider parallel execution

**Issue:** Observability dashboard not showing data

- **Check:** Backend API is reachable from frontend
- **Check:** CORS settings allow requests from frontend
- **Check:** Data files exist in `backend/data/tool_logs/`
- **Fix:** Verify API endpoints return data, check network tab for errors

---

## Phase 4.5 Acceptance Checklist

**Before marking Phase 4.5 complete, verify:**

- [ ] All 5 milestones complete
- [ ] All E2E Playwright tests passing
- [ ] All manual tests in this guide executed and passing
- [ ] Performance benchmarks met (latency targets)
- [ ] User acceptance testing completed with positive feedback
- [ ] Observability dashboard displays all Phase 4.5 data correctly
- [ ] Error handling verified (graceful degradation works)
- [ ] No regressions in Phase 1-4 functionality
- [ ] Documentation complete (PRD, Architecture, Implementation Plan, this Testing Guide)
- [ ] Code committed to `phase4.5` branch
- [ ] Phase tagged: `git tag phase4.5-complete`

---

## Appendix

### Sample Test Queries

**Single Intent (Cooking):**

- "Set a timer for 30 minutes"
- "How do I make cornbread?"
- "What's a good recipe for spaghetti?"
- "Convert 2 cups to milliliters"

**Single Intent (Household):**

- "Add milk to my shopping list"
- "What's on my calendar tomorrow?"
- "Create a reminder for 3pm"
- "Show me my todo list"

**Multi-Task:**

- "Set a timer for 30 minutes and add flour to my list"
- "Find me a recipe for lasagna and add the ingredients to my list"
- "Set a timer for 45 minutes, turn on the kitchen lights, and add eggs to my list"

**Ambiguous/General:**

- "What's the weather?"
- "Tell me a joke"
- "What is life?"
- "Are you real?"

### Expected Chapter 2 Beat Sequence

1. **hanks_entrance** - First multi-task query
2. **first_words_with_hank** - Next interaction (sequential)
3. **the_clash** - Existence question trigger
4. **first_collaboration** - Multi-task after clash

**Optional Beats:**

- **task_assignment_discussion** - Ambiguous query (who should handle)
- **mutual_respect_moment** - After several collaborations

---

**Document Owner:** Justin
**Last Updated:** February 11, 2026
**Next Update:** After Milestone 1 completion

---
