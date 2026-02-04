"""
Memory Manager - Handles persistent user state and conversation history.

Responsibilities:
- Load and save user state to disk (JSON files)
- Maintain in-memory cache for fast access
- Periodic flush to disk
- Conversation history management (30-minute full window)
- User preferences and story state persistence
"""

import json
import os
import asyncio
import fcntl
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
from contextlib import contextmanager
from models.user_state import UserState, ConversationMessage, DeviceState
from models.message import Message


class MemoryManager:
    """Manages persistent user state across sessions."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the Memory Manager.

        Args:
            data_dir: Root directory for data storage
        """
        self.data_dir = Path(data_dir)
        self.users_dir = self.data_dir / "users"
        self.devices_dir = self.data_dir / "devices"
        self.story_dir = self.data_dir / "story"

        # In-memory cache of user states
        self._user_cache: Dict[str, UserState] = {}

        # Dirty flag for periodic flush
        self._dirty_users: set = set()

        # Auto-flush interval (seconds)
        self._flush_interval = 60  # Flush every minute

        # Initialize directories
        self._init_directories()

        # Start background flush task
        self._flush_task = None

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

        # Use 'a+' mode if file doesn't exist and we need to write
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
        for directory in [self.users_dir, self.devices_dir, self.story_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def _get_user_file_path(self, user_id: str) -> Path:
        """Get the file path for a user's state."""
        return self.users_dir / f"{user_id}.json"

    def load_user_state(self, user_id: str) -> UserState:
        """
        Load user state from cache or disk with file locking for atomicity.

        Args:
            user_id: Unique user identifier

        Returns:
            UserState object
        """
        # Check cache first
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        # Try to load from disk with lock
        file_path = self._get_user_file_path(user_id)

        if file_path.exists():
            try:
                with self._file_lock(file_path, 'r') as f:
                    data = json.load(f)
                    # Convert datetime strings back to datetime objects
                    data = self._deserialize_datetimes(data)
                    user_state = UserState(**data)
                    self._user_cache[user_id] = user_state
                    return user_state
            except Exception as e:
                print(f"Error loading user state for {user_id}: {e}")
                print("Creating new user state")

        # Create new user state if file doesn't exist or load failed
        user_state = UserState(user_id=user_id)
        self._user_cache[user_id] = user_state
        self._dirty_users.add(user_id)
        return user_state

    def save_user_state(self, user_id: str, force: bool = False):
        """
        Save user state to disk.

        Args:
            user_id: Unique user identifier
            force: If True, save immediately. Otherwise mark as dirty for periodic flush.
        """
        if user_id not in self._user_cache:
            print(f"Warning: User {user_id} not in cache, nothing to save")
            return

        user_state = self._user_cache[user_id]
        user_state.update_timestamp()

        if force:
            self._write_user_state(user_id, user_state)
        else:
            self._dirty_users.add(user_id)

    def _write_user_state(self, user_id: str, user_state: UserState):
        """Write user state to disk with file locking for atomicity."""
        file_path = self._get_user_file_path(user_id)

        try:
            # Convert to dict and serialize datetimes
            data = user_state.model_dump()
            data = self._serialize_datetimes(data)

            # Use atomic write: write to temp file, then rename
            # This ensures we never have a partially written file
            temp_path = file_path.with_suffix('.tmp')

            with self._file_lock(temp_path, 'w') as f:
                json.dump(data, f, indent=2)

            # Atomic rename (replaces old file if exists)
            temp_path.replace(file_path)

            print(f"Saved user state for {user_id} (atomic)")
        except Exception as e:
            print(f"Error saving user state for {user_id}: {e}")

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

    async def start_periodic_flush(self):
        """Start background task for periodic flushing."""
        self._flush_task = asyncio.create_task(self._periodic_flush_loop())

    async def _periodic_flush_loop(self):
        """Periodically flush dirty user states to disk."""
        while True:
            await asyncio.sleep(self._flush_interval)
            await self.flush_dirty_users()

    async def flush_dirty_users(self):
        """Flush all dirty user states to disk."""
        if not self._dirty_users:
            return

        dirty_copy = self._dirty_users.copy()
        self._dirty_users.clear()

        for user_id in dirty_copy:
            if user_id in self._user_cache:
                self._write_user_state(user_id, self._user_cache[user_id])

    def stop_periodic_flush(self):
        """Stop the background flush task."""
        if self._flush_task:
            self._flush_task.cancel()

    # Convenience methods for specific state updates

    def add_conversation_message(self, user_id: str, message: Message, role: str):
        """
        Add a message to conversation history.

        Args:
            user_id: Unique user identifier
            message: Message object
            role: "user" or "assistant"
        """
        user_state = self.load_user_state(user_id)

        conv_message = ConversationMessage(
            timestamp=datetime.now(),
            role=role,
            content=message.content,
            tool_calls=message.tool_calls if hasattr(message, 'tool_calls') else None,
            metadata={}
        )

        user_state.conversation_history.messages.append(conv_message)
        user_state.conversation_history.last_interaction = datetime.now()

        # Prune old messages (keep last 30 minutes full detail)
        self._prune_conversation_history(user_state)

        self.save_user_state(user_id)

    def _prune_conversation_history(self, user_state: UserState):
        """
        Prune conversation history to keep only last 30 minutes in full detail.
        Older messages are summarized or dropped.
        """
        cutoff_time = datetime.now() - timedelta(minutes=30)

        recent_messages = []
        old_messages = []

        for msg in user_state.conversation_history.messages:
            if msg.timestamp >= cutoff_time:
                recent_messages.append(msg)
            else:
                old_messages.append(msg)

        # For now, we'll just drop old messages
        # In the future, we could summarize them
        user_state.conversation_history.messages = recent_messages

        # If we dropped messages, we could create a summary
        if old_messages and not user_state.conversation_history.summary:
            # Placeholder: In real implementation, use LLM to summarize
            user_state.conversation_history.summary = f"Earlier conversation with {len(old_messages)} messages"

    def get_conversation_history(self, user_id: str, max_messages: Optional[int] = None) -> List[ConversationMessage]:
        """
        Get conversation history for a user.

        Args:
            user_id: Unique user identifier
            max_messages: Maximum number of messages to return (most recent)

        Returns:
            List of ConversationMessage objects
        """
        user_state = self.load_user_state(user_id)
        messages = user_state.conversation_history.messages

        if max_messages:
            return messages[-max_messages:]

        return messages

    def update_device_state(self, user_id: str, device_id: str, device_type: str, state: Dict):
        """
        Update device state for a user.

        Args:
            user_id: Unique user identifier
            device_id: Device identifier
            device_type: Type of device
            state: Device state dictionary
        """
        user_state = self.load_user_state(user_id)

        device_state = DeviceState(
            device_id=device_id,
            device_type=device_type,
            state=state,
            last_updated=datetime.now()
        )

        user_state.device_preferences.devices[device_id] = device_state
        self.save_user_state(user_id)

    def get_device_state(self, user_id: str, device_id: str) -> Optional[DeviceState]:
        """
        Get device state for a user.

        Args:
            user_id: Unique user identifier
            device_id: Device identifier

        Returns:
            DeviceState object or None if not found
        """
        user_state = self.load_user_state(user_id)
        return user_state.device_preferences.devices.get(device_id)

    def update_story_progress(self, user_id: str, **kwargs):
        """
        Update story progress for a user.

        Args:
            user_id: Unique user identifier
            **kwargs: Story progress fields to update (current_chapter, beats_delivered, etc.)
        """
        user_state = self.load_user_state(user_id)

        for key, value in kwargs.items():
            if hasattr(user_state.story_progress, key):
                setattr(user_state.story_progress, key, value)

        self.save_user_state(user_id)

    def increment_interaction_count(self, user_id: str):
        """Increment the interaction count for a user."""
        user_state = self.load_user_state(user_id)
        user_state.story_progress.interaction_count += 1

        if not user_state.story_progress.first_interaction:
            user_state.story_progress.first_interaction = datetime.now()

        self.save_user_state(user_id)

    def add_user_preference(self, user_id: str, preference_type: str, value: str):
        """
        Add a user preference (e.g., dietary restriction, favorite food).

        Args:
            user_id: Unique user identifier
            preference_type: Type of preference ("dietary_restrictions", "favorite_foods", etc.)
            value: The preference value to add
        """
        user_state = self.load_user_state(user_id)

        if hasattr(user_state.preferences, preference_type):
            pref_list = getattr(user_state.preferences, preference_type)
            if isinstance(pref_list, list) and value not in pref_list:
                pref_list.append(value)

        self.save_user_state(user_id)

    def reset_user_state(self, user_id: str):
        """
        Reset user state to a fresh state.

        Args:
            user_id: Unique user identifier
        """
        user_state = UserState(user_id=user_id)
        self._user_cache[user_id] = user_state
        self.save_user_state(user_id, force=True)
        print(f"Reset user state for {user_id}")
