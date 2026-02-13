"""
Character planning data models for Phase 4.5 Milestone 2.

This module defines the data structures used for character assignment
and task orchestration based on detected intents.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Literal
from enum import Enum


# Execution modes for character plans
class ExecutionMode(str, Enum):
    """
    Defines how a character plan should be executed.
    
    - SINGLE: Single character handles the entire query
    - SEQUENTIAL: Multiple characters handle tasks in sequence with handoffs
    - PARALLEL: Multiple characters can work simultaneously (future milestone)
    """
    SINGLE = "single"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"  # Reserved for future use


# Available characters in the system
CharacterName = Literal["delilah", "hank", "rex", "dimitria"]


@dataclass
class CharacterTask:
    """
    Represents a single task assigned to a character.
    
    Attributes:
        character: The character assigned to this task ("delilah", "hank", etc.)
        task_description: Human-readable description of what the character should do
        intent: The intent category for this task
        confidence: Confidence score (0.0 to 1.0) for this task assignment
        requires_handoff: Whether this task requires a handoff from another character
        handoff_from: The character this task receives a handoff from (if applicable)
        estimated_duration_ms: Estimated time to complete this task in milliseconds
        metadata: Additional information about this task
    """
    character: CharacterName
    task_description: str
    intent: str
    confidence: float
    requires_handoff: bool = False
    handoff_from: Optional[CharacterName] = None
    estimated_duration_ms: int = 1500
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate confidence and handoff logic."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        
        # If requires_handoff is True, handoff_from must be set
        if self.requires_handoff and not self.handoff_from:
            raise ValueError("requires_handoff is True but handoff_from is not set")
        
        # If handoff_from is set, requires_handoff should be True
        if self.handoff_from and not self.requires_handoff:
            raise ValueError("handoff_from is set but requires_handoff is False")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "character": self.character,
            "task_description": self.task_description,
            "intent": self.intent,
            "confidence": self.confidence,
            "requires_handoff": self.requires_handoff,
            "handoff_from": self.handoff_from,
            "estimated_duration_ms": self.estimated_duration_ms,
            "metadata": self.metadata
        }


@dataclass
class CharacterPlan:
    """
    Complete execution plan for handling a user query with character assignments.
    
    Attributes:
        tasks: List of character tasks to execute
        execution_mode: How the plan should be executed (single/sequential/parallel)
        total_confidence: Overall confidence in this plan (weighted average of task confidence)
        estimated_total_duration_ms: Total estimated time to complete all tasks
        metadata: Additional information about the plan
    """
    tasks: List[CharacterTask]
    execution_mode: ExecutionMode
    total_confidence: float
    estimated_total_duration_ms: int
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate plan consistency."""
        if not self.tasks:
            raise ValueError("CharacterPlan must have at least one task")
        
        if not 0.0 <= self.total_confidence <= 1.0:
            raise ValueError(f"Total confidence must be between 0.0 and 1.0, got {self.total_confidence}")
        
        # Validate execution mode matches task structure
        if self.execution_mode == ExecutionMode.SINGLE and len(self.tasks) > 1:
            # Check if all tasks are for the same character
            characters = set(task.character for task in self.tasks)
            if len(characters) > 1:
                raise ValueError("ExecutionMode.SINGLE requires all tasks to be for the same character")
        
        # Validate handoff chain for sequential execution
        if self.execution_mode == ExecutionMode.SEQUENTIAL and len(self.tasks) > 1:
            for i, task in enumerate(self.tasks):
                if i == 0:
                    # First task should not have a handoff_from
                    if task.requires_handoff:
                        raise ValueError("First task in sequential plan should not require handoff")
                else:
                    # Subsequent tasks with different characters should have handoffs
                    prev_character = self.tasks[i-1].character
                    if task.character != prev_character and not task.requires_handoff:
                        raise ValueError(
                            f"Task {i} changes character but does not require handoff"
                        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "tasks": [task.to_dict() for task in self.tasks],
            "execution_mode": self.execution_mode.value,
            "total_confidence": self.total_confidence,
            "estimated_total_duration_ms": self.estimated_total_duration_ms,
            "metadata": self.metadata
        }


@dataclass
class PlanLog:
    """
    Log entry for a character planning operation.
    
    Used for observability and future analysis of planning performance.
    
    Attributes:
        timestamp: When the planning occurred
        user_id: ID of the user making the query
        query: The original user query
        intent_category: The primary intent detected
        character_plan: The resulting character plan
        processing_time_ms: Time taken to create the plan (in milliseconds)
        current_chapter: The story chapter the user is in
        metadata: Additional logging information
    """
    timestamp: datetime
    user_id: str
    query: str
    intent_category: str
    character_plan: CharacterPlan
    processing_time_ms: float
    current_chapter: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON logging."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "query": self.query,
            "intent_category": self.intent_category,
            "character_plan": self.character_plan.to_dict(),
            "processing_time_ms": self.processing_time_ms,
            "current_chapter": self.current_chapter,
            "metadata": self.metadata
        }
