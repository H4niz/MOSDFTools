"""
Timeline Generator
==================

Generate chronological timelines from FSEvents.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
from mfaa.models import FSEvent, XattrRecord, TimelineEntry, Timeline, Pattern
from mfaa.analyzer.priority_scorer import PriorityScorer
from mfaa.analyzer.pattern_detector import PatternDetector
from mfaa.utils.logger import setup_logger

logger = setup_logger(__name__)


class TimelineGenerator:
    """Generate forensic timelines from FSEvents."""

    def __init__(
        self,
        scorer: Optional[PriorityScorer] = None,
        detector: Optional[PatternDetector] = None
    ):
        """
        Initialize TimelineGenerator.

        Args:
            scorer: PriorityScorer instance for calculating event priority
            detector: PatternDetector instance for identifying patterns
        """
        self.scorer = scorer or PriorityScorer()
        self.detector = detector or PatternDetector()
        logger.debug("TimelineGenerator initialized")

    def generate_timeline(
        self,
        events: List[FSEvent],
        xattr_records: Optional[Dict[Path, XattrRecord]] = None,
        detect_patterns: bool = True
    ) -> Timeline:
        """
        Generate complete timeline from events.

        Args:
            events: List of FSEvent objects
            xattr_records: Optional dictionary mapping file paths to XattrRecords
            detect_patterns: Whether to run pattern detection

        Returns:
            Timeline object with sorted entries and patterns
        """
        if not events:
            logger.warning("No events provided to generate timeline")
            return Timeline(
                entries=[],
                patterns=[],
                statistics={},
                info={'generated_at': datetime.now().isoformat()}
            )

        logger.info(f"Generating timeline from {len(events)} events")

        # Create timeline entries with priority scores
        entries = []
        xattr_records = xattr_records or {}

        for event in events:
            xattr = xattr_records.get(event.path)

            # Calculate priority score
            score = self.scorer.calculate_score(event, xattr)
            category = self.scorer.categorize_score(score)

            entry = TimelineEntry(
                event=event,
                priority_score=score,
                priority_category=category,
                xattr=xattr
            )
            entries.append(entry)

        # Sort chronologically
        entries.sort(key=lambda e: e.event.timestamp)

        # Detect patterns
        patterns = []
        if detect_patterns:
            logger.debug("Running pattern detection")
            patterns = self.detector.detect_all_patterns(events)

        # Calculate statistics
        statistics = self._calculate_statistics(entries, patterns)

        # Create info dictionary
        info = self._create_timeline_info(events, entries)

        timeline = Timeline(
            entries=entries,
            patterns=patterns,
            statistics=statistics,
            info=info
        )

        logger.info(f"Timeline generated: {len(entries)} entries, {len(patterns)} patterns")
        return timeline

    def generate_focused_timeline(
        self,
        events: List[FSEvent],
        focus_path: Path,
        window_minutes: int = 60,
        xattr_records: Optional[Dict[Path, XattrRecord]] = None
    ) -> Timeline:
        """
        Generate timeline focused on events around a specific path.

        Args:
            events: List of all FSEvent objects
            focus_path: Path to focus on
            window_minutes: Time window in minutes (before and after)
            xattr_records: Optional dictionary mapping file paths to XattrRecords

        Returns:
            Timeline object with events around focus_path
        """
        logger.info(f"Generating focused timeline for: {focus_path}")

        # Find events for focus path
        focus_events = [e for e in events if e.path == focus_path]

        if not focus_events:
            logger.warning(f"No events found for path: {focus_path}")
            return Timeline(
                entries=[],
                patterns=[],
                statistics={},
                info={'focus_path': str(focus_path)}
            )

        # Get time window
        focus_times = [e.timestamp for e in focus_events]
        earliest = min(focus_times)
        latest = max(focus_times)

        window_delta = timedelta(minutes=window_minutes)
        start_time = earliest - window_delta
        end_time = latest + window_delta

        # Filter events in time window
        window_events = [
            e for e in events
            if start_time <= e.timestamp <= end_time
        ]

        logger.debug(f"Found {len(window_events)} events in {window_minutes}min window")

        # Generate timeline
        timeline = self.generate_timeline(window_events, xattr_records)

        # Add focus info
        timeline.info['focus_path'] = str(focus_path)
        timeline.info['window_minutes'] = window_minutes
        timeline.info['time_range'] = {
            'start': start_time.isoformat(),
            'end': end_time.isoformat()
        }

        return timeline

    def generate_daily_timeline(
        self,
        events: List[FSEvent],
        target_date: datetime,
        xattr_records: Optional[Dict[Path, XattrRecord]] = None
    ) -> Timeline:
        """
        Generate timeline for a specific day.

        Args:
            events: List of FSEvent objects
            target_date: Date to generate timeline for (time ignored)
            xattr_records: Optional dictionary mapping file paths to XattrRecords

        Returns:
            Timeline object for the specified day
        """
        logger.info(f"Generating daily timeline for: {target_date.date()}")

        # Define day boundaries
        start_of_day = datetime.combine(target_date.date(), datetime.min.time())
        end_of_day = datetime.combine(target_date.date(), datetime.max.time())

        # Filter events for this day
        daily_events = [
            e for e in events
            if start_of_day <= e.timestamp <= end_of_day
        ]

        logger.debug(f"Found {len(daily_events)} events on {target_date.date()}")

        # Generate timeline
        timeline = self.generate_timeline(daily_events, xattr_records)

        # Add day info
        timeline.info['target_date'] = target_date.date().isoformat()
        timeline.info['day_range'] = {
            'start': start_of_day.isoformat(),
            'end': end_of_day.isoformat()
        }

        return timeline

    def generate_summary_timeline(
        self,
        events: List[FSEvent],
        min_priority: int = 50,
        xattr_records: Optional[Dict[Path, XattrRecord]] = None
    ) -> Timeline:
        """
        Generate summary timeline with only high-priority events.

        Args:
            events: List of FSEvent objects
            min_priority: Minimum priority score (0-100)
            xattr_records: Optional dictionary mapping file paths to XattrRecords

        Returns:
            Timeline object with only high-priority entries
        """
        logger.info(f"Generating summary timeline (min priority: {min_priority})")

        # Generate full timeline
        full_timeline = self.generate_timeline(events, xattr_records, detect_patterns=True)

        # Filter by priority
        high_priority_entries = [
            e for e in full_timeline.entries
            if e.priority_score >= min_priority
        ]

        # Create summary timeline
        summary_timeline = Timeline(
            entries=high_priority_entries,
            patterns=full_timeline.patterns,
            statistics=self._calculate_statistics(high_priority_entries, full_timeline.patterns),
            info={
                **full_timeline.info,
                'summary_min_priority': min_priority,
                'filtered_from_total': len(full_timeline.entries)
            }
        )

        logger.info(f"Summary timeline: {len(high_priority_entries)}/{len(full_timeline.entries)} entries")
        return summary_timeline

    def _calculate_statistics(
        self,
        entries: List[TimelineEntry],
        patterns: List[Pattern]
    ) -> Dict[str, Any]:
        """
        Calculate timeline statistics.

        Args:
            entries: List of TimelineEntry objects
            patterns: List of detected Pattern objects

        Returns:
            Dictionary with statistics
        """
        if not entries:
            return {
                'total_entries': 0,
                'priority_distribution': {},
                'patterns_detected': 0
            }

        from collections import Counter

        # Priority distribution
        priority_counter = Counter(e.priority_category for e in entries)

        # Score statistics
        scores = [e.priority_score for e in entries]

        # Pattern severity
        pattern_severity = Counter(p.severity for p in patterns)

        # Time span
        timestamps = [e.event.timestamp for e in entries]
        time_span = None
        if timestamps:
            earliest = min(timestamps)
            latest = max(timestamps)
            time_span = {
                'earliest': earliest.isoformat(),
                'latest': latest.isoformat(),
                'duration_hours': (latest - earliest).total_seconds() / 3600
            }

        # Event types distribution
        event_types_counter = Counter()
        for entry in entries:
            for event_type in entry.event.event_types:
                event_types_counter[event_type.value] += 1

        # Xattr statistics
        entries_with_xattr = sum(1 for e in entries if e.xattr is not None)
        quarantined_count = sum(
            1 for e in entries
            if e.xattr and e.xattr.has_quarantine
        )

        return {
            'total_entries': len(entries),
            'priority_distribution': dict(priority_counter),
            'score_statistics': {
                'min': min(scores),
                'max': max(scores),
                'average': sum(scores) / len(scores)
            },
            'patterns_detected': len(patterns),
            'pattern_severity': dict(pattern_severity),
            'time_span': time_span,
            'event_types': dict(event_types_counter),
            'xattr_statistics': {
                'entries_with_xattr': entries_with_xattr,
                'quarantined_files': quarantined_count
            }
        }

    def _create_timeline_info(
        self,
        events: List[FSEvent],
        entries: List[TimelineEntry]
    ) -> Dict[str, Any]:
        """
        Create timeline info dictionary.

        Args:
            events: Original list of FSEvent objects
            entries: Generated list of TimelineEntry objects

        Returns:
            Dictionary with timeline info
        """
        return {
            'generated_at': datetime.now().isoformat(),
            'total_events': len(events),
            'total_entries': len(entries),
            'scorer_version': 'v1.0',
            'detector_version': 'v1.0'
        }

    def add_notes_to_entry(
        self,
        timeline: Timeline,
        event_id: int,
        note: str
    ) -> bool:
        """
        Add analyst note to a timeline entry.

        Args:
            timeline: Timeline object
            event_id: Event ID to add note to
            note: Note text to add

        Returns:
            True if note added, False if event not found
        """
        for entry in timeline.entries:
            if entry.event.event_id == event_id:
                entry.notes.append(note)
                logger.debug(f"Added note to event {event_id}")
                return True

        logger.warning(f"Event {event_id} not found in timeline")
        return False

    def get_entries_by_priority(
        self,
        timeline: Timeline,
        category: str
    ) -> List[TimelineEntry]:
        """
        Get all entries with specific priority category.

        Args:
            timeline: Timeline object
            category: Priority category ("CRITICAL", "HIGH", "MEDIUM", "LOW")

        Returns:
            List of matching TimelineEntry objects
        """
        return [e for e in timeline.entries if e.priority_category == category]

    def get_entries_in_range(
        self,
        timeline: Timeline,
        start_time: datetime,
        end_time: datetime
    ) -> List[TimelineEntry]:
        """
        Get entries within a time range.

        Args:
            timeline: Timeline object
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of TimelineEntry objects in range
        """
        return [
            e for e in timeline.entries
            if start_time <= e.event.timestamp <= end_time
        ]

    def get_entries_for_path(
        self,
        timeline: Timeline,
        path: Path,
        include_subdirectories: bool = False
    ) -> List[TimelineEntry]:
        """
        Get entries for a specific path.

        Args:
            timeline: Timeline object
            path: Path to filter by
            include_subdirectories: Include events in subdirectories

        Returns:
            List of TimelineEntry objects for path
        """
        if include_subdirectories:
            path_str = str(path)
            return [
                e for e in timeline.entries
                if str(e.event.path).startswith(path_str)
            ]
        else:
            return [
                e for e in timeline.entries
                if e.event.path == path
            ]
