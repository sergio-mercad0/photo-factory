"""
Tests for dashboard service monitoring functionality.

Verifies that dashboard correctly displays all services and their heartbeats.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from Src.Dashboard.dashboard import (
    get_all_services_status,
    get_service_heartbeat,
    get_available_services,
    DOCKER_AVAILABLE,
)


class TestDashboardServiceMonitoring:
    """Test dashboard service monitoring and display."""
    
    def test_get_all_services_status_includes_all_critical_services(self):
        """Test that get_all_services_status includes all critical services."""
        get_all_services_status.clear()
        
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True):
            with patch('Src.Dashboard.dashboard.get_available_services') as mock_services:
                mock_services.return_value = [
                    "librarian",
                    "dashboard",
                    "factory_postgres",
                    "syncthing",
                    "service_monitor"
                ]
                
                with patch('Src.Dashboard.dashboard.get_container_status') as mock_container:
                    mock_container.return_value = {
                        "running": True,
                        "health": "healthy"
                    }
                    
                    with patch('Src.Dashboard.dashboard.get_service_heartbeat') as mock_heartbeat:
                        mock_heartbeat.return_value = {
                            "last_heartbeat": datetime.now() - timedelta(seconds=30),
                            "status": "OK",
                            "current_task": "Running"
                        }
                        
                        result = get_all_services_status()
                        
                        # Should include all services
                        assert len(result) == 5
                        service_names = [svc["name"] for svc in result]
                        assert "librarian" in service_names
                        assert "dashboard" in service_names
                        assert "factory_postgres" in service_names
                        assert "syncthing" in service_names
                        assert "service_monitor" in service_names
    
    def test_service_name_mapping_correct(self):
        """Test that container names are correctly mapped to service names."""
        get_all_services_status.clear()
        
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True):
            with patch('Src.Dashboard.dashboard.get_available_services') as mock_services:
                mock_services.return_value = ["factory_postgres", "syncthing"]
                
                with patch('Src.Dashboard.dashboard.get_container_status') as mock_container:
                    mock_container.return_value = {"running": True, "health": "healthy"}
                    
                    with patch('Src.Dashboard.dashboard.get_service_heartbeat') as mock_heartbeat:
                        mock_heartbeat.return_value = {
                            "last_heartbeat": datetime.now(),
                            "status": "OK"
                        }
                        
                        result = get_all_services_status()
                        
                        # Verify service name mapping
                        heartbeat_calls = [call[0][0] for call in mock_heartbeat.call_args_list]
                        assert "factory-db" in heartbeat_calls  # factory_postgres -> factory-db
                        assert "syncthing" in heartbeat_calls  # syncthing -> syncthing
    
    def test_dashboard_shows_heartbeat_for_all_services(self):
        """Test that dashboard shows heartbeat information for all services."""
        get_all_services_status.clear()
        
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True):
            with patch('Src.Dashboard.dashboard.get_available_services') as mock_services:
                mock_services.return_value = ["librarian", "factory_postgres", "syncthing"]
                
                with patch('Src.Dashboard.dashboard.get_container_status') as mock_container:
                    mock_container.return_value = {"running": True, "health": "healthy"}
                    
                    with patch('Src.Dashboard.dashboard.get_service_heartbeat') as mock_heartbeat:
                        mock_heartbeat.return_value = {
                            "last_heartbeat": datetime.now() - timedelta(seconds=45),
                            "status": "OK",
                            "current_task": "Processing"
                        }
                        
                        result = get_all_services_status()
                        
                        # All services should have heartbeat info
                        for svc in result:
                            assert "heartbeat" in svc
                            assert svc["heartbeat"] is not None
                            assert svc["heartbeat"]["status"] == "OK"
    
    def test_dashboard_handles_missing_heartbeat_gracefully(self):
        """Test that dashboard handles services without heartbeat gracefully."""
        get_all_services_status.clear()
        
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True):
            with patch('Src.Dashboard.dashboard.get_available_services') as mock_services:
                mock_services.return_value = ["librarian", "unknown_service"]
                
                with patch('Src.Dashboard.dashboard.get_container_status') as mock_container:
                    mock_container.return_value = {"running": True, "health": "healthy"}
                    
                    with patch('Src.Dashboard.dashboard.get_service_heartbeat') as mock_heartbeat:
                        # Return heartbeat for librarian, None for unknown
                        def side_effect(service_name):
                            if service_name == "librarian":
                                return {
                                    "last_heartbeat": datetime.now(),
                                    "status": "OK"
                                }
                            return None
                        
                        mock_heartbeat.side_effect = side_effect
                        
                        result = get_all_services_status()
                        
                        # Should still include both services
                        assert len(result) == 2
                        # Unknown service should have None heartbeat
                        unknown_svc = [svc for svc in result if svc["name"] == "unknown_service"][0]
                        assert unknown_svc["heartbeat"] is None
    
    def test_get_service_heartbeat_returns_correct_format(self):
        """Test that get_service_heartbeat returns correct dictionary format."""
        get_service_heartbeat.clear()
        
        recent_time = datetime.now() - timedelta(seconds=30)
        
        with patch('Src.Dashboard.dashboard.get_db_session') as mock_session:
            mock_status = Mock()
            mock_status.last_heartbeat = recent_time
            mock_status.status = "OK"
            mock_status.current_task = "Processing files"
            mock_status.updated_at = datetime.now()
            
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = mock_status
            
            mock_session_obj = Mock()
            mock_session_obj.__enter__ = Mock(return_value=mock_session_obj)
            mock_session_obj.__exit__ = Mock(return_value=False)
            mock_session_obj.query.return_value = mock_query
            mock_session.return_value = mock_session_obj
            
            result = get_service_heartbeat("librarian")
            
            assert result is not None
            assert result["last_heartbeat"] == recent_time
            assert result["status"] == "OK"
            assert result["current_task"] == "Processing files"
            assert "updated_at" in result
    
    def test_get_service_heartbeat_returns_none_when_no_record(self):
        """Test that get_service_heartbeat returns None when no record exists."""
        get_service_heartbeat.clear()
        
        with patch('Src.Dashboard.dashboard.get_db_session') as mock_session:
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            
            mock_session_obj = Mock()
            mock_session_obj.__enter__ = Mock(return_value=mock_session_obj)
            mock_session_obj.__exit__ = Mock(return_value=False)
            mock_session_obj.query.return_value = mock_query
            mock_session.return_value = mock_session_obj
            
            result = get_service_heartbeat("nonexistent-service")
            
            assert result is None
    
    def test_dashboard_includes_service_monitor_in_list(self):
        """Test that service_monitor container is included in available services."""
        get_available_services.clear()
        
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True):
            with patch('Src.Dashboard.dashboard.docker_client') as mock_docker:
                mock_container1 = Mock()
                mock_container1.name = "librarian"
                mock_container2 = Mock()
                mock_container2.name = "service_monitor"
                mock_container3 = Mock()
                mock_container3.name = "factory_postgres"
                
                mock_docker.containers.list.return_value = [
                    mock_container1,
                    mock_container2,
                    mock_container3
                ]
                
                result = get_available_services()
                
                # service_monitor should be included (it's in known_services list)
                assert "librarian" in result
                assert "factory_postgres" in result
                assert "service_monitor" in result, "service_monitor should be included in available services"
    
    def test_service_monitor_appears_in_all_services_status(self):
        """Test that service_monitor appears in all services status even without heartbeat."""
        get_all_services_status.clear()
        
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True):
            with patch('Src.Dashboard.dashboard.get_available_services') as mock_services:
                mock_services.return_value = ["librarian", "service_monitor"]
                
                with patch('Src.Dashboard.dashboard.get_container_status') as mock_container:
                    mock_container.return_value = {"running": True, "health": "healthy"}
                    
                    with patch('Src.Dashboard.dashboard.get_service_heartbeat') as mock_heartbeat:
                        # service_monitor doesn't have a heartbeat (returns None)
                        def side_effect(service_name):
                            if service_name == "librarian":
                                return {"last_heartbeat": datetime.now(), "status": "OK"}
                            return None  # service_monitor has no heartbeat
                        
                        mock_heartbeat.side_effect = side_effect
                        
                        result = get_all_services_status()
                        
                        # Should include both services
                        assert len(result) == 2
                        service_names = [svc["name"] for svc in result]
                        assert "librarian" in service_names
                        assert "service_monitor" in service_names
                        
                        # service_monitor should have None heartbeat but still appear
                        service_monitor = [svc for svc in result if svc["name"] == "service_monitor"][0]
                        assert service_monitor["heartbeat"] is None
                        assert service_monitor["container_running"] is True

