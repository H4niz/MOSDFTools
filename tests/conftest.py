"""
Pytest configuration and fixtures
"""

import pytest
from pathlib import Path
from datetime import datetime
from mfaa.models import VolumeInfo, FSEvent, EventFlags


@pytest.fixture
def sample_volume():
    """Create a sample VolumeInfo object."""
    return VolumeInfo(
        name="TestVolume",
        mount_point=Path("/Volumes/TestVolume"),
        filesystem_type="apfs",
        device_node="/dev/disk3s1",
        total_size=500000000000,
        available_size=250000000000,
        encryption_enabled=True
    )


@pytest.fixture
def sample_fsevent():
    """Create a sample FSEvent object."""
    return FSEvent(
        event_id=12345,
        timestamp=datetime(2025, 10, 26, 12, 0, 0),
        path=Path("/Users/test/Documents/file.txt"),
        flags=EventFlags.ITEM_CREATED | EventFlags.ITEM_IS_FILE,
        node_id=67890
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
