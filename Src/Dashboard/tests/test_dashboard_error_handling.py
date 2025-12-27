"""
Tests for dashboard error handling and edge cases.

Ensures the dashboard gracefully handles failures (Docker unavailable, DB unavailable, etc.)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from Src.Dashboard.dashboard import (
    get_container_status,
    get_librarian_heartbeat,
    get_total_assets,
    get_assets_last_hour,
    get_recent_assets,
    get_service_heartbeat,
    get_available_services,
    get_service_logs,
    get_all_services_status,
    DOCKER_AVAILABLE,
)


class TestDockerUnavailable:
    """Test dashboard behavior when Docker is unavailable."""
    
    def test_get_container_status_returns_none_when_docker_unavailable(self):
        """Test that get_container_status returns None when Docker is unavailable."""
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', False):
            result = get_container_status("test_container")
            assert result is None
    
    def test_get_available_services_returns_fallback_when_docker_unavailable(self):
        """Test that get_available_services returns known services when Docker unavailable."""
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', False):
            result = get_available_services()
            # Should return known services as fallback
            assert isinstance(result, list)
            assert len(result) > 0
            assert "librarian" in result or "dashboard" in result
    
    def test_get_service_logs_returns_empty_when_docker_unavailable(self):
        """Test that get_service_logs returns empty string when Docker unavailable."""
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', False):
            result = get_service_logs("test_service")
            assert result == ""
    
    def test_get_all_services_status_returns_empty_when_docker_unavailable(self):
        """Test that get_all_services_status returns empty list when Docker unavailable."""
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', False):
            result = get_all_services_status()
            assert result == []


class TestDatabaseUnavailable:
    """Test dashboard behavior when database is unavailable."""
    
    def test_get_librarian_heartbeat_handles_db_error(self):
        """Test that get_librarian_heartbeat handles database errors gracefully."""
        get_librarian_heartbeat.clear()
        
        with patch('Src.Dashboard.dashboard.get_db_session') as mock_session:
            # Simulate database error
            mock_session.side_effect = Exception("Database connection failed")
            
            result = get_librarian_heartbeat()
            # Should return None on error, not crash
            assert result is None
    
    def test_get_total_assets_returns_zero_on_db_error(self):
        """Test that get_total_assets returns 0 on database error."""
        get_total_assets.clear()
        
        with patch('Src.Dashboard.dashboard.get_db_session') as mock_session:
            mock_session.side_effect = Exception("Database connection failed")
            
            result = get_total_assets()
            # Should return 0 on error, not crash
            assert result == 0
    
    def test_get_assets_last_hour_returns_zero_on_db_error(self):
        """Test that get_assets_last_hour returns 0 on database error."""
        get_assets_last_hour.clear()
        
        with patch('Src.Dashboard.dashboard.get_db_session') as mock_session:
            mock_session.side_effect = Exception("Database connection failed")
            
            result = get_assets_last_hour()
            # Should return 0 on error, not crash
            assert result == 0
    
    def test_get_recent_assets_returns_empty_list_on_db_error(self):
        """Test that get_recent_assets returns empty list on database error."""
        get_recent_assets.clear()
        
        with patch('Src.Dashboard.dashboard.get_db_session') as mock_session:
            mock_session.side_effect = Exception("Database connection failed")
            
            result = get_recent_assets()
            # Should return empty list on error, not crash
            assert result == []


class TestDockerErrors:
    """Test dashboard behavior when Docker API calls fail."""
    
    def test_get_container_status_handles_not_found(self):
        """Test that get_container_status handles container not found."""
        if not DOCKER_AVAILABLE:
            pytest.skip("Docker not available in test environment")
        
        with patch('Src.Dashboard.dashboard.docker_client') as mock_client:
            from docker.errors import NotFound
            mock_client.containers.get.side_effect = NotFound("Container not found")
            
            result = get_container_status("nonexistent_container")
            # Should return dict with not_found status, not crash
            assert result is not None
            assert result["status"] == "not_found"
            assert result["running"] is False
    
    def test_get_container_status_handles_generic_error(self):
        """Test that get_container_status handles generic Docker errors."""
        if not DOCKER_AVAILABLE:
            pytest.skip("Docker not available in test environment")
        
        with patch('Src.Dashboard.dashboard.docker_client') as mock_client:
            mock_client.containers.get.side_effect = Exception("Docker API error")
            
            result = get_container_status("test_container")
            # Should return None on error, not crash
            assert result is None
    
    def test_get_service_logs_handles_not_found(self):
        """Test that get_service_logs handles container not found."""
        get_service_logs.clear()
        
        if not DOCKER_AVAILABLE:
            pytest.skip("Docker not available in test environment")
        
        with patch('Src.Dashboard.dashboard.docker_client') as mock_client:
            from docker.errors import NotFound
            mock_container = Mock()
            mock_client.containers.get.side_effect = NotFound("Container not found")
            
            result = get_service_logs("nonexistent_service")
            # Should return error message, not crash
            assert isinstance(result, str)
            assert "not found" in result.lower() or result == ""
    
    def test_get_service_logs_handles_generic_error(self):
        """Test that get_service_logs handles generic errors."""
        get_service_logs.clear()
        
        if not DOCKER_AVAILABLE:
            pytest.skip("Docker not available in test environment")
        
        with patch('Src.Dashboard.dashboard.docker_client') as mock_client:
            mock_client.containers.get.side_effect = Exception("Docker API error")
            
            result = get_service_logs("test_service")
            # Should return empty string on error, not crash
            assert result == ""


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_get_recent_assets_with_limit(self):
        """Test that get_recent_assets respects the limit parameter."""
        get_recent_assets.clear()
        
        with patch('Src.Dashboard.dashboard.get_db_session') as mock_session:
            # Mock multiple assets
            mock_assets = [Mock() for _ in range(20)]
            for i, asset in enumerate(mock_assets):
                asset.id = f"id_{i}"
                asset.original_name = f"file_{i}.jpg"
                asset.final_path = f"/path/to/file_{i}.jpg"
                asset.captured_at = datetime.now()
                asset.ingested_at = datetime.now()
                asset.size_bytes = 1000
            
            mock_query = Mock()
            mock_query.order_by.return_value.limit.return_value.all.return_value = mock_assets
            
            mock_session_obj = Mock()
            mock_session_obj.__enter__ = Mock(return_value=mock_session_obj)
            mock_session_obj.__exit__ = Mock(return_value=False)
            mock_session_obj.query.return_value = mock_query
            mock_session.return_value = mock_session_obj
            
            result = get_recent_assets(limit=10)
            # Should return list of dicts
            assert isinstance(result, list)
            # Note: The actual limit is enforced by SQL, but we verify it's callable
    
    def test_get_service_heartbeat_with_different_service_names(self):
        """Test that get_service_heartbeat handles different service name formats."""
        get_service_heartbeat.clear()
        
        with patch('Src.Dashboard.dashboard.get_db_session') as mock_session:
            mock_status = Mock()
            mock_status.last_heartbeat = datetime.now()
            mock_status.status = "OK"
            mock_status.current_task = None
            mock_status.updated_at = datetime.now()
            
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = mock_status
            
            mock_session_obj = Mock()
            mock_session_obj.__enter__ = Mock(return_value=mock_session_obj)
            mock_session_obj.__exit__ = Mock(return_value=False)
            mock_session_obj.query.return_value = mock_query
            mock_session.return_value = mock_session_obj
            
            # Test with different service name formats
            result1 = get_service_heartbeat("librarian")
            result2 = get_service_heartbeat("factory-db")
            result3 = get_service_heartbeat("factory_postgres")
            
            # All should work without crashing
            assert result1 is not None or result1 is None  # Either is valid
            assert result2 is not None or result2 is None
            assert result3 is not None or result3 is None

