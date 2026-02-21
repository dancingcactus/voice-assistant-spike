"""Base classes for tools in the Tool System."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ToolResultStatus(str, Enum):
    """Status of a tool execution result."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


class ToolResult(BaseModel):
    """Result from executing a tool."""
    status: ToolResultStatus = Field(..., description="Execution status")
    message: str = Field(..., description="Human-readable result message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Structured result data")
    error: Optional[str] = Field(default=None, description="Error details if status is ERROR")


class ToolContext(BaseModel):
    """Context information available to tools during execution."""
    user_id: str = Field(..., description="ID of the user making the request")
    session_id: str = Field(..., description="Current conversation session ID")
    character_id: Optional[str] = Field(default=None, description="Active character ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ToolParameter(BaseModel):
    """Definition of a tool parameter for OpenAI function calling."""
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (string, number, boolean, array, object, etc.)")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=False, description="Whether parameter is required")
    enum: Optional[List[str]] = Field(default=None, description="Allowed values")
    default: Optional[Any] = Field(default=None, description="Default value")
    items: Optional[Dict[str, Any]] = Field(default=None, description="Schema for array items (required when type=array)")


class Tool(ABC):
    """
    Abstract base class for all tools.

    Tools implement specific capabilities (timers, device control, recipes, etc.)
    and are exposed to the LLM via OpenAI function calling.
    """

    def __init__(self):
        """Initialize the tool."""
        self._validate_definition()

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Tool name (used in function calling).
        Must be lowercase, alphanumeric with underscores only.
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Tool description shown to the LLM.
        Should clearly explain what the tool does and when to use it.
        """
        pass

    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """
        List of parameters the tool accepts.
        Used to generate OpenAI function calling schema.
        """
        pass

    @abstractmethod
    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters.

        Args:
            context: Execution context (user_id, session_id, etc.)
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with status, message, and optional data
        """
        pass

    def _validate_definition(self):
        """Validate tool definition on initialization."""
        # Validate name format
        name = self.name
        if not name.replace('_', '').isalnum() or not name.islower():
            raise ValueError(
                f"Tool name must be lowercase alphanumeric with underscores: {name}"
            )

        # Validate description exists
        if not self.description or len(self.description) < 10:
            raise ValueError(
                f"Tool description must be at least 10 characters: {name}"
            )

        # Validate parameters
        param_names = set()
        for param in self.parameters:
            if param.name in param_names:
                raise ValueError(
                    f"Duplicate parameter name in tool {name}: {param.name}"
                )
            param_names.add(param.name)

    def to_openai_function(self) -> Dict[str, Any]:
        """
        Convert tool definition to OpenAI function calling format.

        Returns:
            Dict in OpenAI function schema format
        """
        # Build parameters schema
        properties = {}
        required = []

        for param in self.parameters:
            param_schema = {
                "type": param.type,
                "description": param.description
            }

            if param.enum:
                param_schema["enum"] = param.enum

            if param.default is not None:
                param_schema["default"] = param.default

            # OpenAI requires 'items' for array type parameters
            if param.type == "array":
                param_schema["items"] = param.items if param.items else {"type": "object"}

            properties[param.name] = param_schema

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    def __repr__(self) -> str:
        """String representation of the tool."""
        return f"<Tool: {self.name}>"
