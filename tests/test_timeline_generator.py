"""
Tests for TimelineGenerator
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from mfaa.timeline.generator import TimelineGenerator
from mfaa.models import FSEvent, EventFlags, EventType, XattrRecord, QuarantineInfo
from mfaa.analyzer.priority_scorer import PriorityScorer
from mfaa.analyzer.pattern_detector import PatternDetector


@pytest.fixture
def sample_events():
    """Create sample FSEvents."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)

    events = [
        FSEvent(
            event_id=1,
            timestamp=base_time,
            path=Path("/Users/test/document.txt"),
            flags=EventFlags(EventFlags.ITEM_CREATED | EventFlags.ITEM_IS_FILE),
            node_id=12345
        ),
        FSEvent(
            event_id=2,
            timestamp=base_time + timedelta(minutes=5),
            path=Path("/Users/test/document.txt"),
            flags=EventFlags(EventFlags.ITEM_MODIFIED | EventFlags.ITEM_IS_FILE),
            node_id=12345
        ),
        FSEvent(
            event_id=3,
            timestamp=base_time + timedelta(minutes=10),
            path=Path("/Users/test/script.sh"),
            flags=EventFlags(EventFlags.ITEM_CREATED | EventFlags.ITEM_IS_FILE),
            node_id=12346
        ),
        FSEvent(
            event_id=4,
            timestamp=base_time + timedelta(hours=2),
            path=Path("/Users/test/document.txt"),
            flags=EventFlags(EventFlags.ITEM_REMOVED | EventFlags.ITEM_IS_FILE),
            node_id=12345
        ),
    ]

    return events


@pytest.fixture
def sample_xattr_records():
    """Create sample XattrRecords."""
    quarantine = QuarantineInfo(
        flags='0001',
        timestamp=datetime(2024, 1, 15, 10, 0, 0),
        source_app='com.apple.Safari',
        uuid='ABC-123'
    )

    record = XattrRecord(
        file_path=Path("/Users/test/script.sh"),
        attributes={'com.apple.quarantine': b'0001'},
        quarantine_info=quarantine
    )

    return {
        Path("/Users/test/script.sh"): record
    }


@pytest.fixture
def generator():
    """Create TimelineGenerator instance."""
    return TimelineGenerator()


class TestTimelineGeneratorInit:
    """Test TimelineGenerator initialization."""

    def test_init_default(self):
        """Test initialization with defaults."""
        gen = TimelineGenerator()
        assert gen.scorer is not None
        assert gen.detector is not None
        assert isinstance(gen.scorer, PriorityScorer)
        assert isinstance(gen.detector, PatternDetector)

    def test_init_custom_scorer(self):
        """Test initialization with custom scorer."""
        custom_scorer = PriorityScorer()
        gen = TimelineGenerator(scorer=custom_scorer)
        assert gen.scorer is custom_scorer

    def test_init_custom_detector(self):
        """Test initialization with custom detector."""
        custom_detector = PatternDetector()
        gen = TimelineGenerator(detector=custom_detector)
        assert gen.detector is custom_detector


class TestGenerateTimeline:
    """Test timeline generation."""

    def test_generate_timeline_basic(self, generator, sample_events):
        """Test basic timeline generation."""
        timeline = generator.generate_timeline(sample_events)

        assert timeline is not None
        assert len(timeline.entries) == 4
        assert timeline.statistics['total_entries'] == 4
        assert 'generated_at' in timeline.info

    def test_generate_timeline_empty(self, generator):
        """Test timeline generation with no events."""
        timeline = generator.generate_timeline([])

        assert timeline is not None
        assert len(timeline.entries) == 0
        assert timeline.statistics == {}

    def test_generate_timeline_with_xattr(self, generator, sample_events, sample_xattr_records):
        """Test timeline generation with xattr records."""
        timeline = generator.generate_timeline(sample_events, sample_xattr_records)

        assert timeline is not None
        assert len(timeline.entries) == 4

        # Check that xattr was attached to correct event
        script_entries = [e for e in timeline.entries if e.event.path == Path("/Users/test/script.sh")]
        assert len(script_entries) == 1
        assert script_entries[0].xattr is not None
        assert script_entries[0].xattr.has_quarantine

    def test_timeline_chronological_order(self, generator, sample_events):
        """Test that timeline entries are sorted chronologically."""
        timeline = generator.generate_timeline(sample_events)

        timestamps = [e.event.timestamp for e in timeline.entries]
        assert timestamps == sorted(timestamps)

    def test_timeline_priority_scores(self, generator, sample_events):
        """Test that priority scores are calculated."""
        timeline = generator.generate_timeline(sample_events)

        for entry in timeline.entries:
            assert 0 <= entry.priority_score <= 100
            assert entry.priority_category in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

    def test_timeline_pattern_detection(self, generator, sample_events):
        """Test pattern detection during timeline generation."""
        timeline = generator.generate_timeline(sample_events, detect_patterns=True)

        assert timeline.patterns is not None
        # Pattern detection may or may not find patterns depending on events

    def test_timeline_no_pattern_detection(self, generator, sample_events):
        """Test timeline generation without pattern detection."""
        timeline = generator.generate_timeline(sample_events, detect_patterns=False)

        assert timeline.patterns == []


