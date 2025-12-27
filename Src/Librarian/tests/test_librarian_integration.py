"""
Integration tests for Librarian service.

Tests the full workflow: file watching, date extraction, collision handling,
and file organization.
"""
import time
from pathlib import Path

import pytest

from Src.Librarian.collision_handler import calculate_file_hash
from Src.Librarian.librarian import LibrarianService
from Src.Librarian.metadata_extractor import extract_date_taken, get_date_path_components


class TestDateSorting:
    """Test that files are sorted into correct date folders."""
    
    def test_file_organized_by_date(
        self, mock_paths, mock_database, librarian_service, tmp_inbox: Path, tmp_storage: Path, create_test_file_with_date
    ):
        """Test that file is organized into correct YYYY/YYYY-MM-DD folder."""
        # Verify mock_paths is working
        from Src.Librarian import utils
        assert utils.get_storage_path() == tmp_storage, "Mock paths not working correctly"
        
        # Create a file with a specific date
        test_file = create_test_file_with_date(
            tmp_inbox,
            "photo.jpg",
            year=2025,
            month=6,
            day=15,
            content=b"test photo content"
        )
        
        # Use fixture service (already configured with mocks)
        service = librarian_service
        
        # Verify service is using mocked storage path
        assert service.storage_path == tmp_storage, f"Service using wrong storage path: {service.storage_path} != {tmp_storage}"
        
        # Process the file directly (bypass file watcher)
        service.process_file(test_file)
        
        # Verify file was moved to correct location
        expected_path = tmp_storage / "2025" / "2025-06-15" / "photo.jpg"
        assert expected_path.exists(), f"File not found at {expected_path}. Storage path: {service.storage_path}"
        assert not test_file.exists(), "Source file should be removed from inbox"
    
    def test_multiple_files_different_dates(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path, create_test_file_with_date
    ):
        """Test that multiple files with different dates go to correct folders."""
        # Create files with different dates
        file1 = create_test_file_with_date(
            tmp_inbox, "photo1.jpg", 2024, 1, 15, content=b"content1"
        )
        file2 = create_test_file_with_date(
            tmp_inbox, "photo2.jpg", 2025, 12, 25, content=b"content2"
        )
        file3 = create_test_file_with_date(
            tmp_inbox, "photo3.jpg", 2023, 7, 4, content=b"content3"
        )
        
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING"
        )
        
        # Process all files
        service.process_file(file1)
        service.process_file(file2)
        service.process_file(file3)
        
        # Verify all files in correct locations
        assert (tmp_storage / "2024" / "2024-01-15" / "photo1.jpg").exists()
        assert (tmp_storage / "2025" / "2025-12-25" / "photo2.jpg").exists()
        assert (tmp_storage / "2023" / "2023-07-04" / "photo3.jpg").exists()
        
        # Verify source files removed
        assert not file1.exists()
        assert not file2.exists()
        assert not file3.exists()


class TestDeduplication:
    """Test duplicate detection and handling."""
    
    def test_duplicate_file_deleted_from_inbox(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path, create_test_file
    ):
        """Test that duplicate file (same hash) is deleted from inbox."""
        # Create identical content
        content = b"identical photo content"
        
        # First file - will be moved to storage
        file1 = create_test_file(tmp_inbox, "photo.jpg", content=content)
        
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING"
        )
        
        # Extract date BEFORE processing (file will be moved)
        date_taken = extract_date_taken(file1)
        from Src.Librarian.metadata_extractor import get_date_path_components
        year, date_folder = get_date_path_components(date_taken)
        expected_path = tmp_storage / year / date_folder / "photo.jpg"
        
        # Process first file
        service.process_file(file1)
        
        # Verify first file moved to storage
        assert expected_path.exists()
        
        # Create duplicate file (same content, same name)
        file2 = create_test_file(tmp_inbox, "photo.jpg", content=content)
        
        # Process duplicate
        service.process_file(file2)
        
        # Verify duplicate was deleted from inbox
        assert not file2.exists(), "Duplicate should be deleted from inbox"
        
        # Verify only one file in storage
        assert expected_path.exists()
        # Should not have a _1 variant
        variant_path = tmp_storage / year / date_folder / "photo_1.jpg"
        assert not variant_path.exists()
    
    def test_duplicate_different_name_same_content(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path, create_test_file
    ):
        """Test duplicate detection when files have different names but same content."""
        content = b"same photo content"
        
        # First file
        file1 = create_test_file(tmp_inbox, "photo1.jpg", content=content)
        
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING"
        )
        
        # Extract date BEFORE processing (file will be moved)
        date_taken = extract_date_taken(file1)
        year, date_folder = get_date_path_components(date_taken)
        dest_folder = tmp_storage / year / date_folder
        
        # Process first file
        service.process_file(file1)
        
        # Create second file with different name but same content
        file2 = create_test_file(tmp_inbox, "photo2.jpg", content=content)
        
        # Process second file
        service.process_file(file2)
        
        # Verify duplicate was deleted
        assert not file2.exists()
        
        # Verify only one file in storage (the first one)
        files_in_storage = list(dest_folder.glob("*.jpg"))
        assert len(files_in_storage) == 1


