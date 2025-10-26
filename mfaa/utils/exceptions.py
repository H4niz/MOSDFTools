"""
Custom Exceptions
=================

Custom exception classes for mFAA.
"""


class MFAAError(Exception):
    """Base exception for mFAA errors."""
    pass


class CollectionError(MFAAError):
    """Error during artifact collection."""
    pass


class ParseError(MFAAError):
    """Error during parsing."""
    pass


class CompressionError(ParseError):
    """Error during decompression."""
    pass


class ValidationError(MFAAError):
    """Input validation error."""
    pass


class PermissionError(MFAAError):
    """Insufficient permissions."""
    pass


class ConfigurationError(MFAAError):
    """Configuration file error."""
    pass
