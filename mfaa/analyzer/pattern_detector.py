"""
Pattern Detector
================

Detect suspicious patterns in FSEvents (ransomware, exfiltration, etc.).
"""

from datetime import timedelta
from collections import defaultdict
from typing import List, Dict, Set
from pathlib import Path
from mfaa.models import FSEvent, Pattern, EventType
from mfaa.utils.logger import setup_logger

logger = setup_logger(__name__)


class PatternDetector:
    """Detect suspicious activity patterns in events."""

    # Configuration thresholds
    MASS_DELETION_THRESHOLD = 50  # files
    MASS_DELETION_TIME_WINDOW = 60  # seconds
    RANSOMWARE_RENAME_THRESHOLD = 20  # files
    EXFILTRATION_SIZE_THRESHOLD = 100 * 1024 * 1024  # 100MB
    RAPID_ACCESS_THRESHOLD = 100  # files
    RAPID_ACCESS_TIME_WINDOW = 10  # seconds

    def __init__(self):
        """Initialize PatternDetector."""
        logger.info("PatternDetector initialized")

    def detect_all_patterns(self, events: List[FSEvent]) -> List[Pattern]:
        """
        Detect all suspicious patterns in events.

        Args:
            events: List of FSEvent objects

        Returns:
            List of Pattern objects
        """
        logger.info(f"Analyzing {len(events)} events for patterns...")

        patterns = []

        # Sort events by timestamp for temporal analysis
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Detect various patterns
        patterns.extend(self.detect_mass_deletion(sorted_events))
        patterns.extend(self.detect_ransomware_encryption(sorted_events))
        patterns.extend(self.detect_data_exfiltration(sorted_events))
        patterns.extend(self.detect_persistence_mechanisms(sorted_events))
        patterns.extend(self.detect_rapid_file_access(sorted_events))

        logger.info(f"Detected {len(patterns)} suspicious patterns")
        return patterns

    def detect_mass_deletion(self, events: List[FSEvent]) -> List[Pattern]:
        """
        Detect mass deletion patterns.

        Criteria: >50 files deleted in <60 seconds

        Args:
            events: Sorted list of FSEvent objects

        Returns:
            List of Pattern objects for mass deletions
        """
        patterns = []
        deletion_events = [e for e in events if e.is_removed]

        if len(deletion_events) < self.MASS_DELETION_THRESHOLD:
            return patterns

        logger.debug(f"Analyzing {len(deletion_events)} deletion events...")

        # Sliding window analysis
        for i in range(len(deletion_events)):
            window_events = []
            start_time = deletion_events[i].timestamp

            for j in range(i, len(deletion_events)):
                event = deletion_events[j]
                time_diff = (event.timestamp - start_time).total_seconds()

                if time_diff <= self.MASS_DELETION_TIME_WINDOW:
                    window_events.append(event)
                else:
                    break

            # Check if threshold exceeded
            if len(window_events) >= self.MASS_DELETION_THRESHOLD:
                pattern = Pattern(
                    pattern_type="mass_deletion",
                    severity="CRITICAL",
                    start_time=window_events[0].timestamp,
                    end_time=window_events[-1].timestamp,
                    event_count=len(window_events),
                    affected_paths=[e.path for e in window_events],
                    description=f"Mass deletion detected: {len(window_events)} files "
                               f"deleted in {time_diff:.1f} seconds",
                    indicators={
                        'deletion_rate': len(window_events) / time_diff,
                        'time_window': time_diff,
                        'unique_directories': len(set(e.path.parent for e in window_events))
                    }
                )
                patterns.append(pattern)

                logger.warning(f"Mass deletion detected: {len(window_events)} files")

                # Skip ahead to avoid overlapping patterns
                i = j
                break

        return patterns

    def detect_ransomware_encryption(self, events: List[FSEvent]) -> List[Pattern]:
        """
        Detect ransomware encryption patterns.

        Criteria:
        - Many files renamed to .encrypted, .locked, .crypt, etc.
        - Creation of ransom notes (README.txt, DECRYPT.txt, etc.)

        Args:
            events: Sorted list of FSEvent objects

        Returns:
            List of Pattern objects for ransomware activity
        """
        patterns = []

        # Suspicious extensions indicating encryption
        ransomware_extensions = {
            '.encrypted', '.locked', '.crypt', '.enc', '.vault',
            '.crypted', '.crypto', '.locky', '.cerber', '.zepto',
            '.aaa', '.xyz', '.zzz', '.xxx'
        }

        # Ransom note patterns
        ransom_note_patterns = {
            'readme', 'decrypt', 'recover', 'howto', 'help',
            'instructions', 'ransom', 'locked'
        }

        encrypted_files = []
        ransom_notes = []

        for event in events:
            # Check for encrypted file extensions
            if event.path.suffix.lower() in ransomware_extensions:
                encrypted_files.append(event)

            # Check for ransom notes
            file_name_lower = event.path.name.lower()
            if any(pattern in file_name_lower for pattern in ransom_note_patterns):
                if event.is_created:
                    ransom_notes.append(event)

        # Detect if threshold exceeded
        if len(encrypted_files) >= self.RANSOMWARE_RENAME_THRESHOLD:
            start_time = min(e.timestamp for e in encrypted_files)
            end_time = max(e.timestamp for e in encrypted_files)

            pattern = Pattern(
                pattern_type="ransomware_encryption",
                severity="CRITICAL",
                start_time=start_time,
                end_time=end_time,
                event_count=len(encrypted_files),
                affected_paths=[e.path for e in encrypted_files],
                description=f"Ransomware encryption detected: {len(encrypted_files)} files "
                           f"with suspicious extensions",
                indicators={
                    'encrypted_files': len(encrypted_files),
                    'ransom_notes': len(ransom_notes),
                    'ransom_note_paths': [str(e.path) for e in ransom_notes],
                    'extensions': list(set(e.path.suffix for e in encrypted_files))
                }
            )
            patterns.append(pattern)

            logger.warning(f"Ransomware pattern detected: {len(encrypted_files)} encrypted files")

        return patterns

    def detect_data_exfiltration(self, events: List[FSEvent]) -> List[Pattern]:
        """
        Detect data exfiltration patterns.

        Criteria:
        - Large files copied to external volumes
        - Multiple files archived (zip, tar, etc.)
        - Files copied to removable media

        Args:
            events: Sorted list of FSEvent objects

        Returns:
            List of Pattern objects for exfiltration activity
        """
        patterns = []

        # External/removable volume patterns
        external_volume_patterns = ['/Volumes/', '/media/', '/mnt/']

        # Archive extensions
        archive_extensions = {'.zip', '.tar', '.gz', '.bz2', '.7z', '.rar'}

        # Files copied to external volumes
        external_copies = []
        large_archives = []

        for event in events:
            path_str = str(event.path)

            # Check for copies to external volumes
            if any(pattern in path_str for pattern in external_volume_patterns):
                if event.is_created or event.is_modified:
                    external_copies.append(event)

            # Check for large archive creation
            if event.path.suffix.lower() in archive_extensions:
                if event.is_created:
                    large_archives.append(event)

        # Detect suspicious exfiltration
        if len(external_copies) >= 10:  # At least 10 files to external volume
            start_time = min(e.timestamp for e in external_copies)
            end_time = max(e.timestamp for e in external_copies)

            pattern = Pattern(
                pattern_type="data_exfiltration",
                severity="HIGH",
                start_time=start_time,
                end_time=end_time,
                event_count=len(external_copies),
                affected_paths=[e.path for e in external_copies],
                description=f"Potential data exfiltration: {len(external_copies)} files "
                           f"copied to external volume",
                indicators={
                    'files_to_external': len(external_copies),
                    'archive_files': len(large_archives),
                    'unique_volumes': len(set(e.path.parts[0:3] for e in external_copies))
                }
            )
            patterns.append(pattern)

            logger.warning(f"Exfiltration pattern detected: {len(external_copies)} files to external volume")

        return patterns

    def detect_persistence_mechanisms(self, events: List[FSEvent]) -> List[Pattern]:
        """
        Detect persistence mechanism creation.

        Criteria:
        - LaunchAgents/LaunchDaemons creation
        - Shell profile modifications (.bash_profile, .zshrc, etc.)
        - Startup items

        Args:
            events: Sorted list of FSEvent objects

        Returns:
            List of Pattern objects for persistence mechanisms
        """
        patterns = []

        persistence_paths = []

        for event in events:
            path_str = str(event.path)

            # Check for LaunchAgents/LaunchDaemons
            if 'LaunchAgents' in path_str or 'LaunchDaemons' in path_str:
                if event.is_created or event.is_modified:
                    persistence_paths.append(event)
                    continue

            # Check for shell profile modifications
            if any(profile in event.path.name for profile in
                   ['.bash_profile', '.zshrc', '.bashrc', '.profile', '.zprofile']):
                if event.is_modified or event.is_created:
                    persistence_paths.append(event)
                    continue

        # Create pattern if persistence mechanisms detected
        if persistence_paths:
            start_time = min(e.timestamp for e in persistence_paths)
            end_time = max(e.timestamp for e in persistence_paths)

            pattern = Pattern(
                pattern_type="persistence_mechanism",
                severity="HIGH",
                start_time=start_time,
                end_time=end_time,
                event_count=len(persistence_paths),
                affected_paths=[e.path for e in persistence_paths],
                description=f"Persistence mechanism detected: {len(persistence_paths)} "
                           f"persistence-related files modified/created",
                indicators={
                    'launch_agents': len([e for e in persistence_paths if 'LaunchAgent' in str(e.path)]),
                    'launch_daemons': len([e for e in persistence_paths if 'LaunchDaemon' in str(e.path)]),
                    'shell_profiles': len([e for e in persistence_paths if '.' in e.path.name])
                }
            )
            patterns.append(pattern)

            logger.warning(f"Persistence mechanism detected: {len(persistence_paths)} modifications")

        return patterns

    def detect_rapid_file_access(self, events: List[FSEvent]) -> List[Pattern]:
        """
        Detect rapid file access patterns.

        Criteria: Many files accessed in short time (possible automated scanning)

        Args:
            events: Sorted list of FSEvent objects

        Returns:
            List of Pattern objects for rapid access
        """
        patterns = []

        # Consider modification and creation events
        access_events = [e for e in events if e.is_modified or e.is_created]

        if len(access_events) < self.RAPID_ACCESS_THRESHOLD:
            return patterns

        # Sliding window analysis
        for i in range(len(access_events)):
            window_events = []
            start_time = access_events[i].timestamp

            for j in range(i, len(access_events)):
                event = access_events[j]
                time_diff = (event.timestamp - start_time).total_seconds()

                if time_diff <= self.RAPID_ACCESS_TIME_WINDOW:
                    window_events.append(event)
                else:
                    break

            # Check if threshold exceeded
            if len(window_events) >= self.RAPID_ACCESS_THRESHOLD:
                pattern = Pattern(
                    pattern_type="rapid_file_access",
                    severity="MEDIUM",
                    start_time=window_events[0].timestamp,
                    end_time=window_events[-1].timestamp,
                    event_count=len(window_events),
                    affected_paths=[e.path for e in window_events],
                    description=f"Rapid file access detected: {len(window_events)} files "
                               f"accessed in {time_diff:.1f} seconds",
                    indicators={
                        'access_rate': len(window_events) / time_diff,
                        'unique_extensions': len(set(e.path.suffix for e in window_events))
                    }
                )
                patterns.append(pattern)

                logger.info(f"Rapid access pattern: {len(window_events)} files in {time_diff:.1f}s")
                break

        return patterns
