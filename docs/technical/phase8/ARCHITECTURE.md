# Phase 8: Experience Testing Suite — Architecture

**Version:** 1.0
**Last Updated:** February 24, 2026
**Status:** Draft
**Companion PRD:** [PRD.md](./PRD.md)

---

## Overview

This document describes the technical design for Phase 8. The implementation spans four areas:

1. **Scenario library** — YAML files defining scripted conversations, stored in `backend/data/test_scenarios/`; a loader that parses and validates them at startup and on-demand
2. **Scenario runner (backend)** — An async background engine that executes scenarios against the live chat system, captures effects and logs per-turn, persists results as JSON, and exposes REST endpoints for lifecycle management (start, poll, cancel, list, retrieve)
3. **Bulk Testing UI section** — A new tab in the Observability dashboard with a scenario picker, user selector, run trigger, live progress view, conversation transcript renderer, run history list, and side-by-side comparison view
4. **Test user integration** — Create-test-user flow inside Bulk Testing UI; `source: "bulk_testing"` flag on created users surfaced as a "BULK TEST" badge in the existing User Testing Tool

---

## System Context

```
Browser (React)
  │  Bulk Testing tab
  │    ├── Scenario list → GET /api/test-runs/scenarios
  │    ├── Run trigger  → POST /api/test-runs
  │    ├── Status poll  → GET  /api/test-runs/{run_id}  (every 2s)
  │    ├── Run list     → GET  /api/test-runs
  │    ├── Run detail   → GET  /api/test-runs/{run_id}  (full result)
  │    └── Cancel       → POST /api/test-runs/{run_id}/cancel
  │
  ▼
FastAPI (main.py)
  │
  ├── api/test_runs_api.py          ← NEW: Bulk Testing REST router
  │     prefix: /api/test-runs
  │     routes: POST /, GET /, GET /{id}, POST /{id}/cancel,
  │             GET /scenarios, POST /users (test-user creation)
  │
  └── core/scenario_runner.py       ← NEW: async background executor
        │  reads YAML via ScenarioLoader
        │  calls POST /api/chat (internal) per turn
        │  reads tool call log → effects
        │  reads GET /observability/logs?turn_id= → log capture
        │  writes run_{id}.json → backend/data/test_runs/
        │  enforces 50-run cap (prunes oldest)
        │
        └── core/scenario_loader.py ← NEW: YAML parse + validate

backend/data/
  ├── test_scenarios/               ← NEW: YAML scenario files (version-controlled)
  │     ├── ch1_beat_discovery.yaml
  │     ├── delilah_solo_dinner_plan.yaml
  │     └── ...
  └── test_runs/                    ← NEW: JSON result files (not version-controlled)
        └── run_20260224_143022.json
```

---

## Backend Architecture

### New & Modified Files

```
backend/src/
├── api/
│   └── test_runs_api.py            ← NEW: /api/test-runs router
├── core/
│   ├── scenario_loader.py          ← NEW: YAML loader + validator
│   └── scenario_runner.py          ← NEW: async runner engine
├── models/
│   └── test_run_models.py          ← NEW: Pydantic models for scenarios & runs
└── main.py                          ← MODIFIED: register test_runs router

backend/data/
├── test_scenarios/                  ← NEW: YAML scenario library
└── test_runs/                       ← NEW: persisted run results
```

---

### `models/test_run_models.py` (New)

Pydantic models shared between the loader, runner, and API layer.

