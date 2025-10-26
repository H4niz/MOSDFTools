"""
Unit tests for GzipHandler
"""

import pytest
import gzip
from pathlib import Path
from mfaa.parser.gzip_handler import GzipHandler
from mfaa.utils.exceptions import CompressionError


class TestGzipHandler:
    """Test cases for GzipHandler."""

    def test_is_gzipped_true(self, tmp_path):
        """Test detection of gzipped file."""
        test_file = tmp_path / "test.gz"

        with gzip.open(test_file, 'wb') as f:
            f.write(b'test data')

        assert GzipHandler.is_gzipped(test_file) is True

    def test_is_gzipped_false(self, tmp_path):
        """Test detection of non-gzipped file."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b'plain text data')

        assert GzipHandler.is_gzipped(test_file) is False

    def test_is_gzipped_nonexistent(self, tmp_path):
        """Test detection with nonexistent file."""
        test_file = tmp_path / "nonexistent.gz"

        assert GzipHandler.is_gzipped(test_file) is False

    def test_decompress_file(self, tmp_path):
        """Test decompressing gzipped file."""
        test_file = tmp_path / "test.gz"
        original_data = b'This is test data for compression'

        with gzip.open(test_file, 'wb') as f:
            f.write(original_data)

        decompressed = GzipHandler.decompress_file(test_file)

        assert decompressed == original_data

    def test_decompress_file_to_output(self, tmp_path):
        """Test decompressing with output file."""
        test_file = tmp_path / "test.gz"
        output_file = tmp_path / "output.txt"
        original_data = b'Test data'

        with gzip.open(test_file, 'wb') as f:
            f.write(original_data)

        decompressed = GzipHandler.decompress_file(test_file, output_file)

        assert decompressed == original_data
        assert output_file.exists()
        assert output_file.read_bytes() == original_data

    def test_decompress_invalid_file(self, tmp_path):
        """Test decompressing invalid gzip file."""
        test_file = tmp_path / "invalid.gz"
        test_file.write_bytes(b'not gzipped data')

        with pytest.raises(CompressionError):
            GzipHandler.decompress_file(test_file)

    def test_decompress_bytes(self):
        """Test decompressing gzipped bytes."""
        original_data = b'Byte data for testing'

        # Gzip compress the data
        compressed = gzip.compress(original_data)

        # Decompress
        decompressed = GzipHandler.decompress_bytes(compressed)

        assert decompressed == original_data

    def test_decompress_bytes_invalid(self):
        """Test decompressing invalid gzipped bytes."""
        invalid_data = b'not compressed'

        with pytest.raises(CompressionError):
            GzipHandler.decompress_bytes(invalid_data)

    def test_compress_file(self, tmp_path):
        """Test compressing a file."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.gz"
        original_data = b'Data to be compressed'

        input_file.write_bytes(original_data)

        GzipHandler.compress_file(input_file, output_file)

        assert output_file.exists()
        assert GzipHandler.is_gzipped(output_file) is True

        # Verify by decompressing
        with gzip.open(output_file, 'rb') as f:
            decompressed = f.read()

        assert decompressed == original_data

    def test_compress_file_with_level(self, tmp_path):
        """Test compressing with different compression levels."""
        input_file = tmp_path / "input.txt"
        output_file_min = tmp_path / "output_min.gz"
        output_file_max = tmp_path / "output_max.gz"

        # Create a file with repetitive data (compresses well)
        original_data = b'A' * 10000

        input_file.write_bytes(original_data)

        # Compress with minimum compression
        GzipHandler.compress_file(input_file, output_file_min, compression_level=1)

        # Compress with maximum compression
        GzipHandler.compress_file(input_file, output_file_max, compression_level=9)

        # Maximum compression should result in smaller file
        assert output_file_max.stat().st_size < output_file_min.stat().st_size

    def test_compress_nonexistent_file(self, tmp_path):
        """Test compressing nonexistent file."""
        input_file = tmp_path / "nonexistent.txt"
        output_file = tmp_path / "output.gz"

        with pytest.raises(CompressionError):
            GzipHandler.compress_file(input_file, output_file)

    def test_roundtrip_compression(self, tmp_path):
        """Test compress and decompress roundtrip."""
        original_file = tmp_path / "original.txt"
        compressed_file = tmp_path / "compressed.gz"
        original_data = b'Round trip test data with special chars: \xFF\x00\x01'

        original_file.write_bytes(original_data)

        # Compress
        GzipHandler.compress_file(original_file, compressed_file)

        # Decompress
        decompressed_data = GzipHandler.decompress_file(compressed_file)

        assert decompressed_data == original_data
