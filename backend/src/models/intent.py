"""
Intent detection data models for Phase 4.5.

This module defines the data structures used for intent classification,
including intent results, sub-tasks, and intent logging.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Literal


# Intent categories supported by the system
IntentCategory = Literal["cooking", "household", "smart_home", "general", "multi_task"]

# Classification methods
ClassificationMethod = Literal["rule_based", "llm_assisted", "fallback"]


@dataclass
class SubTask:
    """
    Represents a single task extracted from a multi-task query.
    
    Attributes:
        text: The text of the sub-task
        intent: The intent category for this sub-task
        confidence: Confidence score (0.0 to 1.0) for this classification
    """
    text: str
    intent: IntentCategory
    confidence: float

    def __post_init__(self):
        """Validate confidence is in valid range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


@dataclass
class IntentResult:
    """
    Result of intent detection for a user query.
    
    Attributes:
        intent: The primary intent category detected
        confidence: Confidence score (0.0 to 1.0) for the classification
        classification_method: Method used to classify the intent
        sub_tasks: Optional list of sub-tasks for multi-task queries
    """
    intent: IntentCategory
    confidence: float
    classification_method: ClassificationMethod
    sub_tasks: Optional[List[SubTask]] = None

    def __post_init__(self):
        """Validate confidence and multi-task consistency."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        
        # If intent is multi_task, sub_tasks should be present
        if self.intent == "multi_task" and not self.sub_tasks:
            raise ValueError("multi_task intent requires sub_tasks to be provided")
        
        # If sub_tasks is provided, intent should be multi_task
        if self.sub_tasks and self.intent != "multi_task":
            raise ValueError("sub_tasks can only be provided for multi_task intent")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "intent": self.intent,
            "confidence": self.confidence,
            "classification_method": self.classification_method,
        }
        if self.sub_tasks:
            result["sub_tasks"] = [
                {
                    "text": st.text,
                    "intent": st.intent,
                    "confidence": st.confidence
                }
                for st in self.sub_tasks
            ]
        return result


@dataclass
class IntentLog:
    """
    Log entry for an intent detection operation.
    
    Used for observability and future analysis of intent detection performance.
    
    Attributes:
        timestamp: When the intent detection occurred
        user_id: ID of the user making the query
        query: The original user query
        intent_result: The result of intent detection
        processing_time_ms: Time taken to classify the intent (in milliseconds)
    """
    timestamp: datetime
    user_id: str
    query: str
    intent_result: IntentResult
    processing_time_ms: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON logging."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "query": self.query,
            "intent_result": self.intent_result.to_dict(),
            "processing_time_ms": self.processing_time_ms
        }
