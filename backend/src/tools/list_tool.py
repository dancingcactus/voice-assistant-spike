"""List Tool - manage shopping lists, todo lists, and other lists."""
from typing import Dict, Any, List as TypeList, Optional
import logging

from tools.tool_base import (
    Tool,
    ToolContext,
    ToolResult,
    ToolResultStatus,
    ToolParameter
)
from core.list_manager import ListManager

logger = logging.getLogger(__name__)


class ListTool(Tool):
    """Tool for managing user lists (shopping, todo, etc.)."""

    def __init__(self, data_dir: str = "data"):
        """Initialize the list tool."""
        self.list_manager = ListManager(data_dir=data_dir)
        super().__init__()

    @property
    def name(self) -> str:
        return "manage_list"

    @property
    def description(self) -> str:
        return (
            "Manage user lists such as shopping lists, grocery lists, and todo lists. "
            "Can create lists, add items, mark items complete, update items, and more. "
            "Use this when the user wants to manage items in a list."
        )

    @property
    def parameters(self) -> TypeList[ToolParameter]:
        return [
            ToolParameter(
                name="operation",
                type="string",
                description=(
                    "Operation to perform: 'create_list', 'rename_list', 'delete_list', "
                    "'add_items', 'update_item', 'complete_item', 'remove_item', "
                    "'get_list', 'get_recent_items'"
                ),
                required=True,
                enum=[
                    "create_list", "rename_list", "delete_list",
                    "add_items", "update_item", "complete_item", "remove_item",
                    "get_list", "get_recent_items"
                ]
            ),
            ToolParameter(
                name="list_name",
                type="string",
                description="Name of the list (e.g., 'Groceries', 'Costco List', 'Todo List')",
                required=False
            ),
            ToolParameter(
                name="new_name",
                type="string",
                description="New name for the list (used with 'rename_list' operation)",
                required=False
            ),
            ToolParameter(
                name="items",
                type="array",
                description=(
                    "Array of items to add. Each item can have 'name' (required), "
                    "'description' (optional), and 'quantity' (optional). "
                    "Example: [{'name': 'milk', 'quantity': '1 gallon'}, {'name': 'eggs', 'quantity': '12'}]"
                ),
                required=False,
                items={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Item name"},
                        "description": {"type": "string", "description": "Optional description"},
                        "quantity": {"type": "string", "description": "Optional quantity"}
                    },
                    "required": ["name"]
                }
            ),
            ToolParameter(
                name="item_id",
                type="string",
                description="ID of the item (for update, complete, or remove operations)",
                required=False
            ),
            ToolParameter(
                name="item_name",
                type="string",
                description="New name for the item (used with 'update_item' operation)",
                required=False
            ),
            ToolParameter(
                name="item_description",
                type="string",
                description="New description for the item (used with 'update_item' operation)",
                required=False
            ),
            ToolParameter(
                name="item_quantity",
                type="string",
                description="New quantity for the item (used with 'update_item' operation)",
                required=False
            ),
            ToolParameter(
                name="limit",
                type="number",
                description="Maximum number of items to return (used with 'get_recent_items', default 5)",
                required=False
            ),
            ToolParameter(
                name="include_completed",
                type="boolean",
                description="Whether to include completed items (used with 'get_list' and 'get_recent_items', default false)",
                required=False
            ),
        ]

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        """Execute list operation."""
        operation = kwargs.get("operation")
        user_id = context.user_id

        if not user_id:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="User ID is required",
                error="MISSING_USER_ID"
            )

        try:
            if operation == "create_list":
                return await self._create_list(user_id, **kwargs)
            elif operation == "rename_list":
                return await self._rename_list(user_id, **kwargs)
            elif operation == "delete_list":
                return await self._delete_list(user_id, **kwargs)
            elif operation == "add_items":
                return await self._add_items(user_id, **kwargs)
            elif operation == "update_item":
                return await self._update_item(user_id, **kwargs)
            elif operation == "complete_item":
                return await self._complete_item(user_id, **kwargs)
            elif operation == "remove_item":
                return await self._remove_item(user_id, **kwargs)
            elif operation == "get_list":
                return await self._get_list(user_id, **kwargs)
            elif operation == "get_recent_items":
                return await self._get_recent_items(user_id, **kwargs)
            else:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    message=f"Invalid operation: {operation}",
                    error="INVALID_OPERATION"
                )
        except Exception as e:
            logger.error(f"Error in list tool operation '{operation}': {e}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=str(e),
                error="OPERATION_FAILED"
            )

    async def _create_list(self, user_id: str, **kwargs) -> ToolResult:
        """Create a new list."""
        list_name = kwargs.get("list_name")

        if not list_name:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="list_name is required for 'create_list' operation",
                error="MISSING_PARAMETER"
            )

        try:
            new_list = self.list_manager.create_list(user_id, list_name)
            logger.info(f"Created list '{list_name}' for user {user_id}")

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"Created list '{list_name}'",
                data={
                    "list_id": new_list.list_id,
                    "list_name": new_list.name,
                    "created_at": new_list.created_at.isoformat()
                }
            )
        except ValueError as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=str(e),
                error="LIST_EXISTS"
            )

    async def _rename_list(self, user_id: str, **kwargs) -> ToolResult:
        """Rename an existing list."""
        list_name = kwargs.get("list_name")
        new_name = kwargs.get("new_name")

        if not list_name or not new_name:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="list_name and new_name are required for 'rename_list' operation",
                error="MISSING_PARAMETER"
            )

        try:
            updated_list = self.list_manager.rename_list(user_id, list_name, new_name)
            logger.info(f"Renamed list '{list_name}' to '{new_name}' for user {user_id}")

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"Renamed list from '{list_name}' to '{new_name}'",
                data={
                    "list_id": updated_list.list_id,
                    "old_name": list_name,
                    "new_name": updated_list.name
                }
            )
        except ValueError as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=str(e),
                error="RENAME_FAILED"
            )

    async def _delete_list(self, user_id: str, **kwargs) -> ToolResult:
        """Delete a list."""
        list_name = kwargs.get("list_name")

        if not list_name:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="list_name is required for 'delete_list' operation",
                error="MISSING_PARAMETER"
            )

        try:
            self.list_manager.delete_list(user_id, list_name)
            logger.info(f"Deleted list '{list_name}' for user {user_id}")

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"Deleted list '{list_name}'"
            )
        except ValueError as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=str(e),
                error="LIST_NOT_FOUND"
            )

    async def _add_items(self, user_id: str, **kwargs) -> ToolResult:
        """Add items to a list."""
        list_name = kwargs.get("list_name")
        items = kwargs.get("items")

        if not list_name:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="list_name is required for 'add_items' operation",
                error="MISSING_PARAMETER"
            )

        if not items or not isinstance(items, list) or len(items) == 0:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="items array is required and must contain at least one item",
                error="MISSING_PARAMETER"
            )

        try:
            updated_list = self.list_manager.add_items(user_id, list_name, items)
            logger.info(f"Added {len(items)} items to list '{list_name}' for user {user_id}")

            item_names = [item.get('name', 'unknown') for item in items]
            items_str = ", ".join(item_names) if len(item_names) <= 3 else f"{len(item_names)} items"

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"Added {items_str} to '{list_name}'",
                data={
                    "list_id": updated_list.list_id,
                    "list_name": updated_list.name,
                    "items_added": len(items),
                    "total_items": len(updated_list.items)
                }
            )
        except ValueError as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=str(e),
                error="ADD_ITEMS_FAILED"
            )

    async def _update_item(self, user_id: str, **kwargs) -> ToolResult:
        """Update an item's properties."""
        list_name = kwargs.get("list_name")
        item_id = kwargs.get("item_id")
        item_name = kwargs.get("item_name")
        item_description = kwargs.get("item_description")
        item_quantity = kwargs.get("item_quantity")

        if not list_name or not item_id:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="list_name and item_id are required for 'update_item' operation",
                error="MISSING_PARAMETER"
            )

        if item_name is None and item_description is None and item_quantity is None:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="At least one of item_name, item_description, or item_quantity must be provided",
                error="MISSING_PARAMETER"
            )

        try:
            updated_list = self.list_manager.update_item(
                user_id, list_name, item_id,
                name=item_name,
                description=item_description,
                quantity=item_quantity
            )
            logger.info(f"Updated item {item_id} in list '{list_name}' for user {user_id}")

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"Updated item in '{list_name}'",
                data={
                    "list_id": updated_list.list_id,
                    "list_name": updated_list.name,
                    "item_id": item_id
                }
            )
        except ValueError as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=str(e),
                error="UPDATE_ITEM_FAILED"
            )

    async def _complete_item(self, user_id: str, **kwargs) -> ToolResult:
        """Mark an item as completed."""
        list_name = kwargs.get("list_name")
        item_id = kwargs.get("item_id")

        if not list_name or not item_id:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="list_name and item_id are required for 'complete_item' operation",
                error="MISSING_PARAMETER"
            )

        try:
            updated_list = self.list_manager.complete_item(user_id, list_name, item_id)
            logger.info(f"Completed item {item_id} in list '{list_name}' for user {user_id}")

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"Marked item as completed in '{list_name}'",
                data={
                    "list_id": updated_list.list_id,
                    "list_name": updated_list.name,
                    "item_id": item_id
                }
            )
        except ValueError as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=str(e),
                error="COMPLETE_ITEM_FAILED"
            )

    async def _remove_item(self, user_id: str, **kwargs) -> ToolResult:
        """Remove an item from a list."""
        list_name = kwargs.get("list_name")
        item_id = kwargs.get("item_id")

        if not list_name or not item_id:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="list_name and item_id are required for 'remove_item' operation",
                error="MISSING_PARAMETER"
            )

        try:
            updated_list = self.list_manager.remove_item(user_id, list_name, item_id)
            logger.info(f"Removed item {item_id} from list '{list_name}' for user {user_id}")

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"Removed item from '{list_name}'",
                data={
                    "list_id": updated_list.list_id,
                    "list_name": updated_list.name,
                    "remaining_items": len(updated_list.items)
                }
            )
        except ValueError as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=str(e),
                error="REMOVE_ITEM_FAILED"
            )

    async def _get_list(self, user_id: str, **kwargs) -> ToolResult:
        """Get a list with all its items."""
        list_name = kwargs.get("list_name")
        include_completed = kwargs.get("include_completed", False)

        if not list_name:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="list_name is required for 'get_list' operation",
                error="MISSING_PARAMETER"
            )

        list_obj = self.list_manager.get_list(user_id, list_name)
        
        if not list_obj:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"List '{list_name}' not found",
                error="LIST_NOT_FOUND"
            )

        # Filter items
        items = list_obj.items
        if not include_completed:
            items = [item for item in items if not item.completed]

        # Convert to dict
        items_data = [
            {
                "item_id": item.item_id,
                "name": item.name,
                "description": item.description,
                "quantity": item.quantity,
                "completed": item.completed,
                "created_at": item.created_at.isoformat()
            }
            for item in items
        ]

        return ToolResult(
            status=ToolResultStatus.SUCCESS,
            message=f"Retrieved list '{list_name}' with {len(items_data)} items",
            data={
                "list_id": list_obj.list_id,
                "list_name": list_obj.name,
                "items": items_data,
                "total_items": len(items_data)
            }
        )

    async def _get_recent_items(self, user_id: str, **kwargs) -> ToolResult:
        """Get most recently added items from a list."""
        list_name = kwargs.get("list_name")
        limit = kwargs.get("limit", 5)
        include_completed = kwargs.get("include_completed", False)

        if not list_name:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="list_name is required for 'get_recent_items' operation",
                error="MISSING_PARAMETER"
            )

        try:
            items = self.list_manager.get_recent_items(
                user_id, list_name, 
                limit=int(limit), 
                include_completed=include_completed
            )

            # Convert to dict
            items_data = [
                {
                    "item_id": item.item_id,
                    "name": item.name,
                    "description": item.description,
                    "quantity": item.quantity,
                    "completed": item.completed,
                    "created_at": item.created_at.isoformat()
                }
                for item in items
            ]

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"Retrieved {len(items_data)} recent items from '{list_name}'",
                data={
                    "list_name": list_name,
                    "items": items_data,
                    "count": len(items_data)
                }
            )
        except ValueError as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=str(e),
                error="GET_RECENT_ITEMS_FAILED"
            )
