"""
Story Engine - Manages story beat delivery and chapter progression.

Responsibilities:
- Load and manage story beats and chapters
- Track user progress through story
- Determine when to inject story beats
- Select appropriate beat variants
- Handle progression beats with multiple stages
- Check chapter completion criteria
"""

import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path

from models.story import (
    StoryBeat, Chapter, UserStoryState, BeatProgress,
    ChapterProgress, BeatVariant, BeatTrigger, BeatStage
)

logger = logging.getLogger(__name__)


class StoryEngine:
    """Manages story progression and beat delivery."""

    def __init__(self, story_dir: str = "story"):
        """
        Initialize the Story Engine.

        Args:
            story_dir: Directory containing story beats and chapters
        """
        self.story_dir = Path(story_dir)
        self.beats: Dict[int, List[StoryBeat]] = {}  # chapter_id -> beats
        self.chapters: Dict[int, Chapter] = {}  # chapter_id -> chapter
        self.user_states: Dict[str, UserStoryState] = {}  # user_id -> state

        # Load story content
        self._load_chapters()
        self._load_beats()

        logger.info(
            f"Story Engine initialized: {len(self.chapters)} chapters, "
            f"{sum(len(b) for b in self.beats.values())} beats"
        )

    def _load_chapters(self):
        """Load chapter definitions from chapters.json."""
        chapters_file = self.story_dir / "chapters.json"

        if not chapters_file.exists():
            logger.warning(f"Chapters file not found: {chapters_file}")
            return

        try:
            with open(chapters_file, 'r') as f:
                data = json.load(f)

            for chapter_data in data.get("chapters", []):
                chapter = Chapter(**chapter_data)
                self.chapters[chapter.id] = chapter

            logger.info(f"Loaded {len(self.chapters)} chapters")

        except Exception as e:
            logger.error(f"Error loading chapters: {str(e)}", exc_info=True)

    def _load_beats(self):
        """Load beat definitions from beats directory."""
        beats_dir = self.story_dir / "beats"

        if not beats_dir.exists():
            logger.warning(f"Beats directory not found: {beats_dir}")
            return

        # Load each chapter's beats
        for beat_file in beats_dir.glob("chapter*.json"):
            try:
                with open(beat_file, 'r') as f:
                    data = json.load(f)

                chapter_id = data.get("chapter")
                if not chapter_id:
                    logger.warning(f"No chapter ID in {beat_file}")
                    continue

                beats = []
                for beat_data in data.get("beats", []):
                    beat = StoryBeat(**beat_data)
                    beats.append(beat)

                self.beats[chapter_id] = beats
                logger.info(f"Loaded {len(beats)} beats for Chapter {chapter_id}")

            except Exception as e:
                logger.error(f"Error loading beats from {beat_file}: {str(e)}", exc_info=True)

    def get_or_create_user_state(self, user_id: str) -> UserStoryState:
        """
        Get existing user state or create a new one.

        Args:
            user_id: User identifier

        Returns:
            UserStoryState for this user
        """
        if user_id not in self.user_states:
            self.user_states[user_id] = UserStoryState(user_id=user_id)
            logger.info(f"Created new story state for user {user_id}")

        return self.user_states[user_id]

    def get_active_beats(self, user_id: str) -> List[StoryBeat]:
        """
        Get all active (unlocked but not completed) beats for user's current chapter.

        Args:
            user_id: User identifier

        Returns:
            List of active beats
        """
        state = self.get_or_create_user_state(user_id)
        chapter_beats = self.beats.get(state.current_chapter, [])

        active = []
        for beat in chapter_beats:
            beat_progress = state.get_beat_progress(beat.id)

            # One-shot beats: active if not delivered
            if beat.type == "one_shot":
                if not beat_progress or not beat_progress.delivered:
                    active.append(beat)

            # Progression beats: active if not all stages delivered
            elif beat.type == "progression":
                if not beat_progress or not beat_progress.delivered:
                    active.append(beat)

        return active

    def should_inject_beat(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Optional[Tuple[StoryBeat, int, str]]:
        """
        Determine if a story beat should be injected in this response.

        Args:
            user_id: User identifier
            context: Context information including:
                - user_message: The user's message
                - task_completed: Whether a task was completed
                - tool_used: Name of tool used (if any)
                - response_length: Length of response (for variant selection)

        Returns:
            Tuple of (beat, stage, variant_type) if beat should be injected, None otherwise
        """
        state = self.get_or_create_user_state(user_id)
        active_beats = self.get_active_beats(user_id)

        if not active_beats:
            return None

        # Check each active beat
        for beat in active_beats:
            if self._check_beat_trigger(beat, state, context):
                # Determine stage
                beat_progress = state.get_beat_progress(beat.id)
                stage = 1  # default stage

                if beat.type == "progression" and beat_progress:
                    # For progression beats, use next stage
                    stage = beat_progress.current_stage
                    if stage in beat_progress.delivered_stages:
                        stage += 1

                    # Check if we've delivered all stages
                    if beat.stages and stage > len(beat.stages):
                        continue  # This beat is complete

                # Select variant type
                variant_type = self._select_variant_type(context)

                logger.info(
                    f"Injecting beat '{beat.id}' (stage {stage}, variant {variant_type}) "
                    f"for user {user_id}"
                )

                return (beat, stage, variant_type)

        return None

    def _check_beat_trigger(
        self,
        beat: StoryBeat,
        state: UserStoryState,
        context: Dict[str, Any]
    ) -> bool:
        """
        Check if a beat's trigger conditions are met.

        Args:
            beat: Story beat to check
            state: User story state
            context: Context information

        Returns:
            True if trigger conditions are met
        """
        trigger = beat.trigger

        # Check interaction count trigger
        if trigger.type == "interaction_count":
            chapter_progress = state.chapter_progress.get(state.current_chapter)
            if not chapter_progress:
                return False

            interaction_count = chapter_progress.interaction_count

            if trigger.min_interactions and interaction_count < trigger.min_interactions:
                return False

            if trigger.max_interactions and interaction_count > trigger.max_interactions:
                return False

            return True

        # Check tool use trigger
        if trigger.type == "tool_use":
            tool_used = context.get("tool_used")
            if tool_used == trigger.tool_name:
                return True
            return False

        # Check user engagement trigger
        if trigger.type == "user_engagement":
            user_message = context.get("user_message", "").lower()

            # Check for keywords
            if trigger.keywords:
                if any(keyword in user_message for keyword in trigger.keywords):
                    # If requires direct address, check for character name
                    if trigger.requires_direct_address:
                        # Simple check: message contains "delilah" or similar
                        # TODO: Make this more sophisticated
                        return "delilah" in user_message or "lila" in user_message
                    return True

            return False

        logger.warning(f"Unknown trigger type: {trigger.type}")
        return False

    def _select_variant_type(self, context: Dict[str, Any]) -> str:
        """
        Select appropriate variant type based on context.

        Args:
            context: Context information

        Returns:
            Variant type: 'brief', 'standard', or 'full'
        """
        # Simple heuristic: use response length and task complexity
        response_length = context.get("response_length", 0)
        task_completed = context.get("task_completed", False)

        # Brief: Quick tasks with short responses
        if task_completed and response_length < 50:
            return "brief"

        # Full: Complex tasks or user engagement
        if response_length > 200 or context.get("user_engagement", False):
            return "full"

        # Standard: Default
        return "standard"

    def get_beat_content(
        self,
        beat: StoryBeat,
        stage: int,
        variant_type: str
    ) -> Optional[Tuple[str, str]]:
        """
        Get the content for a specific beat, stage, and variant.

        Args:
            beat: Story beat
            stage: Stage number (for progression beats)
            variant_type: Variant type ('brief', 'standard', 'full')

        Returns:
            Tuple of (content, delivery_type) or None if not found
        """
        try:
            # One-shot beats
            if beat.type == "one_shot" and beat.variants:
                variant = beat.variants.get(variant_type)
                if variant:
                    return (variant.content, variant.delivery)

            # Progression beats
            elif beat.type == "progression" and beat.stages:
                # Find the stage
                for beat_stage in beat.stages:
                    if beat_stage.stage == stage:
                        variant = beat_stage.variants.get(variant_type)
                        if variant:
                            return (variant.content, variant.delivery)

            logger.warning(
                f"No content found for beat '{beat.id}' "
                f"(type={beat.type}, stage={stage}, variant={variant_type})"
            )
            return None

        except Exception as e:
            logger.error(f"Error getting beat content: {str(e)}", exc_info=True)
            return None

    def mark_beat_stage_delivered(
        self,
        user_id: str,
        beat_id: str,
        stage: int
    ):
        """
        Mark a beat stage as delivered and update progress.

        Args:
            user_id: User identifier
            beat_id: Beat identifier
            stage: Stage number
        """
        state = self.get_or_create_user_state(user_id)
        state.update_beat_progress(beat_id, stage)

        # Check if beat is fully delivered
        beat = self._find_beat(beat_id, state.current_chapter)
        if beat:
            beat_progress = state.get_beat_progress(beat_id)

            # One-shot beats: mark as delivered after first delivery
            if beat.type == "one_shot":
                state.mark_beat_delivered(beat_id)

            # Progression beats: mark as delivered if all stages done
            elif beat.type == "progression" and beat.stages and beat_progress:
                if len(beat_progress.delivered_stages) >= len(beat.stages):
                    state.mark_beat_delivered(beat_id)

        logger.info(f"Marked beat '{beat_id}' stage {stage} as delivered for user {user_id}")

    def _find_beat(self, beat_id: str, chapter_id: int) -> Optional[StoryBeat]:
        """Find a beat by ID in a specific chapter."""
        chapter_beats = self.beats.get(chapter_id, [])
        for beat in chapter_beats:
            if beat.id == beat_id:
                return beat
        return None

    def on_user_message(self, user_id: str):
        """
        Handle user message event - increment interaction count.

        Args:
            user_id: User identifier
        """
        state = self.get_or_create_user_state(user_id)
        state.increment_interaction_count()

    def on_tool_executed(self, user_id: str, tool_name: str):
        """
        Handle tool execution event.

        Args:
            user_id: User identifier
            tool_name: Name of tool that was executed
        """
        # Currently just for tracking, could be used for analytics
        logger.debug(f"Tool '{tool_name}' executed for user {user_id}")

    def check_chapter_progression(self, user_id: str) -> Optional[int]:
        """
        Check if user has completed current chapter and should progress.

        Args:
            user_id: User identifier

        Returns:
            Next chapter ID if progression should occur, None otherwise
        """
        state = self.get_or_create_user_state(user_id)
        current_chapter = self.chapters.get(state.current_chapter)

        if not current_chapter:
            return None

        criteria = current_chapter.completion_criteria
        chapter_progress = state.chapter_progress.get(state.current_chapter)

        if not chapter_progress:
            return None

        # Check required beats
        for beat_id in criteria.required_beats:
            beat_progress = state.get_beat_progress(beat_id)
            if not beat_progress or not beat_progress.delivered:
                return None

            # Check specific stage requirements for progression beats
            if criteria.required_beat_stages:
                required_stage = criteria.required_beat_stages.get(beat_id)
                if required_stage:
                    if required_stage not in beat_progress.delivered_stages:
                        return None

        # Check interaction count
        if chapter_progress.interaction_count < criteria.minimum_interactions:
            return None

        # Check time elapsed
        time_elapsed = datetime.utcnow() - chapter_progress.started_at
        required_time = timedelta(hours=criteria.minimum_time_elapsed_hours)
        if time_elapsed < required_time:
            return None

        # All criteria met!
        next_chapter = current_chapter.unlocks.next_chapter
        if next_chapter:
            logger.info(
                f"User {user_id} completed Chapter {state.current_chapter}, "
                f"progressing to Chapter {next_chapter}"
            )

            # Mark chapter as completed
            state.completed_chapters.append(state.current_chapter)
            chapter_progress.completed_at = datetime.utcnow()

            # Progress to next chapter
            state.current_chapter = next_chapter
            state.updated_at = datetime.utcnow()

            return next_chapter

        return None

    def get_user_progress_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a summary of user's story progress.

        Args:
            user_id: User identifier

        Returns:
            Dict with progress information
        """
        state = self.get_or_create_user_state(user_id)
        current_chapter = self.chapters.get(state.current_chapter)
        chapter_progress = state.chapter_progress.get(state.current_chapter)

        summary = {
            "user_id": user_id,
            "current_chapter": state.current_chapter,
            "chapter_title": current_chapter.title if current_chapter else "Unknown",
            "total_interactions": state.total_interactions,
            "completed_chapters": state.completed_chapters,
            "chapter_interactions": chapter_progress.interaction_count if chapter_progress else 0,
            "delivered_beats": []
        }

        if chapter_progress:
            for beat_id, beat_progress in chapter_progress.beat_progress.items():
                if beat_progress.delivered:
                    summary["delivered_beats"].append(beat_id)

        return summary
