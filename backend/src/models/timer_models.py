"""
Timer models for observability.

Data models for timer information exposed via observability API.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TimerInfo(BaseModel):
    """Information about a timer for observability."""
    duration_seconds: int = Field(..., description="Timer duration in seconds")
    label: Optional[str] = Field(None, description="Optional timer label")
    start_time: datetime = Field(..., description="When the timer was started")
    end_time: datetime = Field(..., description="When the timer will/did expire")
    time_remaining: int = Field(..., description="Seconds remaining (0 if expired)")
    is_expired: bool = Field(..., description="Whether timer has expired")
    is_active: bool = Field(..., description="Whether timer is currently active (not expired)")


class TimersStatus(BaseModel):
    """Status of all timers for a session."""
    session_id: str = Field(..., description="Session identifier")
    active_timers: int = Field(..., description="Number of active timers")
    completed_timers: int = Field(..., description="Number of completed timers")
    timers: list[TimerInfo] = Field(default_factory=list, description="List of all timers")
