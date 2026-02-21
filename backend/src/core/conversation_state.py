"""
Conversation state management for Phase 5.1: Robust Character Coordination.

``ConversationStateManager`` is the single source of truth for reading and
writing ``CoordinationState`` into ``ConversationContext.metadata``.  All
access to the coordination metadata keys goes through this class so that
naming conventions and serialisation details are in one place.

Backward compatibility:
    Reads the ``deferred_tasks`` / ``deferred_tasks_expires_at`` keys written
    by the Phase 5 pipeline and converts them to a ``CoordinationState`` in
    ``AWAITING_ACTION`` mode so that old in-flight sessions are handled
    gracefully after a Phase 5.1 deployment.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from models.message import ConversationContext
from models.routing import CoordinationMode, CoordinationState

logger = logging.getLogger(__name__)

# Metadata key under which ``CoordinationState`` is persisted.
_STATE_KEY = "coordination_state"

# Default expiry window in minutes for a pending coordination state.
_DEFAULT_EXPIRY_MINUTES = 20


class ConversationStateManager:
    """
    Reads and writes ``CoordinationState`` on a ``ConversationContext``.

    All public methods are intentionally synchronous because ``context`` is
    an in-process, in-memory object — no I/O is involved.

    Usage::

        state_manager = ConversationStateManager()

        # Read current state
        state = state_manager.get_state(context)

        # Transition to PROPOSING
        state_manager.set_proposing(
            context,
            pending_character="hank",
            pending_task="Add items to shopping list",
            proposed_summary="Southern Fried Chicken dinner",
            items=["chicken", "flour", "buttermilk"],
        )

        # Later, after user confirms → AWAITING_ACTION
        state_manager.set_awaiting_action(context, "hank", "Add items to shopping list")

        # After secondary character executes → back to IDLE
        state_manager.clear(context)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_state(self, context: ConversationContext) -> CoordinationState:
        """
        Return the current ``CoordinationState`` for *context*.

        If the new ``coordination_state`` key is absent, falls back to
        reading the legacy Phase 5 ``deferred_tasks`` keys so that
        in-flight sessions survive an upgrade.

        Args:
            context: The conversation context to read from.

        Returns:
            Current ``CoordinationState`` (never ``None``; returns an IDLE
            state when nothing is stored).
        """
        raw = context.metadata.get(_STATE_KEY)
        if raw:
            try:
                return CoordinationState.from_dict(raw)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to deserialise coordination_state: %s — returning IDLE", exc
                )
                return CoordinationState()

        # Backward-compat: convert legacy deferred_tasks to CoordinationState
        return self._read_legacy_state(context)

    def set_proposing(
        self,
        context: ConversationContext,
        pending_character: str,
        pending_task: str,
        proposed_summary: str,
        items: Optional[list] = None,
        expiry_minutes: int = _DEFAULT_EXPIRY_MINUTES,
    ) -> CoordinationState:
        """
        Transition to ``PROPOSING`` mode and persist to *context*.

        Call this after the primary character has presented an option to the
        user and a follow-up action by a secondary character is expected once
        the user confirms.

        Args:
            context: Conversation context to update.
            pending_character: Secondary character who will act on confirmation.
            pending_task: Description of the pending secondary task.
            proposed_summary: Short summary of what was proposed to the user.
            items: Optional list of items associated with the task.
            expiry_minutes: Minutes until the state auto-expires (default 20).

        Returns:
            The new ``CoordinationState``.
        """
        now = datetime.utcnow()
        state = CoordinationState(
            mode=CoordinationMode.PROPOSING,
            pending_character=pending_character,
            pending_task=pending_task,
            pending_items=list(items) if items else [],
            proposed_summary=proposed_summary,
            expires_at=(now + timedelta(minutes=expiry_minutes)).isoformat(),
            last_updated=now.isoformat(),
        )
        self._persist(context, state)
        logger.debug(
            "Coordination state → PROPOSING (pending=%s, task='%s')",
            pending_character,
            pending_task,
        )
        return state

    def set_awaiting_action(
        self,
        context: ConversationContext,
        pending_character: str,
        pending_task: str,
        items: Optional[list] = None,
        expiry_minutes: int = _DEFAULT_EXPIRY_MINUTES,
    ) -> CoordinationState:
        """
        Transition to ``AWAITING_ACTION`` mode and persist to *context*.

        Call this when the user has confirmed the proposal and the secondary
        character should execute on the next suitable turn.

        Args:
            context: Conversation context to update.
            pending_character: Secondary character who will act next.
            pending_task: Description of the task to execute.
            items: Optional list of items associated with the task.
            expiry_minutes: Minutes until the state auto-expires (default 20).

        Returns:
            The new ``CoordinationState``.
        """
        now = datetime.utcnow()
        state = CoordinationState(
            mode=CoordinationMode.AWAITING_ACTION,
            pending_character=pending_character,
            pending_task=pending_task,
            pending_items=list(items) if items else [],
            expires_at=(now + timedelta(minutes=expiry_minutes)).isoformat(),
            last_updated=now.isoformat(),
        )
        self._persist(context, state)
        logger.debug(
            "Coordination state → AWAITING_ACTION (pending=%s, task='%s')",
            pending_character,
            pending_task,
        )
        return state

    def clear(self, context: ConversationContext) -> None:
        """
        Return to ``IDLE`` and remove all coordination state from *context*.

        Also removes the legacy Phase 5 deferred-task keys if present.

        Args:
            context: Conversation context to clear.
        """
        context.metadata.pop(_STATE_KEY, None)
        # Remove legacy Phase 5 keys for cleanliness
        context.metadata.pop("deferred_tasks", None)
        context.metadata.pop("deferred_tasks_expires_at", None)
        context.metadata.pop("deferred_tasks_trigger_intent", None)
        logger.debug("Coordination state → IDLE (cleared)")

    def is_expired(self, state: CoordinationState) -> bool:
        """
        Return ``True`` if *state* has passed its expiry timestamp.

        A state without an ``expires_at`` field is considered non-expiring
        (returns ``False``).

        Args:
            state: The ``CoordinationState`` to check.

        Returns:
            ``True`` if expired, ``False`` otherwise (including when
            ``expires_at`` is absent or unparseable).
        """
        if not state.expires_at:
            return False
        try:
            return datetime.fromisoformat(state.expires_at) < datetime.utcnow()
        except (ValueError, TypeError):
            logger.warning(
                "Could not parse expires_at '%s' — treating as non-expired",
                state.expires_at,
            )
            return False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _persist(self, context: ConversationContext, state: CoordinationState) -> None:
        """Write *state* to *context.metadata* under the canonical key."""
        context.metadata[_STATE_KEY] = state.to_dict()

    def _read_legacy_state(self, context: ConversationContext) -> CoordinationState:
        """
        Convert Phase 5 ``deferred_tasks`` metadata into a ``CoordinationState``.

        If no legacy keys are present, returns a plain IDLE state.
        """
        deferred = context.metadata.get("deferred_tasks")
        if not deferred:
            return CoordinationState()

        expires_at = context.metadata.get("deferred_tasks_expires_at")
        first = deferred[0] if deferred else {}

        state = CoordinationState(
            mode=CoordinationMode.AWAITING_ACTION,
            pending_character=first.get("character", "hank"),
            pending_task=first.get("task_description", ""),
            expires_at=expires_at,
            last_updated=None,
        )
        logger.debug(
            "Converted legacy deferred_tasks to CoordinationState (mode=AWAITING_ACTION)"
        )
        return state
