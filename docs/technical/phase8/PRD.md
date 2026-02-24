# Phase 8: Experience Testing Suite - Product Requirements Document

**Version:** 1.0
**Last Updated:** 2026-02-23
**Product Owner:** Justin
**Status:** Draft — Awaiting Review
**Phase Position:** Follows Phase 7 (Structured Logging & Observability); independent of Phase 5.1 (Specialist Handoff)

---

## Executive Summary

Phase 8 introduces an **Experience Testing Suite** — a developer-facing tool for evaluating how the system *feels* across a curated set of scripted conversations. Unlike the existing automated E2E tests, which verify deterministic correctness, this suite captures qualitative evidence of how prompt changes, character profile edits, and coordination logic changes actually land in practice. A developer triggers the full suite from a new **Bulk Testing** section in the Observability UI, watches or reviews the conversations afterward with their side-effects annotated inline, and compares runs from different system snapshots to build intuition.

**Success Metric:** A developer can make a change to a character prompt, trigger the full test suite, and within a few minutes read through every resulting conversation with its effects annotated — including before/after comparison with a prior run — without writing any code or opening the terminal.

---

## Product Vision

### Core Principle

Automated tests verify correctness; experience tests build confidence. The quality of an AI character system is difficult to capture in assertions. The characters need to *feel* right — warm, consistent, funny when appropriate, brief when appropriate. The only way to evaluate that is to read conversations. Phase 8 makes that reading systematic and repeatable, so changes are made with evidence rather than guesswork.

### User Experience Goals

1. **One-click suite execution** — A single button in the Observability UI triggers all test scenarios in sequence without manual involvement.
2. **Human-readable conversation transcripts** — Each test result renders as a natural dialogue with "Effect:" annotations breaking up the flow wherever a tool call fired, so the reader sees cause and consequence in one document.
3. **Persistent run history** — Every suite execution is saved as a named run. Previous runs are retrievable so a developer can diff the feel of two different system configurations.
4. **Test persona control** — The developer specifies which user profile the suite runs under (or creates a disposable test user) so memory, story progress, and preferences don't leak between evaluation cycles.
5. **Flexible scope** — The developer may run the whole suite or select individual scenarios without leaving the UI.

---

## Problem Statement

### Current Limitations

1. **No qualitative evaluation path** — There is no structured way to observe how a batch of representative conversations plays out after a prompt or character change. Evaluation is ad-hoc: type a message, read the response, repeat.
2. **No run comparison** — Each manual test is ephemeral. There is no record of how the system responded before a change, making it impossible to verify improvement or detect regression in character voice.
3. **Tool effects are invisible** — When a character sets a timer or adds shopping list items, that fact is buried in the Tool Calls observability tab. There is no view that shows the conversation and its side-effects together.
4. **Memory contamination** — Running informal tests uses the primary user's profile, which accumulates memories and advances the story. This corrupts the user experience for non-testing interactions.

---

## Functional Requirements

### FR1: Test Scenario Library

**Purpose:** Define the canonical set of scripted conversations that constitute the experience test suite.

#### FR1.1: Scenario Definition Format

Each scenario is a YAML (or JSON) file stored in `backend/data/test_scenarios/`. It defines the conversation script, the characters expected to participate, the chapter context, and a set of effects to watch for.

**Scenario file structure:**

```yaml
id: "delilah_dinner_solo"
name: "Delilah — Dinner planning solo"
description: "Single-character conversation testing Delilah's recipe and planning voice"
chapter: 1
characters_expected: ["delilah"]
user_turns:
  - "Can you help me plan dinners for this week?"
  - "I want something fancy for the weekend."
  - "That sounds great."
watch_for_effects:
  - type: "tool_call"
    tool: "set_timer"
    label: "Timer set"
  - type: "character_handoff"
    to: "hank"
    label: "Handoff to Hank"
  - type: "story_beat"
    label: "Story beat advanced"
tags: ["single-character", "delilah", "cooking", "planning"]
```

