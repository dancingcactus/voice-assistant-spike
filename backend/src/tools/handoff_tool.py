"""
Handoff Tool - signals that a character wants to pass work to another character.

This tool gives characters a first-class, explicit mechanism to initiate a
handoff rather than relying on the orchestrator to detect handoff prose.
When a character calls ``request_handoff``, the ``CharacterExecutor`` intercepts
the tool call *before* it reaches ``execute()`` here — so this implementation
is a safety fallback only.  If ``execute()`` is reached, the call was not
intercepted and we return a no-op ``ToolResult`` with SUCCESS so the LLM
message chain isn't broken.

Chapter-awareness
-----------------
The ``to_character`` enum is populated at instantiation time from the list of
valid secondary targets supplied by the caller (typically derived from
``REGISTERED_HANDOFF_PAIRS[chapter_id]`` filtered to available characters).
This ensures the LLM only sees characters that are actually reachable in the
current session.
"""

import logging
from typing import Dict, Any, List, Optional

from tools.tool_base import Tool, ToolContext, ToolResult, ToolResultStatus, ToolParameter

logger = logging.getLogger(__name__)


class HandoffTool(Tool):
    """
    Signals that the current character has completed their part of a task and
    a follow-up action is needed from a different character.

    The ``CharacterExecutor`` intercepts this tool call before ``execute()``
    is reached.  ``execute()`` is a no-op safety fallback.

    Args:
        available_secondaries: List of character IDs that can receive a handoff
            (e.g. ``["hank"]`` for Delilah in chapter 2).  If empty, the tool
            is registered with an empty enum which will not allow the LLM to
            select any target.
    """

    def __init__(self, available_secondaries: Optional[List[str]] = None):
        """
        Initialise the handoff tool.

        Args:
            available_secondaries: Characters that can receive a handoff.
                Defaults to ``["hank"]`` as the most common secondary in
                chapter 2.
        """
        self._available_secondaries: List[str] = (
            list(available_secondaries) if available_secondaries is not None else ["hank"]
        )
        super().__init__()

    @property
    def name(self) -> str:
        return "request_handoff"

    @property
    def description(self) -> str:
        return (
            "Signal that you have completed your part of the task and would like another "
            "character to handle a follow-up action. Call this when you have finished "
            "dealing with your domain and there is clearly remaining work for a different "
            "character (for example, after describing a recipe, Hank can build the "
            "shopping list). You may speak your handoff naturally alongside the tool call — "
            "your spoken words will appear in the response. Do NOT use request_handoff "
            "when the full task is within your own domain. Do NOT use it speculatively — "
            "only call it when the information the other character needs actually exists "
            "in this conversation."
        )

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="to_character",
                type="string",
                description="The character who should handle the follow-up",
                required=True,
        enum=self._available_secondaries if self._available_secondaries else None,
            ),
            ToolParameter(
                name="task_summary",
                type="string",
                description=(
                    "Brief description of what the other character should do (1–2 sentences)"
                ),
                required=True,
            ),
            ToolParameter(
                name="items",
                type="array",
                description=(
                    "Optional structured list of items to pass to the next character "
                    "(e.g., ingredients for a shopping list)"
                ),
                required=False,
                items={"type": "string"},
            ),
        ]

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        """
        Safety fallback — returns no-op SUCCESS.

        This method should normally never be reached because ``CharacterExecutor``
        intercepts ``request_handoff`` before it gets here.  If it *is* reached
        (e.g., in a context without the Phase 5.1 executor), we log a warning and
        return a success so the LLM message chain stays valid.
        """
        to_character = kwargs.get("to_character", "unknown")
        task_summary = kwargs.get("task_summary", "")
        items = kwargs.get("items", [])

        logger.warning(
            "HandoffTool.execute() reached — should have been intercepted by "
            "CharacterExecutor. to_character=%s task_summary=%r items=%s",
            to_character,
            task_summary,
            items,
        )

        return ToolResult(
            status=ToolResultStatus.SUCCESS,
            message=(
                f"Handoff signal noted: {to_character} will handle the follow-up."
            ),
            data={
                "to_character": to_character,
                "task_summary": task_summary,
                "items": items,
                "intercepted": False,
            },
        )