```python
# --- Scenario models (loaded from YAML) ---

class SetupStep(BaseModel):
    type: Literal["set_chapter", "trigger_beat"]
    chapter: Optional[int] = None       # for set_chapter
    beat_id: Optional[str] = None       # for trigger_beat
    variant: Optional[str] = "standard" # for trigger_beat

class WatchForEffect(BaseModel):
    type: Literal["tool_call", "character_handoff", "story_beat", "memory_saved", "timer_set"]
    tool: Optional[str] = None          # for tool_call
    to: Optional[str] = None            # for character_handoff
    label: str

class Scenario(BaseModel):
    id: str
    name: str
    description: str
    required_chapter: int = 1
    characters_expected: List[str]
    setup_steps: List[SetupStep] = []
    user_turns: List[str]
    watch_for_effects: List[WatchForEffect] = []
    tags: List[str] = []

# --- Run request ---

class TestRunRequest(BaseModel):
    scenario_ids: List[str] = []
    run_all: bool = False
    user_id: str
    run_label: str

# --- Run result models (persisted to JSON) ---

class CapturedEffect(BaseModel):
    type: str
    label: str
    raw: Optional[dict] = None          # full tool call record for future use

class TurnResult(BaseModel):
    turn_index: int
    user_message: str
    character: Optional[str]
    response: str
    turn_id: str
    effects: List[CapturedEffect] = []
    logs: List[dict] = []               # verbatim log records from ObservabilityLogHandler

class ScenarioResult(BaseModel):
    scenario_id: str
    scenario_name: str
    status: Literal["complete", "failed", "skipped"]
    duration_seconds: Optional[float]
    error: Optional[str] = None
    turns: List[TurnResult] = []
    expected_effects_missed: List[WatchForEffect] = []

class TestRunResult(BaseModel):
    run_id: str
    run_label: str
    started_at: str                     # ISO 8601 UTC
    completed_at: Optional[str]
    status: Literal["pending", "running", "complete", "failed", "cancelled"]
    user_id: str
    scenario_results: List[ScenarioResult] = []

# --- Run summary (for list endpoint) ---

class TestRunSummary(BaseModel):
    run_id: str
    run_label: str
    started_at: str
    status: str
    scenario_count: int
    completed_count: int
    user_id: str
```

---

### `core/scenario_loader.py` (New)

Responsible for finding, parsing, and validating YAML scenario files. Stateless; called by the runner before each run and by the scenarios list endpoint.

**Responsibilities:**
- Scan `backend/data/test_scenarios/` for `*.yaml` / `*.yml` files
- Parse each file with `PyYAML` and validate against `Scenario` Pydantic model
- Raise `ValueError` with file path and validation detail on bad schema
- Return scenarios sorted by filename (alphabetical within a group prefix)
- Expose `load_all() → list[Scenario]` and `load_by_ids(ids) → list[Scenario]`
- Group ordering (A → B → C) is enforced by filename prefix convention (`a_`, `b_`, `c_`), not by loader logic — the loader returns alphabetical order and the runner respects it

```python
SCENARIOS_DIR = Path(__file__).parent.parent.parent / "data" / "test_scenarios"

def load_all() -> list[Scenario]:
    scenarios = []
    for path in sorted(SCENARIOS_DIR.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text())
        scenarios.append(Scenario.model_validate(raw))
    return scenarios

def load_by_ids(ids: list[str]) -> list[Scenario]:
    all_scenarios = {s.id: s for s in load_all()}
    missing = [i for i in ids if i not in all_scenarios]
    if missing:
        raise ValueError(f"Unknown scenario IDs: {missing}")
    # Preserve ordering from load_all (alphabetical) rather than from `ids`
    return [all_scenarios[i] for i in all_scenarios if i in ids]
```

---

### `core/scenario_runner.py` (New)

The heart of Phase 8. A singleton that manages one active run at a time. All execution happens in an `asyncio` background task so the `POST /api/test-runs` endpoint returns immediately.

**State managed by the runner:**

```python
@dataclass
class RunnerState:
    run: TestRunResult           # mutated in-place during execution
    cancel_requested: bool       # set by cancel endpoint
    current_scenario_index: int  # for progress reporting
```

**Execution flow (`run_scenarios` coroutine):**

