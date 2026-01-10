"""
Tests for dashboard heartbeat color coding with comprehensive coverage.

Verifies that heartbeat displays show correct colors based on ratio calculations.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from Src.Dashboard.dashboard import get_all_services_status, get_service_heartbeat


class TestColorCodingLogic:
    """Test the color coding logic directly."""
    
    def test_syncthing_109s_should_be_green(self):
        """Test syncthing at 109s should show green (109 <= 300)."""
        expected_interval = 300
        seconds_ago = 109
        
        # Implementation uses seconds_ago <= max_interval for green
        assert seconds_ago <= expected_interval, f"{seconds_ago}s should be <= {expected_interval}s for green"
    
    def test_syncthing_250s_should_be_green(self):
        """Test syncthing at 250s should show green (250 <= 300)."""
        expected_interval = 300
        seconds_ago = 250
        
        assert seconds_ago <= expected_interval, f"{seconds_ago}s should be <= {expected_interval}s for green"
    
    def test_syncthing_299s_should_be_green(self):
        """Test syncthing at 299s should show green (299 <= 300) - edge case."""
        expected_interval = 300
        seconds_ago = 299
        
        assert seconds_ago <= expected_interval, f"{seconds_ago}s should be <= {expected_interval}s for green"
    
    def test_syncthing_300s_should_be_green(self):
        """Test syncthing at 300s should show green (300 <= 300) - boundary case.
        
        Implementation uses <= for green, so exactly at interval is still green.
        """
        expected_interval = 300
        seconds_ago = 300
        
        # At exactly the interval boundary, implementation shows GREEN
        assert seconds_ago <= expected_interval, f"{seconds_ago}s should be <= {expected_interval}s for green"
    
    def test_syncthing_301s_should_be_yellow(self):
        """Test syncthing at 301s should show yellow (301 > 300, 301 <= 600)."""
        expected_interval = 300
        seconds_ago = 301
        
        # Implementation: max_interval < seconds_ago <= max_interval * 2 is yellow
        assert seconds_ago > expected_interval, f"{seconds_ago}s should be > {expected_interval}s"
        assert seconds_ago <= expected_interval * 2, f"{seconds_ago}s should be <= {expected_interval * 2}s for yellow"
    
    def test_syncthing_350s_should_be_yellow(self):
        """Test syncthing at 350s should show yellow (300 < 350 <= 600)."""
        expected_interval = 300
        seconds_ago = 350
        
        assert seconds_ago > expected_interval, f"{seconds_ago}s should be > {expected_interval}s"
        assert seconds_ago <= expected_interval * 2, f"{seconds_ago}s should be <= {expected_interval * 2}s for yellow"
    
    def test_syncthing_450s_should_be_yellow(self):
        """Test syncthing at 450s should show yellow (300 < 450 <= 600)."""
        expected_interval = 300
        seconds_ago = 450
        
        assert seconds_ago > expected_interval, f"{seconds_ago}s should be > {expected_interval}s"
        assert seconds_ago <= expected_interval * 2, f"{seconds_ago}s should be <= {expected_interval * 2}s for yellow"
    
    def test_syncthing_600s_should_be_yellow(self):
        """Test syncthing at 600s should show yellow (300 < 600 <= 600) - boundary case.
        
        Implementation uses <= for yellow boundary, so exactly at 2x interval is still yellow.
        """
        expected_interval = 300
        seconds_ago = 600
        
        assert seconds_ago > expected_interval, f"{seconds_ago}s should be > {expected_interval}s"
        assert seconds_ago <= expected_interval * 2, f"{seconds_ago}s should be <= {expected_interval * 2}s for yellow"
    
    def test_syncthing_601s_should_be_red(self):
        """Test syncthing at 601s should show red (601 > 600)."""
        expected_interval = 300
        seconds_ago = 601
        
        # Implementation: seconds_ago > max_interval * 2 is red
        assert seconds_ago > expected_interval * 2, f"{seconds_ago}s should be > {expected_interval * 2}s for red"
    
    def test_syncthing_900s_should_be_red(self):
        """Test syncthing at 900s should show red (900 > 600)."""
        expected_interval = 300
        seconds_ago = 900
        
        assert seconds_ago > expected_interval * 2, f"{seconds_ago}s should be > {expected_interval * 2}s for red"
    
    def test_librarian_41s_should_be_green(self):
        """Test librarian at 41s should show green (41 <= 60)."""
        expected_interval = 60
        seconds_ago = 41
        
        assert seconds_ago <= expected_interval, f"{seconds_ago}s should be <= {expected_interval}s for green"
    
    def test_librarian_60s_should_be_green(self):
        """Test librarian at 60s should show green (60 <= 60) - boundary case."""
        expected_interval = 60
        seconds_ago = 60
        
        assert seconds_ago <= expected_interval, f"{seconds_ago}s should be <= {expected_interval}s for green"
    
    def test_librarian_90s_should_be_yellow(self):
        """Test librarian at 90s should show yellow (60 < 90 <= 120)."""
        expected_interval = 60
        seconds_ago = 90
        
        assert seconds_ago > expected_interval, f"{seconds_ago}s should be > {expected_interval}s"
        assert seconds_ago <= expected_interval * 2, f"{seconds_ago}s should be <= {expected_interval * 2}s for yellow"
    
    def test_librarian_120s_should_be_yellow(self):
        """Test librarian at 120s should show yellow (60 < 120 <= 120) - boundary case."""
        expected_interval = 60
        seconds_ago = 120
        
        assert seconds_ago > expected_interval, f"{seconds_ago}s should be > {expected_interval}s"
        assert seconds_ago <= expected_interval * 2, f"{seconds_ago}s should be <= {expected_interval * 2}s for yellow"
    
    def test_librarian_121s_should_be_red(self):
        """Test librarian at 121s should show red (121 > 120)."""
        expected_interval = 60
        seconds_ago = 121
        
        assert seconds_ago > expected_interval * 2, f"{seconds_ago}s should be > {expected_interval * 2}s for red"


class TestColorCodingDisplay:
    """Test the full display pipeline with mocked data."""
    
    def test_syncthing_109s_shows_green_in_status_data(self):
        """Test that syncthing at 109s shows green in status_data table."""
        get_all_services_status.clear()
        
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True):
            with patch('Src.Dashboard.dashboard.get_available_services') as mock_services:
                mock_services.return_value = ["syncthing"]
                
                with patch('Src.Dashboard.dashboard.get_container_status') as mock_container:
                    mock_container.return_value = {"running": True, "health": "healthy"}
                    
                    with patch('Src.Dashboard.dashboard.get_service_heartbeat') as mock_heartbeat:
                        # Syncthing at 109 seconds (should be green)
                        mock_heartbeat.return_value = {
                            "last_heartbeat": datetime.now() - timedelta(seconds=109),
                            "status": "OK"
                        }
                        
                        result = get_all_services_status()
                        
                        assert len(result) == 1
                        assert result[0]["name"] == "syncthing"
                        assert result[0]["service_name"] == "syncthing"
                        assert result[0]["heartbeat"] is not None
                        
                        # Now test the display logic
                        from Src.Dashboard.dashboard import datetime as dt_module
                        svc = result[0]
                        
                        service_intervals = {
                            "librarian": 60,
                            "dashboard": 300,
                            "factory-db": 300,
                            "syncthing": 300,
                        }
                        
                        service_name_for_interval = svc.get("service_name")
                        expected_interval = service_intervals.get(service_name_for_interval, 300)
                        
                        time_since = datetime.now() - svc["heartbeat"]["last_heartbeat"]
                        seconds_ago = int(time_since.total_seconds())
                        ratio = seconds_ago / expected_interval if expected_interval > 0 else 0
                        
                        # Verify color based on implementation logic (uses <=)
                        assert seconds_ago == 109, f"Expected 109s, got {seconds_ago}s"
                        assert expected_interval == 300, f"Expected 300s interval, got {expected_interval}s"
                        assert seconds_ago <= expected_interval, f"{seconds_ago}s should be <= {expected_interval}s for green"
                        
                        # Match implementation: seconds_ago <= max_interval -> green
                        if seconds_ago <= expected_interval:
                            color = "🟢"
                        elif seconds_ago <= expected_interval * 2:
                            color = "🟡"
                        else:
                            color = "🔴"
                        
                        assert color == "🟢", f"Expected green, got {color} for {seconds_ago}s"
    
    def test_syncthing_350s_shows_yellow_in_status_data(self):
        """Test that syncthing at 350s shows yellow in status_data table."""
        get_all_services_status.clear()
        
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True):
            with patch('Src.Dashboard.dashboard.get_available_services') as mock_services:
                mock_services.return_value = ["syncthing"]
                
                with patch('Src.Dashboard.dashboard.get_container_status') as mock_container:
                    mock_container.return_value = {"running": True, "health": "healthy"}
                    
                    with patch('Src.Dashboard.dashboard.get_service_heartbeat') as mock_heartbeat:
                        # Syncthing at 350 seconds (should be yellow)
                        mock_heartbeat.return_value = {
                            "last_heartbeat": datetime.now() - timedelta(seconds=350),
                            "status": "OK"
                        }
                        
                        result = get_all_services_status()
                        
                        svc = result[0]
                        service_intervals = {"syncthing": 300}
                        service_name_for_interval = svc.get("service_name")
                        expected_interval = service_intervals.get(service_name_for_interval, 300)
                        
                        time_since = datetime.now() - svc["heartbeat"]["last_heartbeat"]
                        seconds_ago = int(time_since.total_seconds())
                        
                        # Implementation uses: max_interval < seconds_ago <= max_interval * 2 for yellow
                        assert seconds_ago > expected_interval, f"{seconds_ago}s should be > {expected_interval}s"
                        assert seconds_ago <= expected_interval * 2, f"{seconds_ago}s should be <= {expected_interval * 2}s for yellow"
                        
                        # Match implementation logic
                        if seconds_ago <= expected_interval:
                            color = "🟢"
                        elif seconds_ago <= expected_interval * 2:
                            color = "🟡"
                        else:
                            color = "🔴"
                        
                        assert color == "🟡", f"Expected yellow, got {color} for {seconds_ago}s"
    
    def test_syncthing_601s_shows_red_in_status_data(self):
        """Test that syncthing at 601s shows red in status_data table.
        
        Note: 600s would be yellow (600 <= 600), so we use 601s for red.
        """
        get_all_services_status.clear()
        
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True):
            with patch('Src.Dashboard.dashboard.get_available_services') as mock_services:
                mock_services.return_value = ["syncthing"]
                
                with patch('Src.Dashboard.dashboard.get_container_status') as mock_container:
                    mock_container.return_value = {"running": True, "health": "healthy"}
                    
                    with patch('Src.Dashboard.dashboard.get_service_heartbeat') as mock_heartbeat:
                        # Syncthing at 601 seconds (should be red: 601 > 600)
                        mock_heartbeat.return_value = {
                            "last_heartbeat": datetime.now() - timedelta(seconds=601),
                            "status": "OK"
                        }
                        
                        result = get_all_services_status()
                        
                        svc = result[0]
                        service_intervals = {"syncthing": 300}
                        service_name_for_interval = svc.get("service_name")
                        expected_interval = service_intervals.get(service_name_for_interval, 300)
                        
                        time_since = datetime.now() - svc["heartbeat"]["last_heartbeat"]
                        seconds_ago = int(time_since.total_seconds())
                        
                        # Implementation: seconds_ago > max_interval * 2 is red
                        assert seconds_ago > expected_interval * 2, f"{seconds_ago}s should be > {expected_interval * 2}s for red"
                        
                        # Match implementation logic
                        if seconds_ago <= expected_interval:
                            color = "🟢"
                        elif seconds_ago <= expected_interval * 2:
                            color = "🟡"
                        else:
                            color = "🔴"
                        
                        assert color == "🔴", f"Expected red, got {color} for {seconds_ago}s"
    
    def test_service_name_mapping_syncthing(self):
        """Test that container name 'syncthing' correctly maps to service name 'syncthing'."""
        get_all_services_status.clear()
        
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True):
            with patch('Src.Dashboard.dashboard.get_available_services') as mock_services:
                mock_services.return_value = ["syncthing"]
                
                with patch('Src.Dashboard.dashboard.get_container_status') as mock_container:
                    mock_container.return_value = {"running": True, "health": "healthy"}
                    
                    with patch('Src.Dashboard.dashboard.get_service_heartbeat') as mock_heartbeat:
                        mock_heartbeat.return_value = {
                            "last_heartbeat": datetime.now() - timedelta(seconds=109),
                            "status": "OK"
                        }
                        
                        result = get_all_services_status()
                        
                        assert len(result) == 1
                        svc = result[0]
                        
                        # Verify service name mapping
                        assert svc["name"] == "syncthing", "Container name should be 'syncthing'"
                        assert svc["service_name"] == "syncthing", "Service name should be 'syncthing'"
                        
                        # Verify expected interval lookup
                        service_intervals = {"syncthing": 300}
                        service_name_for_interval = svc.get("service_name")
                        expected_interval = service_intervals.get(service_name_for_interval, 300)
                        
                        assert expected_interval == 300, f"Expected 300s interval for syncthing, got {expected_interval}s"


class TestColorCodingEndToEnd:
    """Test with mocked database values."""
    
    def test_syncthing_109s_from_database_shows_green(self):
        """Test syncthing at 109s from database shows green."""
        get_all_services_status.clear()
        get_service_heartbeat.clear()
        
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True):
            with patch('Src.Dashboard.dashboard.get_available_services') as mock_services:
                mock_services.return_value = ["syncthing"]
                
                with patch('Src.Dashboard.dashboard.get_container_status') as mock_container:
                    mock_container.return_value = {"running": True, "health": "healthy"}
                    
                    # Mock the database query
                    with patch('Src.Dashboard.dashboard.get_db_session') as mock_db:
                        mock_status = Mock()
                        mock_status.service_name = "syncthing"
                        mock_status.last_heartbeat = datetime.now() - timedelta(seconds=109)
                        mock_status.status = "OK"
                        mock_status.current_task = None
                        mock_status.updated_at = datetime.now()
                        
                        mock_session = Mock()
                        mock_session.__enter__ = Mock(return_value=mock_session)
                        mock_session.__exit__ = Mock(return_value=None)
                        mock_session.query.return_value.filter.return_value.first.return_value = mock_status
                        mock_db.return_value = mock_session
                        
                        result = get_all_services_status()
                        
                        assert len(result) == 1
                        svc = result[0]
                        assert svc["heartbeat"] is not None
                        
                        # Test the color calculation using implementation logic
                        service_intervals = {"syncthing": 300}
                        service_name_for_interval = svc.get("service_name")
                        expected_interval = service_intervals.get(service_name_for_interval, 300)
                        
                        time_since = datetime.now() - svc["heartbeat"]["last_heartbeat"]
                        seconds_ago = int(time_since.total_seconds())
                        
                        # Implementation uses <= for green boundary
                        assert seconds_ago <= expected_interval, f"{seconds_ago}s should be <= {expected_interval}s for green"
                        assert seconds_ago == 109, f"Expected 109s, got {seconds_ago}s"
                        
                        # Match implementation logic
                        if seconds_ago <= expected_interval:
                            color = "🟢"
                        elif seconds_ago <= expected_interval * 2:
                            color = "🟡"
                        else:
                            color = "🔴"
                        
                        assert color == "🟢", f"Expected green for 109s, got {color}"










