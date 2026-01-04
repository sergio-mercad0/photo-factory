"""
Unit tests for utility functions.
"""
from pathlib import Path

import pytest

from Src.Librarian.utils import should_process_file


class TestFileFiltering:
    """Test the deny list file filtering functionality."""
    
    def test_normal_photo_file_passes(self, tmp_path: Path):
        """Test that normal photo files pass the filter."""
        test_file = tmp_path / "photo.jpg"
        test_file.write_bytes(b"test content")
        
        assert should_process_file(test_file) is True
    
    def test_normal_video_file_passes(self, tmp_path: Path):
        """Test that normal video files pass the filter."""
        test_file = tmp_path / "video.mp4"
        test_file.write_bytes(b"test content")
        
        assert should_process_file(test_file) is True
    
    def test_hidden_file_filtered(self, tmp_path: Path):
        """Test that hidden files (starting with .) are filtered out."""
        test_file = tmp_path / ".nomedia"
        test_file.write_bytes(b"test content")
        
        assert should_process_file(test_file) is False
    
    def test_android_thumbnails_filtered(self, tmp_path: Path):
        """Test that Android thumbnail files are filtered out."""
        test_file = tmp_path / ".thumbnails"
        test_file.write_bytes(b"test content")
        
        assert should_process_file(test_file) is False
    
    def test_syncthing_metadata_filtered(self, tmp_path: Path):
        """Test that Syncthing metadata files are filtered out."""
        test_file = tmp_path / "syncthing-folder-817eaa.txt"
        test_file.write_bytes(b"test content")
        
        assert should_process_file(test_file) is False
    
    def test_syncthing_metadata_variations_filtered(self, tmp_path: Path):
        """Test various Syncthing metadata file patterns are filtered."""
        patterns = [
            "syncthing-folder-abc123.txt",
            "syncthing-folder-xyz.txt",
            "syncthing-folder-1234567890abcdef.txt",
        ]
        
        for pattern in patterns:
            test_file = tmp_path / pattern
            test_file.write_bytes(b"test content")
            assert should_process_file(test_file) is False, f"Pattern {pattern} should be filtered"
    
    def test_syncthing_metadata_non_txt_not_filtered(self, tmp_path: Path):
        """Test that files matching syncthing pattern but not .txt are not filtered."""
        # This shouldn't match the pattern (needs .txt extension)
        test_file = tmp_path / "syncthing-folder-abc123.jpg"
        test_file.write_bytes(b"test content")
        
        assert should_process_file(test_file) is True
    
    def test_file_with_dot_in_middle_passes(self, tmp_path: Path):
        """Test that files with dots in the middle (not at start) pass the filter."""
        test_file = tmp_path / "photo.backup.jpg"
        test_file.write_bytes(b"test content")
        
        assert should_process_file(test_file) is True
    
    def test_android_trashed_file_filtered(self, tmp_path: Path):
        """Test that Android trashed files are filtered out."""
        test_file = tmp_path / ".trashed-12345"
        test_file.write_bytes(b"test content")
        
        assert should_process_file(test_file) is False
    
    def test_ds_store_filtered(self, tmp_path: Path):
        """Test that .DS_Store files (macOS) are filtered out."""
        test_file = tmp_path / ".DS_Store"
        test_file.write_bytes(b"test content")
        
        assert should_process_file(test_file) is False
    
    def test_unknown_extension_passes(self, tmp_path: Path):
        """Test that files with unknown extensions still pass (deny list approach)."""
        test_file = tmp_path / "photo.xyz"
        test_file.write_bytes(b"test content")
        
        assert should_process_file(test_file) is True

