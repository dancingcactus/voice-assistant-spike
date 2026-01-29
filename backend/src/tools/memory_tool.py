"""
Memory Tool - Allows AI to save user memories during conversation.

This tool enables the AI to automatically extract and store important information
about users, such as dietary restrictions, preferences, facts, relationships, and events.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from pathlib import Path

from tools.tool_base import (
    Tool,
    ToolContext,
    ToolResult,
    ToolResultStatus,
    ToolParameter
)

logger = logging.getLogger(__name__)


class MemoryTool(Tool):
    """Tool for saving user memories during conversation."""

    def __init__(self):
        """Initialize the memory tool."""
        super().__init__()

    @property
    def name(self) -> str:
        return "save_memory"

    @property
    def description(self) -> str:
        return (
            "Save important information about the user for future reference. "
            "Use this when the user shares facts about themselves, preferences, "
            "dietary restrictions, family information, or upcoming events."
        )

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="category",
                type="string",
                description=(
                    "Type of memory:\n"
                    "- fact: Objective info (location, job, hobbies)\n"
                    "- preference: Likes/dislikes (food preferences, cooking style)\n"
                    "- dietary_restriction: Health/diet needs (allergies, Celiac, vegetarian)\n"
                    "- relationship: Family/friends (kids, spouse, pets)\n"
                    "- event: Time-bound events (appointments, parties, trips)"
                ),
                required=True,
                enum=["fact", "preference", "dietary_restriction", "relationship", "event"]
            ),
            ToolParameter(
                name="content",
                type="string",
                description=(
                    "Clear, concise description of the memory. "
                    "Examples:\n"
                    "- 'Has Celiac disease (gluten intolerance)'\n"
                    "- 'Likes mild foods'\n"
                    "- 'Lives in Provo, Utah'\n"
                    "- 'Has 3 kids'\n"
                    "- 'Parent-teacher conferences on Tuesday'"
                ),
                required=True
            ),
            ToolParameter(
                name="importance",
                type="integer",
                description=(
                    "Importance level (1-10):\n"
                    "- 10: Critical safety (severe allergies)\n"
                    "- 8-9: Very important (dietary restrictions, health)\n"
                    "- 6-7: Important (family, regular preferences)\n"
                    "- 4-5: Useful context (location, work)\n"
                    "- 1-3: Nice to know (minor preferences)"
                ),
                required=True
            ),
            ToolParameter(
                name="metadata",
                type="object",
                description="Optional additional structured data (event_date, severity, etc.)",
                required=False
            ),
        ]

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        """
        Save a memory for the user.

        Args:
            context: Tool execution context
            **kwargs: Tool parameters (category, content, importance, metadata)

        Returns:
            ToolResult with success status and memory_id
        """
        category = kwargs.get("category")
        content = kwargs.get("content")
        importance = kwargs.get("importance", 5)
        metadata = kwargs.get("metadata", {})

        if not category or not content:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="Missing required fields: category and content",
                error="category and content are required parameters"
            )

        # Validate category
        valid_categories = [
            "fact", "preference", "dietary_restriction",
            "relationship", "event"
        ]
        if category not in valid_categories:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"Invalid category. Must be one of: {valid_categories}",
                error=f"Invalid category: {category}"
            )

        # Validate importance
        if not isinstance(importance, int) or importance < 1 or importance > 10:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="Importance must be an integer between 1 and 10",
                error=f"Invalid importance: {importance}"
            )

        try:
            # Import memory accessor
            from observability.memory_access import MemoryAccessor

            # Initialize memory accessor with correct data directory
            data_dir = Path(__file__).parent.parent.parent / "data"
            memory_accessor = MemoryAccessor(str(data_dir))

            # Create memory
            memory = memory_accessor.create_memory(
                user_id=context.user_id,
                category=category,
                content=content,
                source=f"conversation_{datetime.now().isoformat()}",
                importance=importance,
                verified=False,  # Will be verified over time
                metadata=metadata
            )

            logger.info(
                f"Saved memory for user {context.user_id}: "
                f"{category} - {content} (importance: {importance})"
            )

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"Saved {category}: {content}",
                data={
                    "memory_id": memory.memory_id,
                    "category": category,
                    "importance": importance
                }
            )

        except ValueError as e:
            # User not found
            logger.error(f"User not found: {context.user_id}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"User {context.user_id} not found",
                error=str(e)
            )

        except Exception as e:
            logger.error(f"Failed to save memory: {str(e)}", exc_info=True)
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="Failed to save memory due to an internal error",
                error=str(e)
            )
