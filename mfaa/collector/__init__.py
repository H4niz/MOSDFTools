"""
Collector Module
================

Responsible for collecting artifacts from live macOS systems.
"""

from mfaa.collector.volume_scanner import VolumeScanner
from mfaa.collector.fsevents_collector import FSEventsCollector
from mfaa.collector.xattr_collector import XattrCollector
from mfaa.collector.hash_calculator import HashCalculator

__all__ = [
    'VolumeScanner',
    'FSEventsCollector',
    'XattrCollector',
    'HashCalculator',
]
