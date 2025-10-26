"""
Tests for TimelineGrouper
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from mfaa.timeline.grouper import TimelineGrouper
from mfaa.models import FSEvent, EventFlags, EventType, TimelineEntry, XattrRecord, QuarantineInfo


@pytest.fixture
def sample_entries():
    """Create sample timeline entries."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)

    entries = [
        TimelineEntry(
            event=FSEvent(
                event_id=1,
                timestamp=base_time,
                path=Path("/Users/test/document.txt"),
                flags=EventFlags(EventFlags.ITEM_CREATED | EventFlags.ITEM_IS_FILE),
                node_id=1
            ),
            priority_score=60,
            priority_category="MEDIUM"
        ),
        TimelineEntry(
            event=FSEvent(
                event_id=2,
                timestamp=base_time + timedelta(minutes=5),
                path=Path("/Users/test/document.txt"),
                flags=EventFlags(EventFlags.ITEM_MODIFIED | EventFlags.ITEM_IS_FILE),
                node_id=1
            ),
            priority_score=50,
            priority_category="MEDIUM"
        ),
        TimelineEntry(
            event=FSEvent(
                event_id=3,
                timestamp=base_time + timedelta(minutes=10),
                path=Path("/Users/test/script.sh"),
                flags=EventFlags(EventFlags.ITEM_CREATED | EventFlags.ITEM_IS_FILE),
                node_id=2
            ),
            priority_score=80,
            priority_category="HIGH"
        ),
        TimelineEntry(
            event=FSEvent(
                event_id=4,
                timestamp=base_time + timedelta(hours=2),
                path=Path("/Users/test/other/file.pdf"),
                flags=EventFlags(EventFlags.ITEM_CREATED | EventFlags.ITEM_IS_FILE),
                node_id=3
            ),
            priority_score=40,
            priority_category="LOW"
        ),
        TimelineEntry(
            event=FSEvent(
                event_id=5,
                timestamp=base_time + timedelta(hours=3),
                path=Path("/Users/test/document.txt"),
                flags=EventFlags(EventFlags.ITEM_REMOVED | EventFlags.ITEM_IS_FILE),
                node_id=1
            ),
            priority_score=70,
            priority_category="HIGH"
        ),
    ]

    return entries


@pytest.fixture
def grouper():
    """Create TimelineGrouper instance."""
    return TimelineGrouper()


class TestTimelineGrouperInit:
    """Test TimelineGrouper initialization."""

    def test_init_default(self):
        """Test initialization with defaults."""
        grouper = TimelineGrouper()
        assert grouper.time_threshold.total_seconds() == 60

    def test_init_custom_threshold(self):
        """Test initialization with custom threshold."""
        grouper = TimelineGrouper(time_threshold_seconds=300)
        assert grouper.time_threshold.total_seconds() == 300


class TestGroupByPath:
    """Test grouping by path."""

    def test_group_by_path_basic(self, grouper, sample_entries):
        """Test basic path grouping."""
        grouped = grouper.group_by_path(sample_entries)

        assert len(grouped) == 3  # 3 unique paths
        assert Path("/Users/test/document.txt") in grouped
        assert len(grouped[Path("/Users/test/document.txt")]) == 3

    def test_group_by_path_chronological(self, grouper, sample_entries):
        """Test that path groups are chronologically sorted."""
        grouped = grouper.group_by_path(sample_entries)

        for path, entries in grouped.items():
            timestamps = [e.event.timestamp for e in entries]
            assert timestamps == sorted(timestamps)

    def test_group_by_path_empty(self, grouper):
        """Test grouping empty list."""
        grouped = grouper.group_by_path([])
        assert grouped == {}


