"""
Dashboard service pytest configuration and fixtures.

This conftest.py provides:
- Service-specific fixtures for Dashboard tests
- Mocked Streamlit and Docker client fixtures
- pytest-bdd step definitions for Dashboard behavior specs
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# Dashboard-Specific Fixtures
# =============================================================================
@pytest.fixture
def mock_streamlit():
    """
    Mock Streamlit for testing dashboard components without running the UI.
    
    Usage:
        def test_dashboard_metric(mock_streamlit):
            from Src.Dashboard.dashboard import render_metrics
            render_metrics()
            mock_streamlit.metric.assert_called()
    """
    mock_st = MagicMock()
    mock_st.session_state = {}
    mock_st.cache_data = lambda *args, **kwargs: lambda f: f
    mock_st.cache_resource = lambda *args, **kwargs: lambda f: f
    
    with patch.dict("sys.modules", {"streamlit": mock_st}):
        yield mock_st


@pytest.fixture
def mock_dashboard_db_session():
    """
    Mock database session with dashboard-specific query returns.
    
    Provides realistic mock data for system_status and system_status_history.
    """
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=None)
    
    # Mock system status result
    mock_status = MagicMock()
    mock_status.service_name = "librarian"
    mock_status.status = "OK"
    mock_status.last_heartbeat = datetime.now()
    mock_status.current_task = "idle"
    
    mock_session.query.return_value.filter.return_value.first.return_value = mock_status
    mock_session.query.return_value.all.return_value = [mock_status]
    
    return mock_session


@pytest.fixture
def sample_heartbeat_data():
    """
    Sample heartbeat data for testing color coding and status display.
    
    Returns a dict with various heartbeat scenarios for testing.
    """
    now = datetime.now()
    return {
        "healthy": {
            "service_name": "librarian",
            "status": "OK",
            "last_heartbeat": now - timedelta(minutes=1),
            "current_task": "watching",
        },
        "warning": {
            "service_name": "syncthing",
            "status": "OK",
            "last_heartbeat": now - timedelta(minutes=8),
            "current_task": "syncing",
        },
        "stale": {
            "service_name": "old-service",
            "status": "OK",
            "last_heartbeat": now - timedelta(minutes=20),
            "current_task": "unknown",
        },
        "error": {
            "service_name": "broken-service",
            "status": "ERROR",
            "last_heartbeat": now - timedelta(minutes=5),
            "current_task": "failed",
        },
    }


@pytest.fixture
def mock_docker_containers():
    """
    Mock Docker container list for testing service discovery.
    
    Returns mock containers that simulate Photo Factory services.
    """
    def create_mock_container(name: str, status: str, health: str = "healthy"):
        container = MagicMock()
        container.name = name
        container.status = status
        container.attrs = {
            "State": {"Health": {"Status": health}} if health else {"Status": status},
            "Config": {
                "Labels": {
                    "com.docker.compose.project": "photo_factory",
                    "com.docker.compose.service": name.replace("photo_factory_", "").replace("_1", "")
                }
            }
        }
        return container
    
    return [
        create_mock_container("photo_factory_librarian_1", "running", "healthy"),
        create_mock_container("photo_factory_dashboard_1", "running", "healthy"),
        create_mock_container("photo_factory_factory-db_1", "running", "healthy"),
        create_mock_container("photo_factory_syncthing_1", "running", None),
    ]


# =============================================================================
# pytest-bdd Fixtures (for Dashboard feature files)
# =============================================================================
try:
    from pytest_bdd import given, when, then, parsers
    
    @pytest.fixture
    def dashboard_context():
        """
        Context dictionary for Dashboard BDD steps.
        
        Stores state between Given/When/Then steps.
        """
        return {
            "services": [],
            "heartbeats": {},
            "containers": [],
            "render_result": None,
        }

except ImportError:
    # pytest-bdd not installed, skip BDD fixtures
    pass






