# Phase 5.1: Robust Character Coordination & Conversational Routing - PRD

**Version:** 1.0
**Last Updated:** February 20, 2026
**Product Owner:** Justin
**Status:** Draft
**Phase Position:** Sub-phase of Phase 5; replaces/extends the coordination logic introduced in Phase 4.5 and Phase 5

---

## Executive Summary

Phase 5.1 redesigns the character coordination and intent routing systems from first principles.
The current architecture — a pre-classifying intent detector feeding a static rule-based character planner — has proven too brittle for the conversational, multi-turn interactions the system is built around. Phase 5.1 replaces it with a **conversation-aware orchestrator** that understands narrative arc, uses the LLM as a dynamic router, and gives characters an explicit structured mechanism to signal handoffs rather than relying on injected prose hints.

**Success Metric:** The meal-plan → shopping-list scenario (and its variants) consistently routes the shopping-list action to Hank in his own voice, whether the user asks in one message or across three turns.

---

## Problem Statement

### Observed Failure Scenario

```
User:    Can you help me plan a meal for Sunday then make me a shopping list?
Delilah: What kind of flavors are you in the mood for? Something like Southern fried chicken?
User:    Southern Fried Chicken sounds great. No dietary restrictions.
Delilah: Here's your shopping list: [lists all items]    ← Delilah does Hank's job
User:    Can you add those items to my list?
Delilah: Done, honey! I've added all the ingredients...  ← Still Delilah
```

**Expected:**
```
User:    Can you help me plan a meal for Sunday then make me a shopping list?
Delilah: What flavors are you in the mood for?
User:    Southern Fried Chicken sounds great.
Delilah: Perfect, sugar! Here's the menu... Hankie, darlin', would you add those to the list?
Hank:    Aye, Cap'n. List is set — whole chicken, buttermilk, the works.
```

### Root Cause Analysis

The current system has four distinct failure modes that compound each other:

#### Failure 1: Intent Classification Is Disconnected From Conversation History

The `IntentDetector` classifies each message independently using keyword patterns and a context-free LLM call. It has no concept of what happened in previous turns. When the user says "Southern Fried Chicken sounds great", the intent detector sees an isolated phrase and cannot know it is an affirmation of Delilah's meal proposal — let alone that a second‐character shopping-list action is now warranted.

**Impact:** Multi-turn tasks that unfold across several exchanges are invisible to the router.

#### Failure 2: Affirmation Detection Is a Shallow Regex Match

`is_affirmation()` matches a fixed list of short phrases ("sounds good", "yes", "sure"). It misses:
- Content-carrying confirmations: "Southern Fried Chicken sounds great"
- Direct follow-on requests: "Can you add those items to my list?"
- Implicit continuations: "Let's go with that" 

**Impact:** The deferred-task trigger never fires in most real conversations, so Delilah handles everything herself because the Hank handoff never activates.

#### Failure 3: Characters Have No Structured Handoff Mechanism

When Delilah is instructed to "naturally invite Hank to handle the logistics", she produces a sentence like "Hankie, can you add those?" but this is just text. The orchestrator has no way to intercept that phrase and actually run Hank's LLM call with tool access. The prose appears in the transcript but Hank never executes.

**Impact:** Handoffs are cosmetic (a line of dialogue) without being functional (a second LLM call with tools).

#### Failure 4: The Character Planner Ignores Conversational State

The `CharacterPlanner` maps intents to characters at the moment the user's first message arrives. There is no mechanism to re-evaluate the plan as the conversation develops. A plan created at turn 1 cannot adapt to new information revealed at turns 2 and 3.

**Impact:** Multi-turn tasks requiring information that only exists after turn 1 are either deferred mechanically (if `is_dependent` is set) or collapsed incorrectly into a single-character response.

---

## Product Vision

### The Right Mental Model

The characters are a **crew** working together. When a complex request arrives, the orchestrator acts as a silent director: it reads the conversation, decides which character's voice belongs next, and lets that character generate a real response (with tool access). Handoffs should feel like natural conversation transitions — and must trigger real second-character execution, not just spoken words.

### Design Principles

1. **Routing is a conversation-level decision, not a message-level classification.** The router always has full history.
2. **Characters signal handoffs with structured intent, not prose.** A handoff is a tool call or a special structured signal in the response, not a guessed-at phrase.
3. **The orchestrator drives multi-character turns from outside, not via prompt injection.** Delilah should not need a hint telling her to "invite Hank" — the orchestrator should execute Hank independently after Delilah completes her turn.
4. **Confirmation/continuation detection must understand context.** Whether a message is an affirmation depends on what was just said.

