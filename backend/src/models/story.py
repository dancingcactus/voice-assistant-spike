"""
Story Models - Data models for story beats, chapters, and user story state.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BeatVariant(BaseModel):
    """A single variant of a story beat."""
    delivery: str = Field(..., description="How to deliver: 'append' or 'replace'")
    content: str = Field(..., description="The text content of the story beat")


class BeatTrigger(BaseModel):
    """Trigger conditions for a story beat."""
    type: str = Field(..., description="Type of trigger: interaction_count, tool_use, user_engagement, etc.")
    min_interactions: Optional[int] = Field(None, description="Minimum interactions before trigger")
    max_interactions: Optional[int] = Field(None, description="Maximum interactions before trigger")
    tool_name: Optional[str] = Field(None, description="Tool name that triggers this beat")
    keywords: Optional[List[str]] = Field(None, description="Keywords that can trigger this beat")
    requires_direct_address: Optional[bool] = Field(False, description="Whether user must directly address character")


class BeatStage(BaseModel):
    """A stage in a progression beat."""
    stage: int = Field(..., description="Stage number")
    variants: Dict[str, BeatVariant] = Field(..., description="Variants for this stage (brief, standard, full)")


class StoryBeat(BaseModel):
    """A story beat definition."""
    title: Optional[str] = Field(None, description="Human-readable beat title")
    description: Optional[str] = Field(None, description="Optional beat description")
    id: str = Field(..., description="Unique beat identifier")
    type: str = Field(..., description="Beat type: one_shot or progression")
    required: bool = Field(..., description="Whether beat is required for chapter completion")
    priority: str = Field(..., description="Priority: early, normal, high, low")
    trigger: BeatTrigger = Field(..., description="Trigger conditions")
    variants: Optional[Dict[str, BeatVariant]] = Field(None, description="Variants for one-shot beats")
    stages: Optional[List[BeatStage]] = Field(None, description="Stages for progression beats")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Additional conditions")
    auto_advance: bool = Field(False, description="Whether this beat is auto-advance (not triggered in conversation)")
    content: Optional[str] = Field(None, description="Single rich content for auto-advance beats (no variants)")


class ConditionalRequirement(BaseModel):
    """Conditional progression requirement (N of M beats)."""
    n: int = Field(..., description="Number of beats required")
    beats: List[str] = Field(..., description="Beat IDs to choose from")


class ChapterCompletionCriteria(BaseModel):
    """Criteria for completing a chapter."""
    required_beats: List[str] = Field(..., description="Beat IDs required for completion")
    required_beat_stages: Optional[Dict[str, int]] = Field(None, description="Specific stages for progression beats")
    conditional_beats: Optional[ConditionalRequirement] = Field(None, description="N of M optional beats requirement")
    minimum_interactions: int = Field(..., description="Minimum number of interactions")
    minimum_time_elapsed_hours: float = Field(..., description="Minimum time elapsed in hours")


class ChapterUnlocks(BaseModel):
    """What gets unlocked when a chapter completes."""
    next_chapter: Optional[int] = Field(None, description="Next chapter ID")
    characters: List[str] = Field(..., description="Available characters")
    capabilities: List[str] = Field(..., description="Unlocked capabilities")


class ChapterPrerequisites(BaseModel):
    """Prerequisites for a chapter."""
    previous_chapter: Optional[int] = Field(None, description="Previous chapter that must be completed")


class Chapter(BaseModel):
    """A chapter definition."""
    id: int = Field(..., description="Chapter number")
    title: str = Field(..., description="Chapter title")
    description: str = Field(..., description="Chapter description")
    completion_criteria: ChapterCompletionCriteria = Field(..., description="Completion criteria")
    unlocks: ChapterUnlocks = Field(..., description="What this chapter unlocks")
    prerequisites: Optional[ChapterPrerequisites] = Field(None, description="Prerequisites")


class AutoAdvanceNotification(BaseModel):
    """Auto-advance beat ready for delivery."""
    beat_id: str = Field(..., description="Beat identifier")
    name: str = Field(..., description="Human-readable beat name")
    chapter_id: int = Field(..., description="Chapter this beat belongs to")
    ready_since: datetime = Field(..., description="When this beat became ready")
    content: str = Field(..., description="Full content to deliver")
    notified: bool = Field(False, description="Whether user has been notified")


class BeatProgress(BaseModel):
    """Progress tracking for a specific beat."""
    beat_id: str = Field(..., description="Beat identifier")
    current_stage: int = Field(1, description="Current stage (for progression beats)")
    delivered_stages: List[int] = Field(default_factory=list, description="Stages already delivered")
    delivered: bool = Field(False, description="Whether beat has been fully delivered")
    first_triggered: Optional[datetime] = Field(None, description="When beat was first triggered")
    last_delivered: Optional[datetime] = Field(None, description="When beat was last delivered")


class ChapterProgress(BaseModel):
    """Progress tracking for a chapter."""
    chapter_id: int = Field(..., description="Chapter number")
    started_at: datetime = Field(..., description="When chapter was started")
    completed_at: Optional[datetime] = Field(None, description="When chapter was completed")
    interaction_count: int = Field(0, description="Number of interactions in this chapter")
    beat_progress: Dict[str, BeatProgress] = Field(default_factory=dict, description="Progress for each beat")


class UserStoryState(BaseModel):
    """Complete story state for a user."""
    user_id: str = Field(..., description="User identifier")
    current_chapter: int = Field(1, description="Current chapter number")
    completed_chapters: List[int] = Field(default_factory=list, description="Completed chapter IDs")
    chapter_progress: Dict[int, ChapterProgress] = Field(default_factory=dict, description="Progress per chapter")
    auto_advance_queue: List[AutoAdvanceNotification] = Field(default_factory=list, description="Auto-advance beats ready for delivery")
    total_interactions: int = Field(0, description="Total interactions across all chapters")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When state was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When state was last updated")

    def get_beat_progress(self, beat_id: str) -> Optional[BeatProgress]:
        """Get progress for a specific beat in current chapter."""
        if self.current_chapter in self.chapter_progress:
            return self.chapter_progress[self.current_chapter].beat_progress.get(beat_id)
        return None

    def update_beat_progress(self, beat_id: str, stage: int = 1):
        """Update progress for a specific beat."""
        if self.current_chapter not in self.chapter_progress:
            self.chapter_progress[self.current_chapter] = ChapterProgress(
                chapter_id=self.current_chapter,
                started_at=datetime.utcnow()
            )

        chapter_prog = self.chapter_progress[self.current_chapter]

        if beat_id not in chapter_prog.beat_progress:
            chapter_prog.beat_progress[beat_id] = BeatProgress(
                beat_id=beat_id,
                first_triggered=datetime.utcnow()
            )

        beat_prog = chapter_prog.beat_progress[beat_id]
        beat_prog.current_stage = stage
        if stage not in beat_prog.delivered_stages:
            beat_prog.delivered_stages.append(stage)
        beat_prog.last_delivered = datetime.utcnow()

        self.updated_at = datetime.utcnow()

    def mark_beat_delivered(self, beat_id: str):
        """Mark a beat as fully delivered."""
        beat_prog = self.get_beat_progress(beat_id)
        if beat_prog:
            beat_prog.delivered = True
            self.updated_at = datetime.utcnow()

    def increment_interaction_count(self):
        """Increment interaction count for current chapter and total."""
        self.total_interactions += 1

        if self.current_chapter not in self.chapter_progress:
            self.chapter_progress[self.current_chapter] = ChapterProgress(
                chapter_id=self.current_chapter,
                started_at=datetime.utcnow()
            )

        self.chapter_progress[self.current_chapter].interaction_count += 1
        self.updated_at = datetime.utcnow()
