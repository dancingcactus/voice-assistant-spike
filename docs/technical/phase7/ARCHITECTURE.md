# Phase 7: Enhanced Structured Logging & Observability - Architecture

**Version:** 1.0
**Last Updated:** February 22, 2026
**Status:** Draft
**Companion PRD:** [PRD.md](./PRD.md)

---

## Overview

This document describes the technical design for Phase 7. The implementation spans five areas:

1. **Correlation plumbing** — Python `ContextVar` + logging `Filter` to inject `conversation_id` / `turn_id` onto every log record without touching individual subsystems
2. **Structured log storage** — Extended `ObservabilityLogHandler` that captures structured fields alongside the message string
3. **File logging** — Optional JSON Lines sink with runtime on/off control via API
4. **API extensions** — New endpoints for group summaries, lazy-load per-turn entries, and file-logging control
5. **UI overhaul** — Collapsible turn groups, level toggle pills, structured fields sub-row, file logging control panel

---

## System Context

```
Browser (React)
  │  X-Conversation-ID header ──────────────────────────────┐
  │  WS messages / HTTP                                       │
  ▼                                                           ▼
FastAPI (main.py)                               Observability API (/api/v1)
  │                                               │  GET /logs/groups
  ▼                                               │  GET /logs?turn_id=
WebSocket handler                               │  GET /logs/file-logging
  │  sets conversation_id ContextVar            │  POST /logs/file-logging
  ▼                                               │
ConversationManager.process_message()            │
  │  generates turn_id ContextVar               │
  ▼                                               │
Pipeline: TurnClassifier → Router → Executor    │
  │  all loggers emit records                    │
  ▼                                               │
Root logger                                       │
  ├── CorrelationFilter (injects IDs)            │
  ├── ObservabilityLogHandler ────────────────────┘
  │     stores in-memory deque (1000 entries)
  └── RotatingFileHandler (optional, JSON Lines)
```

---

## Backend Architecture

### New & Modified Files

```
backend/src/
├── core/
│   └── logging_context.py          ← NEW: ContextVars + CorrelationFilter
├── observability/
│   ├── log_handler.py              ← MODIFIED: structured storage, group queries
│   ├── json_formatter.py           ← NEW: JsonFormatter for file sink
│   ├── file_log_manager.py         ← NEW: runtime file handler attach/detach
│   └── api.py                      ← MODIFIED: new endpoints
├── api/
│   └── websocket.py                ← MODIFIED: read X-Conversation-ID header
├── core/
│   ├── conversation_manager.py     ← MODIFIED: generate + set turn_id
│   └── tool_system.py              ← MODIFIED: WARNING on failures + structured fields
└── main.py                          ← MODIFIED: file log startup init
```

---

### `core/logging_context.py` (New)

Central home for all correlation plumbing. Kept in `core/` so it has no dependency on `observability/` and can be imported anywhere without circular imports.

```python
# Responsibilities:
# - Define conversation_id_var and turn_id_var ContextVars
# - CorrelationFilter: reads vars, stamps LogRecord attributes
# - set_correlation_ids(conversation_id, turn_id) helper used at entry points
# - generate_id() → uuid4 string helper

from contextvars import ContextVar
import logging, uuid

conversation_id_var: ContextVar[str] = ContextVar("conversation_id", default="")
turn_id_var:         ContextVar[str] = ContextVar("turn_id",         default="")

def generate_id() -> str:
    return str(uuid.uuid4())

def set_correlation_ids(conversation_id: str, turn_id: str):
    conversation_id_var.set(conversation_id)
    turn_id_var.set(turn_id)

class CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.conversation_id = conversation_id_var.get()
        record.turn_id         = turn_id_var.get()
        return True
```

The `CorrelationFilter` is attached to the **root logger** inside `log_handler.install()` so it runs for every handler (in-memory + file).

---

### `observability/log_handler.py` (Modified)

**Changes from current:**

| What | From → To |
|------|-----------|
| `MAX_LOG_ENTRIES` | `500` → `1000` |
| Stored record shape | `{timestamp, level, logger, message}` | + `conversation_id`, `turn_id`, `fields` |
| New method | — | `get_groups()` returns group summaries |
| New method | — | `get_logs_for_turn(turn_id)` filters by turn |
| `install()` | attaches handler | also attaches `CorrelationFilter` to root logger |

**Extended stored record shape:**
```python
{
    "timestamp":       "2026-02-22T14:01:00.123Z",  # ISO8601 UTC
    "level":           "INFO",
    "logger":          "core.character_executor",
    "message":         "Delilah executing turn",
    "conversation_id": "a1b2c3...",                  # from ContextVar
    "turn_id":         "d4e5f6...",                  # from ContextVar
    "fields":          {                              # optional structured extras
        "character":   "delilah",
        "latency_ms":  142.3
    }
}
```

