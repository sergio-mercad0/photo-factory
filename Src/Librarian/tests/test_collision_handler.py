"""
Tests for collision handling and duplicate detection.
"""
from pathlib import Path

import pytest

from Src.Librarian.collision_handler import (
    calculate_file_hash,
    check_duplicate_in_date_folder,
    generate_unique_filename,
    handle_collision,
)


class TestHashCalculation:
    """Test file hash calculation."""
    
    def test_calculate_hash_same_content(self, tmp_path: Path):
        """Test that same content produces same hash."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        content = b"identical content"
        file1.write_bytes(content)
        file2.write_bytes(content)
        
        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)
        
        assert hash1 is not None
        assert hash2 is not None
        assert hash1 == hash2
    
    def test_calculate_hash_different_content(self, tmp_path: Path):
        """Test that different content produces different hashes."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_bytes(b"content one")
        file2.write_bytes(b"content two")
        
        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)
        
        assert hash1 is not None
        assert hash2 is not None
        assert hash1 != hash2
    
    def test_calculate_hash_empty_file(self, tmp_path: Path):
        """Test hash calculation for empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_bytes(b"")
        
        hash_value = calculate_file_hash(empty_file)
        
        # Empty file should still produce a hash
        assert hash_value is not None
        assert len(hash_value) == 64  # SHA256 hex digest length


class TestCollisionHandling:
    """Test collision and duplicate handling."""
    
    def test_handle_collision_no_collision(self, tmp_path: Path):
        """Test handling when no collision exists."""
        source = tmp_path / "source.txt"
        destination = tmp_path / "dest" / "source.txt"
        destination.parent.mkdir()
        
        source.write_bytes(b"test content")
        file_hash = calculate_file_hash(source)
        
        should_move, final_path, reason = handle_collision(
            source, destination, file_hash
        )
        
        assert should_move is True
        assert final_path == destination
        assert "No collision" in reason
    
    def test_handle_collision_true_duplicate(self, tmp_path: Path):
        """Test handling when file is a true duplicate (same hash)."""
        source = tmp_path / "source.txt"
        destination = tmp_path / "dest" / "source.txt"
        destination.parent.mkdir()
        
        content = b"identical content"
        source.write_bytes(content)
        destination.write_bytes(content)  # Same content
        
        file_hash = calculate_file_hash(source)
        
        should_move, final_path, reason = handle_collision(
            source, destination, file_hash
        )
        
        assert should_move is False
        assert final_path is None
        assert "duplicate" in reason.lower()
    
    def test_handle_collision_name_collision(self, tmp_path: Path):
        """Test handling when same name but different content."""
        source = tmp_path / "source.txt"
        destination = tmp_path / "dest" / "source.txt"
        destination.parent.mkdir()
        
        source.write_bytes(b"new content")
        destination.write_bytes(b"different content")  # Different content
        
        file_hash = calculate_file_hash(source)
        
        should_move, final_path, reason = handle_collision(
            source, destination, file_hash
        )
        
        assert should_move is True
        assert final_path is not None
        assert final_path != destination
        assert final_path.name == "source_1.txt"
        assert "collision" in reason.lower()
    
    def test_generate_unique_filename(self, tmp_path: Path):
        """Test unique filename generation."""
        base_name = "test.jpg"
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        
        # First file doesn't exist - should return base name
        unique1 = generate_unique_filename(dest_dir, base_name)
        assert unique1.name == base_name
        
        # Create the file
        unique1.write_bytes(b"content")
        
        # Next call should return _1 variant
        unique2 = generate_unique_filename(dest_dir, base_name)
        assert unique2.name == "test_1.jpg"
        
        # Create that too
        unique2.write_bytes(b"content")
        
        # Next should be _2
        unique3 = generate_unique_filename(dest_dir, base_name)
        assert unique3.name == "test_2.jpg"


class TestDuplicateDetection:
    """Test duplicate detection in date folders."""
    
    def test_check_duplicate_in_date_folder_found(self, tmp_path: Path):
        """Test finding duplicate in date folder."""
        date_folder = tmp_path / "2025-12-25"
        date_folder.mkdir()
        
        content = b"duplicate content"
        existing_file = date_folder / "existing.jpg"
        existing_file.write_bytes(content)
        
        # Create source file with same content
        source_file = tmp_path / "source.jpg"
        source_file.write_bytes(content)
        
        file_hash = calculate_file_hash(source_file)
        
        # Should find the duplicate
        duplicate = check_duplicate_in_date_folder(
            date_folder, file_hash, exclude_path=None
        )
        
        assert duplicate is not None
        assert duplicate == existing_file
    
    def test_check_duplicate_in_date_folder_not_found(self, tmp_path: Path):
        """Test when no duplicate exists."""
        date_folder = tmp_path / "2025-12-25"
        date_folder.mkdir()
        
        existing_file = date_folder / "existing.jpg"
        existing_file.write_bytes(b"unique content")
        
        source_file = tmp_path / "source.jpg"
        source_file.write_bytes(b"different content")
        
        file_hash = calculate_file_hash(source_file)
        
        # Should not find duplicate
        duplicate = check_duplicate_in_date_folder(
            date_folder, file_hash, exclude_path=None
        )
        
        assert duplicate is None
    
    def test_check_duplicate_excludes_path(self, tmp_path: Path):
        """Test that excluded path is not considered."""
        date_folder = tmp_path / "2025-12-25"
        date_folder.mkdir()
        
        content = b"same content"
        excluded_file = date_folder / "excluded.jpg"
        excluded_file.write_bytes(content)
        
        source_file = tmp_path / "source.jpg"
        source_file.write_bytes(b"different content")
        
        file_hash = calculate_file_hash(source_file)
        
        # Should not find excluded file as duplicate
        duplicate = check_duplicate_in_date_folder(
            date_folder, file_hash, exclude_path=excluded_file
        )
        
        assert duplicate is None

