"""
Shared pytest fixtures for Librarian tests.
"""
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

import pytest

from Src.Librarian import utils


@pytest.fixture
def tmp_inbox(tmp_path: Path) -> Path:
    """Create a temporary inbox directory."""
    inbox = tmp_path / "Photos_Inbox"
    inbox.mkdir()
    return inbox


@pytest.fixture
def tmp_storage(tmp_path: Path) -> Path:
    """Create a temporary storage directory."""
    storage = tmp_path / "Storage" / "Originals"
    storage.mkdir(parents=True)
    return storage


@pytest.fixture
def mock_paths(monkeypatch, tmp_path: Path, tmp_inbox: Path, tmp_storage: Path):
    """
    Mock the path resolution functions to use temporary directories.
    
    This allows tests to run without touching the real filesystem.
    """
    # Import librarian module to patch the imported functions
    from Src.Librarian import librarian
    
    # Store original functions
    original_get_project_root = utils.get_project_root
    original_get_inbox_path = utils.get_inbox_path
    original_get_storage_path = utils.get_storage_path
    
    # Override in utils module
    monkeypatch.setattr(utils, "get_project_root", lambda: tmp_path)
    monkeypatch.setattr(utils, "get_inbox_path", lambda: tmp_inbox)
    monkeypatch.setattr(utils, "get_storage_path", lambda: tmp_storage)
    
    # Also override in librarian module (since it imports the functions directly)
    monkeypatch.setattr(librarian, "get_storage_path", lambda: tmp_storage)
    
    yield {
        "project_root": tmp_path,
        "inbox": tmp_inbox,
        "storage": tmp_storage,
    }
    
    # Restore original functions (though pytest does this automatically)
    monkeypatch.setattr(utils, "get_project_root", original_get_project_root)
    monkeypatch.setattr(utils, "get_inbox_path", original_get_inbox_path)
    monkeypatch.setattr(utils, "get_storage_path", original_get_storage_path)


@pytest.fixture
def create_test_file(tmp_path: Path) -> Callable:
    """
    Factory fixture to create test files with specific properties.
    
    Returns a function that creates files with:
    - Optional content (for hash control)
    - Optional modification time (for date extraction)
    """
    def _create_file(
        location: Path,
        filename: str,
        content: bytes = b"test file content",
        mtime: float | None = None
    ) -> Path:
        """
        Create a test file.
        
        Args:
            location: Directory where file should be created
            filename: Name of the file
            content: File content (default: "test file content")
            mtime: Modification time as Unix timestamp (default: current time)
        
        Returns:
            Path to created file
        """
        file_path = location / filename
        file_path.write_bytes(content)
        
        # Set modification time if specified
        if mtime is not None:
            os.utime(file_path, (mtime, mtime))
        
        return file_path
    
    return _create_file


@pytest.fixture
def create_test_file_with_date(tmp_path: Path) -> Callable:
    """
    Factory fixture to create test files with a specific date.
    
    Returns a function that creates files with a specific date for testing
    date-based organization.
    """
    def _create_file_with_date(
        location: Path,
        filename: str,
        year: int,
        month: int,
        day: int,
        hour: int = 12,
        minute: int = 0,
        content: bytes = b"test file content"
    ) -> Path:
        """
        Create a test file with a specific date.
        
        Args:
            location: Directory where file should be created
            filename: Name of the file
            year, month, day, hour, minute: Date components
            content: File content
        
        Returns:
            Path to created file
        """
        # Create datetime and convert to timestamp
        file_date = datetime(year, month, day, hour, minute)
        mtime = file_date.timestamp()
        
        file_path = location / filename
        file_path.write_bytes(content)
        os.utime(file_path, (mtime, mtime))
        
        return file_path
    
    return _create_file_with_date

