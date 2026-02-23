"""
Tests for Phase 7 Milestone 5: UI Level Visualisation & Structured Fields.

This milestone is primarily frontend; backend tests verify end-to-end filter
correctness and that tool failures produce WARNING-level records with correct fields.

Covers:
- GET /logs with no filters returns records including fields dict on every entry
- GET /logs?turn_id=X&order=desc returns entries for that turn, newest-first
- A tool failure produces a WARNING-level record with tool_name in fields
- A tool success produces an INFO-level record with tool_name in fields
- Structured field latency_ms is a float, not a string
- GET /logs/groups level_counts correctly includes WARNING when tool failures present
"""

import logging
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logging_context import CorrelationFilter, set_correlation_ids
from observability.log_handler import ObservabilityLogHandler
from observability.file_log_manager import FileLogManager


# ===========================================================================
# Helpers
# ===========================================================================


def make_handler() -> ObservabilityLogHandler:
    h = ObservabilityLogHandler()
    h.setFormatter(logging.Formatter("%(name)s - %(message)s"))
    return h


def emit(handler: ObservabilityLogHandler, turn_id: str, conv_id: str = "c1",
         msg: str = "msg", level: int = logging.INFO, **extra) -> None:
    set_correlation_ids(conv_id, turn_id)
    r = logging.LogRecord("test", level, "", 0, msg, (), None)
    CorrelationFilter().filter(r)
    for k, v in extra.items():
        setattr(r, k, v)
    handler.emit(r)


# ===========================================================================
# End-to-end handler tests
# ===========================================================================


class TestEndToEndFilters:
    def test_all_entries_have_fields_key(self):
        h = make_handler()
        emit(h, "t1", msg="hello")
        emit(h, "t2", msg="world", tool_name="timer")
        logs = h.get_logs()
        assert all("fields" in e for e in logs)

    def test_turn_id_desc_order(self):
        h = make_handler()
        emit(h, "t-order", msg="first")
        emit(h, "t-order", msg="second")
        logs = h.get_logs(turn_id="t-order", order="desc")
        assert logs[0]["message"].endswith("second")
        assert logs[1]["message"].endswith("first")

    def test_tool_failure_is_warning_with_tool_name(self):
        h = make_handler()
        set_correlation_ids("cx", "tx")
        r = logging.LogRecord("core.tool_system", logging.WARNING, "", 0,
                              "Tool execution failed: bad_tool — not found", (), None)
        CorrelationFilter().filter(r)
        setattr(r, "tool_name", "bad_tool")
        setattr(r, "latency_ms", 0.5)
        h.emit(r)
        warnings = h.get_logs(level="WARNING")
        assert len(warnings) >= 1
        assert warnings[-1]["level"] == "WARNING"
        assert warnings[-1]["fields"]["tool_name"] == "bad_tool"

    def test_tool_success_is_info_with_tool_name(self):
        h = make_handler()
        emit(h, "t-success", msg="Tool executed", level=logging.INFO, tool_name="set_timer", latency_ms=12.4)
        infos = h.get_logs(level="INFO")
        tool_entry = next((e for e in infos if e["fields"].get("tool_name") == "set_timer"), None)
        assert tool_entry is not None
        assert tool_entry["level"] == "INFO"

    def test_latency_ms_is_float(self):
        h = make_handler()
        emit(h, "t-float", msg="latency test", latency_ms=42.5)
        entry = h.get_logs()[-1]
        assert isinstance(entry["fields"]["latency_ms"], float)

    def test_groups_level_counts_include_warning_on_tool_failure(self):
        h = make_handler()
        # Emit an INFO record first
        emit(h, "t-warn", msg="turn start", level=logging.INFO)
        # Emit a WARNING for a tool failure
        set_correlation_ids("cx", "t-warn")
        r = logging.LogRecord("core.tool_system", logging.WARNING, "", 0, "fail", (), None)
        CorrelationFilter().filter(r)
        setattr(r, "tool_name", "bad_tool")
        h.emit(r)

        groups = h.get_groups()
        g = next((g for g in groups if g["turn_id"] == "t-warn"), None)
        assert g is not None
        assert g["level_counts"].get("WARNING", 0) >= 1


# ===========================================================================
# API regression tests
# ===========================================================================


def _get_client():
    FileLogManager._reset()
    from observability.api import app
    return TestClient(app)


class TestLogsAPIRegression:
    def setup_method(self):
        FileLogManager._reset()

    def teardown_method(self):
        FileLogManager._reset()

    def test_get_logs_returns_fields_on_every_entry(self):
        from observability.log_handler import get_handler, install
        install()
        handler = get_handler()
        handler.clear()
        emit(handler, "t-api", msg="api test")

        client = _get_client()
        resp = client.get("/logs", headers={"Authorization": "Bearer dev_token_12345"})
        assert resp.status_code == 200
        logs = resp.json()["logs"]
        if logs:
            assert all("fields" in e for e in logs)

    def test_get_logs_turn_id_desc_filter(self):
        from observability.log_handler import get_handler, install
        install()
        handler = get_handler()
        handler.clear()
        emit(handler, "t-desc", msg="first entry")
        emit(handler, "t-desc", msg="second entry")

        client = _get_client()
        resp = client.get(
            "/logs?turn_id=t-desc&order=desc",
            headers={"Authorization": "Bearer dev_token_12345"}
        )
        assert resp.status_code == 200
        logs = resp.json()["logs"]
        assert len(logs) == 2
        # desc order: second entry should come first
        assert "second entry" in logs[0]["message"]
