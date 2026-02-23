"""
In-memory log handler for the observability dashboard.

Captures recent log records and exposes them via the /logs API endpoint.
"""

import logging
from collections import deque
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Deque


# Maximum number of log entries to keep in memory
MAX_LOG_ENTRIES = 1000

# Supported structured field names extracted from LogRecord extras
STRUCTURED_FIELDS = frozenset({
    "character", "tool_name", "turn_type", "coordination_mode",
    "latency_ms", "model", "token_count",
})


class ObservabilityLogHandler(logging.Handler):
    """A logging handler that stores recent log records in a bounded deque."""

    def __init__(self, maxlen: int = MAX_LOG_ENTRIES):
        super().__init__()
        self._records: Deque[Dict[str, Any]] = deque(maxlen=maxlen)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            fields = {k: getattr(record, k) for k in STRUCTURED_FIELDS if hasattr(record, k)}
            self._records.append({
                "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": self.format(record),
                "conversation_id": getattr(record, "conversation_id", ""),
                "turn_id": getattr(record, "turn_id", ""),
                "fields": fields,
            })
        except Exception:
            self.handleError(record)

    def get_logs(
        self,
        limit: int = 200,
        level: Optional[str] = None,
        turn_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        order: str = "asc",
    ) -> List[Dict[str, Any]]:
        """Return recent log entries, optionally filtered and ordered."""
        entries = list(self._records)
        if level:
            level_upper = level.upper()
            entries = [e for e in entries if e["level"] == level_upper]
        if turn_id is not None:
            entries = [e for e in entries if e.get("turn_id") == turn_id]
        if conversation_id is not None:
            entries = [e for e in entries if e.get("conversation_id") == conversation_id]
        if order == "desc":
            entries = list(reversed(entries))
        return entries[-limit:]

    def get_groups(self) -> List[Dict[str, Any]]:
        """
        Return one summary dict per turn_id (empty turn_id → system group).
        Groups are sorted newest-first; system group always first.
        """
        buckets: Dict[str, Dict[str, Any]] = {}
        for entry in self._records:
            key = entry.get("turn_id") or ""
            if key not in buckets:
                buckets[key] = {
                    "turn_id": entry.get("turn_id") or None,
                    "conversation_id": entry.get("conversation_id", ""),
                    "start_timestamp": entry["timestamp"],
                    "headline": None,
                    "level_counts": {},
                    "entry_count": 0,
                }
            b = buckets[key]
            b["entry_count"] += 1
            lvl = entry["level"]
            b["level_counts"][lvl] = b["level_counts"].get(lvl, 0) + 1
            if b["headline"] is None and lvl in ("INFO", "WARNING", "ERROR", "CRITICAL"):
                b["headline"] = entry["message"]

        groups = sorted(buckets.values(), key=lambda g: g["start_timestamp"], reverse=True)
        system = [g for g in groups if g["turn_id"] is None]
        turns = [g for g in groups if g["turn_id"] is not None]
        return system + turns

    def clear(self) -> None:
        self._records.clear()


# Singleton handler instance shared across the application
_handler: Optional[ObservabilityLogHandler] = None


def get_handler() -> ObservabilityLogHandler:
    """Return the singleton ObservabilityLogHandler, creating it if needed."""
    global _handler
    if _handler is None:
        _handler = ObservabilityLogHandler()
        formatter = logging.Formatter("%(name)s - %(message)s")
        _handler.setFormatter(formatter)
    return _handler


def install(level: int = logging.DEBUG) -> ObservabilityLogHandler:
    """
    Attach the observability handler to the root logger.

    Safe to call multiple times – duplicate installation is a no-op.
    Also attaches CorrelationFilter so every record carries conversation_id/turn_id.
    """
    from core.logging_context import CorrelationFilter

    handler = get_handler()
    root = logging.getLogger()
    if handler not in root.handlers:
        handler.setLevel(level)
        root.addHandler(handler)
        # Attach correlation filter to root so all handlers see the IDs
        root.addFilter(CorrelationFilter())
    return handler
