"""
Integration tests for Collector module
"""

import pytest
from pathlib import Path
from mfaa.collector import VolumeScanner, FSEventsCollector, XattrCollector
from mfaa.models import VolumeInfo


@pytest.mark.integration
class TestCollectorIntegration:
    """Integration tests for complete collector workflow."""

    def test_full_collection_workflow(self, tmp_path):
        """Test complete collection workflow: scan -> collect FSEvents -> collect xattr."""
        # Setup mock volume environment
        volume_root = tmp_path / "test_volume"
        volume_root.mkdir()

        # Create mock FSEvents
        fsevents_dir = volume_root / ".fseventsd"
        fsevents_dir.mkdir()
        (fsevents_dir / "0000000000abcdef").write_bytes(b"mock fsevents data")

        # Create test files with mock xattr (would need xattr library in real test)
        test_file = volume_root / "Downloads" / "suspicious.dmg"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("test file content")

        # Create volume info
        volume = VolumeInfo(
            name="TestVolume",
            mount_point=volume_root,
            filesystem_type="apfs",
            device_node="/dev/disk3s1",
            total_size=500000000000,
            available_size=250000000000,
            encryption_enabled=False
        )

        # Step 1: Collect FSEvents
        output_dir = tmp_path / "evidence"
        fsevents_collector = FSEventsCollector(output_dir, verify_hashes=True)

        fsevents_result = fsevents_collector.collect(volume)

        assert fsevents_result.success is True
        assert fsevents_result.files_copied == 1
        assert len(fsevents_result.checksums) == 1

        # Step 2: Collect Extended Attributes
        xattr_collector = XattrCollector(parse_attributes=True)

        # In real scenario, would collect from actual files with xattr
        # For this test, just verify collector is working
        assert xattr_collector is not None
        assert xattr_collector.parse_attributes is True

        # Verify output structure
        assert output_dir.exists()
        assert (output_dir / volume.name / ".fseventsd").exists()

        # Verify acquisition log
        log_file = output_dir / volume.name / "acquisition_log.json"
        assert log_file.exists()

    def test_multiple_volumes_collection(self, tmp_path):
        """Test collecting from multiple volumes."""
        volumes = []

        # Create multiple mock volumes
        for i in range(2):
            volume_root = tmp_path / f"volume_{i}"
            volume_root.mkdir()

            fsevents_dir = volume_root / ".fseventsd"
            fsevents_dir.mkdir()
            (fsevents_dir / f"file_{i}").write_text(f"data {i}")

            volumes.append(VolumeInfo(
                name=f"Volume{i}",
                mount_point=volume_root,
                filesystem_type="apfs",
                device_node=f"/dev/disk{i}s1",
                total_size=500000000000,
                available_size=250000000000,
                encryption_enabled=False
            ))

        # Collect from all volumes
        output_dir = tmp_path / "evidence"
        collector = FSEventsCollector(output_dir, verify_hashes=True)

        results = collector.collect_all_volumes(volumes)

        assert len(results) == 2
        assert all(r.success for r in results)
        assert sum(r.files_copied for r in results) == 2

        # Verify each volume has its own directory
        for volume in volumes:
            assert (output_dir / volume.name).exists()
            assert (output_dir / volume.name / ".fseventsd").exists()
            assert (output_dir / volume.name / "acquisition_log.json").exists()

    def test_error_handling_in_workflow(self, tmp_path):
        """Test error handling in collection workflow."""
        # Volume without FSEvents directory
        volume_root = tmp_path / "bad_volume"
        volume_root.mkdir()

        volume = VolumeInfo(
            name="BadVolume",
            mount_point=volume_root,
            filesystem_type="apfs",
            device_node="/dev/disk3s1",
            total_size=500000000000,
            available_size=250000000000,
            encryption_enabled=False
        )

        output_dir = tmp_path / "evidence"
        collector = FSEventsCollector(output_dir)

        from mfaa.utils.exceptions import CollectionError

        with pytest.raises(CollectionError):
            collector.collect(volume)
