"""
Event Correlator
================

Correlate and group related FSEvents.
"""

from datetime import timedelta
from collections import defaultdict
from typing import List, Dict, Set
from pathlib import Path
from mfaa.models import FSEvent
from mfaa.utils.logger import setup_logger

logger = setup_logger(__name__)


class EventCorrelator:
    """Correlate and group related events."""

    # Correlation time windows
    RENAME_SEQUENCE_WINDOW = 5  # seconds
    DIRECTORY_OPERATION_WINDOW = 10  # seconds
    FILE_MODIFICATION_WINDOW = 60  # seconds

    def __init__(self):
        """Initialize EventCorrelator."""
        logger.info("EventCorrelator initialized")

    def correlate_events(self, events: List[FSEvent]) -> Dict[str, List[List[FSEvent]]]:
        """
        Correlate events and group related ones.

        Args:
            events: List of FSEvent objects

        Returns:
            Dictionary with correlation types and grouped events
        """
        logger.info(f"Correlating {len(events)} events...")

        correlations = {
            'rename_sequences': self.group_rename_sequences(events),
            'directory_operations': self.group_directory_operations(events),
            'file_modifications': self.group_file_modifications(events),
            'by_path': self.group_by_path(events)
        }

        total_groups = sum(len(groups) for groups in correlations.values())
        logger.info(f"Created {total_groups} correlation groups")

        return correlations

    def group_rename_sequences(self, events: List[FSEvent]) -> List[List[FSEvent]]:
        """
        Group rename sequences (file renamed multiple times).

        Args:
            events: List of FSEvent objects

        Returns:
            List of event groups
        """
        rename_groups = []
        rename_events = sorted(
            [e for e in events if e.is_renamed],
            key=lambda x: x.timestamp
        )

        if not rename_events:
            return rename_groups

        current_group = [rename_events[0]]

        for i in range(1, len(rename_events)):
            prev_event = rename_events[i - 1]
            curr_event = rename_events[i]

            # Check if same directory and within time window
            time_diff = (curr_event.timestamp - prev_event.timestamp).total_seconds()

            if (curr_event.path.parent == prev_event.path.parent and
                time_diff <= self.RENAME_SEQUENCE_WINDOW):
                current_group.append(curr_event)
            else:
                if len(current_group) > 1:
                    rename_groups.append(current_group)
                current_group = [curr_event]

        # Add last group if it has multiple events
        if len(current_group) > 1:
            rename_groups.append(current_group)

        logger.debug(f"Found {len(rename_groups)} rename sequences")
        return rename_groups

    def group_directory_operations(self, events: List[FSEvent]) -> List[List[FSEvent]]:
        """
        Group operations on same directory.

        Args:
            events: List of FSEvent objects

        Returns:
            List of event groups
        """
        # Group by directory
        dir_events = defaultdict(list)

        for event in events:
            dir_events[event.path.parent].append(event)

        # Filter and group directories with multiple operations
        dir_groups = []

        for directory, dir_event_list in dir_events.items():
            if len(dir_event_list) < 2:
                continue

            # Sort by timestamp
            sorted_events = sorted(dir_event_list, key=lambda x: x.timestamp)

            # Group events within time window
            current_group = [sorted_events[0]]

            for i in range(1, len(sorted_events)):
                prev_event = sorted_events[i - 1]
                curr_event = sorted_events[i]

                time_diff = (curr_event.timestamp - prev_event.timestamp).total_seconds()

                if time_diff <= self.DIRECTORY_OPERATION_WINDOW:
                    current_group.append(curr_event)
                else:
                    if len(current_group) >= 3:  # At least 3 operations
                        dir_groups.append(current_group)
                    current_group = [curr_event]

            # Add last group
            if len(current_group) >= 3:
                dir_groups.append(current_group)

        logger.debug(f"Found {len(dir_groups)} directory operation groups")
        return dir_groups

    def group_file_modifications(self, events: List[FSEvent]) -> List[List[FSEvent]]:
        """
        Group multiple modifications to same file.

        Args:
            events: List of FSEvent objects

        Returns:
            List of event groups
        """
        # Group by file path
        file_events = defaultdict(list)

        for event in events:
            if event.is_modified:
                file_events[event.path].append(event)

        # Filter files with multiple modifications
        mod_groups = []

        for file_path, file_event_list in file_events.items():
            if len(file_event_list) < 2:
                continue

            # Sort by timestamp
            sorted_events = sorted(file_event_list, key=lambda x: x.timestamp)

            # Check if modifications are within time window
            time_span = (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds()

            if time_span <= self.FILE_MODIFICATION_WINDOW:
                mod_groups.append(sorted_events)

        logger.debug(f"Found {len(mod_groups)} file modification groups")
        return mod_groups

    def group_by_path(self, events: List[FSEvent]) -> Dict[Path, List[FSEvent]]:
        """
        Group events by file path.

        Args:
            events: List of FSEvent objects

        Returns:
            Dictionary mapping paths to event lists
        """
        path_groups = defaultdict(list)

        for event in events:
            path_groups[event.path].append(event)

        # Sort events within each group by timestamp
        for path in path_groups:
            path_groups[path].sort(key=lambda x: x.timestamp)

        logger.debug(f"Grouped events into {len(path_groups)} unique paths")
        return dict(path_groups)

    def find_related_events(
        self,
        event: FSEvent,
        all_events: List[FSEvent],
        time_window: int = 60
    ) -> List[FSEvent]:
        """
        Find events related to a specific event.

        Args:
            event: Target FSEvent
            all_events: List of all FSEvent objects
            time_window: Time window in seconds

        Returns:
            List of related events
        """
        related = []

        for other_event in all_events:
            if other_event == event:
                continue

            # Check if same directory
            if other_event.path.parent != event.path.parent:
                continue

            # Check if within time window
            time_diff = abs((other_event.timestamp - event.timestamp).total_seconds())
            if time_diff <= time_window:
                related.append(other_event)

        logger.debug(f"Found {len(related)} related events for {event.path.name}")
        return related

    def detect_multi_step_operations(self, events: List[FSEvent]) -> List[Dict]:
        """
        Detect multi-step operations (create → modify → move).

        Args:
            events: List of FSEvent objects

        Returns:
            List of multi-step operation dictionaries
        """
        operations = []

        # Group by path
        path_events = self.group_by_path(events)

        for path, event_list in path_events.items():
            if len(event_list) < 2:
                continue

            # Sort by timestamp
            sorted_events = event_list

            # Analyze sequence
            sequence = []
            for event in sorted_events:
                if event.is_created:
                    sequence.append('CREATE')
                elif event.is_modified:
                    sequence.append('MODIFY')
                elif event.is_renamed:
                    sequence.append('RENAME')
                elif event.is_removed:
                    sequence.append('DELETE')

            # Detect common patterns
            sequence_str = '->'.join(sequence)

            if len(sequence) >= 2:
                operation = {
                    'path': path,
                    'sequence': sequence_str,
                    'events': sorted_events,
                    'start_time': sorted_events[0].timestamp,
                    'end_time': sorted_events[-1].timestamp,
                    'duration': (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds()
                }
                operations.append(operation)

        logger.debug(f"Detected {len(operations)} multi-step operations")
        return operations

    def calculate_correlation_statistics(
        self,
        correlations: Dict[str, List[List[FSEvent]]]
    ) -> Dict:
        """
        Calculate statistics about correlations.

        Args:
            correlations: Correlation groups from correlate_events()

        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_groups': 0,
            'by_type': {},
            'largest_group_size': 0,
            'average_group_size': 0
        }

        all_group_sizes = []

        for corr_type, groups in correlations.items():
            if isinstance(groups, list):
                stats['by_type'][corr_type] = len(groups)
                stats['total_groups'] += len(groups)

                for group in groups:
                    if isinstance(group, list):
                        group_size = len(group)
                        all_group_sizes.append(group_size)
                        stats['largest_group_size'] = max(stats['largest_group_size'], group_size)
            elif isinstance(groups, dict):
                stats['by_type'][corr_type] = len(groups)

        if all_group_sizes:
            stats['average_group_size'] = round(sum(all_group_sizes) / len(all_group_sizes), 2)

        return stats
