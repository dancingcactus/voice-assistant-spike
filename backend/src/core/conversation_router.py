"""
Conversation router for Phase 5.1: Robust Character Coordination.

``ConversationRouter`` decides which character should respond to a user message
and whether a second character should act after the primary responds (a
"pending followup").  It uses a single LLM call with full recent conversation
history so it can reason about cross-turn context (e.g., "add those to my
list" after a recipe discussion).

On any LLM failure, the router falls back to ``RoutingDecision(primary_character="delilah")``
and logs an ERROR — the conversation continues safely with the default character.

Registered handoff pairs (from ``character_assignments.REGISTERED_HANDOFF_PAIRS``)
are injected into the prompt so the LLM only proposes handoffs that are valid for
the current chapter.
"""

import json
import logging
from typing import Dict, List, Optional

from config.character_assignments import (
    CHARACTER_DOMAIN_DESCRIPTIONS,
    REGISTERED_HANDOFF_PAIRS,
)
from models.routing import CoordinationState, PendingFollowup, RoutingDecision

logger = logging.getLogger(__name__)

# LLM parameters
_TEMPERATURE = 0.1
_MAX_TOKENS = 150

# Default fallback character
_FALLBACK_CHARACTER = "delilah"

# System prompt template.
_SYSTEM_PROMPT_TEMPLATE = """\
You are the routing coordinator for a multi-character voice assistant.

Available characters and their domains:
{character_roster}

{handoff_section}

Given the conversation so far and the user's latest message, decide:
  1. Which character should respond first (primary_character)
  2. Whether a second character should act AFTER the primary responds
     (pending_followup — only when the conversation clearly spans two domains)

A pending_followup is appropriate when:
  - The user's message spans two character domains in one request
  - The primary character's response will produce content another character needs to act on
  - The user's message directly requests the secondary character's domain after the primary's

Do NOT set a pending_followup for speculative future needs. Only set it when the current
message clearly requires both characters.

Respond with valid JSON only, no extra text:
{{
  "primary_character": "delilah",
  "pending_followup": {{
    "character": "hank",
    "task_summary": "Add the meal items from Delilah's response to the shopping list"
  }},
  "rationale": "short explanation"
}}

Omit "pending_followup" entirely (or set to null) when only one character is needed.\
"""


def _build_character_roster(available_characters: List[str]) -> str:
    """Build the character roster block for the system prompt."""
    lines = []
    for char in available_characters:
        domain = CHARACTER_DOMAIN_DESCRIPTIONS.get(char, char)
        lines.append(f"  - {char}: {domain}")
    return "\n".join(lines)


def _build_handoff_section(available_characters: List[str], chapter_id: int) -> str:
    """Build the handoff instructions block for the system prompt."""
    pairs = REGISTERED_HANDOFF_PAIRS.get(chapter_id, [])
    # Filter to pairs where both characters are currently available
    valid_pairs = [
        (frm, to)
        for frm, to in pairs
        if frm in available_characters and to in available_characters
    ]
    if not valid_pairs:
        return "Note: Character handoffs are not available at this chapter."

    pair_strs = ", ".join(f"{frm} → {to}" for frm, to in valid_pairs)
    return (
        f"Registered handoff pairs for this chapter: {pair_strs}\n"
        "You may propose a pending_followup only for characters in these registered pairs."
    )


