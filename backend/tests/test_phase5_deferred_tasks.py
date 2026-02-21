"""
Tests for Phase 5: Specialist Handoff for Dependent Multi-Turn Tasks.

Covers:
- SubTask.is_dependent field
- DeferredTask model
- CharacterPlan.deferred_tasks field + to_dict()
- CharacterPlanner splitting dependent subtasks out of the immediate plan
- is_affirmation() helper
- ConversationContext deferred task metadata expiry
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from models.intent import SubTask, IntentResult
from models.character_plan import (
    CharacterTask,
    CharacterPlan,
    DeferredTask,
    ExecutionMode,
)
from models.message import ConversationContext
from core.character_planner import CharacterPlanner
from core.utils import is_affirmation


# ============================================================================
# SubTask Tests
# ============================================================================


class TestSubTaskIsDependent:
    """Tests for the new is_dependent field on SubTask."""

    def test_is_dependent_defaults_to_false(self):
        task = SubTask(text="set timer", intent="cooking", confidence=0.9)
        assert task.is_dependent is False

    def test_is_dependent_can_be_set_true(self):
        task = SubTask(
            text="create shopping list for that dinner",
            intent="household",
            confidence=0.9,
            is_dependent=True,
        )
        assert task.is_dependent is True

    def test_is_dependent_false_explicit(self):
        task = SubTask(
            text="add milk to list",
            intent="household",
            confidence=0.8,
            is_dependent=False,
        )
        assert task.is_dependent is False

    def test_subtask_confidence_validation_still_works(self):
        with pytest.raises(ValueError):
            SubTask(text="bad", intent="cooking", confidence=1.5)

    def test_to_dict_includes_is_dependent(self):
        """IntentResult.to_dict() should serialise is_dependent per sub-task."""
        result = IntentResult(
            intent="multi_task",
            confidence=0.85,
            classification_method="llm_assisted",
            sub_tasks=[
                SubTask(text="plan dinner", intent="cooking", confidence=0.9, is_dependent=False),
                SubTask(text="make shopping list", intent="household", confidence=0.9, is_dependent=True),
            ],
        )
        d = result.to_dict()
        assert d["sub_tasks"][0]["is_dependent"] is False
        assert d["sub_tasks"][1]["is_dependent"] is True


# ============================================================================
# DeferredTask Tests
# ============================================================================


class TestDeferredTask:
    """Tests for the DeferredTask model."""

    def test_create_deferred_task(self):
        dt = DeferredTask(
            character="hank",
            task_description="Add salmon, leeks, lemon to shopping list",
            intent="household",
        )
        assert dt.character == "hank"
        assert dt.intent == "household"

    def test_to_dict(self):
        dt = DeferredTask(
            character="hank",
            task_description="Add items to list",
            intent="household",
        )
        d = dt.to_dict()
        assert d == {
            "character": "hank",
            "task_description": "Add items to list",
            "intent": "household",
        }


# ============================================================================
# CharacterPlan deferred_tasks Tests
# ============================================================================


class TestCharacterPlanDeferredTasks:
    """Tests for the deferred_tasks field on CharacterPlan."""

    def _make_plan(self, deferred=None):
        task = CharacterTask(
            character="delilah",
            task_description="Suggest a dinner",
            intent="cooking",
            confidence=0.9,
        )
        return CharacterPlan(
            tasks=[task],
            execution_mode=ExecutionMode.SINGLE,
            total_confidence=0.9,
            estimated_total_duration_ms=2000,
            deferred_tasks=deferred or [],
        )

    def test_defaults_to_empty_list(self):
        plan = self._make_plan()
        assert plan.deferred_tasks == []

    def test_stores_deferred_tasks(self):
        dt = DeferredTask(character="hank", task_description="Add items", intent="household")
        plan = self._make_plan(deferred=[dt])
        assert len(plan.deferred_tasks) == 1
        assert plan.deferred_tasks[0].character == "hank"

    def test_to_dict_includes_deferred_tasks(self):
        dt = DeferredTask(character="hank", task_description="Add items", intent="household")
        plan = self._make_plan(deferred=[dt])
        d = plan.to_dict()
        assert "deferred_tasks" in d
        assert len(d["deferred_tasks"]) == 1
        assert d["deferred_tasks"][0]["character"] == "hank"

    def test_to_dict_empty_deferred_tasks(self):
        plan = self._make_plan()
        d = plan.to_dict()
        assert d["deferred_tasks"] == []


# ============================================================================
# CharacterPlanner split logic Tests
# ============================================================================


class TestCharacterPlannerDeferralSplit:
    """Tests for CharacterPlanner splitting dependent subtasks."""

    @pytest.fixture
    def planner(self):
        # Always return chapter 2 so Hank is available
        return CharacterPlanner(story_chapter_provider=lambda user_id: 2)

    def _make_intent(self, sub_tasks):
        return IntentResult(
            intent="multi_task",
            confidence=0.85,
            classification_method="llm_assisted",
            sub_tasks=sub_tasks,
        )

    def test_independent_tasks_all_in_tasks(self, planner):
        """Two independent tasks both appear in plan.tasks."""
        intent = self._make_intent([
            SubTask(text="set timer for 10 min", intent="cooking", confidence=0.9, is_dependent=False),
            SubTask(text="add milk to list", intent="household", confidence=0.9, is_dependent=False),
        ])
        plan = planner.create_plan(intent)
        assert len(plan.tasks) == 2
        assert len(plan.deferred_tasks) == 0

    def test_dependent_task_moved_to_deferred(self, planner):
        """A dependent shopping-list task is deferred, not executed immediately."""
        intent = self._make_intent([
            SubTask(text="plan dinner", intent="cooking", confidence=0.9, is_dependent=False),
            SubTask(text="create shopping list for that dinner", intent="household", confidence=0.9, is_dependent=True),
        ])
        plan = planner.create_plan(intent)
        assert len(plan.tasks) == 1
        assert plan.tasks[0].character == "delilah"
        assert plan.tasks[0].intent == "cooking"
        assert len(plan.deferred_tasks) == 1
        assert plan.deferred_tasks[0].character == "hank"
        assert plan.deferred_tasks[0].intent == "household"

    def test_all_dependent_falls_back_to_single_task(self, planner):
        """If every subtask is dependent the planner falls back to a single-task plan."""
        intent = self._make_intent([
            SubTask(text="add those items", intent="household", confidence=0.9, is_dependent=True),
        ])
        plan = planner.create_plan(intent)
        # Fallback produces a single-task plan from the overall intent
        assert len(plan.tasks) >= 1
        assert plan.deferred_tasks == []

    def test_metadata_includes_deferred_count(self, planner):
        intent = self._make_intent([
            SubTask(text="suggest a meal", intent="cooking", confidence=0.9, is_dependent=False),
            SubTask(text="build shopping list", intent="household", confidence=0.9, is_dependent=True),
        ])
        plan = planner.create_plan(intent)
        assert plan.metadata.get("deferred_task_count") == 1

    def test_chapter1_no_hank_available(self):
        """In chapter 1 only Delilah is available; deferred tasks still use Delilah."""
        planner = CharacterPlanner(story_chapter_provider=lambda uid: 1)
        intent = self._make_intent([
            SubTask(text="suggest dinner", intent="cooking", confidence=0.9, is_dependent=False),
            SubTask(text="make list", intent="household", confidence=0.9, is_dependent=True),
        ])
        plan = planner.create_plan(intent)
        # Hank not available — deferred task falls back to delilah
        assert plan.deferred_tasks[0].character == "delilah"


# ============================================================================
# is_affirmation Tests
# ============================================================================


class TestIsAffirmation:
    """Tests for the is_affirmation() utility."""

    # --- Positive cases ---
    @pytest.mark.parametrize("text", [
        "that looks good",
        "That looks good",
        "That looks good!",
        "sounds great",
        "Sounds great!",
        "yes",
        "Yes",
        "yeah",
        "yep",
        "yup",
        "sure",
        "ok",
        "okay",
        "OK",
        "perfect",
        "Perfect!",
        "great",
        "love it",
        "do it",
        "let's do it",
        "go for it",
        "go ahead",
        "that works",
        "yes please",
        "please",
        "absolutely",
        "exactly",
        "that's perfect",
        "sounds good",
        "that is great",
    ])
    def test_affirmative_phrases(self, text):
        assert is_affirmation(text) is True, f"Expected True for: {repr(text)}"

    # --- Negative cases ---
    @pytest.mark.parametrize("text", [
        "",           # empty
        "   ",        # whitespace only
        "yes, but can you make it vegetarian?",   # follow-up question
        "can you add more garlic?",               # new instruction
        "what's the weather like?",               # unrelated question
        "that sounds good but can we swap the salmon for chicken?",  # modification
        "no",         # negation
        "not really",
        "I don't think so",
        "what time is it?",
    ])
    def test_non_affirmative_phrases(self, text):
        assert is_affirmation(text) is False, f"Expected False for: {repr(text)}"

    def test_long_message_rejected(self):
        """Messages over 60 characters are never treated as plain affirmations."""
        long_msg = "yes " + "a" * 60
        assert is_affirmation(long_msg) is False


# ============================================================================
# ConversationContext deferred metadata expiry Tests
# ============================================================================


class TestDeferredMetadataExpiry:
    """
    Unit tests for the deferred task expiry logic inside handle_user_message.

    We test the logic directly by inspecting context.metadata rather than
    calling the full async handler (which requires a live LLM).
    """

    def _make_context(self, expires_delta: timedelta = None, has_tasks: bool = True):
        ctx = ConversationContext(session_id="test", user_id="test_user")
        if has_tasks:
            ctx.metadata["deferred_tasks"] = [
                {"character": "hank", "task_description": "Add items to list", "intent": "household"}
            ]
        if expires_delta is not None:
            ctx.metadata["deferred_tasks_expires_at"] = (
                datetime.utcnow() + expires_delta
            ).isoformat()
            ctx.metadata["deferred_tasks_trigger_intent"] = "cooking"
        return ctx

    def _apply_expiry_logic(self, context: ConversationContext):
        """Replicate the expiry check from handle_user_message."""
        expires_str = context.metadata.get("deferred_tasks_expires_at")
        if expires_str:
            try:
                expires_at = datetime.fromisoformat(expires_str)
                if datetime.utcnow() > expires_at:
                    context.metadata.pop("deferred_tasks", None)
                    context.metadata.pop("deferred_tasks_expires_at", None)
                    context.metadata.pop("deferred_tasks_trigger_intent", None)
            except (ValueError, TypeError):
                context.metadata.pop("deferred_tasks", None)
                context.metadata.pop("deferred_tasks_expires_at", None)
                context.metadata.pop("deferred_tasks_trigger_intent", None)

    def test_not_expired_tasks_preserved(self):
        ctx = self._make_context(expires_delta=timedelta(minutes=19))
        self._apply_expiry_logic(ctx)
        assert "deferred_tasks" in ctx.metadata

    def test_expired_tasks_cleared(self):
        ctx = self._make_context(expires_delta=timedelta(minutes=-1))
        self._apply_expiry_logic(ctx)
        assert "deferred_tasks" not in ctx.metadata
        assert "deferred_tasks_expires_at" not in ctx.metadata
        assert "deferred_tasks_trigger_intent" not in ctx.metadata

    def test_malformed_expiry_clears_tasks(self):
        ctx = self._make_context(has_tasks=True)
        ctx.metadata["deferred_tasks_expires_at"] = "not-a-date"
        ctx.metadata["deferred_tasks_trigger_intent"] = "cooking"
        self._apply_expiry_logic(ctx)
        assert "deferred_tasks" not in ctx.metadata

    def test_no_expiry_field_leaves_tasks_intact(self):
        """Tasks survive if the expiry key is absent (no-op)."""
        ctx = self._make_context(expires_delta=None)
        ctx.metadata.pop("deferred_tasks_expires_at", None)  # ensure it's absent
        self._apply_expiry_logic(ctx)
        assert "deferred_tasks" in ctx.metadata

    def test_affirmation_check_with_deferred_tasks(self):
        ctx = self._make_context(expires_delta=timedelta(minutes=10))
        # Valid deferred tasks + affirmation = should trigger
        assert bool(ctx.metadata.get("deferred_tasks")) and is_affirmation("that looks good")

    def test_affirmation_check_without_deferred_tasks(self):
        ctx = ConversationContext(session_id="test", user_id="test_user")
        # No deferred tasks = should NOT trigger even if affirmation
        assert not (bool(ctx.metadata.get("deferred_tasks")) and is_affirmation("that looks good"))

    def test_non_affirmation_with_deferred_tasks_does_not_trigger(self):
        ctx = self._make_context(expires_delta=timedelta(minutes=10))
        # Has deferred tasks but message is NOT an affirmation
        assert not (bool(ctx.metadata.get("deferred_tasks")) and is_affirmation("can you add garlic?"))
