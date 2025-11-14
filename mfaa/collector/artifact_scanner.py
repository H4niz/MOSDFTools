"""
Artifact Scanner
================

Scan macOS system for available forensic artifacts.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from mfaa.models import VolumeInfo
from mfaa.utils.logger import setup_logger
from mfaa.utils.exceptions import CollectionError

logger = setup_logger(__name__)


@dataclass
class ArtifactInfo:
    """Information about a forensic artifact."""
    name: str
    category: str  # "filesystem", "system", "application", "user"
    path: Path
    exists: bool
    readable: bool
    size: Optional[int] = None
    item_count: Optional[int] = None  # For directories
    description: str = ""
    collection_command: str = ""
    requires_root: bool = False


@dataclass
class ArtifactScanResult:
    """Result of artifact scanning."""
    volume: VolumeInfo
    scan_time: datetime
    artifacts: List[ArtifactInfo] = field(default_factory=list)
    total_found: int = 0
    accessible_count: int = 0

    def get_by_category(self, category: str) -> List[ArtifactInfo]:
        """Get artifacts by category."""
        return [a for a in self.artifacts if a.category == category]

    def get_accessible(self) -> List[ArtifactInfo]:
        """Get only accessible artifacts."""
        return [a for a in self.artifacts if a.exists and a.readable]


class ArtifactScanner:
    """Scan system for forensic artifacts."""

    # Define artifact locations to scan
    ARTIFACT_DEFINITIONS = [
        {
            'name': 'FSEvents Database',
            'category': 'filesystem',
            'path': '.fseventsd',
            'description': 'File system event logs tracking all file/directory changes',
            'collection_command': 'sudo mfaa collect --volume {volume} --output ./artifacts',
            'requires_root': True
        },
        {
            'name': 'FSEvents Database (Data Volume)',
            'category': 'filesystem',
            'path': 'System/Volumes/Data/.fseventsd',
            'description': 'FSEvents on APFS Data volume (macOS Big Sur+)',
            'collection_command': 'sudo mfaa collect --volume /System/Volumes/Data --output ./artifacts',
            'requires_root': True
        },
        {
            'name': 'Unified Logs',
            'category': 'system',
            'path': 'private/var/db/diagnostics',
            'description': 'System-wide logging (replaced ASL in 10.12+)',
            'collection_command': 'sudo log collect --output unified_logs.logarchive',
            'requires_root': True
        },
        {
            'name': 'System Logs (Legacy)',
            'category': 'system',
            'path': 'private/var/log',
            'description': 'Legacy system log files',
            'collection_command': 'sudo cp -r {path} ./artifacts/system_logs',
            'requires_root': True
        },
        {
            'name': 'Bash History',
            'category': 'user',
            'path': 'Users/*/.bash_history',
            'description': 'Shell command history for all users',
            'collection_command': 'cp {path} ./artifacts/bash_history',
            'requires_root': False
        },
        {
            'name': 'Zsh History',
            'category': 'user',
            'path': 'Users/*/.zsh_history',
            'description': 'Zsh shell command history',
            'collection_command': 'cp {path} ./artifacts/zsh_history',
            'requires_root': False
        },
        {
            'name': 'Recent Items',
            'category': 'user',
            'path': 'Users/*/Library/Application Support/com.apple.sharedfilelist',
            'description': 'Recently accessed files and applications',
            'collection_command': 'cp -r {path} ./artifacts/recent_items',
            'requires_root': False
        },
        {
            'name': 'Downloads Quarantine',
            'category': 'user',
            'path': 'Users/*/Library/Preferences/com.apple.LaunchServices.QuarantineEventsV2',
            'description': 'Database of downloaded files with URLs and timestamps',
            'collection_command': 'cp {path} ./artifacts/quarantine_events.db',
            'requires_root': False
        },
        {
            'name': 'Safari History',
            'category': 'application',
            'path': 'Users/*/Library/Safari/History.db',
            'description': 'Safari browsing history database',
            'collection_command': 'cp {path} ./artifacts/safari_history.db',
            'requires_root': False
        },
        {
            'name': 'Chrome History',
            'category': 'application',
            'path': 'Users/*/Library/Application Support/Google/Chrome/*/History',
            'description': 'Chrome browsing history',
            'collection_command': 'cp {path} ./artifacts/chrome_history.db',
            'requires_root': False
        },
        {
            'name': 'Spotlight Database',
            'category': 'system',
            'path': '.Spotlight-V100',
            'description': 'Spotlight index containing file content and properties',
            'collection_command': 'mdutil -E {volume}  # Export Spotlight data',
            'requires_root': True
        },
        {
            'name': 'Launch Agents',
            'category': 'system',
            'path': 'Library/LaunchAgents',
            'description': 'User-level persistence mechanisms',
            'collection_command': 'cp -r {path} ./artifacts/launch_agents',
            'requires_root': False
        },
        {
            'name': 'Launch Daemons',
            'category': 'system',
            'path': 'Library/LaunchDaemons',
            'description': 'System-level persistence mechanisms',
            'collection_command': 'cp -r {path} ./artifacts/launch_daemons',
            'requires_root': True
        },
        {
            'name': 'Installed Applications',
            'category': 'application',
            'path': 'Applications',
            'description': 'System-wide installed applications',
            'collection_command': 'ls -lR {path} > ./artifacts/applications_list.txt',
            'requires_root': False
        },
        {
            'name': 'User Applications',
            'category': 'application',
            'path': 'Users/*/Applications',
            'description': 'User-installed applications',
            'collection_command': 'ls -lR {path} > ./artifacts/user_applications_list.txt',
            'requires_root': False
        },
        {
            'name': 'Crash Reports',
            'category': 'system',
            'path': 'Library/Logs/DiagnosticReports',
            'description': 'Application and system crash reports',
            'collection_command': 'cp -r {path} ./artifacts/crash_reports',
            'requires_root': False
        },
        {
            'name': 'TCC Database',
            'category': 'system',
            'path': 'Library/Application Support/com.apple.TCC/TCC.db',
            'description': 'Transparency, Consent, and Control privacy permissions',
            'collection_command': 'cp {path} ./artifacts/tcc.db',
            'requires_root': True
        },
        {
            'name': 'KnowledgeC Database',
            'category': 'user',
            'path': 'Users/*/Library/Application Support/Knowledge/knowledgeC.db',
            'description': 'User activity database (app usage, device connections)',
            'collection_command': 'cp {path} ./artifacts/knowledgec.db',
            'requires_root': False
        }
    ]

    def __init__(self):
        """Initialize artifact scanner."""
        logger.info("Artifact scanner initialized")

    def scan_volume(self, volume: VolumeInfo) -> ArtifactScanResult:
        """
        Scan a volume for available artifacts.

        Args:
            volume: VolumeInfo object

        Returns:
            ArtifactScanResult with found artifacts
        """
        logger.info(f"Scanning artifacts on volume: {volume.mount_point}")

        scan_start = datetime.now()
        artifacts = []

        for artifact_def in self.ARTIFACT_DEFINITIONS:
            # Resolve path patterns (handle wildcards)
            artifact_paths = self._resolve_path(
                volume.mount_point,
                artifact_def['path']
            )

            for artifact_path in artifact_paths:
                artifact_info = self._check_artifact(
                    artifact_def,
                    artifact_path,
                    volume
                )
                artifacts.append(artifact_info)

        # Create result
        result = ArtifactScanResult(
            volume=volume,
            scan_time=scan_start,
            artifacts=artifacts,
            total_found=sum(1 for a in artifacts if a.exists),
            accessible_count=sum(1 for a in artifacts if a.exists and a.readable)
        )

        logger.info(
            f"Scan complete: {result.total_found} found, "
            f"{result.accessible_count} accessible"
        )

        return result

    def _resolve_path(self, volume_root: Path, path_pattern: str) -> List[Path]:
        """
        Resolve path patterns with wildcards.

        Args:
            volume_root: Volume mount point
            path_pattern: Path pattern (may contain wildcards)

        Returns:
            List of resolved paths
        """
        full_pattern = volume_root / path_pattern

        # If pattern contains wildcard
        if '*' in str(path_pattern):
            try:
                # Use glob to expand wildcards
                expanded = list(volume_root.glob(path_pattern))
                return expanded if expanded else [full_pattern]
            except Exception as e:
                logger.debug(f"Failed to expand pattern {path_pattern}: {e}")
                return [full_pattern]
        else:
            return [full_pattern]

    def _check_artifact(
        self,
        artifact_def: Dict[str, Any],
        path: Path,
        volume: VolumeInfo
    ) -> ArtifactInfo:
        """
        Check if artifact exists and is accessible.

        Args:
            artifact_def: Artifact definition dict
            path: Path to artifact
            volume: VolumeInfo object

        Returns:
            ArtifactInfo object
        """
        exists = path.exists()
        readable = False
        size = None
        item_count = None

        if exists:
            try:
                # Check readability
                if path.is_file():
                    with open(path, 'rb') as f:
                        f.read(1)  # Try to read 1 byte
                    readable = True
                    size = path.stat().st_size
                elif path.is_dir():
                    list(path.iterdir())  # Try to list directory
                    readable = True
                    item_count = sum(1 for _ in path.iterdir())
            except (PermissionError, OSError):
                readable = False

        # Format collection command with actual paths
        collection_cmd = artifact_def['collection_command'].format(
            volume=volume.mount_point,
            path=path
        )

        return ArtifactInfo(
            name=artifact_def['name'],
            category=artifact_def['category'],
            path=path,
            exists=exists,
            readable=readable,
            size=size,
            item_count=item_count,
            description=artifact_def['description'],
            collection_command=collection_cmd,
            requires_root=artifact_def['requires_root']
        )

    def scan_all_volumes(self, volumes: List[VolumeInfo]) -> List[ArtifactScanResult]:
        """
        Scan all volumes for artifacts.

        Args:
            volumes: List of VolumeInfo objects

        Returns:
            List of ArtifactScanResult objects
        """
        results = []

        logger.info(f"Scanning {len(volumes)} volumes for artifacts")

        for volume in volumes:
            try:
                result = self.scan_volume(volume)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to scan {volume.name}: {e}")

        return results

    def generate_collection_guide(
        self,
        scan_result: ArtifactScanResult
    ) -> Dict[str, Any]:
        """
        Generate a collection guide based on scan results.

        Args:
            scan_result: ArtifactScanResult object

        Returns:
            Dictionary with collection instructions
        """
        guide = {
            'volume': str(scan_result.volume.mount_point),
            'scan_time': scan_result.scan_time.isoformat(),
            'summary': {
                'total_artifacts': len(scan_result.artifacts),
                'found': scan_result.total_found,
                'accessible': scan_result.accessible_count,
                'requires_root': sum(
                    1 for a in scan_result.artifacts
                    if a.exists and a.requires_root
                )
            },
            'categories': {},
            'collection_steps': []
        }

        # Group by category
        for category in ['filesystem', 'system', 'application', 'user']:
            artifacts = scan_result.get_by_category(category)
            accessible = [a for a in artifacts if a.exists and a.readable]

            guide['categories'][category] = {
                'total': len(artifacts),
                'accessible': len(accessible),
                'artifacts': [
                    {
                        'name': a.name,
                        'path': str(a.path),
                        'exists': a.exists,
                        'readable': a.readable,
                        'size': a.size,
                        'description': a.description,
                        'requires_root': a.requires_root
                    }
                    for a in accessible
                ]
            }

        # Generate collection steps
        step_num = 1
        accessible_artifacts = scan_result.get_accessible()

        # Group by root requirement
        root_required = [a for a in accessible_artifacts if a.requires_root]
        no_root = [a for a in accessible_artifacts if not a.requires_root]

        if root_required:
            guide['collection_steps'].append({
                'step': step_num,
                'title': 'Collect artifacts requiring root privileges',
                'note': 'Run these commands with sudo',
                'commands': [
                    {
                        'artifact': a.name,
                        'command': a.collection_command
                    }
                    for a in root_required
                ]
            })
            step_num += 1

        if no_root:
            guide['collection_steps'].append({
                'step': step_num,
                'title': 'Collect user-accessible artifacts',
                'note': 'These can be collected without elevated privileges',
                'commands': [
                    {
                        'artifact': a.name,
                        'command': a.collection_command
                    }
                    for a in no_root
                ]
            })

        return guide