class ConversationRouter:
    """
    Routes a user message to the appropriate primary character and optionally
    records a pending follow-up for a second character.

    Usage::

        router = ConversationRouter(llm=llm_integration)
        decision = router.route(
            user_message="Plan a meal for Sunday and add the ingredients to my list",
            recent_history=[...],
            available_characters=["delilah", "hank"],
            chapter_id=2,
        )
        # decision.primary_character == "delilah"
        # decision.pending_followup.character == "hank"

    Args:
        llm: An ``LLMIntegration`` instance (or compatible mock).
    """

    def __init__(self, llm):
        self.llm = llm

    def route(
        self,
        user_message: str,
        recent_history: List[Dict],
        available_characters: List[str],
        chapter_id: int = 1,
        coordination_state: Optional[CoordinationState] = None,
    ) -> RoutingDecision:
        """
        Decide which character(s) should respond to *user_message*.

        Args:
            user_message: The user's latest message text.
            recent_history: Last 4–6 turns in ``[{"role": ..., "content": ...}]``
                format — gives the LLM full conversational context.
            available_characters: List of character IDs that are active in the
                current chapter (e.g. ``["delilah", "hank"]``).
            chapter_id: Current story chapter (controls registered handoff pairs).
            coordination_state: Current ``CoordinationState`` (for context; not
                mutated here).

        Returns:
            A ``RoutingDecision`` with ``primary_character``, optional
            ``pending_followup``, and a ``rationale`` string.  Falls back to
            ``RoutingDecision(primary_character="delilah")`` on any LLM failure.
        """
        # Validate available_characters — always need at least one
        if not available_characters:
            available_characters = [_FALLBACK_CHARACTER]

        try:
            return self._route_with_llm(
                user_message, recent_history, available_characters, chapter_id
            )
        except (Exception,) as exc:  # noqa: BLE001 — intentional broad catch for LLM safety net
            logger.error(
                "ConversationRouter: LLM call failed (%s) — falling back to '%s'",
                exc,
                _FALLBACK_CHARACTER,
            )
            return RoutingDecision(
                primary_character=_FALLBACK_CHARACTER,
                rationale="fallback: LLM router unavailable",
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _route_with_llm(
        self,
        user_message: str,
        recent_history: List[Dict],
        available_characters: List[str],
        chapter_id: int,
    ) -> RoutingDecision:
        """Build messages, call the LLM, and parse the routing decision."""
        roster = _build_character_roster(available_characters)
        handoff_section = _build_handoff_section(available_characters, chapter_id)
        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
            character_roster=roster,
            handoff_section=handoff_section,
        )

        messages = [{"role": "system", "content": system_prompt}]

        # Include up to 6 recent turns for context
        for msg in recent_history[-6:]:
            messages.append(
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            )

        messages.append({"role": "user", "content": user_message})

        logger.debug(
            "ConversationRouter: calling LLM (messages=%d, user_message=%r)",
            len(messages),
            user_message[:60],
        )
        response = self.llm.generate_response(
            messages=messages,
            temperature=_TEMPERATURE,
            max_tokens=_MAX_TOKENS,
        )

        raw = response.get("content", "") or ""
        if not raw:
            raise ValueError(
                "Router LLM returned empty content — check that OPENAI_MODEL is set to a "
                "supported chat model (e.g. gpt-4o-mini) and that max_tokens is sufficient."
            )
        logger.info("ConversationRouter: LLM raw response: %r", raw[:500])
        decision = self._parse_llm_response(raw, available_characters)
        logger.info(
            "ConversationRouter: routing decision — primary=%r, followup=%r, rationale=%r",
            decision.primary_character,
            decision.pending_followup.character if decision.pending_followup else None,
            decision.rationale,
        )
        return decision

    def _parse_llm_response(
        self, raw: str, available_characters: List[str]
    ) -> RoutingDecision:
        """Parse the JSON response from the LLM into a RoutingDecision."""
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        data = json.loads(cleaned)

        # --- primary_character ---
        primary = str(data.get("primary_character", _FALLBACK_CHARACTER)).lower()
        if primary not in available_characters:
            logger.warning(
                "ConversationRouter: LLM chose '%s' which is not in available characters %s"
                " — using fallback '%s'",
                primary,
                available_characters,
                _FALLBACK_CHARACTER,
            )
            primary = _FALLBACK_CHARACTER

        # --- pending_followup ---
        pending_followup: Optional[PendingFollowup] = None
        raw_followup = data.get("pending_followup")
        if raw_followup and isinstance(raw_followup, dict):
            followup_char = str(raw_followup.get("character", "")).lower()
            followup_task = str(raw_followup.get("task_summary", ""))
            followup_items = raw_followup.get("items", [])
            if isinstance(followup_items, list):
                followup_items = [str(i) for i in followup_items]
            else:
                followup_items = []

            if followup_char and followup_char in available_characters:
                pending_followup = PendingFollowup(
                    character=followup_char,
                    task_summary=followup_task,
                    source="router",
                    items=followup_items,
                )
            elif followup_char:
                logger.warning(
                    "ConversationRouter: pending followup character '%s' not in available %s"
                    " — ignoring followup",
                    followup_char,
                    available_characters,
                )

        rationale = str(data.get("rationale", ""))

        return RoutingDecision(
            primary_character=primary,
            pending_followup=pending_followup,
            rationale=rationale,
        )
