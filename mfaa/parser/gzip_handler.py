"""
Gzip Handler
============

Handle gzip compression/decompression for FSEvents v2.
"""

import gzip
from pathlib import Path
from typing import Optional
from mfaa.utils.logger import setup_logger
from mfaa.utils.exceptions import CompressionError

logger = setup_logger(__name__)


class GzipHandler:
    """Handle gzip compressed FSEvents files (DLS format)."""

    @staticmethod
    def is_gzipped(file_path: Path) -> bool:
        """
        Check if file is gzip compressed.

        Args:
            file_path: Path to file

        Returns:
            True if file is gzipped
        """
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(2)
                return magic == b'\x1f\x8b'  # Gzip magic number
        except Exception:
            return False

    @staticmethod
    def decompress_file(file_path: Path, output_path: Optional[Path] = None) -> bytes:
        """
        Decompress gzip file.

        Args:
            file_path: Path to gzipped file
            output_path: Optional output path for decompressed data

        Returns:
            Decompressed data as bytes

        Raises:
            CompressionError: If decompression fails
        """
        logger.debug(f"Decompressing: {file_path}")

        try:
            with gzip.open(file_path, 'rb') as f:
                decompressed_data = f.read()

            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(decompressed_data)
                logger.debug(f"Decompressed data written to: {output_path}")

            return decompressed_data

        except Exception as e:
            raise CompressionError(f"Decompression failed for {file_path}: {e}")

    @staticmethod
    def decompress_bytes(data: bytes) -> bytes:
        """
        Decompress gzipped bytes.

        Args:
            data: Gzipped byte data

        Returns:
            Decompressed bytes

        Raises:
            CompressionError: If decompression fails
        """
        try:
            return gzip.decompress(data)
        except Exception as e:
            raise CompressionError(f"Decompression failed: {e}")

    @staticmethod
    def compress_file(file_path: Path, output_path: Path, compression_level: int = 9) -> None:
        """
        Compress file with gzip.

        Args:
            file_path: Path to input file
            output_path: Path to output gzipped file
            compression_level: Compression level (0-9)
        """
        logger.debug(f"Compressing: {file_path}")

        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(output_path, 'wb', compresslevel=compression_level) as f_out:
                    f_out.write(f_in.read())

            logger.debug(f"Compressed data written to: {output_path}")

        except Exception as e:
            raise CompressionError(f"Compression failed for {file_path}: {e}")
