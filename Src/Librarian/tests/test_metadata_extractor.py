"""
Tests for metadata extraction (date extraction).
"""
from datetime import datetime
from pathlib import Path

import pytest

from Src.Librarian.metadata_extractor import (
    extract_date_taken,
    get_date_path_components,
)


class TestDateExtraction:
    """Test date extraction from files."""
    
    def test_extract_date_from_file_mtime(self, tmp_path: Path):
        """Test date extraction falls back to file modification time."""
        # Create a file with a specific modification time
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"fake image data")
        
        # Set modification time to a known date
        target_date = datetime(2025, 6, 15, 14, 30, 0)
        import os
        os.utime(test_file, (target_date.timestamp(), target_date.timestamp()))
        
        # Extract date
        extracted_date = extract_date_taken(test_file)
        
        # Should match the file's modification time (within 1 second tolerance)
        assert extracted_date is not None
        assert abs((extracted_date - target_date).total_seconds()) < 1
    
    def test_extract_date_returns_datetime(self, tmp_path: Path):
        """Test that extract_date_taken returns a datetime object."""
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"test content")
        
        extracted_date = extract_date_taken(test_file)
        
        assert extracted_date is not None
        assert isinstance(extracted_date, datetime)
    
    def test_get_date_path_components(self):
        """Test date path component generation."""
        test_date = datetime(2025, 12, 25, 10, 30, 0)
        
        year, date_folder = get_date_path_components(test_date)
        
        assert year == "2025"
        assert date_folder == "2025-12-25"
    
    def test_get_date_path_components_edge_cases(self):
        """Test date path components with edge cases."""
        # January 1st
        date1 = datetime(2020, 1, 1, 0, 0, 0)
        year1, folder1 = get_date_path_components(date1)
        assert year1 == "2020"
        assert folder1 == "2020-01-01"
        
        # December 31st
        date2 = datetime(1999, 12, 31, 23, 59, 59)
        year2, folder2 = get_date_path_components(date2)
        assert year2 == "1999"
        assert folder2 == "1999-12-31"
        
        # Leap year
        date3 = datetime(2024, 2, 29, 12, 0, 0)
        year3, folder3 = get_date_path_components(date3)
        assert year3 == "2024"
        assert folder3 == "2024-02-29"

