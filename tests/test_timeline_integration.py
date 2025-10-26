"""
Integration Tests for Timeline Module
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from mfaa.timeline.generator import TimelineGenerator
from mfaa.timeline.grouper import TimelineGrouper
from mfaa.analyzer.priority_scorer import PriorityScorer
from mfaa.analyzer.pattern_detector import PatternDetector
from mfaa.models import FSEvent, EventFlags, XattrRecord, QuarantineInfo


@pytest.fixture
def realistic_events():
    """Create realistic event sequence simulating file operations."""
    base_time = datetime(2024, 1, 15, 14, 30, 0)
    events = []

    # Download a suspicious file
    events.append(FSEvent(
        event_id=1,
        timestamp=base_time,
        path=Path("/Users/test/Downloads/malware.exe"),
        flags=EventFlags(EventFlags.ITEM_CREATED | EventFlags.ITEM_IS_FILE),
        node_id=10001
    ))

    # Modify executable permissions
    events.append(FSEvent(
        event_id=2,
        timestamp=base_time + timedelta(seconds=5),
        path=Path("/Users/test/Downloads/malware.exe"),
        flags=EventFlags(EventFlags.ITEM_CHANGE_OWNER | EventFlags.ITEM_IS_FILE),
        node_id=10001
    ))

    # Execute and create persistence
    events.append(FSEvent(
        event_id=3,
        timestamp=base_time + timedelta(seconds=30),
        path=Path("/Users/test/Library/LaunchAgents/malware.plist"),
        flags=EventFlags(EventFlags.ITEM_CREATED | EventFlags.ITEM_IS_FILE),
        node_id=10002
    ))

    # Mass file deletion (ransomware simulation)
    for i in range(50):
        events.append(FSEvent(
            event_id=100 + i,
            timestamp=base_time + timedelta(minutes=5, seconds=i),
            path=Path(f"/Users/test/Documents/file_{i}.txt"),
            flags=EventFlags(EventFlags.ITEM_REMOVED | EventFlags.ITEM_IS_FILE),
            node_id=20000 + i
        ))

    # Create encrypted versions
    for i in range(50):
        events.append(FSEvent(
            event_id=200 + i,
            timestamp=base_time + timedelta(minutes=6, seconds=i),
            path=Path(f"/Users/test/Documents/file_{i}.txt.encrypted"),
            flags=EventFlags(EventFlags.ITEM_CREATED | EventFlags.ITEM_IS_FILE),
            node_id=30000 + i
        ))

    # Create ransom note
    events.append(FSEvent(
        event_id=300,
        timestamp=base_time + timedelta(minutes=7),
        path=Path("/Users/test/Documents/README_RANSOM.txt"),
        flags=EventFlags(EventFlags.ITEM_CREATED | EventFlags.ITEM_IS_FILE),
        node_id=40001
    ))

    return events


@pytest.fixture
def realistic_xattr():
    """Create realistic xattr records."""
    quarantine = QuarantineInfo(
        flags='0001',
        timestamp=datetime(2024, 1, 15, 14, 30, 0),
        source_app='com.apple.Safari',
        uuid='ABC-123-DEF'
    )

    return {
        Path("/Users/test/Downloads/malware.exe"): XattrRecord(
            file_path=Path("/Users/test/Downloads/malware.exe"),
            attributes={'com.apple.quarantine': b'0001'},
            quarantine_info=quarantine,
            download_urls=['http://malicious-site.com/malware.exe']
        )
    }


class TestEndToEndTimeline:
    """Test complete timeline generation workflow."""

    def test_full_timeline_workflow(self, realistic_events, realistic_xattr):
        """Test complete timeline generation with all features."""
        generator = TimelineGenerator()

        # Generate full timeline
        timeline = generator.generate_timeline(
            realistic_events,
            realistic_xattr,
            detect_patterns=True
        )

        # Verify timeline structure
        assert timeline is not None
        assert len(timeline.entries) == len(realistic_events)
        assert len(timeline.patterns) > 0  # Should detect ransomware pattern

        # Verify patterns detected
        pattern_types = [p.pattern_type for p in timeline.patterns]
        assert 'mass_deletion' in pattern_types or 'ransomware_encryption' in pattern_types

        # Verify statistics
        assert timeline.statistics['total_entries'] == len(realistic_events)
        assert 'priority_distribution' in timeline.statistics
        assert 'patterns_detected' in timeline.statistics

    def test_timeline_with_grouping(self, realistic_events, realistic_xattr):
        """Test timeline generation followed by grouping."""
        generator = TimelineGenerator()
        grouper = TimelineGrouper()

        # Generate timeline
        timeline = generator.generate_timeline(realistic_events, realistic_xattr)

        # Apply various groupings
        by_priority = grouper.group_by_priority(timeline.entries)
        by_operation = grouper.group_file_operations(timeline.entries)
        by_extension = grouper.group_by_file_extension(timeline.entries)

        # Verify groupings
        assert 'CRITICAL' in by_priority or 'HIGH' in by_priority
        assert 'created' in by_operation
        assert 'deleted' in by_operation
        assert '.exe' in by_extension
        assert '.encrypted' in by_extension

    def test_suspicious_activity_detection(self, realistic_events, realistic_xattr):
        """Test detection and grouping of suspicious activities."""
        generator = TimelineGenerator()
        grouper = TimelineGrouper()

        # Generate timeline
        timeline = generator.generate_timeline(realistic_events, realistic_xattr)

        # Get high-priority entries
        high_priority = grouper.group_by_priority(timeline.entries)

        # Group suspicious activities
        suspicious = grouper.group_suspicious_activity(timeline.entries, min_priority=70)

        # Should detect quarantined downloads
        assert len(suspicious['quarantined_downloads']) > 0

        # Should detect persistence mechanisms
        persistence_paths = [e.event.path for e in timeline.entries
                           if 'LaunchAgents' in str(e.event.path)]
        assert len(persistence_paths) > 0


class TestTimelineFiltering:
    """Test timeline filtering and focused views."""

    def test_focused_timeline_on_suspicious_file(self, realistic_events, realistic_xattr):
        """Test focused timeline around suspicious file."""
        generator = TimelineGenerator()

        focus_path = Path("/Users/test/Downloads/malware.exe")
        timeline = generator.generate_focused_timeline(
            realistic_events,
            focus_path,
            window_minutes=1
        )

        # Should include creation and permission change
        assert len(timeline.entries) >= 2

        # Verify focus info
        assert timeline.info['focus_path'] == str(focus_path)
        assert timeline.info['window_minutes'] == 1

    def test_summary_timeline_high_priority_only(self, realistic_events, realistic_xattr):
        """Test summary timeline with high-priority events."""
        generator = TimelineGenerator()

        timeline = generator.generate_summary_timeline(
            realistic_events,
            min_priority=75,
            xattr_records=realistic_xattr
        )

        # All entries should be high priority
        assert all(e.priority_score >= 75 for e in timeline.entries)

        # Should still include patterns from full analysis
        assert len(timeline.patterns) > 0

    def test_daily_timeline_specific_day(self, realistic_events, realistic_xattr):
        """Test daily timeline for specific date."""
        generator = TimelineGenerator()

        target_date = datetime(2024, 1, 15)
        timeline = generator.generate_daily_timeline(
            realistic_events,
            target_date,
            realistic_xattr
        )

        # All events should be on target day
        for entry in timeline.entries:
            assert entry.event.timestamp.date() == target_date.date()


class TestTimelineGroupingIntegration:
    """Test integration of different grouping methods."""

    def test_hierarchical_grouping(self, realistic_events, realistic_xattr):
        """Test combining multiple grouping methods."""
        generator = TimelineGenerator()
        grouper = TimelineGrouper()

        # Generate timeline
        timeline = generator.generate_timeline(realistic_events, realistic_xattr)

        # First group by priority
        by_priority = grouper.group_by_priority(timeline.entries)

        # Then group high-priority events by directory
        if 'HIGH' in by_priority:
            high_priority_by_dir = grouper.group_by_directory(by_priority['HIGH'])
            assert len(high_priority_by_dir) > 0

        # Then group by time windows
        if 'CRITICAL' in by_priority:
            critical_by_time = grouper.group_by_time_window(
                by_priority['CRITICAL'],
                window_size_minutes=5
            )
            assert len(critical_by_time) > 0

    def test_related_events_with_operations(self, realistic_events, realistic_xattr):
        """Test grouping related events and analyzing operations."""
        generator = TimelineGenerator()
        grouper = TimelineGrouper()

        # Generate timeline
        timeline = generator.generate_timeline(realistic_events, realistic_xattr)

        # Group related events
        related_groups = grouper.group_related_events(timeline.entries)

        # Analyze operations within each related group
        for group in related_groups:
            operations = grouper.group_file_operations(group)

            # Each group should have coherent operations
            assert len(operations) > 0


class TestTimelineAnalystWorkflow:
    """Test realistic analyst workflow."""

    def test_analyst_investigation_workflow(self, realistic_events, realistic_xattr):
        """Simulate analyst investigating suspicious activity."""
        generator = TimelineGenerator()
        grouper = TimelineGrouper()

        # Step 1: Generate full timeline with pattern detection
        timeline = generator.generate_timeline(
            realistic_events,
            realistic_xattr,
            detect_patterns=True
        )

        # Step 2: Review detected patterns
        assert len(timeline.patterns) > 0
        most_severe = max(timeline.patterns, key=lambda p: p.event_count)

        # Step 3: Focus on time range of most severe pattern
        focused_entries = generator.get_entries_in_range(
            timeline,
            most_severe.start_time,
            most_severe.end_time
        )
        assert len(focused_entries) > 0

        # Step 4: Group affected files by directory
        affected_by_dir = grouper.group_by_directory(focused_entries)
        assert len(affected_by_dir) > 0

        # Step 5: Add analyst notes to key events
        if focused_entries:
            first_event_id = focused_entries[0].event.event_id
            result = generator.add_notes_to_entry(
                timeline,
                first_event_id,
                "Potential ransomware - initial file deletion"
            )
            assert result is True

        # Step 6: Create summary report of high-priority events
        summary = generator.generate_summary_timeline(
            realistic_events,
            min_priority=70,
            xattr_records=realistic_xattr
        )

        assert summary.info['summary_min_priority'] == 70
        assert len(summary.entries) < len(timeline.entries)

    def test_temporal_analysis_workflow(self, realistic_events, realistic_xattr):
        """Test temporal analysis of events."""
        generator = TimelineGenerator()
        grouper = TimelineGrouper()

        # Generate timeline
        timeline = generator.generate_timeline(realistic_events, realistic_xattr)

        # Create hourly groups to see activity patterns
        hourly = grouper.create_hourly_groups(timeline.entries)

        # Find hours with most activity
        busiest_hour = max(hourly.items(), key=lambda x: len(x[1]))
        hour_label, hour_entries = busiest_hour

        # Analyze operations during busiest hour
        operations = grouper.group_file_operations(hour_entries)

        # Should see high deletion activity (ransomware simulation)
        assert len(operations['deleted']) > 0

    def test_file_lifecycle_tracking(self, realistic_events, realistic_xattr):
        """Test tracking complete lifecycle of a file."""
        generator = TimelineGenerator()
        grouper = TimelineGrouper()

        # Generate timeline
        timeline = generator.generate_timeline(realistic_events, realistic_xattr)

        # Track malware.exe lifecycle
        malware_path = Path("/Users/test/Downloads/malware.exe")
        malware_entries = generator.get_entries_for_path(timeline, malware_path)

        # Group operations on this file
        operations = grouper.group_file_operations(malware_entries)

        # Should have creation and permission change
        assert len(operations['created']) > 0
        assert len(operations['permission_changed']) > 0

        # Verify chronological order
        timestamps = [e.event.timestamp for e in malware_entries]
        assert timestamps == sorted(timestamps)


class TestPerformanceAndScaling:
    """Test timeline performance with larger datasets."""

    def test_large_dataset_timeline(self):
        """Test timeline generation with large event set."""
        # Generate 1000 events
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        events = []

        for i in range(1000):
            events.append(FSEvent(
                event_id=i,
                timestamp=base_time + timedelta(seconds=i),
                path=Path(f"/Users/test/file_{i % 100}.txt"),
                flags=EventFlags(EventFlags.ITEM_MODIFIED | EventFlags.ITEM_IS_FILE),
                node_id=10000 + i
            ))

        generator = TimelineGenerator()

        # Should handle large dataset
        timeline = generator.generate_timeline(events, detect_patterns=False)

        assert len(timeline.entries) == 1000
        assert timeline.statistics['total_entries'] == 1000

    def test_grouping_performance(self):
        """Test grouping performance with many entries."""
        # Generate 500 events
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        events = []

        for i in range(500):
            events.append(FSEvent(
                event_id=i,
                timestamp=base_time + timedelta(minutes=i),
                path=Path(f"/Users/test/dir_{i % 10}/file_{i}.txt"),
                flags=EventFlags(EventFlags.ITEM_CREATED | EventFlags.ITEM_IS_FILE),
                node_id=10000 + i
            ))

        generator = TimelineGenerator()
        grouper = TimelineGrouper()

        timeline = generator.generate_timeline(events)

        # Apply multiple groupings
        by_dir = grouper.group_by_directory(timeline.entries)
        by_time = grouper.group_by_time_window(timeline.entries, window_size_minutes=60)
        by_ext = grouper.group_by_file_extension(timeline.entries)

        # Verify all groupings completed
        assert len(by_dir) > 0
        assert len(by_time) > 0
        assert len(by_ext) > 0
