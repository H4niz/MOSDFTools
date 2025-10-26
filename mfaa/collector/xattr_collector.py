"""
Extended Attributes Collector
==============================

Collect Extended Attributes from files.
"""

import os
import xattr
from pathlib import Path
from typing import List, Dict, Optional
from mfaa.models import XattrRecord
from mfaa.parser.xattr_parser import XattrParser
from mfaa.utils.logger import setup_logger
from mfaa.utils.exceptions import CollectionError

logger = setup_logger(__name__)


class XattrCollector:
    """Collect Extended Attributes from files."""

    def __init__(self, parse_attributes: bool = True):
        """
        Initialize XattrCollector.

        Args:
            parse_attributes: Parse attributes immediately after collection
        """
        self.parse_attributes = parse_attributes
        self.parser = XattrParser() if parse_attributes else None

    def collect_xattr(self, file_path: Path) -> XattrRecord:
        """
        Collect all Extended Attributes from a file.

        Args:
            file_path: Path to file

        Returns:
            XattrRecord with all attributes

        Raises:
            FileNotFoundError: If file doesn't exist
            OSError: If unable to read attributes
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.debug(f"Collecting xattr from: {file_path}")

        attributes: Dict[str, bytes] = {}

        try:
            # Get all xattr names
            xattr_obj = xattr.xattr(file_path)

            for attr_name in xattr_obj.list():
                try:
                    attr_value = xattr_obj.get(attr_name)
                    attributes[attr_name.decode('utf-8')] = attr_value
                except Exception as e:
                    logger.warning(f"Failed to read xattr {attr_name}: {e}")

            logger.debug(f"Collected {len(attributes)} attributes from {file_path.name}")

            # Create XattrRecord
            record = XattrRecord(
                file_path=file_path,
                attributes=attributes
            )

            # Parse attributes if enabled
            if self.parse_attributes and attributes:
                self._parse_and_update_record(record)

            return record

        except OSError as e:
            logger.error(f"Failed to collect xattr from {file_path}: {e}")
            raise

    def _parse_and_update_record(self, record: XattrRecord) -> None:
        """
        Parse attributes and update XattrRecord with decoded values.

        Args:
            record: XattrRecord to update
        """
        try:
            # Parse quarantine
            if 'com.apple.quarantine' in record.attributes:
                quarantine = self.parser.parse_quarantine(
                    record.attributes['com.apple.quarantine']
                )
                if quarantine:
                    record.quarantine_info = quarantine

            # Parse download URLs
            if 'com.apple.metadata:kMDItemWhereFroms' in record.attributes:
                urls = self.parser.parse_download_source(
                    record.attributes['com.apple.metadata:kMDItemWhereFroms']
                )
                if urls:
                    record.download_urls = urls

            # Parse download date
            if 'com.apple.metadata:kMDItemDownloadedDate' in record.attributes:
                date = self.parser.parse_download_date(
                    record.attributes['com.apple.metadata:kMDItemDownloadedDate']
                )
                if date:
                    record.download_timestamp = date

            # Parse last used date
            if 'com.apple.lastuseddate#PS' in record.attributes:
                date = self.parser.parse_last_used_date(
                    record.attributes['com.apple.lastuseddate#PS']
                )
                if date:
                    record.last_used_date = date

        except Exception as e:
            logger.warning(f"Failed to parse some attributes for {record.file_path}: {e}")

    def collect_directory(
        self,
        dir_path: Path,
        recursive: bool = True,
        follow_symlinks: bool = False
    ) -> List[XattrRecord]:
        """
        Collect Extended Attributes from all files in a directory.

        Args:
            dir_path: Directory path
            recursive: Scan subdirectories
            follow_symlinks: Follow symbolic links

        Returns:
            List of XattrRecord objects

        Raises:
            NotADirectoryError: If path is not a directory
        """
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {dir_path}")

        logger.info(f"Collecting xattr from directory: {dir_path}")

        records = []

        if recursive:
            # Walk directory tree
            for root, dirs, files in os.walk(dir_path, followlinks=follow_symlinks):
                for file_name in files:
                    file_path = Path(root) / file_name
                    try:
                        record = self.collect_xattr(file_path)
                        if record.attributes:  # Only add if has attributes
                            records.append(record)
                    except Exception as e:
                        logger.warning(f"Skipping {file_path}: {e}")
        else:
            # Only scan immediate files
            for item in dir_path.iterdir():
                if item.is_file():
                    try:
                        record = self.collect_xattr(item)
                        if record.attributes:
                            records.append(record)
                    except Exception as e:
                        logger.warning(f"Skipping {item}: {e}")

        logger.info(f"Collected xattr from {len(records)} files")
        return records

    def has_quarantine(self, file_path: Path) -> bool:
        """
        Quick check if file has quarantine attribute.

        Args:
            file_path: Path to file

        Returns:
            True if file has com.apple.quarantine attribute
        """
        try:
            xattr_obj = xattr.xattr(file_path)
            return 'com.apple.quarantine' in [
                name.decode('utf-8') for name in xattr_obj.list()
            ]
        except Exception:
            return False

    def has_download_metadata(self, file_path: Path) -> bool:
        """
        Quick check if file has download metadata.

        Args:
            file_path: Path to file

        Returns:
            True if file has kMDItemWhereFroms attribute
        """
        try:
            xattr_obj = xattr.xattr(file_path)
            return 'com.apple.metadata:kMDItemWhereFroms' in [
                name.decode('utf-8') for name in xattr_obj.list()
            ]
        except Exception:
            return False

    def filter_by_attributes(
        self,
        records: List[XattrRecord],
        has_quarantine: Optional[bool] = None,
        has_download: Optional[bool] = None,
        has_last_used: Optional[bool] = None
    ) -> List[XattrRecord]:
        """
        Filter XattrRecords by attribute presence.

        Args:
            records: List of XattrRecords to filter
            has_quarantine: Filter by quarantine presence
            has_download: Filter by download URLs presence
            has_last_used: Filter by last used date presence

        Returns:
            Filtered list of XattrRecords
        """
        filtered = records

        if has_quarantine is not None:
            filtered = [r for r in filtered if r.has_quarantine == has_quarantine]

        if has_download is not None:
            filtered = [r for r in filtered if r.is_downloaded == has_download]

        if has_last_used is not None:
            has_last_used_check = lambda r: r.last_used_date is not None
            filtered = [r for r in filtered if has_last_used_check(r) == has_last_used]

        return filtered

    def get_downloaded_files(self, records: List[XattrRecord]) -> List[XattrRecord]:
        """
        Get all records for files that were downloaded from internet.

        Args:
            records: List of XattrRecords

        Returns:
            List of records for downloaded files
        """
        return [r for r in records if r.is_downloaded]

    def get_quarantined_files(self, records: List[XattrRecord]) -> List[XattrRecord]:
        """
        Get all records for files with quarantine flag.

        Args:
            records: List of XattrRecords

        Returns:
            List of records for quarantined files
        """
        return [r for r in records if r.has_quarantine]

    def export_to_dict(self, record: XattrRecord) -> dict:
        """
        Export XattrRecord to dictionary format.

        Args:
            record: XattrRecord to export

        Returns:
            Dictionary representation
        """
        export_data = {
            'file_path': str(record.file_path),
            'attributes_count': len(record.attributes),
            'raw_attributes': {
                key: value.decode('utf-8', errors='replace')
                for key, value in record.attributes.items()
            }
        }

        if record.has_quarantine:
            export_data['quarantine'] = {
                'flags': record.quarantine_info.flags,
                'timestamp': record.quarantine_info.timestamp.isoformat(),
                'source_app': record.quarantine_info.source_app,
                'uuid': record.quarantine_info.uuid,
                'is_web_download': record.quarantine_info.is_web_download
            }

        if record.is_downloaded:
            export_data['download_urls'] = record.download_urls

        if record.download_timestamp:
            export_data['download_timestamp'] = record.download_timestamp.isoformat()

        if record.last_used_date:
            export_data['last_used_date'] = record.last_used_date.isoformat()

        return export_data
