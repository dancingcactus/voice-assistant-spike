"""
Tests for Story Engine module.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from datetime import datetime, timedelta
from core.story_engine import StoryEngine
from models.story import UserStoryState, BeatProgress, ChapterProgress


class TestStoryEngine:
    """Test suite for Story Engine."""

    @pytest.fixture
    def story_engine(self):
        """Create a StoryEngine instance for testing."""
        # Use the story directory from project root
        story_dir = Path(__file__).parent.parent.parent / "story"
        return StoryEngine(story_dir=str(story_dir))

    @pytest.fixture
    def user_id(self):
        """Test user ID."""
        return "test_user_123"

    def test_initialization(self, story_engine):
        """Test that Story Engine initializes correctly."""
        assert story_engine is not None
        assert len(story_engine.chapters) > 0
        assert len(story_engine.beats) > 0
        assert 1 in story_engine.chapters  # Chapter 1 should exist
        assert 1 in story_engine.beats  # Chapter 1 beats should exist

    def test_user_state_creation(self, story_engine, user_id):
        """Test that user state is created correctly."""
        state = story_engine.get_or_create_user_state(user_id)

        assert state.user_id == user_id
        assert state.current_chapter == 1
        assert state.total_interactions == 0
        assert len(state.completed_chapters) == 0

    def test_interaction_count_increment(self, story_engine, user_id):
        """Test that interaction count increments correctly."""
        story_engine.on_user_message(user_id)
        story_engine.on_user_message(user_id)
        story_engine.on_user_message(user_id)

        state = story_engine.get_or_create_user_state(user_id)
        assert state.total_interactions == 3
        assert state.chapter_progress[1].interaction_count == 3

    def test_awakening_confusion_beat_triggers(self, story_engine, user_id):
        """Test that 'awakening_confusion' beat triggers in first 5 interactions."""
        # Simulate first few interactions
        for i in range(5):
            story_engine.on_user_message(user_id)

            context = {
                "user_message": f"Test message {i}",
                "task_completed": False,
                "response_length": 50
            }

            beat_result = story_engine.should_inject_beat(user_id, context)

            # Should trigger within first 5 interactions
            if beat_result:
                beat, stage, variant = beat_result
                assert beat.id == "awakening_confusion"
                assert stage == 1
                assert variant in ["brief", "standard", "full"]
                break
        else:
            pytest.fail("awakening_confusion beat did not trigger in first 5 interactions")

    def test_first_timer_beat_triggers(self, story_engine, user_id):
        """Test that 'first_timer' beat triggers after setting a timer."""
        # First, deliver awakening_confusion (prerequisite)
        story_engine.on_user_message(user_id)
        context = {
            "user_message": "Hello",
            "task_completed": False,
            "response_length": 50
        }
        beat_result = story_engine.should_inject_beat(user_id, context)
        if beat_result:
            beat, stage, _ = beat_result
            story_engine.mark_beat_stage_delivered(user_id, beat.id, stage)

        # Now trigger first_timer with set_timer tool
        context = {
            "user_message": "Set timer for 5 minutes",
            "task_completed": True,
            "tool_used": "set_timer",
            "response_length": 30
        }

        beat_result = story_engine.should_inject_beat(user_id, context)

        assert beat_result is not None
        beat, stage, variant = beat_result
        assert beat.id == "first_timer"
        assert stage == 1

    def test_progression_beat_stages(self, story_engine, user_id):
        """Test that progression beats advance through stages."""
        # First, deliver awakening_confusion (prerequisite)
        story_engine.on_user_message(user_id)
        context = {
            "user_message": "Hello",
            "task_completed": False,
            "response_length": 50
        }
        beat_result = story_engine.should_inject_beat(user_id, context)
        if beat_result:
            beat, stage, _ = beat_result
            story_engine.mark_beat_stage_delivered(user_id, beat.id, stage)

        # Trigger recipe_help beat multiple times
        stages_delivered = []

        for i in range(5):
            context = {
                "user_message": "How do I make biscuits?",
                "task_completed": True,
                "tool_used": "get_recipe",
                "response_length": 100
            }

            beat_result = story_engine.should_inject_beat(user_id, context)

            if beat_result:
                beat, stage, variant = beat_result
                assert beat.id == "recipe_help"
                stages_delivered.append(stage)

                # Mark as delivered
                story_engine.mark_beat_stage_delivered(user_id, beat.id, stage)

                # Check content exists
                content = story_engine.get_beat_content(beat, stage, "standard")
                assert content is not None
                assert len(content[0]) > 0  # content text

        # Should have progressed through stages
        assert len(stages_delivered) >= 1
        # Stages should be sequential
        for i, stage in enumerate(stages_delivered):
            assert stage == i + 1

    def test_variant_selection(self, story_engine):
        """Test that variant selection works based on context."""
        # Brief variant: short response, task completed
        context = {
            "user_message": "Set timer",
            "task_completed": True,
            "response_length": 20
        }
        variant = story_engine._select_variant_type(context)
        assert variant == "brief"

        # Standard variant: medium response
        context = {
            "user_message": "How do I make soup?",
            "task_completed": True,
            "response_length": 100
        }
        variant = story_engine._select_variant_type(context)
        assert variant == "standard"

        # Full variant: long response or user engagement
        context = {
            "user_message": "Delilah, are you okay?",
            "task_completed": False,
            "response_length": 250,
            "user_engagement": True
        }
        variant = story_engine._select_variant_type(context)
        assert variant == "full"

    def test_beat_content_retrieval(self, story_engine, user_id):
        """Test that beat content can be retrieved correctly."""
        # Get awakening_confusion beat
        beats = story_engine.beats.get(1, [])
        awakening_beat = next((b for b in beats if b.id == "awakening_confusion"), None)

        assert awakening_beat is not None

        # Get content for each variant
        for variant in ["brief", "standard", "full"]:
            content = story_engine.get_beat_content(awakening_beat, 1, variant)
            assert content is not None
            text, delivery = content
            assert len(text) > 0
            assert delivery in ["append", "replace"]

    def test_chapter_progression_criteria(self, story_engine, user_id):
        """Test that chapter progression checks all criteria."""
        state = story_engine.get_or_create_user_state(user_id)

        # Initially should not progress (no beats delivered)
        result = story_engine.check_chapter_progression(user_id)
        assert result is None

        # Deliver required beats
        story_engine.mark_beat_stage_delivered(user_id, "awakening_confusion", 1)
        story_engine.mark_beat_stage_delivered(user_id, "self_awareness", 1)
        story_engine.mark_beat_stage_delivered(user_id, "self_awareness", 2)
        story_engine.mark_beat_stage_delivered(user_id, "self_awareness", 3)
        state.mark_beat_delivered("awakening_confusion")
        state.mark_beat_delivered("self_awareness")

        # Still shouldn't progress (not enough interactions)
        result = story_engine.check_chapter_progression(user_id)
        assert result is None

        # Add enough interactions
        for i in range(10):
            story_engine.on_user_message(user_id)

        # Still shouldn't progress (not enough time)
        result = story_engine.check_chapter_progression(user_id)
        assert result is None

        # Manually adjust time for testing
        chapter_progress = state.chapter_progress[1]
        chapter_progress.started_at = datetime.utcnow() - timedelta(hours=25)

        # Now should progress
        result = story_engine.check_chapter_progression(user_id)
        assert result == 2  # Should progress to Chapter 2
        assert 1 in state.completed_chapters
        assert state.current_chapter == 2

    def test_concurrent_progression_beats(self, story_engine, user_id):
        """Test that multiple progression beats can be active simultaneously."""
        # Deliver awakening_confusion first
        story_engine.on_user_message(user_id)
        context = {
            "user_message": "Hello",
            "task_completed": False,
            "response_length": 50
        }
        beat_result = story_engine.should_inject_beat(user_id, context)
        if beat_result:
            beat, stage, _ = beat_result
            story_engine.mark_beat_stage_delivered(user_id, beat.id, stage)

        # Trigger recipe_help
        context1 = {
            "user_message": "How do I make biscuits?",
            "task_completed": True,
            "tool_used": "get_recipe",
            "response_length": 100
        }

        # Trigger self_awareness
        context2 = {
            "user_message": "Delilah, are you okay?",
            "task_completed": False,
            "response_length": 150
        }

        # Both should be available
        beat1 = story_engine.should_inject_beat(user_id, context1)
        assert beat1 is not None
        story_engine.mark_beat_stage_delivered(user_id, beat1[0].id, beat1[1])

        beat2 = story_engine.should_inject_beat(user_id, context2)
        assert beat2 is not None

        # They should be different beats
        if beat1 and beat2:
            assert beat1[0].id != beat2[0].id

    def test_user_progress_summary(self, story_engine, user_id):
        """Test that user progress summary is generated correctly."""
        # Add some interactions and beats
        for i in range(5):
            story_engine.on_user_message(user_id)

        story_engine.mark_beat_stage_delivered(user_id, "awakening_confusion", 1)
        state = story_engine.get_or_create_user_state(user_id)
        state.mark_beat_delivered("awakening_confusion")

        # Get summary
        summary = story_engine.get_user_progress_summary(user_id)

        assert summary["user_id"] == user_id
        assert summary["current_chapter"] == 1
        assert summary["chapter_title"] == "Awakening"
        assert summary["total_interactions"] == 5
        assert summary["chapter_interactions"] == 5
        assert "awakening_confusion" in summary["delivered_beats"]

    def test_get_active_beats(self, story_engine, user_id):
        """Test that active beats are correctly identified."""
        # Initially, all Chapter 1 beats should be active
        active = story_engine.get_active_beats(user_id)
        assert len(active) > 0

        # After delivering a one-shot beat, it should no longer be active
        story_engine.mark_beat_stage_delivered(user_id, "awakening_confusion", 1)
        state = story_engine.get_or_create_user_state(user_id)
        state.mark_beat_delivered("awakening_confusion")

        active = story_engine.get_active_beats(user_id)
        active_ids = [beat.id for beat in active]
        assert "awakening_confusion" not in active_ids
