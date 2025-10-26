"""
Unit tests for binary structures and parsing utilities
"""

import pytest
import struct
from mfaa.parser.structures import FSEventsPageHeader, StructParser, FSEventsFlags


class TestFSEventsPageHeader:
    """Test cases for FSEventsPageHeader."""

    def test_parse_v1_header(self):
        """Test parsing v1 page header."""
        data = b'1SLD' + b'\x00' * 8
        header = FSEventsPageHeader.from_bytes(data)

        assert header.signature == b'1SLD'
        assert header.version == 1
        assert len(header.unknown) == 8

    def test_parse_v2_header(self):
        """Test parsing v2 page header."""
        data = b'2SLD' + b'\xFF' * 8
        header = FSEventsPageHeader.from_bytes(data)

        assert header.signature == b'2SLD'
        assert header.version == 2

    def test_parse_insufficient_data(self):
        """Test parsing with insufficient data."""
        data = b'1SLD'  # Only 4 bytes

        with pytest.raises(ValueError, match="Insufficient data"):
            FSEventsPageHeader.from_bytes(data)


class TestStructParser:
    """Test cases for StructParser."""

    def test_read_null_terminated_string(self):
        """Test reading null-terminated string."""
        data = b'Hello, World!\x00remaining data'
        string, offset = StructParser.read_null_terminated_string(data, 0)

        assert string == "Hello, World!"
        assert offset == 14  # Length of string + 1

    def test_read_null_terminated_string_unicode(self):
        """Test reading unicode string."""
        data = "Здравствуй мир\x00".encode('utf-8') + b'more'
        string, offset = StructParser.read_null_terminated_string(data, 0)

        assert "мир" in string
        assert offset > 14

    def test_read_null_terminated_no_terminator(self):
        """Test reading when no null terminator found."""
        data = b'No terminator here'

        with pytest.raises(ValueError, match="No null terminator found"):
            StructParser.read_null_terminated_string(data, 0)

    def test_read_null_terminated_max_length(self):
        """Test max_length parameter."""
        data = b'A' * 5000 + b'\x00'

        with pytest.raises(ValueError, match="No null terminator found"):
            StructParser.read_null_terminated_string(data, 0, max_length=100)

    def test_unpack_uint64(self):
        """Test unpacking 64-bit unsigned integer."""
        value = 0x123456789ABCDEF0
        data = struct.pack('<Q', value) + b'extra'

        unpacked, offset = StructParser.unpack_uint64(data, 0)

        assert unpacked == value
        assert offset == 8

    def test_unpack_uint64_insufficient_data(self):
        """Test unpacking with insufficient data."""
        data = b'short'

        with pytest.raises(struct.error):
            StructParser.unpack_uint64(data, 0)

    def test_unpack_uint32(self):
        """Test unpacking 32-bit unsigned integer."""
        value = 0x12345678
        data = struct.pack('<I', value) + b'more'

        unpacked, offset = StructParser.unpack_uint32(data, 0)

        assert unpacked == value
        assert offset == 4

    def test_unpack_uint32_insufficient_data(self):
        """Test unpacking with insufficient data."""
        data = b'xy'

        with pytest.raises(struct.error):
            StructParser.unpack_uint32(data, 0)

    def test_unpack_uint16(self):
        """Test unpacking 16-bit unsigned integer."""
        value = 0x1234
        data = struct.pack('<H', value) + b'x'

        unpacked, offset = StructParser.unpack_uint16(data, 0)

        assert unpacked == value
        assert offset == 2

    def test_unpack_uint8(self):
        """Test unpacking 8-bit unsigned integer."""
        value = 0xFF
        data = struct.pack('B', value) + b'y'

        unpacked, offset = StructParser.unpack_uint8(data, 0)

        assert unpacked == value
        assert offset == 1

    def test_validate_signature_valid(self):
        """Test signature validation with valid signature."""
        data = b'MAGIC' + b'rest of data'
        assert StructParser.validate_signature(data, b'MAGIC', 0) is True

    def test_validate_signature_invalid(self):
        """Test signature validation with invalid signature."""
        data = b'WRONG' + b'rest of data'
        assert StructParser.validate_signature(data, b'MAGIC', 0) is False

    def test_validate_signature_offset(self):
        """Test signature validation at offset."""
        data = b'xxx' + b'MAGIC' + b'yyy'
        assert StructParser.validate_signature(data, b'MAGIC', 3) is True

    def test_validate_signature_insufficient_data(self):
        """Test signature validation with insufficient data."""
        data = b'MAG'
        assert StructParser.validate_signature(data, b'MAGIC', 0) is False

    def test_hex_dump(self):
        """Test hex dump generation."""
        data = b'Hello, World!\x00\xFF'

        hex_dump = StructParser.hex_dump(data, 0, 15)

        assert '00000000:' in hex_dump
        assert 'Hello' in hex_dump
        assert '48 65 6c 6c 6f' in hex_dump  # 'Hello' in hex

    def test_hex_dump_limited_length(self):
        """Test hex dump with length limit."""
        data = b'A' * 100

        hex_dump = StructParser.hex_dump(data, 0, 16)

        # Should only dump 16 bytes
        assert hex_dump.count('41') == 16  # 'A' is 0x41


class TestFSEventsFlags:
    """Test cases for FSEvents flag constants."""

    def test_flag_constants(self):
        """Test that flag constants are defined."""
        assert FSEventsFlags.ITEM_CREATED == 0x00000100
        assert FSEventsFlags.ITEM_REMOVED == 0x00000200
        assert FSEventsFlags.ITEM_MODIFIED == 0x00001000
        assert FSEventsFlags.ITEM_IS_FILE == 0x00010000
        assert FSEventsFlags.ITEM_IS_DIR == 0x00020000

    def test_flag_combinations(self):
        """Test combining flags."""
        combined = FSEventsFlags.ITEM_CREATED | FSEventsFlags.ITEM_IS_FILE

        assert (combined & FSEventsFlags.ITEM_CREATED) != 0
        assert (combined & FSEventsFlags.ITEM_IS_FILE) != 0
        assert (combined & FSEventsFlags.ITEM_REMOVED) == 0