#### FR1.2: Initial Scenario Set

The initial suite ships with the following scenarios:

| ID | Name | Characters | Description |
|----|------|-----------|-------------|
| `delilah_solo_dinner_plan` | Delilah — Dinner planning | delilah | User asks for a weekly dinner plan. Tests recipe voice and warmth. |
| `delilah_solo_allergy` | Delilah — Allergy restriction | delilah | User mentions a food allergy mid-conversation. Tests MAMA BEAR mode. |
| `delilah_solo_wrong_food` | Delilah — Food done wrong | delilah | User describes a cooking method Delilah disagrees with. Tests PROTECTIVE mode. |
| `hank_solo_shopping` | Hank — Shopping list | hank | User asks Hank to build a shopping list from scratch. Tests efficiency and sailor voice. |
| `hank_solo_reminder` | Hank — Reminder scheduling | hank | User asks Hank to set a reminder. Tests task management brevity. |
| `hank_solo_philosophy` | Hank — Deflects philosophy | hank | User asks Hank a reflective question about consciousness. Tests deflection and care through action. |
| `coord_dinner_to_list` | Coordination — Dinner plan → shopping | delilah + hank | Delilah builds a dinner plan; Hank builds the shopping list. Tests the delilah→hank handoff. |
| `coord_list_to_recipe` | Coordination — List query → recipe | hank + delilah | Hank is building a list and a recipe question arises; Hank hands off to Delilah. Tests hank→delilah handoff. |
| `coord_multiturn_plan` | Coordination — Multi-turn meal week | delilah + hank | Extended planning session spanning 5+ turns. Tests memory continuity and handoff quality in longer context. |

Additional scenarios can be added without code changes by placing new YAML files in the `test_scenarios/` directory.

#### FR1.3: Scenario Tagging

Scenarios support free-form tags for filtering. Pre-defined tags include: `single-character`, `multi-character`, `delilah`, `hank`, `cooking`, `shopping`, `task`, `coordination`, `handoff`, `philosophy`, `long`. Tags are displayed in the UI and used for scope selection.

---

### FR2: Scenario Runner (Backend)

**Purpose:** Execute test scenarios against the live conversation system and capture rich, structured results.

#### FR2.1: Runner Endpoint

A new POST endpoint `POST /api/test-runs` accepts:

```json
{
  "scenario_ids": ["delilah_solo_dinner_plan", "coord_dinner_to_list"],
  "user_id": "test_user_experience_01",
  "run_label": "After Delilah prompt v3",
  "run_all": false
}
```

- `scenario_ids` — list of specific scenario IDs to run (empty if `run_all: true`)
- `run_all` — if true, run every scenario in the library in order
- `user_id` — the user profile to use for the session; must exist or be a test user
- `run_label` — a human-readable label for this run (e.g., "After Delilah prompt v3", "Baseline before Phase 8")

The endpoint responds with a `run_id` immediately and executes scenarios sequentially in the background.

#### FR2.2: Turn Execution

Each user turn in a scenario is sent to the existing `POST /api/chat` endpoint under the specified user context. The runner waits for the full response before sending the next turn. Streaming responses are consumed but stored as complete text.

#### FR2.3: Effect Capture

After each turn, the runner queries the tool call log for that `turn_id` and records any tool calls that fired. Recognized effect types:

| Effect Type | Source | Display Label |
|-------------|--------|---------------|
| `tool_call` | Tool call log | Tool name + summary (e.g., "14 items added to list") |
| `character_handoff` | Handoff signal | "Handoff: delilah → hank" |
| `story_beat` | Story engine | "Story beat advanced: [beat name]" |
| `memory_saved` | Memory tool call | "Memory saved: [content snippet]" |
| `timer_set` | Timer tool | "Timer set: [duration]" |

The runner captures *all* tool calls, not just those in `watch_for_effects`. The `watch_for_effects` list is used only to flag expected effects that did *not* fire (shown as "Expected but not seen" in the UI).

