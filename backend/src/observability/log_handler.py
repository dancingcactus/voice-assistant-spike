"""
In-memory log handler for the observability dashboard.

Captures recent log records and exposes them via the /logs API endpoint.
"""

import logging
from collections import deque
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Deque


# Maximum number of log entries to keep in memory
MAX_LOG_ENTRIES = 500


class ObservabilityLogHandler(logging.Handler):
    """A logging handler that stores recent log records in a bounded deque."""

    def __init__(self, maxlen: int = MAX_LOG_ENTRIES):
        super().__init__()
        self._records: Deque[Dict[str, Any]] = deque(maxlen=maxlen)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._records.append({
                "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": self.format(record),
            })
        except Exception:
            self.handleError(record)

    def get_logs(self, limit: int = 200, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return recent log entries, newest last."""
        entries = list(self._records)
        if level:
            level_upper = level.upper()
            entries = [e for e in entries if e["level"] == level_upper]
        return entries[-limit:]

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
    """
    handler = get_handler()
    root = logging.getLogger()
    if handler not in root.handlers:
        handler.setLevel(level)
        root.addHandler(handler)
    return handler
