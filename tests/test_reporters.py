"""
Tests for Reporter Module
"""

import pytest
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
from mfaa.reporter.base_reporter import BaseReporter
from mfaa.reporter.csv_reporter import CSVReporter
from mfaa.reporter.json_reporter import JSONReporter
from mfaa.reporter.html_reporter import HTMLReporter
from mfaa.models import (
    FSEvent, EventFlags, TimelineEntry, Timeline,
    Pattern, XattrRecord, QuarantineInfo
)


@pytest.fixture
def sample_timeline(tmp_path):
    """Create sample timeline for testing."""
    base_time = datetime(2024, 1, 15, 10, 0, 0)

    # Create events
    events = [
        FSEvent(
            event_id=1,
            timestamp=base_time,
            path=Path("/Users/test/malware.exe"),
            flags=EventFlags(EventFlags.ITEM_CREATED | EventFlags.ITEM_IS_FILE),
            node_id=1001
        ),
        FSEvent(
            event_id=2,
            timestamp=base_time + timedelta(minutes=5),
            path=Path("/Users/test/document.txt"),
            flags=EventFlags(EventFlags.ITEM_MODIFIED | EventFlags.ITEM_IS_FILE),
            node_id=1002
        ),
        FSEvent(
            event_id=3,
            timestamp=base_time + timedelta(minutes=10),
            path=Path("/Users/test/script.sh"),
            flags=EventFlags(EventFlags.ITEM_REMOVED | EventFlags.ITEM_IS_FILE),
            node_id=1003
        ),
    ]

    # Create xattr
    quarantine = QuarantineInfo(
        flags='0001',
        timestamp=base_time,
        source_app='com.apple.Safari',
        uuid='ABC-123'
    )
    xattr = XattrRecord(
        file_path=Path("/Users/test/malware.exe"),
        attributes={'com.apple.quarantine': b'0001'},
        quarantine_info=quarantine,
        download_urls=['http://malicious.com/malware.exe']
    )

    # Create timeline entries
    entries = [
        TimelineEntry(
            event=events[0],
            priority_score=90,
            priority_category="CRITICAL",
            xattr=xattr
        ),
        TimelineEntry(
            event=events[1],
            priority_score=50,
            priority_category="MEDIUM"
        ),
        TimelineEntry(
            event=events[2],
            priority_score=70,
            priority_category="HIGH"
        ),
    ]

    # Create pattern
    pattern = Pattern(
        pattern_type="ransomware_encryption",
        severity="CRITICAL",
        start_time=base_time,
        end_time=base_time + timedelta(minutes=15),
        event_count=10,
        affected_paths=[Path("/Users/test/file1.txt"), Path("/Users/test/file2.txt")],
        description="Potential ransomware encryption detected",
        indicators={'encrypted_files': 10}
    )

    # Create timeline
    timeline = Timeline(
        entries=entries,
        patterns=[pattern],
        statistics={
            'total_entries': 3,
            'priority_distribution': {'CRITICAL': 1, 'HIGH': 1, 'MEDIUM': 1},
            'patterns_detected': 1
        },
        info={'generated_at': datetime.now().isoformat()}
    )

    return timeline