```
for each scenario in ordered list:
    if cancel_requested → mark remaining as "skipped", stop
    apply setup_steps (set_chapter, trigger_beat)
    start fresh conversation_id for this scenario
    for each user_turn:
        POST /api/chat  { user_id, message, conversation_id }
        extract turn_id from response.metadata.turn_id
        query tool call log for turn_id → CapturedEffect list
        query GET /observability/logs?turn_id= → raw log records
        append TurnResult to scenario result
    diff watch_for_effects vs captured effects → expected_effects_missed
    append ScenarioResult to run
    persist run to disk (incremental — write after each scenario completes)
```

**`setup_steps` execution:**

| Step type | Calls |
|-----------|-------|
| `set_chapter` | `POST /test/state/{user_id}` with `{"story_progress": {"current_chapter": N}}` — reuses `test_api` route (internal HTTP call via `httpx` or direct function call) |
| `trigger_beat` | `POST /observability/beats/{chapter}/{beat_id}/trigger` with `{"variant": "..."}` — same endpoint as Observability UI button |

To avoid HTTP round-trips on the same server, setup steps call the underlying access functions directly (e.g., `user_testing_access.update_user_state(...)` and `story_access.trigger_beat(...)`) rather than making HTTP requests to itself.

**`POST /api/chat` invocation strategy:**

The runner calls `ConversationManager.process_message()` directly (not via HTTP) to avoid port availability issues and serialisation overhead. A thin helper constructs the same call that `websocket.py` makes:

```python
async def _send_turn(user_message: str, user_id: str, conversation_id: str) -> dict:
    set_correlation_ids(conversation_id=conversation_id, turn_id="")  # turn_id set inside process_message
    response = await conversation_manager.process_message(
        user_message=user_message,
        session_id=conversation_id,
        user_id=user_id,
    )
    return response
```

This keeps the runner purely in-process. The `ConversationManager` instance is the same live singleton used by the WebSocket handler — imported at startup.

**Effect capture (`_capture_effects`):**

```python
async def _capture_effects(turn_id: str) -> list[CapturedEffect]:
    tool_calls = tool_call_access.get_tool_calls_for_turn(turn_id)
    effects = []
    for tc in tool_calls:
        effects.append(_tool_call_to_effect(tc))       # maps tool name → effect type + label
    # Handoff signals are a special tool call; detected by tool name "request_handoff"
    # Story beat advances are detected by tool name "advance_story_beat"
    # Memory saves detected by "save_memory"
    # Timer sets detected by "set_timer"
    return effects
```

The mapping from tool name to `CapturedEffect.type` is defined in a small table in the runner; no config file required for Phase 8.

**Concurrency guard:**

Only one run can be active at a time. The runner maintains a module-level `_active_run_id: str | None`. `POST /api/test-runs` returns HTTP 409 with `{"detail": "A run is already active: {run_id}"}` if `_active_run_id` is set. The guard is cleared when the background task completes (normally or via cancel).

**Run storage and 50-run cap:**

```python
RUNS_DIR = Path(__file__).parent.parent.parent / "data" / "test_runs"

def _persist_run(run: TestRunResult) -> None:
    path = RUNS_DIR / f"{run.run_id}.json"
    path.write_text(run.model_dump_json(indent=2))
    _enforce_run_cap()

def _enforce_run_cap(max_runs: int = 50) -> None:
    files = sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    while len(files) > max_runs:
        files.pop(0).unlink()
```

**Run ID format:** `run_{YYYYMMDD}_{HHMMSS}` (timestamp-based, collision-safe for single-server use).

---

### `api/test_runs_api.py` (New)

FastAPI router registered at prefix `/api/test-runs`.

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/` | Start a new test run (returns `run_id` immediately) |
| `GET` | `/` | List all runs (paginated, newest-first) |
| `GET` | `/scenarios` | List all available scenarios from the library |
| `GET` | `/{run_id}` | Get run status + full result |
| `POST` | `/{run_id}/cancel` | Request cancellation of active run |
| `POST` | `/users` | Create a test user (source: "bulk_testing") |

**`POST /api/test-runs` request/response:**

```json
// Request
{
  "scenario_ids": ["delilah_solo_dinner_plan"],
  "run_all": false,
  "user_id": "test_user_bulk_01",
  "run_label": "After Delilah prompt v3"
}

