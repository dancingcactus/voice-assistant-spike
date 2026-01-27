"""Tool System - manages tool registration and execution."""
import logging
from typing import Dict, List, Optional, Any

from tools.tool_base import Tool, ToolContext, ToolResult, ToolResultStatus

logger = logging.getLogger(__name__)


class ToolSystem:
    """
    Central system for managing and executing tools.

    Responsibilities:
    - Register tools
    - Convert tools to OpenAI function calling format
    - Execute tool calls
    - Handle errors and timeouts
    """

    def __init__(self):
        """Initialize the Tool System."""
        self.tools: Dict[str, Tool] = {}
        logger.info("Tool System initialized")

    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool for use.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If a tool with the same name is already registered
        """
        if tool.name in self.tools:
            raise ValueError(f"Tool already registered: {tool.name}")

        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def unregister_tool(self, tool_name: str) -> None:
        """
        Unregister a tool.

        Args:
            tool_name: Name of the tool to unregister
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """Get list of registered tool names."""
        return list(self.tools.keys())

    def get_openai_functions(self) -> List[Dict[str, Any]]:
        """
        Get all tools in OpenAI function calling format.

        Returns:
            List of function definitions for OpenAI API
        """
        return [tool.to_openai_function() for tool in self.tools.values()]

    async def execute_tool(
        self,
        tool_name: str,
        context: ToolContext,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute a tool with given arguments.

        Args:
            tool_name: Name of the tool to execute
            context: Execution context
            arguments: Tool arguments from LLM

        Returns:
            ToolResult with execution status and data
        """
        tool = self.get_tool(tool_name)

        if not tool:
            logger.error(f"Tool not found: {tool_name}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"Tool not found: {tool_name}",
                error="TOOL_NOT_FOUND"
            )

        try:
            logger.info(
                f"Executing tool: {tool_name} with arguments: {arguments}"
            )

            # Execute the tool
            result = await tool.execute(context, **arguments)

            logger.info(
                f"Tool {tool_name} completed with status: {result.status}"
            )

            return result

        except TypeError as e:
            # Parameter mismatch
            logger.error(f"Invalid parameters for tool {tool_name}: {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"Invalid parameters for {tool_name}",
                error=str(e)
            )

        except Exception as e:
            # Unexpected error
            logger.error(
                f"Error executing tool {tool_name}: {e}",
                exc_info=True
            )
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"Error executing {tool_name}",
                error=str(e)
            )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get Tool System statistics.

        Returns:
            Dict with tool count and registered tools
        """
        return {
            "total_tools": len(self.tools),
            "registered_tools": list(self.tools.keys())
        }
