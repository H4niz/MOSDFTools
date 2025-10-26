"""
Event Filter
============

Filter FSEvents based on various criteria.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set, Pattern
from mfaa.models import FSEvent, EventType, FilterConfig
from mfaa.utils.logger import setup_logger

logger = setup_logger(__name__)


class EventFilter:
    """Filter FSEvents based on configurable criteria."""

    def __init__(self, config: Optional[FilterConfig] = None):
        """
        Initialize EventFilter.

        Args:
            config: FilterConfig object with filtering rules
        """
        self.config = config or FilterConfig()
        self._compiled_patterns: List[Pattern] = []

        # Compile regex patterns for performance
        if self.config.path_patterns:
            for pattern_str in self.config.path_patterns:
                try:
                    self._compiled_patterns.append(re.compile(pattern_str))
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern_str}': {e}")

        logger.info(f"EventFilter initialized with {len(self._compiled_patterns)} path patterns")

    def filter_events(self, events: List[FSEvent]) -> List[FSEvent]:
        """
        Apply all configured filters to events.

        Args:
            events: List of FSEvent objects

        Returns:
            Filtered list of FSEvent objects
        """
        logger.info(f"Filtering {len(events)} events...")

        filtered = events

        # Apply each filter
        if self.config.event_types:
            filtered = self.filter_by_event_type(filtered, self.config.event_types)

        if self.config.path_patterns:
            filtered = self.filter_by_path_patterns(filtered, self.config.path_patterns)

        if self.config.extensions:
            filtered = self.filter_by_extensions(filtered, self.config.extensions)

        if self.config.time_range:
            filtered = self.filter_by_time_range(
                filtered,
                self.config.time_range[0],
                self.config.time_range[1]
            )

        logger.info(f"Filtering complete: {len(filtered)}/{len(events)} events remaining")
        return filtered

    def filter_by_event_type(
        self,
        events: List[FSEvent],
        event_types: List[str]
    ) -> List[FSEvent]:
        """
        Filter events by event type.

        Args:
            events: List of FSEvent objects
            event_types: List of event type names (e.g., ["Created", "Removed"])

        Returns:
            Filtered list matching specified event types
        """
        if not event_types:
            return events

        # Convert string names to EventType enum values
        target_types = set()
        for type_str in event_types:
            try:
                event_type = EventType(type_str)
                target_types.add(event_type)
            except ValueError:
                logger.warning(f"Unknown event type: {type_str}")

        filtered = []
        for event in events:
            # Check if event has any of the target types
            event_type_set = set(event.event_types)
            if event_type_set & target_types:  # Intersection
                filtered.append(event)

        logger.debug(f"Event type filter: {len(filtered)}/{len(events)} events")
        return filtered

    def filter_by_path_patterns(
        self,
        events: List[FSEvent],
        patterns: List[str]
    ) -> List[FSEvent]:
        """
        Filter events by path patterns (regex).

        Args:
            events: List of FSEvent objects
            patterns: List of regex patterns

        Returns:
            Filtered list matching path patterns
        """
        if not patterns or not self._compiled_patterns:
            return events

        filtered = []
        for event in events:
            path_str = str(event.path)

            # Check if path matches any pattern
            for pattern in self._compiled_patterns:
                if pattern.search(path_str):
                    filtered.append(event)
                    break

        logger.debug(f"Path pattern filter: {len(filtered)}/{len(events)} events")
        return filtered

    def filter_by_extensions(
        self,
        events: List[FSEvent],
        extensions: List[str]
    ) -> List[FSEvent]:
        """
        Filter events by file extensions.

        Args:
            events: List of FSEvent objects
            extensions: List of file extensions (e.g., [".txt", ".log"])

        Returns:
            Filtered list with matching extensions
        """
        if not extensions:
            return events

        # Normalize extensions (ensure they start with '.')
        normalized_exts = set()
        for ext in extensions:
            if not ext.startswith('.'):
                ext = '.' + ext
            normalized_exts.add(ext.lower())

        filtered = []
        for event in events:
            file_ext = event.path.suffix.lower()
            if file_ext in normalized_exts:
                filtered.append(event)

        logger.debug(f"Extension filter: {len(filtered)}/{len(events)} events")
        return filtered

    def filter_by_time_range(
        self,
        events: List[FSEvent],
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> List[FSEvent]:
        """
        Filter events by time range.

        Args:
            events: List of FSEvent objects
            start_time: Start datetime (inclusive)
            end_time: End datetime (inclusive)

        Returns:
            Filtered list within time range
        """
        if not start_time and not end_time:
            return events

        filtered = []
        for event in events:
            # Check if event is within range
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue

            filtered.append(event)

        logger.debug(f"Time range filter: {len(filtered)}/{len(events)} events")
        return filtered

    def filter_by_priority(
        self,
        events: List[FSEvent],
        min_priority: int
    ) -> List[FSEvent]:
        """
        Filter events by minimum priority score.

        Note: Requires events to have been scored by PriorityScorer first.

        Args:
            events: List of FSEvent objects
            min_priority: Minimum priority score (0-100)

        Returns:
            Filtered list with priority >= min_priority
        """
        # This assumes events have a 'priority_score' attribute
        # Added by PriorityScorer
        filtered = []
        for event in events:
            if hasattr(event, 'priority_score') and event.priority_score >= min_priority:
                filtered.append(event)

        logger.debug(f"Priority filter: {len(filtered)}/{len(events)} events")
        return filtered

    def filter_executables(self, events: List[FSEvent]) -> List[FSEvent]:
        """
        Filter for executable files.

        Returns:
            Events for executable file types
        """
        executable_exts = {'.app', '.command', '.sh', '.bash', '.zsh', '.py', '.pl',
                          '.rb', '.jar', '.pkg', '.dmg', '.exe', '.dll', '.scr'}

        filtered = []
        for event in events:
            if event.path.suffix.lower() in executable_exts:
                filtered.append(event)

        logger.debug(f"Executable filter: {len(filtered)}/{len(events)} events")
        return filtered

    def filter_documents(self, events: List[FSEvent]) -> List[FSEvent]:
        """
        Filter for document files.

        Returns:
            Events for document file types
        """
        document_exts = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                        '.txt', '.rtf', '.pages', '.numbers', '.keynote'}

        filtered = []
        for event in events:
            if event.path.suffix.lower() in document_exts:
                filtered.append(event)

        logger.debug(f"Document filter: {len(filtered)}/{len(events)} events")
        return filtered

    def filter_suspicious_paths(self, events: List[FSEvent]) -> List[FSEvent]:
        """
        Filter for events in suspicious locations.

        Returns:
            Events in suspicious paths (tmp, LaunchAgents, etc.)
        """
        suspicious_patterns = [
            r'^/tmp/',
            r'^/var/tmp/',
            r'^/private/tmp/',
            r'/Library/LaunchAgents/',
            r'/Library/LaunchDaemons/',
            r'/Users/.*/Library/LaunchAgents/',
            r'\.bash_profile$',
            r'\.zshrc$',
            r'\.bashrc$',
        ]

        compiled_patterns = [re.compile(p) for p in suspicious_patterns]

        filtered = []
        for event in events:
            path_str = str(event.path)
            for pattern in compiled_patterns:
                if pattern.search(path_str):
                    filtered.append(event)
                    break

        logger.debug(f"Suspicious path filter: {len(filtered)}/{len(events)} events")
        return filtered

    def get_filter_statistics(self, events: List[FSEvent]) -> dict:
        """
        Get statistics about filtered events.

        Args:
            events: List of FSEvent objects

        Returns:
            Dictionary with filter statistics
        """
        stats = {
            'total_events': len(events),
            'by_type': {},
            'by_extension': {},
            'time_range': None
        }

        # Count by event type
        for event in events:
            for event_type in event.event_types:
                type_name = event_type.value
                stats['by_type'][type_name] = stats['by_type'].get(type_name, 0) + 1

        # Count by extension
        for event in events:
            ext = event.path.suffix.lower() or '(no extension)'
            stats['by_extension'][ext] = stats['by_extension'].get(ext, 0) + 1

        # Get time range
        if events:
            timestamps = [e.timestamp for e in events if e.timestamp.year > 2001]
            if timestamps:
                stats['time_range'] = {
                    'earliest': min(timestamps).isoformat(),
                    'latest': max(timestamps).isoformat()
                }

        return stats