class TestFocusedTimeline:
    """Test focused timeline generation."""

    def test_focused_timeline(self, generator, sample_events):
        """Test focused timeline around specific path."""
        focus_path = Path("/Users/test/document.txt")
        timeline = generator.generate_focused_timeline(
            sample_events,
            focus_path,
            window_minutes=60
        )

        assert timeline is not None
        assert timeline.info['focus_path'] == str(focus_path)
        assert timeline.info['window_minutes'] == 60

        # Should include events within 60 minutes of document.txt events
        assert len(timeline.entries) >= 2

    def test_focused_timeline_nonexistent_path(self, generator, sample_events):
        """Test focused timeline for nonexistent path."""
        focus_path = Path("/nonexistent/file.txt")
        timeline = generator.generate_focused_timeline(
            sample_events,
            focus_path,
            window_minutes=30
        )

        assert len(timeline.entries) == 0
        assert timeline.info['focus_path'] == str(focus_path)

    def test_focused_timeline_narrow_window(self, generator, sample_events):
        """Test focused timeline with narrow time window."""
        focus_path = Path("/Users/test/document.txt")
        timeline = generator.generate_focused_timeline(
            sample_events,
            focus_path,
            window_minutes=1
        )

        # With 1-minute window, should include document.txt events and nearby events
        # document.txt has events at 10:00, 10:05, 12:00
        # script.sh is at 10:10, which is within 1 min of one occurrence
        assert len(timeline.entries) >= 2  # At least document.txt events
        assert len(timeline.entries) <= 4  # All events in sample


class TestDailyTimeline:
    """Test daily timeline generation."""

    def test_daily_timeline(self, generator, sample_events):
        """Test daily timeline generation."""
        target_date = datetime(2024, 1, 15)
        timeline = generator.generate_daily_timeline(sample_events, target_date)

        assert timeline is not None
        assert timeline.info['target_date'] == '2024-01-15'
        assert len(timeline.entries) == 4  # All events on same day

    def test_daily_timeline_different_day(self, generator, sample_events):
        """Test daily timeline for different day."""
        target_date = datetime(2024, 1, 16)
        timeline = generator.generate_daily_timeline(sample_events, target_date)

        assert len(timeline.entries) == 0  # No events on this day

    def test_daily_timeline_boundary(self, generator):
        """Test daily timeline at day boundaries."""
        events = [
            FSEvent(
                event_id=1,
                timestamp=datetime(2024, 1, 15, 23, 59, 59),
                path=Path("/test1.txt"),
                flags=EventFlags(EventFlags.ITEM_CREATED),
                node_id=1
            ),
            FSEvent(
                event_id=2,
                timestamp=datetime(2024, 1, 16, 0, 0, 1),
                path=Path("/test2.txt"),
                flags=EventFlags(EventFlags.ITEM_CREATED),
                node_id=2
            ),
        ]

        timeline = generator.generate_daily_timeline(events, datetime(2024, 1, 15))
        assert len(timeline.entries) == 1  # Only first event


class TestSummaryTimeline:
    """Test summary timeline generation."""

    def test_summary_timeline(self, generator, sample_events):
        """Test summary timeline with priority filter."""
        timeline = generator.generate_summary_timeline(
            sample_events,
            min_priority=50
        )

        assert timeline is not None
        assert 'summary_min_priority' in timeline.info
        assert timeline.info['summary_min_priority'] == 50

        # All entries should meet minimum priority
        for entry in timeline.entries:
            assert entry.priority_score >= 50

    def test_summary_timeline_high_threshold(self, generator, sample_events):
        """Test summary timeline with high threshold."""
        timeline = generator.generate_summary_timeline(
            sample_events,
            min_priority=90
        )

        # May have fewer entries due to high threshold
        assert len(timeline.entries) <= len(sample_events)

    def test_summary_timeline_low_threshold(self, generator, sample_events):
        """Test summary timeline with low threshold."""
        timeline = generator.generate_summary_timeline(
            sample_events,
            min_priority=0
        )

        # Should include all events
        assert len(timeline.entries) == len(sample_events)


