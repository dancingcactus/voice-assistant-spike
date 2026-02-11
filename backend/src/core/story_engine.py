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
    ChapterProgress, BeatVariant, BeatTrigger, BeatStage,
    AutoAdvanceNotification, ConditionalRequirement
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class StoryEngine:
    """Manages story progression and beat delivery."""

    def __init__(self, story_dir: str = "story", memory_manager: Optional["MemoryManager"] = None):
        """
        Initialize the Story Engine.

        Args:
            story_dir: Directory containing story beats and chapters
            memory_manager: Memory manager instance for persistent storage
        """
        self.story_dir = Path(story_dir)
        self.beats: Dict[int, List[StoryBeat]] = {}  # chapter_id -> beats
        self.chapters: Dict[int, Chapter] = {}  # chapter_id -> chapter
        self.user_states: Dict[str, UserStoryState] = {}  # user_id -> state (in-memory cache)
        self.memory_manager = memory_manager  # Optional - for persistent storage

        # Load story content
        self._load_chapters()
        self._load_beats()

        print(f"📖 Story Engine initialized: {len(self.chapters)} chapters, "
              f"{sum(len(b) for b in self.beats.values())} beats")
        logger.info(
            f"Story Engine initialized: {len(self.chapters)} chapters, "
            f"{sum(len(b) for b in self.beats.values())} beats, "
            f"memory={self.memory_manager is not None}"
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
        Loads from persistent storage if memory_manager is available.

        Args:
            user_id: User identifier

        Returns:
            UserStoryState for this user
        """
        if user_id not in self.user_states:
            # Try to load from memory manager if available
            if self.memory_manager:
                user_state = self.memory_manager.load_user_state(user_id)
                # Convert StoryProgress to UserStoryState
                story_state = UserStoryState(user_id=user_id)
                story_state.current_chapter = user_state.story_progress.current_chapter
                story_state.total_interactions = user_state.story_progress.interaction_count

                # Reconstruct beat progress and chapter progress from stored data
                for beat_id, beat_data in user_state.story_progress.beats_delivered.items():
                    progress = BeatProgress(
                        beat_id=beat_id,
                        delivered=beat_data.get("delivered", False),
                        current_stage=beat_data.get("current_stage", 1),
                        delivered_stages=set(beat_data.get("delivered_stages", [])),
                        first_delivered_at=beat_data.get("first_delivered_at")
                    )

                    # Determine which chapter this beat belongs to
                    chapter_id = story_state.current_chapter  # Assume current chapter for now

                    # Create chapter progress if it doesn't exist
                    if chapter_id not in story_state.chapter_progress:
                        story_state.chapter_progress[chapter_id] = ChapterProgress(
                            chapter_id=chapter_id,
                            started_at=user_state.story_progress.first_interaction or datetime.utcnow(),
                            interaction_count=story_state.total_interactions
                        )

                    # Add beat progress to chapter
                    story_state.chapter_progress[chapter_id].beat_progress[beat_id] = progress

                self.user_states[user_id] = story_state
                logger.info(f"Loaded story state for user {user_id} (Chapter {story_state.current_chapter})")
            else:
                # Create new state
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

            # Chapter-end beats are not injected into responses
            elif beat.type == "chapter_end":
                continue

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

        logger.debug(
            f"Evaluating beat injection for user {user_id}: "
            f"{len(active_beats)} active beats, chapter {state.current_chapter}, "
            f"tool_used={context.get('tool_used')}"
        )

        if not active_beats:
            logger.debug(f"No active beats for user {user_id}")
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
                        logger.debug(f"Beat '{beat.id}' all stages complete, skipping")
                        continue  # This beat is complete

                # Select variant type
                variant_type = self._select_variant_type(context)

                logger.info(
                    f"✅ Injecting beat '{beat.id}' (stage {stage}, variant {variant_type}) "
                    f"for user {user_id}"
                )

                return (beat, stage, variant_type)

        logger.debug(f"No beats triggered for user {user_id} (checked {len(active_beats)} beats)")
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
        logger.debug(f"Checking trigger for beat '{beat.id}'")

        # FIRST: Check prerequisite conditions (must pass before checking trigger)
        if beat.conditions:
            if not self._check_beat_conditions(beat, state):
                logger.debug(f"Beat '{beat.id}' conditions not met")
                return False

        trigger = beat.trigger

        # Check interaction count trigger
        if trigger.type == "interaction_count":
            chapter_progress = state.chapter_progress.get(state.current_chapter)
            if not chapter_progress:
                logger.debug(f"Beat '{beat.id}': No chapter progress found")
                return False

            interaction_count = chapter_progress.interaction_count

            if trigger.min_interactions and interaction_count < trigger.min_interactions:
                logger.debug(
                    f"Beat '{beat.id}': Interaction count {interaction_count} < "
                    f"min {trigger.min_interactions}"
                )
                return False

            if trigger.max_interactions and interaction_count > trigger.max_interactions:
                logger.debug(
                    f"Beat '{beat.id}': Interaction count {interaction_count} > "
                    f"max {trigger.max_interactions}"
                )
                return False

            logger.debug(f"Beat '{beat.id}': Interaction count trigger passed ({interaction_count})")
            return True

        # Check tool use trigger
        if trigger.type == "tool_use":
            tool_used = context.get("tool_used")
            if tool_used == trigger.tool_name:
                logger.debug(f"Beat '{beat.id}': Tool use trigger passed (tool={tool_used})")
                return True
            logger.debug(
                f"Beat '{beat.id}': Tool use trigger failed "
                f"(expected={trigger.tool_name}, got={tool_used})"
            )
            return False

        # Check user engagement trigger
        if trigger.type == "user_engagement":
            user_message = context.get("user_message", "").lower()

            # Check for keywords
            if trigger.keywords:
                matched_keywords = [kw for kw in trigger.keywords if kw in user_message]
                if matched_keywords:
                    # If requires direct address, check for character name
                    if trigger.requires_direct_address:
                        # Simple check: message contains "delilah" or similar
                        # TODO: Make this more sophisticated
                        has_address = "delilah" in user_message or "lila" in user_message
                        if has_address:
                            logger.debug(
                                f"Beat '{beat.id}': User engagement trigger passed "
                                f"(keywords={matched_keywords}, direct_address=True)"
                            )
                            return True
                        else:
                            logger.debug(
                                f"Beat '{beat.id}': Keywords matched but direct address required"
                            )
                            return False
                    logger.debug(f"Beat '{beat.id}': User engagement trigger passed (keywords={matched_keywords})")
                    return True
                else:
                    logger.debug(f"Beat '{beat.id}': No keywords matched (looking for {trigger.keywords})")

            return False

        # Condition-only trigger (conditions already checked)
        if trigger.type == "condition":
            logger.debug(f"Beat '{beat.id}': Condition trigger passed")
            return True

        logger.warning(f"Unknown trigger type: {trigger.type}")
        return False

    def _check_beat_conditions(
        self,
        beat: StoryBeat,
        state: UserStoryState
    ) -> bool:
        """
        Check if a beat's prerequisite conditions are met.

        Conditions can include:
        - {beat_id}_delivered: true - Requires a specific beat to be delivered
        - Other condition types can be added here

        Args:
            beat: Story beat to check
            state: User story state

        Returns:
            True if all conditions are met
        """
        if not beat.conditions:
            return True

        logger.debug(f"Checking conditions for beat '{beat.id}': {beat.conditions}")

        for condition_key, condition_value in beat.conditions.items():
            # Check for beat delivery conditions (e.g., "awakening_confusion_delivered": true)
            if condition_key.endswith("_delivered"):
                # Extract beat_id from condition key
                required_beat_id = condition_key.replace("_delivered", "")
                beat_progress = state.get_beat_progress(required_beat_id)

                if condition_value is True:
                    # Requires beat to be delivered
                    if not beat_progress or not beat_progress.delivered:
                        logger.debug(
                            f"Beat '{beat.id}': Condition failed - "
                            f"requires '{required_beat_id}' to be delivered"
                        )
                        return False
                    logger.debug(f"Beat '{beat.id}': Prerequisite '{required_beat_id}' is delivered ✓")
                elif condition_value is False:
                    # Requires beat to NOT be delivered
                    if beat_progress and beat_progress.delivered:
                        logger.debug(
                            f"Beat '{beat.id}': Condition failed - "
                            f"requires '{required_beat_id}' to NOT be delivered"
                        )
                        return False

            # TODO: Add support for other condition types as needed
            # Examples:
            # - "user_seems_receptive": check user sentiment
            # - "not_during_emergency": check system state
            # - "requires_n_of_beats": conditional progression

        logger.debug(f"Beat '{beat.id}': All conditions met ✓")
        return True

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
        logger.debug(f"Marking beat '{beat_id}' stage {stage} as delivered for user {user_id}")

        state = self.get_or_create_user_state(user_id)
        state.update_beat_progress(beat_id, stage)

        # Check if beat is fully delivered
        beat = self._find_beat(beat_id, state.current_chapter)
        if beat:
            beat_progress = state.get_beat_progress(beat_id)

            # One-shot beats: mark as delivered after first delivery
            if beat.type == "one_shot":
                state.mark_beat_delivered(beat_id)
                logger.debug(f"Beat '{beat_id}' is one-shot, marking as fully delivered")

            # Progression beats: mark as delivered if all stages done
            elif beat.type == "progression" and beat.stages and beat_progress:
                if len(beat_progress.delivered_stages) >= len(beat.stages):
                    state.mark_beat_delivered(beat_id)
                    logger.debug(
                        f"Beat '{beat_id}' progression complete "
                        f"({len(beat_progress.delivered_stages)}/{len(beat.stages)} stages)"
                    )

        logger.info(f"✅ Marked beat '{beat_id}' stage {stage} as delivered for user {user_id}")

        # Save to persistent storage
        self._save_story_state(user_id, state)

        # Force reload state from memory manager on next access to ensure consistency
        if self.memory_manager and user_id in self.user_states:
            logger.debug(f"Invalidating cached state for user {user_id}")
            del self.user_states[user_id]

    def _save_story_state(self, user_id: str, state: UserStoryState):
        """Save story state to persistent storage via Memory Manager."""
        if not self.memory_manager:
            logger.debug(f"No memory manager configured, state not persisted for user {user_id}")
            return

        logger.debug(f"Saving story state for user {user_id} to persistent storage")

        # Convert UserStoryState to format for memory manager
        # Collect all beat progress from all chapters
        beats_delivered = {}
        for chapter_id, chapter_progress in state.chapter_progress.items():
            for beat_id, progress in chapter_progress.beat_progress.items():
                beats_delivered[beat_id] = {
                    "delivered": progress.delivered,
                    "current_stage": progress.current_stage,
                    "delivered_stages": progress.delivered_stages,  # Already a list in BeatProgress
                    "first_delivered_at": progress.first_triggered
                }

        # Update story progress in memory manager
        # Get first interaction from chapter progress
        first_interaction = None
        if state.chapter_progress:
            for chapter_progress in state.chapter_progress.values():
                if chapter_progress.started_at:
                    first_interaction = chapter_progress.started_at
                    break

        try:
            self.memory_manager.update_story_progress(
                user_id,
                current_chapter=state.current_chapter,
                beats_delivered=beats_delivered,
                interaction_count=state.total_interactions,
                first_interaction=first_interaction
            )
            logger.debug(
                f"✅ Saved story state for user {user_id}: "
                f"chapter={state.current_chapter}, beats={len(beats_delivered)}, "
                f"interactions={state.total_interactions}"
            )
        except Exception as e:
            logger.error(f"❌ Failed to save story state for user {user_id}: {str(e)}", exc_info=True)

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

        # Chapter-end beats can force progression when their conditions are met.
        chapter_end_advance = self._check_chapter_end_beats(user_id, state, current_chapter)
        if chapter_end_advance:
            return chapter_end_advance

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

        # Check conditional beats (N of M requirement)
        if criteria.conditional_beats:
            satisfied, count = self.check_conditional_progression(
                user_id,
                criteria.conditional_beats.beats,
                criteria.conditional_beats.n
            )
            if not satisfied:
                logger.debug(
                    f"Conditional beats not satisfied: {count}/{len(criteria.conditional_beats.beats)}, "
                    f"requires {criteria.conditional_beats.n}"
                )
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

            # Save to persistent storage
            self._save_story_state(user_id, state)

            return next_chapter

        return None

    def _advance_to_next_chapter(
        self,
        user_id: str,
        state: UserStoryState,
        next_chapter: int,
        reason: str
    ) -> Optional[int]:
        """Advance user to the next chapter and persist state."""
        if not next_chapter:
            return None

        chapter_progress = state.chapter_progress.get(state.current_chapter)
        if state.current_chapter not in state.completed_chapters:
            state.completed_chapters.append(state.current_chapter)

        if chapter_progress:
            chapter_progress.completed_at = datetime.utcnow()

        state.current_chapter = next_chapter
        state.updated_at = datetime.utcnow()
        self._save_story_state(user_id, state)

        logger.info(
            f"User {user_id} progressed to Chapter {next_chapter} "
            f"(reason={reason})"
        )
        return next_chapter

    def _check_chapter_end_beats(
        self,
        user_id: str,
        state: UserStoryState,
        chapter: Chapter
    ) -> Optional[int]:
        """Check chapter_end beats and advance if any are satisfied."""
        chapter_beats = self.beats.get(state.current_chapter, [])

        for beat in chapter_beats:
            if beat.type != "chapter_end":
                continue

            beat_progress = state.get_beat_progress(beat.id)
            if beat_progress and beat_progress.delivered:
                return self._advance_to_next_chapter(
                    user_id,
                    state,
                    chapter.unlocks.next_chapter,
                    reason=f"chapter_end:{beat.id}"
                )

            if beat.conditions and not self._check_beat_conditions(beat, state):
                continue

            trigger_met = False
            if beat.trigger.type == "condition":
                trigger_met = True
            elif beat.trigger.type == "interaction_count":
                trigger_met = self._check_auto_advance_trigger(beat, state)
            else:
                logger.warning(
                    "Chapter-end beat '%s' has unsupported trigger type '%s'",
                    beat.id,
                    beat.trigger.type
                )

            if not trigger_met:
                continue

            state.update_beat_progress(beat.id, 1)
            state.mark_beat_delivered(beat.id)
            self._save_story_state(user_id, state)

            logger.info(
                "✅ Chapter-end beat '%s' satisfied for user %s",
                beat.id,
                user_id
            )

            return self._advance_to_next_chapter(
                user_id,
                state,
                chapter.unlocks.next_chapter,
                reason=f"chapter_end:{beat.id}"
            )

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

    def get_auto_advance_ready(self, user_id: str) -> List[AutoAdvanceNotification]:
        """
        Get all auto-advance beats that are ready for delivery.

        Args:
            user_id: User identifier

        Returns:
            List of auto-advance notifications
        """
        state = self.get_or_create_user_state(user_id)

        # Check for auto-advance beats in the auto-advance queue
        ready_beats = [beat for beat in state.auto_advance_queue if not beat.notified]

        # Check for new auto-advance beats that should be added to the queue
        self._check_auto_advance_beats(user_id, state)

        return state.auto_advance_queue

    def _check_auto_advance_beats(self, user_id: str, state: UserStoryState):
        """
        Check for auto-advance beats that are ready and add them to the queue.

        Args:
            user_id: User identifier
            state: User story state
        """
        chapter_beats = self.beats.get(state.current_chapter, [])

        for beat in chapter_beats:
            # Skip if not auto-advance or already delivered
            if not beat.auto_advance:
                continue

            beat_progress = state.get_beat_progress(beat.id)
            if beat_progress and beat_progress.delivered:
                continue

            # Skip if already in queue
            if any(n.beat_id == beat.id for n in state.auto_advance_queue):
                continue

            # Check if prerequisite conditions are met
            if beat.conditions and not self._check_beat_conditions(beat, state):
                logger.debug(f"Auto-advance beat '{beat.id}' conditions not met")
                continue

            # Check if trigger conditions are met (without user context)
            if not self._check_auto_advance_trigger(beat, state):
                logger.debug(f"Auto-advance beat '{beat.id}' trigger not met")
                continue

            # Beat is ready! Add to queue
            notification = AutoAdvanceNotification(
                beat_id=beat.id,
                name=beat.id.replace('_', ' ').title(),  # Simple formatting
                chapter_id=state.current_chapter,
                ready_since=datetime.utcnow(),
                content=beat.content or "",
                notified=False
            )

            state.auto_advance_queue.append(notification)
            logger.info(f"✅ Auto-advance beat '{beat.id}' ready for user {user_id}")

            # Save state
            self._save_story_state(user_id, state)

    def _check_auto_advance_trigger(self, beat: StoryBeat, state: UserStoryState) -> bool:
        """
        Check if an auto-advance beat's trigger is met (without user context).

        Only checks triggers that don't require user interaction context:
        - interaction_count: Check if user has enough interactions

        Args:
            beat: Story beat to check
            state: User story state

        Returns:
            True if trigger is met
        """
        trigger = beat.trigger

        # Check interaction count trigger
        if trigger.type == "interaction_count":
            chapter_progress = state.chapter_progress.get(state.current_chapter)
            if not chapter_progress:
                logger.debug(f"Auto-advance beat '{beat.id}': No chapter progress found")
                return False

            interaction_count = chapter_progress.interaction_count

            if trigger.min_interactions and interaction_count < trigger.min_interactions:
                logger.debug(
                    f"Auto-advance beat '{beat.id}': Interaction count {interaction_count} < "
                    f"min {trigger.min_interactions}"
                )
                return False

            if trigger.max_interactions and interaction_count > trigger.max_interactions:
                logger.debug(
                    f"Auto-advance beat '{beat.id}': Interaction count {interaction_count} > "
                    f"max {trigger.max_interactions}"
                )
                return False

            logger.debug(f"Auto-advance beat '{beat.id}': Interaction count trigger passed ({interaction_count})")
            return True

        # Other trigger types (tool_use, user_engagement) require context
        # and should not be used with auto-advance beats
        logger.warning(
            f"Auto-advance beat '{beat.id}' has trigger type '{trigger.type}' "
            "which requires user context and cannot be used with auto-advance"
        )
        return False

    def deliver_auto_advance_beat(self, user_id: str, beat_id: str) -> Optional[str]:
        """
        Deliver an auto-advance beat to the user.

        Args:
            user_id: User identifier
            beat_id: Beat identifier

        Returns:
            Beat content if successful, None otherwise
        """
        state = self.get_or_create_user_state(user_id)

        # Find the beat in the queue
        notification = None
        for n in state.auto_advance_queue:
            if n.beat_id == beat_id:
                notification = n
                break

        if not notification:
            logger.warning(f"Auto-advance beat '{beat_id}' not in queue for user {user_id}")
            return None

        # Mark beat as delivered
        self.mark_beat_stage_delivered(user_id, beat_id, 1)

        # Remove from queue
        state.auto_advance_queue = [n for n in state.auto_advance_queue if n.beat_id != beat_id]

        # Save state
        self._save_story_state(user_id, state)

        logger.info(f"✅ Delivered auto-advance beat '{beat_id}' to user {user_id}")

        return notification.content

    def check_conditional_progression(
        self,
        user_id: str,
        required_beats: List[str],
        n: int
    ) -> Tuple[bool, int]:
        """
        Check if N of M conditional progression requirements are met.

        Args:
            user_id: User identifier
            required_beats: List of beat IDs to check
            n: Number of beats required

        Returns:
            Tuple of (satisfied, current_count)
        """
        state = self.get_or_create_user_state(user_id)

        # Count how many of the required beats have been delivered
        count = 0
        for beat_id in required_beats:
            beat_progress = state.get_beat_progress(beat_id)
            if beat_progress and beat_progress.delivered:
                count += 1

        satisfied = count >= n
        logger.debug(
            f"Conditional progression check for user {user_id}: "
            f"{count}/{len(required_beats)} beats, requires {n}, satisfied={satisfied}"
        )

        return (satisfied, count)

    def build_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Build a dependency graph showing which beats depend on which other beats.

        Returns:
            Dict mapping beat_id -> list of beat_ids that depend on it
        """
        dependencies = {}

        # For each chapter's beats
        for chapter_id, beats in self.beats.items():
            for beat in beats:
                # Check conditions for prerequisite beats
                if beat.conditions:
                    for condition_key, condition_value in beat.conditions.items():
                        # Pattern: "{beat_id}_delivered" means this beat requires that prerequisite
                        if condition_key.endswith('_delivered') and condition_value:
                            prereq_beat_id = condition_key.replace('_delivered', '')

                            # Add this beat as a dependent of the prerequisite
                            if prereq_beat_id not in dependencies:
                                dependencies[prereq_beat_id] = []
                            dependencies[prereq_beat_id].append(beat.id)

        logger.debug(f"Built dependency graph: {dependencies}")
        return dependencies

    def get_dependencies(self, beat_id: str, stage: Optional[int] = None) -> List[str]:
        """
        Get all beats that depend on the given beat (transitively).

        Args:
            beat_id: Beat to check dependencies for
            stage: Optional stage number for progression beats

        Returns:
            List of beat IDs that would need to be untriggered
        """
        dep_graph = self.build_dependency_graph()

        # Find all transitive dependencies using BFS
        to_check = [beat_id]
        all_deps = []
        seen = set()

        while to_check:
            current = to_check.pop(0)
            if current in seen:
                continue
            seen.add(current)

            # Get direct dependents
            direct_deps = dep_graph.get(current, [])
            for dep in direct_deps:
                if dep not in all_deps:
                    all_deps.append(dep)
                    to_check.append(dep)

        logger.debug(f"Dependencies for {beat_id}: {all_deps}")
        return all_deps

    def untrigger_beat(
        self,
        user_id: str,
        beat_id: str,
        stage: Optional[int] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Untrigger a beat and all dependent beats (roll back delivery).

        Args:
            user_id: User identifier
            beat_id: Beat to untrigger
            stage: Optional stage to untrigger (for progression beats)
            dry_run: If True, only show what would be untriggered

        Returns:
            Dict with untrigger results
        """
        state = self.get_or_create_user_state(user_id)

        # Find all dependent beats
        dependent_beats = self.get_dependencies(beat_id, stage)

        # Get the beat to see if it's a progression beat
        beat = None
        for chapter_beats in self.beats.values():
            for b in chapter_beats:
                if b.id == beat_id:
                    beat = b
                    break
            if beat:
                break

        # Build result
        result = {
            "beat_id": beat_id,
            "stage": stage,
            "untriggered": [],
            "dependencies_affected": dependent_beats,
            "explanation": "",
            "dry_run": dry_run,
            "timestamp": datetime.utcnow()
        }

        # Check if beat exists and has progress
        beat_progress = state.get_beat_progress(beat_id)
        if not beat_progress:
            result["explanation"] = f"Beat '{beat_id}' has not been delivered yet."
            return result

        # For progression beats, check if any stages have been delivered
        if beat and beat.type == "progression":
            if not beat_progress.delivered_stages or len(beat_progress.delivered_stages) == 0:
                result["explanation"] = f"Beat '{beat_id}' has no stages delivered yet."
                return result
        # For one-shot beats, must be fully delivered
        elif not beat_progress.delivered:
            result["explanation"] = f"Beat '{beat_id}' has not been delivered yet."
            return result

        # Build explanation
        if beat and beat.type == "progression" and stage:
            result["explanation"] = (
                f"Untriggering stage {stage} of '{beat_id}' will roll back this stage "
                f"and all later stages."
            )
        else:
            result["explanation"] = f"Untriggering '{beat_id}' will remove this beat."

        if dependent_beats:
            result["explanation"] += (
                f" This will also untrigger {len(dependent_beats)} dependent beat(s): "
                f"{', '.join(dependent_beats)}."
            )

        # If dry run, just return the preview
        if dry_run:
            return result

        # Actually untrigger - start with dependent beats (reverse order)
        for dep_beat_id in reversed(dependent_beats):
            dep_progress = state.get_beat_progress(dep_beat_id)
            if dep_progress:
                # Remove beat progress
                if state.current_chapter in state.chapter_progress:
                    chapter_prog = state.chapter_progress[state.current_chapter]
                    if dep_beat_id in chapter_prog.beat_progress:
                        del chapter_prog.beat_progress[dep_beat_id]
                        result["untriggered"].append(dep_beat_id)
                        logger.info(f"Untriggered dependent beat '{dep_beat_id}' for user {user_id}")

        # Now untrigger the main beat
        if beat and beat.type == "progression" and stage:
            # For progression beats with stage, roll back that stage and later stages
            if beat_progress:
                # Remove the specified stage and all later stages
                beat_progress.delivered_stages = [s for s in beat_progress.delivered_stages if s < stage]

                # Update current stage
                if beat_progress.delivered_stages:
                    beat_progress.current_stage = max(beat_progress.delivered_stages)
                    beat_progress.delivered = False
                else:
                    # No stages left, remove beat entirely
                    if state.current_chapter in state.chapter_progress:
                        chapter_prog = state.chapter_progress[state.current_chapter]
                        if beat_id in chapter_prog.beat_progress:
                            del chapter_prog.beat_progress[beat_id]

                result["untriggered"].append(f"{beat_id} (stage {stage}+)")
                logger.info(f"Untriggered stage {stage}+ of '{beat_id}' for user {user_id}")
        else:
            # One-shot beat or full progression beat - remove entirely
            if state.current_chapter in state.chapter_progress:
                chapter_prog = state.chapter_progress[state.current_chapter]
                if beat_id in chapter_prog.beat_progress:
                    del chapter_prog.beat_progress[beat_id]
                    result["untriggered"].append(beat_id)
                    logger.info(f"Untriggered beat '{beat_id}' for user {user_id}")

        # Save state
        state.updated_at = datetime.utcnow()
        self._save_story_state(user_id, state)

        return result
