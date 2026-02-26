# Phase 8: Experience Testing Suite — Implementation Plan

**Version:** 1.0
**Last Updated:** February 24, 2026
**Status:** Not Started

---

## References

- **PRD:** [PRD.md](PRD.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Observability API:** `backend/src/observability/api.py`
- **Observability log handler:** `backend/src/observability/log_handler.py`
- **Tool call access:** `backend/src/observability/tool_call_access.py`
- **User testing access:** `backend/src/observability/user_testing_access.py`
- **Story access:** `backend/src/observability/story_access.py`
- **Test API (setup step calls):** `backend/src/api/test_api.py`
- **Conversation manager:** `backend/src/core/conversation_manager.py`
- **Application entry point:** `backend/src/main.py`
- **Frontend Dashboard:** `frontend/src/components/Dashboard.tsx`
- **Frontend API client:** `frontend/src/services/api.ts`
- **User Testing Tool:** `frontend/src/components/UserTestingTool.tsx`

---

## Overview

### Goals

Deliver an Experience Testing Suite: a one-click, UI-driven tool that runs the full set of scripted scenarios against the live system, captures conversation transcripts and tool effects, persists results, and lets the developer review and compare runs in a readable transcript format — without opening a terminal.

### Timeline Estimate

- **Total Duration:** 2–3 weeks
- **Milestone Count:** 6 milestones

### Success Criteria

- Developer can trigger all 11 scenarios with one button click and read every resulting transcript with effects annotated
- Results persist across server restarts; old runs are not lost on reload
- Test runs never affect the primary user's memories or story progress
- Adding a new scenario requires only dropping a YAML file in `backend/data/test_scenarios/` — zero code changes
- All existing backend tests pass unchanged after each milestone
- Automated tests cover the scenario loader, runner logic, effect capture, and API endpoints

---

## Dependency Note: PyYAML

`pyyaml` is not currently in `backend/requirements.txt`. It must be added in **Milestone 1** before any YAML loading code is written.

```bash
echo "pyyaml==6.0.2" >> backend/requirements.txt
pip install pyyaml==6.0.2
```

---

## Milestone 1: Scenario Library & Data Model

**Status:** Not Started
**Goal:** Define the Pydantic data models for scenarios and run results, write the YAML scenario loader, create the 11 initial scenario YAML files, and create the `backend/data/test_scenarios/` and `backend/data/test_runs/` directories.

### Files Changed

#### `backend/requirements.txt` (modified)

Add `pyyaml==6.0.2` to the file.

#### `backend/data/test_scenarios/` (new directory + 11 YAML files)

Files named with group-prefix convention so alphabetical order enforces Group A → B → C execution:

```
a1_ch1_beat_discovery.yaml
a2_delilah_solo_dinner_plan.yaml
a3_delilah_solo_allergy.yaml
a4_delilah_solo_wrong_food.yaml
b1_ch2_beat_hank_arrival.yaml
b2_hank_solo_shopping.yaml
b3_hank_solo_reminder.yaml
b4_hank_solo_philosophy.yaml
c1_coord_dinner_to_list.yaml
c2_coord_list_to_recipe.yaml
c3_coord_multiturn_plan.yaml
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

Group A files use `required_chapter: 1` and no `setup_steps`. Group B files use `required_chapter: 2` with `set_chapter` + `trigger_beat` setup steps. Group C files use `required_chapter: 2` with only `set_chapter` (group B already fired `hank_arrival`; C assumes the chapter is set).

#### `backend/data/test_runs/` (new empty directory)

Add a `.gitkeep` file so the directory is tracked. Add `backend/data/test_runs/*.json` to `.gitignore`.

#### `backend/src/models/test_run_models.py` (new file)

All Pydantic data models shared by the loader, runner, and API:

```python
from __future__ import annotations
from typing import List, Literal, Optional
from pydantic import BaseModel


# ── Scenario models (loaded from YAML) ────────────────────────────────────

class SetupStep(BaseModel):
    type: Literal["set_chapter", "trigger_beat"]
    chapter: Optional[int] = None
    beat_id: Optional[str] = None
    variant: Optional[str] = "standard"


class WatchForEffect(BaseModel):
    type: Literal["tool_call", "character_handoff", "story_beat", "memory_saved", "timer_set"]
    tool: Optional[str] = None   # for tool_call
    to: Optional[str] = None     # for character_handoff
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


# ── Run request ────────────────────────────────────────────────────────────

class TestRunRequest(BaseModel):
    scenario_ids: List[str] = []
    run_all: bool = False
    user_id: str
    run_label: str


# ── Run result models (persisted as JSON) ─────────────────────────────────

class CapturedEffect(BaseModel):
    type: str
    label: str
    raw: Optional[dict] = None


class TurnResult(BaseModel):
    turn_index: int
    user_message: str
    character: Optional[str] = None
    response: str
    turn_id: str
    effects: List[CapturedEffect] = []
    logs: List[dict] = []


class ScenarioResult(BaseModel):
    scenario_id: str
    scenario_name: str
    status: Literal["complete", "failed", "skipped"]
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    turns: List[TurnResult] = []
    expected_effects_missed: List[WatchForEffect] = []


class TestRunResult(BaseModel):
    run_id: str
    run_label: str
    started_at: str
    completed_at: Optional[str] = None
    status: Literal["pending", "running", "complete", "failed", "cancelled"]
    user_id: str
    scenario_results: List[ScenarioResult] = []


# ── List endpoint summary ──────────────────────────────────────────────────

class TestRunSummary(BaseModel):
    run_id: str
    run_label: str
    started_at: str
    status: str
    scenario_count: int
    completed_count: int
    user_id: str
```

#### `backend/src/core/scenario_loader.py` (new file)

```python
from __future__ import annotations
from pathlib import Path
from typing import List
import yaml

from models.test_run_models import Scenario

SCENARIOS_DIR = Path(__file__).parent.parent.parent / "data" / "test_scenarios"


def load_all() -> List[Scenario]:
    """Load all *.yaml scenario files, sorted alphabetically by filename."""
    scenarios: List[Scenario] = []
    for path in sorted(SCENARIOS_DIR.glob("*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            scenarios.append(Scenario.model_validate(raw))
        except Exception as exc:
            raise ValueError(f"Failed to load scenario file {path.name}: {exc}") from exc
    return scenarios


def load_by_ids(ids: List[str]) -> List[Scenario]:
    """Return scenarios matching `ids`, in load_all() (alphabetical) order."""
    all_by_id = {s.id: s for s in load_all()}
    missing = [i for i in ids if i not in all_by_id]
    if missing:
        raise ValueError(f"Unknown scenario IDs: {missing}")
    return [s for s in all_by_id.values() if s.id in set(ids)]
```

### Verification

```bash
cd backend && source .venv/bin/activate
python -c "
import sys; sys.path.insert(0, 'src')
from core.scenario_loader import load_all
scenarios = load_all()
print(f'Loaded {len(scenarios)} scenarios')
for s in scenarios:
    print(f'  {s.id}: {len(s.user_turns)} turns, chapter {s.required_chapter}')
"
```

Expected output: 11 scenarios listed, none throwing validation errors.

### Test File: `backend/tests/test_phase8_milestone1.py`

```python
"""
Tests for Phase 8 Milestone 1: Scenario Library & Data Model.

Covers:
- ScenarioLoader loads all YAML files in alphabetical order
- ScenarioLoader validates required fields via Pydantic
- ScenarioLoader raises on malformed YAML
- ScenarioLoader raises on unknown scenario IDs in load_by_ids
- load_by_ids returns correct subset in alphabetical order
- Group A files have required_chapter=1 and no setup_steps
- Group B files have required_chapter=2
- SetupStep validation: set_chapter requires chapter field
- SetupStep validation: trigger_beat requires beat_id field
- All 11 initial scenario IDs are present and unique
- Each scenario has at least one user_turn
- TestRunResult serialises to and from JSON without data loss
"""
```

**Test scope details:**
- `load_all()` returns a non-empty list; IDs are unique; count matches files on disk
- Alphabetical filename order is respected (a1_ before a2_ before b1_)
- `load_by_ids(["ch1_beat_discovery"])` returns exactly that one scenario
- `load_by_ids(["nonexistent"])` raises `ValueError` mentioning the unknown ID
- A temporary YAML file with a missing `id` field raises `ValueError` on load
- `set_chapter` setup step without a `chapter` field fails Pydantic validation
- `trigger_beat` setup step without a `beat_id` field fails Pydantic validation
- Every Group A scenario has `required_chapter == 1`
- Every Group B/C scenario has `required_chapter == 2`
- `TestRunResult(run_id="x", run_label="y", started_at="...", status="pending", user_id="u").model_dump_json()` round-trips correctly

### Regression Guard

```bash
cd backend && source .venv/bin/activate
pytest tests/ -v --tb=short
```

---

## Milestone 2: Scenario Runner Backend

**Status:** Not Started
**Goal:** Build the async runner engine, the `/api/test-runs` REST endpoints, and effect capture. The runner calls `ConversationManager.process_message()` directly, persists incremental results to `backend/data/test_runs/`, enforces the 50-run cap, and honours a cancellation flag between scenarios.

### Files Changed

#### `backend/src/core/scenario_runner.py` (new file)

Module-level singleton state:

```python
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone

_active_run_id: str | None = None
_cancel_flags: dict[str, bool] = {}   # run_id → cancel requested
_conversation_manager = None          # injected at startup


def set_conversation_manager(cm) -> None:
    global _conversation_manager
    _conversation_manager = cm


def get_active_run_id() -> str | None:
    return _active_run_id


def request_cancel(run_id: str) -> None:
    _cancel_flags[run_id] = True
```

**`start_run(request: TestRunRequest) → str`** (synchronous, called by endpoint):

1. If `_active_run_id` is not `None`, raise `RuntimeError("run already active")`
2. Generate `run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"`
3. Select scenarios: `load_all()` if `run_all` else `load_by_ids(request.scenario_ids)`
4. Build initial `TestRunResult` with `status="pending"` and one `ScenarioResult(status="skipped")` per scenario (pre-populated so progress count is known)
5. Persist to disk
6. Set `_active_run_id = run_id`
7. Schedule `asyncio.create_task(_run_scenarios(run_id, scenarios, request))`
8. Return `run_id`

**`_run_scenarios` coroutine** (private, runs in background):

```python
async def _run_scenarios(run_id, scenarios, request):
    run = _load_run(run_id)
    run.status = "running"
    _persist_run(run)
    try:
        for idx, scenario in enumerate(scenarios):
            if _cancel_flags.get(run_id):
                # Mark remaining as skipped (already pre-filled as skipped)
                break
            result = await _execute_scenario(scenario, request.user_id, run_id)
            run.scenario_results[idx] = result
            _persist_run(run)      # incremental write after each scenario
        else:
            run.status = "complete"
    except Exception as e:
        run.status = "failed"
        logger.error(f"Run {run_id} failed: {e}", exc_info=True)
    finally:
        if _cancel_flags.get(run_id) and run.status == "running":
            run.status = "cancelled"
        run.completed_at = datetime.now(timezone.utc).isoformat()
        _persist_run(run)
        _cancel_flags.pop(run_id, None)
        global _active_run_id
        _active_run_id = None
```

**`_execute_scenario` coroutine**:

1. Apply `setup_steps` (call `user_testing_access` and `story_access` functions directly)
2. Generate a fresh `conversation_id` for this scenario using `generate_id()`
3. For each `user_turn`:
   - Call `conversation_manager.process_message(user_message, conversation_id, user_id)`
   - Extract `turn_id` from response
   - Call `_capture_effects(turn_id, user_id)` → `List[CapturedEffect]`
   - Call `log_handler.get_handler().get_logs(turn_id=turn_id)` → raw log dicts
   - Build `TurnResult` and append
4. Compute `expected_effects_missed` by diffing `scenario.watch_for_effects` against captured effect types/labels
5. Return completed `ScenarioResult`

**Effect capture — `_capture_effects(turn_id, user_id)`**:

```python
EFFECT_TYPE_MAP = {
    "request_handoff":    ("character_handoff", lambda tc: f"Handoff: {tc.get('character')} → {tc.get('result', {}).get('to', '?')}"),
    "advance_story_beat": ("story_beat",        lambda tc: f"Story beat advanced: {tc.get('arguments', {}).get('beat_id', '?')}"),
    "save_memory":        ("memory_saved",       lambda tc: f"Memory saved: {str(tc.get('result', ''))[:60]}"),
    "set_timer":          ("timer_set",          lambda tc: f"Timer set: {tc.get('arguments', {}).get('duration', '?')}"),
}
# All other tool calls → type="tool_call", label="<tool_name>: <result summary>"
```

**Run storage**:

```python
RUNS_DIR = Path(__file__).parent.parent.parent / "data" / "test_runs"

def _persist_run(run: TestRunResult) -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (RUNS_DIR / f"{run.run_id}.json").write_text(run.model_dump_json(indent=2))
    _enforce_run_cap()

def _enforce_run_cap(max_runs: int = 50) -> None:
    files = sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    while len(files) > max_runs:
        files.pop(0).unlink()
        files = files[1:]   # re-align after pop

def _load_run(run_id: str) -> TestRunResult:
    path = RUNS_DIR / f"{run_id}.json"
    return TestRunResult.model_validate_json(path.read_text())

def list_runs() -> List[TestRunResult]:
    runs = []
    for path in sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        runs.append(TestRunResult.model_validate_json(path.read_text()))
    return runs
```

#### `backend/src/api/test_runs_api.py` (new file)

Router registered at prefix `/api/test-runs`:

```python
from fastapi import APIRouter, HTTPException
from models.test_run_models import TestRunRequest, TestRunResult, TestRunSummary, Scenario
from core import scenario_runner, scenario_loader

router = APIRouter(prefix="/api/test-runs", tags=["test-runs"])

_conversation_manager = None

def set_runner_dependencies(conversation_manager) -> None:
    _conversation_manager = conversation_manager
    scenario_runner.set_conversation_manager(conversation_manager)


@router.post("", status_code=202)
async def start_test_run(request: TestRunRequest):
    try:
        run_id = scenario_runner.start_run(request)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"run_id": run_id, "status": "pending"}


@router.get("")
async def list_test_runs():
    runs = scenario_runner.list_runs()
    summaries = [
        TestRunSummary(
            run_id=r.run_id,
            run_label=r.run_label,
            started_at=r.started_at,
            status=r.status,
            scenario_count=len(r.scenario_results),
            completed_count=sum(1 for s in r.scenario_results if s.status == "complete"),
            user_id=r.user_id,
        )
        for r in runs
    ]
    return {"runs": summaries, "total": len(summaries)}


@router.get("/scenarios")
async def list_scenarios():
    scenarios = scenario_loader.load_all()
    return {
        "scenarios": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "required_chapter": s.required_chapter,
                "characters_expected": s.characters_expected,
                "tags": s.tags,
                "turn_count": len(s.user_turns),
            }
            for s in scenarios
        ]
    }


@router.get("/{run_id}")
async def get_test_run(run_id: str):
    try:
        return scenario_runner._load_run(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found")


@router.post("/{run_id}/cancel", status_code=202)
async def cancel_test_run(run_id: str):
    active = scenario_runner.get_active_run_id()
    if active != run_id:
        # Check if the run exists but is already terminal
        try:
            run = scenario_runner._load_run(run_id)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found")
        if run.status in ("complete", "failed", "cancelled"):
            raise HTTPException(status_code=409, detail=f"Run {run_id!r} is already {run.status}")
    scenario_runner.request_cancel(run_id)
    return {"message": "Cancellation requested"}


@router.post("/users", status_code=201)
async def create_bulk_test_user(body: dict):
    # Delegates to user_testing_access; sets source="bulk_testing"
    from observability.user_testing_access import UserTestingDataAccess
    import os
    data_dir = os.getenv("DATA_DIR", "data")
    access = UserTestingDataAccess(data_dir)
    user = access.create_test_user(
        name=body.get("name", "Bulk Test User"),
        source="bulk_testing",
        copy_from_user_id=body.get("copy_from_user_id"),
        clean_slate=body.get("clean_slate", True),
    )
    return {"user_id": user.user_id, "name": user.name, "source": user.source}
```

#### `backend/src/main.py` (modified)

After creating `conversation_manager`, register the new router:

```python
from api.test_runs_api import router as test_runs_router, set_runner_dependencies
app.include_router(test_runs_router)
set_runner_dependencies(conversation_manager=conversation_manager)
```

### Verification

```bash
# Start server
cd backend && source .venv/bin/activate
python -m uvicorn src.main:app --reload --port 8000 &

# List scenarios
curl -s http://localhost:8000/api/test-runs/scenarios | python3 -m json.tool | head -30

# Start a single-scenario run (requires a valid test user)
curl -s -X POST http://localhost:8000/api/test-runs \
  -H "Content-Type: application/json" \
  -d '{"scenario_ids": ["ch1_beat_discovery"], "user_id": "user_justin", "run_label": "smoke test", "run_all": false}' \
  | python3 -m json.tool

# Poll status
curl -s http://localhost:8000/api/test-runs/run_<ID> | python3 -m json.tool
```

### Test File: `backend/tests/test_phase8_milestone2.py`

```python
"""
Tests for Phase 8 Milestone 2: Scenario Runner Backend.

Covers:
- start_run() returns a run_id and persists the initial pending file
- start_run() raises when another run is already active
- _execute_scenario() with a mocked ConversationManager builds correct TurnResult
- _capture_effects() maps request_handoff tool call to character_handoff effect
- _capture_effects() maps advance_story_beat tool call to story_beat effect
- _capture_effects() maps set_timer tool call to timer_set effect
- _capture_effects() maps save_memory tool call to memory_saved effect
- _capture_effects() maps unknown tool calls to generic tool_call effect
- expected_effects_missed computation: expected effect that triggers → not in missed list
- expected_effects_missed computation: expected effect that does not trigger → in missed list
- 50-run cap: creating 51 runs deletes the oldest (by mtime)
- cancel: setting cancel flag stops run between scenarios (completed scenario results preserved)
- list_runs() returns runs newest-first
- GET /api/test-runs/scenarios returns correct count and fields
- POST /api/test-runs returns 409 when a run is already active
- GET /api/test-runs/{run_id} returns 404 for unknown run_id
- POST /api/test-runs/{run_id}/cancel returns 409 for already-complete run
"""
```

**Test design notes:**

- `ConversationManager` is replaced with an `AsyncMock` that returns `{"text": "response", "character": "delilah", "turn_id": "fake-turn-id", "metadata": {"turn_id": "fake-turn-id"}}`
- `tool_call_access` is patched to return synthetic `ToolCallLog` objects for effect capture tests
- `log_handler.get_handler().get_logs(turn_id=...)` is patched to return an empty list (log capture is integration detail; tested separately in Phase 7 tests)
- The 50-run cap test creates 51 tiny stub JSON files in a temp directory, calls `_enforce_run_cap()`, and asserts 50 remain
- The cancel test uses `asyncio.create_task` with a patched runner that checks the flag before each iteration

### Regression Guard

```bash
cd backend && source .venv/bin/activate
pytest tests/ -v --tb=short
```

---

## Milestone 3: Bulk Testing UI — Suite Controls

**Status:** Not Started
**Goal:** Add the "Bulk Testing" tab to the Observability dashboard. Implement the scenario picker, user selector, run label input, and run trigger buttons. The view shows a live loading state while the run is pending; run transitions to the progress view (Milestone 4) on start.

### Files Changed

#### `frontend/src/services/api.ts` (modified)

Add new types and API methods:

```typescript
// New types
export interface ScenarioSummary {
  id: string;
  name: string;
  description: string;
  required_chapter: number;
  characters_expected: string[];
  tags: string[];
  turn_count: number;
}

export interface TestRunSummary {
  run_id: string;
  run_label: string;
  started_at: string;
  status: "pending" | "running" | "complete" | "failed" | "cancelled";
  scenario_count: number;
  completed_count: number;
  user_id: string;
}

// New API methods
getScenarios: () => Promise<{ scenarios: ScenarioSummary[] }>
startTestRun: (params: { scenario_ids: string[]; run_all: boolean; user_id: string; run_label: string }) => Promise<{ run_id: string; status: string }>
listTestRuns: () => Promise<{ runs: TestRunSummary[]; total: number }>
getTestRun: (runId: string) => Promise<TestRunResult>
cancelTestRun: (runId: string) => Promise<void>
createBulkTestUser: (params: { name: string; clean_slate: boolean; copy_from_user_id: string | null }) => Promise<{ user_id: string; name: string; source: string }>
```

Remaining types (`CapturedEffect`, `TurnResult`, `ScenarioResult`, `TestRunResult`) are added at the same time; they are used in Milestone 4 but declared here to keep all API types co-located.

#### `frontend/src/components/BulkTestingTool.tsx` (new file) — Suite Controls portion

The component manages three view states (`"suite"`, `"running"`, `"detail"`) via `useState`. Milestone 3 delivers `"suite"` only; `"running"` and `"detail"` render a placeholder until Milestones 4–5.

```typescript
// State
const [view, setView] = useState<"suite" | "running" | "detail">("suite");
const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
const [activeRunId, setActiveRunId] = useState<string | null>(null);
const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
const [userId, setUserId] = useState<string>("");
const [runLabel, setRunLabel] = useState<string>(`Run — ${new Date().toLocaleString()}`);
const [tagFilter, setTagFilter] = useState<string | null>(null);
```

**Left panel — ScenarioList:**
- Fetches `getScenarios()` once on mount (`staleTime: Infinity`)
- Renders tag filter chips above the list
- Each row: checkbox, scenario name, required-chapter badge, tag chips, character avatars
- "Select All / Deselect All" toggle at top

**Left panel — RunControls:**
- User dropdown (fetches existing users; marks BULK TEST users distinctly)
- "+ New test user" option opens an inline `CreateTestUserForm` (name input + clean_slate checkbox)
- Run label text input
- `Run Selected` button — disabled when `selectedIds.size === 0`; calls `startTestRun` with selected IDs
- `Run All` button — calls `startTestRun` with `run_all: true`

**Right panel placeholder** (Milestone 3): Static "Run History — coming in next milestone" text.

#### `frontend/src/components/BulkTestingTool.css` (new file)

Two-column layout, tag chip styles, character avatar badges, scenario row hover styles.

#### `frontend/src/components/Dashboard.tsx` (modified)

Add "Bulk Testing" to the tab list. Import and render `BulkTestingTool` when that tab is active. No other changes.

### Verification

1. Start backend and frontend: `./scripts/servers.sh start`
2. Open Observability at `http://localhost:5173/observability`
3. Confirm "Bulk Testing" tab appears in navigation
4. Click tab: left panel shows 11 scenarios with names, tags, and character badges
5. Check individual scenarios and confirm checkboxes work; "Select All" selects all 11
6. Select a user from the dropdown; edit the run label
7. Click "Run Selected": a `POST /api/test-runs` is sent (verify in browser Network tab); component enters loading state

### Regression Guard

Confirm all existing tabs (Logs, Memories, Tool Calls, Story Beats, Characters, User Testing) still render and function normally after the Dashboard change.

---

## Milestone 4: Bulk Testing UI — Progress View & Transcript View

**Status:** Not Started
**Goal:** Implement the live run progress view (polling, cancel button) and the full conversation transcript renderer with inline effect annotations, collapsible log disclosure rows, and the "Expected but not seen" warning display.

### Files Changed

#### `frontend/src/components/BulkTestingTool.tsx` (modified)

**`RunProgressView`** (view state: `"running"`):

```typescript
const { data: runResult } = useQuery({
  queryKey: ["test-run", activeRunId],
  queryFn: () => api.getTestRun(activeRunId!),
  refetchInterval: (query) => {
    const status = query.state.data?.status;
    return status === "running" || status === "pending" ? 2000 : false;
  },
  enabled: !!activeRunId,
});

// Auto-transition to detail on completion or cancellation
useEffect(() => {
  if (!runResult) return;
  const terminal = ["complete", "failed", "cancelled"];
  if (terminal.includes(runResult.status)) {
    setView("detail");
    setSelectedRunId(activeRunId);
    setActiveRunId(null);
  }
}, [runResult?.status]);
```

Progress bar: `completedCount / totalExpected` where `totalExpected` is stored in state when the run starts (from the count of selected scenario IDs or from `scenarios.length` for Run All).

Scenario status list: iterate `runResult.scenario_results` — statuses `"complete"` (✓), `"failed"` (✗), `"skipped"` (–); scenarios not yet in results list shown as "queued" with a spinner on the first absent one.

Cancel button state machine — three visual states managed by `useState<"idle" | "cancelling">`:
- `"idle"`: "Stop after this scenario" button, enabled
- `"cancelling"`: "Stopping…" button, disabled; clicking calls `cancelTestRun(activeRunId)` and sets state to `"cancelling"`
- Button disappears when view transitions to `"detail"`

**`TranscriptView`** (sub-component, view state: `"detail"` without comparison):

Renders an array of `ScenarioResult` objects as conversation blocks:

```
┌─ ScenarioHeader: name · tags · duration ─────────────────────────────────────┐
│  [Setup steps metadata block — if present]                                    │
│                                                                                │
│    You: [user message]                                                        │
│                                                                                │
│    Delilah: [character response text]                                         │
│    ► Effect: [effect label]                                                   │
│    ✗ Expected but not seen: [label]                                           │
│    ▶ Logs (N entries)                                                         │
│         [collapsed — expands inline on click]                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

Character name colour: driven by a small map:

```typescript
const CHARACTER_COLORS: Record<string, string> = {
  delilah:  "var(--color-delilah)",
  hank:     "var(--color-hank)",
  rex:      "var(--color-rex)",
  dimitria: "var(--color-dimitria)",
};
```

Log disclosure rows use per-turn state: `Map<string, boolean>` keyed on `turn_id`. Expanding fetches nothing new — the logs are already embedded in `TurnResult.logs` from the run result JSON. Render logs using the same level badge + structured field layout as `SystemLogTool`.

Failed scenario: instead of turn sequence, render the `error` string in an error-styled box.

Cancelled run: banner at top of transcript area: *"Run cancelled — results below are from completed scenarios only."*

#### `frontend/src/components/BulkTestingTool.css` (modified)

Styles for:
- Progress bar track + fill
- Scenario status list rows (✓ green, ✗ red, – muted, spinner orange)
- Transcript scenario divider header
- User turn row (left-gutter indent, muted background)
- Character name (bold, theme colour)
- Effect line (muted-accent, `►` indicator)
- Missed effect line (warning orange, `✗` indicator)
- Setup steps metadata block (italic, muted)
- Log disclosure row (expandable, monospace nested block)

### Verification

1. Start a run using the suite controls from Milestone 3
2. Confirm progress bar advances as scenarios complete
3. Confirm "Stop after this scenario" button cancels between scenarios (not mid-scenario)
4. After run completes, transcript view renders automatically
5. Confirm user/character turns are visually distinct
6. Confirm `► Effect:` lines appear in correct positions
7. Click `▶ Logs (N)` — confirms logs expand inline; collapse does not shift scroll position
8. Start a run, cancel mid-way; confirm cancelled banner appears and completed scenarios are shown

### Regression Guard

All tabs and chat functionality work normally. Cancelling a run does not leave `_active_run_id` stuck (verified by being able to start a new run immediately after).

---

## Milestone 5: Bulk Testing UI — Run History & Comparison

**Status:** Not Started
**Goal:** Implement the run history list in the right panel of the suite view, the "Compare with..." run picker, and the scroll-linked side-by-side comparison view.

### Files Changed

#### `frontend/src/components/BulkTestingTool.tsx` (modified)

**`RunHistoryList`** (right panel when `view === "suite"` and no run is active):

Fetches `listTestRuns()` on mount with a `staleTime` of 5 seconds (not aggressively re-fetched):

```typescript
const { data: runsData, refetch: refetchRuns } = useQuery({
  queryKey: ["test-runs"],
  queryFn: () => api.listTestRuns(),
  staleTime: 5_000,
});
```

Renders each run as a card: label, date/time, user, scenario count, status badge. Clicking a card sets `view = "detail"` and `selectedRunId = run.run_id`.

**`RunDetailView`** (view state: `"detail"`):

Full detail view for a single run. Loads the full `TestRunResult` via `getTestRun(selectedRunId)`. Renders:
- Header: run label, date/time, user; `← Back` button to return to suite view; `Compare with...` button
- Transcript via `TranscriptView` (from Milestone 4)

**`ComparisonView`** (when a comparison run is selected):

Side-by-side: left = primary run, right = comparison run. Both are fetched and rendered via `TranscriptView`. Scroll linking:

```typescript
const leftRef  = useRef<HTMLDivElement>(null);
const rightRef = useRef<HTMLDivElement>(null);
let lockScroll = false;

function handleLeftScroll() {
  if (lockScroll || !rightRef.current) return;
  lockScroll = true;
  rightRef.current.scrollTop = leftRef.current!.scrollTop;
  lockScroll = false;
}
function handleRightScroll() {
  if (lockScroll || !leftRef.current) return;
  lockScroll = true;
  leftRef.current.scrollTop = rightRef.current!.scrollTop;
  lockScroll = false;
}
```

Scenarios missing from one run are shown in a placeholder block:
```
[Scenario "coord_dinner_to_list" not present in this run]
```

The comparison run picker is a modal or dropdown showing `RunHistoryList` excluding the current run. Selecting sets `comparisonRunId` in state.

#### `frontend/src/components/BulkTestingTool.css` (modified)

- Run history card styles (label bold, metadata muted, status badge colours)
- Side-by-side layout: two equal-width `overflow-y: scroll` panels inside a flex row
- Missing-scenario placeholder block style
- "Compare with…" button style
- Back navigation link

### Verification

1. Complete at least two runs with different labels
2. Open suite view — confirm both runs appear in right panel, newest first
3. Click a run — detail view opens showing full transcript
4. Click "Compare with…" — run picker shows the other run
5. Select it — side-by-side view renders; both transcripts visible
6. Scroll left panel — right panel follows; scroll right — left follows
7. A scenario present in only one run shows the placeholder on the other side

### Regression Guard

All previous milestones function normally. No regressions in existing tabs.

---

## Milestone 6: Test User Integration

**Status:** Not Started
**Goal:** Wire up the "New test user" creation flow in the Bulk Testing UI and display the "BULK TEST" badge in the existing User Testing Tool for users with `source: "bulk_testing"`.

### Files Changed

#### `backend/src/observability/user_testing_access.py` (modified)

Add `source` parameter to the test user creation function (if not already present):

```python
def create_test_user(
    self,
    name: str,
    source: str = "test_user",
    copy_from_user_id: Optional[str] = None,
    clean_slate: bool = True,
) -> UserProfile:
    ...
    profile.source = source  # persist in user JSON
    ...
```

The `source` field is already present in `UserProfile` from Phase 1.5; this change only ensures the value `"bulk_testing"` can be passed and persisted.

#### `frontend/src/components/UserTestingTool.tsx` (modified)

Add a "BULK TEST" badge variant for `source === "bulk_testing"`:

```typescript
function SourceBadge({ source }: { source?: string }) {
  if (source === "bulk_testing") {
    return <span className="badge badge-bulk-test">BULK TEST</span>;
  }
  if (source === "test_user") {
    return <span className="badge badge-test">TEST</span>;
  }
  return null;
}
```

The badge colour is distinct from the existing "TEST" badge — use a different hue (e.g., purple vs the existing orange/amber).

#### `frontend/src/components/UserTestingTool.css` (modified)

```css
.badge-bulk-test {
  background-color: var(--color-badge-bulk-test, #7c3aed);
  color: white;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 3px;
  letter-spacing: 0.05em;
}
```

#### `frontend/src/components/BulkTestingTool.tsx` (modified)

Wire the `CreateTestUserForm` (stubbed in Milestone 3) to call `createBulkTestUser()` and:
1. Refresh the user dropdown
2. Auto-select the newly created user

### Verification

1. Open Bulk Testing tab, click "+ New test user"
2. Enter a name, leave "Start with clean slate" checked, click Create
3. New user appears in the user selector, pre-selected
4. Open User Testing Tool tab — new user appears with purple "BULK TEST" badge
5. New user can be deleted from User Testing Tool like any other test user
6. Start a run under the new user — run result stores that user's ID
7. Delete the user; re-open the run detail — user ID shows with "(user deleted)" note

### Regression Guard

Existing test users (source: "test_user") still display the existing orange "TEST" badge. Production users (source: null or not present) show no badge.

---

## Full Regression Test Plan

Run after all milestones are complete.

### Backend

```bash
cd backend && source .venv/bin/activate

# Existing phase tests
pytest tests/test_phase4_5_milestone1.py \
       tests/test_phase4_5_milestone2.py \
       tests/test_phase4_5_milestone3.py \
       tests/test_phase4_5_milestone4.py \
       tests/test_phase4_5_milestone5.py \
       tests/test_phase51_milestone1.py \
       tests/test_phase51_milestone2.py \
       tests/test_phase51_milestone3.py \
       tests/test_phase51_milestone4.py \
       tests/test_phase5_deferred_tasks.py \
       tests/test_story_engine.py \
       tests/test_phase7_milestone1.py \
       tests/test_phase7_milestone2.py \
       tests/test_phase7_milestone3.py \
       tests/test_phase7_milestone4.py \
       tests/test_phase7_milestone5.py \
       -v --tb=short

# Phase 8 suite
pytest tests/test_phase8_milestone1.py \
       tests/test_phase8_milestone2.py \
       -v --tb=short
```

### Manual Bulk Testing API Smoke Test

```bash
BASE="http://localhost:8000"

# List scenarios
curl -s "$BASE/api/test-runs/scenarios" | python3 -m json.tool | grep '"id"'
# Expected: 11 scenario IDs

# Start a run (replace user_id with an existing test user)
RUN=$(curl -s -X POST "$BASE/api/test-runs" \
  -H "Content-Type: application/json" \
  -d '{"scenario_ids": ["ch1_beat_discovery"], "user_id": "user_justin", "run_label": "manual smoke", "run_all": false}')
echo $RUN
RUN_ID=$(echo $RUN | python3 -c "import sys,json; print(json.load(sys.stdin)['run_id'])")

# Poll until complete
for i in $(seq 1 15); do
  STATUS=$(curl -s "$BASE/api/test-runs/$RUN_ID" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "Status: $STATUS"
  [ "$STATUS" = "complete" ] && break
  sleep 5
done

# Inspect result
curl -s "$BASE/api/test-runs/$RUN_ID" | python3 -m json.tool | head -60

# List runs
curl -s "$BASE/api/test-runs" | python3 -m json.tool

# 409 on duplicate active run (start a multi-scenario run, then immediately post again)
curl -s -X POST "$BASE/api/test-runs" \
  -H "Content-Type: application/json" \
  -d '{"run_all": true, "user_id": "user_justin", "run_label": "duplicate test"}' | python3 -m json.tool
# Expected: 409 with "run already active"
```

### Manual UI Smoke Test

| Step | Expected |
|------|----------|
| Open Observability → Bulk Testing tab | Left panel: 11 scenarios; right panel: run history (empty initially) |
| Check all Group A scenarios + Run Selected | Run starts; progress view shows 4 scenarios queued |
| Wait for run to complete | View auto-transitions to transcript; 4 scenario blocks visible |
| Read first scenario transcript | User/character turns visually distinct; `► Effect:` lines present where tools fired |
| Click `▶ Logs (N)` on a turn | Log entries expand inline; collapse returns to scroll position |
| Back to suite; start a second run with different label | Two runs in history list |
| Click first run, then "Compare with…" | Side-by-side view; scroll linking works |
| "+ New test user" → create → run under it | User has BULK TEST badge in User Testing Tool |
| Cancel a running run | "Stopping…" while current scenario finishes; "cancelled" banner in transcript |

---

## Git Commit Plan

One commit per completed milestone on the `phase8` branch:

```
Complete Milestone 1: Scenario Library & Data Model for Phase 8
Complete Milestone 2: Scenario Runner Backend for Phase 8
Complete Milestone 3: Bulk Testing UI — Suite Controls for Phase 8
Complete Milestone 4: Bulk Testing UI — Progress & Transcript View for Phase 8
Complete Milestone 5: Bulk Testing UI — Run History & Comparison for Phase 8
Complete Milestone 6: Test User Integration for Phase 8
```

Tag on phase completion:

```bash
git tag phase8-complete
git push --tags
```

---

## Status Tracker

| Milestone | Status | Completion Date |
|-----------|--------|----------------|
| 1 — Scenario Library & Data Model | Not Started | — |
| 2 — Scenario Runner Backend | Not Started | — |
| 3 — Bulk Testing UI: Suite Controls | Not Started | — |
| 4 — Bulk Testing UI: Progress & Transcript View | Not Started | — |
| 5 — Bulk Testing UI: Run History & Comparison | Not Started | — |
| 6 — Test User Integration | Not Started | — |
