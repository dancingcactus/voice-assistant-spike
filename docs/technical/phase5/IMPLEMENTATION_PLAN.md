# Phase 5: Specialist Handoff for Dependent Multi-Turn Tasks - Implementation Plan

**Version:** 1.0
**Last Updated:** February 20, 2026
**Status:** In Progress

---

## References

- **PRD**: [PRD.md](PRD.md)
- **Phase 4.5 Architecture**: [../phase4.5/ARCHITECTURE.md](../phase4.5/ARCHITECTURE.md)
- **Character Assignments**: `backend/src/config/character_assignments.py`
- **Handoff Templates**: `backend/src/config/handoff_templates.json`

---

## Overview

### Goals

Enable multi-turn dependent task execution with correct character specialisation and per-character audio voice preservation. Fix the root cause: the multi-task LLM decomposition runs all subtasks in the same turn even when a later subtask cannot meaningfully execute before an earlier one produces output.

### Timeline Estimate

- **Total Duration:** 1–2 weeks
- **Milestone Count:** 3 milestones

### Success Criteria

- Intent decomposition correctly splits dependent tasks from immediate ones
- Deferred tasks execute with natural handoff after user affirmation
- Per-character `DialogueFragment` objects present in response metadata for TTS
- 20-minute expiry enforced silently

---

## Milestone 1: Model & Detection Changes

**Status:** In Progress
**Goal:** Add `is_dependent` to `SubTask`, update LLM prompt, add `DeferredTask` model, split plan

### Files Changed

#### `backend/src/models/intent.py`
- Add `is_dependent: bool = False` field to `SubTask` dataclass
- Update `IntentResult.to_dict()` to include `is_dependent` per sub-task

#### `backend/src/core/intent_detector.py` — `_parse_multi_task_llm()`
- Update system prompt to document `is_dependent` in the expected JSON format
- Instruction: set `is_dependent: true` when a subtask cannot execute meaningfully until the preceding subtask produces output (e.g., "create shopping list for that dinner" depends on the dinner being chosen first)
- Parse `is_dependent` from LLM response when constructing `SubTask` objects

#### `backend/src/models/character_plan.py`
- Add `DeferredTask` dataclass: `character`, `task_description`, `intent`
- Add `deferred_tasks: List[DeferredTask] = field(default_factory=list)` to `CharacterPlan`
- Update `CharacterPlan.to_dict()` to include `deferred_tasks`

#### `backend/src/core/character_planner.py` — `_create_multi_task_plan()`
- After assigning characters to subtasks, check `sub_task.is_dependent`
- Dependent subtasks → `CharacterPlan.deferred_tasks`; all others → `CharacterPlan.tasks`

### Verification
```bash
cd backend && python -c "
from src.models.intent import SubTask
t = SubTask(text='add to list', intent='household', confidence=0.9, is_dependent=True)
assert t.is_dependent == True
print('SubTask OK')
"
```

---

## Milestone 2: Deferral Storage, Expiry & Affirmation Trigger

**Status:** Not Started
**Goal:** Store deferred tasks with expiry timestamp, detect affirmation, execute on confirmation

### Files Changed

#### `backend/src/core/utils.py` (new file)
- `is_affirmation(text: str) -> bool`: regex match against common confirmatory phrases
- Case-insensitive, punctuation-stripped

#### `backend/src/core/conversation_manager.py`

**Expiry check** — early in `handle_user_message()`, before Phase 4.5 block:
```python
# Evict expired deferred tasks silently
expires_str = context.metadata.get("deferred_tasks_expires_at")
if expires_str:
    if datetime.fromisoformat(expires_str) < datetime.utcnow():
        context.metadata.pop("deferred_tasks", None)
        context.metadata.pop("deferred_tasks_expires_at", None)
        context.metadata.pop("deferred_tasks_trigger_intent", None)
```