#### FR2.4: Run Result Storage

Results are stored as JSON files in `backend/data/test_runs/`. Each file is named `{run_id}.json` and contains:

```json
{
  "run_id": "run_20260223_143022",
  "run_label": "After Delilah prompt v3",
  "started_at": "2026-02-23T14:30:22Z",
  "completed_at": "2026-02-23T14:33:41Z",
  "user_id": "test_user_experience_01",
  "scenario_results": [
    {
      "scenario_id": "delilah_solo_dinner_plan",
      "scenario_name": "Delilah — Dinner planning solo",
      "status": "complete",
      "duration_seconds": 12.4,
      "turns": [
        {
          "turn_index": 0,
          "user_message": "Can you help me plan dinners for this week?",
          "character": "delilah",
          "response": "Why, sugar, of course I can! ...",
          "effects": []
        },
        {
          "turn_index": 1,
          "user_message": "I want something fancy for the weekend.",
          "character": "delilah",
          "response": "Well, now you are speakin' my language ...",
          "effects": [
            {
              "type": "story_beat",
              "label": "Story beat advanced: plan_acknowledged"
            }
          ]
        }
      ],
      "expected_effects_missed": []
    }
  ]
}
```

#### FR2.5: Run Status Polling

`GET /api/test-runs/{run_id}` returns the current status (`pending`, `running`, `complete`, `failed`) and progress (e.g., 3 of 9 scenarios complete). The frontend polls this endpoint while a run is in progress to show a live progress indicator.

#### FR2.6: Run List Endpoint

`GET /api/test-runs` returns a paginated list of all stored runs, sorted newest-first, with `run_id`, `run_label`, `started_at`, `status`, and scenario count.

---

### FR3: Bulk Testing UI Section

**Purpose:** A new top-level section in the Observability dashboard for managing and reviewing test runs.

#### FR3.1: Navigation Entry

A new tab/section labelled **"Bulk Testing"** appears in the Observability UI navigation alongside existing tabs (Logs, Memories, Tool Calls, etc.). It is always visible regardless of chapter or character state.

#### FR3.2: Test Suite Panel

The main Bulk Testing view has two columns:

**Left column — Suite Controls:**
- List of all available scenarios with their name, tags, and expected characters
- Checkboxes to select individual scenarios, or a "Select All" toggle
- User selector: dropdown of existing users + "Create test user" option
- "Run Label" text input (pre-populated with current date and time)
- **"Run Selected"** primary button (disabled when no scenarios selected)
- **"Run All"** secondary button

**Right column — Run History:**
- List of past runs sorted newest-first
- Each run shows: label, date/time, user, scenario count, status badge (Complete / Failed / Running)
- Click a run to open the Run Detail view

#### FR3.3: Run Progress View

While a run is executing, the right column switches to a live progress view:
- Run label and user shown at top
- Progress bar (N of M scenarios complete)
- Live list of scenario statuses: queued / running (spinner) / complete (checkmark) / failed (X)
- Scenarios complete show their turn count

The view auto-updates via polling every 2 seconds. On run completion the view transitions to the Run Detail view automatically.

#### FR3.4: Run Detail View — Conversation Transcript

The heart of the feature. Each completed run can be opened into a full-screen (or full-panel) detail view. The view renders all scenarios in the run as a sequence of conversation transcripts.

**Transcript rendering format:**

```
──────────────────────────────────────────────
Delilah — Dinner planning solo
Tags: single-character  delilah  cooking  planning
Duration: 12.4s
──────────────────────────────────────────────

  User: Can you help me plan dinners for this week?

  Delilah: Why, sugar, of course I can! Let me think on what would
           suit you best this week...

  User: I want something fancy for the weekend.

  Delilah: Well now you are speakin' my language. I was thinkin'
           a braised short rib with a red wine reduction — it looks
           like you spent all day on it, but between you and me,
           it practically cooks itself.

  ► Effect: Story beat advanced — plan_acknowledged

  User: That sounds great.

  Delilah: Wonderful. Now let me see if Hankie can put that list
           together for us. Hankie, oh Hankie, would you be a dear...

  Hank: Aye. Got 'em on the list.

  ► Effect: 14 items added to shopping list
  ► Effect: Handoff — delilah → hank
```

