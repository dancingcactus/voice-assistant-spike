"""
Tests for Phase 7 Milestone 2: Structured Logging.

Covers:
- emit() correctly extracts each supported structured field when present
- emit() stores empty fields: {} when no structured fields are on the record
- Unknown extra fields are NOT included in fields (no leakage)
- GET /logs?turn_id=X returns only records with that turn_id
- GET /logs?conversation_id=X returns only records for that session
- GET /logs?order=desc returns newest first
- GET /logs?order=asc (default) returns oldest first
- Tool failure logs are at WARNING level
- Tool success logs carry tool_name in fields
- LLM call logs carry model and token_count in fields when provided
"""

import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logging_context import CorrelationFilter, set_correlation_ids
from observability.log_handler import ObservabilityLogHandler, STRUCTURED_FIELDS


# ===========================================================================
# Helpers
# ===========================================================================


def make_handler() -> ObservabilityLogHandler:
    h = ObservabilityLogHandler()
    h.setFormatter(logging.Formatter("%(name)s - %(message)s"))
    return h


def make_record(msg: str = "test", level: int = logging.INFO, **extra_attrs) -> logging.LogRecord:
    record = logging.LogRecord("test", level, "", 0, msg, (), None)
    for k, v in extra_attrs.items():
        setattr(record, k, v)
    # Stamp correlation IDs
    CorrelationFilter().filter(record)
    return record


# ===========================================================================
# STRUCTURED_FIELDS constant
# ===========================================================================


class TestStructuredFieldsConstant:
    def test_contains_expected_keys(self):
        expected = {"character", "tool_name", "turn_type", "coordination_mode", "latency_ms", "model", "token_count"}
        assert expected <= STRUCTURED_FIELDS


# ===========================================================================
# emit() structured field extraction
# ===========================================================================


class TestEmitStructuredFields:
    def test_character_field_extracted(self):
        h = make_handler()
        h.emit(make_record(character="delilah"))
        assert h.get_logs()[-1]["fields"]["character"] == "delilah"

    def test_tool_name_field_extracted(self):
        h = make_handler()
        h.emit(make_record(tool_name="set_timer"))
        assert h.get_logs()[-1]["fields"]["tool_name"] == "set_timer"

    def test_latency_ms_field_extracted(self):
        h = make_handler()
        h.emit(make_record(latency_ms=42.7))
        assert h.get_logs()[-1]["fields"]["latency_ms"] == 42.7

    def test_model_field_extracted(self):
        h = make_handler()
        h.emit(make_record(model="gpt-4o-mini"))
        assert h.get_logs()[-1]["fields"]["model"] == "gpt-4o-mini"

    def test_token_count_field_extracted(self):
        h = make_handler()
        h.emit(make_record(token_count=312))
        assert h.get_logs()[-1]["fields"]["token_count"] == 312

    def test_turn_type_field_extracted(self):
        h = make_handler()
        h.emit(make_record(turn_type="new_request"))
        assert h.get_logs()[-1]["fields"]["turn_type"] == "new_request"

    def test_coordination_mode_field_extracted(self):
        h = make_handler()
        h.emit(make_record(coordination_mode="idle"))
        assert h.get_logs()[-1]["fields"]["coordination_mode"] == "idle"

    def test_empty_fields_when_no_extras(self):
        h = make_handler()
        h.emit(make_record())
        assert h.get_logs()[-1]["fields"] == {}

    def test_unknown_extras_not_in_fields(self):
        h = make_handler()
        h.emit(make_record(some_secret="should_not_appear"))
        assert "some_secret" not in h.get_logs()[-1]["fields"]

    def test_multiple_fields_extracted(self):
        h = make_handler()
        h.emit(make_record(character="hank", latency_ms=10.0, tool_name="set_reminder"))
        fields = h.get_logs()[-1]["fields"]
        assert fields["character"] == "hank"
        assert fields["latency_ms"] == 10.0
        assert fields["tool_name"] == "set_reminder"


# ===========================================================================
# get_logs() filtering
# ===========================================================================


class TestGetLogsFiltering:
    def _handler_with_two_turns(self) -> ObservabilityLogHandler:
        h = make_handler()
        set_correlation_ids("conv-1", "turn-A")
        f = CorrelationFilter()

        r1 = logging.LogRecord("t", logging.INFO, "", 0, "msg-turn-A", (), None)
        f.filter(r1)
        h.emit(r1)

        set_correlation_ids("conv-1", "turn-B")
        r2 = logging.LogRecord("t", logging.INFO, "", 0, "msg-turn-B", (), None)
        f.filter(r2)
        h.emit(r2)

        return h

    def test_filter_by_turn_id(self):
        h = self._handler_with_two_turns()
        result = h.get_logs(turn_id="turn-A")
        assert all(e["turn_id"] == "turn-A" for e in result)
        assert len(result) == 1

    def test_filter_by_conversation_id(self):
        h = make_handler()
        f = CorrelationFilter()
        for conv, msg in [("conv-X", "x"), ("conv-Y", "y")]:
            set_correlation_ids(conv, "t1")
            r = logging.LogRecord("t", logging.INFO, "", 0, msg, (), None)
            f.filter(r)
            h.emit(r)
        result = h.get_logs(conversation_id="conv-X")
        assert all(e["conversation_id"] == "conv-X" for e in result)
        assert len(result) == 1

    def test_order_desc_returns_newest_first(self):
        h = self._handler_with_two_turns()
        result = h.get_logs(order="desc")
        # turn-B was emitted second, so it should be first in desc order
        assert result[0]["message"].endswith("msg-turn-B")

    def test_order_asc_returns_oldest_first(self):
        h = self._handler_with_two_turns()
        result = h.get_logs(order="asc")
        assert result[0]["message"].endswith("msg-turn-A")


# ===========================================================================
# Tool failure level
# ===========================================================================


class TestToolFailureLevel:
    def test_tool_failure_is_warning_not_error(self):
        """Tool failures must be stored at WARNING level per design decision 3."""
        h = make_handler()
        r = logging.LogRecord("core.tool_system", logging.WARNING, "", 0, "Tool execution failed", (), None)
        CorrelationFilter().filter(r)
        setattr(r, "tool_name", "bad_tool")
        h.emit(r)
        logs = h.get_logs(level="WARNING")
        assert len(logs) == 1
        assert logs[0]["level"] == "WARNING"
        assert logs[0]["fields"]["tool_name"] == "bad_tool"

    def test_tool_success_is_info_with_tool_name(self):
        h = make_handler()
        r = logging.LogRecord("core.tool_system", logging.INFO, "", 0, "Tool executed", (), None)
        CorrelationFilter().filter(r)
        setattr(r, "tool_name", "set_timer")
        h.emit(r)
        logs = h.get_logs(level="INFO")
        assert any(e["fields"].get("tool_name") == "set_timer" for e in logs)


# ===========================================================================
# LLM log fields
# ===========================================================================


class TestLLMLogFields:
    def test_llm_log_carries_model_and_token_count(self):
        h = make_handler()
        r = logging.LogRecord("integrations.llm_integration", logging.INFO, "", 0, "LLM response received", (), None)
        CorrelationFilter().filter(r)
        setattr(r, "model", "gpt-4o-mini")
        setattr(r, "token_count", 150)
        setattr(r, "latency_ms", 820.5)
        h.emit(r)
        entry = h.get_logs()[-1]
        assert entry["fields"]["model"] == "gpt-4o-mini"
        assert entry["fields"]["token_count"] == 150
        assert isinstance(entry["fields"]["latency_ms"], float)