**`get_groups()` logic:**
- Iterate `_records`, bucket by `turn_id` (empty turn_id → "system" bucket)
- Per group: first `start_timestamp`, first `INFO`/`WARNING`/`ERROR` message as `headline`, count per level
- Return groups sorted newest-first

**`emit()` structured field extraction:**
```python
STRUCTURED_FIELDS = {
    "character", "tool_name", "turn_type", "coordination_mode",
    "latency_ms", "model", "token_count"
}

def emit(self, record):
    fields = {
        k: getattr(record, k)
        for k in STRUCTURED_FIELDS
        if hasattr(record, k)
    }
    self._records.append({
        "timestamp":       ...,
        "level":           record.levelname,
        "logger":          record.name,
        "message":         self.format(record),
        "conversation_id": getattr(record, "conversation_id", ""),
        "turn_id":         getattr(record, "turn_id", ""),
        "fields":          fields,
    })
```

---

### `observability/json_formatter.py` (New)

Single-responsibility class; knows nothing about file paths or rotation.

```python
class JsonFormatter(logging.Formatter):
    """Formats a LogRecord as a single JSON object (no trailing newline)."""
    STRUCTURED_FIELDS = { ... }  # same set as log_handler

    def format(self, record: logging.LogRecord) -> str:
        fields = {k: getattr(record, k) for k in self.STRUCTURED_FIELDS if hasattr(record, k)}
        obj = {
            "timestamp":       datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level":           record.levelname,
            "logger":          record.name,
            "message":         record.getMessage(),
            "conversation_id": getattr(record, "conversation_id", ""),
            "turn_id":         getattr(record, "turn_id", ""),
            "fields":          fields,
        }
        return json.dumps(obj, default=str)
```

---

### `observability/file_log_manager.py` (New)

Singleton that owns the `RotatingFileHandler` lifecycle at runtime.

**Responsibilities:**
- `status() → FileLogStatus` — current enabled state, resolved path, file size
- `enable(filename: str)` — validates path, creates `logs/` dir if needed, creates/attaches handler
- `disable()` — detaches and closes handler
- Path safety: `Path("logs") / filename` must not escape `logs/` — validated with `.resolve()` comparison

**Path validation logic:**
```python
LOGS_DIR = Path(__file__).parent.parent.parent.parent / "logs"

def _safe_path(filename: str) -> Path:
    # Reject anything with path separators or traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise ValueError("filename must be a plain name, not a path")
    resolved = (LOGS_DIR / filename).resolve()
    if not str(resolved).startswith(str(LOGS_DIR.resolve())):
        raise ValueError("path escapes logs/ directory")
    return resolved
```

**Startup initialisation** (in `main.py`):
```python
from observability.file_log_manager import FileLogManager
log_file = os.getenv("LOG_FILE")
if log_file:
    FileLogManager.instance().enable(Path(log_file).name)
```

---

### `observability/api.py` (Modified)

**New and modified endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/logs` | Extended: now accepts `turn_id`, `conversation_id`, `order` params; returns extended record shape |
| `GET` | `/logs/groups` | New: lightweight group summaries for initial UI poll |
| `GET` | `/logs/file-logging` | New: current file logging state |
| `POST` | `/logs/file-logging` | New: enable/disable at runtime |

**`GET /logs` extended query params:**
```
limit          int     default 200
level          str     single level filter (existing)
turn_id        str     filter to one turn (new)
conversation_id str    filter to one session (new)
order          str     "asc" (default) | "desc"
```

**`GET /logs/groups` response:**
```json
{
  "groups": [
    {
      "turn_id":         "d4e5f6...",
      "conversation_id": "a1b2c3...",
      "start_timestamp": "2026-02-22T14:01:00.123Z",
      "headline":        "Delilah executing turn",
      "level_counts":    {"DEBUG": 4, "INFO": 2, "WARNING": 1},
      "entry_count":     7
    }
  ]
}
```

The `"system"` group (empty `turn_id`) always appears as the first item if it has entries, with `turn_id: null`.

**`GET /logs/file-logging` response:**
```json
{
  "enabled":    true,
  "path":       "logs/aperture-assist.log",
  "size_bytes": 24601
}
```

**`POST /logs/file-logging` request body:**
```json
{ "enabled": true, "filename": "aperture-assist.log" }
```
Returns the same shape as `GET`. Returns HTTP 400 with `{ "detail": "..." }` on path validation failure.

---

### `api/websocket.py` (Modified)

WebSocket connections carry the `conversation_id` in the `X-Conversation-ID` header of the HTTP upgrade request, or embedded in the first message payload as a fallback (WS headers are not universally accessible in all client environments).

**Entry-point handling:**
```python
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Read from upgrade headers first; fall back to first message field
    conversation_id = (
        websocket.headers.get("x-conversation-id")
        or generate_id()          # server fallback
    )
    conversation_id_var.set(conversation_id)
    ...
