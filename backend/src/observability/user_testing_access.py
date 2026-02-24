"""
User Testing Access Layer for Observability API

Handles test user lifecycle: creation, deletion, state export.
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .data_access import DataAccessLayer
from .memory_access import MemoryAccessor


# List of names for auto-generating test user names
RANDOM_NAMES = [
    "Riley", "Jordan", "Morgan", "Casey", "Alex", "Taylor", "Quinn", "Avery",
    "Charlie", "Dakota", "Emerson", "Finley", "Harper", "Hayden", "Jamie",
    "Jesse", "Kennedy", "Logan", "Parker", "Peyton", "River", "Rowan",
    "Sage", "Skylar", "Spencer"
]


class UserTestingAccessor:
    """Manages test user lifecycle and operations."""

    def __init__(self, data_dir: str):
        """
        Initialize user testing accessor.

        Args:
            data_dir: Root directory for data storage
        """
        self.data_dir = Path(data_dir)
        self.dal = DataAccessLayer(data_dir)
        self.memory_dal = MemoryAccessor(data_dir)

        # Production users that cannot be deleted
        self.production_users = {"user_justin"}

    def generate_test_user_id(self) -> str:
        """
        Generate a unique test user ID.

        Returns:
            User ID in format: TestUser_<Name>_<Random4Digits>
        """
        name = random.choice(RANDOM_NAMES)
        random_digits = random.randint(1000, 9999)
        return f"TestUser_{name}_{random_digits}"

    def is_production_user(self, user_id: str) -> bool:
        """
        Check if a user is a production user.

        Args:
            user_id: User identifier

        Returns:
            True if production user (cannot be deleted)
        """
        return user_id in self.production_users

    def create_test_user(
        self,
        starting_chapter: int = 1,
        initial_memories: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new test user with optional initial state.

        Args:
            starting_chapter: Chapter to start at (default: 1)
            initial_memories: List of memory dicts to create
            tags: List of tags for categorizing test users
            user_id: Optional specific user ID (otherwise auto-generated)

        Returns:
            Created user data including user_id
        """
        # Generate user ID if not provided
        if not user_id:
            user_id = self.generate_test_user_id()

        # Create base user state
        now = datetime.now().isoformat()
        user_data = {
            "user_id": user_id,
            "preferences": {
                "dietary_restrictions": [],
                "cooking_skill_level": None,
                "favorite_foods": [],
                "disliked_foods": [],
                "custom_preferences": {}
            },
            "conversation_history": {
                "messages": [],
                "summary": None,
                "last_interaction": None
            },
            "device_preferences": {
                "devices": {},
                "custom_scenes": {}
            },
            "story_progress": {
                "current_chapter": starting_chapter,
                "beats_delivered": {},
                "interaction_count": 0,
                "first_interaction": None,
                "chapter_start_time": now,
                "custom_story_data": {}
            },
            "created_at": now,
            "updated_at": now,
            "metadata": {
                "is_test_user": True,
                "tags": tags or []
            }
        }

        # Save user data
        self.dal.save_user(user_id, user_data)

        # Create initial memories if provided
        if initial_memories:
            for mem in initial_memories:
                self.memory_dal.create_memory(
                    user_id=user_id,
                    category=mem.get("category", "preference"),
                    content=mem["content"],
                    source=mem.get("source", f"test_user_creation_{datetime.now().isoformat()}"),
                    importance=mem.get("importance", 5),
                    verified=mem.get("verified", True),
                    metadata=mem.get("metadata", {})
                )

        return user_data

    def delete_test_user(self, user_id: str) -> Dict[str, Any]:
        """
        Delete a test user and all associated data.

        Args:
            user_id: User identifier

        Returns:
            Summary of deleted data

        Raises:
            ValueError: If trying to delete a production user
        """
        if self.is_production_user(user_id):
            raise ValueError(f"Cannot delete production user: {user_id}")

        # Get user data for summary before deletion
        user_data = self.dal.get_user(user_id)
        if not user_data:
            raise ValueError(f"User {user_id} not found")

        # Count what will be deleted
        memories = self.memory_dal.get_all_memories(user_id)
        memory_count = len(memories)

        story_progress = user_data.get("story_progress", {})
        beats_completed = len(story_progress.get("beats_delivered", {}))
        interaction_count = story_progress.get("interaction_count", 0)

        # Delete user file
        self.dal.delete_user(user_id)

        # Delete memory file
        memory_file = self.data_dir / "users" / f"{user_id}_memories.json"
        if memory_file.exists():
            memory_file.unlink()

        # Delete any tool call logs (if they exist)
        # This would be implemented when tool call logging is added

        return {
            "user_id": user_id,
            "deleted": True,
            "summary": {
                "memories_deleted": memory_count,
                "beats_completed": beats_completed,
                "interaction_count": interaction_count
            }
        }

    def get_user_state_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive summary of user state.

        Args:
            user_id: User identifier

        Returns:
            Detailed user state summary
        """
        user_data = self.dal.get_user(user_id)
        if not user_data:
            raise ValueError(f"User {user_id} not found")

        memories = self.memory_dal.get_all_memories(user_id)
        story_progress = user_data.get("story_progress", {})

        is_test = user_data.get("metadata", {}).get("is_test_user", False)
        is_production = self.is_production_user(user_id)

        metadata = user_data.get("metadata", {})
        tags = metadata.get("tags", []) if isinstance(metadata, dict) else []

        return {
            "user_id": user_id,
            "type": "production" if is_production else ("test" if is_test else "unknown"),
            "created_at": user_data.get("created_at"),
            "updated_at": user_data.get("updated_at"),
            "tags": tags,
            "profile": {
                "interaction_count": story_progress.get("interaction_count", 0),
                "first_interaction": story_progress.get("first_interaction"),
                "last_interaction": user_data.get("conversation_history", {}).get("last_interaction")
            },
            "story_progress": {
                "current_chapter": story_progress.get("current_chapter", 1),
                "beats_delivered": len(story_progress.get("beats_delivered", {})),
                "chapter_start_time": story_progress.get("chapter_start_time")
            },
            "memory_count": len(memories),
            "device_count": len(user_data.get("device_preferences", {}).get("devices", {}))
        }

    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export complete user data for backup or analysis.

        Args:
            user_id: User identifier

        Returns:
            Complete user data including memories
        """
        user_data = self.dal.get_user(user_id)
        if not user_data:
            raise ValueError(f"User {user_id} not found")

        memories = self.memory_dal.get_all_memories(user_id)

        return {
            "user_data": user_data,
            "memories": [
                {
                    "memory_id": m.memory_id,
                    "category": m.category,
                    "content": m.content,
                    "source": m.source,
                    "importance": m.importance,
                    "verified": m.verified,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "last_accessed": m.last_accessed.isoformat() if m.last_accessed else None,
                    "access_count": m.access_count,
                    "metadata": m.metadata
                }
                for m in memories
            ],
            "export_timestamp": datetime.now().isoformat()
        }

    def list_all_users_with_type(self) -> List[Dict[str, Any]]:
        """
        List all users with their type (production, test).

        Returns:
            List of user summaries with type information
        """
        user_ids = self.dal.list_users()
        users = []

        for user_id in user_ids:
            user_data = self.dal.get_user(user_id)
            if not user_data:
                continue

            is_test = user_data.get("metadata", {}).get("is_test_user", False)
            is_production = self.is_production_user(user_id)

            story_progress = user_data.get("story_progress", {})

            users.append({
                "user_id": user_id,
                "type": "production" if is_production else ("test" if is_test else "unknown"),
                "current_chapter": story_progress.get("current_chapter", 1),
                "interaction_count": story_progress.get("interaction_count", 0),
                "created_at": user_data.get("created_at"),
                "tags": user_data.get("metadata", {}).get("tags", []),
                "metadata": user_data.get("metadata", {}),
            })

        # Sort: production users first, then by creation date
        users.sort(key=lambda u: (
            0 if u["type"] == "production" else 1,
            u["created_at"] or ""
        ))

        return users
