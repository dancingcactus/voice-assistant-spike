"""
Memory Access Layer for Observability API.

Provides read/write access to user memories for the observability dashboard.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from filelock import FileLock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.user_state import Memory, UserState


class MemoryAccessor:
    """Provides access to user memory data."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the Memory Accessor.

        Args:
            data_dir: Root directory for data storage
        """
        self.data_dir = Path(data_dir)
        self.users_dir = self.data_dir / "users"

    def _get_user_file_path(self, user_id: str) -> Path:
        """Get the file path for a user's state."""
        return self.users_dir / f"{user_id}.json"

    def _load_user_state(self, user_id: str) -> Optional[UserState]:
        """Load user state from disk."""
        file_path = self._get_user_file_path(user_id)
        lock_path = file_path.with_suffix('.json.lock')

        if not file_path.exists():
            return None

        with FileLock(lock_path, timeout=5):
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Convert datetime strings to datetime objects
                data = self._deserialize_datetimes(data)
                return UserState(**data)

    def _save_user_state(self, user_id: str, user_state: UserState):
        """Save user state to disk."""
        file_path = self._get_user_file_path(user_id)
        lock_path = file_path.with_suffix('.json.lock')

        # Update timestamp
        user_state.updated_at = datetime.now()

        with FileLock(lock_path, timeout=5):
            data = user_state.model_dump()
            data = self._serialize_datetimes(data)

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

    def _serialize_datetimes(self, obj: Any) -> Any:
        """Recursively convert datetime objects to ISO format strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._serialize_datetimes(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetimes(item) for item in obj]
        else:
            return obj

    def _deserialize_datetimes(self, obj: Any) -> Any:
        """Recursively convert ISO format strings to datetime objects."""
        if isinstance(obj, str):
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

    def get_all_memories(self, user_id: str) -> List[Memory]:
        """
        Get all memories for a user.

        Args:
            user_id: User identifier

        Returns:
            List of Memory objects
        """
        user_state = self._load_user_state(user_id)
        if not user_state:
            return []

        return list(user_state.memories.memories.values())

    def get_memory(self, user_id: str, memory_id: str) -> Optional[Memory]:
        """
        Get a specific memory by ID.

        Args:
            user_id: User identifier
            memory_id: Memory identifier

        Returns:
            Memory object or None if not found
        """
        user_state = self._load_user_state(user_id)
        if not user_state:
            return None

        return user_state.memories.memories.get(memory_id)

    def create_memory(
        self,
        user_id: str,
        category: str,
        content: str,
        source: str,
        importance: int = 5,
        verified: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """
        Create a new memory for a user.

        Args:
            user_id: User identifier
            category: Memory category
            content: Memory content
            source: Source of the memory
            importance: Importance rating (1-10)
            verified: Whether memory is verified
            metadata: Additional metadata

        Returns:
            Created Memory object
        """
        user_state = self._load_user_state(user_id)
        if not user_state:
            raise ValueError(f"User {user_id} not found")

        # Create new memory
        memory = Memory(
            category=category,
            content=content,
            source=source,
            importance=importance,
            verified=verified,
            metadata=metadata or {}
        )

        # Add to user state
        user_state.memories.memories[memory.memory_id] = memory

        # Save
        self._save_user_state(user_id, user_state)

        return memory

    def update_memory(
        self,
        user_id: str,
        memory_id: str,
        category: Optional[str] = None,
        content: Optional[str] = None,
        importance: Optional[int] = None,
        verified: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Memory]:
        """
        Update an existing memory.

        Args:
            user_id: User identifier
            memory_id: Memory identifier
            category: New category (if updating)
            content: New content (if updating)
            importance: New importance (if updating)
            verified: New verified status (if updating)
            metadata: New metadata (if updating)

        Returns:
            Updated Memory object or None if not found
        """
        user_state = self._load_user_state(user_id)
        if not user_state:
            return None

        memory = user_state.memories.memories.get(memory_id)
        if not memory:
            return None

        # Update fields
        if category is not None:
            memory.category = category
        if content is not None:
            memory.content = content
        if importance is not None:
            memory.importance = importance
        if verified is not None:
            memory.verified = verified
        if metadata is not None:
            memory.metadata = metadata

        # Save
        self._save_user_state(user_id, user_state)

        return memory

    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """
        Delete a memory.

        Args:
            user_id: User identifier
            memory_id: Memory identifier

        Returns:
            True if deleted, False if not found
        """
        user_state = self._load_user_state(user_id)
        if not user_state:
            return False

        if memory_id not in user_state.memories.memories:
            return False

        del user_state.memories.memories[memory_id]
        self._save_user_state(user_id, user_state)

        return True

    def get_context_preview(self, user_id: str, min_importance: int = 3) -> Dict[str, Any]:
        """
        Get a preview of what memories would be loaded into context.

        Args:
            user_id: User identifier
            min_importance: Minimum importance to include

        Returns:
            Dictionary with preview information
        """
        memories = self.get_all_memories(user_id)

        # Filter by importance
        context_memories = [m for m in memories if m.importance >= min_importance]

        # Sort by importance (descending)
        context_memories.sort(key=lambda m: m.importance, reverse=True)

        # Estimate token count (rough approximation: 4 chars = 1 token)
        total_tokens = sum(len(m.content) // 4 for m in context_memories)

        # Group by category
        by_category: Dict[str, List[Memory]] = {}
        for memory in context_memories:
            if memory.category not in by_category:
                by_category[memory.category] = []
            by_category[memory.category].append(memory)

        return {
            "total_memories": len(memories),
            "context_memories": len(context_memories),
            "estimated_tokens": total_tokens,
            "by_category": {
                cat: len(mems) for cat, mems in by_category.items()
            },
            "memories": [
                {
                    "memory_id": m.memory_id,
                    "category": m.category,
                    "content": m.content,
                    "importance": m.importance,
                    "tokens": len(m.content) // 4
                }
                for m in context_memories
            ]
        }