class TestGroupByDirectory:
    """Test grouping by directory."""

    def test_group_by_directory_basic(self, grouper, sample_entries):
        """Test basic directory grouping."""
        grouped = grouper.group_by_directory(sample_entries)

        assert Path("/Users/test") in grouped
        assert Path("/Users/test/other") in grouped

    def test_group_by_directory_counts(self, grouper, sample_entries):
        """Test directory group sizes."""
        grouped = grouper.group_by_directory(sample_entries)

        # /Users/test has document.txt and script.sh events
        test_dir_count = len(grouped[Path("/Users/test")])
        assert test_dir_count == 4

    def test_group_by_directory_chronological(self, grouper, sample_entries):
        """Test that directory groups are sorted."""
        grouped = grouper.group_by_directory(sample_entries)

        for directory, entries in grouped.items():
            timestamps = [e.event.timestamp for e in entries]
            assert timestamps == sorted(timestamps)


class TestGroupByPriority:
    """Test grouping by priority."""

    def test_group_by_priority_basic(self, grouper, sample_entries):
        """Test basic priority grouping."""
        grouped = grouper.group_by_priority(sample_entries)

        assert "MEDIUM" in grouped
        assert "HIGH" in grouped
        assert "LOW" in grouped

    def test_group_by_priority_counts(self, grouper, sample_entries):
        """Test priority group sizes."""
        grouped = grouper.group_by_priority(sample_entries)

        assert len(grouped["MEDIUM"]) == 2
        assert len(grouped["HIGH"]) == 2
        assert len(grouped["LOW"]) == 1

    def test_group_by_priority_correctness(self, grouper, sample_entries):
        """Test that entries are in correct priority groups."""
        grouped = grouper.group_by_priority(sample_entries)

        for category, entries in grouped.items():
            assert all(e.priority_category == category for e in entries)


class TestGroupByEventType:
    """Test grouping by event type."""

    def test_group_by_event_type_basic(self, grouper, sample_entries):
        """Test basic event type grouping."""
        grouped = grouper.group_by_event_type(sample_entries)

        assert "Created" in grouped
        assert "Modified" in grouped
        assert "Removed" in grouped

    def test_group_by_event_type_correctness(self, grouper, sample_entries):
        """Test that events are grouped correctly."""
        grouped = grouper.group_by_event_type(sample_entries)

        # Check Created events
        created = grouped["Created"]
        assert len(created) == 3


class TestGroupByTimeWindow:
    """Test grouping by time window."""

    def test_group_by_time_window_basic(self, grouper, sample_entries):
        """Test basic time window grouping."""
        groups = grouper.group_by_time_window(sample_entries, window_size_minutes=60)

        assert len(groups) > 0
        assert isinstance(groups, list)
        assert all(isinstance(g, list) for g in groups)

    def test_group_by_time_window_60min(self, grouper, sample_entries):
        """Test 60-minute window grouping."""
        groups = grouper.group_by_time_window(sample_entries, window_size_minutes=60)

        # Events at 0, 5, 10 minutes should be in first window
        # Event at 2 hours should be in different window
        assert len(groups) >= 2

    def test_group_by_time_window_large(self, grouper, sample_entries):
        """Test large time window."""
        groups = grouper.group_by_time_window(sample_entries, window_size_minutes=240)

        # All events within 4 hours should be in one group
        assert len(groups) == 1

    def test_group_by_time_window_empty(self, grouper):
        """Test time window grouping with empty list."""
        groups = grouper.group_by_time_window([])
        assert groups == []


