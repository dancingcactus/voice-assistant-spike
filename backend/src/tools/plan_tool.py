"""
Planning Tool - gives characters a first-class mechanism to create and
advance multi-step plans.

A character calls ``plan_action`` to:

- ``start``:  Outline a new plan with a title and an ordered list of steps.
- ``advance``: Mark the current step complete and move to the next one.
- ``complete``: End the plan early or confirm all steps are done.

The ``CharacterExecutor`` intercepts this tool call *before* it reaches
``execute()`` here — so this implementation is a safety fallback only.  If
``execute()`` is reached, the call was not intercepted and we return a no-op
``ToolResult`` with SUCCESS so the LLM message chain isn't broken.
"""

import logging
from typing import Dict, Any, List, Optional

from tools.tool_base import Tool, ToolContext, ToolResult, ToolResultStatus, ToolParameter

logger = logging.getLogger(__name__)

# Tool name constant used across the system.
PLAN_TOOL_NAME = "plan_action"


class PlanningTool(Tool):
    """
    Creates and advances multi-step coordinator plans.

    Characters call ``plan_action`` to outline a plan (``start``), move
    to the next step (``advance``), or finish it (``complete``).

    The ``CharacterExecutor`` intercepts this tool call before ``execute()``
    is reached.  ``execute()`` is a no-op safety fallback.
    """

    @property
    def name(self) -> str:
        return PLAN_TOOL_NAME

    @property
    def description(self) -> str:
        return (
            "Create and track a multi-step plan. "
            "Use action='start' with a title and steps list to outline a new plan. "
            "Use action='advance' to mark the current step complete and move to the next one. "
            "Use action='complete' to end the plan when all steps are finished."
        )

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description=(
                    "Plan action: 'start' to create a new plan, "
                    "'advance' to move to the next step, "
                    "'complete' to end the plan."
                ),
                required=True,
                enum=["start", "advance", "complete"],
            ),
            ToolParameter(
                name="title",
                type="string",
                description="Short title for the plan (required when action=start).",
                required=False,
            ),
            ToolParameter(
                name="steps",
                type="array",
                description=(
                    "Ordered list of step descriptions (required when action=start). "
                    "Each step should be a concise description of what happens in that step."
                ),
                required=False,
                items={"type": "string"},
            ),
            ToolParameter(
                name="notes",
                type="string",
                description="Optional notes about the current step when advancing.",
                required=False,
            ),
        ]

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        """
        Safety fallback — returns no-op SUCCESS.

        This method should normally never be reached because
        ``CharacterExecutor`` intercepts ``plan_action`` before it gets here.
        If it *is* reached (e.g., in a context without the Phase 5.1 executor),
        we log a warning and return a success so the LLM message chain stays
        valid.
        """
        action = kwargs.get("action", "unknown")
        title = kwargs.get("title", "")
        steps = kwargs.get("steps", [])

        logger.warning(
            "PlanningTool.execute() reached — should have been intercepted by "
            "CharacterExecutor. action=%s title=%r",
            action,
            title,
        )

        return ToolResult(
            status=ToolResultStatus.SUCCESS,
            message=f"Plan action '{action}' noted.",
            data={
                "intercepted": False,
                "action": action,
                "title": title,
                "steps": steps,
            },
        )