---

## Functional Requirements

### FR1: Conversation-Aware LLM Router

**FR1.1** — A new `ConversationRouter` component replaces `IntentDetector` + static character assignment. It receives the full recent conversation history and the new user message, and returns a `RoutingDecision`.

**FR1.2** — `RoutingDecision` specifies:
- `primary_character`: who should respond first
- `pending_followup`: optional description of a second-character action to execute after the primary responds (e.g., "Hank should add the items Delilah described to the shopping list")
- `conversation_mode`: one of `SINGLE_TURN | MULTI_TURN_CONFIRMING | MULTI_TURN_EXECUTING`
- `routing_rationale`: short string logged for observability

**FR1.3** — The router receives 3-5 turns of recent history plus character roster and domain descriptions. It does NOT receive raw tool definitions.

**FR1.4** — Router output is validated against a strict schema (Pydantic). Malformed output falls back to the previous Delilah-default behaviour.

**FR1.5** — The router runs at the start of every `handle_user_message` call (replaces the current intent detect → plan create pipeline).

---

### FR2: Structured Character Handoff Signal

**FR2.1** — Characters gain access to a `request_handoff` tool with schema:
```json
{
  "to_character": "hank",
  "task_summary": "Add the Southern Fried Chicken ingredients to the Sunday Meal shopping list",
  "items": ["whole chicken", "buttermilk", "flour", "..."]
}
```

**FR2.2** — When the orchestrator detects a `request_handoff` tool call in a character's response, it:
1. Completes the primary character's text response (stripping the raw tool-call text)
2. Immediately executes the named second character with full tool access and the handed-off task as context
3. Appends the second character's response as a `DialogueFragment` alongside the first

**FR2.3** — Characters are instructed in their system prompts to use `request_handoff` when they have completed their domain work and a task outside their domain is now ready to execute. They may still produce natural prose alongside the tool call (e.g., "Hankie, I think you've got the list covered").

**FR2.4** — Only one level of handoff per turn (no chaining Hank → Rex → Delilah in a single response cycle).

---

### FR3: Conversation State Tracking

**FR3.1** — `ConversationContext.metadata` gains a `coordination_state` dict tracking:
- `mode`: `idle | proposing | awaiting_action`
- `pending_character`: which character has a pending action
- `pending_task`: short description of what they should do
- `proposed_content`: structured summary of what the primary character offered (items list, plan, etc.)
- `expires_at`: ISO timestamp after which coordination state clears automatically

**FR3.2** — When a character produces a proposal (e.g., a meal plan or recipe), the orchestrator extracts a structured summary from the LLM response and stores it as `proposed_content`. This replaces the current practice of asking Delilah to remember what she said and relay it in a follow-up prompt.

**FR3.3** — State clears after 20 minutes with no user interaction (matching the existing deferred-task expiry).

**FR3.4** — State clears immediately when the user clearly changes topic (detected by the router).

---

### FR4: Context-Aware Continuation Detection

**FR4.1** — Replace the regex `is_affirmation()` with an LLM-powered `IntentClassifier.classify_user_turn()` that returns one of:
- `AFFIRMATION` — user is confirming a prior proposal
- `NEW_REQUEST` — user is asking something new
- `CLARIFICATION` — user is adding detail to the current topic
- `REJECTION` — user is declining the prior proposal

**FR4.2** — Classification uses the last 2 turns of history plus the `coordination_state.proposed_content` for context.

**FR4.3** — When `AFFIRMATION` is returned and `coordination_state.pending_character` is set, the orchestrator triggers the pending character's action directly (bypassing the normal routing step).

**FR4.4** — When `NEW_REQUEST` is returned, any pending coordination state is cleared before routing.

---

### FR5: Backward Compatibility

**FR5.1** — The existing `deferred_tasks` metadata path remains in place as a fallback. If the new router is unavailable (LLM failure), conversation falls back to the current Phase 5 behaviour.

**FR5.2** — Single-character queries (the majority) are unaffected in latency — the router makes one fast LLM call that replaces the current intent-detect + plan-create calls.

**FR5.3** — All existing tests for Phase 4.5 and Phase 5 milestones continue to pass.

---

