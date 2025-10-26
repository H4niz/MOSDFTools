"""
Parser Module
=============

Responsible for parsing binary formats (FSEvents, Extended Attributes).
"""

from mfaa.parser.fsevents_parser import FSEventsParser
from mfaa.parser.xattr_parser import XattrParser
from mfaa.parser.gzip_handler import GzipHandler

__all__ = [
    'FSEventsParser',
    'XattrParser',
    'GzipHandler',
]
