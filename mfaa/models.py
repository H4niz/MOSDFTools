"""
Data Models
===========

Data structures for FSEvents, Extended Attributes, and analysis results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, Flag
from pathlib import Path
from typing import Optional, List, Dict, Any


# ============================================================================
# Volume Information
# ============================================================================

@dataclass
class VolumeInfo:
    """Information about an APFS volume."""
    name: str
    mount_point: Path
    filesystem_type: str  # "apfs"
    device_node: str  # "/dev/disk3s1"
    total_size: int  # bytes
    available_size: int  # bytes
    encryption_enabled: bool


# ============================================================================
# FSEvents
# ============================================================================

class EventType(Enum):
    """FSEvents event types."""
    CREATED = "Created"
    REMOVED = "Removed"
    MODIFIED = "Modified"
    RENAMED = "Renamed"
    INODE_META_MOD = "InodeMetaMod"
    FINDER_INFO_MOD = "FinderInfoMod"
    CHANGE_OWNER = "ChangeOwner"
    XATTR_MOD = "XAttrMod"
    IS_FILE = "IsFile"
    IS_DIR = "IsDir"
    IS_SYMLINK = "IsSymlink"
    IS_HARDLINK = "IsHardlink"
    ITEM_CLONED = "ItemCloned"


class EventFlags(Flag):
    """FSEvents flags (bitfield)."""
    NONE = 0
    MUST_SCAN_SUBDIRS = 0x00000001
    USER_DROPPED = 0x00000002
    KERNEL_DROPPED = 0x00000004
    EVENT_IDS_WRAPPED = 0x00000008
    HISTORY_DONE = 0x00000010
    ROOT_CHANGED = 0x00000020
    MOUNT = 0x00000040
    UNMOUNT = 0x00000080
    ITEM_CREATED = 0x00000100
    ITEM_REMOVED = 0x00000200
    ITEM_INODE_META_MOD = 0x00000400
    ITEM_RENAMED = 0x00000800
    ITEM_MODIFIED = 0x00001000
    ITEM_FINDER_INFO_MOD = 0x00002000
    ITEM_CHANGE_OWNER = 0x00004000
    ITEM_XATTR_MOD = 0x00008000
    ITEM_IS_FILE = 0x00010000
    ITEM_IS_DIR = 0x00020000
    ITEM_IS_SYMLINK = 0x00040000
    ITEM_IS_HARDLINK = 0x00100000
    ITEM_CLONED = 0x00400000


@dataclass
class FSEvent:
    """A single FSEvents record."""
    event_id: int
    timestamp: datetime
    path: Path
    flags: EventFlags
    node_id: Optional[int] = None  # inode number

    @property
    def is_created(self) -> bool:
        return EventFlags.ITEM_CREATED in self.flags

    @property
    def is_removed(self) -> bool:
        return EventFlags.ITEM_REMOVED in self.flags

    @property
    def is_modified(self) -> bool:
        return EventFlags.ITEM_MODIFIED in self.flags

    @property
    def is_renamed(self) -> bool:
        return EventFlags.ITEM_RENAMED in self.flags

    @property
    def is_file(self) -> bool:
        return EventFlags.ITEM_IS_FILE in self.flags

    @property
    def is_directory(self) -> bool:
        return EventFlags.ITEM_IS_DIR in self.flags

    @property
    def event_types(self) -> List[EventType]:
        """Return list of event types for this event."""
        types = []
        if self.is_created:
            types.append(EventType.CREATED)
        if self.is_removed:
            types.append(EventType.REMOVED)
        if self.is_modified:
            types.append(EventType.MODIFIED)
        if self.is_renamed:
            types.append(EventType.RENAMED)
        if EventFlags.ITEM_INODE_META_MOD in self.flags:
            types.append(EventType.INODE_META_MOD)
        if EventFlags.ITEM_FINDER_INFO_MOD in self.flags:
            types.append(EventType.FINDER_INFO_MOD)
        if EventFlags.ITEM_CHANGE_OWNER in self.flags:
            types.append(EventType.CHANGE_OWNER)
        if EventFlags.ITEM_XATTR_MOD in self.flags:
            types.append(EventType.XATTR_MOD)
        return types


# ============================================================================
# Extended Attributes
# ============================================================================

@dataclass
class QuarantineInfo:
    """Decoded com.apple.quarantine attribute."""
    flags: int  # quarantine flags
    timestamp: datetime  # when quarantined
    source_app: str  # "Safari", "Chrome", etc.
    uuid: str  # unique identifier

    @property
    def is_web_download(self) -> bool:
        """Check if file was downloaded from internet."""
        return (self.flags & 0x0080) != 0

    @property
    def is_safe_source(self) -> bool:
        """Check if from known safe source."""
        return (self.flags & 0x0001) != 0


@dataclass
class XattrRecord:
    """Extended Attributes for a file."""
    file_path: Path
    attributes: Dict[str, bytes]  # raw xattr key-value pairs

    # Parsed attributes
    quarantine_info: Optional[QuarantineInfo] = None
    download_urls: Optional[List[str]] = None
    download_timestamp: Optional[datetime] = None
    last_used_date: Optional[datetime] = None

    @property
    def has_quarantine(self) -> bool:
        return self.quarantine_info is not None

    @property
    def is_downloaded(self) -> bool:
        return self.download_urls is not None and len(self.download_urls) > 0


# ============================================================================
# Analysis Results
# ============================================================================

@dataclass
class Pattern:
    """Detected suspicious pattern."""
    pattern_type: str  # "mass_deletion", "encryption", "exfiltration"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    start_time: datetime
    end_time: datetime
    event_count: int
    affected_paths: List[Path]
    description: str
    indicators: Dict[str, Any] = field(default_factory=dict)  # additional pattern-specific data


@dataclass
class TimelineEntry:
    """Entry in timeline."""
    event: FSEvent
    priority_score: int
    priority_category: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    xattr: Optional[XattrRecord] = None
    related_events: List[FSEvent] = field(default_factory=list)  # grouped events
    notes: List[str] = field(default_factory=list)  # analyst notes


@dataclass
class Timeline:
    """Complete timeline of analysis."""
    entries: List[TimelineEntry]
    patterns: List[Pattern]
    statistics: Dict[str, Any]
    info: Dict[str, Any]  # Changed from metadata to info

    def sort_chronological(self) -> None:
        """Sort entries by timestamp."""
        self.entries.sort(key=lambda e: e.event.timestamp)

    def filter_by_priority(self, min_score: int) -> List[TimelineEntry]:
        """Return entries with score >= min_score."""
        return [e for e in self.entries if e.priority_score >= min_score]


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class FilterConfig:
    """Configuration for event filtering."""
    event_types: List[str] = field(default_factory=list)  # ["ItemRemoved", "ItemCreated"]
    path_patterns: List[str] = field(default_factory=list)  # regex patterns
    extensions: List[str] = field(default_factory=list)  # [".sh", ".command", ".app"]
    time_range: Optional[tuple] = None  # (start_datetime, end_datetime)
    min_priority: Optional[int] = None

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'FilterConfig':
        """Load configuration from YAML file."""
        import yaml
        with open(yaml_path, 'r') as f:
            config_data = yaml.safe_load(f)

        return cls(
            event_types=config_data.get('event_types', []),
            path_patterns=config_data.get('paths', {}).get('include', []),
            extensions=config_data.get('extensions', {}).get('executables', []),
            min_priority=config_data.get('min_priority')
        )


@dataclass
class ScoringWeights:
    """Weights for priority scoring."""
    event_type_weights: Dict[str, int] = field(default_factory=dict)  # {"Removed": 10}
    path_weights: Dict[str, int] = field(default_factory=dict)  # {"/System": 10}
    file_type_weights: Dict[str, int] = field(default_factory=dict)  # {".app": 10}
    quarantine_bonus: int = 5
    download_bonus: int = 5


# ============================================================================
# Results
# ============================================================================

@dataclass
class CollectionResult:
    """Result of artifact collection."""
    volume: VolumeInfo
    collection_time: datetime
    output_directory: Path
    files_copied: int
    total_size: int  # bytes
    checksums: Dict[str, str] = field(default_factory=dict)  # filename -> SHA-256
    errors: List[str] = field(default_factory=list)
    success: bool = True
