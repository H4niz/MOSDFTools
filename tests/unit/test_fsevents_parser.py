"""
Unit tests for FSEventsParser
"""

import pytest
import struct
from pathlib import Path
from datetime import datetime
from mfaa.parser.fsevents_parser import FSEventsParser
from mfaa.models import FSEvent, EventFlags
from mfaa.utils.exceptions import ParseError


class TestFSEventsParser:
    """Test cases for FSEventsParser."""

    def test_init(self):
        """Test parser initialization."""
        parser = FSEventsParser()
        assert parser.version is None
        assert parser.gzip_handler is not None

        parser_v1 = FSEventsParser(version=1)
        assert parser_v1.version == 1

    def test_timestamp_conversion(self):
        """Test macOS timestamp to datetime conversion."""
        # Test timestamp for 2025-01-01 00:00:00
        # macOS epoch: 2001-01-01, Unix epoch: 1970-01-01
        # 2025-01-01 = 757382400 seconds since 2001-01-01
        macos_timestamp = 757382400
        dt = FSEventsParser.timestamp_to_datetime(macos_timestamp)

        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 1

    def test_decode_flags(self):
        """Test flag decoding."""
        # Test ITEM_CREATED flag
        flags = EventFlags.ITEM_CREATED
        decoded = FSEventsParser.decode_flags(flags.value)
        assert EventFlags.ITEM_CREATED in decoded

        # Test combined flags
        combined = EventFlags.ITEM_CREATED | EventFlags.ITEM_IS_FILE
        decoded = FSEventsParser.decode_flags(combined.value)
        assert EventFlags.ITEM_CREATED in decoded
        assert EventFlags.ITEM_IS_FILE in decoded

    def test_parse_v1_format(self, tmp_path):
        """Test parsing FSEvents v1 format."""
        # Create mock v1 FSEvents data
        test_file = tmp_path / "test_v1"

        # Build v1 format: path + event_id + flags
        path = b"/Users/test/file.txt\x00"
        event_id = struct.pack('<Q', 12345)  # 8 bytes
        flags = struct.pack('<I', EventFlags.ITEM_CREATED.value)  # 4 bytes

        data = path + event_id + flags
        test_file.write_bytes(data)

        parser = FSEventsParser(version=1)
        events = parser.parse_file(test_file)

        assert len(events) == 1
        assert events[0].event_id == 12345
        assert str(events[0].path) == "/Users/test/file.txt"
        assert EventFlags.ITEM_CREATED in events[0].flags

    def test_parse_v1_multiple_records(self, tmp_path):
        """Test parsing multiple v1 records."""
        test_file = tmp_path / "test_v1_multi"

        # Create 3 records
        data = b""
        for i in range(3):
            path = f"/Users/test/file{i}.txt\x00".encode()
            event_id = struct.pack('<Q', 1000 + i)
            flags = struct.pack('<I', EventFlags.ITEM_CREATED.value)
            data += path + event_id + flags

        test_file.write_bytes(data)

        parser = FSEventsParser(version=1)
        events = parser.parse_file(test_file)

        assert len(events) == 3
        for i, event in enumerate(events):
            assert event.event_id == 1000 + i
            assert f"file{i}.txt" in str(event.path)

    def test_parse_v2_format(self, tmp_path):
        """Test parsing FSEvents v2/DLS format."""
        test_file = tmp_path / "test_v2"

        # Build v2 format with header
        header = b'1SLD' + b'\x00' * 8  # 12 bytes header

        # Record: path + event_id + flags + timestamp + node_id
        path = b"/Users/test/file.txt\x00"
        event_id = struct.pack('<Q', 54321)
        flags = struct.pack('<I', EventFlags.ITEM_MODIFIED.value)
        timestamp = struct.pack('<Q', 757382400)  # 2025-01-01
        node_id = struct.pack('<Q', 999)

        data = header + path + event_id + flags + timestamp + node_id
        test_file.write_bytes(data)

        parser = FSEventsParser(version=2)
        events = parser.parse_file(test_file)

        assert len(events) == 1
        assert events[0].event_id == 54321
        assert str(events[0].path) == "/Users/test/file.txt"
        assert EventFlags.ITEM_MODIFIED in events[0].flags
        assert events[0].timestamp.year == 2025
        assert events[0].node_id == 999

    def test_parse_v2_multiple_records(self, tmp_path):
        """Test parsing multiple v2 records."""
        test_file = tmp_path / "test_v2_multi"

        header = b'2SLD' + b'\x00' * 8
        data = header

        for i in range(5):
            path = f"/Users/test/dir{i}/file.txt\x00".encode()
            event_id = struct.pack('<Q', 2000 + i)
            flags = struct.pack('<I', EventFlags.ITEM_CREATED.value | EventFlags.ITEM_IS_FILE.value)
            timestamp = struct.pack('<Q', 757382400 + i * 3600)
            node_id = struct.pack('<Q', 1000 + i)
            data += path + event_id + flags + timestamp + node_id

        test_file.write_bytes(data)

        parser = FSEventsParser(version=2)
        events = parser.parse_file(test_file)

        assert len(events) == 5
        for i, event in enumerate(events):
            assert event.event_id == 2000 + i
            assert event.node_id == 1000 + i

    def test_parse_gzipped_file(self, tmp_path):
        """Test parsing gzip-compressed FSEvents (v2)."""
        import gzip

        test_file = tmp_path / "test_v2.gz"

        # Create v2 data
        header = b'2SLD' + b'\x00' * 8
        path = b"/test.txt\x00"
        event_id = struct.pack('<Q', 99999)
        flags = struct.pack('<I', EventFlags.ITEM_REMOVED.value)
        timestamp = struct.pack('<Q', 757382400)
        node_id = struct.pack('<Q', 777)

        data = header + path + event_id + flags + timestamp + node_id

        # Gzip compress
        with gzip.open(test_file, 'wb') as f:
            f.write(data)

        parser = FSEventsParser()  # Auto-detect
        events = parser.parse_file(test_file)

        assert len(events) == 1
        assert events[0].event_id == 99999
        assert EventFlags.ITEM_REMOVED in events[0].flags

    def test_parse_invalid_file(self, tmp_path):
        """Test parsing invalid file."""
        test_file = tmp_path / "invalid"
        test_file.write_bytes(b"invalid data")

        parser = FSEventsParser(version=1)
        # Should not crash, but return empty list or raise ParseError
        with pytest.raises((ParseError, Exception)):
            events = parser.parse_file(test_file)

    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file."""
        parser = FSEventsParser()

        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("/nonexistent/file"))

    def test_parse_directory(self, tmp_path):
        """Test parsing directory of FSEvents files."""
        fsevents_dir = tmp_path / ".fseventsd"
        fsevents_dir.mkdir()

        # Create multiple FSEvents files
        for i in range(3):
            file_path = fsevents_dir / f"000000000000{i:04x}"
            path = f"/test{i}.txt\x00".encode()
            event_id = struct.pack('<Q', i)
            flags = struct.pack('<I', EventFlags.ITEM_CREATED.value)
            data = path + event_id + flags
            file_path.write_bytes(data)

        parser = FSEventsParser(version=1)
        all_events = parser.parse_directory(fsevents_dir)

        assert len(all_events) == 3

    def test_validate_events(self):
        """Test event validation."""
        parser = FSEventsParser()

        valid_event = FSEvent(
            event_id=123,
            timestamp=datetime(2025, 1, 1),
            path=Path("/valid/path.txt"),
            flags=EventFlags.ITEM_CREATED
        )

        invalid_event_id = FSEvent(
            event_id=0,  # Invalid
            timestamp=datetime(2025, 1, 1),
            path=Path("/valid/path.txt"),
            flags=EventFlags.ITEM_CREATED
        )

        events = [valid_event, invalid_event_id]
        validated = parser.validate_events(events)

        assert len(validated) == 1
        assert validated[0].event_id == 123

    def test_get_statistics(self):
        """Test getting event statistics."""
        parser = FSEventsParser()

        events = [
            FSEvent(
                event_id=1,
                timestamp=datetime(2025, 1, 1),
                path=Path("/file1.txt"),
                flags=EventFlags.ITEM_CREATED | EventFlags.ITEM_IS_FILE
            ),
            FSEvent(
                event_id=2,
                timestamp=datetime(2025, 1, 2),
                path=Path("/file2.txt"),
                flags=EventFlags.ITEM_MODIFIED | EventFlags.ITEM_IS_FILE
            ),
            FSEvent(
                event_id=3,
                timestamp=datetime(2025, 1, 3),
                path=Path("/file3.txt"),
                flags=EventFlags.ITEM_REMOVED | EventFlags.ITEM_IS_FILE,
                node_id=12345
            )
        ]

        stats = parser.get_statistics(events)

        assert stats['total_events'] == 3
        assert stats['unique_paths'] == 3
        assert stats['has_timestamps'] is True
        assert stats['has_node_ids'] is True
        assert 'Created' in stats['event_types']
        assert 'Modified' in stats['event_types']
        assert 'Removed' in stats['event_types']

    def test_get_statistics_empty(self):
        """Test statistics with empty event list."""
        parser = FSEventsParser()
        stats = parser.get_statistics([])

        assert stats['total_events'] == 0
        assert stats['unique_paths'] == 0
        assert stats['date_range'] is None
