"""
List Manager - Handles persistent user lists.

Responsibilities:
- Load and save user lists to disk (JSON files)
- CRUD operations on lists and items
- Thread-safe file operations with locking
"""

import json
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List as TypeList, Any
from contextlib import contextmanager
from models.list_models import UserLists, List, ListItem


class ListManager:
    """Manages persistent user lists (shopping, todo, etc.)."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the List Manager.

        Args:
            data_dir: Root directory for data storage
        """
        self.data_dir = Path(data_dir)
        self.users_dir = self.data_dir / "users"

        # Initialize directories
        self._init_directories()

    @contextmanager
    def _file_lock(self, file_path: Path, mode: str = 'r'):
        """
        Context manager for file locking to prevent race conditions.

        Args:
            file_path: Path to file to lock
            mode: File open mode ('r' for read, 'w' for write)

        Yields:
            File handle with exclusive lock
        """
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Open file with appropriate mode
        lock_mode = fcntl.LOCK_SH if 'r' in mode else fcntl.LOCK_EX

        # Use 'w+' mode if file doesn't exist and we need to write
        if not file_path.exists() and 'w' in mode:
            file_mode = 'w+'
        else:
            file_mode = mode

        file_handle = None
        try:
            file_handle = open(file_path, file_mode)
            # Acquire lock (will block if another process has lock)
            fcntl.flock(file_handle.fileno(), lock_mode)
            yield file_handle
        finally:
            if file_handle:
                # Release lock and close file
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
                file_handle.close()

    def _init_directories(self):
        """Create data directories if they don't exist."""
        self.users_dir.mkdir(parents=True, exist_ok=True)

    def _get_lists_file_path(self, user_id: str) -> Path:
        """Get the file path for a user's lists."""
        return self.users_dir / f"{user_id}_lists.json"

    def load_lists(self, user_id: str) -> UserLists:
        """
        Load user lists from disk with file locking.

        Args:
            user_id: Unique user identifier

        Returns:
            UserLists object
        """
        file_path = self._get_lists_file_path(user_id)

        if file_path.exists():
            try:
                with self._file_lock(file_path, 'r') as f:
                    raw_data = json.load(f)
                    # Convert datetime strings back to datetime objects
                    data_obj = self._deserialize_datetimes(raw_data)
                    # Type assertion: we know this is a dict after deserialization
                    data: Dict[str, Any] = data_obj if isinstance(data_obj, dict) else {}
                    # Ensure user_id is present in data
                    if 'user_id' not in data:
                        data['user_id'] = user_id
                    return UserLists(**data)
            except Exception as e:
                print(f"Error loading lists for {user_id}: {e}")
                print("Creating new user lists")

        # Create new user lists if file doesn't exist or load failed
        return UserLists(user_id=user_id)

    def save_lists(self, user_lists: UserLists):
        """
        Save user lists to disk with atomic write.

        Args:
            user_lists: UserLists object to save
        """
        file_path = self._get_lists_file_path(user_lists.user_id)

        try:
            # Convert to dict and serialize datetimes
            data = user_lists.model_dump()
            data = self._serialize_datetimes(data)

            # Use atomic write: write to temp file, then rename
            temp_path = file_path.with_suffix('.tmp')

            with self._file_lock(temp_path, 'w') as f:
                json.dump(data, f, indent=2)

            # Atomic rename (replaces old file if exists)
            temp_path.replace(file_path)

            print(f"Saved lists for {user_lists.user_id}")
        except Exception as e:
            print(f"Error saving lists for {user_lists.user_id}: {e}")
            raise

    def _serialize_datetimes(self, obj):
        """Recursively convert datetime objects to ISO format strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._serialize_datetimes(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetimes(item) for item in obj]
        else:
            return obj

    def _deserialize_datetimes(self, obj):
        """Recursively convert ISO format strings to datetime objects."""
        if isinstance(obj, str):
            # Try to parse as datetime
            try:
                return datetime.fromisoformat(obj)
            except (ValueError, AttributeError):
                return obj
        elif isinstance(obj, dict):
            return {key: self._deserialize_datetimes(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._deserialize_datetimes(item) for item in obj]
        else:
            return obj

    # List CRUD operations

    def get_list(self, user_id: str, list_name: str) -> Optional[List]:
        """
        Get a specific list by name.

        Args:
            user_id: User identifier
            list_name: Name of the list

        Returns:
            List object or None if not found
        """
        user_lists = self.load_lists(user_id)
        
        # Find list by name
        for list_obj in user_lists.lists.values():
            if list_obj.name.lower() == list_name.lower():
                return list_obj
        
        return None

    def create_list(self, user_id: str, name: str) -> List:
        """
        Create a new list.

        Args:
            user_id: User identifier
            name: Name for the new list

        Returns:
            Created List object

        Raises:
            ValueError: If list with that name already exists
        """
        user_lists = self.load_lists(user_id)

        # Check if list with this name already exists
        for list_obj in user_lists.lists.values():
            if list_obj.name.lower() == name.lower():
                raise ValueError(f"List '{name}' already exists")

        # Create new list
        new_list = List(name=name)
        user_lists.lists[new_list.list_id] = new_list

        # Save
        self.save_lists(user_lists)

        return new_list

    def rename_list(self, user_id: str, old_name: str, new_name: str) -> List:
        """
        Rename an existing list.

        Args:
            user_id: User identifier
            old_name: Current list name
            new_name: New name for the list

        Returns:
            Updated List object

        Raises:
            ValueError: If list doesn't exist or new name conflicts
        """
        user_lists = self.load_lists(user_id)

        # Find list by old name
        target_list = None
        for list_obj in user_lists.lists.values():
            if list_obj.name.lower() == old_name.lower():
                target_list = list_obj
                break

        if not target_list:
            raise ValueError(f"List '{old_name}' not found")

        # Check if new name conflicts
        for list_obj in user_lists.lists.values():
            if list_obj.list_id != target_list.list_id and list_obj.name.lower() == new_name.lower():
                raise ValueError(f"List '{new_name}' already exists")

        # Rename
        target_list.name = new_name
        target_list.updated_at = datetime.now()

        # Save
        self.save_lists(user_lists)

        return target_list

    def delete_list(self, user_id: str, name: str):
        """
        Delete a list.

        Args:
            user_id: User identifier
            name: Name of the list to delete

        Raises:
            ValueError: If list doesn't exist
        """
        user_lists = self.load_lists(user_id)

        # Find and remove list
        list_id_to_remove = None
        for list_id, list_obj in user_lists.lists.items():
            if list_obj.name.lower() == name.lower():
                list_id_to_remove = list_id
                break

        if not list_id_to_remove:
            raise ValueError(f"List '{name}' not found")

        del user_lists.lists[list_id_to_remove]

        # Save
        self.save_lists(user_lists)

    # Item operations

    def add_items(self, user_id: str, list_name: str, items: TypeList[Dict[str, Optional[str]]]) -> List:
        """
        Add multiple items to a list.

        Args:
            user_id: User identifier
            list_name: Name of the list
            items: List of item dictionaries with 'name', 'description', 'quantity'

        Returns:
            Updated List object

        Raises:
            ValueError: If list doesn't exist
        """
        user_lists = self.load_lists(user_id)

        # Find list
        target_list = None
        for list_obj in user_lists.lists.values():
            if list_obj.name.lower() == list_name.lower():
                target_list = list_obj
                break

        if not target_list:
            raise ValueError(f"List '{list_name}' not found")

        # Add items
        for item_data in items:
            new_item = ListItem(
                name=item_data.get('name') or '',
                description=item_data.get('description'),
                quantity=item_data.get('quantity')
            )
            target_list.items.append(new_item)

        target_list.updated_at = datetime.now()

        # Save
        self.save_lists(user_lists)

        return target_list

    def update_item(self, user_id: str, list_name: str, item_id: str, 
                   name: Optional[str] = None, description: Optional[str] = None, 
                   quantity: Optional[str] = None) -> List:
        """
        Update an item's properties.

        Args:
            user_id: User identifier
            list_name: Name of the list
            item_id: ID of the item to update
            name: New item name (optional)
            description: New description (optional)
            quantity: New quantity (optional)

        Returns:
            Updated List object

        Raises:
            ValueError: If list or item doesn't exist
        """
        user_lists = self.load_lists(user_id)

        # Find list and item
        target_list = None
        target_item = None
        
        for list_obj in user_lists.lists.values():
            if list_obj.name.lower() == list_name.lower():
                target_list = list_obj
                for item in list_obj.items:
                    if item.item_id == item_id:
                        target_item = item
                        break
                break

        if not target_list:
            raise ValueError(f"List '{list_name}' not found")
        if not target_item:
            raise ValueError(f"Item '{item_id}' not found")

        # Update item
        if name is not None:
            target_item.name = name
        if description is not None:
            target_item.description = description
        if quantity is not None:
            target_item.quantity = quantity

        target_list.updated_at = datetime.now()

        # Save
        self.save_lists(user_lists)

        return target_list

    def complete_item(self, user_id: str, list_name: str, item_id: str) -> List:
        """
        Mark an item as completed.

        Args:
            user_id: User identifier
            list_name: Name of the list
            item_id: ID of the item to complete

        Returns:
            Updated List object

        Raises:
            ValueError: If list or item doesn't exist
        """
        user_lists = self.load_lists(user_id)

        # Find list and item
        target_list = None
        target_item = None
        
        for list_obj in user_lists.lists.values():
            if list_obj.name.lower() == list_name.lower():
                target_list = list_obj
                for item in list_obj.items:
                    if item.item_id == item_id:
                        target_item = item
                        break
                break

        if not target_list:
            raise ValueError(f"List '{list_name}' not found")
        if not target_item:
            raise ValueError(f"Item '{item_id}' not found")

        # Mark as completed
        target_item.completed = True
        target_item.completed_at = datetime.now()

        target_list.updated_at = datetime.now()

        # Save
        self.save_lists(user_lists)

        return target_list

    def remove_item(self, user_id: str, list_name: str, item_id: str) -> List:
        """
        Remove an item from a list.

        Args:
            user_id: User identifier
            list_name: Name of the list
            item_id: ID of the item to remove

        Returns:
            Updated List object

        Raises:
            ValueError: If list or item doesn't exist
        """
        user_lists = self.load_lists(user_id)

        # Find list and item
        target_list = None
        item_index = None
        
        for list_obj in user_lists.lists.values():
            if list_obj.name.lower() == list_name.lower():
                target_list = list_obj
                for i, item in enumerate(list_obj.items):
                    if item.item_id == item_id:
                        item_index = i
                        break
                break

        if not target_list:
            raise ValueError(f"List '{list_name}' not found")
        if item_index is None:
            raise ValueError(f"Item '{item_id}' not found")

        # Remove item
        target_list.items.pop(item_index)
        target_list.updated_at = datetime.now()

        # Save
        self.save_lists(user_lists)

        return target_list

    def get_recent_items(self, user_id: str, list_name: str, limit: int = 5, 
                        include_completed: bool = False) -> TypeList[ListItem]:
        """
        Get most recently added items from a list.

        Args:
            user_id: User identifier
            list_name: Name of the list
            limit: Maximum number of items to return
            include_completed: Whether to include completed items

        Returns:
            List of ListItem objects (most recent first)

        Raises:
            ValueError: If list doesn't exist
        """
        list_obj = self.get_list(user_id, list_name)
        
        if not list_obj:
            raise ValueError(f"List '{list_name}' not found")

        # Filter and sort items
        items = list_obj.items
        if not include_completed:
            items = [item for item in items if not item.completed]

        # Sort by created_at descending
        items = sorted(items, key=lambda x: x.created_at, reverse=True)

        # Limit
        return items[:limit]
