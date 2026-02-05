"""
Story Data Accessor for Observability API

Provides read access to story configuration (chapters, beats) and user story progress.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class StoryAccessLayer:
    """Access layer for story configuration and user progress."""

    def __init__(self, project_root: str):
        """
        Initialize story access layer.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.story_dir = self.project_root / "story"
        self.users_dir = self.project_root / "data" / "users"

        # Load story configuration
        self._chapters_cache = None
        self._beats_cache = {}

    def _load_chapters(self) -> Dict[str, Any]:
        """Load chapters configuration."""
        if self._chapters_cache is None:
            chapters_file = self.story_dir / "chapters.json"
            if chapters_file.exists():
                with open(chapters_file, 'r') as f:
                    self._chapters_cache = json.load(f)
            else:
                self._chapters_cache = {"chapters": [], "metadata": {}}
        return self._chapters_cache

    def _load_chapter_beats(self, chapter_id: int) -> Dict[str, Any]:
        """Load beats for a specific chapter."""
        if chapter_id not in self._beats_cache:
            beats_file = self.story_dir / "beats" / f"chapter{chapter_id}.json"
            if beats_file.exists():
                with open(beats_file, 'r') as f:
                    self._beats_cache[chapter_id] = json.load(f)
            else:
                self._beats_cache[chapter_id] = {"chapter": chapter_id, "beats": []}
        return self._beats_cache[chapter_id]

    def get_all_chapters(self) -> List[Dict[str, Any]]:
        """Get all chapter definitions."""
        chapters_data = self._load_chapters()
        return chapters_data.get("chapters", [])

    def get_chapter(self, chapter_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific chapter definition."""
        chapters = self.get_all_chapters()
        for chapter in chapters:
            if chapter["id"] == chapter_id:
                return chapter
        return None

    def get_chapter_beats(self, chapter_id: int) -> List[Dict[str, Any]]:
        """Get all beats for a chapter."""
        beats_data = self._load_chapter_beats(chapter_id)
        return beats_data.get("beats", [])

    def get_beat(self, chapter_id: int, beat_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific beat definition."""
        beats = self.get_chapter_beats(chapter_id)
        for beat in beats:
            if beat["id"] == beat_id:
                return beat
        return None

    def get_user_story_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's story progress."""
        user_file = self.users_dir / f"{user_id}.json"
        if not user_file.exists():
            return None

        with open(user_file, 'r') as f:
            user_data = json.load(f)

        return user_data.get("story_progress", {})

    def get_user_beat_status(self, user_id: str, beat_id: str) -> Dict[str, Any]:
        """
        Get the status of a specific beat for a user.

        Returns:
            Dict with keys: delivered, timestamp, variant, stage (if applicable)
        """
        progress = self.get_user_story_progress(user_id)
        if not progress:
            return {"delivered": False}

        beats_delivered = progress.get("beats_delivered", {})
        beat_status = beats_delivered.get(beat_id, {})

        if beat_status:
            return {
                "delivered": beat_status.get("delivered", False),
                "timestamp": beat_status.get("timestamp"),
                "variant": beat_status.get("variant"),
                "stage": beat_status.get("stage")
            }

        return {"delivered": False}

    def get_enriched_chapter_beats(self, chapter_id: int, user_id: str) -> List[Dict[str, Any]]:
        """
        Get chapter beats enriched with user progress information.

        Each beat includes:
        - All beat definition fields
        - status: "delivered", "ready", "locked"
        - delivery_info: timestamp, variant, stage if delivered
        """
        beats = self.get_chapter_beats(chapter_id)
        progress = self.get_user_story_progress(user_id)

        if not progress:
            # No progress, all beats are locked except early ones
            return [
                {
                    **beat,
                    "status": "locked",
                    "delivery_info": None
                }
                for beat in beats
            ]

        beats_delivered = progress.get("beats_delivered", {})
        current_chapter = progress.get("current_chapter", 1)

        enriched_beats = []
        for beat in beats:
            beat_id = beat["id"]
            beat_status_info = beats_delivered.get(beat_id, {})

            # Determine status
            if beat_status_info.get("delivered"):
                status = "delivered"
                delivery_info = {
                    "timestamp": beat_status_info.get("timestamp"),
                    "variant": beat_status_info.get("variant"),
                    "stage": beat_status_info.get("stage")
                }
            elif current_chapter == chapter_id:
                # Beat is in current chapter, check if ready to deliver
                status = "ready"  # Simplified - actual logic would check conditions
                delivery_info = None
            else:
                status = "locked"
                delivery_info = None

            enriched_beats.append({
                **beat,
                "status": status,
                "delivery_info": delivery_info
            })

        return enriched_beats

    def generate_chapter_flow_diagram(self, chapter_id: int, user_id: Optional[str] = None) -> str:
        """
        Generate a Mermaid flowchart diagram for chapter beat dependencies.

        Args:
            chapter_id: Chapter ID to generate diagram for
            user_id: Optional user ID to color-code beats by delivery status

        Returns:
            Mermaid diagram syntax as string
        """
        beats = self.get_chapter_beats(chapter_id)
        chapter = self.get_chapter(chapter_id)

        if not beats or not chapter:
            return "graph TD\n  A[No beats found]"

        # Get user progress if user_id provided
        user_progress = None
        if user_id:
            user_progress = self.get_user_story_progress(user_id)

        # Start Mermaid diagram
        lines = ["graph TD"]

        # Add chapter title
        lines.append(f"  ChapterStart[{chapter['title']}]")

        # Track which beats we've added
        added_beats = set()

        # Add beats
        for beat in beats:
            beat_id = beat["id"]
            beat_name = beat_id.replace("_", " ").title()

            # Determine node style based on user progress or required status
            if user_id and user_progress:
                # Color by delivery status
                beat_status = self.get_user_beat_status(user_id, beat_id)
                if beat_status.get("delivered"):
                    node_style = f"{beat_id}[{beat_name}]:::delivered"
                elif beat_status.get("status") == "ready":
                    node_style = f"{beat_id}[{beat_name}]:::ready"
                elif beat_status.get("status") == "locked":
                    node_style = f"{beat_id}[{beat_name}]:::locked"
                else:
                    node_style = f"{beat_id}[{beat_name}]:::notStarted"
            else:
                # Color by required status (default behavior)
                if beat.get("required"):
                    node_style = f"{beat_id}[{beat_name}]:::required"
                else:
                    node_style = f"{beat_id}[{beat_name}]:::optional"

            lines.append(f"  {node_style}")
            added_beats.add(beat_id)

            # Add connection from chapter start for early beats
            if beat.get("priority") == "early":
                lines.append(f"  ChapterStart --> {beat_id}")

            # Add dependencies based on conditions
            conditions = beat.get("conditions", {})
            for condition_key, condition_value in conditions.items():
                if condition_key.endswith("_delivered") and condition_value:
                    prerequisite_beat = condition_key.replace("_delivered", "")
                    if prerequisite_beat in added_beats:
                        lines.append(f"  {prerequisite_beat} --> {beat_id}")

        # Add styling based on mode
        if user_id and user_progress:
            # User-specific colors (status-based)
            lines.append("  classDef delivered fill:#10b981,stroke:#059669,color:#fff")
            lines.append("  classDef ready fill:#f59e0b,stroke:#d97706,color:#fff")
            lines.append("  classDef notStarted fill:#3b82f6,stroke:#2563eb,color:#fff")
            lines.append("  classDef locked fill:#6b7280,stroke:#4b5563,color:#fff")
        else:
            # Default colors (required/optional)
            lines.append("  classDef required fill:#4a90e2,stroke:#2e5c8a,color:#fff")
            lines.append("  classDef optional fill:#6c757d,stroke:#495057,color:#fff")

        return "\n".join(lines)

    def get_user_chapter_progress_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a summary of user's progress in current chapter.

        Returns:
            Dict with: current_chapter, beats_total, beats_delivered,
                      beats_ready, interaction_count, chapter_start_time
        """
        progress = self.get_user_story_progress(user_id)
        if not progress:
            return {
                "current_chapter": 1,
                "beats_total": 0,
                "beats_delivered": 0,
                "beats_ready": 0,
                "interaction_count": 0,
                "chapter_start_time": None
            }

        current_chapter = progress.get("current_chapter", 1)
        beats = self.get_chapter_beats(current_chapter)
        beats_delivered_dict = progress.get("beats_delivered", {})

        # Count beats
        beats_total = len(beats)
        beats_delivered = sum(
            1 for beat_id in [b["id"] for b in beats]
            if beats_delivered_dict.get(beat_id, {}).get("delivered")
        )

        return {
            "current_chapter": current_chapter,
            "beats_total": beats_total,
            "beats_delivered": beats_delivered,
            "beats_ready": beats_total - beats_delivered,
            "interaction_count": progress.get("interaction_count", 0),
            "chapter_start_time": progress.get("chapter_start_time")
        }