Visual design notes:
- User messages are left-indented, styled differently from character messages
- Character name is bolded/coloured matching their character theme
- `► Effect:` lines use a distinct muted-accent colour and a right-pointing indicator to visually break up the flow without overwhelming the dialogue
- Expected effects that did **not** fire are shown as: `✗ Expected but not seen: [label]` in a warning colour
- Scenarios are separated by a visible divider with the scenario name and metadata

#### FR3.5: Run Comparison View

From the Run Detail view, a **"Compare with..."** button opens a run picker. The developer selects a second run and the view enters a side-by-side mode:

- Left panel: the original run
- Right panel: the comparison run
- Panels are scroll-linked — scrolling one scrolls the other
- No automated diff highlighting — character responses can differ enough that character-level diffing creates more noise than signal; the developer reads both sides and judges qualitatively
- Effects are rendered identically on each side so differences are apparent by reading, not by automated marking

Comparison is per-turn and per-scenario (matched by `scenario_id` and `turn_index`). Scenarios that appear in one run but not the other are shown as blank on the missing side.

---

### FR4: Test User Management

**Purpose:** Allow the developer to isolate test runs from the primary user profile.

#### FR4.1: Create Test User from Bulk Testing UI

The user selector in the Suite Controls panel includes a **"+ New test user"** option. Clicking it opens an inline form:
- Name field (pre-filled: "Test User [date]")
- Checkbox: "Start with clean slate" (default: checked) — sets chapter to 1, clears memories
- Checkbox: "Copy from existing user" — shows a user picker to copy memories/story state from another user

On creation, the new user is added to the selector and selected automatically.

#### FR4.2: Test User Indicator

Test users created via Bulk Testing carry a `source: "bulk_testing"` flag. They appear in the existing User Testing Tool with a "BULK TEST" badge distinct from the existing "TEST" badge. They can be deleted from the User Testing Tool like any other test user.

#### FR4.3: Run-to-User Association

Each run stores the `user_id` it ran under. The Run Detail view displays the user name alongside the run label. If the user has been deleted since the run was saved, the run still displays the stored `user_id` string with a "user deleted" note.

---

## Non-Functional Requirements

### NFR1: Performance

- Individual scenario execution should not significantly exceed real-world conversation speed; the bottleneck is the LLM, not the runner framework.
- The full suite of 9 initial scenarios should complete in under 3 minutes on typical hardware.
- The UI should remain responsive during a running test (non-blocking background execution).

### NFR2: Isolation

- Test runs must not affect the primary user's memory, story progress, or conversation history.
- Each run starts a fresh conversation context for the specified user — prior test run conversations are not carried forward into a new run.

### NFR3: Persistence & Portability

- Run result files are plain JSON and human-readable without the UI.
- Run files survive server restarts and are not stored in memory.
- Scenario YAML files are version-controlled alongside the codebase, so they evolve with the system.

### NFR4: Extensibility

- Adding a new scenario requires only a YAML file drop — no backend code changes.
- New effect types can be registered by extending the runner's effect capture registry.
- The comparison feature must not hard-code scenario structure; it must work with any scenario set present in both runs.

### NFR5: Run Storage Cap

- A maximum of **50 runs** are retained on disk. When a new run is saved and the count exceeds 50, the oldest run by `started_at` timestamp is deleted automatically. The 50-run limit applies per installation and is not configurable in Phase 8.

---

## Out of Scope

The following are explicitly not part of Phase 8:

- **Automated scoring or pass/fail verdicts** — the suite is explicitly qualitative; a human reads the transcripts. Automated scoring is a potential future phase.
- **Audio playback in the UI** — transcripts are text only; TTS-generated audio is not stored or replayed.
- **Regression alert automation** — there is no CI hook that fails a build when transcripts differ. This is a deliberate read-and-judge workflow.
- **Rex or Dimitria scenarios** — Rex (Chapter 3+) and Dimitria (Chapter 4+) are out of scope for the initial suite. Their scenarios can be added via YAML after Phase 8 ships.
- **Parallel scenario execution** — scenarios run sequentially to avoid LLM rate-limit pressure, keep run logs clean, and allow story beat progression to carry forward across scenarios within a run.
- **Real-time streaming display** — character responses are shown in full after turn completion, not streamed word-by-word in the transcript.
- **Conditional/branching scenario scripts** — scenarios are linear turn sequences only; branching logic ("if character says X, respond Y") is deferred to a future phase.
- **Git-committed run artefacts** — run result JSON files live on disk only and are not version-controlled.

---

## User Stories

| # | As a... | I want to... | So that... |
|---|---------|-------------|-----------|
| U1 | Developer | Run the full test suite with one button | I can evaluate a prompt change comprehensively without manual effort |
| U2 | Developer | Read conversation transcripts with effects annotated inline | I can quickly see whether tool calls and handoffs fired in the right places |
| U3 | Developer | Compare two runs side-by-side | I can confidently say whether a change improved or degraded the experience |
| U4 | Developer | Assign runs to a dedicated test user | My primary user's memories and story progress are never contaminated by evaluation |
| U5 | Developer | Select a subset of scenarios to run | I can do a quick spot-check on just the coordination scenarios after a handoff change |
| U6 | Developer | Browse past runs without re-running them | I can return to a baseline run weeks later as a reference |
| U7 | Developer | Add a new scenario without touching back-end code | I can capture a new conversation pattern the moment I think of it |

---

## Decisions Log

The following questions were resolved before architecture began.

| # | Question | Decision |
|---|----------|----------|
| Q1 | Should scenarios support conditional branches? | **No.** Keep scenarios as simple linear turn sequences. Branching deferred to a future phase. |
| Q2 | Should the comparison view highlight textual differences between runs? | **No.** Character responses differ too much for automated diffing to be useful. The comparison view is plain side-by-side; the developer reads and judges qualitatively. |
| Q3 | Should run result files be committed to git as team artefacts? | **No.** Out of scope. Run files live on disk only. |
| Q4 | Should the runner share one conversation session across all turns in a scenario? | **Yes — one `conversation_id` per scenario.** Turns within a scenario are sent as part of the same session so multi-turn memory and story beat progression work correctly. Scenarios run sequentially within a run so story beats carry forward across scenarios. |
| Q5 | How many runs to retain before auto-pruning? | **50 runs.** Oldest run by `started_at` is deleted when the limit is exceeded. |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Time from "Run All" click to readable transcripts | < 3 minutes for full 9-scenario suite |
| Effort to add a new scenario | < 5 minutes (YAML only, no code) |
| Effort to compare two runs | < 30 seconds to open comparison view |
| Test user contamination incidents | 0 (primary user unaffected by any test run) |

---

## Milestones Preview

*(Detailed breakdown to follow in IMPLEMENTATION_PLAN.md after Architecture is approved)*

| Milestone | Name | Key Deliverable |
|-----------|------|----------------|
| M1 | Scenario Library & Data Model | YAML loader, initial 9 scenarios, data storage schema |
| M2 | Scenario Runner Backend | Runner engine, `/api/test-runs` endpoints, effect capture |
| M3 | Bulk Testing UI — Suite Controls | New ObsUI section, scenario picker, user selector, run trigger |
| M4 | Bulk Testing UI — Transcript View | Conversation transcript renderer with inline effects |
| M5 | Bulk Testing UI — Run History & Comparison | Run list, run detail, side-by-side comparison view |
| M6 | Test User Integration | Create-test-user flow in Bulk Testing UI, BULK TEST badge |