// Response (202 Accepted)
{
  "run_id": "run_20260224_143022",
  "status": "pending"
}
```

**`GET /api/test-runs` response:**

```json
{
  "runs": [
    {
      "run_id": "run_20260224_143022",
      "run_label": "After Delilah prompt v3",
      "started_at": "2026-02-24T14:30:22Z",
      "status": "complete",
      "scenario_count": 9,
      "completed_count": 9,
      "user_id": "test_user_bulk_01"
    }
  ],
  "total": 1
}
```

**`GET /api/test-runs/{run_id}` response:**

Returns the full `TestRunResult` JSON. During an active run, `scenario_results` contains completed scenarios; in-progress and queued scenarios are absent (the frontend infers them from `scenario_count`).

**`GET /api/test-runs/scenarios` response:**

```json
{
  "scenarios": [
    {
      "id": "ch1_beat_discovery",
      "name": "Chapter 1 — Beat walk: discovery",
      "description": "...",
      "required_chapter": 1,
      "characters_expected": ["delilah"],
      "tags": ["beat-walk", "delilah", "single-character"],
      "turn_count": 5
    }
  ]
}
```

**`POST /api/test-runs/{run_id}/cancel`:**

- Returns `202 Accepted` if run is `pending` or `running`
- Returns `409 Conflict` if run is already `complete`, `failed`, or `cancelled`

**`POST /api/test-runs/users` (create test user):**

```json
// Request
{
  "name": "Test User 2026-02-24",
  "clean_slate": true,
  "copy_from_user_id": null         // or a user_id string
}

// Response (201 Created)
{
  "user_id": "test_user_bulk_20260224",
  "name": "Test User 2026-02-24",
  "source": "bulk_testing"
}
```

Creates the user via the existing `user_testing_access` functions, setting `source: "bulk_testing"` in the user record.

---

### `main.py` (Modified)

Register the new router alongside the existing test router:

```python
from api.test_runs_api import router as test_runs_router, set_runner_dependencies
app.include_router(test_runs_router)
set_runner_dependencies(conversation_manager=conversation_manager)
```

The runner needs a reference to the live `ConversationManager` instance to call `process_message()` directly. `set_runner_dependencies()` is called after both are instantiated.

---

### Scenario YAML Files — Initial Set

Files are placed in `backend/data/test_scenarios/` with alphabetical-prefix naming to enforce group order:

```
backend/data/test_scenarios/
├── a1_ch1_beat_discovery.yaml
├── a2_delilah_solo_dinner_plan.yaml
├── a3_delilah_solo_allergy.yaml
├── a4_delilah_solo_wrong_food.yaml
├── b1_ch2_beat_hank_arrival.yaml
├── b2_hank_solo_shopping.yaml
├── b3_hank_solo_reminder.yaml
├── b4_hank_solo_philosophy.yaml
├── c1_coord_dinner_to_list.yaml
├── c2_coord_list_to_recipe.yaml
└── c3_coord_multiturn_plan.yaml
```

Example — `b1_ch2_beat_hank_arrival.yaml`:

```yaml
id: "ch2_beat_hank_arrival"
name: "Chapter 2 — Beat walk: Hank arrival"
description: "Triggers hank_arrival beat and evaluates both characters' intro voices"
required_chapter: 2
characters_expected: ["delilah", "hank"]
setup_steps:
  - type: "set_chapter"
    chapter: 2
  - type: "trigger_beat"
    beat_id: "hank_arrival"
    variant: "standard"
user_turns:
  - "Is someone new here?"
  - "Hi Hank, nice to meet you."
watch_for_effects:
  - type: "story_beat"
    label: "hank_arrival beat fired"
