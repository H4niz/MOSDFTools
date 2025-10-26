"""
Timeline Grouper
=================

Group related timeline entries for better visualization.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from pathlib import Path
from collections import defaultdict
from mfaa.models import TimelineEntry, FSEvent, EventType
from mfaa.utils.logger import setup_logger

logger = setup_logger(__name__)


class TimelineGrouper:
    """Group related timeline entries."""

    def __init__(self, time_threshold_seconds: int = 60):
        """
        Initialize TimelineGrouper.

        Args:
            time_threshold_seconds: Time threshold for grouping events (default: 60s)
        """
        self.time_threshold = timedelta(seconds=time_threshold_seconds)
        logger.debug(f"TimelineGrouper initialized (threshold: {time_threshold_seconds}s)")

    def group_by_path(
        self,
        entries: List[TimelineEntry]
    ) -> Dict[Path, List[TimelineEntry]]:
        """
        Group timeline entries by file path.

        Args:
            entries: List of TimelineEntry objects

        Returns:
            Dictionary mapping paths to entries
        """
        logger.debug(f"Grouping {len(entries)} entries by path")

        grouped: Dict[Path, List[TimelineEntry]] = defaultdict(list)

        for entry in entries:
            grouped[entry.event.path].append(entry)

        # Sort each group chronologically
        for path in grouped:
            grouped[path].sort(key=lambda e: e.event.timestamp)

        logger.info(f"Grouped into {len(grouped)} unique paths")
        return dict(grouped)

    def group_by_directory(
        self,
        entries: List[TimelineEntry]
    ) -> Dict[Path, List[TimelineEntry]]:
        """
        Group timeline entries by parent directory.

        Args:
            entries: List of TimelineEntry objects

        Returns:
            Dictionary mapping directories to entries
        """
        logger.debug(f"Grouping {len(entries)} entries by directory")

        grouped: Dict[Path, List[TimelineEntry]] = defaultdict(list)

        for entry in entries:
            parent = entry.event.path.parent
            grouped[parent].append(entry)

        # Sort each group chronologically
        for directory in grouped:
            grouped[directory].sort(key=lambda e: e.event.timestamp)

        logger.info(f"Grouped into {len(grouped)} directories")
        return dict(grouped)

    def group_by_priority(
        self,
        entries: List[TimelineEntry]
    ) -> Dict[str, List[TimelineEntry]]:
        """
        Group timeline entries by priority category.

        Args:
            entries: List of TimelineEntry objects

        Returns:
            Dictionary mapping priority categories to entries
        """
        logger.debug(f"Grouping {len(entries)} entries by priority")

        grouped: Dict[str, List[TimelineEntry]] = defaultdict(list)

        for entry in entries:
            grouped[entry.priority_category].append(entry)

        # Sort each group chronologically
        for category in grouped:
            grouped[category].sort(key=lambda e: e.event.timestamp)

        logger.info(f"Priority distribution: {', '.join(f'{k}={len(v)}' for k, v in grouped.items())}")
        return dict(grouped)

    def group_by_event_type(
        self,
        entries: List[TimelineEntry]
    ) -> Dict[str, List[TimelineEntry]]:
        """
        Group timeline entries by primary event type.

        Args:
            entries: List of TimelineEntry objects

        Returns:
            Dictionary mapping event types to entries
        """
        logger.debug(f"Grouping {len(entries)} entries by event type")

        grouped: Dict[str, List[TimelineEntry]] = defaultdict(list)

        for entry in entries:
            # Use first event type as primary
            if entry.event.event_types:
                primary_type = entry.event.event_types[0].value
                grouped[primary_type].append(entry)

        # Sort each group chronologically
        for event_type in grouped:
            grouped[event_type].sort(key=lambda e: e.event.timestamp)

        logger.info(f"Grouped into {len(grouped)} event types")
        return dict(grouped)

    def group_by_time_window(
        self,
        entries: List[TimelineEntry],
        window_size_minutes: int = 60
    ) -> List[List[TimelineEntry]]:
        """
        Group timeline entries into time windows.

        Args:
            entries: List of TimelineEntry objects
            window_size_minutes: Size of time window in minutes

        Returns:
            List of groups, each containing entries within window
        """
        logger.debug(f"Grouping {len(entries)} entries by {window_size_minutes}min windows")

        if not entries:
            return []

        # Sort entries chronologically
        sorted_entries = sorted(entries, key=lambda e: e.event.timestamp)

        groups = []
        current_group = [sorted_entries[0]]
        window_start = sorted_entries[0].event.timestamp

        for entry in sorted_entries[1:]:
            window_end = window_start + timedelta(minutes=window_size_minutes)

            if entry.event.timestamp <= window_end:
                # Within current window
                current_group.append(entry)
            else:
                # Start new window
                groups.append(current_group)
                current_group = [entry]
                window_start = entry.event.timestamp

        # Add final group
        if current_group:
            groups.append(current_group)

        logger.info(f"Created {len(groups)} time windows")
        return groups

    def group_related_events(
        self,
        entries: List[TimelineEntry]
    ) -> List[List[TimelineEntry]]:
        """
        Group related events based on path and time proximity.

        Events are considered related if they:
        - Affect the same file or directory
        - Occur within time_threshold seconds of each other

        Args:
            entries: List of TimelineEntry objects

        Returns:
            List of groups with related entries
        """
        logger.debug(f"Grouping {len(entries)} related events")

        if not entries:
            return []

        # Sort entries chronologically
        sorted_entries = sorted(entries, key=lambda e: e.event.timestamp)

        groups = []
        current_group = [sorted_entries[0]]

        for entry in sorted_entries[1:]:
            prev_entry = current_group[-1]

            # Check if related to current group
            is_related = self._are_entries_related(prev_entry, entry)

            if is_related:
                current_group.append(entry)
            else:
                # Start new group
                groups.append(current_group)
                current_group = [entry]

        # Add final group
        if current_group:
            groups.append(current_group)

        logger.info(f"Created {len(groups)} related event groups")
        return groups

    def _are_entries_related(
        self,
        entry1: TimelineEntry,
        entry2: TimelineEntry
    ) -> bool:
        """
        Check if two entries are related.

        Args:
            entry1: First TimelineEntry
            entry2: Second TimelineEntry

        Returns:
            True if entries are related
        """
        # Check time proximity
        time_diff = abs(entry2.event.timestamp - entry1.event.timestamp)
        if time_diff > self.time_threshold:
            return False

        # Check path relationship
        path1 = entry1.event.path
        path2 = entry2.event.path

        # Same path
        if path1 == path2:
            return True

        # Same directory
        if path1.parent == path2.parent:
            return True

        # Parent-child relationship
        if path1 in path2.parents or path2 in path1.parents:
            return True

        return False

    def group_file_operations(
        self,
        entries: List[TimelineEntry]
    ) -> Dict[str, List[TimelineEntry]]:
        """
        Group entries by operation type (create, modify, delete, etc.).

        Args:
            entries: List of TimelineEntry objects

        Returns:
            Dictionary mapping operation types to entries
        """
        logger.debug(f"Grouping {len(entries)} entries by file operation")

        operations = {
            'created': [],
            'modified': [],
            'deleted': [],
            'renamed': [],
            'permission_changed': [],
            'xattr_modified': [],
            'other': []
        }

        for entry in entries:
            event_types = entry.event.event_types

            if EventType.ITEM_CREATED in event_types:
                operations['created'].append(entry)
            elif EventType.ITEM_REMOVED in event_types:
                operations['deleted'].append(entry)
            elif EventType.ITEM_RENAMED in event_types:
                operations['renamed'].append(entry)
            elif EventType.ITEM_MODIFIED in event_types:
                operations['modified'].append(entry)
            elif EventType.ITEM_CHANGE_OWNER in event_types:
                operations['permission_changed'].append(entry)
            elif EventType.ITEM_XATTR_MOD in event_types:
                operations['xattr_modified'].append(entry)
            else:
                operations['other'].append(entry)

        # Sort each group chronologically
        for operation in operations:
            operations[operation].sort(key=lambda e: e.event.timestamp)

        # Log distribution
        non_empty = {k: len(v) for k, v in operations.items() if v}
        logger.info(f"Operations: {', '.join(f'{k}={v}' for k, v in non_empty.items())}")

        return operations

    def group_by_file_extension(
        self,
        entries: List[TimelineEntry]
    ) -> Dict[str, List[TimelineEntry]]:
        """
        Group entries by file extension.

        Args:
            entries: List of TimelineEntry objects

        Returns:
            Dictionary mapping extensions to entries
        """
        logger.debug(f"Grouping {len(entries)} entries by file extension")

        grouped: Dict[str, List[TimelineEntry]] = defaultdict(list)

        for entry in entries:
            suffix = entry.event.path.suffix.lower()
            ext = suffix if suffix else '(no extension)'
            grouped[ext].append(entry)

        # Sort each group chronologically
        for ext in grouped:
            grouped[ext].sort(key=lambda e: e.event.timestamp)

        logger.info(f"Grouped into {len(grouped)} file extensions")
        return dict(grouped)

    def group_suspicious_activity(
        self,
        entries: List[TimelineEntry],
        min_priority: int = 70
    ) -> Dict[str, List[TimelineEntry]]:
        """
        Group suspicious activities by type.

        Args:
            entries: List of TimelineEntry objects
            min_priority: Minimum priority score for suspicious activity

        Returns:
            Dictionary mapping activity types to entries
        """
        logger.debug(f"Grouping suspicious activities (min priority: {min_priority})")

        # Filter high-priority entries
        suspicious = [e for e in entries if e.priority_score >= min_priority]

        activities = {
            'quarantined_downloads': [],
            'system_modifications': [],
            'rapid_changes': [],
            'bulk_deletions': [],
            'permission_escalations': [],
            'other_suspicious': []
        }

        for entry in suspicious:
            # Quarantined downloads
            if entry.xattr and entry.xattr.has_quarantine:
                activities['quarantined_downloads'].append(entry)
                continue

            # System modifications
            path_str = str(entry.event.path)
            if any(sys_path in path_str for sys_path in ['/System/', '/Library/', '/usr/']):
                activities['system_modifications'].append(entry)
                continue

            # Bulk deletions
            if EventType.ITEM_REMOVED in entry.event.event_types:
                activities['bulk_deletions'].append(entry)
                continue

            # Permission changes
            if EventType.ITEM_CHANGE_OWNER in entry.event.event_types:
                activities['permission_escalations'].append(entry)
                continue

            # Other suspicious
            activities['other_suspicious'].append(entry)

        # Sort each group chronologically
        for activity in activities:
            activities[activity].sort(key=lambda e: e.event.timestamp)

        # Log distribution
        non_empty = {k: len(v) for k, v in activities.items() if v}
        logger.info(f"Suspicious activities: {', '.join(f'{k}={v}' for k, v in non_empty.items())}")

        return activities

    def create_hourly_groups(
        self,
        entries: List[TimelineEntry]
    ) -> Dict[str, List[TimelineEntry]]:
        """
        Group entries by hour of day.

        Args:
            entries: List of TimelineEntry objects

        Returns:
            Dictionary mapping hour labels to entries
        """
        logger.debug(f"Grouping {len(entries)} entries by hour")

        grouped: Dict[str, List[TimelineEntry]] = defaultdict(list)

        for entry in entries:
            timestamp = entry.event.timestamp
            hour_label = f"{timestamp.year}-{timestamp.month:02d}-{timestamp.day:02d} {timestamp.hour:02d}:00"
            grouped[hour_label].append(entry)

        # Sort each group chronologically
        for hour in grouped:
            grouped[hour].sort(key=lambda e: e.event.timestamp)

        logger.info(f"Grouped into {len(grouped)} hourly buckets")
        return dict(grouped)

    def create_daily_groups(
        self,
        entries: List[TimelineEntry]
    ) -> Dict[str, List[TimelineEntry]]:
        """
        Group entries by day.

        Args:
            entries: List of TimelineEntry objects

        Returns:
            Dictionary mapping date labels to entries
        """
        logger.debug(f"Grouping {len(entries)} entries by day")

        grouped: Dict[str, List[TimelineEntry]] = defaultdict(list)

        for entry in entries:
            date_label = entry.event.timestamp.date().isoformat()
            grouped[date_label].append(entry)

        # Sort each group chronologically
        for day in grouped:
            grouped[day].sort(key=lambda e: e.event.timestamp)

        logger.info(f"Grouped into {len(grouped)} daily buckets")
        return dict(grouped)

    def custom_grouping(
        self,
        entries: List[TimelineEntry],
        key_func: Callable[[TimelineEntry], str]
    ) -> Dict[str, List[TimelineEntry]]:
        """
        Group entries using a custom key function.

        Args:
            entries: List of TimelineEntry objects
            key_func: Function that takes TimelineEntry and returns grouping key

        Returns:
            Dictionary mapping keys to entries
        """
        logger.debug(f"Grouping {len(entries)} entries with custom function")

        grouped: Dict[str, List[TimelineEntry]] = defaultdict(list)

        for entry in entries:
            try:
                key = key_func(entry)
                grouped[key].append(entry)
            except Exception as e:
                logger.warning(f"Error applying key function to entry: {e}")

        # Sort each group chronologically
        for key in grouped:
            grouped[key].sort(key=lambda e: e.event.timestamp)

        logger.info(f"Custom grouping created {len(grouped)} groups")
        return dict(grouped)
