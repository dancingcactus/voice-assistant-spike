# Phase 7: Enhanced Structured Logging & Observability - Implementation Plan

**Version:** 1.0
**Last Updated:** February 22, 2026
**Status:** Not Started

---

## References

- **PRD:** [PRD.md](PRD.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Existing log handler:** `backend/src/observability/log_handler.py`
- **Existing observability API:** `backend/src/observability/api.py`
- **Entry point:** `backend/src/main.py`
- **WebSocket handler:** `backend/src/api/websocket.py`
- **Conversation entry point:** `backend/src/core/conversation_manager.py`
- **Tool dispatch:** `backend/src/core/tool_system.py`
- **Frontend log component:** `frontend/src/components/SystemLogTool.tsx`
- **Frontend API client:** `frontend/src/services/api.ts`

---

## Overview

### Goals

Introduce correlated, structured logging so every log record emitted during a chat turn carries `conversation_id` and `turn_id`. Expose this structure through a new Observability UI that groups logs by turn in collapsible rows, with level visualisation, lazy loading, and a file-logging toggle. No existing functionality is broken.

### Timeline Estimate

- **Total Duration:** 1–2 weeks
- **Milestone Count:** 5 milestones

### Success Criteria

- Every log record emitted inside `process_message()` carries a non-empty `turn_id`
- UI shows one collapsible row per chat turn with level count badges
- Expanding a row loads the full structured log for that turn without a page-level re-fetch
- File logging can be toggled on/off from the UI; output is valid JSON Lines
- All existing backend tests pass unchanged after each milestone
- All new tests pass

---

## Milestone 1: Correlation IDs

**Status:** Not Started
**Goal:** Plumb `conversation_id` and `turn_id` through `ContextVar`s so every log record emitted during a turn is automatically stamped with both IDs. Return `turn_id` in the chat API response.

### Files Changed

#### `backend/src/core/logging_context.py` (new file)

```python
from contextvars import ContextVar
import uuid, logging

conversation_id_var: ContextVar[str] = ContextVar("conversation_id", default="")
turn_id_var:         ContextVar[str] = ContextVar("turn_id",         default="")

def generate_id() -> str:
    return str(uuid.uuid4())

def set_correlation_ids(conversation_id: str, turn_id: str) -> None:
    conversation_id_var.set(conversation_id)
    turn_id_var.set(turn_id)

class CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.conversation_id = conversation_id_var.get()
        record.turn_id         = turn_id_var.get()
        return True
```

#### `backend/src/observability/log_handler.py`

- `MAX_LOG_ENTRIES` → `1000`
- `install()`: after attaching the handler, also attach `CorrelationFilter` to `logging.getLogger()`
- `emit()`: read `record.conversation_id` and `record.turn_id` (default `""`) and store them on the record dict alongside existing fields

Record dict after this milestone:
```python
{
    "timestamp":       "...",
    "level":           "INFO",
    "logger":          "core.conversation_manager",
    "message":         "Turn start",
    "conversation_id": "aaa",
    "turn_id":         "bbb",
    "fields":          {},          # populated in Milestone 2
}
```

#### `backend/src/api/websocket.py`

In `websocket_endpoint()`, after `await websocket.accept()`:
```python
from core.logging_context import conversation_id_var, generate_id
conversation_id = websocket.headers.get("x-conversation-id") or generate_id()
conversation_id_var.set(conversation_id)
```

#### `backend/src/core/conversation_manager.py`

At the top of `process_message()` (or equivalent entry method):
```python
from core.logging_context import generate_id, set_correlation_ids, turn_id_var
turn_id = generate_id()
# conversation_id already set by websocket handler; read it here if needed
set_correlation_ids(conversation_id_var.get(), turn_id)
logger.info("Turn start")
```

Include `turn_id` in the returned response dict:
```python
return { ..., "turn_id": turn_id }
```

### Verification

```bash
cd backend && source venv/bin/activate
python -c "
import sys; sys.path.insert(0, 'src')
from core.logging_context import (
    conversation_id_var, turn_id_var, set_correlation_ids, generate_id, CorrelationFilter
)
import logging

# Attach filter to root logger
logging.getLogger().addFilter(CorrelationFilter())

cid = generate_id()
tid = generate_id()
set_correlation_ids(cid, tid)

record = logging.LogRecord('test', logging.INFO, '', 0, 'hello', (), None)
logging.getLogger().callHandlers(record)
assert record.conversation_id == cid
assert record.turn_id == tid
print('CorrelationFilter OK')
"
```

### Test File: `backend/tests/test_phase7_milestone1.py`

Scope:
- `CorrelationFilter` stamps correct IDs onto a `LogRecord`
- Unset context → IDs default to `""`, not `None`
- Two concurrent async tasks with different IDs do not bleed into each other (async isolation)
- `ObservabilityLogHandler.emit()` stores `conversation_id` and `turn_id` in the record dict
- `get_logs()` returns records with `conversation_id` and `turn_id` fields present
- Ring-buffer capped at 1000 (not 500)

### Regression Guard

```bash
cd backend && source venv/bin/activate
pytest tests/ -v --tb=short
```

All existing tests must pass before this milestone is committed.

---

## Milestone 2: Structured Logging

**Status:** Not Started
**Goal:** Extend the log handler to capture optional structured fields (`character`, `tool_name`, `latency_ms`, etc.) as a `fields` dict. Annotate the four key call sites. Update the `/logs` API response shape.

### Files Changed

#### `backend/src/observability/log_handler.py`

Define the supported field names (shared constant):
```python
STRUCTURED_FIELDS = frozenset({
    "character", "tool_name", "turn_type", "coordination_mode",
    "latency_ms", "model", "token_count",
})
```

Update `emit()` to extract them:
```python
fields = {k: getattr(record, k) for k in STRUCTURED_FIELDS if hasattr(record, k)}
self._records.append({ ..., "fields": fields })
```

#### `backend/src/observability/api.py` — `GET /logs`

Extend query params: `turn_id: Optional[str] = None`, `conversation_id: Optional[str] = None`, `order: str = "asc"`.

The response shape already includes `conversation_id`, `turn_id`, `fields` from the updated handler — no schema versioning needed as the additions are additive.

Filter logic (in `get_logs()`):
```python
if turn_id:
    entries = [e for e in entries if e.get("turn_id") == turn_id]
if conversation_id:
    entries = [e for e in entries if e.get("conversation_id") == conversation_id]
if order == "desc":
    entries = list(reversed(entries))
```

#### `backend/src/core/conversation_manager.py`

Add `extra={}` to the turn-start and turn-end log calls:
```python
logger.info("Turn start", extra={"turn_type": turn_type_str, "coordination_mode": mode_str})
logger.info("Turn complete", extra={"latency_ms": elapsed_ms})
```

#### `backend/src/core/character_executor.py`

Add `extra={}` to character execution log:
```python
logger.info("Executing character", extra={"character": character_id, "latency_ms": elapsed_ms})
```

#### `backend/src/integrations/llm_integration.py`

Add `extra={}` to LLM call log:
```python
logger.info("LLM response received", extra={"model": model_name, "token_count": tokens, "latency_ms": elapsed_ms})
```

#### `backend/src/core/tool_system.py`

Change tool failure logging from `logger.error` → `logger.warning` (per design decision 3) and add structured fields:
```python
# For all three failure branches (not found / bad params / unexpected exception):
logger.warning(
    f"Tool execution failed: {tool_name} — {error_summary}",
    extra={"tool_name": tool_name, "latency_ms": elapsed_ms},
)
```

Successful execution also logs with fields:
```python
logger.info("Tool executed", extra={"tool_name": tool_name, "latency_ms": elapsed_ms})
```

### Verification

```bash
cd backend && source venv/bin/activate
python -c "
import sys; sys.path.insert(0, 'src')
import logging
from observability.log_handler import get_handler, install

install()
handler = get_handler()
handler.clear()

logging.getLogger('test').info('hello', extra={'character': 'delilah', 'latency_ms': 42.1})
logs = handler.get_logs()
assert logs[-1]['fields']['character'] == 'delilah'
assert logs[-1]['fields']['latency_ms'] == 42.1
print('Structured fields OK')
"
```

### Test File: `backend/tests/test_phase7_milestone2.py`

Scope:
- `emit()` correctly extracts each supported structured field when present
- `emit()` stores empty `fields: {}` when no structured fields are on the record
- Unknown extra fields are **not** included in `fields` (no leakage)
- `GET /logs?turn_id=X` returns only records with that `turn_id`
- `GET /logs?conversation_id=X` returns only records for that session
- `GET /logs?order=desc` returns newest first
- `GET /logs?order=asc` (default) returns oldest first
- Tool failure logs are at WARNING level (not ERROR) — verify `level` field in stored record
- Tool success logs carry `tool_name` in `fields`
- LLM call logs carry `model` and `token_count` in `fields` when provided

### Regression Guard

```bash
cd backend && source venv/bin/activate
pytest tests/ -v --tb=short
```

---

## Milestone 3: File Logging

**Status:** Not Started
**Goal:** Add a `JsonFormatter`, a `FileLogManager` singleton for runtime attach/detach, two new API endpoints (`GET`/`POST /logs/file-logging`), and a UI control panel in the Logs tab toolbar.

### Files Changed

#### `backend/src/observability/json_formatter.py` (new file)

```python
import json, logging
from datetime import datetime, timezone
from .log_handler import STRUCTURED_FIELDS

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        fields = {k: getattr(record, k) for k in STRUCTURED_FIELDS if hasattr(record, k)}
        return json.dumps({
            "timestamp":       datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level":           record.levelname,
            "logger":          record.name,
            "message":         record.getMessage(),
            "conversation_id": getattr(record, "conversation_id", ""),
            "turn_id":         getattr(record, "turn_id", ""),
            "fields":          fields,
        }, default=str)
```

#### `backend/src/observability/file_log_manager.py` (new file)

Singleton with `enable(filename)`, `disable()`, `status()` methods.

Path safety:
```python
from pathlib import Path
LOGS_DIR = (Path(__file__).parent.parent.parent.parent / "logs").resolve()

def _safe_path(filename: str) -> Path:
    if "/" in filename or "\\" in filename or ".." in filename:
        raise ValueError("filename must be a plain name, not a path")
    resolved = (LOGS_DIR / filename).resolve()
    if not str(resolved).startswith(str(LOGS_DIR)):
        raise ValueError("path escapes logs/ directory")
    return resolved
```

`enable(filename)`:
1. Call `_safe_path(filename)` — raises `ValueError` on invalid input
2. Create `LOGS_DIR` if it doesn't exist
3. Create `RotatingFileHandler(path, maxBytes=10*1024*1024, backupCount=5)`
4. Attach `JsonFormatter` and `CorrelationFilter`
5. Add to `logging.getLogger()`
6. Store handler reference and path on the singleton

`disable()`:
1. Remove handler from root logger
2. Close handler
3. Clear stored reference

`status()` → `{"enabled": bool, "path": str|None, "size_bytes": int|None}`

#### `backend/src/main.py`

On startup, after installing observability handler:
```python
from observability.file_log_manager import FileLogManager
import os
log_file = os.getenv("LOG_FILE")
if log_file:
    from pathlib import Path
    FileLogManager.instance().enable(Path(log_file).name)
    print(f"✅ File logging enabled: logs/{Path(log_file).name}")
```

#### `backend/src/observability/api.py` — two new endpoints

```python
@app.get("/logs/file-logging")
async def get_file_logging_status(authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    from .file_log_manager import FileLogManager
    return FileLogManager.instance().status()

@app.post("/logs/file-logging")
async def set_file_logging(
    body: FileLoggingRequest,
    authorization: Optional[str] = Header(None)
):
    verify_token(authorization)
    from .file_log_manager import FileLogManager, ValueError as FLMValueError
    mgr = FileLogManager.instance()
    try:
        if body.enabled:
            filename = body.filename or os.getenv("LOG_FILE", "aperture-assist.log")
            filename = Path(filename).name  # strip any accidental path components
            mgr.enable(filename)
        else:
            mgr.disable()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return mgr.status()
```

`FileLoggingRequest` Pydantic model:
```python
class FileLoggingRequest(BaseModel):
    enabled: bool
    filename: Optional[str] = None
```

#### `frontend/src/services/api.ts`

New types and methods:
```typescript
export interface FileLoggingStatus {
  enabled:    boolean;
  path:       string | null;
  size_bytes: number | null;
}

getFileLoggingStatus(): Promise<FileLoggingStatus>
setFileLogging(enabled: boolean, filename: string): Promise<FileLoggingStatus>
```

#### `frontend/src/components/SystemLogTool.tsx` — FileLoggingPanel section

New section added to the existing toolbar (alongside the level filter):
- `useQuery` fetches `GET /logs/file-logging` on mount, refetches every 5 s
- Toggle switch, filename text input (pre-filled from status), resolved `logs/<filename>` path display, file size
- `useMutation` calls `POST /logs/file-logging`; displays inline success/error
- Filename input `disabled` while enabled; validates no `/`, `\`, or `..` client-side

### Verification

```bash
# Start backend, then:
curl -s -H "Authorization: Bearer dev_token_12345" \
  http://localhost:8000/api/v1/logs/file-logging | jq .

# Enable file logging
curl -s -X POST -H "Authorization: Bearer dev_token_12345" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "filename": "test.log"}' \
  http://localhost:8000/api/v1/logs/file-logging | jq .

