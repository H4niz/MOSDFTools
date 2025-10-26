"""
Base Reporter
=============

Abstract base class for all reporters.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from mfaa.models import Timeline
from mfaa.utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseReporter(ABC):
    """Abstract base class for report generators."""

    def __init__(self, include_metadata: bool = True):
        """
        Initialize BaseReporter.

        Args:
            include_metadata: Include generation metadata in reports
        """
        self.include_metadata = include_metadata
        logger.debug(f"{self.__class__.__name__} initialized")

    @abstractmethod
    def generate(
        self,
        timeline: Timeline,
        output_path: Path,
        **kwargs
    ) -> None:
        """
        Generate report from timeline.

        Args:
            timeline: Timeline object to report on
            output_path: Path to save report
            **kwargs: Additional reporter-specific options
        """
        pass

    def _prepare_metadata(self, timeline: Timeline) -> Dict[str, Any]:
        """
        Prepare metadata for report.

        Args:
            timeline: Timeline object

        Returns:
            Dictionary with metadata
        """
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'generator': self.__class__.__name__,
            'version': '1.0.0'
        }

        # Add timeline metadata
        if timeline.info:
            metadata['timeline_info'] = timeline.info

        return metadata

    def _validate_timeline(self, timeline: Timeline) -> None:
        """
        Validate timeline before reporting.

        Args:
            timeline: Timeline object to validate

        Raises:
            ValueError: If timeline is invalid
        """
        if not isinstance(timeline, Timeline):
            raise ValueError(f"Expected Timeline object, got {type(timeline)}")

        if not timeline.entries:
            logger.warning("Timeline has no entries")

    def _ensure_output_directory(self, output_path: Path) -> None:
        """
        Ensure output directory exists.

        Args:
            output_path: Output file path
        """
        output_dir = output_path.parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created output directory: {output_dir}")

    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def get_report_info(self, output_path: Path) -> Dict[str, Any]:
        """
        Get information about generated report.

        Args:
            output_path: Path to generated report

        Returns:
            Dictionary with report information
        """
        if not output_path.exists():
            return {'exists': False}

        stat = output_path.stat()
        return {
            'exists': True,
            'path': str(output_path.absolute()),
            'size': stat.st_size,
            'size_formatted': self._format_file_size(stat.st_size),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