```

---

### `core/conversation_manager.py` (Modified)

`process_message()` is the single authoritative place where `turn_id` is born:

```python
async def process_message(self, user_message: str, session_id: str, ...) -> dict:
    turn_id = generate_id()
    turn_id_var.set(turn_id)
    logger.info("Turn start", extra={"turn_type": "..."})
    ...
    response = { ..., "turn_id": turn_id }  # returned to caller → WS response
    return response
```

The `turn_id` is included in the WebSocket response message so the frontend can link a chat bubble to a log group.

---

### `core/tool_system.py` (Modified)

**Error logging changed from `ERROR` to `WARNING`** for tool execution failures (tool not found, bad params, unexpected exception) per design decision 3. Structured fields added:

```python
# Before (current)
logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)

# After
logger.warning(
    f"Tool execution failed: {tool_name}",
    extra={"tool_name": tool_name, "latency_ms": elapsed_ms}
)
```

This means routine tool failures contribute to the amber border in the UI without triggering the red/error visual. `logger.error` is reserved for truly unexpected internal failures.

---

### Key Call Sites Annotated for Structured Fields (FR2.4)

| File | Logger call | Extra fields added |
|------|-------------|-------------------|
| `core/conversation_manager.py` | Turn start/end | `turn_type`, `coordination_mode` |
| `core/character_executor.py` | Character execution | `character`, `latency_ms` |
| `integrations/llm_integration.py` | LLM request | `model`, `token_count`, `latency_ms` |
| `core/tool_system.py` | Tool execution | `tool_name`, `latency_ms` |

All other call sites continue to work unchanged.

---

## Frontend Architecture

### Modified & New Files

```
frontend/src/
├── services/
│   └── api.ts                      ← MODIFIED: new types, new API methods, conversation_id header
└── components/
    ├── SystemLogTool.tsx            ← MODIFIED: complete overhaul (groups, lazy load, level pills)
    └── SystemLogTool.css           ← MODIFIED: new styles for groups, badges, file logging panel
```

---

### `services/api.ts` (Modified)

**New types:**
```typescript
export interface LogEntry {
  timestamp:       string;
  level:           string;
  logger:          string;
  message:         string;
  conversation_id: string;
  turn_id:         string;
  fields:          Record<string, unknown>;
}

export interface LogGroup {
  turn_id:         string | null;   // null = System group
  conversation_id: string;
  start_timestamp: string;
  headline:        string;
  level_counts:    Record<string, number>;
  entry_count:     number;
}

export interface FileLoggingStatus {
  enabled:    boolean;
  path:       string | null;
  size_bytes: number | null;
}
```

**`conversation_id` management:**
```typescript
function getOrCreateConversationId(): string {
  let id = sessionStorage.getItem("conversation_id");
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem("conversation_id", id);
  }
  return id;
}
```

All chat WebSocket messages and HTTP requests include the header `X-Conversation-ID: <id>`.

**New API methods:**
```typescript
getLogGroups(): Promise<{ groups: LogGroup[] }>
getLogsForTurn(turnId: string, limit?: number): Promise<{ logs: LogEntry[] }>
getFileLoggingStatus(): Promise<FileLoggingStatus>
setFileLogging(enabled: boolean, filename: string): Promise<FileLoggingStatus>
```

---

### `SystemLogTool.tsx` (Modified — Full Overhaul)

**Component structure:**

```
SystemLogTool
├── Toolbar
│   ├── LevelTogglePills          ← replaces level dropdown
│   ├── AutoScrollToggle
│   └── FileLoggingPanel          ← new
│       ├── toggle switch
│       ├── filename input
│       ├── resolved path display
│       └── file size / status indicator
└── TurnGroupList
    ├── SystemGroup               ← always first; collapsed by default
    │   └── [LogEntry…]
    └── TurnGroup (×N)            ← one per turn_id
        ├── GroupHeader
        │   ├── chevron
        │   ├── headline text
        │   ├── timestamp
        │   └── LevelCountBadges
        └── [LogEntry…] (lazy loaded on expand)
            └── FieldsSubRow (collapsed by default)