## User Stories

### US1 — One-Message Multi-Task (Immediate)
> "Set a timer for 20 minutes and add flour to my list."

Both tasks are independent and immediate. The router outputs `primary_character=delilah` (timer) and `pending_followup` for Hank (list). Delilah sets the timer; Hank adds flour. Both respond in the same turn.

### US2 — Two-Turn Dependent Flow (Confirm Then Execute)
> Turn 1: "Plan me a Sunday dinner and create a shopping list."
> Delilah: [proposes Southern Fried Chicken and stores proposed items]
> Turn 2: "That sounds perfect."
> System: Delilah confirms; Hank adds items to the list.

The router detects turn 2 as `AFFIRMATION` with `pending_character=hank`. Hank executes the list action without Delilah needing to re-describe the items; the orchestrator passes `proposed_content` as Hank's task context.

### US3 — Direct Request for Second Character's Work
> Turn 1: Delilah: [describes Southern Fried Chicken recipe]
> Turn 2: "Can you add those items to my list?"

The router classifies this as a direct `household` request (list addition) with context referencing Delilah's prior recipe. It assigns `primary_character=hank`, who adds the items from conversation context.

### US4 — Topic Change Clears State
> Turn 1: Delilah proposes a meal (pending Hank action stored)
> Turn 2: "What's the weather like?"

Router returns `NEW_REQUEST`. Coordination state clears. Rex (or general character) answers the weather question. The pending Hank action is discarded cleanly.

### US5 — Character Handoff Tool Call
> Delilah finishes her recipe response and calls `request_handoff(to="hank", task_summary="Add chicken recipe ingredients to Sunday Meal list", items=[...])`
> Orchestrator: runs Hank with tool access, Hank calls `add_items_to_list`, responds "Aye, got 'em on the list, Cap'n."

---

## Non-Functional Requirements

### NFR1 — Latency
- Single-character turns: ≤ 50ms additional overhead vs. current (one router call replaces one intent-detect call)
- Multi-character turns: second character call runs after primary, total latency increase acceptable given the functional improvement
- Router LLM call uses `temperature=0.1`, `max_tokens=150` to keep it fast

### NFR2 — Reliability
- Router must return a valid `RoutingDecision` or raise a typed exception; no silent failures
- Handoff tool processing must be idempotent (calling twice doesn't add items to the list twice)

### NFR3 — Observability
- All routing decisions logged with rationale for debugging
- Handoff events recorded in the existing `CoordinationTracker`
- Conversation state transitions logged at INFO level

### NFR4 — Testability
- `ConversationRouter` is unit-testable in isolation (mock LLM)
- `IntentClassifier.classify_user_turn()` is unit-testable with canned history
- Integration tests cover each of the five user stories above

---

## Out of Scope for Phase 5.1

- Rex character involvement (Phase 5.1 only targets Delilah ↔ Hank coordination)
- TTS audio queuing for multi-character responses (tracked separately)
- Parallel (simultaneous) character execution — all multi-character turns remain sequential
- Long-term cross-session memory of coordination patterns

---

## Success Criteria

| Scenario | Before Phase 5.1 | After Phase 5.1 |
|---|---|---|
| Multi-message meal-plan → shopping-list | Delilah handles both | Hank adds the list in his voice |
| Direct "add those to my list" | Delilah responds | Hank responds |
| "Set timer + add to list" one-shot | Inconsistent (depends on LLM) | Reliably two-character turn |
| Topic change after proposal | State may leak across turns | Clean state reset |
| Affirmation detection accuracy | ~40% on natural language | >85% on natural language |

---

## Decisions

1. **Router model:** Use the same Claude model as character turns. LLM call overhead is kept minimal via `max_tokens=150` and `temperature=0.1`.
2. **Proposed content extraction:** Start with a free-text summary; evaluate whether structured extraction is needed based on how reliably Hank can act on it in practice.
3. **Handoff tool visibility:** `request_handoff` is only surfaced to characters in registered pairs for the current chapter (e.g., Delilah↔Hank in chapter 2). Characters without a registered secondary do not receive the tool definition.
4. **Router fallback:** If the `ConversationRouter` LLM call fails, default to Delilah and log an ERROR. Do not fall back to rule-based assignment — prefer a predictable no-op over unpredictable routing.

---

**Document Owner:** Development Team
**Next:** [ARCHITECTURE.md](ARCHITECTURE.md)
