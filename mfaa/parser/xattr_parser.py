"""
Extended Attributes Parser
===========================

Parse and decode Extended Attributes values.
"""

import plistlib
from datetime import datetime
from typing import List, Optional
from mfaa.models import QuarantineInfo
from mfaa.utils.logger import setup_logger

logger = setup_logger(__name__)


class XattrParser:
    """Parse and decode Extended Attributes values."""

    @staticmethod
    def parse_quarantine(value: bytes) -> Optional[QuarantineInfo]:
        """
        Parse com.apple.quarantine attribute.

        Format: "FLAGS;TIMESTAMP;APP;UUID"
        Example: "0083;673a8f2d;Safari;F643CD5F-6974-46AB-8A9B-C7A7E9C4F8F7"

        Args:
            value: Raw bytes of quarantine xattr

        Returns:
            QuarantineInfo object or None if parsing fails
        """
        try:
            # Decode bytes to string
            quarantine_str = value.decode('utf-8', errors='replace').strip()

            # Split into components
            parts = quarantine_str.split(';')

            if len(parts) < 4:
                logger.warning(f"Invalid quarantine format: {quarantine_str}")
                return None

            flags_hex = parts[0]
            timestamp_hex = parts[1]
            source_app = parts[2]
            uuid = parts[3]

            # Parse flags
            flags = int(flags_hex, 16)

            # Parse timestamp (hex -> seconds since epoch)
            timestamp_int = int(timestamp_hex, 16)
            timestamp = datetime.fromtimestamp(timestamp_int)

            return QuarantineInfo(
                flags=flags,
                timestamp=timestamp,
                source_app=source_app,
                uuid=uuid
            )

        except Exception as e:
            logger.error(f"Failed to parse quarantine attribute: {e}")
            return None

    @staticmethod
    def parse_download_source(value: bytes) -> Optional[List[str]]:
        """
        Parse kMDItemWhereFroms attribute (binary plist).

        Args:
            value: Raw bytes of WhereFroms xattr (binary plist)

        Returns:
            List of URLs or None if parsing fails
        """
        try:
            # Parse binary plist
            plist_data = plistlib.loads(value)

            # Extract URLs
            if isinstance(plist_data, list):
                urls = [str(url) for url in plist_data if url]
                return urls
            elif isinstance(plist_data, str):
                return [plist_data]
            else:
                logger.warning(f"Unexpected WhereFroms format: {type(plist_data)}")
                return None

        except Exception as e:
            logger.error(f"Failed to parse download source: {e}")
            return None

    @staticmethod
    def parse_download_date(value: bytes) -> Optional[datetime]:
        """
        Parse kMDItemDownloadedDate attribute.

        Args:
            value: Raw bytes of download date xattr

        Returns:
            datetime object or None if parsing fails
        """
        try:
            # Parse binary plist
            plist_data = plistlib.loads(value)

            if isinstance(plist_data, datetime):
                return plist_data
            elif isinstance(plist_data, (int, float)):
                return datetime.fromtimestamp(plist_data)
            else:
                logger.warning(f"Unexpected download date format: {type(plist_data)}")
                return None

        except Exception as e:
            logger.error(f"Failed to parse download date: {e}")
            return None

    @staticmethod
    def parse_last_used_date(value: bytes) -> Optional[datetime]:
        """
        Parse com.apple.lastuseddate#PS attribute.

        Args:
            value: Raw bytes of last used date xattr

        Returns:
            datetime object or None if parsing fails
        """
        try:
            # Parse binary plist
            plist_data = plistlib.loads(value)

            if isinstance(plist_data, datetime):
                return plist_data
            elif isinstance(plist_data, (int, float)):
                return datetime.fromtimestamp(plist_data)
            else:
                logger.warning(f"Unexpected last used date format: {type(plist_data)}")
                return None

        except Exception as e:
            logger.error(f"Failed to parse last used date: {e}")
            return None

    @staticmethod
    def decode_all_attributes(attributes: dict) -> dict:
        """
        Decode all common Extended Attributes.

        Args:
            attributes: Dict of attribute name -> raw bytes

        Returns:
            Dict of attribute name -> decoded value
        """
        decoded = {}

        # Parse quarantine
        if 'com.apple.quarantine' in attributes:
            quarantine = XattrParser.parse_quarantine(attributes['com.apple.quarantine'])
            if quarantine:
                decoded['quarantine_info'] = quarantine

        # Parse download URLs
        if 'com.apple.metadata:kMDItemWhereFroms' in attributes:
            urls = XattrParser.parse_download_source(
                attributes['com.apple.metadata:kMDItemWhereFroms']
            )
            if urls:
                decoded['download_urls'] = urls

        # Parse download date
        if 'com.apple.metadata:kMDItemDownloadedDate' in attributes:
            date = XattrParser.parse_download_date(
                attributes['com.apple.metadata:kMDItemDownloadedDate']
            )
            if date:
                decoded['download_date'] = date

        # Parse last used date
        if 'com.apple.lastuseddate#PS' in attributes:
            date = XattrParser.parse_last_used_date(
                attributes['com.apple.lastuseddate#PS']
            )
            if date:
                decoded['last_used_date'] = date

        return decoded
