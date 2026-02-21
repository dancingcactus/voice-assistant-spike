"""
Character assignment configuration for Phase 4.5 Milestone 2.

This module defines which characters handle which intents based on the current story chapter.
Character availability is chapter-dependent:
- Chapter 1: Only Delilah is available
- Chapter 2+: Delilah and Hank are available
- Chapter 3+: Delilah, Hank, and Rex are available
- Future: Dimitria joins in later chapters
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class CharacterAssignment:
    """
    Defines character assignment rules for an intent.
    
    Attributes:
        primary: The primary character who should handle this intent
        fallback: Backup character if primary is unavailable or confidence is low
        confidence_threshold: Minimum confidence required to use primary character
        note: Optional explanation of the assignment logic
        domain_description: Short description of the character's domain, used in
            the ConversationRouter prompt so the LLM understands each character's scope.
    """
    primary: Optional[str]
    fallback: Optional[str]
    confidence_threshold: float
    note: Optional[str] = None
    domain_description: str = ""  # Used in router prompt


# Domain descriptions per character (chapter-independent).
# Injected into the ConversationRouter LLM prompt.
CHARACTER_DOMAIN_DESCRIPTIONS: Dict[str, str] = {
    "delilah": "cooking, recipes, meal planning, food advice, kitchen timers",
    "hank": "shopping lists, task management, reminders, scheduling, practical logistics",
    "rex": "smart home control, automation, device coordination, team leadership",
    "dimitria": "advanced automations, technical devices, engineering solutions",
}


# Registered handoff pairs per chapter.
# Keys are chapter IDs; values are lists of (from_character, to_character) tuples.
# The ConversationRouter and CharacterExecutor only advertise / accept handoffs
# for pairs that are registered for the current chapter.
REGISTERED_HANDOFF_PAIRS: Dict[int, List[Tuple[str, str]]] = {
    2: [("delilah", "hank"), ("hank", "delilah")],
    3: [("delilah", "hank"), ("hank", "delilah"), ("rex", "delilah"), ("rex", "hank")],
}


# Character assignments for Chapter 1 (Delilah only)
CHAPTER_1_ASSIGNMENTS: Dict[str, CharacterAssignment] = {
    "cooking": CharacterAssignment(
        primary="delilah",
        fallback=None,
        confidence_threshold=0.5,
        note="Delilah handles all cooking queries with enthusiasm"
    ),
    "household": CharacterAssignment(
        primary="delilah",
        fallback=None,
        confidence_threshold=0.5,
        note="Delilah handles household tasks but uses DEADPAN mode"
    ),
    "smart_home": CharacterAssignment(
        primary="delilah",
        fallback=None,
        confidence_threshold=0.6,
        note="Delilah can handle smart home but less confident"
    ),
    "general": CharacterAssignment(
        primary="delilah",
        fallback=None,
        confidence_threshold=0.3,
        note="Delilah handles general queries"
    ),
    "multi_task": CharacterAssignment(
        primary="delilah",
        fallback=None,
        confidence_threshold=0.5,
        note="Delilah handles all sub-tasks sequentially"
    )
}


# Character assignments for Chapter 2+ (Delilah + Hank)
CHAPTER_2_PLUS_ASSIGNMENTS: Dict[str, CharacterAssignment] = {
    "cooking": CharacterAssignment(
        primary="delilah",
        fallback=None,
        confidence_threshold=0.5,
        note="Delilah owns the cooking domain"
    ),
    "household": CharacterAssignment(
        primary="hank",
        fallback="delilah",
        confidence_threshold=0.5,
        note="Hank handles practical household tasks (lists, calendar, organization)"
    ),
    "smart_home": CharacterAssignment(
        primary="hank",
        fallback="delilah",
        confidence_threshold=0.6,
        note="Hank handles smart home control and devices"
    ),
    "general": CharacterAssignment(
        primary=None,  # Both characters can bid on general queries
        fallback="delilah",
        confidence_threshold=0.3,
        note="Both characters can handle general queries based on context"
    ),
    "multi_task": CharacterAssignment(
        primary=None,  # Tasks are split between characters
        fallback="delilah",
        confidence_threshold=0.5,
        note="Multi-task queries are decomposed and assigned per sub-task"
    )
}


# Character assignments for Chapter 3+ (Delilah + Hank + Rex)
CHAPTER_3_PLUS_ASSIGNMENTS: Dict[str, CharacterAssignment] = {
    "cooking": CharacterAssignment(
        primary="delilah",
        fallback=None,
        confidence_threshold=0.5,
        note="Delilah owns the cooking domain"
    ),
    "household": CharacterAssignment(
        primary="hank",
        fallback="delilah",
        confidence_threshold=0.5,
        note="Hank handles practical tasks with Rex coordinating complex plans"
    ),
    "smart_home": CharacterAssignment(
        primary="rex",
        fallback="hank",
        confidence_threshold=0.6,
        note="Rex loves smart home control and science experiments"
    ),
    "general": CharacterAssignment(
        primary=None,  # All characters can bid
        fallback="rex",
        confidence_threshold=0.3,
        note="Rex coordinates general queries and manages the team"
    ),
    "multi_task": CharacterAssignment(
        primary="rex",
        fallback="delilah",
        confidence_threshold=0.5,
        note="Rex coordinates multi-task queries and delegates to the team"
    )
}


# Default fallback character when everything else fails
DEFAULT_CHARACTER = "delilah"


def get_character_assignments(chapter_id: int) -> Dict[str, CharacterAssignment]:
    """
    Get the character assignment rules for the current chapter.
    
    Args:
        chapter_id: The current story chapter ID
        
    Returns:
        Dictionary mapping intent categories to character assignments
    """
    if chapter_id == 1:
        return CHAPTER_1_ASSIGNMENTS
    elif chapter_id == 2:
        return CHAPTER_2_PLUS_ASSIGNMENTS
    elif chapter_id >= 3:
        return CHAPTER_3_PLUS_ASSIGNMENTS
    else:
        # Fallback to Chapter 1 if chapter_id is invalid
        return CHAPTER_1_ASSIGNMENTS


def get_available_characters(chapter_id: int) -> List[str]:
    """
    Get the list of available characters for the current chapter.
    
    Args:
        chapter_id: The current story chapter ID
        
    Returns:
        List of available character names
    """
    if chapter_id == 1:
        return ["delilah"]
    elif chapter_id == 2:
        return ["delilah", "hank"]
    elif chapter_id >= 3:
        return ["delilah", "hank", "rex"]
    else:
        return ["delilah"]


def get_character_for_intent(
    intent: str,
    chapter_id: int,
    confidence: float = 1.0
) -> str:
    """
    Get the appropriate character for an intent based on chapter and confidence.
    
    Args:
        intent: The intent category
        chapter_id: The current story chapter ID
        confidence: The confidence score for the intent classification
        
    Returns:
        The character name who should handle this intent
    """
    assignments = get_character_assignments(chapter_id)
    
    # Get assignment for this intent, fall back to general if not found
    assignment = assignments.get(intent, assignments.get("general"))
    
    if not assignment:
        return DEFAULT_CHARACTER
    
    # If confidence is below threshold, use fallback
    if confidence < assignment.confidence_threshold:
        return assignment.fallback or DEFAULT_CHARACTER
    
    # Return primary character, or fallback if primary is None
    return assignment.primary or assignment.fallback or DEFAULT_CHARACTER
