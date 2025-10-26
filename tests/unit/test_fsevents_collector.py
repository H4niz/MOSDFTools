"""
Unit tests for FSEventsCollector
"""

import pytest
from pathlib import Path
from datetime import datetime
from mfaa.collector.fsevents_collector import FSEventsCollector
from mfaa.models import VolumeInfo, CollectionResult
from mfaa.utils.exceptions import CollectionError


class TestFSEventsCollector:
    """Test cases for FSEventsCollector."""

    def test_init(self, tmp_path):
        """Test FSEventsCollector initialization."""
        output_dir = tmp_path / "output"
        collector = FSEventsCollector(output_dir, verify_hashes=True)

        assert collector.output_dir == output_dir
        assert collector.verify_hashes is True
        assert collector.hash_calculator is not None
        assert output_dir.exists()

    def test_init_without_hash_verification(self, tmp_path):
        """Test initialization without hash verification."""
        output_dir = tmp_path / "output"
        collector = FSEventsCollector(output_dir, verify_hashes=False)

        assert collector.verify_hashes is False
        assert collector.hash_calculator is None

    def test_collect_success(self, tmp_path):
        """Test successful FSEvents collection."""
        # Setup mock volume with FSEvents
        volume_root = tmp_path / "volume"
        volume_root.mkdir()

        fsevents_dir = volume_root / ".fseventsd"
        fsevents_dir.mkdir()

        # Create mock FSEvents files
        (fsevents_dir / "0000000000abcdef").write_text("mock fsevents data 1")
        (fsevents_dir / "0000000000fedcba").write_text("mock fsevents data 2")

        volume = VolumeInfo(
            name="TestVolume",
            mount_point=volume_root,
            filesystem_type="apfs",
            device_node="/dev/disk3s1",
            total_size=500000000000,
            available_size=250000000000,
            encryption_enabled=False
        )

        output_dir = tmp_path / "output"
        collector = FSEventsCollector(output_dir, verify_hashes=True)

        result = collector.collect(volume)

        assert isinstance(result, CollectionResult)
        assert result.success is True
        assert result.files_copied == 2
        assert result.total_size > 0
        assert len(result.checksums) == 2
        assert len(result.errors) == 0
        assert result.output_directory.exists()

    def test_collect_nonexistent_fsevents(self, tmp_path):
        """Test collection with nonexistent FSEvents directory."""
        volume_root = tmp_path / "volume"
        volume_root.mkdir()

        volume = VolumeInfo(
            name="TestVolume",
            mount_point=volume_root,
            filesystem_type="apfs",
            device_node="/dev/disk3s1",
            total_size=500000000000,
            available_size=250000000000,
            encryption_enabled=False
        )

        output_dir = tmp_path / "output"
        collector = FSEventsCollector(output_dir)

        with pytest.raises(CollectionError, match="FSEvents directory not found"):
            collector.collect(volume)

    def test_collect_without_hash_verification(self, tmp_path):
        """Test collection without hash calculation."""
        volume_root = tmp_path / "volume"
        volume_root.mkdir()

        fsevents_dir = volume_root / ".fseventsd"
        fsevents_dir.mkdir()
        (fsevents_dir / "testfile").write_text("test data")

        volume = VolumeInfo(
            name="TestVolume",
            mount_point=volume_root,
            filesystem_type="apfs",
            device_node="/dev/disk3s1",
            total_size=500000000000,
            available_size=250000000000,
            encryption_enabled=False
        )

        output_dir = tmp_path / "output"
        collector = FSEventsCollector(output_dir, verify_hashes=False)

        result = collector.collect(volume)

        assert result.success is True
        assert result.files_copied == 1
        assert len(result.checksums) == 0  # No checksums calculated

    def test_collect_all_volumes(self, tmp_path):
        """Test collecting from multiple volumes."""
        volumes = []

        for i in range(3):
            volume_root = tmp_path / f"volume{i}"
            volume_root.mkdir()

            fsevents_dir = volume_root / ".fseventsd"
            fsevents_dir.mkdir()
            (fsevents_dir / f"file{i}").write_text(f"data {i}")

            volumes.append(VolumeInfo(
                name=f"Volume{i}",
                mount_point=volume_root,
                filesystem_type="apfs",
                device_node=f"/dev/disk{i}s1",
                total_size=500000000000,
                available_size=250000000000,
                encryption_enabled=False
            ))

        output_dir = tmp_path / "output"
        collector = FSEventsCollector(output_dir)

        results = collector.collect_all_volumes(volumes)

        assert len(results) == 3
        assert all(r.success for r in results)
        assert sum(r.files_copied for r in results) == 3

    def test_acquisition_log_creation(self, tmp_path):
        """Test that acquisition log is created."""
        volume_root = tmp_path / "volume"
        volume_root.mkdir()

        fsevents_dir = volume_root / ".fseventsd"
        fsevents_dir.mkdir()
        (fsevents_dir / "testfile").write_text("test data")

        volume = VolumeInfo(
            name="TestVolume",
            mount_point=volume_root,
            filesystem_type="apfs",
            device_node="/dev/disk3s1",
            total_size=500000000000,
            available_size=250000000000,
            encryption_enabled=True
        )

        output_dir = tmp_path / "output"
        collector = FSEventsCollector(output_dir)

        result = collector.collect(volume, create_log=True)

        # Check if acquisition log exists
        log_file = result.output_directory.parent / "acquisition_log.json"
        assert log_file.exists()

        # Verify log content
        import json
        with open(log_file) as f:
            log_data = json.load(f)

        assert 'tool' in log_data
        assert log_data['tool']['name'] == 'mFAA'
        assert 'acquisition' in log_data
        assert 'volume' in log_data
        assert log_data['volume']['name'] == 'TestVolume'
        assert log_data['volume']['encryption_enabled'] is True
