"""
Turn classifier for Phase 5.1: Robust Character Coordination.

``TurnClassifier`` determines the conversational intent of the user's latest
message *relative to the current coordination state*.  It is only called when
the state is not IDLE (i.e., there is a pending proposal or pending action).

Classification uses a single, fast LLM call (temperature=0.0, max_tokens=80).
If the LLM call fails for any reason, the classifier falls back to the existing
``is_affirmation()`` regex to guarantee a safe classification without crashing.
"""

import json
import logging
from typing import Dict, List, Optional

from models.routing import CoordinationState, TurnClassification, TurnType
from core.utils import is_affirmation

logger = logging.getLogger(__name__)

# LLM parameters
_TEMPERATURE = 0.0
# 300 tokens leaves room for models that consume reasoning/thinking tokens
# internally before producing visible output (e.g. gpt-5-mini).  The JSON
# response itself is only ~50–60 tokens; the extra headroom prevents
# finish_reason=length with an empty content string.
_MAX_TOKENS = 1000

# Maximum character length for any single message content sent to the LLM.
_MAX_MSG_LEN = 200

# System prompt template for the turn classifier.
_SYSTEM_PROMPT_TEMPLATE = """\
You are a turn-classifier for a voice assistant multi-character system.
Given the recent conversation and what is currently pending, classify the user's
latest message as exactly one of:
  - affirmation: user is saying yes / confirming / accepting the prior proposal
  - new_request: user is asking for something unrelated to the current pending topic
  - clarification: user is adding context that refines the current pending topic
  - rejection: user is declining or cancelling the current pending topic

{pending_context}

Respond with valid JSON only, no extra text:
{{"type": "affirmation", "confidence": 0.92, "reasoning": "short explanation"}}\
"""


def _build_system_prompt(state: Optional[CoordinationState]) -> str:
    """Build the system prompt with or without a pending context block."""
    if state and state.proposed_summary:
        pending_context = f"Pending context: {state.proposed_summary}"
    elif state and state.pending_task:
        pending_context = f"Pending context: {state.pending_task}"
    else:
        pending_context = "Pending context: (none specified)"
    return _SYSTEM_PROMPT_TEMPLATE.format(pending_context=pending_context)


class TurnClassifier:
    """
    Classifies the user's latest message relative to the current coordination state.

    Only relevant when ``coordination_state.mode != IDLE`` — when the system is
    actively waiting for the user to confirm, clarify, or reject a prior proposal.

    Usage::

        classifier = TurnClassifier(llm=llm_integration)
        tc = classifier.classify(
            user_message="Southern Fried Chicken sounds great",
            recent_history=[...],
            coordination_state=current_state,
        )
        if tc.turn_type == TurnType.AFFIRMATION:
            ...

    Args:
        llm: An ``LLMIntegration`` instance (or compatible mock).
    """

    def __init__(self, llm):
        self.llm = llm

    def classify(
        self,
        user_message: str,
        recent_history: List[Dict],
        coordination_state: Optional[CoordinationState] = None,
    ) -> TurnClassification:
        """
        Classify the user's turn relative to *coordination_state*.

        Args:
            user_message: The user's latest message text.
            recent_history: Last 2–4 turns in ``[{"role": ..., "content": ...}]``
                format — used so the LLM has conversational context.
            coordination_state: Current ``CoordinationState`` (may be None or IDLE,
                but the caller should generally only call this when non-IDLE).

        Returns:
            A ``TurnClassification`` with ``turn_type``, ``confidence``, and
            ``reasoning``.  Falls back to a regex-based AFFIRMATION / NEW_REQUEST
            classification if the LLM call fails.
        """
        try:
            return self._classify_with_llm(user_message, recent_history, coordination_state)
        except (Exception,) as exc:  # noqa: BLE001 — intentional broad catch for LLM safety net
            logger.warning(
                "TurnClassifier: LLM call failed (%s) — falling back to regex", exc
            )
            return self._classify_with_regex(user_message)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _classify_with_llm(
        self,
        user_message: str,
        recent_history: List[Dict],
        coordination_state: Optional[CoordinationState],
    ) -> TurnClassification:
        """Call the LLM to classify the turn, then parse the JSON response."""
        system_prompt = _build_system_prompt(coordination_state)

        messages = [{"role": "system", "content": system_prompt}]

        # Include last 2 turns of history for context (up to 4 messages),
        # truncated to avoid token bloat from long assistant responses.
        # Also deduplicate: the user message is added to history before this
        # method is called, so without this guard it would appear twice.
        for msg in recent_history[-4:]:
            content = msg.get("content", "")[:_MAX_MSG_LEN]
            role = msg.get("role", "user")
            if role == "user" and content == user_message[:_MAX_MSG_LEN]:
                continue
            messages.append({"role": role, "content": content})

        # Append the current user message
        messages.append({"role": "user", "content": user_message[:_MAX_MSG_LEN]})

        logger.debug(
            "TurnClassifier: calling LLM (messages=%d, user_message=%r)",
            len(messages),
            user_message[:60],
        )
        response = self.llm.generate_response(
            messages=messages,
            temperature=_TEMPERATURE,
            max_tokens=_MAX_TOKENS,
        )

        raw = response.get("content", "") or ""
        finish_reason = response.get("finish_reason", "")
        if not raw and finish_reason == "length":
            raise ValueError(
                "LLM returned empty content with finish_reason=length — "
                f"max_tokens={_MAX_TOKENS} is too small for this model "
                "(likely consumed by internal reasoning tokens)"
            )
        logger.debug("TurnClassifier: LLM raw response: %r", raw[:500])
        classification = self._parse_llm_response(raw)
        logger.info(
            "TurnClassifier: classification — type=%r, confidence=%.2f, reasoning=%r",
            classification.turn_type,
            classification.confidence,
            classification.reasoning,
        )
        return classification

    def _parse_llm_response(self, raw: str) -> TurnClassification:
        """Parse the JSON response from the LLM into a TurnClassification."""
        # Strip markdown fences if the model wrapped the JSON
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        data = json.loads(cleaned)

        turn_type_str = data.get("type", "new_request").lower()
        try:
            turn_type = TurnType(turn_type_str)
        except ValueError:
            logger.warning(
                "TurnClassifier: unknown turn type '%s' — treating as NEW_REQUEST",
                turn_type_str,
            )
            turn_type = TurnType.NEW_REQUEST

        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
        reasoning = str(data.get("reasoning", ""))

        return TurnClassification(
            turn_type=turn_type,
            confidence=confidence,
            reasoning=reasoning,
        )

    def _classify_with_regex(self, user_message: str) -> TurnClassification:
        """
        Regex-based fallback when the LLM is unavailable.

        Uses the existing ``is_affirmation()`` helper to detect simple
        confirmations.  Everything else is treated as a NEW_REQUEST.
        """
        if is_affirmation(user_message):
            return TurnClassification(
                turn_type=TurnType.AFFIRMATION,
                confidence=0.7,
                reasoning="regex fallback: matched affirmation pattern",
            )
        return TurnClassification(
            turn_type=TurnType.NEW_REQUEST,
            confidence=0.6,
            reasoning="regex fallback: no affirmation pattern matched",
        )
