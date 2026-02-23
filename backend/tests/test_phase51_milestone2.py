"""
Tests for Phase 5.1 Milestone 2: TurnClassifier & ConversationRouter.

Covers:
- character_assignments.py: domain_description field, REGISTERED_HANDOFF_PAIRS
- turn_classifier.py: TurnClassifier — LLM classification, regex fallback, JSON parsing
- conversation_router.py: ConversationRouter — routing decisions, fallback, handoff pairs
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add src to path so imports match the backend module layout
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.character_assignments import (
    CHARACTER_DOMAIN_DESCRIPTIONS,
    REGISTERED_HANDOFF_PAIRS,
    CharacterAssignment,
    get_available_characters,
)
from core.conversation_router import (
    ConversationRouter,
    _build_character_roster,
    _build_handoff_section,
)
from core.turn_classifier import TurnClassifier
from models.routing import (
    CoordinationMode,
    CoordinationState,
    TurnClassification,
    TurnType,
    RoutingDecision,
)


def _extract_messages_from_call(mock_obj) -> list:
    """Extract the messages list from a mock LLM generate_response call."""
    call_args = mock_obj.generate_response.call_args
    if "messages" in call_args[1]:
        return call_args[1]["messages"]
    return call_args[0][0]


# ===========================================================================
# character_assignments.py — new fields
# ===========================================================================


class TestCharacterAssignmentDomainDescription:
    def test_field_has_default_empty_string(self):
        ca = CharacterAssignment(primary="delilah", fallback=None, confidence_threshold=0.5)
        assert ca.domain_description == ""

    def test_field_can_be_set(self):
        ca = CharacterAssignment(
            primary="delilah",
            fallback=None,
            confidence_threshold=0.5,
            domain_description="cooking, recipes",
        )
        assert ca.domain_description == "cooking, recipes"


class TestCharacterDomainDescriptions:
    def test_delilah_description_present(self):
        assert "delilah" in CHARACTER_DOMAIN_DESCRIPTIONS
        desc = CHARACTER_DOMAIN_DESCRIPTIONS["delilah"]
        assert "cooking" in desc.lower()
        assert len(desc) > 5

    def test_hank_description_present(self):
        assert "hank" in CHARACTER_DOMAIN_DESCRIPTIONS
        desc = CHARACTER_DOMAIN_DESCRIPTIONS["hank"]
        assert "list" in desc.lower() or "logistics" in desc.lower()
        assert len(desc) > 5

    def test_at_least_delilah_and_hank(self):
        assert "delilah" in CHARACTER_DOMAIN_DESCRIPTIONS
        assert "hank" in CHARACTER_DOMAIN_DESCRIPTIONS


class TestRegisteredHandoffPairs:
    def test_chapter_2_has_delilah_hank_pairs(self):
        pairs = REGISTERED_HANDOFF_PAIRS.get(2, [])
        assert ("delilah", "hank") in pairs

    def test_chapter_2_has_reverse_pair(self):
        pairs = REGISTERED_HANDOFF_PAIRS.get(2, [])
        assert ("hank", "delilah") in pairs

    def test_chapter_1_not_in_pairs(self):
        # Chapter 1 has only Delilah — no handoffs
        assert 1 not in REGISTERED_HANDOFF_PAIRS

    def test_chapter_3_extends_chapter_2(self):
        if 3 in REGISTERED_HANDOFF_PAIRS:
            ch2 = set(REGISTERED_HANDOFF_PAIRS[2])
            ch3 = set(REGISTERED_HANDOFF_PAIRS[3])
            assert ch2.issubset(ch3)


# ===========================================================================
# turn_classifier.py — TurnClassifier
# ===========================================================================


def _make_classifier(llm_response_content: str = "") -> TurnClassifier:
    """Build a TurnClassifier backed by a mock LLM."""
    llm = MagicMock()
    llm.generate_response.return_value = {
        "content": llm_response_content,
        "tool_calls": None,
    }
    return TurnClassifier(llm=llm)


def _llm_json(turn_type: str, confidence: float = 0.9, reasoning: str = "test") -> str:
    return json.dumps({"type": turn_type, "confidence": confidence, "reasoning": reasoning})


class TestTurnClassifierLLMPath:
    def test_affirmation_classification(self):
        classifier = _make_classifier(_llm_json("affirmation", 0.95, "user said yes"))
        result = classifier.classify("Sounds great!", [], None)
        assert result.turn_type == TurnType.AFFIRMATION
        assert result.confidence == 0.95
        assert result.reasoning == "user said yes"

    def test_new_request_classification(self):
        classifier = _make_classifier(_llm_json("new_request", 0.88))
        result = classifier.classify("What's the weather?", [], None)
        assert result.turn_type == TurnType.NEW_REQUEST
        assert result.confidence == 0.88

    def test_clarification_classification(self):
        classifier = _make_classifier(_llm_json("clarification", 0.75))
        result = classifier.classify("I meant for Sunday dinner", [], None)
        assert result.turn_type == TurnType.CLARIFICATION

    def test_rejection_classification(self):
        classifier = _make_classifier(_llm_json("rejection", 0.92))
        result = classifier.classify("Actually no, let's skip it", [], None)
        assert result.turn_type == TurnType.REJECTION

    def test_content_carrying_affirmation(self):
        """Phrase with content like 'Southern Fried Chicken sounds great' → AFFIRMATION."""
        classifier = _make_classifier(_llm_json("affirmation", 0.92))
        result = classifier.classify("Southern Fried Chicken sounds great", [], None)
        assert result.turn_type == TurnType.AFFIRMATION

    def test_history_passed_to_llm(self):
        llm = MagicMock()
        llm.generate_response.return_value = {
            "content": _llm_json("affirmation"),
            "tool_calls": None,
        }
        classifier = TurnClassifier(llm=llm)
        history = [
            {"role": "user", "content": "Can you plan a dinner?"},
            {"role": "assistant", "content": "Sure! What flavors?"},
        ]
        classifier.classify("Fried chicken sounds great", history, None)
        messages = _extract_messages_from_call(llm)
        # System prompt + history + user message = at least 4 messages
        assert len(messages) >= 4

    def test_proposed_summary_injected_into_prompt(self):
        llm = MagicMock()
        llm.generate_response.return_value = {
            "content": _llm_json("affirmation"),
            "tool_calls": None,
        }
        classifier = TurnClassifier(llm=llm)
        state = CoordinationState(
            mode=CoordinationMode.PROPOSING,
            proposed_summary="Southern Fried Chicken dinner",
        )
        classifier.classify("Sounds good!", [], state)
        messages = _extract_messages_from_call(llm)
        system_content = messages[0]["content"]
        assert "Southern Fried Chicken dinner" in system_content

    def test_unknown_turn_type_becomes_new_request(self):
        classifier = _make_classifier(json.dumps({"type": "banana", "confidence": 0.5}))
        result = classifier.classify("something", [], None)
        assert result.turn_type == TurnType.NEW_REQUEST

    def test_confidence_clamped_to_0_1(self):
        classifier = _make_classifier(json.dumps({"type": "affirmation", "confidence": 5.0}))
        result = classifier.classify("yes", [], None)
        assert result.confidence == 1.0

    def test_markdown_fenced_json_parsed(self):
        classifier = _make_classifier(
            "```json\n" + _llm_json("affirmation", 0.9) + "\n```"
        )
        result = classifier.classify("yes", [], None)
        assert result.turn_type == TurnType.AFFIRMATION

    def test_temperature_and_max_tokens_passed(self):
        llm = MagicMock()
        llm.generate_response.return_value = {
            "content": _llm_json("new_request"),
            "tool_calls": None,
        }
        classifier = TurnClassifier(llm=llm)
        classifier.classify("hello", [], None)
        call_kwargs = llm.generate_response.call_args[1]
        assert call_kwargs.get("temperature") == 0.0
        assert call_kwargs.get("max_tokens") == 80


class TestTurnClassifierRegexFallback:
    def test_llm_failure_falls_back_to_regex(self):
        llm = MagicMock()
        llm.generate_response.side_effect = RuntimeError("no connection")
        classifier = TurnClassifier(llm=llm)
        result = classifier.classify("yes please", [], None)
        assert result.turn_type == TurnType.AFFIRMATION

    def test_llm_failure_non_affirmation_becomes_new_request(self):
        llm = MagicMock()
        llm.generate_response.side_effect = RuntimeError("timeout")
        classifier = TurnClassifier(llm=llm)
        result = classifier.classify("What's the weather today?", [], None)
        assert result.turn_type == TurnType.NEW_REQUEST

    def test_llm_bad_json_falls_back(self):
        classifier = _make_classifier("NOT VALID JSON")
        result = classifier.classify("yes", [], None)
        # Falls back to regex — "yes" is an affirmation
        assert result.turn_type == TurnType.AFFIRMATION


# ===========================================================================
# conversation_router.py — helpers
# ===========================================================================


class TestBuildCharacterRoster:
    def test_includes_known_characters(self):
        roster = _build_character_roster(["delilah", "hank"])
        assert "delilah" in roster
        assert "hank" in roster
        assert "cooking" in roster.lower()

    def test_unknown_character_uses_name_as_domain(self):
        roster = _build_character_roster(["mystery_char"])
        assert "mystery_char" in roster


class TestBuildHandoffSection:
    def test_chapter_2_includes_delilah_hank(self):
        section = _build_handoff_section(["delilah", "hank"], chapter_id=2)
        assert "delilah" in section
        assert "hank" in section

    def test_chapter_1_no_handoffs(self):
        section = _build_handoff_section(["delilah"], chapter_id=1)
        assert "not available" in section.lower() or section == ""

    def test_unavailable_character_excluded_from_pairs(self):
        # Chapter 2 has (delilah, hank) but if hank is not available it's excluded
        section = _build_handoff_section(["delilah"], chapter_id=2)
        # No valid pairs — both sides must be available
        assert "hank" not in section or "not available" in section.lower()


# ===========================================================================
# conversation_router.py — ConversationRouter
# ===========================================================================


def _make_router(llm_response_content: str = "") -> ConversationRouter:
    """Build a ConversationRouter backed by a mock LLM."""
    llm = MagicMock()
    llm.generate_response.return_value = {
        "content": llm_response_content,
        "tool_calls": None,
    }
    return ConversationRouter(llm=llm)


def _routing_json(
    primary: str,
    followup_char: str = None,
    followup_task: str = "",
    rationale: str = "test",
) -> str:
    data: dict = {"primary_character": primary, "rationale": rationale}
    if followup_char:
        data["pending_followup"] = {
            "character": followup_char,
            "task_summary": followup_task,
        }
    return json.dumps(data)


class TestConversationRouterBasic:
    def test_single_character_no_followup(self):
        router = _make_router(_routing_json("delilah"))
        decision = router.route(
            user_message="Set a timer for 10 minutes",
            recent_history=[],
            available_characters=["delilah", "hank"],
            chapter_id=2,
        )
        assert decision.primary_character == "delilah"
        assert decision.pending_followup is None

    def test_hank_primary_no_followup(self):
        router = _make_router(_routing_json("hank"))
        decision = router.route(
            user_message="Add milk to my shopping list",
            recent_history=[],
            available_characters=["delilah", "hank"],
            chapter_id=2,
        )
        assert decision.primary_character == "hank"
        assert decision.pending_followup is None

    def test_with_pending_followup(self):
        router = _make_router(
            _routing_json("delilah", "hank", "Add ingredients to Sunday shopping list")
        )
        decision = router.route(
            user_message="Plan a meal and add the items to my list",
            recent_history=[],
            available_characters=["delilah", "hank"],
            chapter_id=2,
        )
        assert decision.primary_character == "delilah"
        assert decision.pending_followup is not None
        assert decision.pending_followup.character == "hank"
        assert "Sunday" in decision.pending_followup.task_summary

    def test_rationale_preserved(self):
        router = _make_router(_routing_json("delilah", rationale="meal planning domain"))
        decision = router.route("Plan dinner", [], ["delilah", "hank"], chapter_id=2)
        assert "meal" in decision.rationale.lower() or decision.rationale != ""

    def test_history_passed_to_llm(self):
        llm = MagicMock()
        llm.generate_response.return_value = {"content": _routing_json("delilah")}
        router = ConversationRouter(llm=llm)
        history = [
            {"role": "user", "content": "Can you plan a meal?"},
            {"role": "assistant", "content": "Sure!"},
        ]
        router.route("Fried chicken sounds great", history, ["delilah", "hank"], chapter_id=2)
        messages = _extract_messages_from_call(llm)
        assert len(messages) >= 4  # system + 2 history + user message

    def test_temperature_and_max_tokens(self):
        llm = MagicMock()
        llm.generate_response.return_value = {"content": _routing_json("delilah")}
        router = ConversationRouter(llm=llm)
        router.route("hello", [], ["delilah"], chapter_id=1)
        call_kwargs = llm.generate_response.call_args[1]
        assert call_kwargs.get("temperature") == 0.1
        assert call_kwargs.get("max_tokens") == 400


class TestConversationRouterFallback:
    def test_llm_failure_returns_delilah(self):
        llm = MagicMock()
        llm.generate_response.side_effect = RuntimeError("no connection")
        router = ConversationRouter(llm=llm)
        decision = router.route("anything", [], ["delilah", "hank"], chapter_id=2)
        assert decision.primary_character == "delilah"
        assert decision.pending_followup is None

    def test_bad_json_falls_back(self):
        router = _make_router("NOT VALID JSON")
        decision = router.route("anything", [], ["delilah", "hank"], chapter_id=2)
        assert decision.primary_character == "delilah"

    def test_unavailable_character_replaced_by_fallback(self):
        # LLM returns "rex" but rex is not in available_characters
        router = _make_router(_routing_json("rex", rationale="smart home"))
        decision = router.route("Turn on the lights", [], ["delilah", "hank"], chapter_id=2)
        assert decision.primary_character == "delilah"

    def test_empty_available_characters_uses_fallback(self):
        router = _make_router(_routing_json("delilah"))
        decision = router.route("hello", [], available_characters=[], chapter_id=1)
        assert decision.primary_character == "delilah"

    def test_pending_followup_with_unavailable_character_ignored(self):
        # pending_followup.character="rex" but rex not in available chars
        router = _make_router(_routing_json("delilah", "rex", "smart home task"))
        decision = router.route("Plan and control lights", [], ["delilah", "hank"], chapter_id=2)
        assert decision.pending_followup is None

    def test_markdown_fenced_json_parsed(self):
        router = _make_router("```json\n" + _routing_json("delilah") + "\n```")
        decision = router.route("hello", [], ["delilah"], chapter_id=1)
        assert decision.primary_character == "delilah"

    def test_empty_content_falls_back(self):
        # Reproduces the bug: model returns no content (e.g. gpt-5-mini with
        # max_completion_tokens too small) → router should fall back to delilah
        # with a clear error, not a cryptic JSONDecodeError.
        router = _make_router("")
        decision = router.route("How many teaspoons in a tablespoon?", [], ["delilah", "hank"], chapter_id=2)
        assert decision.primary_character == "delilah"
        assert decision.pending_followup is None
