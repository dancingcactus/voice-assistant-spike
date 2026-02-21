# Phase 5.1: Two-Character Coordination - Implementation Plan

**Version:** 1.0
**Last Updated:** 2026-02-21
**Status:** ✅ Completed

---

## Problem Statement

Character interactions lacked coordination. When a user asked for a dinner plan (Chapter 2+),
Delilah would respond with a full meal plan and shopping list on her own, with no handoff or
acknowledgment of Hank's role in task and list management. The characters operated in isolation
rather than as a crew.

**Root Causes:**

1. `ConversationManager` always used a single active character with no mechanism for a second character to weigh in.
2. Character system prompts contained no awareness of other crew members.
3. Character JSON definitions did not declare which tools each character could use (`available_tools`).

---

## Changes Made

### 1. `available_tools` in Character Definitions

**Where tools available to each character are defined:**
Tools are declared in each character's JSON file (`story/characters/<id>.json`) under the
`available_tools` key. This makes it immediately visible which tools a character can call,
and the `CharacterSystem` automatically includes this list in the LLM system prompt.

**Files changed:**
- `story/characters/delilah.json` — added `available_tools`
- `story/characters/hank.json` — added `available_tools` and `tool_instructions`
- `backend/src/models/character.py` — added `available_tools: Optional[List[str]]` field

### 2. Crew Context in System Prompts

`CharacterSystem` now has a `build_crew_context(active_character_id)` method that returns
a brief description of other loaded characters. This context is passed into
`build_system_prompt` as `crew_context` and appears in the LLM prompt under
**"## Your Crew"**, giving Delilah awareness of Hank and vice versa.

**Files changed:**
- `backend/src/core/character_system.py`
  - Added `crew_context` parameter to `build_system_prompt`
  - Added `build_crew_context` method
- `backend/src/core/conversation_manager.py`
  - `_build_system_prompt` now calls `build_crew_context` and passes it through

### 3. `_handle_character_coordination` in `ConversationManager`

**Renamed from what would have been `_handle_phase51`** to the more descriptive
`_handle_character_coordination`.

This method:
- Only activates in Chapter 2+ (Hank must be unlocked in the story).
- Checks whether the user message or Delilah's response contains task/list keywords
  (e.g. "shopping list", "grocery list", "remind me", "checklist").
- If coordination is warranted, makes a second LLM call using Hank's character prompt,
  passing the full exchange as context and asking Hank whether he has anything to add.
- Appends Hank's reply to Delilah's response, producing a natural crew dialogue.

**Keyword triggers for coordination:**

```
"shopping list", "grocery list", "to-do list", "todo list",
"task list", "checklist", "remind me", "don't forget",
"add to list", "make a list", "write down", "note that",
"pick up", "need to buy", "need to get", "grab some", "grab a"
```

**Files changed:**
- `backend/src/core/conversation_manager.py`
  - Added `_COORDINATION_KEYWORDS` class attribute
  - Added `_handle_character_coordination` method
  - Integrated call into `handle_user_message` (after primary LLM response, before beat injection)

### 4. `chapter_id` in Beat Context and Response Metadata

The current story chapter is now:
- Included in `beat_context` as `"chapter_id"` when `should_inject_beat` is called.
- Included in the `handle_user_message` response metadata as `"current_chapter"`.
- Included in response metadata as `"coordination_active"` (bool).

---

## Architecture

```
User message
    │
    ▼
ConversationManager.handle_user_message
    │
    ├─► _build_system_prompt (Delilah + crew context)
    │       └─► CharacterSystem.build_crew_context
    │
    ├─► LLM call (Delilah responds)
    │
    ├─► _handle_character_coordination (chapter 2+ only)
    │       ├─► keyword check on user message + Delilah response
    │       ├─► CharacterSystem.build_system_prompt (Hank + crew context)
    │       └─► LLM call (Hank weighs in)
    │
    ├─► Story beat injection (beat_context includes chapter_id)
    │
    └─► Response {text, metadata: {current_chapter, coordination_active, ...}}
```

---

## Testing

Run the existing backend unit tests:

```bash
cd backend
python -m pytest tests/ -v
```

To manually test coordination, set the user's chapter to 2 and send a message
containing list/task keywords:

```bash
# Using the test API (ENABLE_TEST_API=true)
curl -X POST http://localhost:8000/api/test/state/test_user \
  -H "Content-Type: application/json" \
  -d '{"state_updates": {"story_progress": {"current_chapter": 2}}}'

curl -X POST http://localhost:8000/api/test/conversation \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "message": "Can you help me plan dinner and make a shopping list?"}'
```

Hank's reply should appear after Delilah's response in the output.

---

## Future Work

- Add beat IDs to the `beat_context` for finer-grained learning/analytics.
- Support Rex as a third coordination target in Chapter 3+.
- Allow character coordination to trigger tool calls on behalf of the secondary character.
