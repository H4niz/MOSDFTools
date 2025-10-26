"""
CSV Reporter
============

Generate CSV reports from timeline data.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any
from mfaa.reporter.base_reporter import BaseReporter
from mfaa.models import Timeline, TimelineEntry
from mfaa.utils.logger import setup_logger

logger = setup_logger(__name__)


class CSVReporter(BaseReporter):
    """Generate CSV reports compatible with Excel, Splunk, etc."""

    def __init__(self, include_metadata: bool = True, delimiter: str = ','):
        """
        Initialize CSVReporter.

        Args:
            include_metadata: Include metadata in separate CSV
            delimiter: CSV delimiter character (default: ',')
        """
        super().__init__(include_metadata)
        self.delimiter = delimiter

    def generate(
        self,
        timeline: Timeline,
        output_path: Path,
        include_patterns: bool = True,
        include_statistics: bool = True
    ) -> None:
        """
        Generate CSV report.

        Args:
            timeline: Timeline object
            output_path: Path to save CSV file
            include_patterns: Include patterns in separate CSV
            include_statistics: Include statistics in separate CSV
        """
        logger.info(f"Generating CSV report: {output_path}")

        self._validate_timeline(timeline)
        self._ensure_output_directory(output_path)

        # Generate main events CSV
        self._write_events_csv(timeline, output_path)

        # Generate patterns CSV if requested
        if include_patterns and timeline.patterns:
            patterns_path = output_path.with_name(
                output_path.stem + '_patterns' + output_path.suffix
            )
            self._write_patterns_csv(timeline, patterns_path)

        # Generate statistics CSV if requested
        if include_statistics and timeline.statistics:
            stats_path = output_path.with_name(
                output_path.stem + '_statistics' + output_path.suffix
            )
            self._write_statistics_csv(timeline, stats_path)

        logger.info(f"CSV report generated successfully: {output_path}")

    def _write_events_csv(self, timeline: Timeline, output_path: Path) -> None:
        """
        Write events to CSV file.

        Args:
            timeline: Timeline object
            output_path: Output CSV path
        """
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=self.delimiter)

            # Write header
            header = [
                'event_id',
                'timestamp',
                'path',
                'event_types',
                'flags',
                'node_id',
                'priority_score',
                'priority_category',
                'has_quarantine',
                'is_downloaded',
                'download_url',
                'quarantine_source',
                'notes'
            ]
            writer.writerow(header)

            # Write entries
            for entry in timeline.entries:
                row = self._entry_to_row(entry)
                writer.writerow(row)

        logger.debug(f"Wrote {len(timeline.entries)} events to {output_path}")

    def _entry_to_row(self, entry: TimelineEntry) -> List[str]:
        """
        Convert TimelineEntry to CSV row.

        Args:
            entry: TimelineEntry object

        Returns:
            List of cell values
        """
        event = entry.event

        # Event types as comma-separated string
        event_types_str = '|'.join(et.value for et in event.event_types)

        # Xattr information
        has_quarantine = 'Yes' if entry.xattr and entry.xattr.has_quarantine else 'No'
        is_downloaded = 'Yes' if entry.xattr and entry.xattr.is_downloaded else 'No'

        download_url = ''
        quarantine_source = ''
        if entry.xattr:
            if entry.xattr.download_urls:
                download_url = entry.xattr.download_urls[0]
            if entry.xattr.quarantine_info:
                quarantine_source = entry.xattr.quarantine_info.source_app

        # Notes as semicolon-separated string
        notes_str = '; '.join(entry.notes) if entry.notes else ''

        return [
            str(event.event_id),
            event.timestamp.isoformat(),
            str(event.path),
            event_types_str,
            hex(event.flags.value),
            str(event.node_id),
            str(entry.priority_score),
            entry.priority_category,
            has_quarantine,
            is_downloaded,
            download_url,
            quarantine_source,
            notes_str
        ]

    def _write_patterns_csv(self, timeline: Timeline, output_path: Path) -> None:
        """
        Write detected patterns to CSV.

        Args:
            timeline: Timeline object
            output_path: Output CSV path
        """
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=self.delimiter)

            # Write header
            header = [
                'pattern_type',
                'severity',
                'start_time',
                'end_time',
                'duration_seconds',
                'event_count',
                'affected_paths_count',
                'description'
            ]
            writer.writerow(header)

            # Write patterns
            for pattern in timeline.patterns:
                duration = (pattern.end_time - pattern.start_time).total_seconds()

                row = [
                    pattern.pattern_type,
                    pattern.severity,
                    pattern.start_time.isoformat(),
                    pattern.end_time.isoformat(),
                    str(duration),
                    str(pattern.event_count),
                    str(len(pattern.affected_paths)),
                    pattern.description
                ]
                writer.writerow(row)

        logger.debug(f"Wrote {len(timeline.patterns)} patterns to {output_path}")

    def _write_statistics_csv(self, timeline: Timeline, output_path: Path) -> None:
        """
        Write statistics to CSV.

        Args:
            timeline: Timeline object
            output_path: Output CSV path
        """
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=self.delimiter)

            # Write header
            writer.writerow(['statistic', 'value'])

            # Flatten statistics dictionary
            flat_stats = self._flatten_statistics(timeline.statistics)

            for key, value in flat_stats.items():
                writer.writerow([key, str(value)])

        logger.debug(f"Wrote statistics to {output_path}")

    def _flatten_statistics(
        self,
        stats: Dict[str, Any],
        prefix: str = ''
    ) -> Dict[str, Any]:
        """
        Flatten nested statistics dictionary.

        Args:
            stats: Statistics dictionary
            prefix: Key prefix for nested values

        Returns:
            Flattened dictionary
        """
        flat = {}

        for key, value in stats.items():
            full_key = f"{prefix}{key}" if prefix else key

            if isinstance(value, dict):
                # Recursively flatten nested dicts
                nested = self._flatten_statistics(value, f"{full_key}.")
                flat.update(nested)
            elif isinstance(value, (list, tuple)):
                # Convert lists to comma-separated strings
                flat[full_key] = ', '.join(str(v) for v in value)
            else:
                flat[full_key] = value

        return flat

    def generate_summary_csv(
        self,
        timeline: Timeline,
        output_path: Path,
        min_priority: int = 70
    ) -> None:
        """
        Generate summary CSV with only high-priority events.

        Args:
            timeline: Timeline object
            output_path: Output CSV path
            min_priority: Minimum priority score to include
        """
        logger.info(f"Generating summary CSV (min priority: {min_priority})")

        # Filter high-priority entries
        filtered_entries = [
            e for e in timeline.entries
            if e.priority_score >= min_priority
        ]

        # Create temporary timeline with filtered entries
        summary_timeline = Timeline(
            entries=filtered_entries,
            patterns=timeline.patterns,
            statistics=timeline.statistics,
            info={**timeline.info, 'summary_filter': f'priority>={min_priority}'}
        )

        # Generate CSV
        self.generate(summary_timeline, output_path, include_patterns=True)

        logger.info(f"Summary CSV generated: {len(filtered_entries)} entries")
