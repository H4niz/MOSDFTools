"""
Unit tests for HashCalculator
"""

import pytest
from pathlib import Path
from mfaa.collector.hash_calculator import HashCalculator


class TestHashCalculator:
    """Test cases for HashCalculator."""

    def test_calculate_sha256(self, tmp_path):
        """Test SHA-256 hash calculation."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        # Calculate hash
        hash_calc = HashCalculator()
        result = hash_calc.calculate_sha256(test_file)

        # Known SHA-256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert result == expected

    def test_calculate_sha256_nonexistent_file(self):
        """Test SHA-256 with non-existent file."""
        hash_calc = HashCalculator()

        with pytest.raises(FileNotFoundError):
            hash_calc.calculate_sha256(Path("/nonexistent/file.txt"))

    def test_verify_hash_success(self, tmp_path):
        """Test hash verification with correct hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        hash_calc = HashCalculator()
        actual_hash = hash_calc.calculate_sha256(test_file)

        assert hash_calc.verify_hash(test_file, actual_hash, 'sha256')

    def test_verify_hash_failure(self, tmp_path):
        """Test hash verification with incorrect hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        hash_calc = HashCalculator()
        wrong_hash = "0" * 64

        assert not hash_calc.verify_hash(test_file, wrong_hash, 'sha256')
