"""
Hash Calculator
===============

Calculate cryptographic hashes for file integrity verification.
"""

import hashlib
from pathlib import Path
from mfaa.utils.logger import setup_logger

logger = setup_logger(__name__)


class HashCalculator:
    """Calculate file hashes for integrity verification."""

    BUFFER_SIZE = 65536  # 64KB chunks

    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        """
        Calculate SHA-256 hash of a file.

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal SHA-256 hash string

        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If unable to read file
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        sha256_hash = hashlib.sha256()

        with open(file_path, 'rb') as f:
            while True:
                data = f.read(HashCalculator.BUFFER_SIZE)
                if not data:
                    break
                sha256_hash.update(data)

        return sha256_hash.hexdigest()

    @staticmethod
    def calculate_md5(file_path: Path) -> str:
        """
        Calculate MD5 hash of a file.

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal MD5 hash string
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        md5_hash = hashlib.md5()

        with open(file_path, 'rb') as f:
            while True:
                data = f.read(HashCalculator.BUFFER_SIZE)
                if not data:
                    break
                md5_hash.update(data)

        return md5_hash.hexdigest()

    @staticmethod
    def verify_hash(file_path: Path, expected_hash: str, algorithm: str = 'sha256') -> bool:
        """
        Verify file hash matches expected value.

        Args:
            file_path: Path to file
            expected_hash: Expected hash value (hexadecimal)
            algorithm: Hash algorithm ('sha256' or 'md5')

        Returns:
            True if hash matches, False otherwise
        """
        if algorithm.lower() == 'sha256':
            actual_hash = HashCalculator.calculate_sha256(file_path)
        elif algorithm.lower() == 'md5':
            actual_hash = HashCalculator.calculate_md5(file_path)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        return actual_hash.lower() == expected_hash.lower()
