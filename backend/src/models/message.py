"""
Message models for communication between frontend and backend
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single message in the conversation"""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserMessage(BaseModel):
    """User message sent from frontend"""
    text: str = Field(..., description="User's message text")
    timestamp: Optional[datetime] = None


class AssistantResponse(BaseModel):
    """Assistant response sent to frontend"""
    text: str = Field(..., description="Assistant's response text")
    audio_url: Optional[str] = Field(None, description="URL to TTS audio file")
    character: str = Field(default="delilah", description="Character responding")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WebSocketMessage(BaseModel):
    """WebSocket message wrapper"""
    type: str = Field(..., description="Message type: 'user_message', 'assistant_response', 'error', 'status'")
    data: Dict[str, Any] = Field(..., description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationContext(BaseModel):
    """Context for a conversation session"""
    session_id: str
    user_id: str = Field(default="default_user")
    history: List[Message] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """A tool/function call from the LLM"""
    id: str = Field(..., description="Unique identifier for this tool call")
    type: str = Field(default="function", description="Type of tool call")
    function: Dict[str, str] = Field(..., description="Function name and arguments")


class LLMResponse(BaseModel):
    """Response from the LLM including content and metadata"""
    content: Optional[str] = Field(None, description="Text content of the response")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tool calls requested by LLM")
    finish_reason: str = Field(..., description="Reason the model stopped generating")
    usage: Dict[str, int] = Field(..., description="Token usage statistics")
    response_time: float = Field(..., description="Time taken to generate response")
