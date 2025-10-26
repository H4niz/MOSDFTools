"""
Volume Scanner
==============

Scan and identify APFS volumes on macOS.
"""

import subprocess
import plistlib
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from mfaa.models import VolumeInfo
from mfaa.utils.logger import setup_logger
from mfaa.utils.exceptions import CollectionError

logger = setup_logger(__name__)


class VolumeScanner:
    """Scan and identify APFS volumes."""

    def __init__(self):
        """Initialize VolumeScanner."""
        self._check_diskutil_available()

    def _check_diskutil_available(self) -> None:
        """
        Check if diskutil command is available.

        Raises:
            CollectionError: If diskutil is not available
        """
        try:
            subprocess.run(
                ['which', 'diskutil'],
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError:
            raise CollectionError(
                "diskutil command not found. This tool requires macOS."
            )

    def scan_volumes(self) -> List[VolumeInfo]:
        """
        Scan all mounted volumes and return APFS volumes.

        Returns:
            List of VolumeInfo objects for APFS volumes

        Raises:
            OSError: If unable to scan volumes
        """
        logger.info("Scanning for APFS volumes...")
        volumes = []

        try:
            # Get list of all disks
            result = subprocess.run(
                ['diskutil', 'list', '-plist'],
                capture_output=True,
                check=True
            )

            # Parse plist
            plist_data = plistlib.loads(result.stdout)

            # Get all disks
            all_disks = plist_data.get('AllDisksAndPartitions', [])

            for disk in all_disks:
                # Check if disk has APFS containers
                if 'APFSVolumes' in disk:
                    for apfs_vol in disk['APFSVolumes']:
                        mount_point = apfs_vol.get('MountPoint')
                        if mount_point:
                            try:
                                vol_info = self.get_volume_info(mount_point)
                                volumes.append(vol_info)
                                logger.debug(f"Found APFS volume: {vol_info.name}")
                            except Exception as e:
                                logger.warning(f"Failed to get info for {mount_point}: {e}")

                # Also check partitions for APFS
                for partition in disk.get('Partitions', []):
                    if partition.get('Content', '').startswith('Apple_APFS'):
                        mount_point = partition.get('MountPoint')
                        if mount_point:
                            try:
                                vol_info = self.get_volume_info(mount_point)
                                if vol_info not in volumes:  # Avoid duplicates
                                    volumes.append(vol_info)
                                    logger.debug(f"Found APFS volume: {vol_info.name}")
                            except Exception as e:
                                logger.warning(f"Failed to get info for {mount_point}: {e}")

            logger.info(f"Found {len(volumes)} APFS volumes")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to scan volumes: {e}")
            raise OSError(f"Volume scan failed: {e}")
        except Exception as e:
            logger.error(f"Error parsing volume list: {e}")
            raise OSError(f"Volume parsing failed: {e}")

        return volumes

    def get_volume_info(self, mount_point: str) -> VolumeInfo:
        """
        Get detailed information about a specific volume.

        Args:
            mount_point: Path to volume mount point

        Returns:
            VolumeInfo object with volume details

        Raises:
            ValueError: If mount point is invalid
            OSError: If unable to get volume info
        """
        mount_path = Path(mount_point)

        if not mount_path.exists():
            raise ValueError(f"Mount point does not exist: {mount_point}")

        logger.debug(f"Getting info for volume: {mount_point}")

        try:
            # Use diskutil to get volume info
            result = subprocess.run(
                ['diskutil', 'info', '-plist', str(mount_path)],
                capture_output=True,
                check=True
            )

            # Parse plist output
            plist_data = plistlib.loads(result.stdout)

            # Extract volume information
            name = plist_data.get('VolumeName', '') or plist_data.get('MediaName', 'Unknown')
            filesystem_type = plist_data.get('FilesystemType', 'unknown').lower()
            device_node = plist_data.get('DeviceIdentifier', '')

            # Get size information
            total_size = plist_data.get('TotalSize', 0)
            free_space = plist_data.get('FreeSpace', 0)
            available_size = plist_data.get('AvailableSpace', free_space)

            # Check encryption status
            encryption_enabled = plist_data.get('Encrypted', False) or \
                               plist_data.get('FileVault', False)

            return VolumeInfo(
                name=name,
                mount_point=mount_path,
                filesystem_type=filesystem_type,
                device_node=device_node,
                total_size=total_size,
                available_size=available_size,
                encryption_enabled=encryption_enabled
            )

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get volume info: {e}")
            raise OSError(f"Volume info failed: {e}")
        except Exception as e:
            logger.error(f"Error parsing volume info: {e}")
            raise OSError(f"Volume info parsing failed: {e}")

    def get_all_mount_points(self) -> List[Path]:
        """
        Get all mounted volumes' mount points.

        Returns:
            List of Path objects for all mount points
        """
        mount_points = []

        try:
            # Get all mounted volumes using df
            result = subprocess.run(
                ['df', '-h'],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse df output (skip header)
            for line in result.stdout.split('\n')[1:]:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 6:
                        mount_point = ' '.join(parts[5:])  # Handle spaces in path
                        mount_points.append(Path(mount_point))

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get mount points: {e}")

        return mount_points

    def is_apfs_volume(self, mount_point: Path) -> bool:
        """
        Check if a mount point is an APFS volume.

        Args:
            mount_point: Path to check

        Returns:
            True if APFS volume, False otherwise
        """
        try:
            volume_info = self.get_volume_info(str(mount_point))
            return volume_info.filesystem_type.lower() == "apfs"
        except (ValueError, OSError):
            return False

    def get_fsevents_path(self, volume: VolumeInfo) -> Optional[Path]:
        """
        Get FSEvents database path for a volume.

        Args:
            volume: VolumeInfo object

        Returns:
            Path to .fseventsd directory, or None if not found
        """
        fsevents_path = volume.mount_point / '.fseventsd'

        if fsevents_path.exists() and fsevents_path.is_dir():
            return fsevents_path

        logger.warning(f"FSEvents directory not found for {volume.name}")
        return None