class TestNameCollision:
    """Test name collision handling (same name, different content)."""
    
    def test_name_collision_renamed(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path, create_test_file
    ):
        """Test that file with same name but different content is renamed."""
        # First file
        file1 = create_test_file(
            tmp_inbox, "photo.jpg", content=b"first photo content"
        )
        
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING"
        )
        
        # Extract date BEFORE processing (file will be moved)
        date_taken = extract_date_taken(file1)
        year, date_folder = get_date_path_components(date_taken)
        dest_folder = tmp_storage / year / date_folder
        
        # Process first file
        service.process_file(file1)
        
        # Verify first file moved
        expected_path1 = dest_folder / "photo.jpg"
        assert expected_path1.exists()
        
        # Create second file with same name but different content
        file2 = create_test_file(
            tmp_inbox, "photo.jpg", content=b"different photo content"
        )
        
        # Process second file
        service.process_file(file2)
        
        # Verify second file was renamed and moved
        expected_path2 = dest_folder / "photo_1.jpg"
        assert expected_path2.exists(), "Collision should rename file to photo_1.jpg"
        assert not file2.exists(), "Source file should be removed"
        
        # Verify both files exist with different content
        assert expected_path1.read_bytes() == b"first photo content"
        assert expected_path2.read_bytes() == b"different photo content"
    
    def test_multiple_collisions_sequential_naming(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path, create_test_file
    ):
        """Test that multiple collisions get sequential names (_1, _2, etc.)."""
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING"
        )
        
        # Create first file
        file1 = create_test_file(tmp_inbox, "photo.jpg", content=b"content1")
        
        # Extract date BEFORE processing (file will be moved)
        date_taken = extract_date_taken(file1)
        from Src.Librarian.metadata_extractor import get_date_path_components
        year, date_folder = get_date_path_components(date_taken)
        dest_folder = tmp_storage / year / date_folder
        
        # Process first file
        service.process_file(file1)
        
        # Create and process second collision
        file2 = create_test_file(tmp_inbox, "photo.jpg", content=b"content2")
        service.process_file(file2)
        assert (dest_folder / "photo_1.jpg").exists()
        
        # Create and process third collision
        file3 = create_test_file(tmp_inbox, "photo.jpg", content=b"content3")
        service.process_file(file3)
        assert (dest_folder / "photo_2.jpg").exists()
        
        # Verify all three files exist
        assert (dest_folder / "photo.jpg").exists()
        assert (dest_folder / "photo_1.jpg").exists()
        assert (dest_folder / "photo_2.jpg").exists()


