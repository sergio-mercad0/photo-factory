"""
Project-wide pytest configuration and pytest-bdd fixtures.

This conftest.py provides:
- Shared fixtures for cross-service integration tests
- pytest-bdd step definitions that apply across all services
- Test markers for two-phase testing strategy
"""
import os
import sys
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

# Add project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Test Markers Configuration
# =============================================================================
def pytest_configure(config):
    """Register custom markers for two-phase testing strategy."""
    config.addinivalue_line(
        "markers", "unit: Build-time safe tests (mocked, no I/O, no DB)"
    )
    config.addinivalue_line(
        "markers", "integration: Runtime tests (requires DB, services)"
    )
    config.addinivalue_line(
        "markers", "browser: Runtime tests (uses browser tools)"
    )
    config.addinivalue_line(
        "markers", "real_asset: Runtime tests (uses actual photos/videos)"
    )
    config.addinivalue_line(
        "markers", "slow: Decoupled from build (media processing, long I/O)"
    )
    config.addinivalue_line(
        "markers", "heavy: Decoupled from build (GPU, ML inference)"
    )


# =============================================================================
# Project-Wide Fixtures
# =============================================================================
@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture
def tmp_inbox(tmp_path: Path) -> Path:
    """Create a temporary inbox directory for testing."""
    inbox = tmp_path / "Photos_Inbox"
    inbox.mkdir()
    return inbox


@pytest.fixture
def tmp_storage(tmp_path: Path) -> Path:
    """Create a temporary storage directory for testing."""
    storage = tmp_path / "Storage" / "Originals"
    storage.mkdir(parents=True)
    return storage


@pytest.fixture
def tmp_derivatives(tmp_path: Path) -> Path:
    """Create a temporary derivatives directory for testing."""
    derivatives = tmp_path / "Storage" / "Derivatives"
    derivatives.mkdir(parents=True)
    return derivatives


@pytest.fixture
def mock_database_session():
    """
    Create a mock database session for unit tests.
    
    Use this fixture to avoid database connections in build-time tests.
    """
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=None)
    mock_session.commit = MagicMock()
    mock_session.rollback = MagicMock()
    mock_session.close = MagicMock()
    mock_session.query = MagicMock(return_value=mock_session)
    mock_session.filter = MagicMock(return_value=mock_session)
    mock_session.first = MagicMock(return_value=None)
    mock_session.add = MagicMock()
    return mock_session


@pytest.fixture
def mock_docker_client():
    """
    Create a mock Docker client for unit tests.
    
    Use this fixture to test Docker-related code without Docker running.
    """
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_container.status = "running"
    mock_container.health = "healthy"
    mock_container.attrs = {
        "State": {"Health": {"Status": "healthy"}},
        "Config": {"Labels": {"com.docker.compose.project": "photo_factory"}}
    }
    mock_client.containers.list.return_value = [mock_container]
    mock_client.containers.get.return_value = mock_container
    return mock_client


# =============================================================================
# pytest-bdd Fixtures (for Gherkin feature files)
# =============================================================================
try:
    from pytest_bdd import given, when, then, parsers
    
    @pytest.fixture
    def bdd_context():
        """
        Shared context dictionary for passing data between BDD steps.
        
        Usage in step definitions:
            @given("a photo in the inbox")
            def photo_in_inbox(bdd_context, tmp_inbox):
                bdd_context["photo_path"] = tmp_inbox / "test.jpg"
                # ... create file ...
            
            @when("the librarian processes the inbox")
            def librarian_processes(bdd_context):
                # ... process ...
                bdd_context["result"] = result
            
            @then("the photo should be organized")
            def photo_organized(bdd_context):
                assert bdd_context["result"].success
        """
        return {}

except ImportError:
    # pytest-bdd not installed, skip BDD fixtures
    pass


# =============================================================================
# Test File Creation Helpers
# =============================================================================
@pytest.fixture
def create_test_file():
    """
    Factory fixture to create test files with specific content.
    
    Returns a function that creates files and optionally sets modification time.
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
        
        if mtime is not None:
            os.utime(file_path, (mtime, mtime))
        
        return file_path
    
    return _create_file


@pytest.fixture
def create_test_image(tmp_path: Path):
    """
    Factory fixture to create minimal valid image files for testing.
    
    Note: These are tiny valid images, not realistic photos.
    Use @real_asset marker for tests with actual photos.
    """
    def _create_image(
        location: Path,
        filename: str = "test.jpg"
    ) -> Path:
        """Create a minimal valid JPEG file."""
        # Minimal valid JPEG (1x1 pixel, gray)
        # This is a real JPEG that image libraries will accept
        jpeg_data = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00,
            0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB,
            0x00, 0x43, 0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07,
            0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B,
            0x0B, 0x0C, 0x19, 0x12, 0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E,
            0x1D, 0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C,
            0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29, 0x2C, 0x30, 0x31, 0x34, 0x34,
            0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34,
            0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01, 0x00, 0x01, 0x01,
            0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00, 0x01, 0x05,
            0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01,
            0x03, 0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00,
            0x01, 0x7D, 0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21,
            0x31, 0x41, 0x06, 0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32,
            0x81, 0x91, 0xA1, 0x08, 0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1,
            0xF0, 0x24, 0x33, 0x62, 0x72, 0x82, 0x09, 0x0A, 0x16, 0x17, 0x18,
            0x19, 0x1A, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x34, 0x35, 0x36,
            0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49,
            0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x63, 0x64,
            0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75, 0x76, 0x77,
            0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A,
            0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
            0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5,
            0xB6, 0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7,
            0xC8, 0xC9, 0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9,
            0xDA, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA,
            0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF,
            0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD5,
            0xDB, 0x20, 0xA8, 0xF1, 0x45, 0xFF, 0xD9
        ])
        
        file_path = location / filename
        file_path.write_bytes(jpeg_data)
        return file_path
    
    return _create_image