```

**State shape:**
```typescript
interface TurnGroupState {
  group:    LogGroup;
  expanded: boolean;
  loading:  boolean;
  entries:  LogEntry[] | null;  // null = not yet fetched
}
```

**Polling strategy:**
- `useQuery` polls `GET /logs/groups` every 3 seconds (same current interval)
- New groups are prepended; existing groups are updated in-place (level counts may grow)
- Most recent group auto-expands on first appearance (triggers eager lazy-fetch)
- Expanding manually calls `GET /logs?turn_id=<id>` and stores result in `entries`; subsequent expands use cached data

**Level toggle pills:**

```
[DEBUG] [INFO] [WARNING] [ERROR] [CRITICAL]  (all active by default)
```

Clicking a pill toggles it on/off. Filtering is client-side only — all entries are loaded; pills hide/show rows. This avoids extra round-trips.

**Level badge colours** (from PRD FR6.1) applied via CSS classes: `level-debug`, `level-info`, `level-warning`, `level-error`, `level-critical`.

**Group header severity border:**
- `border-left: 3px solid #ef4444` when `level_counts.ERROR > 0 || level_counts.CRITICAL > 0`
- `border-left: 3px solid #f59e0b` when `level_counts.WARNING > 0` (and no errors)
- No border otherwise

**Relative time display:**
```typescript
function relativeMs(entryTimestamp: string, groupStart: string): string {
  const delta = new Date(entryTimestamp).getTime() - new Date(groupStart).getTime();
  return delta < 1000 ? `+${delta}ms` : `+${(delta/1000).toFixed(1)}s`;
}
```

**FileLoggingPanel:**
- `useQuery` fetches `GET /logs/file-logging` on mount
- `useMutation` calls `POST /logs/file-logging` on toggle
- Filename input validates `/[\/\\.]./` client-side; shows error inline without calling API
- Field is `disabled` while logging is enabled
- File size updates every 3 s via the same polling query

---

## Data Flow: Single Chat Turn

```
1. User sends message from browser
   │  sessionStorage → conversation_id = "AAA"
   │  WebSocket message carries header X-Conversation-ID: AAA
   ▼
2. websocket.py receives message
   │  conversation_id_var.set("AAA")
   ▼
3. ConversationManager.process_message()
   │  turn_id = uuid4() = "BBB"
   │  turn_id_var.set("BBB")
   │  logger.info("Turn start", extra={"turn_type": "single"})
   │    → LogRecord stamped conversation_id="AAA", turn_id="BBB"
   ▼
4. TurnClassifier, ConversationRouter, CharacterExecutor all emit logs
   │  Every record gets conversation_id="AAA", turn_id="BBB" from CorrelationFilter
   ▼
5. ToolSystem.execute_tool("set_timer", ...)
   │  logger.info("Tool executed", extra={"tool_name": "set_timer", "latency_ms": 12.4})
   │    → record stored with fields={"tool_name": "set_timer", "latency_ms": 12.4}
   ▼
6. LLMIntegration logs response
   │  extra={"model": "gpt-4o", "token_count": 312, "latency_ms": 840}
   ▼
7. ConversationManager returns response
   │  { "text": "...", "turn_id": "BBB", ... }
   ▼
8. ObservabilityLogHandler has ~12 records all tagged turn_id="BBB"
   ▼
9. UI polls GET /logs/groups
   │  Sees new group: turn_id="BBB", headline="Turn start", level_counts={DEBUG:6, INFO:4}
   │  Most-recent group → auto-expands → fetches GET /logs?turn_id=BBB
   ▼
10. Developer sees full correlated trail without touching the terminal
```

---

## Migration Notes

### Breaking Changes
None. The `/logs` endpoint schema is additive — new fields appear alongside existing ones. The frontend `SystemLogTool` is a full replacement but no external consumers depend on it.

### Backwards Compatibility for Existing Log Callers
All existing `logger.info("message")` calls continue to work. The `CorrelationFilter` adds `conversation_id`/`turn_id`, but if called outside a request context both default to `""` (empty string), which routes them to the System group in the UI.

### `logs/` Directory
Created at application startup by `FileLogManager` if file logging is enabled. The directory is at the project root (`/logs/`). It should be added to `.gitignore`.

---

## Dependencies

No new Python packages required. All components use stdlib:
- `contextvars` — Python 3.7+
- `logging`, `logging.handlers.RotatingFileHandler` — stdlib
- `json`, `uuid`, `pathlib` — stdlib

No new frontend packages required:
- `crypto.randomUUID()` — available in all modern browsers
- `@tanstack/react-query` — already used

