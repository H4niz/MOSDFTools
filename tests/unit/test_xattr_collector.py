"""
Unit tests for XattrCollector
"""

import pytest
import platform
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from mfaa.collector.xattr_collector import XattrCollector
from mfaa.models import XattrRecord


pytestmark = pytest.mark.skipif(
    platform.system() != 'Darwin',
    reason="XattrCollector requires macOS"
)


class TestXattrCollector:
    """Test cases for XattrCollector."""

    def test_init_with_parsing(self):
        """Test initialization with parsing enabled."""
        collector = XattrCollector(parse_attributes=True)
        assert collector.parse_attributes is True
        assert collector.parser is not None

    def test_init_without_parsing(self):
        """Test initialization without parsing."""
        collector = XattrCollector(parse_attributes=False)
        assert collector.parse_attributes is False
        assert collector.parser is None

    @patch('xattr.xattr')
    def test_collect_xattr(self, mock_xattr, tmp_path):
        """Test collecting extended attributes."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Mock xattr
        mock_xattr_obj = MagicMock()
        mock_xattr_obj.list.return_value = [
            b'com.apple.quarantine',
            b'user.custom'
        ]
        mock_xattr_obj.get.side_effect = lambda x: {
            b'com.apple.quarantine': b'0000;00000000;Test;UUID',
            b'user.custom': b'custom value'
        }[x]

        mock_xattr.return_value = mock_xattr_obj

        collector = XattrCollector(parse_attributes=False)
        record = collector.collect_xattr(test_file)

        assert isinstance(record, XattrRecord)
        assert record.file_path == test_file
        assert len(record.attributes) == 2
        assert 'com.apple.quarantine' in record.attributes

    def test_collect_xattr_nonexistent_file(self):
        """Test collecting xattr from nonexistent file."""
        collector = XattrCollector()

        with pytest.raises(FileNotFoundError):
            collector.collect_xattr(Path("/nonexistent/file.txt"))

    @patch('xattr.xattr')
    def test_collect_directory(self, mock_xattr, tmp_path):
        """Test collecting xattr from directory."""
        # Create test directory with files
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        (test_dir / "file1.txt").write_text("file 1")
        (test_dir / "file2.txt").write_text("file 2")

        # Mock xattr
        mock_xattr_obj = MagicMock()
        mock_xattr_obj.list.return_value = [b'user.test']
        mock_xattr_obj.get.return_value = b'test value'
        mock_xattr.return_value = mock_xattr_obj

        collector = XattrCollector(parse_attributes=False)
        records = collector.collect_directory(test_dir, recursive=False)

        assert isinstance(records, list)
        assert len(records) == 2
        assert all(isinstance(r, XattrRecord) for r in records)

    @patch('xattr.xattr')
    def test_collect_directory_recursive(self, mock_xattr, tmp_path):
        """Test recursive directory collection."""
        # Create nested structure
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        sub_dir = test_dir / "subdir"
        sub_dir.mkdir()

        (test_dir / "file1.txt").write_text("file 1")
        (sub_dir / "file2.txt").write_text("file 2")

        # Mock xattr
        mock_xattr_obj = MagicMock()
        mock_xattr_obj.list.return_value = [b'user.test']
        mock_xattr_obj.get.return_value = b'test value'
        mock_xattr.return_value = mock_xattr_obj

        collector = XattrCollector(parse_attributes=False)
        records = collector.collect_directory(test_dir, recursive=True)

        assert len(records) == 2

    @patch('xattr.xattr')
    def test_has_quarantine(self, mock_xattr, tmp_path):
        """Test checking for quarantine attribute."""
        test_file = tmp_path / "test.dmg"
        test_file.write_text("test")

        mock_xattr_obj = MagicMock()
        mock_xattr_obj.list.return_value = [b'com.apple.quarantine']
        mock_xattr.return_value = mock_xattr_obj

        collector = XattrCollector()
        has_quarantine = collector.has_quarantine(test_file)

        assert has_quarantine is True

    @patch('xattr.xattr')
    def test_has_download_metadata(self, mock_xattr, tmp_path):
        """Test checking for download metadata."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test")

        mock_xattr_obj = MagicMock()
        mock_xattr_obj.list.return_value = [b'com.apple.metadata:kMDItemWhereFroms']
        mock_xattr.return_value = mock_xattr_obj

        collector = XattrCollector()
        has_download = collector.has_download_metadata(test_file)

        assert has_download is True

    def test_filter_by_attributes(self):
        """Test filtering records by attributes."""
        # Create mock records
        records = [
            XattrRecord(
                file_path=Path("/file1"),
                attributes={},
                quarantine_info=None
            ),
            XattrRecord(
                file_path=Path("/file2"),
                attributes={},
                quarantine_info=Mock()  # Has quarantine
            )
        ]

        collector = XattrCollector()
        filtered = collector.filter_by_attributes(records, has_quarantine=True)

        assert len(filtered) == 1
        assert filtered[0].file_path == Path("/file2")

    def test_get_downloaded_files(self):
        """Test getting downloaded files."""
        records = [
            XattrRecord(
                file_path=Path("/file1"),
                attributes={},
                download_urls=None
            ),
            XattrRecord(
                file_path=Path("/file2"),
                attributes={},
                download_urls=["https://example.com/file.dmg"]
            )
        ]

        collector = XattrCollector()
        downloaded = collector.get_downloaded_files(records)

        assert len(downloaded) == 1
        assert downloaded[0].file_path == Path("/file2")

    def test_get_quarantined_files(self):
        """Test getting quarantined files."""
        records = [
            XattrRecord(
                file_path=Path("/file1"),
                attributes={},
                quarantine_info=None
            ),
            XattrRecord(
                file_path=Path("/file2"),
                attributes={},
                quarantine_info=Mock()
            )
        ]

        collector = XattrCollector()
        quarantined = collector.get_quarantined_files(records)

        assert len(quarantined) == 1
        assert quarantined[0].file_path == Path("/file2")

    def test_export_to_dict(self):
        """Test exporting XattrRecord to dictionary."""
        from datetime import datetime

        record = XattrRecord(
            file_path=Path("/test/file.dmg"),
            attributes={'user.test': b'test value'},
            download_urls=["https://example.com/file.dmg"],
            download_timestamp=datetime(2025, 10, 26, 12, 0, 0)
        )

        collector = XattrCollector()
        export_data = collector.export_to_dict(record)

        assert export_data['file_path'] == '/test/file.dmg'
        assert export_data['attributes_count'] == 1
        assert 'download_urls' in export_data
        assert export_data['download_urls'][0] == "https://example.com/file.dmg"
        assert 'download_timestamp' in export_data