**Affirmation trigger** — after expiry check, before Phase 4.5 block:
```python
if context.metadata.get("deferred_tasks") and is_affirmation(user_message):
    return await self._execute_deferred_tasks(session_id, user_id, user_message, context, input_mode)
```

**Deferred task storage** — after `character_planner.create_plan()`, if `plan.deferred_tasks`:
```python
context.metadata["deferred_tasks"] = [
    {"character": dt.character, "task_description": dt.task_description, "intent": dt.intent}
    for dt in character_plan.deferred_tasks
]
context.metadata["deferred_tasks_expires_at"] = (
    datetime.utcnow() + timedelta(minutes=20)
).isoformat()
context.metadata["deferred_tasks_trigger_intent"] = character_plan.tasks[-1].intent
```

**`_execute_deferred_tasks()` method** (new async method):
1. Get deferred tasks from `context.metadata["deferred_tasks"]`
2. Call `dialogue_synthesizer.synthesize_handoff("delilah", "hank")` for the handoff phrase
3. Select Hank's voice mode via `character_system.select_voice_mode("hank", task_description, ...)`
4. Build Hank's system prompt and generate his LLM response (with tool call loop — calls `manage_list`)
5. Manually build `fragments` list: `[{character: "delilah", text: handoff_phrase, voice_mode: "warm_baseline"}, {character: "hank", text: hank_text, voice_mode: hank_voice_mode}]`
6. Combine `full_text = f"{handoff_phrase} {hank_text}"`
7. Append combined text as assistant Message to history + persist
8. Clear `deferred_tasks`, `deferred_tasks_expires_at`, `deferred_tasks_trigger_intent` from metadata
9. Return `{text: full_text, metadata: {..., fragments: [...], deferred_executed: True}}`

### Verification

- Test: deferred task stored with correct expiry after planning turn
- Test: message 20+ minutes later → deferred tasks silently cleared, no execution
- Test: "that looks good" → `is_affirmation()` True; "can you add more garlic?" → False

---

## Milestone 3: System Prompt Context & Voice Fragment Metadata

**Status:** Not Started
**Goal:** Shape Delilah's natural handoff invite; verify TTS fragment metadata contract

### Files Changed

#### `backend/src/core/conversation_manager.py` — `_build_system_prompt()`

When `char_id == "delilah"` and valid (non-expired) deferred tasks are in `context.metadata`, append to the built system prompt:

```
## Pending Follow-up Action
After the user confirms or approves your suggestion, naturally and briefly invite Hank to handle
the follow-up logistics. Keep it short and in character — for example:
"Hankie, darlin', would you be a dear and add those to the list?"
Do not use a list tool yourself for this; Hank will handle the logistics.
```

### Response Metadata Contract (for TTS layer)

The `/chat` API response `metadata` will include when deferred tasks execute:
```json
{
  "deferred_executed": true,
  "fragments": [
    {"character": "delilah", "text": "Hankie, would you be a dear...", "voice_mode": "warm_baseline"},
    {"character": "hank",    "text": "Aye, Miss Lila. Got 'em on the list, Cap'n.", "voice_mode": "working"}
  ]
}
```

The TTS layer uses `character` + `voice_mode` per fragment to select the correct voice model and render audio segments sequentially.

### Verification

- Check response metadata contains `fragments` with two entries and correct characters/voice modes
- Manually verify Delilah's system prompt includes the follow-up note when deferred tasks are pending
- End-to-end: full 3-turn conversation produces correct character/voice attribution throughout

---

## Testing

### Run existing suite
```bash
cd backend && source venv/bin/activate
pytest tests/test_phase4_5_milestone*.py -v
```

### New test file
`tests/test_phase5_deferred_tasks.py` covering:
- Dependent subtask split during planning
- Deferred task storage with correct expiry timestamp
- Affirmation detection (positive and negative cases)
- Silent expiry without side effects
- Full deferred execution flow with correct fragment metadata
- No regression: simple single-intent queries unaffected
