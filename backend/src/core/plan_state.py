"""
Plan state management for multi-step coordinator plans.

``PlanStateManager`` is the single source of truth for reading and writing
``PlanState`` into ``ConversationContext.metadata``.

A *plan* is a multi-step sequence created when a character calls the
``plan_action`` tool with ``action="start"``.  While a plan is ``active``:

- Characters receive a wider history window that includes **all turns since
  the plan started**, giving them full context of what has already happened.
- The plan automatically expires (resets to idle) after
  ``_DEFAULT_PLAN_EXPIRY_MINUTES`` of inactivity.  Every conversation turn
  refreshes the expiry via ``touch()``.

Life-cycle::

    # Character calls plan_action(action="start", title=..., steps=[...])
    # → CharacterExecutor raises plan_signal → ConversationManager calls:
    plan_state_manager.start_plan(context, title, steps, turn_start_index)

    # Character calls plan_action(action="advance")
    # → plan_signal → ConversationManager calls:
    plan_state_manager.advance_step(context)

    # Character calls plan_action(action="complete")
    # → plan_signal → ConversationManager calls:
    plan_state_manager.complete_plan(context)

    # 20 min of inactivity → orchestrator calls:
    plan_state_manager.clear(context)   # resets to idle
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from models.message import ConversationContext

logger = logging.getLogger(__name__)

# Metadata key under which ``PlanState`` is persisted.
_PLAN_STATE_KEY = "plan_state"

# Default TTL for an active plan in minutes.
_DEFAULT_PLAN_EXPIRY_MINUTES = 20


@dataclass
class PlanState:
    """
    State for an active multi-step plan.

    Attributes:
        title: Short human-readable description of the plan.
        steps: Ordered list of step descriptions.
        current_step_index: Zero-based index of the step currently being
            executed.  Incremented by ``advance_step()``.
        status: ``"active"`` while in progress, ``"completed"`` when all steps
            are done or ``complete_plan()`` is called.
        plan_turn_start_index: Index into ``ConversationContext.history`` at the
            point the plan was started.  Characters receive all history from
            this index onward so they have full plan context.
        expires_at: ISO-format UTC timestamp after which the plan is considered
            stale and will be silently cleared by the orchestrator.
        last_updated: ISO-format UTC timestamp of the last mutation.
    """

    title: str
    steps: List[str]
    current_step_index: int = 0
    status: str = "active"  # "active" | "completed"
    plan_turn_start_index: int = 0
    expires_at: Optional[str] = None
    last_updated: Optional[str] = None

    @property
    def current_step(self) -> Optional[str]:
        """Return the description of the current step, or ``None`` if complete."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    @property
    def is_active(self) -> bool:
        """``True`` when the plan is in progress."""
        return self.status == "active"

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dictionary."""
        return {
            "title": self.title,
            "steps": self.steps,
            "current_step_index": self.current_step_index,
            "status": self.status,
            "plan_turn_start_index": self.plan_turn_start_index,
            "expires_at": self.expires_at,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlanState":
        """Deserialise from a dictionary (as stored in ``context.metadata``)."""
        return cls(
            title=data.get("title", ""),
            steps=data.get("steps", []),
            current_step_index=data.get("current_step_index", 0),
            status=data.get("status", "active"),
            plan_turn_start_index=data.get("plan_turn_start_index", 0),
            expires_at=data.get("expires_at"),
            last_updated=data.get("last_updated"),
        )


class PlanStateManager:
    """
    Reads and writes ``PlanState`` on a ``ConversationContext``.

    All public methods are synchronous — no I/O is involved.

    Usage::

        psm = PlanStateManager()

        # Start a plan when the character calls plan_action(action="start")
        psm.start_plan(
            context,
            title="Southern Fried Chicken Dinner",
            steps=["Choose recipe", "Build shopping list", "Set timers"],
            turn_start_index=len(context.history),
        )

        # Advance to the next step
        psm.advance_step(context)

        # Mark complete
        psm.complete_plan(context)

        # Or expire automatically — orchestrator calls clear() when TTL elapses
        psm.clear(context)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_state(self, context: ConversationContext) -> Optional[PlanState]:
        """
        Return the current ``PlanState`` for *context*, or ``None`` if no plan
        is stored.

        Args:
            context: The conversation context to read from.

        Returns:
            ``PlanState`` if one exists, otherwise ``None``.
        """
        raw = context.metadata.get(_PLAN_STATE_KEY)
        if raw:
            try:
                return PlanState.from_dict(raw)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to deserialise plan_state: %s — ignoring", exc
                )
        return None

    def start_plan(
        self,
        context: ConversationContext,
        title: str,
        steps: List[str],
        turn_start_index: int = 0,
        expiry_minutes: int = _DEFAULT_PLAN_EXPIRY_MINUTES,
    ) -> PlanState:
        """
        Create a new active plan and persist it to *context*.

        Any existing plan state is overwritten.

        Args:
            context: Conversation context to update.
            title: Short plan title.
            steps: Ordered list of step descriptions.
            turn_start_index: Index into ``context.history`` when the plan was
                created.  Characters will see all history from this point.
            expiry_minutes: Inactivity TTL in minutes (default 20).

        Returns:
            The new ``PlanState``.
        """
        now = datetime.utcnow()
        state = PlanState(
            title=title,
            steps=list(steps),
            current_step_index=0,
            status="active",
            plan_turn_start_index=turn_start_index,
            expires_at=(now + timedelta(minutes=expiry_minutes)).isoformat(),
            last_updated=now.isoformat(),
        )
        self._persist(context, state)
        logger.info(
            "Plan started: title=%r, steps=%d, turn_start=%d",
            title,
            len(steps),
            turn_start_index,
        )
        return state

    def advance_step(
        self,
        context: ConversationContext,
        expiry_minutes: int = _DEFAULT_PLAN_EXPIRY_MINUTES,
    ) -> Optional[PlanState]:
        """
        Increment ``current_step_index`` and refresh the TTL.

        If the last step is advanced past, ``status`` is set to ``"completed"``.

        Args:
            context: Conversation context to update.
            expiry_minutes: Refreshed TTL in minutes.

        Returns:
            Updated ``PlanState``, or ``None`` if no active plan exists.
        """
        state = self.get_state(context)
        if not state or not state.is_active:
            logger.debug("advance_step called but no active plan — no-op")
            return state

        now = datetime.utcnow()
        state.current_step_index += 1
        if state.current_step_index >= len(state.steps):
            state.status = "completed"
            logger.info("Plan '%s' completed (all %d steps done)", state.title, len(state.steps))
        else:
            logger.info(
                "Plan '%s' advanced to step %d/%d: %r",
                state.title,
                state.current_step_index + 1,
                len(state.steps),
                state.current_step,
            )
        state.expires_at = (now + timedelta(minutes=expiry_minutes)).isoformat()
        state.last_updated = now.isoformat()
        self._persist(context, state)
        return state

    def complete_plan(
        self,
        context: ConversationContext,
    ) -> Optional[PlanState]:
        """
        Mark the plan as completed regardless of current step.

        Args:
            context: Conversation context to update.

        Returns:
            Updated ``PlanState``, or ``None`` if no plan exists.
        """
        state = self.get_state(context)
        if not state:
            logger.debug("complete_plan called but no plan exists — no-op")
            return None

        now = datetime.utcnow()
        state.status = "completed"
        state.last_updated = now.isoformat()
        self._persist(context, state)
        logger.info("Plan '%s' explicitly completed", state.title)
        return state

    def clear(self, context: ConversationContext) -> None:
        """
        Remove plan state from *context*, returning to idle.

        Args:
            context: Conversation context to clear.
        """
        context.metadata.pop(_PLAN_STATE_KEY, None)
        logger.debug("Plan state cleared")

    def touch(
        self,
        context: ConversationContext,
        expiry_minutes: int = _DEFAULT_PLAN_EXPIRY_MINUTES,
    ) -> None:
        """
        Refresh the expiry timestamp of an active plan.

        Called at the start of every conversation turn while a plan is active,
        so that user interaction keeps the plan alive.

        Args:
            context: Conversation context to update.
            expiry_minutes: New TTL from now in minutes.
        """
        raw = context.metadata.get(_PLAN_STATE_KEY)
        if not raw:
            return
        now = datetime.utcnow()
        raw["expires_at"] = (now + timedelta(minutes=expiry_minutes)).isoformat()
        raw["last_updated"] = now.isoformat()
        context.metadata[_PLAN_STATE_KEY] = raw

    def is_expired(self, state: PlanState) -> bool:
        """
        Return ``True`` if *state* has passed its ``expires_at`` timestamp.

        A state without ``expires_at`` is considered non-expiring.

        Args:
            state: The ``PlanState`` to check.

        Returns:
            ``True`` if expired, ``False`` otherwise.
        """
        if not state.expires_at:
            return False
        try:
            return datetime.fromisoformat(state.expires_at) < datetime.utcnow()
        except (ValueError, TypeError):
            logger.warning(
                "Could not parse plan expires_at '%s' — treating as non-expired",
                state.expires_at,
            )
            return False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _persist(self, context: ConversationContext, state: PlanState) -> None:
        """Write *state* to *context.metadata* under the canonical key."""
        context.metadata[_PLAN_STATE_KEY] = state.to_dict()
