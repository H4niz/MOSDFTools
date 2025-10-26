"""
macOS Forensics Artifacts Analyzer (mFAA)
==========================================

A digital forensics tool for macOS live acquisition and analysis of FSEvents
and Extended Attributes.

Author: Digital Forensics Team
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Digital Forensics Team"

from mfaa.utils.logger import setup_logger

# Initialize default logger
logger = setup_logger(__name__)
