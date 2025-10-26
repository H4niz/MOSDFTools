"""
Binary Structures
=================

Define binary structures for FSEvents parsing.
"""

import struct
from dataclasses import dataclass
from typing import Optional


@dataclass
class FSEventsPageHeader:
    """FSEvents page header structure."""
    signature: bytes  # b'1SLD' or b'2SLD'
    version: int
    unknown: bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> 'FSEventsPageHeader':
        """
        Parse page header from bytes.

        Args:
            data: Raw bytes (at least 12 bytes)

        Returns:
            FSEventsPageHeader object
        """
        if len(data) < 12:
            raise ValueError("Insufficient data for page header")

        signature = data[0:4]
        version = 1 if signature == b'1SLD' else 2

        return cls(
            signature=signature,
            version=version,
            unknown=data[4:12]
        )


@dataclass
class FSEventsRecord:
    """Single FSEvents record structure."""
    path: str
    event_id: int
    flags: int
    node_id: Optional[int] = None

    @property
    def version(self) -> int:
        """Determine format version from record structure."""
        return 2 if self.node_id is not None else 1


# FSEvents flag constants (from Apple documentation)
class FSEventsFlags:
    """FSEvents flag constants."""

    # Event types
    MUST_SCAN_SUBDIRS = 0x00000001
    USER_DROPPED = 0x00000002
    KERNEL_DROPPED = 0x00000004
    EVENT_IDS_WRAPPED = 0x00000008
    HISTORY_DONE = 0x00000010
    ROOT_CHANGED = 0x00000020
    MOUNT = 0x00000040
    UNMOUNT = 0x00000080

    # Item events
    ITEM_CREATED = 0x00000100
    ITEM_REMOVED = 0x00000200
    ITEM_INODE_META_MOD = 0x00000400
    ITEM_RENAMED = 0x00000800
    ITEM_MODIFIED = 0x00001000
    ITEM_FINDER_INFO_MOD = 0x00002000
    ITEM_CHANGE_OWNER = 0x00004000
    ITEM_XATTR_MOD = 0x00008000

    # Item type flags
    ITEM_IS_FILE = 0x00010000
    ITEM_IS_DIR = 0x00020000
    ITEM_IS_SYMLINK = 0x00040000
    ITEM_IS_HARDLINK = 0x00100000
    ITEM_CLONED = 0x00400000


class StructParser:
    """Helper for parsing binary structures."""

    @staticmethod
    def read_null_terminated_string(data: bytes, offset: int, max_length: int = 4096) -> tuple[str, int]:
        """
        Read null-terminated string from bytes.

        Args:
            data: Byte array
            offset: Starting offset
            max_length: Maximum string length to prevent infinite loops

        Returns:
            Tuple of (string, new_offset)

        Raises:
            ValueError: If no null terminator found within max_length
        """
        end = data.find(b'\x00', offset, offset + max_length)
        if end == -1:
            raise ValueError("No null terminator found within max_length")

        string = data[offset:end].decode('utf-8', errors='replace')
        return string, end + 1

    @staticmethod
    def unpack_uint64(data: bytes, offset: int) -> tuple[int, int]:
        """
        Unpack 64-bit unsigned integer (little-endian).

        Args:
            data: Byte array
            offset: Starting offset

        Returns:
            Tuple of (integer, new_offset)

        Raises:
            struct.error: If insufficient data
        """
        if offset + 8 > len(data):
            raise struct.error("Insufficient data for uint64")

        value = struct.unpack_from('<Q', data, offset)[0]
        return value, offset + 8

    @staticmethod
    def unpack_uint32(data: bytes, offset: int) -> tuple[int, int]:
        """
        Unpack 32-bit unsigned integer (little-endian).

        Args:
            data: Byte array
            offset: Starting offset

        Returns:
            Tuple of (integer, new_offset)

        Raises:
            struct.error: If insufficient data
        """
        if offset + 4 > len(data):
            raise struct.error("Insufficient data for uint32")

        value = struct.unpack_from('<I', data, offset)[0]
        return value, offset + 4

    @staticmethod
    def unpack_uint16(data: bytes, offset: int) -> tuple[int, int]:
        """
        Unpack 16-bit unsigned integer (little-endian).

        Args:
            data: Byte array
            offset: Starting offset

        Returns:
            Tuple of (integer, new_offset)
        """
        if offset + 2 > len(data):
            raise struct.error("Insufficient data for uint16")

        value = struct.unpack_from('<H', data, offset)[0]
        return value, offset + 2

    @staticmethod
    def unpack_uint8(data: bytes, offset: int) -> tuple[int, int]:
        """
        Unpack 8-bit unsigned integer.

        Args:
            data: Byte array
            offset: Starting offset

        Returns:
            Tuple of (integer, new_offset)
        """
        if offset + 1 > len(data):
            raise struct.error("Insufficient data for uint8")

        value = struct.unpack_from('B', data, offset)[0]
        return value, offset + 1

    @staticmethod
    def validate_signature(data: bytes, expected: bytes, offset: int = 0) -> bool:
        """
        Validate magic signature at offset.

        Args:
            data: Byte array
            expected: Expected signature bytes
            offset: Offset to check

        Returns:
            True if signature matches
        """
        if offset + len(expected) > len(data):
            return False

        return data[offset:offset + len(expected)] == expected

    @staticmethod
    def hex_dump(data: bytes, offset: int = 0, length: int = 16) -> str:
        """
        Create hex dump of data for debugging.

        Args:
            data: Byte array
            offset: Starting offset
            length: Number of bytes to dump

        Returns:
            Hex dump string
        """
        end = min(offset + length, len(data))
        hex_str = ' '.join(f'{b:02x}' for b in data[offset:end])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[offset:end])
        return f"{offset:08x}: {hex_str:<48} {ascii_str}"
