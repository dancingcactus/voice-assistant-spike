# Phase 7: Enhanced Structured Logging & Observability - PRD

**Version:** 1.0
**Last Updated:** February 22, 2026
**Product Owner:** Justin
**Status:** Draft — Awaiting Review
**Phase Position:** Follows Phase 5.1 (Specialist Handoff)

---

## Executive Summary

Phase 7 introduces **structured, correlated logging** across the backend and a significantly improved Observability UI that exposes that structure to the developer. Every message into the system will carry a `conversation_id` and a `turn_id` that tie together every log line, LLM call, tool invocation, and TTS event that occurred for that chat turn. The Observability UI will present logs grouped by turn in a collapsible tree, with full visibility into DEBUG/INFO/WARNING entries and the rich extra fields added by structured logging. An optional file sink makes it easy to capture log history for offline analysis.

**Success Metric:** A developer can open the Observability UI, see a recent chat turn, expand it, and in one view read the full structured log trail from intent classification through character response — with zero terminal scraping required.

---

## Product Vision

### Core Principle

Right now the logs panel is a flat, time-ordered stream of strings. When something goes wrong mid-turn it is difficult to isolate which log lines belong to which user message. Structured, correlated logging eliminates that friction: every record carries enough context to be filtered, grouped, and understood in isolation.

### User Experience Goals (Developer)

1. **Correlation at a Glance:** Open the Logs tab, see one expandable row per chat turn, immediately drill into the exact records for a problematic message without re-running anything.
2. **Rich Context Without Noise:** Structured fields (character, tool name, turn type, latency) appear on demand inside a log entry, not cluttering the headline row.
3. **Full Spectrum Visibility:** DEBUG, INFO, and WARNING entries are all visible and visually distinct without hiding behind a level filter wall.
4. **Zero-Friction Capture:** Turn on file logging with a single env-var; receive well-formed JSON log lines that pipe into any log-analysis tool.

---

## Problem Statement

### Current Limitations

1. **No correlation** — There is no shared ID linking the `TurnClassifier`, `ConversationRouter`, `CharacterExecutor`, tool calls, and TTS into a single trace. A crash mid-turn requires reading the entire flat log to reconstruct what happened.
2. **Flat strings only** — The in-memory handler stores `"message"` as the formatted string from `%(name)s - %(message)s`. Extra fields (character, latency, tool name) live only in the string itself or are lost entirely.
3. **All-or-nothing level display** — The UI offers a level filter dropdown but provides no visual priority hierarchy. DEBUG and WARNING look identical until you squint at the badge.
4. **No collapsing** — A message that triggers 2 LLM calls and 3 tool calls generates 40+ log lines. There is no way to collapse them to a summary row.
5. **No file output** — If the in-memory buffer (500 entries) rolls over, earlier context is lost. There is no persistent log for retrospective debugging.

---

## Functional Requirements

### FR1: Conversation & Turn Correlation IDs

**FR1.1** — The `conversation_id` is read from the incoming `X-Conversation-ID` request header, sent by the client on every chat request. If the header is absent the server generates a UUID4 as a fallback, ensuring no turn ever has a missing ID. The client stores its `conversation_id` in `sessionStorage` so it persists across page-level refreshes within the same tab but resets on a new session.

**FR1.2** — A `turn_id` (UUID4, unique per user message) is generated at the entry point of `ConversationManager.process_message()` before any downstream call.

**FR1.3** — Both IDs are stored in a Python `contextvars.ContextVar` so they are automatically available in any downstream code on the same async task without explicit passing.

**FR1.4** — A stdlib logging `Filter` subclass (`CorrelationFilter`) reads the context vars and injects `conversation_id` and `turn_id` as attributes onto every `LogRecord` emitted during that turn.

**FR1.5** — All existing key subsystems (TurnClassifier, ConversationRouter, CharacterExecutor, ToolSystem, LLMIntegration, TTSIntegration) benefit automatically because they use `logging.getLogger(__name__)` — no changes required in each subsystem.

**FR1.6** — The `turn_id` is included in the API response JSON so the frontend can correlate a displayed message with its log group.

### FR2: Structured Logging

**FR2.1** — An `ExtraFieldFilter` logging filter inspects `LogRecord.args` or the `extra={}` dict passed at the call site and promotes named fields to top-level attributes on the record.

**FR2.2** — Supported structured fields (all optional at each log call site):

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | str | Injected by CorrelationFilter |
| `turn_id` | str | Injected by CorrelationFilter |
| `character` | str | Which character is executing |
| `tool_name` | str | Tool being invoked |
| `turn_type` | str | TurnType enum value |
| `coordination_mode` | str | CoordinationMode enum value |
| `latency_ms` | float | Duration of an operation in ms |
| `model` | str | LLM model name used |
| `token_count` | int | Tokens consumed in LLM call |

