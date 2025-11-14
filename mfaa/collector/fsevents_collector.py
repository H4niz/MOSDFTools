"""
FSEvents Collector
==================

Collect FSEvents database from APFS volumes.
"""

import shutil
import json
import socket
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from mfaa.models import VolumeInfo, CollectionResult
from mfaa.collector.hash_calculator import HashCalculator
from mfaa.utils.logger import setup_logger
from mfaa.utils.exceptions import CollectionError, PermissionError
from mfaa.utils.macos_helper import MacOSHelper

logger = setup_logger(__name__)


class FSEventsCollector:
    """Collect FSEvents database from volumes."""

    FSEVENTS_DIR = ".fseventsd"
    ACQUISITION_LOG = "acquisition_log.json"

    def __init__(self, output_dir: Path, verify_hashes: bool = True):
        """
        Initialize FSEvents collector.

        Args:
            output_dir: Directory to store collected artifacts
            verify_hashes: Calculate SHA-256 hashes for verification
        """
        self.output_dir = output_dir
        self.verify_hashes = verify_hashes
        self.hash_calculator = HashCalculator() if verify_hashes else None
        self.hostname = socket.gethostname()

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"FSEvents collector initialized. Output: {output_dir}")

    def collect(self, volume: VolumeInfo, create_log: bool = True) -> CollectionResult:
        """
        Collect FSEvents database from a volume.

        Args:
            volume: VolumeInfo object from VolumeScanner
            create_log: Create acquisition log (default: True)

        Returns:
            CollectionResult with collection details

        Raises:
            PermissionError: Insufficient permissions to access FSEvents
            CollectionError: Error during collection
        """
        logger.info(f"Collecting FSEvents from: {volume.mount_point}")

        # Use macOS helper to get correct FSEvents paths based on OS version
        possible_paths = MacOSHelper.get_fsevents_paths(volume.mount_point)

        # Try to find FSEvents in possible locations
        fsevents_path = None
        for path in possible_paths:
            if path.exists():
                fsevents_path = path
                if path != volume.mount_point / self.FSEVENTS_DIR:
                    logger.info(f"Using alternative FSEvents location: {fsevents_path}")
                break

        if not fsevents_path:
            # Get macOS version info for better error message
            try:
                version = MacOSHelper.get_macos_version()
                version_info = f" (macOS {version.name} {version.version_string})"
            except:
                version_info = ""

            raise CollectionError(
                f"FSEvents directory not found{version_info}. "
                f"Searched: {', '.join(str(p) for p in possible_paths)}. "
                f"Ensure you have proper permissions (try with sudo)."
            )

        # Check read permissions
        if not fsevents_path.is_dir():
            raise CollectionError(f"Not a directory: {fsevents_path}")

        # Verify we can read the directory
        try:
            list(fsevents_path.iterdir())
        except PermissionError as e:
            raise PermissionError(
                f"Permission denied accessing {fsevents_path}. "
                "FSEvents collection requires root privileges."
            )

        # Create output subdirectory for this volume
        volume_output = self.output_dir / volume.name / self.FSEVENTS_DIR
        volume_output.mkdir(parents=True, exist_ok=True)

        files_copied = 0
        total_size = 0
        checksums = {}
        errors = []
        file_details = []

        collection_start = datetime.now()

        try:
            # Copy FSEvents files
            for item in fsevents_path.iterdir():
                if item.is_file():
                    try:
                        dest = volume_output / item.name

                        # Get original file stats before copying
                        original_stat = item.stat()
                        original_mtime = datetime.fromtimestamp(original_stat.st_mtime)
                        file_size = original_stat.st_size

                        # Copy file with preserved metadata
                        shutil.copy2(item, dest)

                        files_copied += 1
                        total_size += file_size

                        # Calculate hash if requested
                        file_hash = None
                        if self.verify_hashes:
                            file_hash = self.hash_calculator.calculate_sha256(dest)
                            checksums[item.name] = file_hash
                            logger.debug(f"Copied: {item.name} ({file_size} bytes, SHA-256: {file_hash})")
                        else:
                            logger.debug(f"Copied: {item.name} ({file_size} bytes)")

                        # Record file details for acquisition log
                        file_details.append({
                            'filename': item.name,
                            'size': file_size,
                            'modified_time': original_mtime.isoformat(),
                            'sha256': file_hash
                        })

                    except PermissionError as e:
                        error_msg = f"Permission denied: {item.name}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                    except Exception as e:
                        error_msg = f"Failed to copy {item.name}: {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)

            collection_end = datetime.now()
            logger.info(f"Collection complete. Files: {files_copied}, Size: {total_size} bytes")

            result = CollectionResult(
                volume=volume,
                collection_time=collection_end,
                output_directory=volume_output,
                files_copied=files_copied,
                total_size=total_size,
                checksums=checksums,
                errors=errors,
                success=len(errors) == 0
            )

            # Create acquisition log
            if create_log:
                self._create_acquisition_log(
                    volume=volume,
                    result=result,
                    collection_start=collection_start,
                    collection_end=collection_end,
                    file_details=file_details
                )

            return result

        except OSError as e:
            if e.errno == 13:  # Permission denied
                raise PermissionError(
                    f"Permission denied accessing {fsevents_path}. "
                    "FSEvents collection requires root privileges."
                )
            raise CollectionError(f"Collection failed: {e}")

    def _create_acquisition_log(
        self,
        volume: VolumeInfo,
        result: CollectionResult,
        collection_start: datetime,
        collection_end: datetime,
        file_details: List[dict]
    ) -> None:
        """
        Create acquisition log for chain of custody.

        Args:
            volume: VolumeInfo object
            result: CollectionResult object
            collection_start: Collection start time
            collection_end: Collection end time
            file_details: List of file detail dictionaries
        """
        log_path = result.output_directory.parent / self.ACQUISITION_LOG

        acquisition_log = {
            'tool': {
                'name': 'mFAA',
                'version': '1.0.0',
                'description': 'macOS Forensics Artifacts Analyzer'
            },
            'acquisition': {
                'hostname': self.hostname,
                'collection_start': collection_start.isoformat(),
                'collection_end': collection_end.isoformat(),
                'duration_seconds': (collection_end - collection_start).total_seconds(),
                'success': result.success
            },
            'volume': {
                'name': volume.name,
                'mount_point': str(volume.mount_point),
                'filesystem_type': volume.filesystem_type,
                'device_node': volume.device_node,
                'total_size': volume.total_size,
                'available_size': volume.available_size,
                'encryption_enabled': volume.encryption_enabled
            },
            'collection_summary': {
                'files_collected': result.files_copied,
                'total_bytes': result.total_size,
                'output_directory': str(result.output_directory),
                'errors_count': len(result.errors),
                'errors': result.errors
            },
            'files': file_details,
            'verification': {
                'hash_algorithm': 'SHA-256' if self.verify_hashes else 'None',
                'checksums': result.checksums
            }
        }

        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(acquisition_log, f, indent=2, ensure_ascii=False)
            logger.info(f"Acquisition log created: {log_path}")
        except Exception as e:
            logger.error(f"Failed to create acquisition log: {e}")

    def collect_all_volumes(self, volumes: List[VolumeInfo]) -> List[CollectionResult]:
        """
        Collect from all provided volumes.

        Args:
            volumes: List of VolumeInfo objects

        Returns:
            List of CollectionResult objects
        """
        results = []

        logger.info(f"Starting collection from {len(volumes)} volumes")

        for idx, volume in enumerate(volumes, 1):
            logger.info(f"Processing volume {idx}/{len(volumes)}: {volume.name}")

            try:
                result = self.collect(volume)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to collect from {volume.name}: {e}")
                # Create failed result
                results.append(CollectionResult(
                    volume=volume,
                    collection_time=datetime.now(),
                    output_directory=self.output_dir / volume.name,
                    files_copied=0,
                    total_size=0,
                    checksums={},
                    errors=[str(e)],
                    success=False
                ))

        # Summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_files = sum(r.files_copied for r in results)
        total_bytes = sum(r.total_size for r in results)

        logger.info(f"Collection complete: {successful} successful, {failed} failed")
        logger.info(f"Total: {total_files} files, {total_bytes} bytes")

        return results
