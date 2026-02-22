"""Character models for personality and voice mode management."""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class VoiceMode(BaseModel):
    """Represents a specific voice mode for a character."""
    id: str = Field(..., description="Unique identifier for this mode")
    name: str = Field(..., description="Human-readable mode name")
    triggers: List[str] = Field(..., description="Contexts that activate this mode")
    characteristics: List[str] = Field(..., description="Behavioral changes in this mode")
    example_phrases: List[str] = Field(..., description="Sample phrases for this mode")
    response_style: str = Field(..., description="Overall style guide for responses")


class Personality(BaseModel):
    """Core personality traits and patterns."""
    core_traits: List[str] = Field(..., description="Fundamental characteristics")
    speech_patterns: List[str] = Field(..., description="How character speaks")
    mannerisms: Optional[List[str]] = Field(default=None, description="Behavioral quirks")


class ContextAwareness(BaseModel):
    """What the character tracks and remembers."""
    remembers: Optional[List[str]] = Field(default=None, description="Info to retain")
    tracks: Optional[List[str]] = Field(default=None, description="Active state to monitor")


class StoryArc(BaseModel):
    """Character development and narrative progression."""
    chapter_1: Optional[str] = Field(default=None, description="State in Chapter 1")
    internal_conflict: Optional[str] = Field(default=None, description="Core struggle")
    coping_mechanism: Optional[str] = Field(default=None, description="How they cope")


class CharacterRelationship(BaseModel):
    """Relationship between characters."""
    dynamic: str = Field(..., description="Nature of the relationship")
    interaction_style: str = Field(..., description="Communication style")
    running_gags: Optional[List[str]] = Field(default=None, description="Recurring patterns")


class Character(BaseModel):
    """Complete character definition."""
    id: str = Field(..., description="Unique character identifier")
    name: str = Field(..., description="Full name")
    display_name: Optional[str] = Field(default=None, description="Short display name shown in the UI")
    nickname: Optional[str] = Field(default=None, description="Informal name")
    role: str = Field(..., description="Primary role or expertise")
    description: Optional[str] = Field(default=None, description="Brief description")

    personality: Personality
    voice_modes: List[VoiceMode] = Field(..., min_items=1)

    context_awareness: Optional[ContextAwareness] = Field(default=None)
    tool_instructions: Optional[Dict[str, Dict[str, Any]]] = Field(default=None, description="Instructions for using tools")
    story_arc: Optional[StoryArc] = Field(default=None)
    available_tools: Optional[List[str]] = Field(default=None, description="Tool names this character can use")
    capabilities: List[str] = Field(..., min_items=1)
    relationships: Optional[Dict[str, CharacterRelationship]] = Field(default=None)

    def get_voice_mode(self, mode_id: str) -> Optional[VoiceMode]:
        """Get a specific voice mode by ID."""
        for mode in self.voice_modes:
            if mode.id == mode_id:
                return mode
        return None

    def find_matching_voice_mode(self, user_input: str) -> VoiceMode:
        """
        Find the best matching voice mode based on user input.
        Returns the first matching mode, or warm_baseline/first mode as fallback.
        """
        user_lower = user_input.lower()

        # Check each mode's triggers
        # We check for keywords within the trigger strings
        for mode in self.voice_modes:
            for trigger in mode.triggers:
                trigger_lower = trigger.lower()
                # Extract keywords from trigger (simple split on spaces/punctuation)
                trigger_words = trigger_lower.replace(',', ' ').replace('(', ' ').replace(')', ' ').split()

                # Check if any significant trigger words appear in user input
                for word in trigger_words:
                    if len(word) > 3 and word in user_lower:  # Only match words > 3 chars
                        return mode

                # Also check if the trigger phrase appears in user input
                if trigger_lower in user_lower or user_lower in trigger_lower:
                    return mode

        # Fallback to warm_baseline if it exists
        baseline = self.get_voice_mode("warm_baseline")
        if baseline:
            return baseline

        # Ultimate fallback to first mode
        return self.voice_modes[0]


class VoiceModeSelection(BaseModel):
    """Result of voice mode selection."""
    mode: VoiceMode
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in selection")
    reasoning: Optional[str] = Field(default=None, description="Why this mode was selected")