**FR2.3** — The `ObservabilityLogHandler.emit()` method stores structured fields as a separate `fields` dict in the record dict, keeping `message` as the human-readable string.

**FR2.4** — Existing log call sites are **not** required to be updated immediately — structured fields are opt-in extras. Key integration points (LLMIntegration, CharacterExecutor) will add `extra={}` as part of this phase so the feature is demonstrated in practice.

### FR3: File Logging

**FR3.1** — If the environment variable `LOG_FILE` is set to a file path, a `logging.handlers.RotatingFileHandler` is attached to the root logger at application startup.

**FR3.2** — File output is **JSON Lines format** (one JSON object per line) using a custom `JsonFormatter`, making it directly consumable by `jq`, Splunk, Datadog, and similar tools.

**FR3.3** — Each JSON log line includes: `timestamp`, `level`, `logger`, `message`, `conversation_id`, `turn_id`, and any extra `fields` dict.

**FR3.4** — File rotation: 10 MB max per file, keep 5 backups, configurable via `LOG_FILE_MAX_BYTES` and `LOG_FILE_BACKUP_COUNT` env vars.

**FR3.5** — File logging is entirely optional; omitting `LOG_FILE` has zero impact on system behaviour.

**FR3.6** — A `POST /logs/file-logging` endpoint accepts `{ "enabled": bool, "filename": "<optional filename>" }` and dynamically attaches or detaches the `RotatingFileHandler` at runtime without requiring a server restart. The `filename` value must be a plain filename (no path separators); the server always resolves it relative to the `logs/` directory. If `filename` is omitted the server falls back to the `LOG_FILE` env var basename, then to `aperture-assist.log`. Any attempt to write outside `logs/` is rejected with HTTP 400.

**FR3.7** — A `GET /logs/file-logging` endpoint returns the current state: `{ "enabled": bool, "path": "logs/<filename>" | null, "size_bytes": int | null }`.

### FR4: Observability API — Structured Log Endpoint

**FR4.1** — The `/logs` endpoint response shape is extended to include `turn_id`, `conversation_id`, and `fields` on each entry (backwards-compatible; existing fields unchanged).

**FR4.2** — A new query parameter `turn_id` filters logs to a single turn. This is the lazy-load endpoint: the UI calls `GET /logs?turn_id=<id>` only when a turn group is expanded.

**FR4.3** — A new query parameter `conversation_id` filters logs to a session.

**FR4.4** — The endpoint returns logs newest-first when `order=desc` is passed (default remains newest-last / chronological within a turn group).

**FR4.5** — A new endpoint `GET /logs/groups` returns group summary objects only (no individual log entries). Each summary includes: `turn_id`, `conversation_id`, `start_timestamp`, `headline` (first INFO-or-above message), and a `level_counts` map (`{"DEBUG": 3, "INFO": 2, "WARNING": 1}`). This is the lightweight payload polled by the UI ticker.

### FR5: Observability UI — Collapsible Turn Groups

**FR5.1** — The Logs tab displays an **outer list of turn groups** rather than a flat list of entries. Each group is identified by `turn_id` and shows:
  - The first INFO-or-above message as a headline summary
  - Timestamp of the first log line in the turn
  - Total log count badge per level (e.g. `3 DEBUG · 2 INFO · 1 WARN`)
  - Expand/collapse chevron

**FR5.2** — Logs with no `turn_id` (e.g. startup logs, background tasks) are grouped into a persistent **"System"** group placed at the top of the list.

**FR5.3** — Groups default to **collapsed**. The most recent turn group defaults to **expanded** (its entries are pre-fetched alongside the initial group summary load).

**FR5.4** — Expanding a collapsed group triggers a **lazy fetch**: the frontend calls `GET /logs?turn_id=<id>` and renders a loading skeleton until the response arrives. Already-fetched turn data is cached in component state for the lifetime of the page — re-collapsing and re-expanding does not re-fetch.

**FR5.5** — Inside an expanded group, individual log entries are rendered in chronological order (oldest first within the turn).

**FR5.6** — Each log entry inside a group renders:
  - Time (relative to turn start, e.g. `+42 ms`)
  - Level badge (colour-coded, see FR6)
  - Logger name (abbreviated module path)
  - Message text
  - A collapsible **"Fields"** sub-row for structured fields (only shown if `fields` is non-empty)

**FR5.7** — The copy-to-clipboard button on error entries is preserved.

### FR6: Observability UI — Level Visualisation

**FR6.1** — Level badges use distinct background colours:

| Level | Colour |
|-------|--------|
| DEBUG | Cool grey `#6b7280` |
| INFO | Blue `#3b82f6` |
| WARNING | Amber `#f59e0b` |
| ERROR | Red `#ef4444` |
| CRITICAL | Deep red + bold `#991b1b` |