tags: ["chapter-setup", "hank", "delilah", "multi-character", "beat-walk"]
```

---

## Frontend Architecture

### New & Modified Files

```
frontend/src/
├── components/
│   ├── BulkTestingTool.tsx         ← NEW: Bulk Testing section (main component)
│   └── BulkTestingTool.css         ← NEW: styles
└── services/
    └── api.ts                       ← MODIFIED: new types + API methods
```

The new `BulkTestingTool` tab is registered in `Dashboard.tsx` alongside existing tabs (Logs, Memories, Tool Calls, etc.).

---

### `services/api.ts` (Modified)

**New types:**

```typescript
// Scenario from library
export interface ScenarioSummary {
  id: string;
  name: string;
  description: string;
  required_chapter: number;
  characters_expected: string[];
  tags: string[];
  turn_count: number;
}

// Run summary (for list)
export interface TestRunSummary {
  run_id: string;
  run_label: string;
  started_at: string;
  status: "pending" | "running" | "complete" | "failed" | "cancelled";
  scenario_count: number;
  completed_count: number;
  user_id: string;
}

// Full run result (for detail/poll)
export interface CapturedEffect {
  type: string;
  label: string;
}

export interface TurnResult {
  turn_index: number;
  user_message: string;
  character: string | null;
  response: string;
  turn_id: string;
  effects: CapturedEffect[];
  logs: LogEntry[];           // reuses LogEntry type from Phase 7
}

export interface ScenarioResult {
  scenario_id: string;
  scenario_name: string;
  status: "complete" | "failed" | "skipped";
  duration_seconds: number | null;
  error: string | null;
  turns: TurnResult[];
  expected_effects_missed: Array<{ type: string; label: string }>;
}

export interface TestRunResult {
  run_id: string;
  run_label: string;
  started_at: string;
  completed_at: string | null;
  status: TestRunSummary["status"];
  user_id: string;
  scenario_results: ScenarioResult[];
}
```

**New API methods:**

```typescript
// Scenario library
getScenarios(): Promise<{ scenarios: ScenarioSummary[] }>

// Run management
startTestRun(params: {
  scenario_ids: string[];
  run_all: boolean;
  user_id: string;
  run_label: string;
}): Promise<{ run_id: string; status: string }>

listTestRuns(): Promise<{ runs: TestRunSummary[]; total: number }>

getTestRun(runId: string): Promise<TestRunResult>

cancelTestRun(runId: string): Promise<void>

// Test user creation
createBulkTestUser(params: {
  name: string;
  clean_slate: boolean;
  copy_from_user_id: string | null;
}): Promise<{ user_id: string; name: string; source: string }>
```

---

### `BulkTestingTool.tsx` (New)

The component has three primary view states managed by local React state:

```
BulkTestingTool
├── [view === "suite"]   → SuiteView
│     ├── LeftPanel: ScenarioList + RunControls
│     └── RightPanel: RunHistoryList
│           └── click → [view = "detail", selectedRunId = id]
│
├── [view === "running"] → RunProgressView  (auto-transitions to "detail" on completion)
│     ├── RunHeader (label, user, status)
│     ├── ProgressBar
│     ├── ScenarioStatusList (queued / spinner / ✓ / ✗ / –)
│     └── CancelButton ("Stop after this scenario" / "Stopping...")
│
└── [view === "detail"]  → RunDetailView
      ├── RunHeader (label, user, date, "Compare with..." button)
      ├── [comparison === null] → TranscriptList (single)
      └── [comparison !== null] → ComparisonView (side-by-side)
