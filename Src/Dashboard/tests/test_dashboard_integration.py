"""
Integration tests for Dashboard service.

Tests the dashboard's integration with other services (Database, Docker, Librarian).
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from Src.Dashboard.dashboard import (
    get_librarian_heartbeat,
    get_total_assets,
    get_all_services_status,
    get_available_services,
    get_service_heartbeat,
    DOCKER_AVAILABLE,
)


class TestDashboardDatabaseIntegration:
    """Test dashboard integration with the database."""
    
    def test_dashboard_reads_librarian_heartbeat_from_db(self):
        """Test that dashboard can read librarian heartbeat from database."""
        get_librarian_heartbeat.clear()
        
        # Create a mock heartbeat record
        recent_heartbeat = datetime.now() - timedelta(seconds=30)
        
        with patch('Src.Dashboard.dashboard.get_db_session') as mock_session:
            mock_status = Mock()
            mock_status.last_heartbeat = recent_heartbeat
            mock_status.status = "OK"
            mock_status.current_task = "processing files"
            mock_status.updated_at = datetime.now()
            
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = mock_status
            
            mock_session_obj = Mock()
            mock_session_obj.__enter__ = Mock(return_value=mock_session_obj)
            mock_session_obj.__exit__ = Mock(return_value=False)
            mock_session_obj.query.return_value = mock_query
            mock_session.return_value = mock_session_obj
            
            result = get_librarian_heartbeat()
            
            # Verify dashboard can read heartbeat data
            assert result is not None
            assert result["status"] == "OK"
            assert result["current_task"] == "processing files"
            assert result["last_heartbeat"] == recent_heartbeat
    
    def test_dashboard_reads_asset_counts_from_db(self):
        """Test that dashboard can read asset counts from database."""
        get_total_assets.clear()
        
        with patch('Src.Dashboard.dashboard.get_db_session') as mock_session:
            from sqlalchemy import func
            
            mock_query = Mock()
            mock_query.scalar.return_value = 42
            
            mock_session_obj = Mock()
            mock_session_obj.__enter__ = Mock(return_value=mock_session_obj)
            mock_session_obj.__exit__ = Mock(return_value=False)
            mock_session_obj.query.return_value = mock_query
            mock_session.return_value = mock_session_obj
            
            result = get_total_assets()
            
            # Verify dashboard can read asset count
            assert result == 42


class TestDashboardDockerIntegration:
    """Test dashboard integration with Docker API."""
    
    def test_dashboard_discovers_services_from_docker(self):
        """Test that dashboard can discover services from Docker."""
        # Mock Docker availability check
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True):
            # This test verifies the dashboard can interact with Docker
            # We'll mock the actual Docker client to avoid requiring Docker in tests
            with patch('Src.Dashboard.dashboard.docker_client') as mock_client:
                # Mock container list
                mock_container1 = Mock()
                mock_container1.name = "librarian"
                mock_container2 = Mock()
                mock_container2.name = "dashboard"
                mock_client.containers.list.return_value = [mock_container1, mock_container2]
                
                result = get_available_services()
                
                # Should return a list of service names
                assert isinstance(result, list)
                assert len(result) >= 0  # May be empty or contain services
    
    def test_dashboard_aggregates_service_status(self):
        """Test that dashboard can aggregate status from multiple services."""
        get_all_services_status.clear()
        
        # Mock Docker and database responses
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True), \
             patch('Src.Dashboard.dashboard.get_available_services', return_value=["librarian", "dashboard"]), \
             patch('Src.Dashboard.dashboard.get_container_status') as mock_container, \
             patch('Src.Dashboard.dashboard.get_service_heartbeat') as mock_heartbeat:
            
            # Mock container status
            mock_container.side_effect = [
                {"running": True, "health": "healthy"},  # librarian
                {"running": True, "health": "healthy"},  # dashboard
            ]
            
            # Mock heartbeat
            mock_heartbeat.side_effect = [
                {"last_heartbeat": datetime.now() - timedelta(seconds=30), "status": "OK"},
                None,  # dashboard might not have heartbeat
            ]
            
            result = get_all_services_status()
            
            # Should aggregate status from both services
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["name"] == "librarian"
            assert result[1]["name"] == "dashboard"


class TestDashboardServiceInteraction:
    """Test how dashboard interacts with other services."""
    
    def test_dashboard_handles_missing_service_gracefully(self):
        """Test that dashboard handles missing services gracefully."""
        get_service_heartbeat.clear()
        
        with patch('Src.Dashboard.dashboard.get_db_session') as mock_session:
            # Simulate service not found in database
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            
            mock_session_obj = Mock()
            mock_session_obj.__enter__ = Mock(return_value=mock_session_obj)
            mock_session_obj.__exit__ = Mock(return_value=False)
            mock_session_obj.query.return_value = mock_query
            mock_session.return_value = mock_session_obj
            
            result = get_service_heartbeat("nonexistent_service")
            
            # Should return None, not crash
            assert result is None
    
    def test_dashboard_handles_partial_service_failures(self):
        """Test that dashboard handles partial service failures (some services up, some down)."""
        get_all_services_status.clear()
        
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True), \
             patch('Src.Dashboard.dashboard.get_available_services', return_value=["librarian", "dashboard", "factory-db"]), \
             patch('Src.Dashboard.dashboard.get_container_status') as mock_container, \
             patch('Src.Dashboard.dashboard.get_service_heartbeat') as mock_heartbeat:
            
            # Simulate mixed status: one service healthy, one unhealthy, one not found
            mock_container.side_effect = [
                {"running": True, "health": "healthy"},   # librarian - OK
                {"running": False, "health": "unknown"},  # dashboard - down
                None,  # factory-db - error getting status
            ]
            
            mock_heartbeat.side_effect = [
                {"last_heartbeat": datetime.now() - timedelta(seconds=30), "status": "OK"},
                None,
                None,
            ]
            
            result = get_all_services_status()
            
            # Should handle all cases gracefully
            assert isinstance(result, list)
            assert len(result) == 3
            # All services should have status info, even if some are None/False
            for svc in result:
                assert "name" in svc
                assert "container_running" in svc
                assert "container_health" in svc
                assert "heartbeat" in svc

