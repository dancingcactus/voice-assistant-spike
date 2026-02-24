"""
Tests for the Planning Tool & Plan State Management.

Covers:
- PlanningTool: name, description, parameters, execute() fallback
- PlanStateManager: start_plan, advance_step, complete_plan, clear, touch, is_expired
- PlanState: to_dict, from_dict, properties
- CharacterExecutor: plan_action interception, plan_signal in CharacterResponse,
  plan-aware history window
- ConversationManager: plan_signal handled, plan TTL expiry, plan_state_manager injected
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.plan_state import PlanState, PlanStateManager
from core.conversation_state import ConversationStateManager
from core.character_executor import CharacterExecutor, CharacterResponse
from core.conversation_manager import ConversationManager
from core.conversation_router import ConversationRouter
from core.turn_classifier import TurnClassifier
from models.message import ConversationContext, Message
from models.routing import CoordinationMode, TurnType, TurnClassification, RoutingDecision
from tools.plan_tool import PlanningTool, PLAN_TOOL_NAME
from tools.tool_base import ToolContext, ToolResultStatus


# ===========================================================================
# PlanningTool — basic contract
# ===========================================================================


class TestPlanningToolBasic:
    def test_name_is_plan_action(self):
        tool = PlanningTool()
        assert tool.name == "plan_action"

    def test_constant_matches_name(self):
        assert PLAN_TOOL_NAME == "plan_action"

    def test_description_is_meaningful(self):
        tool = PlanningTool()
        assert len(tool.description) > 50

    def test_parameters_include_required_fields(self):
        tool = PlanningTool()
        names = {p.name for p in tool.parameters}
        assert "action" in names
        assert "title" in names
        assert "steps" in names
        assert "notes" in names

    def test_action_is_required(self):
        tool = PlanningTool()
        action = next(p for p in tool.parameters if p.name == "action")
        assert action.required is True

    def test_action_enum_contains_expected_values(self):
        tool = PlanningTool()
        action = next(p for p in tool.parameters if p.name == "action")
        assert set(action.enum) == {"start", "advance", "complete"}

    def test_title_is_optional(self):
        tool = PlanningTool()
        title = next(p for p in tool.parameters if p.name == "title")
        assert title.required is False

    def test_steps_is_optional_array(self):
        tool = PlanningTool()
        steps = next(p for p in tool.parameters if p.name == "steps")
        assert steps.required is False
        assert steps.type == "array"
        assert steps.items == {"type": "string"}

    def test_notes_is_optional(self):
        tool = PlanningTool()
        notes = next(p for p in tool.parameters if p.name == "notes")
        assert notes.required is False


class TestPlanningToolExecuteFallback:
    @pytest.mark.asyncio
    async def test_execute_returns_success(self):
        tool = PlanningTool()
        ctx = ToolContext(user_id="u1", session_id="s1", character_id="delilah")
        result = await tool.execute(ctx, action="start", title="Plan", steps=["step 1"])
        assert result.status == ToolResultStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_execute_data_includes_intercepted_false(self):
        tool = PlanningTool()
        ctx = ToolContext(user_id="u1", session_id="s1", character_id="rex")
        result = await tool.execute(ctx, action="advance")
        assert result.data["intercepted"] is False

    @pytest.mark.asyncio
    async def test_execute_data_includes_action(self):
        tool = PlanningTool()
        ctx = ToolContext(user_id="u1", session_id="s1")
        result = await tool.execute(ctx, action="complete")
        assert result.data["action"] == "complete"


# ===========================================================================
# PlanState — dataclass behaviour
# ===========================================================================


class TestPlanState:
    def _make_state(self, **kwargs) -> PlanState:
        defaults = dict(
            title="Test Plan",
            steps=["step 1", "step 2", "step 3"],
        )
        defaults.update(kwargs)
        return PlanState(**defaults)

    def test_current_step_returns_first_step(self):
        state = self._make_state()
        assert state.current_step == "step 1"

    def test_current_step_advances_with_index(self):
        state = self._make_state(current_step_index=1)
        assert state.current_step == "step 2"

    def test_current_step_none_when_completed(self):
        state = self._make_state(current_step_index=3)
        assert state.current_step is None

    def test_is_active_true_for_active(self):
        state = self._make_state(status="active")
        assert state.is_active is True

    def test_is_active_false_for_completed(self):
        state = self._make_state(status="completed")
        assert state.is_active is False

    def test_to_dict_roundtrip(self):
        state = self._make_state(
            current_step_index=1,
            plan_turn_start_index=5,
            expires_at="2099-01-01T00:00:00",
            last_updated="2024-01-01T00:00:00",
        )
        d = state.to_dict()
        restored = PlanState.from_dict(d)
        assert restored.title == state.title
        assert restored.steps == state.steps
        assert restored.current_step_index == 1
        assert restored.plan_turn_start_index == 5
        assert restored.status == "active"

    def test_from_dict_with_missing_fields_uses_defaults(self):
        state = PlanState.from_dict({"title": "Minimal", "steps": ["a"]})
        assert state.current_step_index == 0
        assert state.status == "active"
        assert state.plan_turn_start_index == 0


# ===========================================================================
# PlanStateManager
# ===========================================================================


def _make_context(**kwargs) -> ConversationContext:
    return ConversationContext(session_id="s1", user_id="u1", **kwargs)


class TestPlanStateManagerStartPlan:
    def test_start_plan_stores_state(self):
        psm = PlanStateManager()
        ctx = _make_context()
        psm.start_plan(ctx, title="My Plan", steps=["a", "b"])
        state = psm.get_state(ctx)
        assert state is not None
        assert state.title == "My Plan"
        assert state.steps == ["a", "b"]

    def test_start_plan_status_is_active(self):
        psm = PlanStateManager()
        ctx = _make_context()
        psm.start_plan(ctx, title="Plan", steps=["x"])
        assert psm.get_state(ctx).status == "active"

    def test_start_plan_records_turn_start_index(self):
        psm = PlanStateManager()
        ctx = _make_context()
        psm.start_plan(ctx, title="Plan", steps=["x"], turn_start_index=7)
        assert psm.get_state(ctx).plan_turn_start_index == 7

    def test_start_plan_sets_expires_at(self):
        psm = PlanStateManager()
        ctx = _make_context()
        psm.start_plan(ctx, title="Plan", steps=["x"])
        state = psm.get_state(ctx)
        assert state.expires_at is not None

    def test_start_plan_overwrites_existing_plan(self):
        psm = PlanStateManager()
        ctx = _make_context()
        psm.start_plan(ctx, title="Old Plan", steps=["old"])
        psm.start_plan(ctx, title="New Plan", steps=["new"])
        assert psm.get_state(ctx).title == "New Plan"


class TestPlanStateManagerAdvanceStep:
    def test_advance_step_increments_index(self):
        psm = PlanStateManager()
        ctx = _make_context()
        psm.start_plan(ctx, title="Plan", steps=["a", "b", "c"])
        psm.advance_step(ctx)
        assert psm.get_state(ctx).current_step_index == 1

    def test_advance_step_past_end_completes_plan(self):
        psm = PlanStateManager()
        ctx = _make_context()
        psm.start_plan(ctx, title="Plan", steps=["a"])
        psm.advance_step(ctx)
        assert psm.get_state(ctx).status == "completed"

    def test_advance_step_no_op_when_no_plan(self):
        psm = PlanStateManager()
        ctx = _make_context()
        result = psm.advance_step(ctx)
        assert result is None

    def test_advance_step_no_op_when_completed(self):
        psm = PlanStateManager()
        ctx = _make_context()
        psm.start_plan(ctx, title="Plan", steps=["a"])
        psm.advance_step(ctx)  # completes the plan
        initial_index = psm.get_state(ctx).current_step_index
        psm.advance_step(ctx)  # should be no-op
        assert psm.get_state(ctx).current_step_index == initial_index

    def test_advance_step_refreshes_ttl(self):
        psm = PlanStateManager()
        ctx = _make_context()
        psm.start_plan(ctx, title="Plan", steps=["a", "b"], expiry_minutes=1)
        original_expiry = psm.get_state(ctx).expires_at
        # Advance refreshes TTL to default 20 min
        psm.advance_step(ctx)
        new_expiry = psm.get_state(ctx).expires_at
        # New expiry should be later than the 1-min original
        assert new_expiry > original_expiry


class TestPlanStateManagerCompletePlan:
    def test_complete_plan_sets_status(self):
        psm = PlanStateManager()
        ctx = _make_context()
        psm.start_plan(ctx, title="Plan", steps=["a", "b"])
        psm.complete_plan(ctx)
        assert psm.get_state(ctx).status == "completed"

    def test_complete_plan_no_op_when_no_plan(self):
        psm = PlanStateManager()
        ctx = _make_context()
        result = psm.complete_plan(ctx)
        assert result is None


class TestPlanStateManagerClearAndTouch:
    def test_clear_removes_state(self):
        psm = PlanStateManager()
        ctx = _make_context()
        psm.start_plan(ctx, title="Plan", steps=["a"])
        psm.clear(ctx)
        assert psm.get_state(ctx) is None

    def test_touch_refreshes_expiry(self):
        psm = PlanStateManager()
        ctx = _make_context()
        psm.start_plan(ctx, title="Plan", steps=["a"], expiry_minutes=1)
        old_expiry = psm.get_state(ctx).expires_at
        # Touch with 20 min → new expiry should be later
        psm.touch(ctx, expiry_minutes=20)
        new_expiry = psm.get_state(ctx).expires_at
        assert new_expiry > old_expiry

    def test_touch_no_op_when_no_plan(self):
        psm = PlanStateManager()
        ctx = _make_context()
        psm.touch(ctx)  # should not raise


class TestPlanStateManagerIsExpired:
    def test_expired_plan_returns_true(self):
        psm = PlanStateManager()
        past = (datetime.utcnow() - timedelta(minutes=1)).isoformat()
        state = PlanState(title="X", steps=["a"], expires_at=past)
        assert psm.is_expired(state) is True

    def test_future_plan_returns_false(self):
        psm = PlanStateManager()
        future = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        state = PlanState(title="X", steps=["a"], expires_at=future)
        assert psm.is_expired(state) is False

    def test_no_expires_at_returns_false(self):
        psm = PlanStateManager()
        state = PlanState(title="X", steps=["a"])
        assert psm.is_expired(state) is False


# ===========================================================================
# CharacterExecutor — plan_action interception
# ===========================================================================


def _make_llm_with_plan_tool_call(action="start", title="Dinner Plan", steps=None):
    """Build a mock LLM that returns a plan_action tool call."""
    if steps is None:
        steps = ["Choose recipe", "Build shopping list"]
    llm = MagicMock()
    # First call: plan_action tool call
    # Second call: final text response (no tool calls)
    llm.generate_response.side_effect = [
        {
            "content": "",
            "tool_calls": [
                {
                    "id": "tc1",
                    "function": {
                        "name": "plan_action",
                        "arguments": json.dumps(
                            {"action": action, "title": title, "steps": steps}
                        ),
                    },
                }
            ],
        },
        {
            "content": "Plan created!",
            "tool_calls": None,
        },
    ]
    return llm


def _make_executor_with_plan_tool():
    """Build real CharacterExecutor with plan tool intercepted (LLM calls plan_action)."""
    llm = _make_llm_with_plan_tool_call()
    char_sys = MagicMock()
    char_sys.select_voice_mode.return_value = MagicMock(
        mode=MagicMock(name="warm_baseline"), confidence=0.8
    )
    char_sys.build_system_prompt.return_value = "You are Delilah."
    tool_sys = MagicMock()
    tool_sys.list_tools.return_value = ["plan_action"]
    tool_sys.get_openai_functions.return_value = [
        {"type": "function", "function": {"name": "plan_action"}}
    ]
    story_engine = MagicMock()

    return CharacterExecutor(
        llm_integration=llm,
        character_system=char_sys,
        tool_system=tool_sys,
        story_engine=story_engine,
    )


class TestCharacterExecutorPlanInterception:
    @pytest.mark.asyncio
    async def test_plan_action_call_sets_plan_signal(self):
        executor = _make_executor_with_plan_tool()
        ctx = ConversationContext(session_id="s1", user_id="u1")
        response = await executor.execute(
            character="delilah",
            task_description="Plan a dinner",
            context=ctx,
            session_id="s1",
            user_id="u1",
        )
        assert response.plan_signal is not None
        assert response.plan_signal["action"] == "start"
        assert response.plan_signal["title"] == "Dinner Plan"

    @pytest.mark.asyncio
    async def test_plan_action_does_not_add_tool_result_to_messages(self):
        """plan_action should NOT trigger another LLM round-trip."""
        llm = _make_llm_with_plan_tool_call()
        char_sys = MagicMock()
        char_sys.select_voice_mode.return_value = None
        char_sys.build_system_prompt.return_value = "System"
        tool_sys = MagicMock()
        tool_sys.list_tools.return_value = ["plan_action"]
        tool_sys.get_openai_functions.return_value = []
        story_engine = MagicMock()

        executor = CharacterExecutor(
            llm_integration=llm,
            character_system=char_sys,
            tool_system=tool_sys,
            story_engine=story_engine,
        )
        ctx = ConversationContext(session_id="s1", user_id="u1")
        await executor.execute(
            character="delilah",
            task_description="Plan it",
            context=ctx,
            session_id="s1",
            user_id="u1",
        )
        # LLM should only be called once (no second round-trip for plan_action)
        assert llm.generate_response.call_count == 1

    @pytest.mark.asyncio
    async def test_plan_signal_in_character_response_to_dict(self):
        executor = _make_executor_with_plan_tool()
        ctx = ConversationContext(session_id="s1", user_id="u1")
        response = await executor.execute(
            character="delilah",
            task_description="Plan it",
            context=ctx,
            session_id="s1",
            user_id="u1",
        )
        d = response.to_dict()
        assert "plan_signal" in d
        assert d["plan_signal"]["action"] == "start"

    @pytest.mark.asyncio
    async def test_no_plan_signal_when_no_plan_action_called(self):
        llm = MagicMock()
        llm.generate_response.return_value = {
            "content": "Hello sugar!",
            "tool_calls": None,
        }
        char_sys = MagicMock()
        char_sys.select_voice_mode.return_value = None
        char_sys.build_system_prompt.return_value = "System"
        tool_sys = MagicMock()
        tool_sys.list_tools.return_value = []
        tool_sys.get_openai_functions.return_value = []
        story_engine = MagicMock()

        executor = CharacterExecutor(
            llm_integration=llm,
            character_system=char_sys,
            tool_system=tool_sys,
            story_engine=story_engine,
        )
        ctx = ConversationContext(session_id="s1", user_id="u1")
        response = await executor.execute(
            character="delilah",
            task_description="What's for dinner?",
            context=ctx,
            session_id="s1",
            user_id="u1",
        )
        assert response.plan_signal is None


# ===========================================================================
# CharacterExecutor — plan-aware history window
# ===========================================================================


class TestCharacterExecutorPlanAwareHistory:
    @pytest.mark.asyncio
    async def test_uses_all_plan_history_when_plan_active(self):
        """
        When an active plan is stored in context.metadata, the executor
        should include history from plan_turn_start_index, not just the
        last history_window messages.
        """
        captured_messages = []

        def _capture_messages(messages, **kwargs):
            captured_messages.extend(messages)
            return {"content": "Got it.", "tool_calls": None}

        llm = MagicMock()
        llm.generate_response.side_effect = _capture_messages

        char_sys = MagicMock()
        char_sys.select_voice_mode.return_value = None
        char_sys.build_system_prompt.return_value = "System"
        tool_sys = MagicMock()
        tool_sys.list_tools.return_value = []
        tool_sys.get_openai_functions.return_value = []
        story_engine = MagicMock()

        executor = CharacterExecutor(
            llm_integration=llm,
            character_system=char_sys,
            tool_system=tool_sys,
            story_engine=story_engine,
        )

        # Build context with 5 history messages
        ctx = ConversationContext(session_id="s1", user_id="u1")
        for i in range(5):
            ctx.history.append(Message(role="user", content=f"Message {i}"))

        # Store an active plan starting at index 2
        psm = PlanStateManager()
        psm.start_plan(ctx, title="Test", steps=["a", "b"], turn_start_index=2)

        await executor.execute(
            character="delilah",
            task_description="Continue",
            context=ctx,
            session_id="s1",
            user_id="u1",
            history_window=2,  # would normally only give 2 messages
        )

        # Should have included messages from index 2 onward (3 messages: 2, 3, 4)
        user_messages = [m for m in captured_messages if m["role"] == "user"]
        contents = [m["content"] for m in user_messages]
        assert any("Message 2" in c for c in contents)
        assert any("Message 3" in c for c in contents)

    @pytest.mark.asyncio
    async def test_uses_history_window_when_no_plan(self):
        """Without an active plan, the default history_window=2 applies."""
        captured_messages = []

        def _capture_messages(messages, **kwargs):
            captured_messages.extend(messages)
            return {"content": "Done.", "tool_calls": None}

        llm = MagicMock()
        llm.generate_response.side_effect = _capture_messages

        char_sys = MagicMock()
        char_sys.select_voice_mode.return_value = None
        char_sys.build_system_prompt.return_value = "System"
        tool_sys = MagicMock()
        tool_sys.list_tools.return_value = []
        tool_sys.get_openai_functions.return_value = []
        story_engine = MagicMock()

        executor = CharacterExecutor(
            llm_integration=llm,
            character_system=char_sys,
            tool_system=tool_sys,
            story_engine=story_engine,
        )

        ctx = ConversationContext(session_id="s1", user_id="u1")
        for i in range(5):
            ctx.history.append(Message(role="user", content=f"Message {i}"))

        await executor.execute(
            character="delilah",
            task_description="Continue",
            context=ctx,
            session_id="s1",
            user_id="u1",
            history_window=2,
        )

        user_messages = [m for m in captured_messages if m["role"] == "user"]
        contents = [m["content"] for m in user_messages]
        # With window=2, should NOT include message 0 or 1
        assert not any("Message 0" in c for c in contents)
        assert not any("Message 1" in c for c in contents)


# ===========================================================================
# ConversationManager — plan_signal handling
# ===========================================================================


def _make_memory_manager():
    mm = MagicMock()
    mm.load_user_state.return_value = MagicMock(
        story_progress=MagicMock(current_chapter=2),
        conversation_history=MagicMock(messages=[]),
    )
    mm.add_conversation_message = MagicMock()
    mm.increment_interaction_count = MagicMock()
    return mm


def _make_router(primary="delilah", pending_followup=None, rationale="test"):
    router = MagicMock(spec=ConversationRouter)
    router.route.return_value = RoutingDecision(
        primary_character=primary,
        pending_followup=pending_followup,
        rationale=rationale,
    )
    return router


def _make_classifier(turn_type=TurnType.NEW_REQUEST, confidence=0.9):
    clf = MagicMock(spec=TurnClassifier)
    clf.classify.return_value = TurnClassification(
        turn_type=turn_type, confidence=confidence, reasoning="test"
    )
    return clf


def _make_cm(
    executor=None,
    router=None,
    classifier=None,
    state_manager=None,
    plan_state_manager=None,
    memory_manager=None,
):
    llm = MagicMock()
    llm.generate_response.return_value = {
        "content": "Hello sugar!",
        "tool_calls": None,
        "usage": {"total_tokens": 20},
        "response_time": 0.05,
        "finish_reason": "stop",
    }
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

    default_executor = MagicMock(spec=CharacterExecutor)
    default_executor.execute = AsyncMock(
        return_value=CharacterResponse(
            character="delilah",
            text="Hello sugar!",
            voice_mode="warm_baseline",
            tool_calls_made=0,
            handoff_signal=None,
            plan_signal=None,
        )
    )

    return ConversationManager(
        llm_integration=llm,
        character_system=cs,
        tool_system=tool_system,
        story_engine=story_engine,
        memory_manager=mm,
        state_manager=state_manager or ConversationStateManager(),
        plan_state_manager=plan_state_manager or PlanStateManager(),
        turn_classifier=classifier or _make_classifier(),
        conversation_router=router or _make_router(),
        character_executor=executor or default_executor,
    )


class TestConversationManagerPlanStateManagerInjection:
    def test_plan_state_manager_injected(self):
        psm = PlanStateManager()
        cm = _make_cm(plan_state_manager=psm)
        assert cm.plan_state_manager is psm

    def test_plan_state_manager_auto_created(self):
        cm = _make_cm()
        assert isinstance(cm.plan_state_manager, PlanStateManager)


class TestConversationManagerPlanSignalStart:
    @pytest.mark.asyncio
    async def test_plan_start_signal_creates_plan_state(self):
        """When primary character emits plan_signal(action='start'), plan state is created."""
        plan_signal = {
            "action": "start",
            "title": "Dinner Prep Plan",
            "steps": ["Choose recipe", "Build shopping list", "Set timers"],
        }
        executor = MagicMock(spec=CharacterExecutor)
        executor.execute = AsyncMock(
            return_value=CharacterResponse(
                character="delilah",
                text="Let me plan this out for you!",
                voice_mode="passionate",
                tool_calls_made=1,
                handoff_signal=None,
                plan_signal=plan_signal,
            )
        )

        psm = PlanStateManager()
        cm = _make_cm(executor=executor, plan_state_manager=psm)

        result = await cm.handle_user_message(
            session_id="s1", user_message="Plan dinner for Sunday", user_id="u1"
        )

        assert result["metadata"]["phase51"] is True
        ctx = cm.conversations["s1"]
        state = psm.get_state(ctx)
        assert state is not None
        assert state.title == "Dinner Prep Plan"
        assert state.steps == ["Choose recipe", "Build shopping list", "Set timers"]
        assert state.is_active

    @pytest.mark.asyncio
    async def test_plan_start_records_turn_start_index(self):
        """plan_turn_start_index matches the history length at the time plan_signal fires."""
        plan_signal = {
            "action": "start",
            "title": "Plan",
            "steps": ["step 1"],
        }
        executor = MagicMock(spec=CharacterExecutor)
        executor.execute = AsyncMock(
            return_value=CharacterResponse(
                character="delilah",
                text="Planning!",
                voice_mode="passionate",
                tool_calls_made=1,
                handoff_signal=None,
                plan_signal=plan_signal,
            )
        )

        psm = PlanStateManager()
        cm = _make_cm(executor=executor, plan_state_manager=psm)

        # Pre-seed with some history
        ctx = cm.get_or_create_conversation("s1", "u1")
        ctx.history.append(Message(role="user", content="Older message"))
        ctx.history.append(Message(role="assistant", content="Older response"))

        history_len_before = len(ctx.history)

        # Send user message — this adds 1 user message, making history_len_before+1
        # The plan_signal fires after the user message is added but before executor
        # actually appends the assistant message — in practice, after execute() returns
        # we see context.history has the user message but not yet the assistant.
        await cm.handle_user_message(
            session_id="s1", user_message="Plan it", user_id="u1"
        )

        state = psm.get_state(ctx)
        assert state is not None
        # turn_start_index should be history_len_before + 1 (after user msg appended)
        assert state.plan_turn_start_index == history_len_before + 1


class TestConversationManagerPlanSignalAdvance:
    @pytest.mark.asyncio
    async def test_plan_advance_signal_advances_step(self):
        """plan_signal(action='advance') moves to the next step."""
        plan_signal = {"action": "advance"}
        executor = MagicMock(spec=CharacterExecutor)
        executor.execute = AsyncMock(
            return_value=CharacterResponse(
                character="delilah",
                text="Step done!",
                voice_mode="warm_baseline",
                tool_calls_made=1,
                handoff_signal=None,
                plan_signal=plan_signal,
            )
        )

        psm = PlanStateManager()
        ctx_pre = ConversationContext(session_id="s1", user_id="u1")
        psm.start_plan(ctx_pre, title="Plan", steps=["a", "b", "c"], turn_start_index=0)

        cm = _make_cm(executor=executor, plan_state_manager=psm)
        cm.conversations["s1"] = ctx_pre

        await cm.handle_user_message(session_id="s1", user_message="Next step", user_id="u1")

        state = psm.get_state(ctx_pre)
        assert state.current_step_index == 1


class TestConversationManagerPlanSignalComplete:
    @pytest.mark.asyncio
    async def test_plan_complete_signal_completes_plan(self):
        """plan_signal(action='complete') marks the plan as completed."""
        plan_signal = {"action": "complete"}
        executor = MagicMock(spec=CharacterExecutor)
        executor.execute = AsyncMock(
            return_value=CharacterResponse(
                character="delilah",
                text="All done!",
                voice_mode="warm_baseline",
                tool_calls_made=1,
                handoff_signal=None,
                plan_signal=plan_signal,
            )
        )

        psm = PlanStateManager()
        ctx_pre = ConversationContext(session_id="s1", user_id="u1")
        psm.start_plan(ctx_pre, title="Plan", steps=["a", "b"], turn_start_index=0)

        cm = _make_cm(executor=executor, plan_state_manager=psm)
        cm.conversations["s1"] = ctx_pre

        await cm.handle_user_message(session_id="s1", user_message="Done!", user_id="u1")

        state = psm.get_state(ctx_pre)
        assert state.status == "completed"


# ===========================================================================
# ConversationManager — plan TTL expiry
# ===========================================================================


class TestConversationManagerPlanTTL:
    @pytest.mark.asyncio
    async def test_expired_plan_is_cleared(self):
        """An expired plan is silently cleared at the start of the turn."""
        psm = PlanStateManager()
        ctx = ConversationContext(session_id="s1", user_id="u1")
        # Set plan with already-expired TTL
        past = (datetime.utcnow() - timedelta(minutes=1)).isoformat()
        psm.start_plan(ctx, title="Old Plan", steps=["a"])
        # Manually override expiry to be in the past
        ctx.metadata["plan_state"]["expires_at"] = past

        executor = MagicMock(spec=CharacterExecutor)
        executor.execute = AsyncMock(
            return_value=CharacterResponse(
                character="delilah",
                text="Hello.",
                voice_mode="warm_baseline",
                tool_calls_made=0,
                handoff_signal=None,
                plan_signal=None,
            )
        )

        cm = _make_cm(executor=executor, plan_state_manager=psm)
        cm.conversations["s1"] = ctx

        await cm.handle_user_message(session_id="s1", user_message="Hi", user_id="u1")

        # Plan should be cleared
        state = psm.get_state(ctx)
        assert state is None

    @pytest.mark.asyncio
    async def test_active_plan_ttl_refreshed_on_each_turn(self):
        """An active non-expired plan has its TTL refreshed on each turn."""
        psm = PlanStateManager()
        ctx = ConversationContext(session_id="s1", user_id="u1")
        # Start plan with short TTL
        psm.start_plan(ctx, title="Plan", steps=["a"], expiry_minutes=1)
        original_expiry = psm.get_state(ctx).expires_at

        executor = MagicMock(spec=CharacterExecutor)
        executor.execute = AsyncMock(
            return_value=CharacterResponse(
                character="delilah",
                text="Hi.",
                voice_mode="warm_baseline",
                tool_calls_made=0,
                handoff_signal=None,
                plan_signal=None,
            )
        )

        cm = _make_cm(executor=executor, plan_state_manager=psm)
        cm.conversations["s1"] = ctx

        await cm.handle_user_message(session_id="s1", user_message="Next", user_id="u1")

        new_expiry = psm.get_state(ctx).expires_at
        # TTL should be refreshed to 20 minutes, so new_expiry > original_expiry
        assert new_expiry > original_expiry


# ===========================================================================
# PlanningTool registered in ToolSystem
# ===========================================================================


class TestPlanningToolRegistration:
    def test_plan_tool_can_be_registered(self):
        from core.tool_system import ToolSystem

        ts = ToolSystem()
        ts.register_tool(PlanningTool())
        assert "plan_action" in ts.list_tools()

    def test_plan_tool_in_openai_functions(self):
        from core.tool_system import ToolSystem

        ts = ToolSystem()
        ts.register_tool(PlanningTool())
        fns = ts.get_openai_functions()
        names = [f["function"]["name"] for f in fns]
        assert "plan_action" in names