**FR6.2** — The level filter dropdown is replaced by a **multi-select level toggle** (pill buttons) so developers can show DEBUG+WARNING together without seeing INFO noise.

**FR6.3** — When a turn group contains at least one ERROR or CRITICAL entry the group row receives a red left border to surface failures without expanding.

**FR6.4** — When a turn group contains at least one WARNING entry (and no errors) it receives an amber left border.

**FR6.5** — Tool call failures (a tool invocation that raises an exception or receives a non-2xx status) are recorded at WARNING level by the tool dispatch layer. This means they automatically contribute to the amber border and level count badge with no extra configuration needed at individual tool call sites.

### FR7: Observability UI — File Logging Control

**FR7.1** — The Logs tab toolbar includes a **File Logging** section with:
  - An enable/disable toggle switch
  - A text input field pre-filled with the current or default filename (`aperture-assist.log`), constrained to plain filenames only (no `/` or `..` characters enforced client-side)
  - A read-only display of the resolved full path (`logs/<filename>`) so the user knows exactly where the file will land
  - A current file size indicator (shown when enabled, updated on each poll)

**FR7.2** — On mount the UI fetches `GET /logs/file-logging` to populate the toggle state, filename, and size.

**FR7.3** — Clicking the toggle calls `POST /logs/file-logging` with the current filename value. An inline success indicator (green check) or error message confirms the result. The filename field is disabled while file logging is enabled to prevent mid-session path changes.

**FR7.4** — The server enforces that the resolved path stays within the `logs/` directory. If the client somehow submits an invalid value, the API returns HTTP 400 and the UI displays the error message inline without toggling state.

---

## Non-Functional Requirements

**NFR1: Zero performance regression** — The correlation filter and structured field injection must add < 1 ms overhead per log record, measured on the test machine.

**NFR2: Backwards compatibility** — All existing `/logs` consumers receive the same `timestamp`, `level`, `logger`, `message` fields. New fields are additive.

**NFR3: No mandatory call-site changes** — Existing `logger.info("message")` calls continue to work unchanged. Structured fields are added via `extra={}` only where they add value.

**NFR4: Async-safe** — `ContextVar` usage is safe in FastAPI's async handlers and does not leak between concurrent requests.

---

## Out of Scope

- Distributed tracing (OpenTelemetry, Jaeger, Zipkin) — may follow in a later phase
- Log search / full-text query in the UI — future enhancement
- Sending logs to a remote sink (Datadog, Loki, CloudWatch) in Phase 7
- Modifying the existing tool-call capture system (separate concern)

---

## Proposed Milestones

| # | Name | Key Deliverable |
|---|------|-----------------|
| 1 | Correlation IDs | `ContextVar` plumbing, `CorrelationFilter`, `X-Conversation-ID` header handling, `turn_id` in API response, `ObservabilityLogHandler` stores IDs |
| 2 | Structured Logging | `ExtraFieldFilter`, `fields` dict in stored records, key call sites annotated, `/logs` schema updated, ring-buffer bumped to 1000 |
| 3 | File Logging | `JsonFormatter`, `RotatingFileHandler` env-var activation, `GET`/`POST /logs/file-logging` runtime control endpoints, `logs/` path constraint, UI toggle with editable filename field |
| 4 | UI — Collapsible Turn Groups | `GET /logs/groups` endpoint, lazy-load expand, cached turn data, System group |
| 5 | UI — Level Visualisation & Structured Fields | Level toggle pills, colour-coded badges, `fields` sub-row, border severity indicators, tool-call failure WARNING |

---

## Resolved Decisions

| # | Decision | Resolution |
|---|----------|------------|
| 1 | Source of `conversation_id` | Read from `X-Conversation-ID` request header (client-owned, stored in `sessionStorage`). Server generates a UUID4 fallback if the header is absent. |
| 2 | Log entry loading strategy | **Lazy load.** The initial poll hits `GET /logs/groups` for lightweight summaries only. Expanding a group triggers `GET /logs?turn_id=<id>`. Fetched data is cached in component state. |
| 3 | Tool-call failure severity | Tool dispatch layer logs failures at **WARNING** level, making them automatically contribute to amber-border and level-count badge without per-site changes. |
| 4 | Ring-buffer size | Bumped to **1000 entries** to accommodate higher DEBUG volume from structured logging. Revisit if memory pressure observed. |

---

## Success Metrics

- Developer can identify the log group for any chat turn within 5 seconds using only the UI
- Zero new `conversation_id` / `turn_id` values of `None` visible in the logs tab during a normal session
- File log (`LOG_FILE=/tmp/aperture.log`) produces valid JSON Lines parseable by `jq`
- All existing `/logs` API tests continue to pass after endpoint extension

---

**Document Status:** Draft — ready for owner review before implementation begins.
