"""
Tests for Phase 5.1 Milestone 4: Full Wiring & End-to-End Validation.

Covers:
- ConversationManager.__init__: Phase 5.1 dep injection (no feature flags)
- Router is always called (single code path)
- _orchestrate_character_turn execution path via handle_user_message:
  - US1: request_handoff tool call → two character fragments same turn
  - US2: two-turn confirm → pending state + secondary execution on affirmation
  - US3: direct follow-on ("add to my list") → hank responds, not delilah
  - US4: topic change → pending state cleared, no leaked action
  - US5: request_handoff tool call → secondary character executes
- _build_secondary_task helper
- _execute_secondary_and_assemble helper
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.conversation_manager import ConversationManager
from core.conversation_state import ConversationStateManager
from core.character_executor import CharacterExecutor, CharacterResponse
from core.conversation_router import ConversationRouter
from core.turn_classifier import TurnClassifier
from models.message import ConversationContext, Message
from models.routing import (
    CoordinationMode,
    CoordinationState,
    PendingFollowup,
    RoutingDecision,
    TurnClassification,
    TurnType,
)


# ===========================================================================
# Helpers
# ===========================================================================


def _make_llm(content="Hello sugar!", tool_calls=None):
    """Build a mock LLMIntegration that always returns a fixed response."""
    llm = MagicMock()
    llm.generate_response.return_value = {
        "content": content,
        "tool_calls": tool_calls,
        "usage": {"total_tokens": 20},
        "response_time": 0.05,
        "finish_reason": "stop",
    }
    return llm


def _make_executor(character="delilah", text="Hello sugar!", handoff_signal=None):
    """Build a mock CharacterExecutor.execute coroutine."""
    executor = MagicMock(spec=CharacterExecutor)
    executor.execute = AsyncMock(
        return_value=CharacterResponse(
            character=character,
            text=text,
            voice_mode="warm_baseline",
            tool_calls_made=0,
            handoff_signal=handoff_signal,
        )
    )
    return executor


def _make_router(primary="delilah", pending_followup=None, rationale="test"):
    """Build a mock ConversationRouter that always returns a fixed decision."""
    router = MagicMock(spec=ConversationRouter)
    router.route.return_value = RoutingDecision(
        primary_character=primary,
        pending_followup=pending_followup,
        rationale=rationale,
    )
    return router


def _make_classifier(turn_type=TurnType.NEW_REQUEST, confidence=0.9):
    """Build a mock TurnClassifier that returns a fixed classification."""
    clf = MagicMock(spec=TurnClassifier)
    clf.classify.return_value = TurnClassification(
        turn_type=turn_type, confidence=confidence, reasoning="test"
    )
    return clf


def _make_memory_manager():
    mm = MagicMock()
    mm.load_user_state.return_value = MagicMock(
        story_progress=MagicMock(current_chapter=2),
        conversation_history=MagicMock(messages=[]),
    )
    mm.add_conversation_message = MagicMock()
    mm.increment_interaction_count = MagicMock()
    return mm


def _make_cm(
    executor=None,
    router=None,
    classifier=None,
    state_manager=None,
    memory_manager=None,
):
    """Build a ConversationManager with all Phase 5.1 deps injected as mocks."""
    llm = _make_llm()
    cs = MagicMock()
    cs.select_voice_mode.return_value = MagicMock(
        mode=MagicMock(name="warm_baseline"), confidence=0.8
    )
    cs.build_system_prompt.return_value = "You are Delilah."
    tool_system = MagicMock()
    tool_system.list_tools.return_value = []
    tool_system.get_openai_functions.return_value = []
    story_engine = MagicMock()
    mm = memory_manager or _make_memory_manager()

    cm = ConversationManager(
        llm_integration=llm,
        character_system=cs,
        tool_system=tool_system,
        story_engine=story_engine,
        memory_manager=mm,
        state_manager=state_manager or ConversationStateManager(),
        turn_classifier=classifier or _make_classifier(),
        conversation_router=router or _make_router(),
        character_executor=executor or _make_executor(),
    )
    return cm


# ===========================================================================
# ConversationManager.__init__ — Phase 5.1 params
# ===========================================================================


class TestConversationManagerInit:
    def test_state_manager_injected(self):
        sm = ConversationStateManager()
        cm = _make_cm(state_manager=sm)
        assert cm.state_manager is sm

    def test_turn_classifier_injected(self):
        clf = _make_classifier()
        cm = _make_cm(classifier=clf)
        assert cm.turn_classifier is clf

    def test_conversation_router_injected(self):
        router = _make_router()
        cm = _make_cm(router=router)
        assert cm.conversation_router is router

    def test_character_executor_injected(self):
        exe = _make_executor()
        cm = _make_cm(executor=exe)
        assert cm.character_executor is exe

    def test_no_legacy_flags(self):
        """enable_phase51 and enable_phase45 flags no longer exist."""
        cm = _make_cm()
        assert not hasattr(cm, "enable_phase51")
        assert not hasattr(cm, "enable_phase45")


# ===========================================================================
# Router is always called
# ===========================================================================


class TestRouterAlwaysCalled:
    @pytest.mark.asyncio
    async def test_router_called_on_every_message(self):
        """The router is always called — there is no feature flag bypass."""
        router = _make_router()
        cm = _make_cm(router=router)
        result = await cm.handle_user_message(
            session_id="s1", user_message="hello", user_id="u1"
        )
        router.route.assert_called_once()
        assert result["metadata"].get("phase51") is True


# ===========================================================================
# US1: Single-message multi-task → two character fragments
# ===========================================================================


class TestUS1SingleMessageMultiTask:
    @pytest.mark.asyncio
    async def test_two_fragments_returned_when_router_has_followup(self):
        """
        US1: "Set timer and add milk to my list"
        Delilah handles the timer and explicitly calls request_handoff for Hank
        to add the item.  Response should contain two fragments.
        """
        handoff_signal = {
            "to_character": "hank",
            "task_summary": "Add milk to the shopping list",
            "items": ["milk"],
        }
        executor = MagicMock(spec=CharacterExecutor)
        # First call → delilah (with handoff_signal), second call → hank
        executor.execute = AsyncMock(side_effect=[
            CharacterResponse(character="delilah", text="Timer set, sugar!", voice_mode="deadpan",
                              tool_calls_made=1, handoff_signal=handoff_signal),
            CharacterResponse(character="hank", text="Aye, milk's on the list.", voice_mode="working",
                              tool_calls_made=1, handoff_signal=None),
        ])

        router = _make_router(primary="delilah", pending_followup=None)
        cm = _make_cm(executor=executor, router=router)
        result = await cm.handle_user_message(
            session_id="s1", user_message="Set timer and add milk to list", user_id="u1"
        )

        assert result["metadata"]["phase51"] is True
        fragments = result["metadata"]["fragments"]
        assert len(fragments) == 2
        chars = {f["character"] for f in fragments}
        assert "delilah" in chars
        assert "hank" in chars

    @pytest.mark.asyncio
    async def test_full_text_contains_both_responses(self):
        handoff_signal = {
            "to_character": "hank",
            "task_summary": "Add milk to the shopping list",
            "items": ["milk"],
        }
        executor = MagicMock(spec=CharacterExecutor)
        executor.execute = AsyncMock(side_effect=[
            CharacterResponse(character="delilah", text="Timer set!", voice_mode="deadpan",
                              tool_calls_made=0, handoff_signal=handoff_signal),
            CharacterResponse(character="hank", text="Aye, milk added.", voice_mode="working",
                              tool_calls_made=0, handoff_signal=None),
        ])
        router = _make_router(primary="delilah", pending_followup=None)
        cm = _make_cm(executor=executor, router=router)
        result = await cm.handle_user_message(
            session_id="s1", user_message="timer and list", user_id="u1"
        )
        assert "Timer set!" in result["text"]
        assert "Aye, milk added." in result["text"]


# ===========================================================================
# US2: Two-turn confirm → pending state + affirmation triggers secondary
# ===========================================================================


class TestUS2TwoTurnConfirm:
    @pytest.mark.asyncio
    async def test_pending_state_stored_after_turn1(self):
        """
        Turn 1: Router returns pending_followup=hank but Delilah doesn't call
        request_handoff yet → state is set to PROPOSING with pending hank.
        """
        followup = PendingFollowup(character="hank", task_summary="Add ingredients to list", source="router")
        router = _make_router(primary="delilah", pending_followup=followup)
        executor = _make_executor("delilah", "What flavours do you fancy?")

        sm = ConversationStateManager()
        cm = _make_cm(executor=executor, router=router, state_manager=sm)

        result = await cm.handle_user_message(
            session_id="s1", user_message="Plan dinner for Sunday", user_id="u1"
        )
        # Single character turn with no immediate followup execution
        assert result["metadata"]["phase51"] is True
        # Check state was stored
        ctx = cm.conversations["s1"]
        state = sm.get_state(ctx)
        assert state.mode == CoordinationMode.PROPOSING
        assert state.pending_character == "hank"

    @pytest.mark.asyncio
    async def test_affirmation_on_turn2_executes_secondary(self):
        """
        Turn 2: User says "yes!" with PROPOSING state → secondary (hank) runs.
        """
        sm = ConversationStateManager()
        # Pre-seed state
        ctx = ConversationContext(session_id="s2", user_id="u1")
        sm.set_proposing(ctx, pending_character="hank", pending_task="Add items to list",
                         proposed_summary="Fried Chicken ingredients: chicken, flour...")

        classifier = _make_classifier(turn_type=TurnType.AFFIRMATION, confidence=0.95)

        executor = MagicMock(spec=CharacterExecutor)
        executor.execute = AsyncMock(
            return_value=CharacterResponse(
                character="hank", text="Aye, list is set.", voice_mode="working",
                tool_calls_made=1, handoff_signal=None
            )
        )

        cm = _make_cm(executor=executor, classifier=classifier, state_manager=sm)
        # Inject pre-seeded context
        cm.conversations["s2"] = ctx

        result = await cm.handle_user_message(
            session_id="s2", user_message="yes!", user_id="u1"
        )
        assert result["metadata"]["phase51"] is True
        assert "hank" in result["metadata"]["characters"]

    @pytest.mark.asyncio
    async def test_state_cleared_after_secondary_execution(self):
        """After secondary runs on affirmation, state returns to IDLE."""
        sm = ConversationStateManager()
        ctx = ConversationContext(session_id="s3", user_id="u1")
        sm.set_proposing(ctx, pending_character="hank", pending_task="Add to list",
                         proposed_summary="Fried chicken recipe")

        classifier = _make_classifier(turn_type=TurnType.AFFIRMATION)
        executor = _make_executor("hank", "Aye, done.")

        cm = _make_cm(executor=executor, classifier=classifier, state_manager=sm)
        cm.conversations["s3"] = ctx

        await cm.handle_user_message(session_id="s3", user_message="yes", user_id="u1")

        state = sm.get_state(ctx)
        assert state.mode == CoordinationMode.IDLE


# ===========================================================================
# US3: Direct follow-on → hank responds, not delilah
# ===========================================================================


class TestUS3DirectFollowon:
    @pytest.mark.asyncio
    async def test_add_to_list_routes_to_hank(self):
        """
        "Add those to my list" → router returns primary=hank (list domain).
        """
        router = _make_router(primary="hank", pending_followup=None)
        executor = _make_executor("hank", "Aye, Cap'n. Items added to the list.")

        cm = _make_cm(executor=executor, router=router)
        result = await cm.handle_user_message(
            session_id="s1", user_message="Add those chicken ingredients to my list",
            user_id="u1"
        )

        assert result["metadata"]["phase51"] is True
        assert result["metadata"]["characters"] == ["hank"]

    @pytest.mark.asyncio
    async def test_executor_called_with_hank(self):
        router = _make_router(primary="hank")
        executor = MagicMock(spec=CharacterExecutor)
        executor.execute = AsyncMock(
            return_value=CharacterResponse(
                character="hank", text="Done.", voice_mode="working",
                tool_calls_made=0, handoff_signal=None
            )
        )
        cm = _make_cm(executor=executor, router=router)
        await cm.handle_user_message(
            session_id="s1", user_message="Add those to my list", user_id="u1"
        )
        call_kwargs = executor.execute.call_args[1]
        assert call_kwargs["character"] == "hank"


# ===========================================================================
# US4: Topic change clears pending state
# ===========================================================================


class TestUS4TopicChangeClearsState:
    @pytest.mark.asyncio
    async def test_new_request_clears_proposing_state(self):
        sm = ConversationStateManager()
        ctx = ConversationContext(session_id="s4", user_id="u1")
        sm.set_proposing(ctx, pending_character="hank", pending_task="Add to list",
                         proposed_summary="Chicken recipe")

        # TurnClassifier says NEW_REQUEST (topic change)
        classifier = _make_classifier(turn_type=TurnType.NEW_REQUEST)
        executor = _make_executor("delilah", "What's the weather?")
        router = _make_router(primary="delilah")

        cm = _make_cm(executor=executor, classifier=classifier, router=router, state_manager=sm)
        cm.conversations["s4"] = ctx

        result = await cm.handle_user_message(
            session_id="s4", user_message="What's the weather today?", user_id="u1"
        )

        # State must be IDLE (cleared)
        state = sm.get_state(ctx)
        assert state.mode == CoordinationMode.IDLE
        # Only one character (delilah) responded
        assert result["metadata"]["characters"] == ["delilah"]

    @pytest.mark.asyncio
    async def test_rejection_clears_proposing_state(self):
        sm = ConversationStateManager()
        ctx = ConversationContext(session_id="s5", user_id="u1")
        sm.set_proposing(ctx, pending_character="hank", pending_task="Add to list",
                         proposed_summary="Chicken recipe")

        classifier = _make_classifier(turn_type=TurnType.REJECTION)
        executor = _make_executor("delilah", "No problem, darlin'.")
        router = _make_router(primary="delilah")

        cm = _make_cm(executor=executor, classifier=classifier, router=router, state_manager=sm)
        cm.conversations["s5"] = ctx

        await cm.handle_user_message(
            session_id="s5", user_message="actually never mind", user_id="u1"
        )

        state = sm.get_state(ctx)
        assert state.mode == CoordinationMode.IDLE


# ===========================================================================
# US5: request_handoff tool call → secondary character executes
# ===========================================================================


class TestUS5HandoffTool:
    @pytest.mark.asyncio
    async def test_handoff_signal_triggers_secondary(self):
        """
        Delilah calls request_handoff(to_character=hank, ...) →
        CharacterExecutor surfaces this in handoff_signal →
        orchestrator runs Hank.
        """
        handoff_signal = {
            "to_character": "hank",
            "task_summary": "Add Southern Fried Chicken ingredients to the list",
            "items": ["chicken", "buttermilk", "flour"],
        }
        executor = MagicMock(spec=CharacterExecutor)
        executor.execute = AsyncMock(side_effect=[
            CharacterResponse(
                character="delilah",
                text="Here's your chicken recipe! Let me pass this to Hank.",
                voice_mode="passionate",
                tool_calls_made=1,
                handoff_signal=handoff_signal,
            ),
            CharacterResponse(
                character="hank",
                text="Aye, got 'em on the list.",
                voice_mode="working",
                tool_calls_made=1,
                handoff_signal=None,
            ),
        ])

        router = _make_router(primary="delilah", pending_followup=None)
        cm = _make_cm(executor=executor, router=router)

        result = await cm.handle_user_message(
            session_id="s1",
            user_message="Plan a fried chicken dinner and add to my list",
            user_id="u1",
        )

        assert result["metadata"]["phase51"] is True
        fragments = result["metadata"]["fragments"]
        assert len(fragments) == 2
        assert fragments[0]["character"] == "delilah"
        assert fragments[1]["character"] == "hank"

    @pytest.mark.asyncio
    async def test_handoff_signal_preferred_over_router_followup(self):
        """
        When both handoff_signal and router pending_followup exist, the
        handoff_signal (explicit tool call) takes precedence.
        """
        handoff_signal = {
            "to_character": "hank",
            "task_summary": "Add items from Delilah to list",
            "items": ["butter", "flour"],
        }
        # Router also has a followup (should be overridden)
        router_followup = PendingFollowup(character="hank", task_summary="Router followup", source="router")
        router = _make_router(primary="delilah", pending_followup=router_followup)

        executor = MagicMock(spec=CharacterExecutor)
        executor.execute = AsyncMock(side_effect=[
            CharacterResponse(
                character="delilah", text="Recipe ready!", voice_mode="passionate",
                tool_calls_made=1, handoff_signal=handoff_signal
            ),
            CharacterResponse(
                character="hank", text="Aye, sorted.", voice_mode="working",
                tool_calls_made=0, handoff_signal=None
            ),
        ])

        cm = _make_cm(executor=executor, router=router)
        result = await cm.handle_user_message(
            session_id="s1", user_message="Plan dinner and add items", user_id="u1"
        )

        fragments = result["metadata"]["fragments"]
        assert len(fragments) == 2
        # Hank ran second (from handoff_signal, not router)
        assert fragments[1]["character"] == "hank"
        # Executor called twice
        assert executor.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_secondary_execution_clears_state(self):
        """After handoff tool execution, coordination state is IDLE."""
        handoff_signal = {"to_character": "hank", "task_summary": "Add to list", "items": []}
        executor = MagicMock(spec=CharacterExecutor)
        executor.execute = AsyncMock(side_effect=[
            CharacterResponse(character="delilah", text="Done!", voice_mode="warm_baseline",
                              tool_calls_made=1, handoff_signal=handoff_signal),
            CharacterResponse(character="hank", text="Aye.", voice_mode="working",
                              tool_calls_made=0, handoff_signal=None),
        ])
        sm = ConversationStateManager()
        cm = _make_cm(executor=executor, state_manager=sm)

        await cm.handle_user_message(session_id="s1", user_message="test", user_id="u1")

        ctx = cm.conversations["s1"]
        state = sm.get_state(ctx)
        assert state.mode == CoordinationMode.IDLE


# ===========================================================================
# _build_secondary_task helper
# ===========================================================================


class TestBuildSecondaryTask:
    def _cm(self):
        return _make_cm()

    def test_items_injected_when_present(self):
        cm = self._cm()
        followup = {"task_summary": "Add ingredients", "items": ["chicken", "flour"]}
        result = cm._build_secondary_task(followup, primary_text="Here is your recipe.")
        assert "chicken" in result
        assert "flour" in result

    def test_no_items_uses_primary_excerpt(self):
        cm = self._cm()
        followup = {"task_summary": "Handle logistics", "items": []}
        primary = "Delilah says you should add these: butter, eggs, sugar."
        result = cm._build_secondary_task(followup, primary_text=primary)
        assert "Delilah says" in result

    def test_items_cap_at_20(self):
        cm = self._cm()
        items = [f"item{i}" for i in range(30)]
        followup = {"task_summary": "Add all items", "items": items}
        result = cm._build_secondary_task(followup, primary_text="")
        # Only first 20 items should appear
        assert "item19" in result
        assert "item20" not in result

    def test_empty_everything_returns_task_summary(self):
        cm = self._cm()
        followup = {"task_summary": "Do something", "items": []}
        result = cm._build_secondary_task(followup, primary_text="")
        assert result == "Do something"


# ===========================================================================
# Error handling — secondary failure falls back to primary-only
# ===========================================================================


class TestSecondaryFailureFallback:
    @pytest.mark.asyncio
    async def test_secondary_execution_failure_returns_primary_only(self):
        """
        If the secondary character execution raises an exception, the response
        still contains the primary character's fragment.
        """
        followup = PendingFollowup(character="hank", task_summary="Add to list", source="router")
        router = _make_router(primary="delilah", pending_followup=followup)

        executor = MagicMock(spec=CharacterExecutor)
        executor.execute = AsyncMock(side_effect=[
            CharacterResponse(
                character="delilah", text="Here's the recipe!", voice_mode="passionate",
                tool_calls_made=0, handoff_signal=None
            ),
            RuntimeError("Hank's LLM call failed"),
        ])

        cm = _make_cm(executor=executor, router=router)
        result = await cm.handle_user_message(
            session_id="s1", user_message="Plan dinner and add ingredients", user_id="u1"
        )

        # Response should not raise — should be non-empty (primary fragment at minimum)
        assert result["text"], "Expected non-empty response even when secondary fails"


# ===========================================================================
# Phase 5.1 flag in log metadata
# ===========================================================================


class TestPhase51Metadata:
    @pytest.mark.asyncio
    async def test_metadata_phase51_true_when_enabled(self):
        cm = _make_cm()
        result = await cm.handle_user_message(
            session_id="s1", user_message="hello", user_id="u1"
        )
        assert result["metadata"].get("phase51") is True

    @pytest.mark.asyncio
    async def test_metadata_has_characters_list(self):
        cm = _make_cm()
        result = await cm.handle_user_message(
            session_id="s1", user_message="hello", user_id="u1"
        )
        assert "characters" in result["metadata"]
        assert isinstance(result["metadata"]["characters"], list)
        assert len(result["metadata"]["characters"]) >= 1

    @pytest.mark.asyncio
    async def test_metadata_has_fragments(self):
        cm = _make_cm()
        result = await cm.handle_user_message(
            session_id="s1", user_message="hello", user_id="u1"
        )
        assert "fragments" in result["metadata"]
        assert isinstance(result["metadata"]["fragments"], list)
