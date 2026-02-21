"""
Data models for inter-character dialogue and handoffs.

This module defines the data structures used for multi-character
dialogue synthesis, including handoffs and character references.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class DialogueFragment:
    """
    A single fragment of dialogue from one character.
    
    Used to represent individual character contributions in
    multi-character responses, including handoffs.
    """
    character: str
    text: str
    voice_mode: str
    includes_handoff: bool
    handoff_to: Optional[str] = None


@dataclass
class SynthesizedDialogue:
    """
    A complete multi-character dialogue response.
    
    Combines multiple dialogue fragments into a cohesive
    multi-character response with appropriate handoffs.
    """
    fragments: List[DialogueFragment]
    full_text: str
    total_characters: int
    includes_handoffs: bool


@dataclass
class HandoffTemplate:
    """
    A template for natural handoff phrases between characters.
    
    Stores variations of handoff phrases to maintain naturalness
    and avoid repetition.
    """
    from_character: str
    to_character: str
    template: str
    usage_count: int = 0
    last_used: Optional[str] = None  # ISO timestamp


@dataclass
class CharacterRelationship:
    """
    Defines the relationship between two characters.
    
    Used to inject appropriate context into system prompts
    and guide inter-character dialogue style.
    """
    other_character: str
    relationship_type: str  # "colleague", "friend", "rival"
    trust_level: float  # 0.0 to 1.0
    descriptors: List[str]
    dialogue_style: List[str]