class TestCSVReporter:
    """Test CSV reporter."""

    def test_generate_basic(self, sample_timeline, tmp_path):
        """Test basic CSV generation."""
        reporter = CSVReporter()
        output_path = tmp_path / "report.csv"

        reporter.generate(sample_timeline, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_csv_content(self, sample_timeline, tmp_path):
        """Test CSV content is correct."""
        reporter = CSVReporter()
        output_path = tmp_path / "report.csv"

        reporter.generate(sample_timeline, output_path)

        # Read and verify
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        assert rows[0]['event_id'] == '1'
        assert rows[0]['priority_category'] == 'CRITICAL'

    def test_patterns_csv(self, sample_timeline, tmp_path):
        """Test patterns CSV generation."""
        reporter = CSVReporter()
        output_path = tmp_path / "report.csv"

        reporter.generate(sample_timeline, output_path, include_patterns=True)

        patterns_path = tmp_path / "report_patterns.csv"
        assert patterns_path.exists()

        with open(patterns_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]['pattern_type'] == 'ransomware_encryption'

    def test_summary_csv(self, sample_timeline, tmp_path):
        """Test summary CSV generation."""
        reporter = CSVReporter()
        output_path = tmp_path / "summary.csv"

        reporter.generate_summary_csv(sample_timeline, output_path, min_priority=60)

        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should only include events with priority >= 60
        assert len(rows) == 2  # CRITICAL (90) and HIGH (70)


class TestJSONReporter:
    """Test JSON reporter."""

    def test_generate_basic(self, sample_timeline, tmp_path):
        """Test basic JSON generation."""
        reporter = JSONReporter()
        output_path = tmp_path / "report.json"

        reporter.generate(sample_timeline, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_json_structure(self, sample_timeline, tmp_path):
        """Test JSON structure is correct."""
        reporter = JSONReporter()
        output_path = tmp_path / "report.json"

        reporter.generate(sample_timeline, output_path)

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'metadata' in data
        assert 'summary' in data
        assert 'events' in data
        assert 'patterns' in data
        assert 'statistics' in data

        assert len(data['events']) == 3
        assert len(data['patterns']) == 1

    def test_compact_json(self, sample_timeline, tmp_path):
        """Test compact JSON generation."""
        reporter = JSONReporter()
        output_path = tmp_path / "compact.json"

        reporter.generate_compact(sample_timeline, output_path)

        with open(output_path, 'r') as f:
            content = f.read()
            data = json.loads(content)

        # Compact should have fewer keys per event
        assert 'events' in data
        event = data['events'][0]
        assert 'event_id' in event
        assert 'timestamp' in event

    def test_events_only_json(self, sample_timeline, tmp_path):
        """Test events-only JSON."""
        reporter = JSONReporter()
        output_path = tmp_path / "events.json"

        reporter.generate_events_only(sample_timeline, output_path)

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'events' in data
        assert 'patterns' not in data

    def test_patterns_only_json(self, sample_timeline, tmp_path):
        """Test patterns-only JSON."""
        reporter = JSONReporter()
        output_path = tmp_path / "patterns.json"

        reporter.generate_patterns_only(sample_timeline, output_path)

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'patterns' in data
        assert 'events' not in data
        assert len(data['patterns']) == 1


class TestHTMLReporter:
    """Test HTML reporter."""

    def test_generate_basic(self, sample_timeline, tmp_path):
        """Test basic HTML generation."""
        reporter = HTMLReporter()
        output_path = tmp_path / "report.html"

        reporter.generate(sample_timeline, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_html_content(self, sample_timeline, tmp_path):
        """Test HTML contains expected elements."""
        reporter = HTMLReporter()
        output_path = tmp_path / "report.html"

        reporter.generate(sample_timeline, output_path)

        with open(output_path, 'r') as f:
            content = f.read()

        # Check for key elements
        assert 'mFAA Forensic Analysis Report' in content
        assert 'timeline-container' in content
        assert 'priority-chart' in content
        assert 'correlation-graph' in content
        assert 'Plotly' in content or 'plotly' in content

    def test_executive_summary(self, sample_timeline, tmp_path):
        """Test executive summary generation."""
        reporter = HTMLReporter()
        output_path = tmp_path / "summary.html"

        reporter.generate_executive_summary(sample_timeline, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            content = f.read()

        assert 'Executive Summary' in content
        assert 'CRITICAL' in content


class TestBaseReporter:
    """Test base reporter functionality."""

    def test_metadata_preparation(self, sample_timeline):
        """Test metadata preparation."""
        reporter = CSVReporter()
        metadata = reporter._prepare_metadata(sample_timeline)

        assert 'generated_at' in metadata
        assert 'generator' in metadata
        assert 'version' in metadata

    def test_validate_timeline(self, sample_timeline):
        """Test timeline validation."""
        reporter = CSVReporter()

        # Should not raise for valid timeline
        reporter._validate_timeline(sample_timeline)

        # Should raise for invalid input
        with pytest.raises(ValueError):
            reporter._validate_timeline("not a timeline")

    def test_ensure_output_directory(self, tmp_path):
        """Test output directory creation."""
        reporter = CSVReporter()
        output_path = tmp_path / "subdir" / "report.csv"

        assert not output_path.parent.exists()

        reporter._ensure_output_directory(output_path)

        assert output_path.parent.exists()

    def test_format_file_size(self):
        """Test file size formatting."""
        reporter = CSVReporter()

        assert "1.00 KB" == reporter._format_file_size(1024)
        assert "1.00 MB" == reporter._format_file_size(1024 * 1024)
        assert "500.00 B" == reporter._format_file_size(500)

    def test_get_report_info(self, sample_timeline, tmp_path):
        """Test getting report information."""
        reporter = CSVReporter()
        output_path = tmp_path / "report.csv"

        # Before generation
        info = reporter.get_report_info(output_path)
        assert info['exists'] is False

        # After generation
        reporter.generate(sample_timeline, output_path)
        info = reporter.get_report_info(output_path)

        assert info['exists'] is True
        assert 'size' in info
        assert 'path' in info


class TestReporterIntegration:
    """Integration tests for reporters."""

    def test_all_formats_generated(self, sample_timeline, tmp_path):
        """Test generating all report formats."""
        csv_reporter = CSVReporter()
        json_reporter = JSONReporter()
        html_reporter = HTMLReporter()

        csv_path = tmp_path / "report.csv"
        json_path = tmp_path / "report.json"
        html_path = tmp_path / "report.html"

        csv_reporter.generate(sample_timeline, csv_path)
        json_reporter.generate(sample_timeline, json_path)
        html_reporter.generate(sample_timeline, html_path)

        assert csv_path.exists()
        assert json_path.exists()
        assert html_path.exists()

    def test_consistent_data_across_formats(self, sample_timeline, tmp_path):
        """Test data consistency across formats."""
        csv_reporter = CSVReporter()
        json_reporter = JSONReporter()

        csv_path = tmp_path / "report.csv"
        json_path = tmp_path / "report.json"

        csv_reporter.generate(sample_timeline, csv_path)
        json_reporter.generate(sample_timeline, json_path)

        # Read CSV
        with open(csv_path, 'r') as f:
            csv_rows = list(csv.DictReader(f))

        # Read JSON
        with open(json_path, 'r') as f:
            json_data = json.load(f)

        # Should have same number of events
        assert len(csv_rows) == len(json_data['events'])
