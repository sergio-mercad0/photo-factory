"""
Tests for file watching functionality.

Note: Full end-to-end file watching is tested in test_librarian_integration.py.
These tests focus on verifying the periodic scan mechanism works.
"""
import time
from pathlib import Path

import pytest

from Src.Librarian.file_watcher import FileWatcher
from Src.Librarian.librarian import LibrarianService


class TestFileWatcher:
    """Test file watcher functionality."""
    
    def test_periodic_scan_mechanism_exists(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path
    ):
        """Test that periodic scan mechanism is implemented and functional."""
        def process_callback(file_path: Path):
            pass  # Dummy callback
        
        watcher = FileWatcher(
            process_callback,
            stability_delay=0.1,
            min_file_age=0.1,
            periodic_scan_interval=0.5
        )
        
        # Verify periodic scan is configured
        assert watcher.periodic_scan_interval == 0.5
        assert hasattr(watcher, '_scan_and_register_files')
        assert hasattr(watcher, '_periodic_scan_loop')
        
        try:
            watcher.start()
            
            # Verify scan thread is running
            assert watcher.scan_thread is not None
            assert watcher.scan_thread.is_alive(), "Periodic scan thread should be running"
        
        finally:
            watcher.stop()
    
    def test_file_watcher_has_periodic_scan(
        self, mock_paths, tmp_inbox: Path, tmp_storage: Path
    ):
        """Test that file watcher includes periodic scanning."""
        service = LibrarianService(
            stability_delay=0.1,
            min_file_age=0.1,
            log_level="WARNING",
            periodic_scan_interval=60.0
        )
        
        # Verify periodic scan is configured
        assert service.file_watcher.periodic_scan_interval == 60.0
        assert service.file_watcher.scan_thread is None  # Not started yet
        
        service.start()
        try:
            # Verify scan thread is running
            assert service.file_watcher.scan_thread is not None
            assert service.file_watcher.scan_thread.is_alive()
        finally:
            service.stop()
