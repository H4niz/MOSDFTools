"""
Input Validator
===============

Validate inputs and paths.
"""

import os
from pathlib import Path
from typing import List


class Validator:
    """Input validation utilities."""

    @staticmethod
    def validate_directory(path: Path, must_exist: bool = True) -> bool:
        """
        Validate that path is a directory.

        Args:
            path: Path to validate
            must_exist: If True, directory must exist

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        if must_exist and not path.exists():
            raise ValueError(f"Directory does not exist: {path}")

        if path.exists() and not path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        return True

    @staticmethod
    def validate_file(path: Path, must_exist: bool = True) -> bool:
        """
        Validate that path is a file.

        Args:
            path: Path to validate
            must_exist: If True, file must exist

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        if must_exist and not path.exists():
            raise ValueError(f"File does not exist: {path}")

        if path.exists() and not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        return True

    @staticmethod
    def check_root_privileges() -> bool:
        """
        Check if running with root privileges.

        Returns:
            True if running as root
        """
        return os.geteuid() == 0

    @staticmethod
    def validate_extensions(extensions: List[str]) -> bool:
        """
        Validate file extensions format.

        Args:
            extensions: List of extensions (e.g., ['.txt', '.log'])

        Returns:
            True if valid

        Raises:
            ValueError: If any extension is invalid
        """
        for ext in extensions:
            if not ext.startswith('.'):
                raise ValueError(f"Extension must start with '.': {ext}")

        return True
