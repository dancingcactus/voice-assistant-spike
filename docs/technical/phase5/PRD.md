# Phase 5: Specialist Handoff for Dependent Multi-Turn Tasks - PRD

**Version:** 1.0
**Last Updated:** February 20, 2026
**Product Owner:** Justin
**Status:** In Progress
**Phase Position:** Follows Phase 4.5 (Multi-Character Coordination)

---

## Executive Summary

Phase 5 introduces **dependent task deferral** — the ability for multi-step requests to span conversation turns, with each character handling only the work they can actually do given current context. When a user asks to "plan dinner then create a shopping list," Delilah handles the meal planning first, and only after the user confirms the menu does she hand off to Hank to build the list — in his voice, with her natural Southern invite.

**Success Metric:** Multi-turn dependent tasks complete with natural character handoffs, each character responding in their own TTS voice, and deferred tasks auto-expiring after 20 minutes to prevent buildup.

---

## Product Vision

### Core Principle

Characters should only act on information they have. A shopping list can't be built until a meal is chosen. Rather than running all subtasks immediately (causing Hank to ask "what's on the menu?" before any menu exists), the system recognises dependency and waits for the right moment.

### User Experience Goals

1. **Natural Turn Pacing:** Dependent tasks wait for prerequisite context before executing
2. **Correct Character Ownership:** Cooking → Delilah; Lists/logistics → Hank
3. **Character Voice Preservation:** Each character's audio segment plays in their own TTS voice
4. **Graceful Expiry:** Unconfirmed deferred tasks evaporate after 20 minutes without noise

---

## Problem Statement

### Observed Failure (Before Phase 5)

```
User:    Can you help me plan dinner tonight then create a shopping list?
Hank:    Aye. What's on the menu fer tonight, Cap'n?   ← wrong: menu doesn't exist yet
User:    I was hoping you could suggest a simple dinner
Delilah: [suggests meal + shopping list]
User:    That looks good
Delilah: I've added salmon, leeks... plus catfish and cod you mentioned earlier.  ← hallucinated items
```

### Expected Behaviour (After Phase 5)

```
User:    Can you help me plan dinner tonight then create a shopping list?
Delilah: Sure sugar, did you have something in mind or do you want some ideas?
User:    I would love some ideas
Delilah: [suggests meal] — Hankie, would you be a dear and add those to the list?
Hank:    Aye, Miss Lila. Got 'em on the list, Cap'n.
```

---

## Functional Requirements

### FR1: Dependent Subtask Detection

**FR1.1** — `SubTask` model gains `is_dependent: bool = False` field
**FR1.2** — LLM multi-task decomposition prompt instructs classification of dependency
**FR1.3** — `CharacterPlanner` separates immediate tasks from deferred ones at plan time

### FR2: Deferred Task Storage

**FR2.1** — Deferred tasks stored in `ConversationContext.metadata` with:
- `deferred_tasks`: list of serialised `DeferredTask` dicts
- `deferred_tasks_expires_at`: ISO timestamp (now + 20 minutes)
- `deferred_tasks_trigger_intent`: the intent whose confirmation unlocks execution

**FR2.2** — Expired deferred tasks are silently cleared on the next message (no character acknowledgement)

### FR3: Affirmation Detection

**FR3.1** — Regex-based `is_affirmation()` helper matches short confirmatory phrases
**FR3.2** — Triggers deferred execution only when: tasks exist + not expired + message is affirmation

### FR4: Deferred Task Execution

**FR4.1** — Delilah's handoff phrase generated via `DialogueSynthesizer.synthesize_handoff()`
**FR4.2** — Hank's response generated via LLM (calls `manage_list` tool)
**FR4.3** — Fragments built manually from handoff phrase + Hank's response, each tagged with `character` and `voice_mode`
**FR4.4** — Response metadata includes `fragments` list for TTS layer to render per-character audio

### FR5: System Prompt Context

**FR5.1** — When deferred tasks are pending and not expired, Delilah's system prompt includes a note to naturally invite Hank after user confirmation

---

## Out of Scope

- Three+ character deferred chains (Rex, Dimitria)
- Parallel deferred tasks
- User-visible notification of pending deferred tasks
- Deferred tasks that survive session restart

---

## Acceptance Criteria

- [ ] "Plan dinner then create a shopping list" → only Delilah responds first turn; deferred task stored
- [ ] User affirms meal → Delilah hands off, Hank confirms and calls `manage_list`
- [ ] Response metadata contains `fragments` with correct `character` + `voice_mode` per segment
- [ ] Deferred tasks cleared after execution
- [ ] Deferred tasks silently cleared if 20+ minutes old without confirmation
- [ ] No regression on existing single-turn routing tests
