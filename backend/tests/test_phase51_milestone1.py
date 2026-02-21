"""
Tests for Phase 5.1 Milestone 1: Models & Foundation.

Covers:
- routing.py: TurnType, TurnClassification, PendingFollowup, RoutingDecision,
  CoordinationMode, CoordinationState (including from_dict / to_dict)
- conversation_state.py: ConversationStateManager transitions,
  expiry logic, and backward-compat legacy key conversion
- character_executor.py: CharacterExecutor with mock LLM — tool loop,
  handoff signal detection, duplicate handoff rejection
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path so that module imports work the same way as the backend
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.message import ConversationContext
from models.routing import (
    CoordinationMode,
    CoordinationState,
    PendingFollowup,
    RoutingDecision,
    TurnClassification,
    TurnType,
)
from core.conversation_state import ConversationStateManager
from core.character_executor import CharacterExecutor, CharacterResponse


# ===========================================================================
# routing.py — TurnType
# ===========================================================================


class TestTurnType:
    def test_all_values_exist(self):
        assert TurnType.AFFIRMATION == "affirmation"
        assert TurnType.NEW_REQUEST == "new_request"
        assert TurnType.CLARIFICATION == "clarification"
        assert TurnType.REJECTION == "rejection"

    def test_is_string_enum(self):
        assert isinstance(TurnType.AFFIRMATION, str)


# ===========================================================================
# routing.py — TurnClassification
# ===========================================================================


class TestTurnClassification:
    def test_create_and_to_dict(self):
        tc = TurnClassification(
            turn_type=TurnType.AFFIRMATION,
            confidence=0.95,
            reasoning="User said 'sounds great'",
        )
        d = tc.to_dict()
        assert d["turn_type"] == "affirmation"
        assert d["confidence"] == 0.95
        assert "reasoning" in d

    def test_low_confidence(self):
        tc = TurnClassification(
            turn_type=TurnType.NEW_REQUEST, confidence=0.4, reasoning="ambiguous"
        )
        assert tc.confidence == 0.4


# ===========================================================================
# routing.py — PendingFollowup
# ===========================================================================


class TestPendingFollowup:
    def test_create_with_items(self):
        pf = PendingFollowup(
            character="hank",
            task_summary="Add items to shopping list",
            source="router",
            items=["chicken", "flour"],
        )
        assert pf.character == "hank"
        assert len(pf.items) == 2

    def test_items_defaults_to_empty(self):
        pf = PendingFollowup(
            character="hank", task_summary="Add items", source="handoff_tool"
        )
        assert pf.items == []

    def test_to_dict(self):
        pf = PendingFollowup(
            character="hank",
            task_summary="Add milk",
            source="router",
            items=["milk"],
        )
        d = pf.to_dict()
        assert d == {
            "character": "hank",
            "task_summary": "Add milk",
            "source": "router",
            "items": ["milk"],
        }


# ===========================================================================
# routing.py — RoutingDecision
# ===========================================================================


class TestRoutingDecision:
    def test_minimal_routing_decision(self):
        rd = RoutingDecision(primary_character="delilah")
        assert rd.primary_character == "delilah"
        assert rd.pending_followup is None
        assert rd.rationale == ""

    def test_with_pending_followup(self):
        pf = PendingFollowup(
            character="hank", task_summary="Make list", source="router"
        )
        rd = RoutingDecision(
            primary_character="delilah",
            pending_followup=pf,
            rationale="meal planning → list follow-up",
        )
        d = rd.to_dict()
        assert d["primary_character"] == "delilah"
        assert d["pending_followup"]["character"] == "hank"
        assert "rationale" in d

    def test_to_dict_no_followup(self):
        rd = RoutingDecision(primary_character="delilah")
        d = rd.to_dict()
        assert d["pending_followup"] is None


# ===========================================================================
# routing.py — CoordinationState round-trip
# ===========================================================================


class TestCoordinationState:
    def test_default_state_is_idle(self):
        state = CoordinationState()
        assert state.mode == CoordinationMode.IDLE
        assert state.pending_character is None
        assert state.pending_task is None
        assert state.pending_items == []

    def test_to_dict_round_trip(self):
        state = CoordinationState(
            mode=CoordinationMode.PROPOSING,
            pending_character="hank",
            pending_task="Add items to list",
            pending_items=["chicken", "flour"],
            proposed_summary="Southern Fried Chicken",
            expires_at="2026-02-21T03:00:00",
            last_updated="2026-02-21T02:40:00",
        )
        d = state.to_dict()
        restored = CoordinationState.from_dict(d)
        assert restored.mode == CoordinationMode.PROPOSING
        assert restored.pending_character == "hank"
        assert restored.pending_items == ["chicken", "flour"]
        assert restored.proposed_summary == "Southern Fried Chicken"

    def test_from_dict_invalid_mode_falls_back_to_idle(self):
        state = CoordinationState.from_dict({"mode": "not_a_real_mode"})
        assert state.mode == CoordinationMode.IDLE

    def test_from_dict_empty(self):
        state = CoordinationState.from_dict({})
        assert state.mode == CoordinationMode.IDLE


# ===========================================================================
# conversation_state.py — ConversationStateManager
# ===========================================================================


def _make_context() -> ConversationContext:
    return ConversationContext(session_id="test-session", user_id="test-user")


class TestConversationStateManagerGetState:
    def test_idle_when_no_metadata(self):
        mgr = ConversationStateManager()
        ctx = _make_context()
        state = mgr.get_state(ctx)
        assert state.mode == CoordinationMode.IDLE

    def test_reads_persisted_state(self):
        mgr = ConversationStateManager()
        ctx = _make_context()
        ctx.metadata["coordination_state"] = {
            "mode": "proposing",
            "pending_character": "hank",
            "pending_task": "Add to list",
            "pending_items": [],
            "proposed_summary": None,
            "expires_at": None,
            "last_updated": None,
        }
        state = mgr.get_state(ctx)
        assert state.mode == CoordinationMode.PROPOSING
        assert state.pending_character == "hank"

    def test_bad_serialised_state_returns_idle(self):
        mgr = ConversationStateManager()
        ctx = _make_context()
        ctx.metadata["coordination_state"] = "not_a_dict"
        state = mgr.get_state(ctx)
        assert state.mode == CoordinationMode.IDLE


class TestConversationStateManagerTransitions:
    def test_set_proposing(self):
        mgr = ConversationStateManager()
        ctx = _make_context()
        state = mgr.set_proposing(
            ctx,
            pending_character="hank",
            pending_task="Add items to shopping list",
            proposed_summary="Southern Fried Chicken dinner",
            items=["chicken", "flour"],
        )
        assert state.mode == CoordinationMode.PROPOSING
        assert state.pending_character == "hank"
        assert "chicken" in state.pending_items
        # Verify persisted
        assert ctx.metadata["coordination_state"]["mode"] == "proposing"

    def test_set_awaiting_action(self):
        mgr = ConversationStateManager()
        ctx = _make_context()
        state = mgr.set_awaiting_action(
            ctx,
            pending_character="hank",
            pending_task="Add items to shopping list",
        )
        assert state.mode == CoordinationMode.AWAITING_ACTION
        assert ctx.metadata["coordination_state"]["mode"] == "awaiting_action"

    def test_clear(self):
        mgr = ConversationStateManager()
        ctx = _make_context()
        mgr.set_proposing(ctx, "hank", "some task", "some summary")
        mgr.clear(ctx)
        assert "coordination_state" not in ctx.metadata
        state = mgr.get_state(ctx)
        assert state.mode == CoordinationMode.IDLE

    def test_clear_also_removes_legacy_keys(self):
        mgr = ConversationStateManager()
        ctx = _make_context()
        ctx.metadata["deferred_tasks"] = [{"character": "hank"}]
        ctx.metadata["deferred_tasks_expires_at"] = "2026-01-01T00:00:00"
        ctx.metadata["deferred_tasks_trigger_intent"] = "household"
        mgr.clear(ctx)
        assert "deferred_tasks" not in ctx.metadata
        assert "deferred_tasks_expires_at" not in ctx.metadata
        assert "deferred_tasks_trigger_intent" not in ctx.metadata

    def test_items_default_to_empty_list(self):
        mgr = ConversationStateManager()
        ctx = _make_context()
        state = mgr.set_proposing(ctx, "hank", "task", "summary")
        assert state.pending_items == []


class TestConversationStateManagerExpiry:
    def test_not_expired(self):
        mgr = ConversationStateManager()
        state = CoordinationState(
            mode=CoordinationMode.PROPOSING,
            expires_at=(datetime.utcnow() + timedelta(minutes=19)).isoformat(),
        )
        assert mgr.is_expired(state) is False

    def test_expired(self):
        mgr = ConversationStateManager()
        state = CoordinationState(
            mode=CoordinationMode.PROPOSING,
            expires_at=(datetime.utcnow() - timedelta(seconds=1)).isoformat(),
        )
        assert mgr.is_expired(state) is True

    def test_no_expires_at_is_not_expired(self):
        mgr = ConversationStateManager()
        state = CoordinationState(mode=CoordinationMode.AWAITING_ACTION, expires_at=None)
        assert mgr.is_expired(state) is False

    def test_malformed_expires_at_is_not_expired(self):
        mgr = ConversationStateManager()
        state = CoordinationState(
            mode=CoordinationMode.AWAITING_ACTION, expires_at="not-a-date"
        )
        assert mgr.is_expired(state) is False


class TestConversationStateManagerLegacyBackwardCompat:
    """Reads legacy Phase 5 deferred_tasks keys and converts them."""

    def test_legacy_keys_produce_awaiting_action(self):
        mgr = ConversationStateManager()
        ctx = _make_context()
        ctx.metadata["deferred_tasks"] = [
            {
                "character": "hank",
                "task_description": "Add salmon to list",
                "intent": "household",
            }
        ]
        ctx.metadata["deferred_tasks_expires_at"] = (
            datetime.utcnow() + timedelta(minutes=15)
        ).isoformat()
        state = mgr.get_state(ctx)
        assert state.mode == CoordinationMode.AWAITING_ACTION
        assert state.pending_character == "hank"
        assert state.pending_task == "Add salmon to list"

    def test_empty_legacy_keys_produce_idle(self):
        mgr = ConversationStateManager()
        ctx = _make_context()
        # No deferred_tasks key at all
        state = mgr.get_state(ctx)
        assert state.mode == CoordinationMode.IDLE

    def test_new_state_key_takes_precedence_over_legacy(self):
        """When both old and new keys exist, the new coordination_state wins."""
        mgr = ConversationStateManager()
        ctx = _make_context()
        # Simulate old key
        ctx.metadata["deferred_tasks"] = [
            {"character": "hank", "task_description": "old task", "intent": "household"}
        ]
        # Simulate new key (e.g. already migrated)
        ctx.metadata["coordination_state"] = CoordinationState(
            mode=CoordinationMode.IDLE
        ).to_dict()
        state = mgr.get_state(ctx)
        assert state.mode == CoordinationMode.IDLE


# ===========================================================================
# character_executor.py — CharacterExecutor (mock LLM)
# ===========================================================================


def _make_executor(llm=None, character_system=None, tool_system=None, story_engine=None):
    """Build a CharacterExecutor with sensible mocks."""
    if llm is None:
        llm = MagicMock()
        llm.generate_response.return_value = {
            "content": "Sure thing!",
            "tool_calls": None,
        }
    if character_system is None:
        character_system = MagicMock()
        character_system.select_voice_mode.return_value = None
        character_system.build_system_prompt.return_value = "You are Delilah."
    if tool_system is None:
        tool_system = MagicMock()
        tool_system.list_tools.return_value = []
        tool_system.get_openai_functions.return_value = []
    if story_engine is None:
        story_engine = MagicMock()

    return CharacterExecutor(
        llm_integration=llm,
        character_system=character_system,
        tool_system=tool_system,
        story_engine=story_engine,
        max_tool_calls=5,
    )


class TestCharacterExecutorBasic:
    @pytest.mark.asyncio
    async def test_returns_character_response(self):
        executor = _make_executor()
        ctx = _make_context()
        result = await executor.execute(
            character="delilah",
            task_description="What should I cook tonight?",
            context=ctx,
            session_id="s1",
            user_id="u1",
        )
        assert isinstance(result, CharacterResponse)
        assert result.character == "delilah"
        assert result.text == "Sure thing!"
        assert result.tool_calls_made == 0
        assert result.handoff_signal is None

    @pytest.mark.asyncio
    async def test_system_prompt_override(self):
        llm = MagicMock()
        llm.generate_response.return_value = {"content": "Aye, Cap'n.", "tool_calls": None}
        executor = _make_executor(llm=llm)
        ctx = _make_context()
        result = await executor.execute(
            character="hank",
            task_description="Add milk to list",
            context=ctx,
            session_id="s1",
            user_id="u1",
            system_prompt_override="You are Hank. Be gruff.",
        )
        # The override prompt should have been used (no call to character_system)
        executor.character_system.build_system_prompt.assert_not_called()
        assert result.text == "Aye, Cap'n."

    @pytest.mark.asyncio
    async def test_empty_content_becomes_done(self):
        llm = MagicMock()
        llm.generate_response.return_value = {"content": "", "tool_calls": None}
        executor = _make_executor(llm=llm)
        ctx = _make_context()
        result = await executor.execute(
            character="delilah",
            task_description="anything",
            context=ctx,
            session_id="s1",
            user_id="u1",
        )
        assert result.text == "Done."


class TestCharacterExecutorToolLoop:
    @pytest.mark.asyncio
    async def test_tool_call_loop_runs(self):
        """Executor calls LLM twice when first response has tool calls."""
        tool_system = MagicMock()
        tool_system.list_tools.return_value = ["manage_list"]
        tool_system.get_openai_functions.return_value = [{}]
        tool_system.execute_tool = AsyncMock(
            return_value=MagicMock(message="Added to list.")
        )

        llm = MagicMock()
        llm.generate_response.side_effect = [
            {
                "content": None,
                "tool_calls": [
                    {
                        "id": "tc1",
                        "function": {
                            "name": "manage_list",
                            "arguments": '{"action": "add", "item": "milk"}',
                        },
                    }
                ],
            },
            {"content": "Got it, added milk.", "tool_calls": None},
        ]

        executor = _make_executor(llm=llm, tool_system=tool_system)
        ctx = _make_context()
        result = await executor.execute(
            character="hank",
            task_description="Add milk to my list",
            context=ctx,
            session_id="s1",
            user_id="u1",
        )
        assert result.tool_calls_made == 1
        assert result.text == "Got it, added milk."
        assert result.handoff_signal is None

    @pytest.mark.asyncio
    async def test_circuit_breaker_limits_tool_calls(self):
        """max_tool_calls is respected."""
        tool_system = MagicMock()
        tool_system.list_tools.return_value = ["some_tool"]
        tool_system.get_openai_functions.return_value = [{}]
        tool_system.execute_tool = AsyncMock(
            return_value=MagicMock(message="result")
        )

        # Always return tool calls — without circuit breaker this would loop forever
        llm = MagicMock()
        llm.generate_response.return_value = {
            "content": None,
            "tool_calls": [
                {
                    "id": "tc1",
                    "function": {"name": "some_tool", "arguments": "{}"},
                }
            ],
        }

        executor = _make_executor(llm=llm, tool_system=tool_system)
        executor.max_tool_calls = 3
        ctx = _make_context()
        result = await executor.execute(
            character="hank",
            task_description="loop task",
            context=ctx,
            session_id="s1",
            user_id="u1",
        )
        assert result.tool_calls_made == 3


class TestCharacterExecutorHandoffInterception:
    @pytest.mark.asyncio
    async def test_handoff_signal_captured(self):
        """request_handoff tool call is intercepted; handoff_signal is populated."""
        llm = MagicMock()
        llm.generate_response.return_value = {
            "content": "Hankie, darlin', would you handle the list?",
            "tool_calls": [
                {
                    "id": "tc_handoff",
                    "function": {
                        "name": "request_handoff",
                        "arguments": '{"to_character": "hank", "task_summary": "Add items to list", "items": ["chicken"]}',
                    },
                }
            ],
        }

        executor = _make_executor(llm=llm)
        ctx = _make_context()
        result = await executor.execute(
            character="delilah",
            task_description="Plan dinner and ask Hank to handle the list",
            context=ctx,
            session_id="s1",
            user_id="u1",
        )
        assert result.handoff_signal is not None
        assert result.handoff_signal["to_character"] == "hank"
        assert result.handoff_signal["task_summary"] == "Add items to list"

    @pytest.mark.asyncio
    async def test_handoff_does_not_call_tool_execute(self):
        """request_handoff is NOT passed to tool_system.execute_tool."""
        tool_system = MagicMock()
        tool_system.list_tools.return_value = ["request_handoff"]
        tool_system.get_openai_functions.return_value = [{}]
        tool_system.execute_tool = AsyncMock()

        llm = MagicMock()
        llm.generate_response.return_value = {
            "content": "Hankie, take over!",
            "tool_calls": [
                {
                    "id": "tc_handoff",
                    "function": {
                        "name": "request_handoff",
                        "arguments": '{"to_character": "hank", "task_summary": "list task"}',
                    },
                }
            ],
        }

        executor = _make_executor(llm=llm, tool_system=tool_system)
        ctx = _make_context()
        await executor.execute(
            character="delilah",
            task_description="Plan dinner",
            context=ctx,
            session_id="s1",
            user_id="u1",
        )
        tool_system.execute_tool.assert_not_called()

    @pytest.mark.asyncio
    async def test_second_handoff_in_same_turn_ignored(self):
        """Second request_handoff in the same turn is silently rejected (FR2.4)."""
        llm = MagicMock()
        llm.generate_response.return_value = {
            "content": "Here you go!",
            "tool_calls": [
                {
                    "id": "tc1",
                    "function": {
                        "name": "request_handoff",
                        "arguments": '{"to_character": "hank", "task_summary": "first task"}',
                    },
                },
                {
                    "id": "tc2",
                    "function": {
                        "name": "request_handoff",
                        "arguments": '{"to_character": "hank", "task_summary": "second task"}',
                    },
                },
            ],
        }

        executor = _make_executor(llm=llm)
        ctx = _make_context()
        result = await executor.execute(
            character="delilah",
            task_description="multiple handoffs",
            context=ctx,
            session_id="s1",
            user_id="u1",
        )
        # Only the first handoff should be recorded
        assert result.handoff_signal["task_summary"] == "first task"

    @pytest.mark.asyncio
    async def test_handoff_with_malformed_json_does_not_crash(self):
        """Malformed handoff arguments produce an empty dict signal, not a crash."""
        llm = MagicMock()
        llm.generate_response.return_value = {
            "content": "Hank, take over!",
            "tool_calls": [
                {
                    "id": "tc_bad",
                    "function": {
                        "name": "request_handoff",
                        "arguments": "NOT VALID JSON",
                    },
                }
            ],
        }

        executor = _make_executor(llm=llm)
        ctx = _make_context()
        result = await executor.execute(
            character="delilah",
            task_description="anything",
            context=ctx,
            session_id="s1",
            user_id="u1",
        )
        assert result.handoff_signal == {}
