"""
Shared library pytest configuration and fixtures.

This conftest.py provides:
- Fixtures for testing shared components (database, heartbeat, models)
- Mock fixtures for infrastructure monitoring tests
- pytest-bdd step definitions for shared behavior specs
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# Database Fixtures
# =============================================================================
@pytest.fixture
def mock_engine():
    """
    Mock SQLAlchemy engine for testing database module.
    
    Use this to test database functions without a real PostgreSQL connection.
    """
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__ = MagicMock()
    mock_engine.connect.return_value.__exit__ = MagicMock()
    return mock_engine


@pytest.fixture
def mock_session_factory(mock_engine):
    """
    Mock session factory for testing database operations.
    """
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=None)
    mock_session.commit = MagicMock()
    mock_session.rollback = MagicMock()
    mock_session.close = MagicMock()
    
    mock_factory = MagicMock(return_value=mock_session)
    return mock_factory


# =============================================================================
# Heartbeat Service Fixtures
# =============================================================================
@pytest.fixture
def mock_heartbeat_service():
    """
    Mock HeartbeatService for testing components that use heartbeats.
    
    Prevents background threads and database calls during tests.
    """
    mock_service = MagicMock()
    mock_service.start = MagicMock()
    mock_service.stop = MagicMock()
    mock_service.send_heartbeat = MagicMock()
    mock_service._running = False
    return mock_service


@pytest.fixture
def sample_system_status():
    """
    Sample SystemStatus model instances for testing.
    
    Returns a factory function to create mock status objects.
    """
    def _create_status(
        service_name: str = "test-service",
        status: str = "OK",
        minutes_ago: int = 1,
        current_task: str = "idle"
    ):
        mock_status = MagicMock()
        mock_status.service_name = service_name
        mock_status.status = status
        mock_status.last_heartbeat = datetime.now() - timedelta(minutes=minutes_ago)
        mock_status.current_task = current_task
        return mock_status
    
    return _create_status


# =============================================================================
# Infrastructure Monitor Fixtures
# =============================================================================
@pytest.fixture
def mock_docker_client_for_monitor():
    """
    Mock Docker client for infrastructure_monitor tests.
    
    Simulates Docker API responses for service health checking.
    """
    mock_client = MagicMock()
    
    # Mock container with health status
    mock_container = MagicMock()
    mock_container.status = "running"
    mock_container.attrs = {
        "State": {
            "Status": "running",
            "Health": {"Status": "healthy"}
        }
    }
    
    mock_client.containers.get.return_value = mock_container
    mock_client.ping.return_value = True
    
    return mock_client


@pytest.fixture
def mock_psycopg2_connection():
    """
    Mock psycopg2 connection for testing database connectivity checks.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (1,)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock()
    mock_conn.close = MagicMock()
    return mock_conn


# =============================================================================
# Model Fixtures
# =============================================================================
@pytest.fixture
def sample_media_asset():
    """
    Sample MediaAsset model instance for testing.
    
    Returns a factory function to create mock media asset objects.
    """
    def _create_asset(
        filename: str = "test.jpg",
        original_path: str = "/path/to/test.jpg",
        file_hash: str = "abc123",
        file_size: int = 1024,
        status: str = "OK"
    ):
        mock_asset = MagicMock()
        mock_asset.id = 1
        mock_asset.filename = filename
        mock_asset.original_path = original_path
        mock_asset.file_hash = file_hash
        mock_asset.file_size = file_size
        mock_asset.status = status
        mock_asset.is_ingested = True
        mock_asset.ingested_at = datetime.now()
        mock_asset.capture_date = datetime.now()
        mock_asset.location = None
        return mock_asset
    
    return _create_asset


# =============================================================================
# pytest-bdd Fixtures (for Shared feature files)
# =============================================================================
try:
    from pytest_bdd import given, when, then, parsers
    
    @pytest.fixture
    def shared_context():
        """
        Context dictionary for Shared library BDD steps.
        
        Stores state between Given/When/Then steps.
        """
        return {
            "database_connected": False,
            "heartbeat_sent": False,
            "error_message": None,
        }

except ImportError:
    # pytest-bdd not installed, skip BDD fixtures
    pass

