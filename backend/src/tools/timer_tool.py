"""Timer Tool - set, query, and cancel timers."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from tools.tool_base import (
    Tool,
    ToolContext,
    ToolResult,
    ToolResultStatus,
    ToolParameter
)

logger = logging.getLogger(__name__)


class Timer:
    """Represents an active timer."""

    def __init__(self, duration_seconds: int, label: Optional[str] = None):
        """
        Initialize a timer.

        Args:
            duration_seconds: Timer duration in seconds
            label: Optional label for the timer
        """
        self.duration_seconds = duration_seconds
        self.label = label
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(seconds=duration_seconds)

    def time_remaining(self) -> int:
        """Get time remaining in seconds."""
        now = datetime.now()
        if now >= self.end_time:
            return 0
        return int((self.end_time - now).total_seconds())

    def is_expired(self) -> bool:
        """Check if timer has expired."""
        return datetime.now() >= self.end_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert timer to dict representation."""
        return {
            "duration_seconds": self.duration_seconds,
            "label": self.label,
            "time_remaining": self.time_remaining(),
            "is_expired": self.is_expired()
        }


class TimerTool(Tool):
    """Tool for managing timers."""

    def __init__(self):
        """Initialize the timer tool."""
        # Store timers per session
        self.timers: Dict[str, List[Timer]] = {}
        super().__init__()

    @property
    def name(self) -> str:
        return "manage_timer"

    @property
    def description(self) -> str:
        return (
            "Set, query, or cancel kitchen timers. "
            "Use this when the user wants to set a timer, check how much time is left, "
            "or cancel a timer."
        )

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="Action to perform: 'set', 'query', or 'cancel'",
                required=True,
                enum=["set", "query", "cancel"]
            ),
            ToolParameter(
                name="duration_minutes",
                type="number",
                description="Duration in minutes (required for 'set' action)",
                required=False
            ),
            ToolParameter(
                name="label",
                type="string",
                description="Optional label for the timer (e.g., 'pasta', 'bread')",
                required=False
            ),
        ]

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        """Execute timer action."""
        action = kwargs.get("action")
        session_id = context.session_id

        # Initialize session timers if needed
        if session_id not in self.timers:
            self.timers[session_id] = []

        if action == "set":
            return await self._set_timer(session_id, **kwargs)
        elif action == "query":
            return await self._query_timers(session_id)
        elif action == "cancel":
            return await self._cancel_timer(session_id, **kwargs)
        else:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"Invalid action: {action}",
                error="INVALID_ACTION"
            )

    async def _set_timer(self, session_id: str, **kwargs) -> ToolResult:
        """Set a new timer."""
        duration_minutes = kwargs.get("duration_minutes")

        if duration_minutes is None:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="duration_minutes is required for 'set' action",
                error="MISSING_PARAMETER"
            )

        if duration_minutes <= 0:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="duration_minutes must be positive",
                error="INVALID_DURATION"
            )

        label = kwargs.get("label")
        duration_seconds = int(duration_minutes * 60)

        # Create and store timer
        timer = Timer(duration_seconds, label)
        self.timers[session_id].append(timer)

        logger.info(
            f"Set timer for {duration_minutes} minutes"
            + (f" (label: {label})" if label else "")
        )

        label_str = f" for {label}" if label else ""
        return ToolResult(
            status=ToolResultStatus.SUCCESS,
            message=f"Timer set for {duration_minutes} minutes{label_str}",
            data=timer.to_dict()
        )

    async def _query_timers(self, session_id: str) -> ToolResult:
        """Query active timers."""
        timers = self.timers.get(session_id, [])

        # Remove expired timers
        active_timers = [t for t in timers if not t.is_expired()]
        self.timers[session_id] = active_timers

        if not active_timers:
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message="No active timers",
                data={"timers": []}
            )

        # Build response
        timer_info = [t.to_dict() for t in active_timers]

        if len(active_timers) == 1:
            timer = active_timers[0]
            minutes = timer.time_remaining() // 60
            seconds = timer.time_remaining() % 60

            label_str = f" for {timer.label}" if timer.label else ""
            time_str = f"{minutes} minutes and {seconds} seconds" if minutes > 0 else f"{seconds} seconds"

            message = f"Timer{label_str} has {time_str} remaining"
        else:
            message = f"{len(active_timers)} active timers"

        return ToolResult(
            status=ToolResultStatus.SUCCESS,
            message=message,
            data={"timers": timer_info}
        )

    async def _cancel_timer(self, session_id: str, **kwargs) -> ToolResult:
        """Cancel timer(s)."""
        timers = self.timers.get(session_id, [])

        if not timers:
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message="No timers to cancel",
                data={"cancelled": 0}
            )

        label = kwargs.get("label")

        if label:
            # Cancel timer with specific label
            initial_count = len(timers)
            self.timers[session_id] = [t for t in timers if t.label != label]
            cancelled = initial_count - len(self.timers[session_id])

            if cancelled > 0:
                return ToolResult(
                    status=ToolResultStatus.SUCCESS,
                    message=f"Cancelled timer for {label}",
                    data={"cancelled": cancelled}
                )
            else:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    message=f"No timer found with label: {label}",
                    error="TIMER_NOT_FOUND"
                )
        else:
            # Cancel all timers
            count = len(timers)
            self.timers[session_id] = []

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"Cancelled {count} timer(s)",
                data={"cancelled": count}
            )