# Send a chat message, then inspect the file
tail -5 logs/test.log | jq .

# Verify JSON Lines validity
jq -c '.' logs/test.log | head -5
```

### Test File: `backend/tests/test_phase7_milestone3.py`

Scope:
- `JsonFormatter.format()` produces a valid JSON string with all required keys
- `JsonFormatter` correctly includes structured fields when present; omits them when absent
- `FileLogManager.enable()` creates file under `logs/`, attaches handler to root logger
- `FileLogManager.disable()` removes handler and closes file handle
- `FileLogManager.enable()` is idempotent (double-enable doesn't create two handlers)
- `_safe_path()` raises `ValueError` for `"../secret.log"`, `"/tmp/bad.log"`, `"sub/dir.log"`
- `_safe_path()` accepts `"aperture-assist.log"`, `"my-debug.log"`
- `GET /logs/file-logging` returns `{"enabled": false, "path": null, "size_bytes": null}` when disabled
- `POST /logs/file-logging {"enabled": true, "filename": "test.log"}` enables logging and returns updated status
- `POST /logs/file-logging {"enabled": false}` disables logging
- `POST /logs/file-logging {"enabled": true, "filename": "../escape.log"}` returns HTTP 400
- After enabling, a log record written by the root logger appears in the JSON Lines file

### Regression Guard

```bash
cd backend && source venv/bin/activate
pytest tests/ -v --tb=short
```

---

## Milestone 4: UI — Collapsible Turn Groups

**Status:** Not Started
**Goal:** Replace the flat log list in `SystemLogTool` with a grouped view. Initial poll fetches lightweight summaries; expanding a group lazy-fetches its entries.

### Files Changed

#### `backend/src/observability/log_handler.py` — `get_groups()` (new method)

```python
def get_groups(self) -> list[dict]:
    """
    Return one summary dict per turn_id (empty turn_id → system group).
    Groups are sorted newest-first by start_timestamp.
    """
    buckets: dict[str, dict] = {}
    for entry in self._records:
        key = entry.get("turn_id") or ""
        if key not in buckets:
            buckets[key] = {
                "turn_id":         entry.get("turn_id") or None,
                "conversation_id": entry.get("conversation_id", ""),
                "start_timestamp": entry["timestamp"],
                "headline":        None,
                "level_counts":    {},
                "entry_count":     0,
            }
        b = buckets[key]
        b["entry_count"] += 1
        lvl = entry["level"]
        b["level_counts"][lvl] = b["level_counts"].get(lvl, 0) + 1
        if b["headline"] is None and lvl in ("INFO", "WARNING", "ERROR", "CRITICAL"):
            b["headline"] = entry["message"]
    groups = sorted(buckets.values(), key=lambda g: g["start_timestamp"], reverse=True)
    # Ensure System group (turn_id=None) is always first
    system = [g for g in groups if g["turn_id"] is None]
    turns  = [g for g in groups if g["turn_id"] is not None]
    return system + turns