class TestGroupRelatedEvents:
    """Test grouping related events."""

    def test_group_related_events_basic(self, grouper, sample_entries):
        """Test basic related events grouping."""
        groups = grouper.group_related_events(sample_entries)

        assert len(groups) > 0
        assert isinstance(groups, list)

    def test_group_related_events_same_file(self, grouper):
        """Test that events on same file are grouped."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)

        entries = [
            TimelineEntry(
                event=FSEvent(
                    event_id=1,
                    timestamp=base_time,
                    path=Path("/test.txt"),
                    flags=EventFlags(EventFlags.ITEM_CREATED),
                    node_id=1
                ),
                priority_score=50,
                priority_category="MEDIUM"
            ),
            TimelineEntry(
                event=FSEvent(
                    event_id=2,
                    timestamp=base_time + timedelta(seconds=30),
                    path=Path("/test.txt"),
                    flags=EventFlags(EventFlags.ITEM_MODIFIED),
                    node_id=1
                ),
                priority_score=50,
                priority_category="MEDIUM"
            ),
        ]

        groups = grouper.group_related_events(entries)

        # Should be in same group (same path, within 60s)
        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_group_related_events_time_threshold(self, grouper):
        """Test that time threshold separates groups."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)

        entries = [
            TimelineEntry(
                event=FSEvent(
                    event_id=1,
                    timestamp=base_time,
                    path=Path("/test.txt"),
                    flags=EventFlags(EventFlags.ITEM_CREATED),
                    node_id=1
                ),
                priority_score=50,
                priority_category="MEDIUM"
            ),
            TimelineEntry(
                event=FSEvent(
                    event_id=2,
                    timestamp=base_time + timedelta(minutes=5),
                    path=Path("/test.txt"),
                    flags=EventFlags(EventFlags.ITEM_MODIFIED),
                    node_id=1
                ),
                priority_score=50,
                priority_category="MEDIUM"
            ),
        ]

        # Use custom grouper with 30s threshold
        custom_grouper = TimelineGrouper(time_threshold_seconds=30)
        groups = custom_grouper.group_related_events(entries)

        # Should be in separate groups (beyond 30s threshold)
        assert len(groups) == 2


class TestGroupFileOperations:
    """Test grouping by file operations."""

    def test_group_file_operations_basic(self, grouper, sample_entries):
        """Test basic file operations grouping."""
        operations = grouper.group_file_operations(sample_entries)

        assert 'created' in operations
        assert 'modified' in operations
        assert 'deleted' in operations

    def test_group_file_operations_counts(self, grouper, sample_entries):
        """Test file operation counts."""
        operations = grouper.group_file_operations(sample_entries)

        assert len(operations['created']) == 3
        assert len(operations['modified']) == 1
        assert len(operations['deleted']) == 1

    def test_group_file_operations_chronological(self, grouper, sample_entries):
        """Test that operations are sorted chronologically."""
        operations = grouper.group_file_operations(sample_entries)

        for op_type, entries in operations.items():
            if entries:
                timestamps = [e.event.timestamp for e in entries]
                assert timestamps == sorted(timestamps)


class TestGroupByFileExtension:
    """Test grouping by file extension."""

    def test_group_by_extension_basic(self, grouper, sample_entries):
        """Test basic extension grouping."""
        grouped = grouper.group_by_file_extension(sample_entries)

        assert '.txt' in grouped
        assert '.sh' in grouped
        assert '.pdf' in grouped

    def test_group_by_extension_counts(self, grouper, sample_entries):
        """Test extension group sizes."""
        grouped = grouper.group_by_file_extension(sample_entries)

        # document.txt has 3 events
        assert len(grouped['.txt']) == 3

    def test_group_by_extension_no_extension(self, grouper):
        """Test files without extension."""
        entries = [
            TimelineEntry(
                event=FSEvent(
                    event_id=1,
                    timestamp=datetime(2024, 1, 15, 10, 0, 0),
                    path=Path("/Users/test/Makefile"),
                    flags=EventFlags(EventFlags.ITEM_CREATED),
                    node_id=1
                ),
                priority_score=50,
                priority_category="MEDIUM"
            )
        ]

        grouped = grouper.group_by_file_extension(entries)
        assert '(no extension)' in grouped


