"""
Data models for tool call logging and inspection.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ToolCallStatus(str, Enum):
    """Status of a tool call execution"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class ToolCallLog(BaseModel):
    """Complete log entry for a single tool call"""

    # Identification
    call_id: str = Field(..., description="Unique identifier for this tool call")
    session_id: Optional[str] = Field(None, description="Session ID if available")
    interaction_id: Optional[str] = Field(None, description="Interaction ID if available")

    # Timing
    timestamp: datetime = Field(..., description="When the call was initiated")
    duration_ms: int = Field(..., description="Duration in milliseconds")

    # Tool information
    tool_name: str = Field(..., description="Name of the tool that was called")

    # Context
    character: Optional[str] = Field(None, description="Character who made the call (Delilah, Hank, etc.)")
    user_id: str = Field(..., description="User the interaction was for")

    # Request/Response
    request: Dict[str, Any] = Field(..., description="Tool call parameters")
    response: Dict[str, Any] = Field(..., description="Tool execution result")

    # Status
    status: ToolCallStatus = Field(..., description="Success or error status")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    # Optional context
    reasoning: Optional[str] = Field(None, description="Character's reasoning for the tool call")
    conversation_context: Optional[str] = Field(None, description="Relevant conversation context")

    # Replay tracking
    is_replay: bool = Field(default=False, description="Whether this was a replay of another call")
    replayed_from: Optional[str] = Field(None, description="Original call_id if this is a replay")

    # Phase 5.1: Orchestrator decision fields (only populated for request_handoff calls)
    orchestrator_decision: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "For request_handoff calls: orchestrator decision metadata. "
            "Keys: accepted (bool), rejected_reason (str|None). "
            "None for all other tool types."
        ),
    )
    resulted_in_character: Optional[str] = Field(
        default=None,
        description=(
            "For request_handoff calls: the character ID that was triggered "
            "as a result of the accepted handoff. None if the handoff was "
            "rejected or the tool is not request_handoff."
        ),
    )


class ToolCallFilter(BaseModel):
    """Filtering options for querying tool calls"""

    user_id: Optional[str] = None
    tool_name: Optional[str] = None
    character: Optional[str] = None
    status: Optional[ToolCallStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class ToolCallDetail(BaseModel):
    """Detailed view of a tool call for inspection"""

    # All log fields
    call: ToolCallLog

    # Additional computed fields
    formatted_timestamp: str = Field(..., description="Human-readable timestamp")
    duration_seconds: float = Field(..., description="Duration in seconds")
    request_preview: str = Field(..., description="Short preview of request")
    response_preview: str = Field(..., description="Short preview of response")


class ToolUsageStats(BaseModel):
    """Statistics for a specific tool"""

    tool_name: str
    total_calls: int
    success_count: int
    error_count: int
    success_rate: float = Field(..., description="Success rate as percentage (0-100)")
    avg_duration_ms: float
    min_duration_ms: int
    max_duration_ms: int
    last_used: Optional[datetime] = None


class CharacterUsageStats(BaseModel):
    """Statistics for a specific character"""

    character: str
    total_calls: int
    success_count: int
    error_count: int
    success_rate: float = Field(..., description="Success rate as percentage (0-100)")
    most_used_tool: Optional[str] = None
    avg_duration_ms: float


class ToolCallStatistics(BaseModel):
    """Aggregate statistics for tool call inspection"""

    # Overall stats
    total_calls: int
    total_successes: int
    total_errors: int
    overall_success_rate: float = Field(..., description="Overall success rate (0-100)")
    avg_duration_ms: float

    # Time range
    earliest_call: Optional[datetime] = None
    latest_call: Optional[datetime] = None

    # Breakdowns
    by_tool: List[ToolUsageStats] = Field(default_factory=list)
    by_character: List[CharacterUsageStats] = Field(default_factory=list)

    # Top lists
    slowest_calls: List[ToolCallLog] = Field(default_factory=list)
    recent_errors: List[ToolCallLog] = Field(default_factory=list)


class ReplayRequest(BaseModel):
    """Request to replay a tool call"""

    call_id: str = Field(..., description="ID of the call to replay")
    modified_request: Optional[Dict[str, Any]] = Field(
        None,
        description="Modified parameters (if None, use original)"
    )


class ReplayResult(BaseModel):
    """Result of replaying a tool call"""

    original_call: ToolCallLog
    new_call: ToolCallLog
    comparison: Dict[str, Any] = Field(
        ...,
        description="Comparison between original and new results"
    )