class TestTimelineStatistics:
    """Test timeline statistics calculation."""

    def test_statistics_priority_distribution(self, generator, sample_events):
        """Test priority distribution in statistics."""
        timeline = generator.generate_timeline(sample_events)

        assert 'priority_distribution' in timeline.statistics
        assert isinstance(timeline.statistics['priority_distribution'], dict)

    def test_statistics_score_statistics(self, generator, sample_events):
        """Test score statistics."""
        timeline = generator.generate_timeline(sample_events)

        stats = timeline.statistics['score_statistics']
        assert 'min' in stats
        assert 'max' in stats
        assert 'average' in stats
        assert stats['min'] <= stats['average'] <= stats['max']

    def test_statistics_time_span(self, generator, sample_events):
        """Test time span statistics."""
        timeline = generator.generate_timeline(sample_events)

        time_span = timeline.statistics['time_span']
        assert 'earliest' in time_span
        assert 'latest' in time_span
        assert 'duration_hours' in time_span
        assert time_span['duration_hours'] >= 0

    def test_statistics_event_types(self, generator, sample_events):
        """Test event types statistics."""
        timeline = generator.generate_timeline(sample_events)

        assert 'event_types' in timeline.statistics
        assert isinstance(timeline.statistics['event_types'], dict)


class TestTimelineHelpers:
    """Test helper methods."""

    def test_add_notes_to_entry(self, generator, sample_events):
        """Test adding notes to timeline entry."""
        timeline = generator.generate_timeline(sample_events)

        result = generator.add_notes_to_entry(timeline, 1, "Suspicious activity")
        assert result is True

        # Find the entry
        entry = next(e for e in timeline.entries if e.event.event_id == 1)
        assert "Suspicious activity" in entry.notes

    def test_add_notes_nonexistent_event(self, generator, sample_events):
        """Test adding notes to nonexistent event."""
        timeline = generator.generate_timeline(sample_events)

        result = generator.add_notes_to_entry(timeline, 9999, "Note")
        assert result is False

    def test_get_entries_by_priority(self, generator, sample_events):
        """Test getting entries by priority category."""
        timeline = generator.generate_timeline(sample_events)

        # Get all priority categories present
        categories = set(e.priority_category for e in timeline.entries)

        for category in categories:
            entries = generator.get_entries_by_priority(timeline, category)
            assert all(e.priority_category == category for e in entries)

    def test_get_entries_in_range(self, generator, sample_events):
        """Test getting entries in time range."""
        timeline = generator.generate_timeline(sample_events)

        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 30, 0)

        entries = generator.get_entries_in_range(timeline, start_time, end_time)

        for entry in entries:
            assert start_time <= entry.event.timestamp <= end_time

    def test_get_entries_for_path(self, generator, sample_events):
        """Test getting entries for specific path."""
        timeline = generator.generate_timeline(sample_events)

        path = Path("/Users/test/document.txt")
        entries = generator.get_entries_for_path(timeline, path)

        assert all(e.event.path == path for e in entries)
        assert len(entries) == 3  # document.txt has 3 events

    def test_get_entries_for_path_with_subdirs(self, generator):
        """Test getting entries including subdirectories."""
        events = [
            FSEvent(
                event_id=1,
                timestamp=datetime(2024, 1, 15, 10, 0, 0),
                path=Path("/Users/test/file.txt"),
                flags=EventFlags(EventFlags.ITEM_CREATED),
                node_id=1
            ),
            FSEvent(
                event_id=2,
                timestamp=datetime(2024, 1, 15, 10, 5, 0),
                path=Path("/Users/test/subdir/file.txt"),
                flags=EventFlags(EventFlags.ITEM_CREATED),
                node_id=2
            ),
        ]

        timeline = generator.generate_timeline(events)

        path = Path("/Users/test")
        entries = generator.get_entries_for_path(timeline, path, include_subdirectories=True)

        assert len(entries) == 2  # Both files under /Users/test
