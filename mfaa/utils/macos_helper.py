"""
macOS Helper
============

Utilities for detecting macOS version and determining correct artifact paths.
"""

import platform
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass
from mfaa.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class MacOSVersion:
    """macOS version information."""
    major: int
    minor: int
    patch: int
    name: str
    build: str

    @property
    def version_string(self) -> str:
        """Get version as string (e.g., '14.6.0')."""
        return f"{self.major}.{self.minor}.{self.patch}"

    @property
    def is_catalina_or_later(self) -> bool:
        """Check if macOS Catalina (10.15) or later."""
        return self.major >= 11 or (self.major == 10 and self.minor >= 15)

    @property
    def is_big_sur_or_later(self) -> bool:
        """Check if macOS Big Sur (11.0) or later."""
        return self.major >= 11

    @property
    def has_read_only_system_volume(self) -> bool:
        """Check if system uses read-only system volume (Catalina+)."""
        return self.is_catalina_or_later

    @property
    def has_data_volume_separation(self) -> bool:
        """Check if system/data volumes are separated (Catalina+)."""
        return self.is_catalina_or_later


class MacOSHelper:
    """Helper for macOS-specific operations and path detection."""

    # macOS version name mapping
    VERSION_NAMES = {
        15: "Sequoia",
        14: "Sonoma",
        13: "Ventura",
        12: "Monterey",
        11: "Big Sur",
        10: {
            15: "Catalina",
            14: "Mojave",
            13: "High Sierra",
            12: "Sierra",
            11: "El Capitan",
            10: "Yosemite",
        }
    }

    # Artifact paths for different macOS versions
    FSEVENTS_PATHS = {
        'modern': [  # Catalina (10.15) and later
            Path('/System/Volumes/Data/.fseventsd'),
            Path('/.fseventsd'),  # Fallback
        ],
        'legacy': [  # Mojave and earlier
            Path('/.fseventsd'),
        ]
    }

    SPOTLIGHT_PATHS = {
        'modern': [
            Path('/System/Volumes/Data/.Spotlight-V100'),
            Path('/.Spotlight-V100'),
        ],
        'legacy': [
            Path('/.Spotlight-V100'),
        ]
    }

    TCC_DATABASE_PATHS = {
        'modern': [
            Path('/Library/Application Support/com.apple.TCC/TCC.db'),
            Path('/System/Volumes/Data/Library/Application Support/com.apple.TCC/TCC.db'),
        ],
        'legacy': [
            Path('/Library/Application Support/com.apple.TCC/TCC.db'),
        ]
    }

    @staticmethod
    def get_macos_version() -> MacOSVersion:
        """
        Get macOS version information.

        Returns:
            MacOSVersion object with version details

        Raises:
            OSError: If unable to determine macOS version
        """
        try:
            # Get version from sw_vers command
            result = subprocess.run(
                ['sw_vers', '-productVersion'],
                capture_output=True,
                text=True,
                check=True
            )

            version_str = result.stdout.strip()
            parts = version_str.split('.')

            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0

            # Get build number
            build_result = subprocess.run(
                ['sw_vers', '-buildVersion'],
                capture_output=True,
                text=True,
                check=True
            )
            build = build_result.stdout.strip()

            # Determine version name
            if major in MacOSHelper.VERSION_NAMES:
                if isinstance(MacOSHelper.VERSION_NAMES[major], dict):
                    name = MacOSHelper.VERSION_NAMES[major].get(minor, f"macOS {major}.{minor}")
                else:
                    name = MacOSHelper.VERSION_NAMES[major]
            else:
                name = f"macOS {major}"

            version = MacOSVersion(
                major=major,
                minor=minor,
                patch=patch,
                name=name,
                build=build
            )

            logger.info(f"Detected {version.name} {version.version_string} (Build {version.build})")
            return version

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get macOS version: {e}")
            raise OSError(f"Could not determine macOS version: {e}")
        except (ValueError, IndexError) as e:
            logger.error(f"Failed to parse macOS version: {e}")
            raise OSError(f"Could not parse macOS version: {e}")

    @staticmethod
    def get_fsevents_paths(volume_mount_point: Path) -> List[Path]:
        """
        Get possible FSEvents paths for a volume.

        Args:
            volume_mount_point: Volume mount point path

        Returns:
            List of possible FSEvents paths, ordered by likelihood
        """
        version = MacOSHelper.get_macos_version()

        if version.has_data_volume_separation:
            # Modern macOS (Catalina+)
            if str(volume_mount_point) == '/':
                # Root volume - check Data volume first
                return [
                    Path('/System/Volumes/Data/.fseventsd'),
                    volume_mount_point / '.fseventsd',
                ]
            else:
                # Other volumes
                return [volume_mount_point / '.fseventsd']
        else:
            # Legacy macOS
            return [volume_mount_point / '.fseventsd']

    @staticmethod
    def get_spotlight_paths(volume_mount_point: Path) -> List[Path]:
        """
        Get possible Spotlight database paths for a volume.

        Args:
            volume_mount_point: Volume mount point path

        Returns:
            List of possible Spotlight paths, ordered by likelihood
        """
        version = MacOSHelper.get_macos_version()

        if version.has_data_volume_separation:
            if str(volume_mount_point) == '/':
                return [
                    Path('/System/Volumes/Data/.Spotlight-V100'),
                    volume_mount_point / '.Spotlight-V100',
                ]
            else:
                return [volume_mount_point / '.Spotlight-V100']
        else:
            return [volume_mount_point / '.Spotlight-V100']

    @staticmethod
    def get_tcc_database_path() -> List[Path]:
        """
        Get possible TCC database paths.

        Returns:
            List of possible TCC database paths, ordered by likelihood
        """
        version = MacOSHelper.get_macos_version()

        if version.is_catalina_or_later:
            return [
                Path('/Library/Application Support/com.apple.TCC/TCC.db'),
                Path('/System/Volumes/Data/Library/Application Support/com.apple.TCC/TCC.db'),
            ]
        else:
            return [Path('/Library/Application Support/com.apple.TCC/TCC.db')]

    @staticmethod
    def get_user_tcc_database_path(username: Optional[str] = None) -> List[Path]:
        """
        Get user-specific TCC database paths.

        Args:
            username: Username (defaults to current user)

        Returns:
            List of possible user TCC database paths
        """
        if username:
            user_home = Path(f'/Users/{username}')
        else:
            user_home = Path.home()

        return [
            user_home / 'Library/Application Support/com.apple.TCC/TCC.db'
        ]

    @staticmethod
    def find_artifact(possible_paths: List[Path]) -> Optional[Path]:
        """
        Find first existing artifact from list of possible paths.

        Args:
            possible_paths: List of paths to check

        Returns:
            First existing path, or None if none exist
        """
        for path in possible_paths:
            if path.exists():
                logger.debug(f"Found artifact at: {path}")
                return path

        logger.debug(f"Artifact not found in any of: {[str(p) for p in possible_paths]}")
        return None

    @staticmethod
    def get_system_volume_info() -> dict:
        """
        Get system volume architecture information.

        Returns:
            Dictionary with volume architecture details
        """
        version = MacOSHelper.get_macos_version()

        info = {
            'macos_version': version.version_string,
            'macos_name': version.name,
            'build': version.build,
            'has_read_only_system': version.has_read_only_system_volume,
            'has_data_volume_separation': version.has_data_volume_separation,
            'is_modern_macos': version.is_catalina_or_later,
        }

        # Check if Data volume exists
        data_volume = Path('/System/Volumes/Data')
        info['data_volume_exists'] = data_volume.exists()

        # Check system volume mount options
        try:
            result = subprocess.run(
                ['mount'],
                capture_output=True,
                text=True,
                check=True
            )

            for line in result.stdout.split('\n'):
                if ' on / ' in line:
                    info['root_mount_info'] = line.strip()
                    info['root_is_read_only'] = 'read-only' in line
                    break

        except subprocess.CalledProcessError as e:
            logger.warning(f"Could not get mount info: {e}")

        return info

    @staticmethod
    def suggest_volume_for_analysis() -> Tuple[Path, str]:
        """
        Suggest the best volume to analyze based on macOS version.

        Returns:
            Tuple of (volume_path, reason)
        """
        version = MacOSHelper.get_macos_version()

        if version.has_data_volume_separation:
            data_volume = Path('/System/Volumes/Data')
            if data_volume.exists():
                return (
                    data_volume,
                    f"Data volume recommended for {version.name} - contains user data and FSEvents"
                )

        return (
            Path('/'),
            "Root volume - standard analysis target"
        )


def get_recommended_artifact_paths(artifact_type: str, volume_mount_point: Path = Path('/')) -> List[Path]:
    """
    Get recommended paths for a specific artifact type.

    Args:
        artifact_type: Type of artifact ('fsevents', 'spotlight', 'tcc', etc.)
        volume_mount_point: Volume mount point

    Returns:
        List of recommended paths for the artifact

    Example:
        >>> paths = get_recommended_artifact_paths('fsevents', Path('/'))
        >>> print(paths)
        [Path('/System/Volumes/Data/.fseventsd'), Path('/.fseventsd')]
    """
    helper = MacOSHelper()

    artifact_getters = {
        'fsevents': lambda: helper.get_fsevents_paths(volume_mount_point),
        'spotlight': lambda: helper.get_spotlight_paths(volume_mount_point),
        'tcc': lambda: helper.get_tcc_database_path(),
    }

    getter = artifact_getters.get(artifact_type.lower())
    if getter:
        return getter()

    logger.warning(f"Unknown artifact type: {artifact_type}")
    return []
