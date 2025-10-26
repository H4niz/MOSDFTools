"""
Integration tests for Parser module with Collector
"""

import pytest
import struct
import gzip
from pathlib import Path
from mfaa.collector import FSEventsCollector
from mfaa.parser import FSEventsParser
from mfaa.models import VolumeInfo, EventFlags


@pytest.mark.integration
class TestParserIntegration:
    """Integration tests for Parser module."""

    def test_collect_and_parse_workflow(self, tmp_path):
        """Test complete workflow: collect FSEvents and parse them."""
        # Step 1: Create mock FSEvents data
        volume_root = tmp_path / "test_volume"
        volume_root.mkdir()

        fsevents_dir = volume_root / ".fseventsd"
        fsevents_dir.mkdir()

        # Create mock FSEvents file (v1 format)
        fsevents_file = fsevents_dir / "0000000000abcdef"

        events_data = b""
        for i in range(10):
            path = f"/Users/test/file{i}.txt\x00".encode()
            event_id = struct.pack('<Q', 1000 + i)
            flags = struct.pack('<I', EventFlags.ITEM_CREATED.value | EventFlags.ITEM_IS_FILE.value)
            events_data += path + event_id + flags

        fsevents_file.write_bytes(events_data)

        # Step 2: Collect FSEvents
        volume = VolumeInfo(
            name="TestVolume",
            mount_point=volume_root,
            filesystem_type="apfs",
            device_node="/dev/disk3s1",
            total_size=500000000000,
            available_size=250000000000,
            encryption_enabled=False
        )

        output_dir = tmp_path / "collected"
        collector = FSEventsCollector(output_dir, verify_hashes=True)

        collection_result = collector.collect(volume)

        assert collection_result.success is True
        assert collection_result.files_copied == 1

        # Step 3: Parse collected FSEvents
        collected_fsevents_dir = collection_result.output_directory
        parser = FSEventsParser(version=1)

        events = parser.parse_directory(collected_fsevents_dir)

        assert len(events) == 10
        for i, event in enumerate(events):
            assert event.event_id == 1000 + i
            assert EventFlags.ITEM_CREATED in event.flags
            assert EventFlags.ITEM_IS_FILE in event.flags

    def test_collect_parse_v2_gzipped(self, tmp_path):
        """Test collecting and parsing gzipped v2 FSEvents."""
        # Create mock volume with v2 FSEvents
        volume_root = tmp_path / "test_volume"
        volume_root.mkdir()

        fsevents_dir = volume_root / ".fseventsd"
        fsevents_dir.mkdir()

        # Create v2 FSEvents data
        header = b'2SLD' + b'\x00' * 8
        events_data = header

        for i in range(5):
            path = f"/Applications/App{i}.app\x00".encode()
            event_id = struct.pack('<Q', 2000 + i)
            flags = struct.pack('<I', EventFlags.ITEM_MODIFIED.value)
            timestamp = struct.pack('<Q', 757382400 + i * 86400)  # Daily increments
            node_id = struct.pack('<Q', 5000 + i)
            events_data += path + event_id + flags + timestamp + node_id

        # Gzip compress
        fsevents_file = fsevents_dir / "0000000000fedcba.gz"
        with gzip.open(fsevents_file, 'wb') as f:
            f.write(events_data)

        # Collect
        volume = VolumeInfo(
            name="TestVolume",
            mount_point=volume_root,
            filesystem_type="apfs",
            device_node="/dev/disk3s1",
            total_size=500000000000,
            available_size=250000000000,
            encryption_enabled=True
        )

        output_dir = tmp_path / "collected"
        collector = FSEventsCollector(output_dir, verify_hashes=True)
        collection_result = collector.collect(volume)

        assert collection_result.success is True

        # Parse (should auto-detect gzip)
        parser = FSEventsParser()  # Auto-detect version
        events = parser.parse_directory(collection_result.output_directory)

        assert len(events) == 5
        for i, event in enumerate(events):
            assert event.event_id == 2000 + i
            assert event.node_id == 5000 + i
            assert event.timestamp.year == 2025

    def test_parse_with_validation(self, tmp_path):
        """Test parsing with validation and statistics."""
        # Create FSEvents data with some invalid records
        fsevents_dir = tmp_path / ".fseventsd"
        fsevents_dir.mkdir()

        fsevents_file = fsevents_dir / "test"

        # Mix of valid and invalid events
        events_data = b""

        # Valid event
        events_data += b"/valid/path.txt\x00"
        events_data += struct.pack('<Q', 123)
        events_data += struct.pack('<I', EventFlags.ITEM_CREATED.value)

        # Invalid event (event_id = 0)
        events_data += b"/invalid/path.txt\x00"
        events_data += struct.pack('<Q', 0)  # Invalid event ID
        events_data += struct.pack('<I', EventFlags.ITEM_CREATED.value)

        # Another valid event
        events_data += b"/another/valid.txt\x00"
        events_data += struct.pack('<Q', 456)
        events_data += struct.pack('<I', EventFlags.ITEM_REMOVED.value)

        fsevents_file.write_bytes(events_data)

        # Parse
        parser = FSEventsParser(version=1)
        events = parser.parse_file(fsevents_file)

        # Validate
        valid_events = parser.validate_events(events)

        # Should filter out the invalid event
        assert len(valid_events) < len(events) or len(valid_events) == 2

        # Get statistics
        stats = parser.get_statistics(valid_events)

        assert stats['total_events'] >= 2
        assert 'Created' in stats['event_types'] or 'Removed' in stats['event_types']

    def test_mixed_format_collection(self, tmp_path):
        """Test collecting and parsing directory with mixed v1/v2 formats."""
        # Create volume with mixed FSEvents files
        volume_root = tmp_path / "test_volume"
        volume_root.mkdir()

        fsevents_dir = volume_root / ".fseventsd"
        fsevents_dir.mkdir()

        # Create v1 file
        v1_file = fsevents_dir / "file_v1"
        v1_data = b"/v1/file.txt\x00"
        v1_data += struct.pack('<Q', 111)
        v1_data += struct.pack('<I', EventFlags.ITEM_CREATED.value)
        v1_file.write_bytes(v1_data)

        # Create v2 file
        v2_file = fsevents_dir / "file_v2"
        v2_data = b'1SLD' + b'\x00' * 8
        v2_data += b"/v2/file.txt\x00"
        v2_data += struct.pack('<Q', 222)
        v2_data += struct.pack('<I', EventFlags.ITEM_MODIFIED.value)
        v2_data += struct.pack('<Q', 757382400)
        v2_data += struct.pack('<Q', 999)
        v2_file.write_bytes(v2_data)

        # Collect
        volume = VolumeInfo(
            name="TestVolume",
            mount_point=volume_root,
            filesystem_type="apfs",
            device_node="/dev/disk3s1",
            total_size=500000000000,
            available_size=250000000000,
            encryption_enabled=False
        )

        output_dir = tmp_path / "collected"
        collector = FSEventsCollector(output_dir)
        collection_result = collector.collect(volume)

        # Parse with auto-detection
        parser = FSEventsParser()
        events = parser.parse_directory(collection_result.output_directory)

        # Should parse both formats
        assert len(events) >= 2

    def test_large_volume_collection(self, tmp_path):
        """Test collecting and parsing large number of events."""
        volume_root = tmp_path / "large_volume"
        volume_root.mkdir()

        fsevents_dir = volume_root / ".fseventsd"
        fsevents_dir.mkdir()

        # Create file with many events
        fsevents_file = fsevents_dir / "large_file"
        events_data = b""

        # Create 1000 events
        for i in range(1000):
            path = f"/large/dataset/file{i:04d}.txt\x00".encode()
            event_id = struct.pack('<Q', 10000 + i)
            flags = struct.pack('<I', EventFlags.ITEM_CREATED.value)
            events_data += path + event_id + flags

        fsevents_file.write_bytes(events_data)

        # Collect
        volume = VolumeInfo(
            name="LargeVolume",
            mount_point=volume_root,
            filesystem_type="apfs",
            device_node="/dev/disk3s1",
            total_size=500000000000,
            available_size=250000000000,
            encryption_enabled=False
        )

        output_dir = tmp_path / "collected"
        collector = FSEventsCollector(output_dir, verify_hashes=True)
        collection_result = collector.collect(volume)

        # Parse
        parser = FSEventsParser(version=1)
        events = parser.parse_directory(collection_result.output_directory)

        assert len(events) == 1000

        # Get statistics
        stats = parser.get_statistics(events)
        assert stats['total_events'] == 1000
        assert stats['unique_paths'] == 1000
