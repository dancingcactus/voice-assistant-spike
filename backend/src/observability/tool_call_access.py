"""
Data access layer for tool call logs.
Handles reading/writing JSONL format tool call logs.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from collections import defaultdict

from .tool_call_models import (
    ToolCallLog,
    ToolCallFilter,
    ToolCallStatistics,
    ToolUsageStats,
    CharacterUsageStats,
    ToolCallStatus,
)


class ToolCallDataAccess:
    """
    Access layer for tool call logs.
    Uses JSONL format for append-only logging.
    """

    def __init__(self, data_dir: str):
        """Initialize with data directory path"""
        self.data_dir = Path(data_dir)
        self.tool_logs_dir = self.data_dir / "tool_logs"
        self.tool_logs_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file_path(self, user_id: str) -> Path:
        """Get path to tool log file for a user"""
        return self.tool_logs_dir / f"{user_id}_tool_calls.jsonl"

    def append_tool_call(self, log_entry: ToolCallLog) -> None:
        """
        Append a tool call log entry to the user's JSONL file.
        Thread-safe append operation.
        """
        log_file = self._get_log_file_path(log_entry.user_id)

        # Convert to dict and ensure datetime is serialized
        log_dict = log_entry.model_dump(mode="json")

        # Append to JSONL file
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_dict) + "\n")

    def get_tool_calls(
        self,
        user_id: str,
        filters: Optional[ToolCallFilter] = None
    ) -> List[ToolCallLog]:
        """
        Get tool calls for a user with optional filtering.
        Returns most recent first.
        """
        log_file = self._get_log_file_path(user_id)

        if not log_file.exists():
            return []

        # Read all lines
        logs: List[ToolCallLog] = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    log = ToolCallLog(**data)
                    logs.append(log)
                except (json.JSONDecodeError, ValueError) as e:
                    # Skip malformed lines
                    print(f"Skipping malformed log line: {e}")
                    continue

        # Apply filters
        if filters:
            logs = self._apply_filters(logs, filters)

        # Sort by timestamp descending (most recent first)
        logs.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        if filters:
            start = filters.offset
            end = start + filters.limit
            logs = logs[start:end]

        return logs

    def get_tool_call_by_id(self, user_id: str, call_id: str) -> Optional[ToolCallLog]:
        """Get a specific tool call by ID"""
        log_file = self._get_log_file_path(user_id)

        if not log_file.exists():
            return None

        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    if data.get("call_id") == call_id:
                        return ToolCallLog(**data)
                except (json.JSONDecodeError, ValueError):
                    continue

        return None

    def _apply_filters(
        self,
        logs: List[ToolCallLog],
        filters: ToolCallFilter
    ) -> List[ToolCallLog]:
        """Apply filter criteria to log list"""
        filtered = logs

        if filters.tool_name:
            filtered = [log for log in filtered if log.tool_name == filters.tool_name]

        if filters.character:
            filtered = [log for log in filtered if log.character == filters.character]

        if filters.status:
            filtered = [log for log in filtered if log.status == filters.status]

        if filters.start_time:
            filtered = [log for log in filtered if log.timestamp >= filters.start_time]

        if filters.end_time:
            filtered = [log for log in filtered if log.timestamp <= filters.end_time]

        return filtered

    def get_statistics(
        self,
        user_id: str,
        time_range: Optional[timedelta] = None
    ) -> ToolCallStatistics:
        """
        Calculate statistics for tool calls.
        Optionally limit to a specific time range (e.g., last 24 hours).
        """
        # Get all logs (or filtered by time)
        filters = ToolCallFilter(limit=1000)  # Get up to 1000 logs for stats
        if time_range:
            filters.start_time = datetime.now() - time_range

        logs = self.get_tool_calls(user_id, filters)

        if not logs:
            return ToolCallStatistics(
                total_calls=0,
                total_successes=0,
                total_errors=0,
                overall_success_rate=0.0,
                avg_duration_ms=0.0,
            )

        # Overall stats
        total_calls = len(logs)
        total_successes = sum(1 for log in logs if log.status == ToolCallStatus.SUCCESS)
        total_errors = total_calls - total_successes
        overall_success_rate = (total_successes / total_calls * 100) if total_calls > 0 else 0.0
        avg_duration_ms = sum(log.duration_ms for log in logs) / total_calls

        # Time range
        earliest_call = min(log.timestamp for log in logs)
        latest_call = max(log.timestamp for log in logs)

        # By tool breakdown
        tool_stats = self._calculate_tool_stats(logs)

        # By character breakdown
        character_stats = self._calculate_character_stats(logs)

        # Top lists
        slowest_calls = sorted(logs, key=lambda x: x.duration_ms, reverse=True)[:5]
        recent_errors = [
            log for log in sorted(logs, key=lambda x: x.timestamp, reverse=True)
            if log.status != ToolCallStatus.SUCCESS
        ][:5]

        return ToolCallStatistics(
            total_calls=total_calls,
            total_successes=total_successes,
            total_errors=total_errors,
            overall_success_rate=overall_success_rate,
            avg_duration_ms=avg_duration_ms,
            earliest_call=earliest_call,
            latest_call=latest_call,
            by_tool=tool_stats,
            by_character=character_stats,
            slowest_calls=slowest_calls,
            recent_errors=recent_errors,
        )

    def _calculate_tool_stats(self, logs: List[ToolCallLog]) -> List[ToolUsageStats]:
        """Calculate per-tool statistics"""
        tool_data: Dict[str, List[ToolCallLog]] = defaultdict(list)

        for log in logs:
            tool_data[log.tool_name].append(log)

        stats = []
        for tool_name, tool_logs in tool_data.items():
            total = len(tool_logs)
            successes = sum(1 for log in tool_logs if log.status == ToolCallStatus.SUCCESS)
            errors = total - successes
            success_rate = (successes / total * 100) if total > 0 else 0.0

            durations = [log.duration_ms for log in tool_logs]
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)

            last_used = max(log.timestamp for log in tool_logs)

            stats.append(ToolUsageStats(
                tool_name=tool_name,
                total_calls=total,
                success_count=successes,
                error_count=errors,
                success_rate=success_rate,
                avg_duration_ms=avg_duration,
                min_duration_ms=min_duration,
                max_duration_ms=max_duration,
                last_used=last_used,
            ))

        # Sort by total calls descending
        stats.sort(key=lambda x: x.total_calls, reverse=True)
        return stats

    def _calculate_character_stats(self, logs: List[ToolCallLog]) -> List[CharacterUsageStats]:
        """Calculate per-character statistics"""
        character_data: Dict[str, List[ToolCallLog]] = defaultdict(list)

        for log in logs:
            if log.character:
                character_data[log.character].append(log)

        stats = []
        for character, char_logs in character_data.items():
            total = len(char_logs)
            successes = sum(1 for log in char_logs if log.status == ToolCallStatus.SUCCESS)
            errors = total - successes
            success_rate = (successes / total * 100) if total > 0 else 0.0

            durations = [log.duration_ms for log in char_logs]
            avg_duration = sum(durations) / len(durations)

            # Find most used tool
            tool_counts: Dict[str, int] = defaultdict(int)
            for log in char_logs:
                tool_counts[log.tool_name] += 1
            most_used_tool = max(tool_counts.items(), key=lambda x: x[1])[0] if tool_counts else None

            stats.append(CharacterUsageStats(
                character=character,
                total_calls=total,
                success_count=successes,
                error_count=errors,
                success_rate=success_rate,
                most_used_tool=most_used_tool,
                avg_duration_ms=avg_duration,
            ))

        # Sort by total calls descending
        stats.sort(key=lambda x: x.total_calls, reverse=True)
        return stats

    def get_tool_calls_for_turn(self, turn_id: str, user_id: Optional[str] = None) -> List[ToolCallLog]:
        """
        Get all tool calls associated with a specific turn_id.

        Args:
            turn_id: The turn correlation ID to filter by.
            user_id: Optional user to scope the search. If omitted, all JSONL
                     files in the tool_logs directory are searched.

        Returns:
            List of ToolCallLog entries for that turn, in file order.
        """
        if user_id:
            files = [self._get_log_file_path(user_id)]
        else:
            files = list(self.tool_logs_dir.glob("*_tool_calls.jsonl"))

        results: List[ToolCallLog] = []
        for log_file in files:
            if not log_file.exists():
                continue
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("turn_id") == turn_id:
                            results.append(ToolCallLog(**data))
                    except (json.JSONDecodeError, ValueError):
                        continue
        return results

    def get_all_tool_names(self, user_id: str) -> List[str]:
        """Get list of all unique tool names for a user"""
        log_file = self._get_log_file_path(user_id)

        if not log_file.exists():
            return []

        tool_names = set()
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    tool_names.add(data.get("tool_name"))
                except (json.JSONDecodeError, ValueError):
                    continue

        return sorted(tool_names)

    def get_all_characters(self, user_id: str) -> List[str]:
        """Get list of all unique characters for a user"""
        log_file = self._get_log_file_path(user_id)

        if not log_file.exists():
            return []

        characters = set()
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    char = data.get("character")
                    if char:
                        characters.add(char)
                except (json.JSONDecodeError, ValueError):
                    continue

        return sorted(characters)
