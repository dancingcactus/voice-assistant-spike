"""
Data Access Layer for Observability API

Handles safe reading and writing of JSON files with file locking.
"""

import json
import fcntl
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from datetime import datetime


class DataAccessLayer:
    """Thread-safe data access for JSON files."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize data access layer.

        Args:
            data_dir: Root directory for data storage
        """
        self.data_dir = Path(data_dir)
        self.users_dir = self.data_dir / "users"
        self.story_dir = self.data_dir / "story"

        # Ensure directories exist
        self.users_dir.mkdir(parents=True, exist_ok=True)
        self.story_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _lock_file(self, file_path: Path, mode: str = 'r'):
        """
        Context manager for file locking.

        Args:
            file_path: Path to the file
            mode: File open mode ('r' or 'w')

        Yields:
            File handle with exclusive lock
        """
        f = open(file_path, mode)
        try:
            # Acquire exclusive lock (blocks until available)
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            yield f
        finally:
            # Release lock and close file
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            f.close()

    def read_json(self, file_path: Path) -> Optional[Dict]:
        """
        Read JSON file with locking.

        Args:
            file_path: Path to JSON file

        Returns:
            Dictionary data or None if file doesn't exist
        """
        if not file_path.exists():
            return None

        try:
            with self._lock_file(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None

    def write_json(self, file_path: Path, data: Dict) -> bool:
        """
        Write JSON file with locking.

        Args:
            file_path: Path to JSON file
            data: Dictionary to write

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with self._lock_file(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return False

    # User data methods

    def list_users(self) -> List[str]:
        """
        List all user IDs.

        Returns:
            List of user IDs
        """
        user_files = self.users_dir.glob("*.json")
        return [f.stem for f in user_files if f.is_file()]

    def get_user(self, user_id: str) -> Optional[Dict]:
        """
        Get user data.

        Args:
            user_id: User identifier

        Returns:
            User data dictionary or None
        """
        file_path = self.users_dir / f"{user_id}.json"
        return self.read_json(file_path)

    def save_user(self, user_id: str, user_data: Dict) -> bool:
        """
        Save user data.

        Args:
            user_id: User identifier
            user_data: User data dictionary

        Returns:
            True if successful
        """
        file_path = self.users_dir / f"{user_id}.json"
        user_data["updated_at"] = datetime.now().isoformat()
        return self.write_json(file_path, user_data)

    def delete_user(self, user_id: str) -> bool:
        """
        Delete user data file.

        Args:
            user_id: User identifier

        Returns:
            True if successful
        """
        file_path = self.users_dir / f"{user_id}.json"
        try:
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting user {user_id}: {e}")
            return False

    # Story data methods

    def get_chapters(self) -> Optional[Dict]:
        """
        Get chapters configuration.

        Returns:
            Chapters data or None
        """
        # Check both locations (root story dir and backend data dir)
        story_file = Path("story/chapters.json")
        if not story_file.exists():
            story_file = self.story_dir / "chapters.json"

        return self.read_json(story_file)

    def get_story_beats(self) -> Dict[str, Any]:
        """
        Get all story beats from beat files.

        Returns:
            Dictionary mapping beat_id to beat data
        """
        beats = {}

        # Check both locations
        beats_dir = Path("story/beats")
        if not beats_dir.exists():
            beats_dir = self.story_dir / "beats"

        if beats_dir.exists():
            for beat_file in beats_dir.glob("*.json"):
                beat_data = self.read_json(beat_file)
                if beat_data:
                    beat_id = beat_file.stem
                    beats[beat_id] = beat_data

        return beats
