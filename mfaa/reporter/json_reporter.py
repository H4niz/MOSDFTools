"""
JSON Reporter
=============

Generate JSON reports from timeline data.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from mfaa.reporter.base_reporter import BaseReporter
from mfaa.models import Timeline, TimelineEntry, FSEvent, Pattern, XattrRecord
from mfaa.utils.logger import setup_logger

logger = setup_logger(__name__)


class JSONReporter(BaseReporter):
    """Generate structured JSON reports for automation and API integration."""

    def __init__(self, include_metadata: bool = True):
        """
        Initialize JSONReporter.

        Args:
            include_metadata: Include generation metadata
        """
        super().__init__(include_metadata)

    def generate(
        self,
        timeline: Timeline,
        output_path: Path,
        pretty: bool = True,
        compact_events: bool = False
    ) -> None:
        """
        Generate JSON report.

        Args:
            timeline: Timeline object
            output_path: Path to save JSON file
            pretty: Pretty-print JSON with indentation
            compact_events: Exclude verbose event details
        """
        logger.info(f"Generating JSON report: {output_path}")

        self._validate_timeline(timeline)
        self._ensure_output_directory(output_path)

        # Build JSON structure
        report_data = self._build_report_structure(timeline, compact_events)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(report_data, f, ensure_ascii=False)

        logger.info(f"JSON report generated successfully: {output_path}")

    def _build_report_structure(
        self,
        timeline: Timeline,
        compact_events: bool
    ) -> Dict[str, Any]:
        """
        Build complete JSON report structure.

        Args:
            timeline: Timeline object
            compact_events: Compact event representation

        Returns:
            Dictionary representing full report
        """
        report = {}

        # Metadata
        if self.include_metadata:
            report['metadata'] = self._prepare_metadata(timeline)

        # Summary
        report['summary'] = self._build_summary(timeline)

        # Events
        report['events'] = [
            self._serialize_entry(entry, compact_events)
            for entry in timeline.entries
        ]

        # Patterns
        if timeline.patterns:
            report['patterns'] = [
                self._serialize_pattern(pattern)
                for pattern in timeline.patterns
            ]

        # Statistics
        if timeline.statistics:
            report['statistics'] = timeline.statistics

        return report

    def _build_summary(self, timeline: Timeline) -> Dict[str, Any]:
        """
        Build summary section.

        Args:
            timeline: Timeline object

        Returns:
            Summary dictionary
        """
        entries = timeline.entries

        if not entries:
            return {
                'total_events': 0,
                'time_range': None
            }

        timestamps = [e.event.timestamp for e in entries]
        earliest = min(timestamps)
        latest = max(timestamps)

        # Count by priority
        priority_counts = {}
        for entry in entries:
            cat = entry.priority_category
            priority_counts[cat] = priority_counts.get(cat, 0) + 1

        # Count quarantined and downloaded files
        quarantined = sum(1 for e in entries if e.xattr and e.xattr.has_quarantine)
        downloaded = sum(1 for e in entries if e.xattr and e.xattr.is_downloaded)

        return {
            'total_events': len(entries),
            'time_range': {
                'earliest': earliest.isoformat(),
                'latest': latest.isoformat(),
                'duration_hours': (latest - earliest).total_seconds() / 3600
            },
            'priority_distribution': priority_counts,
            'patterns_detected': len(timeline.patterns),
            'quarantined_files': quarantined,
            'downloaded_files': downloaded
        }

    def _serialize_entry(
        self,
        entry: TimelineEntry,
        compact: bool
    ) -> Dict[str, Any]:
        """
        Serialize TimelineEntry to dictionary.

        Args:
            entry: TimelineEntry object
            compact: Use compact representation

        Returns:
            Dictionary representation
        """
        event = entry.event

        if compact:
            return {
                'event_id': event.event_id,
                'timestamp': event.timestamp.isoformat(),
                'path': str(event.path),
                'event_types': [et.value for et in event.event_types],
                'priority_score': entry.priority_score,
                'priority_category': entry.priority_category
            }

        data = {
            'event': self._serialize_event(event),
            'priority_score': entry.priority_score,
            'priority_category': entry.priority_category
        }

        # Add xattr if present
        if entry.xattr:
            data['xattr'] = self._serialize_xattr(entry.xattr)

        # Add related events if present
        if entry.related_events:
            data['related_event_ids'] = [e.event_id for e in entry.related_events]

        # Add notes if present
        if entry.notes:
            data['notes'] = entry.notes

        return data

    def _serialize_event(self, event: FSEvent) -> Dict[str, Any]:
        """
        Serialize FSEvent to dictionary.

        Args:
            event: FSEvent object

        Returns:
            Dictionary representation
        """
        return {
            'event_id': event.event_id,
            'timestamp': event.timestamp.isoformat(),
            'path': str(event.path),
            'event_types': [et.value for et in event.event_types],
            'flags': {
                'value': event.flags.value,
                'hex': hex(event.flags.value)
            },
            'node_id': event.node_id
        }

    def _serialize_xattr(self, xattr: XattrRecord) -> Dict[str, Any]:
        """
        Serialize XattrRecord to dictionary.

        Args:
            xattr: XattrRecord object

        Returns:
            Dictionary representation
        """
        data = {
            'file_path': str(xattr.file_path),
            'has_quarantine': xattr.has_quarantine,
            'is_downloaded': xattr.is_downloaded
        }

        if xattr.quarantine_info:
            data['quarantine'] = {
                'flags': xattr.quarantine_info.flags,
                'timestamp': xattr.quarantine_info.timestamp.isoformat(),
                'source_app': xattr.quarantine_info.source_app,
                'uuid': xattr.quarantine_info.uuid
            }

        if xattr.download_urls:
            data['download_urls'] = xattr.download_urls

        if xattr.download_timestamp:
            data['download_timestamp'] = xattr.download_timestamp.isoformat()

        if xattr.last_used_date:
            data['last_used_date'] = xattr.last_used_date.isoformat()

        return data

    def _serialize_pattern(self, pattern: Pattern) -> Dict[str, Any]:
        """
        Serialize Pattern to dictionary.

        Args:
            pattern: Pattern object

        Returns:
            Dictionary representation
        """
        return {
            'pattern_type': pattern.pattern_type,
            'severity': pattern.severity,
            'time_range': {
                'start': pattern.start_time.isoformat(),
                'end': pattern.end_time.isoformat(),
                'duration_seconds': (pattern.end_time - pattern.start_time).total_seconds()
            },
            'event_count': pattern.event_count,
            'affected_paths': [str(p) for p in pattern.affected_paths],
            'description': pattern.description,
            'indicators': pattern.indicators
        }

    def generate_compact(
        self,
        timeline: Timeline,
        output_path: Path
    ) -> None:
        """
        Generate compact JSON report (smaller file size).

        Args:
            timeline: Timeline object
            output_path: Output JSON path
        """
        self.generate(timeline, output_path, pretty=False, compact_events=True)

    def generate_events_only(
        self,
        timeline: Timeline,
        output_path: Path
    ) -> None:
        """
        Generate JSON with events only (no patterns or statistics).

        Args:
            timeline: Timeline object
            output_path: Output JSON path
        """
        logger.info(f"Generating events-only JSON: {output_path}")

        self._validate_timeline(timeline)
        self._ensure_output_directory(output_path)

        events_data = {
            'events': [
                self._serialize_entry(entry, compact=False)
                for entry in timeline.entries
            ]
        }

        if self.include_metadata:
            events_data['metadata'] = self._prepare_metadata(timeline)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(events_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Events-only JSON generated: {len(timeline.entries)} events")

    def generate_patterns_only(
        self,
        timeline: Timeline,
        output_path: Path
    ) -> None:
        """
        Generate JSON with patterns only.

        Args:
            timeline: Timeline object
            output_path: Output JSON path
        """
        logger.info(f"Generating patterns-only JSON: {output_path}")

        patterns_data = {
            'patterns': [
                self._serialize_pattern(pattern)
                for pattern in timeline.patterns
            ],
            'summary': {
                'total_patterns': len(timeline.patterns),
                'by_severity': {}
            }
        }

        # Count by severity
        for pattern in timeline.patterns:
            sev = pattern.severity
            patterns_data['summary']['by_severity'][sev] = \
                patterns_data['summary']['by_severity'].get(sev, 0) + 1

        if self.include_metadata:
            patterns_data['metadata'] = self._prepare_metadata(timeline)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(patterns_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Patterns-only JSON generated: {len(timeline.patterns)} patterns")