class TestGroupSuspiciousActivity:
    """Test grouping suspicious activities."""

    def test_group_suspicious_activity_basic(self, grouper):
        """Test basic suspicious activity grouping."""
        quarantine = QuarantineInfo(
            flags='0001',
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            source_app='com.apple.Safari',
            uuid='ABC'
        )

        xattr = XattrRecord(
            file_path=Path("/test.sh"),
            attributes={'com.apple.quarantine': b'0001'},
            quarantine_info=quarantine
        )

        entries = [
            TimelineEntry(
                event=FSEvent(
                    event_id=1,
                    timestamp=datetime(2024, 1, 15, 10, 0, 0),
                    path=Path("/test.sh"),
                    flags=EventFlags(EventFlags.ITEM_CREATED),
                    node_id=1
                ),
                priority_score=80,
                priority_category="HIGH",
                xattr=xattr
            )
        ]

        activities = grouper.group_suspicious_activity(entries, min_priority=70)

        assert 'quarantined_downloads' in activities
        assert len(activities['quarantined_downloads']) == 1

    def test_group_suspicious_activity_system_mods(self, grouper):
        """Test system modification detection."""
        entries = [
            TimelineEntry(
                event=FSEvent(
                    event_id=1,
                    timestamp=datetime(2024, 1, 15, 10, 0, 0),
                    path=Path("/System/Library/file.plist"),
                    flags=EventFlags(EventFlags.ITEM_MODIFIED),
                    node_id=1
                ),
                priority_score=90,
                priority_category="CRITICAL"
            )
        ]

        activities = grouper.group_suspicious_activity(entries, min_priority=70)

        assert 'system_modifications' in activities
        assert len(activities['system_modifications']) == 1

    def test_group_suspicious_activity_threshold(self, grouper, sample_entries):
        """Test suspicious activity priority threshold."""
        activities = grouper.group_suspicious_activity(sample_entries, min_priority=100)

        # No entries should meet 100 priority threshold
        total = sum(len(v) for v in activities.values())
        assert total == 0


class TestHourlyAndDailyGroups:
    """Test hourly and daily grouping."""

    def test_create_hourly_groups_basic(self, grouper, sample_entries):
        """Test basic hourly grouping."""
        grouped = grouper.create_hourly_groups(sample_entries)

        assert len(grouped) > 0
        assert all(isinstance(k, str) for k in grouped.keys())

    def test_create_daily_groups_basic(self, grouper, sample_entries):
        """Test basic daily grouping."""
        grouped = grouper.create_daily_groups(sample_entries)

        assert len(grouped) > 0
        # All sample entries are from same day
        assert len(grouped) == 1
        assert '2024-01-15' in grouped

    def test_create_daily_groups_multiple_days(self, grouper):
        """Test daily grouping across multiple days."""
        entries = [
            TimelineEntry(
                event=FSEvent(
                    event_id=1,
                    timestamp=datetime(2024, 1, 15, 10, 0, 0),
                    path=Path("/test1.txt"),
                    flags=EventFlags(EventFlags.ITEM_CREATED),
                    node_id=1
                ),
                priority_score=50,
                priority_category="MEDIUM"
            ),
            TimelineEntry(
                event=FSEvent(
                    event_id=2,
                    timestamp=datetime(2024, 1, 16, 10, 0, 0),
                    path=Path("/test2.txt"),
                    flags=EventFlags(EventFlags.ITEM_CREATED),
                    node_id=2
                ),
                priority_score=50,
                priority_category="MEDIUM"
            ),
        ]

        grouped = grouper.create_daily_groups(entries)

        assert len(grouped) == 2
        assert '2024-01-15' in grouped
        assert '2024-01-16' in grouped


class TestCustomGrouping:
    """Test custom grouping function."""

    def test_custom_grouping_basic(self, grouper, sample_entries):
        """Test custom grouping with simple key function."""
        # Group by first character of filename
        def key_func(entry):
            return entry.event.path.name[0].upper()

        grouped = grouper.custom_grouping(sample_entries, key_func)

        assert 'D' in grouped  # document.txt
        assert 'S' in grouped  # script.sh
        assert 'F' in grouped  # file.pdf

    def test_custom_grouping_error_handling(self, grouper, sample_entries):
        """Test custom grouping with errors."""
        def error_func(entry):
            raise ValueError("Test error")

        # Should not raise, but log warnings
        grouped = grouper.custom_grouping(sample_entries, error_func)

        # All entries should fail, resulting in empty dict
        assert grouped == {}

    def test_custom_grouping_by_score_range(self, grouper, sample_entries):
        """Test custom grouping by score ranges."""
        def score_range(entry):
            score = entry.priority_score
            if score >= 80:
                return "80-100"
            elif score >= 60:
                return "60-79"
            elif score >= 40:
                return "40-59"
            else:
                return "0-39"

        grouped = grouper.custom_grouping(sample_entries, score_range)

        assert "80-100" in grouped
        assert "60-79" in grouped
        assert "40-59" in grouped
