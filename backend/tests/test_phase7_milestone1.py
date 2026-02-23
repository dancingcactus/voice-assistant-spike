"""
Tests for Phase 7 Milestone 1: Correlation IDs.

Covers:
- CorrelationFilter stamps correct IDs onto a LogRecord
- Unset context → IDs default to "", not None
- Two concurrent async tasks with different IDs do not bleed into each other
- ObservabilityLogHandler.emit() stores conversation_id and turn_id
- get_logs() returns records with conversation_id and turn_id fields present
- Ring-buffer capped at 1000 (not 500)
"""

import asyncio
import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logging_context import (
    CorrelationFilter,
    conversation_id_var,
    generate_id,
    set_correlation_ids,
    turn_id_var,
)
from observability.log_handler import ObservabilityLogHandler, MAX_LOG_ENTRIES, install


# ===========================================================================
# CorrelationFilter
# ===========================================================================


class TestCorrelationFilter:
    def _make_record(self, msg: str = "test") -> logging.LogRecord:
        return logging.LogRecord("test", logging.INFO, "", 0, msg, (), None)

    def test_stamps_correct_ids(self):
        cid = generate_id()
        tid = generate_id()
        set_correlation_ids(cid, tid)
        f = CorrelationFilter()
        record = self._make_record()
        f.filter(record)
        assert record.conversation_id == cid
        assert record.turn_id == tid

    def test_default_ids_are_empty_string(self):
        # Reset to empty
        conversation_id_var.set("")
        turn_id_var.set("")
        f = CorrelationFilter()
        record = self._make_record()
        f.filter(record)
        assert record.conversation_id == ""
        assert record.turn_id == ""
        assert record.conversation_id is not None
        assert record.turn_id is not None

    def test_filter_returns_true(self):
        f = CorrelationFilter()
        record = self._make_record()
        assert f.filter(record) is True


# ===========================================================================
# Async context isolation
# ===========================================================================


@pytest.mark.asyncio
async def test_async_context_isolation():
    """Two concurrent async tasks must not bleed IDs into each other."""

    async def task_a():
        cid = "task-a-cid"
        tid = "task-a-tid"
        set_correlation_ids(cid, tid)
        await asyncio.sleep(0)  # yield to other task
        assert conversation_id_var.get() == cid
        assert turn_id_var.get() == tid

    async def task_b():
        cid = "task-b-cid"
        tid = "task-b-tid"
        set_correlation_ids(cid, tid)
        await asyncio.sleep(0)
        assert conversation_id_var.get() == cid
        assert turn_id_var.get() == tid

    await asyncio.gather(task_a(), task_b())


# ===========================================================================
# ObservabilityLogHandler.emit()
# ===========================================================================


class TestLogHandlerCorrelationStorage:
    def _make_handler(self) -> ObservabilityLogHandler:
        h = ObservabilityLogHandler()
        h.setFormatter(logging.Formatter("%(name)s - %(message)s"))
        return h

    def _emit_with_ids(self, handler, cid: str, tid: str, msg: str = "hello") -> None:
        set_correlation_ids(cid, tid)
        f = CorrelationFilter()
        record = logging.LogRecord("test", logging.INFO, "", 0, msg, (), None)
        f.filter(record)
        handler.emit(record)

    def test_emit_stores_conversation_id(self):
        h = self._make_handler()
        self._emit_with_ids(h, "ccc", "ttt")
        logs = h.get_logs()
        assert logs[-1]["conversation_id"] == "ccc"

    def test_emit_stores_turn_id(self):
        h = self._make_handler()
        self._emit_with_ids(h, "ccc", "ttt")
        logs = h.get_logs()
        assert logs[-1]["turn_id"] == "ttt"

    def test_get_logs_has_required_keys(self):
        h = self._make_handler()
        self._emit_with_ids(h, "x", "y")
        entry = h.get_logs()[-1]
        for key in ("timestamp", "level", "logger", "message", "conversation_id", "turn_id"):
            assert key in entry, f"Missing key: {key}"

    def test_fields_key_present(self):
        h = self._make_handler()
        self._emit_with_ids(h, "x", "y")
        entry = h.get_logs()[-1]
        assert "fields" in entry


# ===========================================================================
# Ring-buffer size
# ===========================================================================


class TestRingBufferSize:
    def test_max_entries_is_1000(self):
        assert MAX_LOG_ENTRIES == 1000

    def test_buffer_is_capped(self):
        h = ObservabilityLogHandler(maxlen=10)
        h.setFormatter(logging.Formatter("%(message)s"))
        for i in range(20):
            r = logging.LogRecord("t", logging.DEBUG, "", 0, f"msg{i}", (), None)
            h.emit(r)
        assert len(h.get_logs(limit=100)) == 10


# ===========================================================================
# install() sets root logger level
# ===========================================================================


class TestInstallSetsRootLevel:
    """install() must lower the root logger level so sub-ERROR records reach the handler."""

    def test_install_lowers_root_level_to_debug(self, monkeypatch):
        """After install(), root logger level must be <= DEBUG so INFO/DEBUG pass through."""
        import observability.log_handler as lh

        # Reset singleton so install() runs fresh
        monkeypatch.setattr(lh, "_handler", None)
        root = logging.getLogger()
        original_level = root.level
        try:
            root.setLevel(logging.WARNING)
            install(logging.DEBUG)
            assert root.level <= logging.DEBUG
        finally:
            root.setLevel(original_level)
            monkeypatch.setattr(lh, "_handler", None)

    def test_install_captures_info_via_root_logger(self, monkeypatch):
        """INFO messages logged through the root logger must appear in the handler after install()."""
        import observability.log_handler as lh

        monkeypatch.setattr(lh, "_handler", None)
        root = logging.getLogger()
        original_level = root.level
        try:
            root.setLevel(logging.WARNING)
            handler = install(logging.DEBUG)
            handler.clear()

            test_logger = logging.getLogger("test.install.info")
            test_logger.info("info-visible")

            messages = [e["message"] for e in handler.get_logs()]
            assert any("info-visible" in m for m in messages), (
                "INFO log was not captured; root logger level may still be too high"
            )
        finally:
            root.setLevel(original_level)
            monkeypatch.setattr(lh, "_handler", None)