class TestFullWorkflow:
    """Test complete workflow scenarios."""
    
    def test_complete_workflow_mixed_scenarios(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path, create_test_file_with_date
    ):
        """Test a realistic workflow with multiple file types and scenarios."""
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING"
        )
        
        # Scenario 1: Normal file
        file1 = create_test_file_with_date(
            tmp_inbox, "vacation.jpg", 2025, 7, 10, content=b"vacation photo"
        )
        service.process_file(file1)
        
        # Scenario 2: Duplicate of file1 (same content)
        file2 = create_test_file_with_date(
            tmp_inbox, "vacation_copy.jpg", 2025, 7, 10, content=b"vacation photo"
        )
        service.process_file(file2)
        
        # Scenario 3: Name collision (same name as file1, different content)
        file3 = create_test_file_with_date(
            tmp_inbox, "vacation.jpg", 2025, 7, 10, content=b"different vacation photo"
        )
        service.process_file(file3)
        
        # Verify results
        dest_folder = tmp_storage / "2025" / "2025-07-10"
        
        # File1 should exist
        assert (dest_folder / "vacation.jpg").exists()
        
        # File2 (duplicate) should be deleted
        assert not file2.exists()
        
        # File3 (collision) should be renamed
        assert (dest_folder / "vacation_1.jpg").exists()
        
        # Only 2 files in storage (original + renamed collision)
        files = list(dest_folder.glob("*.jpg"))
        assert len(files) == 2


class TestDenyListFiltering:
    """Test that files matching deny list patterns are not processed."""
    
    def test_hidden_file_not_processed(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path, create_test_file_with_date
    ):
        """Test that hidden files (starting with .) are not processed."""
        # Create a hidden file
        hidden_file = create_test_file_with_date(
            tmp_inbox, ".nomedia", 2025, 6, 15, content=b"hidden file content"
        )
        
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING"
        )
        
        # Process the file
        service.process_file(hidden_file)
        
        # Verify file was NOT moved to storage
        dest_folder = tmp_storage / "2025" / "2025-06-15"
        assert not dest_folder.exists(), "Date folder should not be created for filtered file"
        
        # Verify file still exists in inbox (not processed)
        assert hidden_file.exists(), "Hidden file should remain in inbox"
    
    def test_syncthing_metadata_not_processed(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path, create_test_file_with_date
    ):
        """Test that Syncthing metadata files are not processed."""
        # Create Syncthing metadata file
        syncthing_file = create_test_file_with_date(
            tmp_inbox,
            "syncthing-folder-817eaa.txt",
            2025,
            6,
            15,
            content=b"syncthing metadata"
        )
        
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING"
        )
        
        # Process the file
        service.process_file(syncthing_file)
        
        # Verify file was NOT moved to storage
        dest_folder = tmp_storage / "2025" / "2025-06-15"
        assert not dest_folder.exists(), "Date folder should not be created for filtered file"
        
        # Verify file still exists in inbox
        assert syncthing_file.exists(), "Syncthing metadata file should remain in inbox"
    
    def test_mixed_filtered_and_valid_files(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path, create_test_file_with_date
    ):
        """Test that valid files are processed while filtered files are ignored."""
        # Create a valid photo file
        valid_file = create_test_file_with_date(
            tmp_inbox, "photo.jpg", 2025, 6, 15, content=b"valid photo"
        )
        
        # Create filtered files
        hidden_file = create_test_file_with_date(
            tmp_inbox, ".nomedia", 2025, 6, 15, content=b"hidden"
        )
        syncthing_file = create_test_file_with_date(
            tmp_inbox,
            "syncthing-folder-abc.txt",
            2025,
            6,
            15,
            content=b"syncthing"
        )
        
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING"
        )
        
        # Process all files
        service.process_file(valid_file)
        service.process_file(hidden_file)
        service.process_file(syncthing_file)
        
        # Verify only valid file was processed
        dest_folder = tmp_storage / "2025" / "2025-06-15"
        assert (dest_folder / "photo.jpg").exists(), "Valid file should be processed"
        
        # Verify filtered files remain in inbox
        assert hidden_file.exists(), "Hidden file should remain in inbox"
        assert syncthing_file.exists(), "Syncthing file should remain in inbox"
        
        # Verify only one file in storage
        files_in_storage = list(dest_folder.glob("*"))
        assert len(files_in_storage) == 1, "Only valid file should be in storage"
    
    def test_android_thumbnails_not_processed(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path, create_test_file_with_date
    ):
        """Test that Android thumbnail files are not processed."""
        thumbnail_file = create_test_file_with_date(
            tmp_inbox, ".thumbnails", 2025, 6, 15, content=b"thumbnails"
        )
        
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING"
        )
        
        service.process_file(thumbnail_file)
        
        # Verify not processed
        dest_folder = tmp_storage / "2025" / "2025-06-15"
        assert not dest_folder.exists()
        assert thumbnail_file.exists()

