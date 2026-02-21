# Phase 5.1: Robust Character Coordination - Implementation Plan

**Version:** 1.0
**Last Updated:** February 20, 2026
**Status:** Not Started
**Branch:** `phase5.1`

---

## References

- **PRD:** [PRD.md](PRD.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Phase 5 Plan:** [../IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md)

---

## Overview

Four milestones, each independently testable and committed separately. Build foundation first, avoid touching `conversation_manager.py` until the new components are validated in isolation.

**Estimated Duration:** 2–3 weeks

---

## Milestone 1: Models & Foundation

**Status:** Not Started
**Goal:** New data models, `ConversationStateManager`, and extracted `CharacterExecutor`. No behaviour change — the new code is not wired into the conversation flow yet.

### Files Created

#### `backend/src/models/routing.py`
- `TurnType` enum: `AFFIRMATION | NEW_REQUEST | CLARIFICATION | REJECTION`
- `TurnClassification` dataclass: `turn_type`, `confidence`, `reasoning`
- `PendingFollowup` dataclass: `character`, `task_summary`, `source`, `items`
- `RoutingDecision` dataclass: `primary_character`, `pending_followup`, `rationale`
- `CoordinationMode` enum: `IDLE | PROPOSING | AWAITING_ACTION`
- `CoordinationState` dataclass: `mode`, `pending_character`, `pending_task`, `pending_items`, `proposed_summary`, `expires_at`, `last_updated`

#### `backend/src/core/conversation_state.py`
- `ConversationStateManager` class
  - `get_state(context) -> CoordinationState`
  - `set_proposing(context, pending_character, pending_task, proposed_summary, items=None)`
  - `set_awaiting_action(context, pending_character, pending_task, items=None)`
  - `clear(context)`
  - `is_expired(state) -> bool`
  - Reads + converts existing `deferred_tasks` keys for backward compatibility

#### `backend/src/core/character_executor.py`
- `CharacterResponse` dataclass: `character`, `text`, `voice_mode`, `tool_calls_made`, `handoff_signal`
- `CharacterExecutor` class
  - `execute(character, task_description, context, session_id, user_id) -> CharacterResponse`
  - Extracted directly from `_handle_phase45_multi_character()` and `_execute_deferred_tasks()` in `conversation_manager.py`
  - Intercepts `request_handoff` tool calls: sets `handoff_signal`, does NOT add a tool result for that call
  - Accepts `system_prompt_override` for passing task-scoped instructions

### Files Modified

#### `backend/src/models/character_plan.py`
- No logic changes; confirm `DeferredTask` is still importable (no breaking changes)

### Verification

```bash
cd backend && source venv/bin/activate
python -c "
from src.models.routing import TurnType, CoordinationState, CoordinationMode, RoutingDecision
from src.core.conversation_state import ConversationStateManager
from src.core.character_executor import CharacterExecutor
print('Milestone 1: all imports OK')
"
```

### Completion Checklist

- [ ] `routing.py` models with full type hints and docstrings
- [ ] `CoordinationStateManager` serialises/deserialises to `context.metadata` cleanly
- [ ] `CoordinationStateManager` reads existing `deferred_tasks` keys (backward compat)
- [ ] `CharacterExecutor` passes existing single-character response tests
- [ ] `is_expired()` correctly handles missing `expires_at` (returns `False`)
- [ ] Unit tests: `ConversationStateManager` transitions + expiry (8+ cases)
- [ ] Unit tests: `CharacterExecutor` with mock LLM (tool loop, handoff signal detection)
- [ ] One commit on `phase5.1` branch

---

## Milestone 2: TurnClassifier & ConversationRouter

**Status:** Not Started
**Goal:** Both routing components implemented and unit-tested. Still not wired into `handle_user_message` — can be exercised via debug API or direct unit tests only.

### Files Created

#### `backend/src/core/turn_classifier.py`
- `TurnClassifier` class
  - `classify(user_message, recent_history, coordination_state) -> TurnClassification`
  - LLM prompt (see ARCHITECTURE.md Component 1)
  - `temperature=0.0`, `max_tokens=80`
  - Fallback: regex `is_affirmation()` when LLM call fails (log WARNING)
  - Only called when `coordination_state.mode != IDLE`

#### `backend/src/core/conversation_router.py`
- `ConversationRouter` class
  - `route(user_message, recent_history, available_characters, coordination_state) -> RoutingDecision`
  - LLM prompt with character roster + domain descriptions (see ARCHITECTURE.md Component 2)
  - `temperature=0.1`, `max_tokens=150`
  - Registered handoff pairs injected into prompt (chapter-aware, from `character_assignments.py`)
  - Fallback: `RoutingDecision(primary_character="delilah")` on any LLM failure, log ERROR

### Files Modified

#### `backend/src/config/character_assignments.py`
- Add `domain_description` field to `CharacterAssignment`
  ```python
  domain_description: str = ""  # Used in router prompt
  ```
- Populate descriptions for `delilah` and `hank`:
  - delilah: `"cooking, recipes, meal planning, food advice, kitchen timers"`
  - hank: `"shopping lists, task management, reminders, scheduling, practical logistics"`
- Add `REGISTERED_HANDOFF_PAIRS` dict:
  ```python
  REGISTERED_HANDOFF_PAIRS = {
      2: [("delilah", "hank"), ("hank", "delilah")],
      # chapter_id: list of (from, to) pairs
  }
  ```

#### `backend/src/api/debug_api.py`
- Add `POST /api/debug/test-router` endpoint:
  ```json
  Request: {"user_id": "test", "message": "...", "history": [...]}
  Response: {"routing_decision": {...}, "turn_classification": {...}}
  ```
- Add `GET /api/debug/coordination-state/{user_id}` endpoint

### Verification

```bash
# Unit test
cd backend && source venv/bin/activate
python -m pytest tests/test_phase51_milestone2.py -v

# Manual: test router via debug endpoint
curl -X POST http://localhost:8000/api/debug/test-router \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test",
    "message": "Southern Fried Chicken sounds great",
    "history": [
      {"role": "user", "content": "Can you plan a meal and make a shopping list?"},
      {"role": "assistant", "content": "Sure sugar! What flavors are you in the mood for?"}
    ]
  }'
# Expected: primary_character=delilah, pending_followup.character=hank (or null if not yet confirmed)
```

### Completion Checklist

- [ ] `TurnClassifier` returns correct `TurnType` for 10+ canned cases
- [ ] `TurnClassifier` falls back to regex on LLM failure without crashing
- [ ] `ConversationRouter` returns valid `RoutingDecision` for 8+ canned scenarios
- [ ] `ConversationRouter` defaults to `delilah` on LLM failure
- [ ] `request_handoff` only appears in router prompt for registered chapter pairs
- [ ] Debug API endpoints functional (test-router, coordination-state)
- [ ] Unit tests: `tests/test_phase51_milestone2.py` (target: 18+ test cases)
- [ ] One commit on `phase5.1` branch

---

## Milestone 3: `request_handoff` Tool & Character Prompt Updates

**Status:** Not Started
**Goal:** Characters can call `request_handoff` as a real tool. The `CharacterExecutor` correctly intercepts it. Character system prompts updated. Observability extended.

### Files Created

#### `backend/src/tools/handoff_tool.py`
- `HandoffTool` class (extends existing `ToolBase`)
- OpenAI function definition:
  - `name: "request_handoff"`
  - Parameters: `to_character` (enum of available secondaries), `task_summary` (string), `items` (array, optional)
- `execute()` method returns a no-op `ToolResult` — the tool is intercepted by the orchestrator before `execute()` is reached; this is a safety fallback only
- Chapter-aware: `available_secondaries` injected at registration time from `REGISTERED_HANDOFF_PAIRS`

### Files Modified

#### `backend/src/core/character_executor.py` (from Milestone 1)
- Full interception logic for `request_handoff` tool calls:
  ```python
  for tool_call in llm_response["tool_calls"]:
      if tool_call["function"]["name"] == "request_handoff":
          handoff_signal = json.loads(tool_call["function"]["arguments"])
          # Do NOT add tool result — skip to response assembly
          break
  ```
- Log `request_handoff` call with `orchestrator_decision.accepted=True`
- Log second `request_handoff` in same turn with `accepted=False, rejected_reason="FR2.4 — one handoff per turn"`

#### `backend/src/observability/` (existing tool call logging)
- Extend tool call log schema to include `orchestrator_decision` and `resulted_in_character` fields when `tool_name == "request_handoff"`

#### `backend/src/characters/delilah.py` (or equivalent system prompt file)
- Add `request_handoff` guidance block to Delilah's system prompt:
  ```
  ## Handoff to Hank
  You have access to a special tool: request_handoff. Use it when:
  - You have completed your cooking/recipe task
  - AND a logistics task (list, schedule, reminder) is now ready to execute
  - AND that task belongs to Hank's domain

  Use it alongside your natural spoken response. Do NOT use it if the full
  task is within your own domain. Do NOT use it speculatively — only call
  it when the information Hank needs actually exists in this conversation.
  ```

#### `backend/src/characters/hank.py` (or equivalent)
- Add symmetric guidance: Hank can `request_handoff` back to Delilah for cooking follow-ups (e.g., "what temperature should I store this at?")

#### `CLAUDE.md` and `Agents.md`
- Update character domain tables and registered handoff pairs to reflect chapter 2 state

### Verification

```bash
# Integration test: Delilah produces a handoff tool call
cd backend && source venv/bin/activate
python -m pytest tests/test_phase51_milestone3.py -v

# Manual: send a message that should trigger Delilah to use request_handoff
curl -X POST http://localhost:8000/api/conversation/message \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_phase51",
    "message": "Set a timer for 30 minutes and add chicken to my list"
  }'
# Verify in observability: tool_calls should include request_handoff with accepted=true
```

### Completion Checklist

- [ ] `HandoffTool` registered and appears in tool definitions for Delilah/Hank
- [ ] `CharacterExecutor` intercepts `request_handoff` and sets `handoff_signal`
- [ ] Second `request_handoff` in same turn: `accepted=False` logged, not executed
- [ ] Observability UI shows `request_handoff` with `orchestrator_decision` fields
- [ ] Delilah and Hank system prompts include handoff guidance
- [ ] `CLAUDE.md` and `Agents.md` updated with current character domains and handoff pairs
- [ ] Unit tests: `tests/test_phase51_milestone3.py`
- [ ] One commit on `phase5.1` branch

---

## Milestone 4: Full Wiring & End-to-End Validation

**Status:** Not Started
**Goal:** `handle_user_message` refactored to use the new pipeline. All five user stories from the PRD pass. Feature flag `enable_phase51` gates the new path; old path remains as fallback.

### Files Modified

#### `backend/src/core/conversation_manager.py`
- Add `enable_phase51: bool = True` constructor parameter
- Add `ConversationRouter`, `TurnClassifier`, `ConversationStateManager`, `CharacterExecutor` as injected dependencies (with auto-construction defaults)
- Refactor `handle_user_message` to follow the new execution path (see ARCHITECTURE.md — Modified Execution Path section)
- Keep `_handle_phase45_multi_character()` and `_execute_deferred_tasks()` intact as dead code initially; remove in a follow-up cleanup commit once Phase 5.1 is stable
- Remove `is_affirmation()` import from the primary path (retain the function itself for fallback)

#### `backend/src/main.py`
- Pass `enable_phase51=True` when constructing `ConversationManager`

#### `backend/tests/test_phase51_milestone4.py` (integration)
All five PRD user stories tested end-to-end:

| Test | Scenario | Assert |
|---|---|---|
| `test_us1_single_message_multitask` | "Set timer and add to list" | Two fragments: delilah + hank |
| `test_us2_two_turn_confirm` | Meal plan → confirm → list | Turn 2: hank adds items |
| `test_us3_direct_followon` | Recipe shown → "add those to my list" | Hank responds, not Delilah |
| `test_us4_topic_change_clears_state` | Pending state → topic change | State cleared, no leaked action |
| `test_us5_handoff_tool` | Delilah calls request_handoff | Hank executes with tool access |

### Additional Verification

```bash
# Run full Phase 5 regression (existing tests must still pass)
cd backend && source venv/bin/activate
python -m pytest tests/test_phase5_deferred_tasks.py tests/test_story_engine.py -v

# Run new Phase 5.1 tests
python -m pytest tests/test_phase51_milestone4.py -v

# Manual: the original failing scenario
curl -X POST http://localhost:8000/api/conversation/message \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_phase51", "message": "Can you help me plan a meal for Sunday then make me a shopping list for the items?"}'
# Turn 1: Delilah asks what they want

curl -X POST http://localhost:8000/api/conversation/message \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_phase51", "message": "Southern Fried Chicken sounds great. No dietary restrictions."}'
# Expected: Delilah provides menu, Hank adds items — two character fragments in response
```

### Completion Checklist

- [ ] `enable_phase51=True` by default; `False` falls back cleanly to Phase 4.5/5 path
- [ ] All 5 PRD user story tests passing
- [ ] Existing Phase 4.5 and Phase 5 tests still passing
- [ ] Observability dashboard shows coordination state transitions correctly
- [ ] `GET /api/debug/coordination-state/{user_id}` returns live state
- [ ] Router decisions and TurnClassifier outputs visible in backend logs
- [ ] `CLAUDE.md` and `Agents.md` confirmed up to date
- [ ] One commit on `phase5.1` branch
- [ ] Git tag: `phase5.1-complete`

---

## Commit Message Template

```
Complete Milestone N: [Name] for Phase 5.1

[1-2 sentence description]

Changes:
- [key change]
- [key change]

Testing:
- [test approach]

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Router LLM adds too much latency | Medium | Medium | Bounded `max_tokens=150`; measure P95 in M4 |
| TurnClassifier misclassifies topic changes | Medium | Low | Fallback clears state on `NEW_REQUEST`; worst case is a missed handoff, not a wrong execution |
| `request_handoff` prompt guidance ignored by LLM | Low | High | M4 integration tests will catch this; adjust prompt wording |
| Backward compat break in `deferred_tasks` keys | Low | Medium | M1 `ConversationStateManager` explicitly reads old keys |
| `CharacterExecutor` extraction breaks existing flows | Medium | High | M1 is pure extraction with existing tests as guard |
