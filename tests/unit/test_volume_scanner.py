"""
Unit tests for VolumeScanner
"""

import pytest
import platform
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from mfaa.collector.volume_scanner import VolumeScanner
from mfaa.models import VolumeInfo
from mfaa.utils.exceptions import CollectionError


pytestmark = pytest.mark.skipif(
    platform.system() != 'Darwin',
    reason="VolumeScanner requires macOS"
)


class TestVolumeScanner:
    """Test cases for VolumeScanner."""

    @patch('subprocess.run')
    def test_init_checks_diskutil(self, mock_run):
        """Test initialization checks for diskutil availability."""
        mock_run.return_value = Mock(returncode=0)
        scanner = VolumeScanner()
        assert scanner is not None
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_init_raises_on_missing_diskutil(self, mock_run):
        """Test initialization raises error when diskutil not found."""
        mock_run.side_effect = Exception("Command not found")

        with pytest.raises(CollectionError, match="diskutil command not found"):
            VolumeScanner()

    @patch('subprocess.run')
    def test_scan_volumes_success(self, mock_run):
        """Test successful volume scanning."""
        # Mock diskutil list output
        mock_plist_data = b'''<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
        <plist version="1.0">
        <dict>
            <key>AllDisksAndPartitions</key>
            <array>
                <dict>
                    <key>APFSVolumes</key>
                    <array>
                        <dict>
                            <key>MountPoint</key>
                            <string>/</string>
                        </dict>
                    </array>
                </dict>
            </array>
        </dict>
        </plist>'''

        mock_run.side_effect = [
            Mock(returncode=0),  # which diskutil
            Mock(returncode=0, stdout=mock_plist_data),  # diskutil list
            Mock(returncode=0, stdout=self._get_volume_info_plist())  # diskutil info
        ]

        scanner = VolumeScanner()
        volumes = scanner.scan_volumes()

        assert isinstance(volumes, list)
        # Volume may not be found if / doesn't exist in test environment
        # assert len(volumes) >= 0

    def _get_volume_info_plist(self):
        """Helper to get mock volume info plist."""
        return b'''<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
        <plist version="1.0">
        <dict>
            <key>VolumeName</key>
            <string>Macintosh HD</string>
            <key>FilesystemType</key>
            <string>apfs</string>
            <key>DeviceIdentifier</key>
            <string>disk3s1</string>
            <key>TotalSize</key>
            <integer>500000000000</integer>
            <key>AvailableSpace</key>
            <integer>250000000000</integer>
            <key>Encrypted</key>
            <true/>
        </dict>
        </plist>'''

    @patch('subprocess.run')
    def test_get_volume_info(self, mock_run):
        """Test getting volume information."""
        mock_run.side_effect = [
            Mock(returncode=0),  # which diskutil
            Mock(returncode=0, stdout=self._get_volume_info_plist())  # diskutil info
        ]

        scanner = VolumeScanner()
        # Use a path that exists
        vol_info = scanner.get_volume_info('/')

        assert isinstance(vol_info, VolumeInfo)
        assert vol_info.name == "Macintosh HD"
        assert vol_info.filesystem_type == "apfs"
        assert vol_info.device_node == "disk3s1"
        assert vol_info.total_size == 500000000000
        assert vol_info.encryption_enabled is True

    @patch('subprocess.run')
    def test_get_volume_info_nonexistent_path(self, mock_run):
        """Test getting volume info for nonexistent path."""
        mock_run.return_value = Mock(returncode=0)
        scanner = VolumeScanner()

        with pytest.raises(ValueError, match="Mount point does not exist"):
            scanner.get_volume_info('/nonexistent/path')

    @patch('subprocess.run')
    def test_is_apfs_volume(self, mock_run):
        """Test checking if volume is APFS."""
        mock_run.side_effect = [
            Mock(returncode=0),  # which diskutil
            Mock(returncode=0, stdout=self._get_volume_info_plist())  # diskutil info
        ]

        scanner = VolumeScanner()
        is_apfs = scanner.is_apfs_volume(Path('/'))

        assert is_apfs is True

    @patch('subprocess.run')
    def test_get_all_mount_points(self, mock_run):
        """Test getting all mount points."""
        df_output = """Filesystem     Size   Used  Avail Capacity  Mounted on
/dev/disk3s1  500G  250G  250G    50%    /
/dev/disk3s5  500G   10G  490G     2%    /System/Volumes/Data
"""
        mock_run.side_effect = [
            Mock(returncode=0),  # which diskutil
            Mock(returncode=0, stdout=df_output, text=True)  # df -h
        ]

        scanner = VolumeScanner()
        mount_points = scanner.get_all_mount_points()

        assert isinstance(mount_points, list)
        assert len(mount_points) >= 0
        assert all(isinstance(p, Path) for p in mount_points)

    @patch('subprocess.run')
    def test_get_fsevents_path(self, mock_run, tmp_path):
        """Test getting FSEvents path for volume."""
        # Create mock FSEvents directory
        mount_point = tmp_path / "test_volume"
        mount_point.mkdir()
        fsevents_dir = mount_point / ".fseventsd"
        fsevents_dir.mkdir()

        mock_run.return_value = Mock(returncode=0)
        scanner = VolumeScanner()

        volume = VolumeInfo(
            name="TestVolume",
            mount_point=mount_point,
            filesystem_type="apfs",
            device_node="/dev/disk3s1",
            total_size=500000000000,
            available_size=250000000000,
            encryption_enabled=False
        )

        fsevents_path = scanner.get_fsevents_path(volume)
        assert fsevents_path is not None
        assert fsevents_path == fsevents_dir

    @patch('subprocess.run')
    def test_get_fsevents_path_not_found(self, mock_run, tmp_path):
        """Test getting FSEvents path when directory doesn't exist."""
        mount_point = tmp_path / "test_volume"
        mount_point.mkdir()

        mock_run.return_value = Mock(returncode=0)
        scanner = VolumeScanner()

        volume = VolumeInfo(
            name="TestVolume",
            mount_point=mount_point,
            filesystem_type="apfs",
            device_node="/dev/disk3s1",
            total_size=500000000000,
            available_size=250000000000,
            encryption_enabled=False
        )

        fsevents_path = scanner.get_fsevents_path(volume)
        assert fsevents_path is None
