"""
FSEvents Parser
===============

Parse FSEvents binary format (v1 and v2/DLS).
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
from mfaa.models import FSEvent, EventFlags
from mfaa.parser.structures import FSEventsPageHeader, StructParser
from mfaa.parser.gzip_handler import GzipHandler
from mfaa.utils.logger import setup_logger
from mfaa.utils.exceptions import ParseError

logger = setup_logger(__name__)


class FSEventsParser:
    """Parse FSEvents binary format."""

    # macOS epoch offset (January 1, 2001)
    MACOS_EPOCH_OFFSET = 978307200

    def __init__(self, version: Optional[int] = None):
        """
        Initialize parser.

        Args:
            version: FSEvents format version (1 or 2). None = auto-detect
        """
        self.version = version
        self.gzip_handler = GzipHandler()

    def parse_file(self, file_path: Path) -> List[FSEvent]:
        """
        Parse a single FSEvents file.

        Args:
            file_path: Path to FSEvents file

        Returns:
            List of FSEvent objects

        Raises:
            ParseError: If parsing fails
        """
        if not file_path.exists():
            raise FileNotFoundError(f"FSEvents file not found: {file_path}")

        logger.debug(f"Parsing FSEvents file: {file_path}")

        try:
            # Check if file is gzipped (v2/v3 format)
            if self.gzip_handler.is_gzipped(file_path):
                logger.debug("Detected gzip compression")
                data = self.gzip_handler.decompress_file(file_path)

                # Detect version from header signature
                if len(data) >= 4:
                    signature = data[0:4]
                    if signature == b'3SLD':
                        detected_version = 3
                        logger.debug("Detected v3 format (3SLD header)")
                    elif signature in [b'1SLD', b'2SLD', b'DLS2']:
                        detected_version = 2
                        logger.debug("Detected v2/DLS format")
                    else:
                        # Unknown signature, try v2
                        detected_version = 2
                        logger.warning(f"Unknown signature: {signature}, assuming v2")
                else:
                    detected_version = 2
            else:
                logger.debug("Uncompressed format (v1)")
                with open(file_path, 'rb') as f:
                    data = f.read()
                detected_version = 1

            # Use detected version if not explicitly set
            version = self.version if self.version else detected_version

            # Parse based on version
            if version == 1:
                events = self._parse_v1(data)
            elif version == 2:
                events = self._parse_v2(data)
            elif version == 3:
                events = self._parse_v3(data)
            else:
                raise ParseError(f"Unsupported FSEvents version: {version}")

            logger.info(f"Parsed {len(events)} events from {file_path.name}")
            return events

        except Exception as e:
            raise ParseError(f"Failed to parse {file_path}: {e}")

    def parse_directory(self, fsevents_dir: Path) -> List[FSEvent]:
        """
        Parse all FSEvents files in a directory.

        Args:
            fsevents_dir: Path to .fseventsd directory

        Returns:
            List of all FSEvent objects from all files
        """
        if not fsevents_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {fsevents_dir}")

        logger.info(f"Parsing FSEvents directory: {fsevents_dir}")

        all_events = []

        for file_path in sorted(fsevents_dir.iterdir()):
            if file_path.is_file() and not file_path.name.startswith('.'):
                try:
                    events = self.parse_file(file_path)
                    all_events.extend(events)
                except Exception as e:
                    logger.warning(f"Skipping {file_path.name}: {e}")

        logger.info(f"Total events parsed: {len(all_events)}")
        return all_events

    def _parse_v1(self, data: bytes) -> List[FSEvent]:
        """
        Parse FSEvents version 1 format.

        Format: Simple record-based format
        Each record:
        - Path (null-terminated string)
        - Event ID (8 bytes, little-endian)
        - Flags (4 bytes, little-endian)

        Args:
            data: Raw FSEvents data

        Returns:
            List of FSEvent objects
        """
        events = []
        offset = 0
        data_len = len(data)

        logger.debug(f"Parsing FSEvents v1 format, data size: {data_len} bytes")

        try:
            while offset < data_len:
                # Avoid reading beyond data
                if offset + 13 > data_len:  # Min record size (1 byte path + 12 bytes)
                    break

                # Read null-terminated path string
                try:
                    path_str, new_offset = StructParser.read_null_terminated_string(data, offset)
                except ValueError:
                    # No null terminator found, likely end of valid data
                    break

                offset = new_offset

                # Check if we have enough bytes for event ID and flags
                if offset + 12 > data_len:
                    logger.warning("Incomplete record at end of file")
                    break

                # Read event ID (8 bytes)
                event_id, offset = StructParser.unpack_uint64(data, offset)

                # Read flags (4 bytes)
                flags, offset = StructParser.unpack_uint32(data, offset)

                # Decode flags
                event_flags = self.decode_flags(flags)

                # Create FSEvent object
                # Note: v1 doesn't have timestamp in the data, using epoch
                event = FSEvent(
                    event_id=event_id,
                    timestamp=datetime.fromtimestamp(0),  # v1 doesn't store timestamp
                    path=Path(path_str),
                    flags=event_flags,
                    node_id=None  # v1 doesn't have node_id
                )

                events.append(event)

        except Exception as e:
            logger.error(f"Error parsing v1 at offset {offset}: {e}")
            # Return events parsed so far
            pass

        logger.info(f"Parsed {len(events)} events from v1 format")
        return events

    def _parse_v2(self, data: bytes) -> List[FSEvent]:
        """
        Parse FSEvents version 2 (DLS) format.

        Format: Page-based with header
        Header (12 bytes):
        - Signature (4 bytes): '1SLD' or '2SLD'
        - Version info (8 bytes)

        Records:
        - Path (null-terminated string)
        - Event ID (8 bytes)
        - Flags (4 bytes)
        - Timestamp (8 bytes, macOS epoch)
        - Node ID (8 bytes, inode number)

        Args:
            data: Raw FSEvents data (decompressed)

        Returns:
            List of FSEvent objects
        """
        events = []
        offset = 0
        data_len = len(data)

        logger.debug(f"Parsing FSEvents v2/DLS format, data size: {data_len} bytes")

        # Parse page header
        try:
            header = FSEventsPageHeader.from_bytes(data)
            logger.debug(f"Page header: {header.signature}, version: {header.version}")
            offset = 12  # Skip header
        except Exception as e:
            raise ParseError(f"Failed to parse page header: {e}")

        # Validate signature
        if header.signature not in [b'1SLD', b'2SLD']:
            raise ParseError(f"Invalid DLS signature: {header.signature}")

        try:
            while offset < data_len:
                # Need at least path (1 byte) + event_id (8) + flags (4) + timestamp (8) + node_id (8) = 29 bytes
                if offset + 29 > data_len:
                    break

                # Read null-terminated path string
                try:
                    path_str, new_offset = StructParser.read_null_terminated_string(data, offset)
                except ValueError:
                    # No null terminator found
                    break

                offset = new_offset

                # Check if we have enough bytes for remaining fields
                if offset + 28 > data_len:
                    logger.warning("Incomplete record at end of file")
                    break

                # Read event ID (8 bytes)
                event_id, offset = StructParser.unpack_uint64(data, offset)

                # Read flags (4 bytes)
                flags, offset = StructParser.unpack_uint32(data, offset)

                # Read timestamp (8 bytes, macOS epoch)
                timestamp_raw, offset = StructParser.unpack_uint64(data, offset)

                # Read node ID / inode (8 bytes)
                node_id, offset = StructParser.unpack_uint64(data, offset)

                # Decode flags
                event_flags = self.decode_flags(flags)

                # Convert timestamp
                try:
                    timestamp = self.timestamp_to_datetime(timestamp_raw)
                except (ValueError, OSError) as e:
                    # Invalid timestamp, use epoch
                    logger.warning(f"Invalid timestamp {timestamp_raw}: {e}")
                    timestamp = datetime.fromtimestamp(0)

                # Create FSEvent object
                event = FSEvent(
                    event_id=event_id,
                    timestamp=timestamp,
                    path=Path(path_str),
                    flags=event_flags,
                    node_id=node_id if node_id > 0 else None
                )

                events.append(event)

        except Exception as e:
            logger.error(f"Error parsing v2 at offset {offset}: {e}")
            # Return events parsed so far
            pass

        logger.info(f"Parsed {len(events)} events from v2/DLS format")
        return events

    def _parse_v3(self, data: bytes) -> List[FSEvent]:
        """
        Parse FSEvents version 3 format (macOS Sequoia 15.x).

        Format: Header + simplified record structure
        Header (12 bytes):
        - Signature (4 bytes): '3SLD'
        - Metadata (8 bytes)

        Records:
        - Event ID (8 bytes, little-endian)
        - Flags (4 bytes, little-endian)
        - Node ID (8 bytes, little-endian, inode number)
        - Padding (5 bytes, zeros)
        - Path (null-terminated string)

        Args:
            data: Raw FSEvents data (decompressed)

        Returns:
            List of FSEvent objects
        """
        events = []
        offset = 0
        data_len = len(data)

        logger.debug(f"Parsing FSEvents v3 format, data size: {data_len} bytes")

        # Validate header
        if data_len < 12:
            raise ParseError("File too small to contain v3 header")

        signature = data[0:4]
        if signature != b'3SLD':
            raise ParseError(f"Invalid v3 signature: {signature}")

        logger.debug(f"V3 header signature: {signature.decode('ascii')}")
        offset = 12  # Skip header

        try:
            while offset < data_len:
                # Need at least: event_id (8) + flags (4) + node_id (8) + padding (5) + path (1) = 26 bytes
                if offset + 26 > data_len:
                    break

                # Read event ID (8 bytes)
                event_id, offset = StructParser.unpack_uint64(data, offset)

                # Read flags (4 bytes)
                flags, offset = StructParser.unpack_uint32(data, offset)

                # Read node ID / inode (8 bytes)
                node_id, offset = StructParser.unpack_uint64(data, offset)

                # Skip padding (5 bytes)
                offset += 5

                # Read null-terminated path string
                try:
                    path_str, new_offset = StructParser.read_null_terminated_string(data, offset)
                except ValueError:
                    # No null terminator found
                    logger.warning(f"No null terminator found at offset {offset}")
                    break

                offset = new_offset

                # Skip empty paths
                if not path_str or path_str == '':
                    continue

                # Decode flags
                event_flags = self.decode_flags(flags)

                # Create FSEvent object
                # Note: v3 doesn't include timestamp in record, use epoch
                event = FSEvent(
                    event_id=event_id,
                    timestamp=datetime.fromtimestamp(0),  # v3 doesn't store timestamp in record
                    path=Path(path_str),
                    flags=event_flags,
                    node_id=node_id if node_id > 0 else None
                )

                events.append(event)

        except Exception as e:
            logger.error(f"Error parsing v3 at offset {offset}: {e}")
            # Return events parsed so far
            pass

        logger.info(f"Parsed {len(events)} events from v3 format")
        return events

    @staticmethod
    def decode_flags(flags: int) -> EventFlags:
        """
        Decode event flags integer to EventFlags enum.

        Args:
            flags: Raw flags integer from FSEvents

        Returns:
            EventFlags enum value
        """
        # Convert integer to EventFlags
        try:
            return EventFlags(flags)
        except ValueError:
            # If not a valid flag combination, return as-is
            logger.warning(f"Unknown flag combination: 0x{flags:08x}")
            return EventFlags.NONE

    @staticmethod
    def timestamp_to_datetime(timestamp: int) -> datetime:
        """
        Convert macOS timestamp to datetime.

        Args:
            timestamp: macOS timestamp (seconds since 2001-01-01)

        Returns:
            datetime object
        """
        # macOS timestamps are seconds since 2001-01-01
        # Convert to Unix timestamp (seconds since 1970-01-01)
        unix_timestamp = timestamp + FSEventsParser.MACOS_EPOCH_OFFSET
        return datetime.fromtimestamp(unix_timestamp)

    def validate_events(self, events: List[FSEvent]) -> List[FSEvent]:
        """
        Validate parsed events and filter out invalid ones.

        Args:
            events: List of FSEvent objects

        Returns:
            Filtered list of valid FSEvent objects
        """
        valid_events = []

        for event in events:
            # Basic validation
            if event.event_id <= 0:
                logger.warning(f"Invalid event ID: {event.event_id}")
                continue

            if not event.path or str(event.path) == '.':
                logger.warning(f"Invalid path for event {event.event_id}")
                continue

            # Check for reasonable timestamp (after 2001, before 2100)
            if event.timestamp.year < 2001 or event.timestamp.year > 2100:
                logger.debug(f"Suspicious timestamp for event {event.event_id}: {event.timestamp}")
                # Still include but log warning

            valid_events.append(event)

        if len(valid_events) < len(events):
            logger.warning(f"Filtered out {len(events) - len(valid_events)} invalid events")

        return valid_events

    def get_statistics(self, events: List[FSEvent]) -> dict:
        """
        Get statistics about parsed events.

        Args:
            events: List of FSEvent objects

        Returns:
            Dictionary with statistics
        """
        if not events:
            return {
                'total_events': 0,
                'event_types': {},
                'unique_paths': 0,
                'date_range': None
            }

        from collections import Counter

        # Count event types
        event_type_counter = Counter()
        for event in events:
            for event_type in event.event_types:
                event_type_counter[event_type.value] += 1

        # Get unique paths
        unique_paths = len(set(str(event.path) for event in events))

        # Get date range
        timestamps = [e.timestamp for e in events if e.timestamp.year > 2001]
        date_range = None
        if timestamps:
            date_range = {
                'earliest': min(timestamps).isoformat(),
                'latest': max(timestamps).isoformat()
            }

        return {
            'total_events': len(events),
            'event_types': dict(event_type_counter),
            'unique_paths': unique_paths,
            'date_range': date_range,
            'has_timestamps': any(e.timestamp.year > 2001 for e in events),
            'has_node_ids': any(e.node_id is not None for e in events)
        }
