"""
JSON formatter for file-based log output.

Produces a single JSON object per log record (JSON Lines format).
"""

import json
import logging
from datetime import datetime, timezone

from .log_handler import STRUCTURED_FIELDS


class JsonFormatter(logging.Formatter):
    """Formats a LogRecord as a single JSON object (no trailing newline)."""

    def format(self, record: logging.LogRecord) -> str:
        fields = {k: getattr(record, k) for k in STRUCTURED_FIELDS if hasattr(record, k)}
        obj = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "conversation_id": getattr(record, "conversation_id", ""),
            "turn_id": getattr(record, "turn_id", ""),
            "fields": fields,
        }
        return json.dumps(obj, default=str)
