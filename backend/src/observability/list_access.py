"""
List Access Layer for Observability API.

Provides read access to user lists for the observability dashboard.
"""

from pathlib import Path
from typing import List as TypeList, Dict, Optional, Any
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.list_manager import ListManager
from models.list_models import UserLists, List, ListItem


class ListAccessor:
    """Provides access to user list data for observability."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the List Accessor.

        Args:
            data_dir: Root directory for data storage
        """
        self.list_manager = ListManager(data_dir=data_dir)

    def get_all_lists(self, user_id: str) -> Optional[UserLists]:
        """
        Get all lists for a user.

        Args:
            user_id: User identifier

        Returns:
            UserLists object or None if user has no lists
        """
        user_lists = self.list_manager.load_lists(user_id)
        return user_lists if user_lists.lists else None

    def get_list(self, user_id: str, list_name: str) -> Optional[List]:
        """
        Get a specific list by name.

        Args:
            user_id: User identifier
            list_name: Name of the list

        Returns:
            List object or None if not found
        """
        return self.list_manager.get_list(user_id, list_name)

    def get_list_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a summary of all lists for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with list summaries
        """
        user_lists = self.list_manager.load_lists(user_id)
        
        summaries = []
        for list_obj in user_lists.lists.values():
            active_count = sum(1 for item in list_obj.items if not item.completed)
            completed_count = sum(1 for item in list_obj.items if item.completed)
            
            summaries.append({
                "list_id": list_obj.list_id,
                "list_name": list_obj.name,
                "total_items": len(list_obj.items),
                "active_items": active_count,
                "completed_items": completed_count,
                "created_at": list_obj.created_at.isoformat(),
                "updated_at": list_obj.updated_at.isoformat()
            })

        return {
            "user_id": user_id,
            "total_lists": len(user_lists.lists),
            "lists": summaries
        }
