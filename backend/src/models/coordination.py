"""
Data models for coordination event tracking.

This module defines data structures for tracking multi-character
coordination events, calculating metrics, and managing progression
toward coordination milestones.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator


class CoordinationEvent(BaseModel):
    """
    A single coordination event between characters.
    
    Tracks handoffs, multi-task completions, sign-up patterns,
    and other coordination behaviors.
    """
    event_type: str = Field(..., description="Type: handoff, multi_task, sign_up, template_usage")
    timestamp: str = Field(..., description="ISO format datetime string")
    user_id: str
    from_character: Optional[str] = None
    to_character: Optional[str] = None
    intent: Optional[str] = None
    template_used: Optional[str] = None
    success: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def validate_timestamp(cls, v):
        """Convert datetime to ISO string if needed."""
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class CoordinationMetrics(BaseModel):
    """
    Aggregated metrics for coordination behavior.
    
    Provides analytics on handoff frequency, success rates,
    character interactions, and template usage patterns.
    """
    total_handoffs: int = 0
    handoff_success_rate: float = 0.0
    delilah_to_hank_count: int = 0
    hank_to_delilah_count: int = 0
    multi_task_completions: int = 0
    sign_up_pattern_count: int = 0
    template_usage: Dict[str, int] = Field(default_factory=dict)
    average_handoff_latency_ms: float = 0.0


class CoordinationMilestones(BaseModel):
    """
    Tracks progression toward coordination milestones.
    
    Milestones represent significant achievements in multi-character
    coordination that can trigger story beats or unlock capabilities.
    """
    first_handoff: bool = False
    first_multi_task: bool = False
    first_sign_up: bool = False
    five_handoffs: bool = False
    all_templates_used: bool = False


class CoordinationHistory(BaseModel):
    """
    Complete coordination history for a user.
    
    Stores all coordination events, calculated metrics,
    and milestone progression state.
    """
    events: List[CoordinationEvent] = Field(default_factory=list)
    metrics: CoordinationMetrics = Field(default_factory=CoordinationMetrics)
    milestones: CoordinationMilestones = Field(default_factory=CoordinationMilestones)
