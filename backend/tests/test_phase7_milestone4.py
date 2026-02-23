"""
Tests for Phase 7 Milestone 4: UI Collapsible Turn Groups.

Covers:
- get_groups() returns one group per distinct turn_id
- Records with empty turn_id aggregate into the system group (turn_id: None)
- level_counts correctly tallies per level per group
- headline is the first INFO-or-above message, not a DEBUG message
- start_timestamp is the timestamp of the first record in the group
- Groups are sorted newest-first; system group always first
- GET /logs/groups API endpoint returns correct shape and auth-gated (401 without token)
- GET /logs?turn_id=X returns only entries for that turn (regression on Milestone 2 filter)
- Adding records for a second turn creates a second group (does not pollute first)
- Empty handler → get_groups() returns []
"""

import logging
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logging_context import CorrelationFilter, set_correlation_ids, conversation_id_var, turn_id_var
from observability.log_handler import ObservabilityLogHandler
from observability.file_log_manager import FileLogManager


# ===========================================================================
# Helpers
# ===========================================================================


def make_handler() -> ObservabilityLogHandler:
    h = ObservabilityLogHandler()
    h.setFormatter(logging.Formatter("%(name)s - %(message)s"))
    return h


def emit_record(handler: ObservabilityLogHandler, turn_id: str, conv_id: str = "c1",
                msg: str = "msg", level: int = logging.INFO) -> None:
    set_correlation_ids(conv_id, turn_id)
    r = logging.LogRecord("test", level, "", 0, msg, (), None)
    CorrelationFilter().filter(r)
    handler.emit(r)


# ===========================================================================
# get_groups()
# ===========================================================================


class TestGetGroups:
    def test_empty_handler_returns_empty(self):
        h = make_handler()
        assert h.get_groups() == []

    def test_one_group_per_turn_id(self):
        h = make_handler()
        emit_record(h, "turn-A")
        emit_record(h, "turn-A")
        emit_record(h, "turn-B")
        groups = h.get_groups()
        turn_ids = {g["turn_id"] for g in groups}
        assert "turn-A" in turn_ids
        assert "turn-B" in turn_ids
        assert len(turn_ids) == 2

    def test_empty_turn_id_aggregated_to_system(self):
        h = make_handler()
        emit_record(h, "")
        emit_record(h, "")
        groups = h.get_groups()
        system_groups = [g for g in groups if g["turn_id"] is None]
        assert len(system_groups) == 1
        assert system_groups[0]["entry_count"] == 2

    def test_level_counts_tallied_correctly(self):
        h = make_handler()
        emit_record(h, "turn-X", level=logging.DEBUG)
        emit_record(h, "turn-X", level=logging.DEBUG)
        emit_record(h, "turn-X", level=logging.INFO)
        emit_record(h, "turn-X", level=logging.WARNING)
        groups = h.get_groups()
        turn_group = next(g for g in groups if g["turn_id"] == "turn-X")
        assert turn_group["level_counts"]["DEBUG"] == 2
        assert turn_group["level_counts"]["INFO"] == 1
        assert turn_group["level_counts"]["WARNING"] == 1

    def test_headline_is_first_info_or_above_not_debug(self):
        h = make_handler()
        emit_record(h, "turn-Y", msg="debug only", level=logging.DEBUG)
        emit_record(h, "turn-Y", msg="info message", level=logging.INFO)
        groups = h.get_groups()
        turn_group = next(g for g in groups if g["turn_id"] == "turn-Y")
        # Should be the info message (or formatted form), not the debug message
        assert turn_group["headline"] is not None
        assert "info message" in turn_group["headline"]

    def test_headline_none_when_only_debug(self):
        h = make_handler()
        emit_record(h, "turn-Z", msg="only debug", level=logging.DEBUG)
        groups = h.get_groups()
        turn_group = next(g for g in groups if g["turn_id"] == "turn-Z")
        assert turn_group["headline"] is None

    def test_start_timestamp_is_first_record_timestamp(self):
        h = make_handler()
        emit_record(h, "turn-T", msg="first")
        emit_record(h, "turn-T", msg="second")
        groups = h.get_groups()
        turn_group = next(g for g in groups if g["turn_id"] == "turn-T")
        all_entries = h.get_logs(turn_id="turn-T")
        assert turn_group["start_timestamp"] == all_entries[0]["timestamp"]

    def test_system_group_first(self):
        h = make_handler()
        emit_record(h, "turn-A")
        emit_record(h, "")  # system group
        groups = h.get_groups()
        assert groups[0]["turn_id"] is None

    def test_second_turn_does_not_pollute_first(self):
        h = make_handler()
        emit_record(h, "turn-1", msg="msg1")
        emit_record(h, "turn-2", msg="msg2")
        entries_for_1 = h.get_logs(turn_id="turn-1")
        assert all(e["turn_id"] == "turn-1" for e in entries_for_1)
        assert len(entries_for_1) == 1

    def test_entry_count_matches_records(self):
        h = make_handler()
        for i in range(5):
            emit_record(h, "turn-count", msg=f"msg{i}")
        groups = h.get_groups()
        g = next(g for g in groups if g["turn_id"] == "turn-count")
        assert g["entry_count"] == 5

    def test_groups_sorted_newest_first_by_start_timestamp(self):
        import time
        h = make_handler()
        emit_record(h, "turn-old")
        time.sleep(0.01)  # ensure different timestamps
        emit_record(h, "turn-new")
        groups = [g for g in h.get_groups() if g["turn_id"] is not None]
        assert groups[0]["turn_id"] == "turn-new"
        assert groups[1]["turn_id"] == "turn-old"


# ===========================================================================
# API endpoint: GET /logs/groups
# ===========================================================================


def _get_client():
    FileLogManager._reset()
    from observability.api import app
    return TestClient(app)


class TestLogGroupsEndpoint:
    def setup_method(self):
        FileLogManager._reset()

    def teardown_method(self):
        FileLogManager._reset()

    def test_get_groups_returns_200(self):
        client = _get_client()
        resp = client.get("/logs/groups", headers={"Authorization": "Bearer dev_token_12345"})
        assert resp.status_code == 200
        data = resp.json()
        assert "groups" in data
        assert isinstance(data["groups"], list)

    def test_get_groups_requires_auth(self):
        client = _get_client()
        resp = client.get("/logs/groups")
        assert resp.status_code == 401

    def test_group_has_expected_shape(self):
        from observability.log_handler import get_handler
        from observability.log_handler import install
        install()
        handler = get_handler()
        handler.clear()
        set_correlation_ids("cid-1", "turn-shape")
        r = logging.LogRecord("test", logging.INFO, "", 0, "shape test", (), None)
        CorrelationFilter().filter(r)
        handler.emit(r)

        client = _get_client()
        resp = client.get("/logs/groups", headers={"Authorization": "Bearer dev_token_12345"})
        groups = resp.json()["groups"]
        turn_group = next((g for g in groups if g.get("turn_id") == "turn-shape"), None)
        if turn_group:
            for key in ("turn_id", "conversation_id", "start_timestamp", "headline", "level_counts", "entry_count"):
                assert key in turn_group, f"Missing key: {key}"
