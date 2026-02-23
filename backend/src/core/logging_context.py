"""
Correlation context for structured logging.

Provides ContextVar-based conversation_id and turn_id that are automatically
stamped onto every log record emitted during a request/turn via CorrelationFilter.
"""

from contextvars import ContextVar
import logging
import uuid

conversation_id_var: ContextVar[str] = ContextVar("conversation_id", default="")
turn_id_var: ContextVar[str] = ContextVar("turn_id", default="")


def generate_id() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


def set_correlation_ids(conversation_id: str, turn_id: str) -> None:
    """Set both correlation IDs on the current context."""
    conversation_id_var.set(conversation_id)
    turn_id_var.set(turn_id)


class CorrelationFilter(logging.Filter):
    """Stamps conversation_id and turn_id onto every LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.conversation_id = conversation_id_var.get()
        record.turn_id = turn_id_var.get()
        return True
