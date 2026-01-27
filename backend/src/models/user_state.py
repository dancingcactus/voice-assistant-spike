"""
User state models for persistent storage.
Tracks user preferences, story progress, and conversation history.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    """User preferences and dietary information."""
    dietary_restrictions: List[str] = Field(default_factory=list, description="List of allergies and dietary restrictions")
    cooking_skill_level: Optional[str] = Field(default=None, description="User's cooking skill level (beginner, intermediate, advanced)")
    favorite_foods: List[str] = Field(default_factory=list, description="User's favorite foods")
    disliked_foods: List[str] = Field(default_factory=list, description="Foods the user dislikes")
    custom_preferences: Dict[str, Any] = Field(default_factory=dict, description="Other custom preferences")


class ConversationMessage(BaseModel):
    """A single message in the conversation history."""
    timestamp: datetime
    role: str  # "user" or "assistant"
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationHistory(BaseModel):
    """Conversation history with automatic windowing."""
    messages: List[ConversationMessage] = Field(default_factory=list)
    summary: Optional[str] = Field(default=None, description="Summary of older conversations")
    last_interaction: Optional[datetime] = None


class DeviceState(BaseModel):
    """State of a single device."""
    device_id: str
    device_type: str  # "light", "thermostat", "switch", etc.
    state: Dict[str, Any]  # e.g., {"on": True, "brightness": 50}
    last_updated: datetime


class DevicePreferences(BaseModel):
    """User preferences for device control."""
    devices: Dict[str, DeviceState] = Field(default_factory=dict)
    custom_scenes: Dict[str, List[str]] = Field(default_factory=dict, description="User-defined device scenes")


class StoryProgress(BaseModel):
    """User's progress through the story."""
    current_chapter: int = 1
    beats_delivered: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Map of beat_id to delivery info (stages delivered, timestamps, etc.)"
    )
    interaction_count: int = 0
    first_interaction: Optional[datetime] = None
    chapter_start_time: Optional[datetime] = None
    custom_story_data: Dict[str, Any] = Field(default_factory=dict, description="Additional story-specific data")


class UserState(BaseModel):
    """Complete user state for persistence."""
    user_id: str
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    conversation_history: ConversationHistory = Field(default_factory=ConversationHistory)
    device_preferences: DevicePreferences = Field(default_factory=DevicePreferences)
    story_progress: StoryProgress = Field(default_factory=StoryProgress)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()