```

**`ScenarioList` (inside SuiteView left panel):**

- Fetches scenarios via `getScenarios()` on mount (one-time; scenarios are static)
- Renders each scenario as a row: checkbox, name, tag chips, character badges
- "Select All" toggle; tag-based filter chips above the list
- Maintains `selectedIds: Set<string>` in state

**`RunControls` (inside SuiteView left panel):**

- User dropdown: fetches existing users + "BULK TEST" users; "+ New test user" option that opens an inline `CreateTestUserForm`
- Run label text input (default: `"Run — {date} {time}"`)
- `Run Selected` button (disabled when `selectedIds.size === 0`)
- `Run All` button
- On click: calls `startTestRun(...)`, then sets `view = "running"` and `activeRunId = run_id`

**`RunProgressView` (polling loop):**

```typescript
// Polls every 2 seconds while status is "pending" or "running"
const { data: runResult } = useQuery({
  queryKey: ["test-run", activeRunId],
  queryFn: () => api.getTestRun(activeRunId!),
  refetchInterval: (data) =>
    data?.status === "running" || data?.status === "pending" ? 2000 : false,
  enabled: !!activeRunId,
});

// Auto-transition
useEffect(() => {
  if (runResult?.status === "complete" ||
      runResult?.status === "failed" ||
      runResult?.status === "cancelled") {
    setView("detail");
    setSelectedRunId(activeRunId);
    setActiveRunId(null);
  }
}, [runResult?.status]);
```

Progress bar: `completedCount / totalScenarios`. Total is derived from `run.scenario_results.length + skippedCount` — the frontend gets total expected count from the initial `startTestRun` response or from the scenario selection made before start (stored in component state alongside `activeRunId`).

**Cancel button state machine:**

```
idle  →  [user clicks]  →  cancelling  →  [run reaches cancelled]  →  (button disappears)
"Stop after this scenario"   "Stopping…"                         (view transitions to detail)
```

**`TranscriptView` (inside RunDetailView):**

Renders `ScenarioResult[]` as readable conversation blocks. Each block:

1. **Scenario header divider** — name, tags, duration
2. **Setup steps header** (if any) — metadata block styled distinctly from conversation, shows what setup steps ran before the first turn
3. **Turn sequence** — interleaved user / character lines
   - User line: left-gutter indent, muted style
   - Character line: character name in theme colour, response text
   - After each character response: effect lines (`► Effect: ...`) in muted-accent colour
   - After effects: `✗ Expected but not seen: [label]` in warning colour (if applicable)
   - Collapsed `▶ Logs (N entries)` disclosure row — click expands inline log entries using the same `LogEntry` rendering as `SystemLogTool`
4. **Failed scenario notice** — if `status === "failed"`, renders the error string instead of turns

**Character colour mapping** (shared with existing chat UI):

| Character | CSS variable |
|-----------|-------------|
| delilah | `--color-delilah` (warm amber) |
| hank | `--color-hank` (ocean blue) |
| rex | `--color-rex` (energetic orange) |
| unknown | `--color-foreground-muted` |

**`ComparisonView` (inside RunDetailView):**

Two `TranscriptView` instances rendered side-by-side. Scroll linking via a shared scroll proxy:

```typescript
const leftRef  = useRef<HTMLDivElement>(null);
const rightRef = useRef<HTMLDivElement>(null);
let syncingScroll = false;

function onLeftScroll() {
  if (!syncingScroll && rightRef.current) {
    syncingScroll = true;
    rightRef.current.scrollTop = leftRef.current!.scrollTop;
    syncingScroll = false;
  }
}
// Mirror for right → left
```

Scenarios missing from one run are rendered as a placeholder block: `[Scenario "{name}" not present in this run]`.

---

### `Dashboard.tsx` (Modified)

Add `BulkTestingTool` as a new tab entry alongside existing Observability tabs. The tab label is "Bulk Testing". No chapter/character gating — always visible.

---

### `UserTestingTool.tsx` (Modified)

Display a distinct `"BULK TEST"` badge for users with `source: "bulk_testing"` (different colour from the existing `"TEST"` badge for source `"test_user"`). No other logic changes.

---

## Data Flow: Full Test Run

```
1. Developer selects scenarios + user, clicks "Run All"
   │
   ▼
2. Frontend: POST /api/test-runs
   │  { run_all: true, user_id: "test_bulk_01", run_label: "Baseline" }
   │→ Runner creates TestRunResult (status: pending), spawns asyncio task
   │← { run_id: "run_20260224_143022", status: "pending" }
   │
   ▼
