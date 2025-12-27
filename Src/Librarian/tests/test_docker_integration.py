"""
Integration tests for Docker services and full pipeline.

These tests verify:
1. Full pipeline: Syncthing → Photos_Inbox → Librarian → Storage
2. Service health check mechanisms
3. Volume mount paths and file system integration
4. End-to-end workflow validation

Note: These tests use mocked paths and don't require Docker to be running.
For testing with actual Docker services, see README.md.
"""
import time
from pathlib import Path

import pytest

from Src.Librarian.librarian import LibrarianService


class TestDockerPipelineIntegration:
    """Test the full Docker service pipeline integration."""
    
    def test_full_pipeline_syncthing_to_storage(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path, create_test_file_with_date
    ):
        """
        Test the complete pipeline: file appears in inbox → processed → organized.
        
        This simulates:
        1. Syncthing syncs a file to Photos_Inbox
        2. Librarian detects and processes it
        3. File is organized into Storage/Originals/{YYYY}/{YYYY-MM-DD}/
        """
        # Simulate Syncthing syncing a file to inbox
        test_file = create_test_file_with_date(
            tmp_inbox,
            "photo_from_phone.jpg",
            year=2025,
            month=12,
            day=27,
            content=b"synced photo content"
        )
        
        # Verify file exists in inbox (Syncthing's job is done)
        assert test_file.exists(), "File should be in inbox after Syncthing sync"
        
        # Start Librarian service and process file directly
        # (This tests the integration logic, not the async file watcher timing)
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING"
        )
        
        # Process the file (simulates what happens after file watcher detects it)
        service.process_file(test_file)
        
        # Verify file was moved to Storage
        expected_path = tmp_storage / "2025" / "2025-12-27" / "photo_from_phone.jpg"
        assert expected_path.exists(), \
            f"File should be organized in Storage at {expected_path}"
        
        # Verify file was removed from inbox
        assert not test_file.exists(), \
            "File should be removed from inbox after processing"
        
        # Verify file content is preserved
        assert expected_path.read_bytes() == b"synced photo content", \
            "File content should be preserved during move"
    
    def test_multiple_files_from_syncthing_processed_sequentially(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path, create_test_file_with_date
    ):
        """
        Test that multiple files synced by Syncthing are all processed correctly.
        
        Simulates Syncthing syncing multiple files at once.
        """
        # Simulate Syncthing syncing multiple files
        files = [
            create_test_file_with_date(
                tmp_inbox,
                f"photo_{i}.jpg",
                year=2025,
                month=12,
                day=27,
                hour=10 + i,
                content=f"photo content {i}".encode()
            )
            for i in range(3)
        ]
        
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING"
        )
        
        # Process all files
        for file_path in files:
            service.process_file(file_path)
        
        # Verify all files were organized
        for i, original_file in enumerate(files):
            expected_path = tmp_storage / "2025" / "2025-12-27" / f"photo_{i}.jpg"
            assert expected_path.exists(), \
                f"File {i} should be organized in Storage"
            assert not original_file.exists(), \
                f"File {i} should be removed from inbox"
    
    def test_syncthing_duplicate_handled_correctly(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path, create_test_file
    ):
        """
        Test that if Syncthing syncs a duplicate file, it's handled correctly.
        
        Simulates Syncthing syncing the same file twice (e.g., from different devices).
        """
        # Create a file in Storage (already processed)
        storage_file = tmp_storage / "2025" / "2025-12-27" / "existing_photo.jpg"
        storage_file.parent.mkdir(parents=True, exist_ok=True)
        storage_file.write_bytes(b"photo content")
        
        # Simulate Syncthing syncing the same file again
        inbox_file = create_test_file(
            tmp_inbox,
            "existing_photo.jpg",
            content=b"photo content"  # Same content = duplicate
        )
        
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING"
        )
        
        # Process the duplicate file
        service.process_file(inbox_file)
        
        # Verify duplicate was deleted from inbox (not moved)
        assert not inbox_file.exists(), \
            "Duplicate file should be deleted from inbox"
        
        # Verify original file in Storage is unchanged
        assert storage_file.exists(), \
            "Original file in Storage should remain"
        assert storage_file.read_bytes() == b"photo content", \
            "Original file content should be unchanged"
    
    def test_volume_mount_paths_resolved_correctly(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path
    ):
        """
        Test that volume mount paths are resolved correctly.
        
        Verifies that the service correctly resolves paths for:
        - Photos_Inbox (mounted from host)
        - Storage/Originals (mounted from host)
        """
        from Src.Librarian import utils
        
        # Verify paths are resolved correctly
        inbox_path = utils.get_inbox_path()
        storage_path = utils.get_storage_path()
        
        assert inbox_path == tmp_inbox, \
            f"Inbox path should resolve to {tmp_inbox}, got {inbox_path}"
        assert storage_path == tmp_storage, \
            f"Storage path should resolve to {tmp_storage}, got {storage_path}"
        
        # Verify paths exist and are directories
        assert inbox_path.exists(), "Inbox path should exist"
        assert inbox_path.is_dir(), "Inbox path should be a directory"
        assert storage_path.exists(), "Storage path should exist"
        assert storage_path.is_dir(), "Storage path should be a directory"


class TestServiceHealthChecks:
    """Test service health check mechanisms."""
    
    def test_librarian_health_check_mechanism(self, mock_paths):
        """
        Test that Librarian service health check mechanism works.
        
        Verifies that the service can run its health check (pytest tests).
        """
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING"
        )
        
        # Health check should be able to run pytest
        # (In actual Docker, this would be: pytest Src/Librarian/tests/ --tb=short -q)
        # Here we just verify the service is functional
        try:
            service.start()
            assert service.file_watcher is not None, \
                "File watcher should be initialized"
            assert service.running, \
                "Service should be running"
            assert service.file_watcher.observer is not None, \
                "File watcher observer should be initialized"
            assert service.file_watcher.observer.is_alive(), \
                "File watcher observer should be alive"
        finally:
            service.stop()
    
    def test_service_handles_missing_directories_gracefully(self, mock_paths, tmp_inbox: Path, tmp_storage: Path):
        """
        Test that service handles missing directories gracefully.
        
        Verifies idempotent behavior - service should create directories if needed.
        """
        # Remove directories to test creation
        if tmp_storage.exists():
            import shutil
            shutil.rmtree(tmp_storage.parent)
        
        # Service should create directories during initialization
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING"
        )
        
        try:
            # Service should create storage directory on init
            assert tmp_storage.exists(), \
                "Service should create storage directory during initialization"
            
            # Start service - should create inbox if needed
            service.start()
            
            # Verify inbox exists (created by file watcher)
            assert tmp_inbox.exists(), \
                "Service should create inbox directory when starting"
        
        finally:
            service.stop()

