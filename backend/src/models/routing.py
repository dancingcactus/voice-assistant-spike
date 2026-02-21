"""
Routing data models for Phase 5.1: Robust Character Coordination.

This module defines the data structures used for conversation routing,
turn classification, and coordination state management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class TurnType(str, Enum):
    """
    Classification of the current user turn relative to coordination state.

    Used by TurnClassifier to determine whether the user is affirming a
    pending proposal, making a new unrelated request, asking for clarification,
    or rejecting the current proposal.
    """

    AFFIRMATION = "affirmation"
    """User is confirming / approving a previous proposal."""

    NEW_REQUEST = "new_request"
    """User is making an unrelated new request (clears pending state)."""

    CLARIFICATION = "clarification"
    """User is asking a clarifying question about the current proposal."""

    REJECTION = "rejection"
    """User is rejecting the current proposal."""


class CoordinationMode(str, Enum):
    """
    High-level state of the multi-character coordination pipeline.

    Tracks whether the system is idle, has just proposed an action to the
    user, or is actively waiting for the user to confirm before a second
    character executes.
    """

    IDLE = "idle"
    """No pending multi-character work. Normal single-character routing."""

    PROPOSING = "proposing"
    """Primary character has presented options; waiting for user input."""

    AWAITING_ACTION = "awaiting_action"
    """
    User has confirmed; secondary character is ready to act on the next
    affirmative turn.
    """


@dataclass
class TurnClassification:
    """
    Result of classifying a user turn against the current coordination state.

    Attributes:
        turn_type: Categorised type of this turn.
        confidence: Confidence score for the classification (0.0–1.0).
        reasoning: Short human-readable explanation of the classification.
    """

    turn_type: TurnType
    confidence: float
    reasoning: str

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dictionary."""
        return {
            "turn_type": self.turn_type.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


@dataclass
class PendingFollowup:
    """
    Describes a follow-up action that should be executed by a secondary character.

    Stored inside a ``RoutingDecision`` when the router determines that a second
    character should act after the primary character's turn.

    Attributes:
        character: The secondary character who should handle the follow-up.
        task_summary: Short description of the task the secondary character must do.
        source: How this follow-up was identified (e.g. ``"router"``, ``"handoff_tool"``).
        items: Optional list of items relevant to the task (e.g. ingredients for a
            shopping list).
    """

    character: str
    task_summary: str
    source: str
    items: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dictionary."""
        return {
            "character": self.character,
            "task_summary": self.task_summary,
            "source": self.source,
            "items": self.items,
        }


@dataclass
class RoutingDecision:
    """
    Decision produced by ``ConversationRouter`` for a single user turn.

    Attributes:
        primary_character: The character who should respond first.
        pending_followup: Optional second-character action to store in state after
            the primary responds.
        rationale: Short explanation of why this routing was chosen.
    """

    primary_character: str
    pending_followup: Optional[PendingFollowup] = None
    rationale: str = ""

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dictionary."""
        return {
            "primary_character": self.primary_character,
            "pending_followup": (
                self.pending_followup.to_dict() if self.pending_followup else None
            ),
            "rationale": self.rationale,
        }


@dataclass
class CoordinationState:
    """
    Persistent coordination state stored in ``ConversationContext.metadata``.

    Tracks what multi-character coordination is in progress so that
    ``ConversationStateManager`` can correctly route follow-up turns.

    Attributes:
        mode: Current coordination mode (IDLE / PROPOSING / AWAITING_ACTION).
        pending_character: Secondary character waiting to act (if any).
        pending_task: Description of the pending secondary task (if any).
        pending_items: Optional list of items associated with the pending task.
        proposed_summary: Short summary of what was proposed to the user.
        expires_at: ISO-format UTC timestamp after which the state expires silently.
        last_updated: ISO-format UTC timestamp of the last state mutation.
    """

    mode: CoordinationMode = CoordinationMode.IDLE
    pending_character: Optional[str] = None
    pending_task: Optional[str] = None
    pending_items: List[str] = field(default_factory=list)
    proposed_summary: Optional[str] = None
    expires_at: Optional[str] = None
    last_updated: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dictionary."""
        return {
            "mode": self.mode.value,
            "pending_character": self.pending_character,
            "pending_task": self.pending_task,
            "pending_items": self.pending_items,
            "proposed_summary": self.proposed_summary,
            "expires_at": self.expires_at,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CoordinationState":
        """Deserialise from a dictionary (as stored in ``context.metadata``)."""
        mode_str = data.get("mode", CoordinationMode.IDLE.value)
        try:
            mode = CoordinationMode(mode_str)
        except ValueError:
            mode = CoordinationMode.IDLE

        return cls(
            mode=mode,
            pending_character=data.get("pending_character"),
            pending_task=data.get("pending_task"),
            pending_items=data.get("pending_items", []),
            proposed_summary=data.get("proposed_summary"),
            expires_at=data.get("expires_at"),
            last_updated=data.get("last_updated"),
        )