3. Frontend: sets view = "running", begins polling GET /api/test-runs/{run_id} every 2s
   │
   ▼
4. Runner (background): for each scenario in load_all() order...
   │
   ├─ 4a. Apply setup_steps (direct function calls to user_testing_access / story_access)
   │
   ├─ 4b. For each user_turn:
   │     │  generate fresh conversation_id for scenario (shared across turns in scenario)
   │     │  call conversation_manager.process_message(turn, user_id, conversation_id)
   │     │  extract turn_id from response
   │     │  call tool_call_access.get_tool_calls_for_turn(turn_id) → effects
   │     │  call log_handler.get_logs_for_turn(turn_id) → log records
   │     │  build TurnResult, append to scenario
   │     │
   │     └─ persist run incrementally (after each scenario)
   │
   └─ 4c. On completion: run.status = "complete", final persist
   │
   ▼
5. Frontend poll: response.status === "complete" → setView("detail")
   │
   ▼
6. RunDetailView renders TranscriptView for each ScenarioResult
   │  character lines styled by character name
   │  ► Effect: lines after each character response
   │  ▶ Logs (N) disclosure rows collapsed by default
   │
   ▼
7. Developer reads transcript, clicks "Compare with..."
   │  selects a prior run from the picker
   │  ComparisonView renders both TranscriptViews side-by-side with scroll linking
```

---

## Integration Points with Existing Systems

| Existing component | How Phase 8 uses it |
|--------------------|---------------------|
| `ConversationManager.process_message()` | Called directly (in-process) for each user turn |
| `tool_call_access.get_tool_calls_for_turn(turn_id)` | Effect capture after each turn |
| `log_handler.get_logs_for_turn(turn_id)` | Log capture after each turn |
| `user_testing_access` | Setup step `set_chapter`; new test user creation |
| `story_access.trigger_beat(...)` | Setup step `trigger_beat` |
| `POST /test/state/{user_id}` logic | Reused via direct function call (not HTTP) |
| `ObservabilityLogHandler` | `get_logs_for_turn` filter queried immediately after turn |
| `LogEntry` type (Phase 7) | Reused in `TurnResult.logs` and in the transcript log disclosure rows |
| User source field (`"test_user"`) | Extended with `"bulk_testing"` value |

---

## Migration Notes

### Breaking Changes
None. All new code is additive. Existing endpoints, models, and frontend components are unchanged except:
- `Dashboard.tsx` gets a new tab (additive)
- `UserTestingTool.tsx` adds a badge variant (additive)
- `services/api.ts` adds new types and methods (additive)

### New Directories
Two new data directories must exist before the server starts:

```bash
mkdir -p backend/data/test_scenarios
mkdir -p backend/data/test_runs
```

`backend/data/test_scenarios/` is version-controlled (YAML files committed with the codebase).
`backend/data/test_runs/` is not version-controlled — add to `.gitignore`.

### `tool_call_access` — `get_tool_calls_for_turn`

The runner needs to query tool calls by `turn_id`. Phase 7 introduced `turn_id` on log records; the same field should be present on tool call records stored by `tool_call_access.py`. If this method does not exist, it is added as part of Milestone 2. No schema migration is needed — tool call records already include `turn_id` from Phase 7 logging correlation.

---

## Dependencies

### Backend

No new packages beyond what Phase 7 added.

| Package | Already present | Usage |
|---------|----------------|-------|
| `pyyaml` | Check at M1 / add if missing | Scenario YAML parsing |
| `httpx` | Already present (used in tests) | Not needed — direct function calls used instead |
| `asyncio` | stdlib | Background task execution |
| `pydantic` | Already present | Run and scenario models |

`pyyaml` is the only potential new dependency. If not in `requirements.txt`, it is added in Milestone 1.

### Frontend

No new packages required. All patterns used (polling with `@tanstack/react-query`, scroll refs, CSS side-by-side layout) are already established in the codebase.
