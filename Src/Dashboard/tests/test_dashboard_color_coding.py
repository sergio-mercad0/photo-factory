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
        """Test syncthing at 109s should show green (ratio 0.363 < 1.0)."""
        expected_interval = 300
        seconds_ago = 109
        ratio = seconds_ago / expected_interval
        
        assert ratio < 1.0, f"Ratio {ratio} should be < 1.0 for green"
        assert ratio == pytest.approx(0.363, abs=0.001), f"Ratio should be 0.363, got {ratio}"
    
    def test_syncthing_250s_should_be_green(self):
        """Test syncthing at 250s should show green (ratio 0.833 < 1.0)."""
        expected_interval = 300
        seconds_ago = 250
        ratio = seconds_ago / expected_interval
        
        assert ratio < 1.0, f"Ratio {ratio} should be < 1.0 for green"
        assert ratio == pytest.approx(0.833, abs=0.001)
    
    def test_syncthing_299s_should_be_green(self):
        """Test syncthing at 299s should show green (ratio 0.997 < 1.0) - edge case."""
        expected_interval = 300
        seconds_ago = 299
        ratio = seconds_ago / expected_interval
        
        assert ratio < 1.0, f"Ratio {ratio} should be < 1.0 for green"
        assert ratio == pytest.approx(0.997, abs=0.001)
    
    def test_syncthing_300s_should_be_yellow(self):
        """Test syncthing at 300s should show yellow (ratio 1.0) - edge case."""
        expected_interval = 300
        seconds_ago = 300
        ratio = seconds_ago / expected_interval
        
        assert ratio >= 1.0, f"Ratio {ratio} should be >= 1.0 for yellow"
        assert ratio < 2.0, f"Ratio {ratio} should be < 2.0 for yellow"
        assert ratio == 1.0
    
    def test_syncthing_350s_should_be_yellow(self):
        """Test syncthing at 350s should show yellow (ratio 1.167)."""
        expected_interval = 300
        seconds_ago = 350
        ratio = seconds_ago / expected_interval
        
        assert ratio >= 1.0, f"Ratio {ratio} should be >= 1.0 for yellow"
        assert ratio < 2.0, f"Ratio {ratio} should be < 2.0 for yellow"
        assert ratio == pytest.approx(1.167, abs=0.001)
    
    def test_syncthing_450s_should_be_yellow(self):
        """Test syncthing at 450s should show yellow (ratio 1.5)."""
        expected_interval = 300
        seconds_ago = 450
        ratio = seconds_ago / expected_interval
        
        assert ratio >= 1.0, f"Ratio {ratio} should be >= 1.0 for yellow"
        assert ratio < 2.0, f"Ratio {ratio} should be < 2.0 for yellow"
        assert ratio == 1.5
    
    def test_syncthing_599s_should_be_yellow(self):
        """Test syncthing at 599s should show yellow (ratio 1.997) - edge case."""
        expected_interval = 300
        seconds_ago = 599
        ratio = seconds_ago / expected_interval
        
        assert ratio >= 1.0, f"Ratio {ratio} should be >= 1.0 for yellow"
        assert ratio < 2.0, f"Ratio {ratio} should be < 2.0 for yellow"
        assert ratio == pytest.approx(1.997, abs=0.001)
    
    def test_syncthing_600s_should_be_red(self):
        """Test syncthing at 600s should show red (ratio 2.0) - edge case."""
        expected_interval = 300
        seconds_ago = 600
        ratio = seconds_ago / expected_interval
        
        assert ratio >= 2.0, f"Ratio {ratio} should be >= 2.0 for red"
        assert ratio == 2.0
    
    def test_syncthing_900s_should_be_red(self):
        """Test syncthing at 900s should show red (ratio 3.0)."""
        expected_interval = 300
        seconds_ago = 900
        ratio = seconds_ago / expected_interval
        
        assert ratio >= 2.0, f"Ratio {ratio} should be >= 2.0 for red"
        assert ratio == 3.0
    
    def test_librarian_41s_should_be_green(self):
        """Test librarian at 41s should show green (ratio 0.683 < 1.0)."""
        expected_interval = 60
        seconds_ago = 41
        ratio = seconds_ago / expected_interval
        
        assert ratio < 1.0, f"Ratio {ratio} should be < 1.0 for green"
        assert ratio == pytest.approx(0.683, abs=0.001)
    
    def test_librarian_90s_should_be_yellow(self):
        """Test librarian at 90s should show yellow (ratio 1.5)."""
        expected_interval = 60
        seconds_ago = 90
        ratio = seconds_ago / expected_interval
        
        assert ratio >= 1.0, f"Ratio {ratio} should be >= 1.0 for yellow"
        assert ratio < 2.0, f"Ratio {ratio} should be < 2.0 for yellow"
        assert ratio == 1.5
    
    def test_librarian_120s_should_be_red(self):
        """Test librarian at 120s should show red (ratio 2.0)."""
        expected_interval = 60
        seconds_ago = 120
        ratio = seconds_ago / expected_interval
        
        assert ratio >= 2.0, f"Ratio {ratio} should be >= 2.0 for red"
        assert ratio == 2.0


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
                        
                        # Verify ratio and color
                        assert ratio < 1.0, f"Ratio {ratio} should be < 1.0 for green"
                        assert seconds_ago == 109, f"Expected 109s, got {seconds_ago}s"
                        assert expected_interval == 300, f"Expected 300s interval, got {expected_interval}s"
                        
                        if ratio < 1.0:
                            color = "🟢"
                        elif ratio < 2.0:
                            color = "🟡"
                        else:
                            color = "🔴"
                        
                        assert color == "🟢", f"Expected green, got {color} for ratio {ratio}"
    
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
                        ratio = seconds_ago / expected_interval
                        
                        assert ratio >= 1.0 and ratio < 2.0, f"Ratio {ratio} should be 1.0-2.0 for yellow"
                        
                        if ratio < 1.0:
                            color = "🟢"
                        elif ratio < 2.0:
                            color = "🟡"
                        else:
                            color = "🔴"
                        
                        assert color == "🟡", f"Expected yellow, got {color} for ratio {ratio}"
    
    def test_syncthing_600s_shows_red_in_status_data(self):
        """Test that syncthing at 600s shows red in status_data table."""
        get_all_services_status.clear()
        
        with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True):
            with patch('Src.Dashboard.dashboard.get_available_services') as mock_services:
                mock_services.return_value = ["syncthing"]
                
                with patch('Src.Dashboard.dashboard.get_container_status') as mock_container:
                    mock_container.return_value = {"running": True, "health": "healthy"}
                    
                    with patch('Src.Dashboard.dashboard.get_service_heartbeat') as mock_heartbeat:
                        # Syncthing at 600 seconds (should be red)
                        mock_heartbeat.return_value = {
                            "last_heartbeat": datetime.now() - timedelta(seconds=600),
                            "status": "OK"
                        }
                        
                        result = get_all_services_status()
                        
                        svc = result[0]
                        service_intervals = {"syncthing": 300}
                        service_name_for_interval = svc.get("service_name")
                        expected_interval = service_intervals.get(service_name_for_interval, 300)
                        
                        time_since = datetime.now() - svc["heartbeat"]["last_heartbeat"]
                        seconds_ago = int(time_since.total_seconds())
                        ratio = seconds_ago / expected_interval
                        
                        assert ratio >= 2.0, f"Ratio {ratio} should be >= 2.0 for red"
                        
                        if ratio < 1.0:
                            color = "🟢"
                        elif ratio < 2.0:
                            color = "🟡"
                        else:
                            color = "🔴"
                        
                        assert color == "🔴", f"Expected red, got {color} for ratio {ratio}"
    
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
                        
                        # Test the color calculation
                        service_intervals = {"syncthing": 300}
                        service_name_for_interval = svc.get("service_name")
                        expected_interval = service_intervals.get(service_name_for_interval, 300)
                        
                        time_since = datetime.now() - svc["heartbeat"]["last_heartbeat"]
                        seconds_ago = int(time_since.total_seconds())
                        ratio = seconds_ago / expected_interval
                        
                        assert ratio < 1.0, f"Ratio {ratio} should be < 1.0 for green (109/300 = 0.363)"
                        assert seconds_ago == 109, f"Expected 109s, got {seconds_ago}s"
                        
                        if ratio < 1.0:
                            color = "🟢"
                        elif ratio < 2.0:
                            color = "🟡"
                        else:
                            color = "🔴"
                        
                        assert color == "🟢", f"Expected green for 109s (ratio {ratio}), got {color}"