```

#### `backend/src/observability/api.py` — `GET /logs/groups`

```python
@app.get("/logs/groups")
async def get_log_groups(authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    from .log_handler import get_handler
    return {"groups": get_handler().get_groups()}
```

#### `frontend/src/services/api.ts`

New types:
```typescript
export interface LogGroup {
  turn_id:         string | null;
  conversation_id: string;
  start_timestamp: string;
  headline:        string | null;
  level_counts:    Record<string, number>;
  entry_count:     number;
}
```

New methods:
```typescript
getLogGroups(): Promise<{ groups: LogGroup[] }>
getLogsForTurn(turnId: string, limit?: number): Promise<{ logs: LogEntry[] }>
```

#### `frontend/src/components/SystemLogTool.tsx` — full overhaul

State:
```typescript
interface TurnGroupState {
  group:    LogGroup;
  expanded: boolean;
  loading:  boolean;
  entries:  LogEntry[] | null;  // null = not yet fetched
}
const [groupStates, setGroupStates] = useState<TurnGroupState[]>([]);
```

Poll: `useQuery(['logGroups'], apiClient.getLogGroups, { refetchInterval: 3000 })` — when new groups arrive merge them into `groupStates` (update existing, prepend unknown, preserve expanded/entries cache).

Auto-expand: when the most-recent non-system group first appears, automatically expand it and trigger its lazy fetch.

Expand handler:
```typescript
function handleExpand(turnId: string) {
  setGroupStates(prev => prev.map(s => {
    if (s.group.turn_id !== turnId) return s;
    if (s.entries !== null) return { ...s, expanded: !s.expanded };
    // Trigger fetch
    fetchTurnEntries(turnId);
    return { ...s, expanded: true, loading: true };
  }));
}
```

Group header renders:
- Severity left border (red/amber/none based on `level_counts`)
- Chevron (▶ collapsed / ▼ expanded)
- Headline text or "System" label for null turn_id
- Relative timestamp
- Level count pills: `3 DEBUG · 2 INFO · 1 WARN` (hidden if count is 0)

Entry list (when expanded):
- Loading skeleton (3 placeholder rows) while `loading: true`
- Entries in chronological order once loaded
- Relative time from group start (`+42ms`)

#### `frontend/src/components/SystemLogTool.css`

New classes: `.log-group`, `.log-group--error`, `.log-group--warning`, `.log-group__header`, `.log-group__chevron`, `.log-group__headline`, `.log-group__level-counts`, `.log-group__entries`, `.log-entry__relative-time`, `.log-skeleton`.

### Verification

1. Start servers (`./scripts/servers.sh start`)
2. Open `http://localhost:5173/observability` → Logs tab
3. Send a chat message
4. Verify a new turn group row appears within 3 s
5. Verify the group shows a non-empty headline and level count (e.g. `4 DEBUG · 2 INFO`)
6. Click the row — verify it expands and entries load
7. Collapse and re-expand — verify no spinner (cached)
8. System group appears at top

### Test File: `backend/tests/test_phase7_milestone4.py`

Scope:
- `get_groups()` returns one group per distinct `turn_id`
- Records with empty `turn_id` aggregate into the system group (`turn_id: None`)
- `level_counts` correctly tallies per level per group
- `headline` is the first INFO-or-above message, not a DEBUG message
- `start_timestamp` is the timestamp of the first record in the group
- Groups are sorted newest-first; system group always first
- `GET /logs/groups` API endpoint returns correct shape and auth-gated (401 without token)
- `GET /logs?turn_id=X` returns only entries for that turn (regression on Milestone 2 filter)
- Adding records for a second turn creates a second group (does not pollute first)
- Empty handler → `get_groups()` returns `[]`

### Regression Guard

```bash
cd backend && source venv/bin/activate
pytest tests/ -v --tb=short
```

---

## Milestone 5: UI — Level Visualisation & Structured Fields

**Status:** Not Started
**Goal:** Replace the level filter dropdown with multi-select pill toggles. Add colour-coded level badges. Render expandable structured fields sub-rows. Add amber/red severity borders to group headers.

### Files Changed

#### `frontend/src/components/SystemLogTool.tsx`

**Level toggle pills** — replace `<select>` with:
```typescript
const ALL_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];
const [activeLevels, setActiveLevels] = useState<Set<string>>(new Set(ALL_LEVELS));

function toggleLevel(level: string) {
  setActiveLevels(prev => {
    const next = new Set(prev);
    next.has(level) ? next.delete(level) : next.add(level);
    return next;
  });
}
```

Filtering is client-side: entries whose `level` is not in `activeLevels` are hidden (not re-fetched).

**Level badge CSS classes:** `level-debug`, `level-info`, `level-warning`, `level-error`, `level-critical`.

**Structured fields sub-row:** For each log entry, if `fields` is non-empty render a collapsed `<details>` element below the message row:
```tsx
{Object.keys(entry.fields).length > 0 && (
  <details className="log-entry__fields">
    <summary>Fields</summary>
    <pre>{JSON.stringify(entry.fields, null, 2)}</pre>
  </details>
)}
```

**Severity left border** (already partially in Milestone 4 CSS, finalised here):
```css
.log-group--error   { border-left: 3px solid #ef4444; }
.log-group--warning { border-left: 3px solid #f59e0b; }
```

Determination:
```typescript
function groupSeverityClass(g: LogGroup): string {
  const c = g.level_counts;
  if ((c['ERROR'] ?? 0) + (c['CRITICAL'] ?? 0) > 0) return 'log-group--error';
  if ((c['WARNING'] ?? 0) > 0) return 'log-group--warning';
  return '';
}
```

#### `frontend/src/components/SystemLogTool.css`

New rules for all five level badge colours, pill toggle active/inactive states, fields `<details>` block, severity border classes.

### Verification

1. Open Observability → Logs tab
2. Send a chat message that exercises a tool (e.g. "set a timer")
3. Expand the turn group → verify log entries show coloured level badges
4. Verify an entry with `fields` (e.g. from `tool_system`) shows a "Fields" expandable sub-row
5. Click "DEBUG" pill to deactivate → DEBUG entries disappear; click again → they return
6. Toggle only WARNING+ERROR → only those levels visible
7. Trigger a tool failure (e.g. invalid tool call) → verify group header gets amber border without expanding
8. Check file logging panel is still present and functional

### Test File: `backend/tests/test_phase7_milestone5.py`

This milestone is primarily frontend; the backend test file covers the `/logs` filter regression and ensures tool-failure WARNING level is correct end-to-end:

Scope:
- `GET /logs` with no filters returns records including `fields` dict on every entry
- `GET /logs?turn_id=X&order=desc` returns entries for that turn, newest-first
- A simulated tool failure (via mocked `ToolSystem.execute_tool()`) produces a WARNING-level record with `tool_name` in `fields`
- A simulated tool success produces an INFO-level record with `tool_name` in `fields`
- Structured field `latency_ms` is a float, not a string
- `GET /logs/groups` level_counts correctly includes WARNING when tool failures are present

### Regression Guard — Full Suite

```bash
cd backend && source venv/bin/activate
pytest tests/ -v --tb=short
```

Run against all milestone test files in sequence to confirm no cross-milestone regressions:
```bash
pytest tests/test_phase7_milestone1.py \
       tests/test_phase7_milestone2.py \
       tests/test_phase7_milestone3.py \
       tests/test_phase7_milestone4.py \
       tests/test_phase7_milestone5.py \
       -v --tb=short
```

---

## Full Regression Test Plan

Run after all milestones are complete to confirm zero regressions against existing phases.

### Backend

```bash
cd backend && source venv/bin/activate

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
       -v --tb=short

# Phase 7 suite
pytest tests/test_phase7_milestone1.py \
       tests/test_phase7_milestone2.py \
       tests/test_phase7_milestone3.py \
       tests/test_phase7_milestone4.py \
       tests/test_phase7_milestone5.py \
       -v --tb=short
```

### Manual Observability API Smoke Test

```bash
TOKEN="dev_token_12345"
BASE="http://localhost:8000/api/v1"

# Existing endpoint — must still return timestamp/level/logger/message
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/logs?limit=5" | jq '.logs[0] | keys'
# Expected: ["conversation_id","fields","level","logger","message","timestamp","turn_id"]

# New endpoints
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/logs/groups" | jq '.groups | length'
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/logs/file-logging" | jq .

# Auth check
curl -s "$BASE/logs" | jq '.detail'
# Expected: "Not authenticated" or similar 401 message
```

### Manual UI Smoke Test

| Step | Expected |
|------|----------|
| Open Observability → Logs tab | Turn group list visible; System group at top |
| Send "set a timer for 5 minutes" | New turn group appears within 3 s |
| Expand turn group | Entries load; relative timestamps visible |
| Collapse and re-expand | No loading spinner (cached) |
| Trigger a tool error | Amber left border on that group header |
| Click DEBUG pill off | DEBUG entries hidden; counts reflect filter |
| Click DEBUG pill back on | All entries return |
| Enable file logging from UI | Toggle turns on; path shown; size starts incrementing |
| Send a message | File grows; `tail -1 logs/aperture-assist.log \| jq .` returns valid JSON |
| Disable file logging from UI | Toggle off; file stays but stops growing |
| Try filename `../escape.log` | Inline error shown; toggle does not activate |

---

## Git Commit Plan

One commit per completed milestone on a `phase7` branch:

```
Complete Milestone 1: Correlation IDs for Phase 7
Complete Milestone 2: Structured Logging for Phase 7
Complete Milestone 3: File Logging for Phase 7
Complete Milestone 4: UI Collapsible Turn Groups for Phase 7
Complete Milestone 5: UI Level Visualisation & Structured Fields for Phase 7
```

Tag on phase completion:
```bash
git tag phase7-complete
git push --tags
```

---

## Status Tracker

| Milestone | Status | Completion Date |
|-----------|--------|----------------|
| 1 – Correlation IDs | Not Started | — |
| 2 – Structured Logging | Not Started | — |
| 3 – File Logging | Not Started | — |
| 4 – UI: Collapsible Turn Groups | Not Started | — |
| 5 – UI: Level Visualisation & Structured Fields | Not Started | — |
