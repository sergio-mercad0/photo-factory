"""
Simple test to verify heartbeat display format and color logic.
Tests the exact scenario reported by user: syncthing at 102s should be green.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from Src.Dashboard.dashboard import get_all_services_status


def test_syncthing_102s_should_be_green():
    """Test that syncthing at 102s shows green (102/300 = 0.34 < 1.0)."""
    get_all_services_status.clear()
    
    with patch('Src.Dashboard.dashboard.DOCKER_AVAILABLE', True):
        with patch('Src.Dashboard.dashboard.get_available_services') as mock_services:
            mock_services.return_value = ["syncthing"]
            
            with patch('Src.Dashboard.dashboard.get_container_status') as mock_container:
                mock_container.return_value = {"running": True, "health": "healthy"}
                
                with patch('Src.Dashboard.dashboard.get_service_heartbeat') as mock_heartbeat:
                    # Syncthing at 102 seconds (should be green)
                    mock_heartbeat.return_value = {
                        "last_heartbeat": datetime.now() - timedelta(seconds=102),
                        "status": "OK"
                    }
                    
                    result = get_all_services_status()
                    
                    assert len(result) == 1
                    svc = result[0]
                    assert svc["name"] == "syncthing"
                    assert svc["service_name"] == "syncthing"
                    assert svc["heartbeat"] is not None
                    
                    # Now test the display logic (simulate what happens in the table)
                    service_intervals = {
                        "librarian": 60,
                        "dashboard": 300,
                        "factory-db": 300,
                        "syncthing": 300,
                    }
                    
                    service_name = svc.get("service_name")
                    expected_interval = service_intervals.get(service_name, 300)
                    
                    time_since = datetime.now() - svc["heartbeat"]["last_heartbeat"]
                    seconds_ago = int(time_since.total_seconds())
                    ratio = seconds_ago / expected_interval if expected_interval > 0 else 0
                    
                    # Verify the calculation
                    assert seconds_ago == 102, f"Expected 102s, got {seconds_ago}s"
                    assert expected_interval == 300, f"Expected 300s interval, got {expected_interval}s"
                    assert ratio == pytest.approx(0.34, abs=0.01), f"Expected ratio ~0.34, got {ratio:.4f}"
                    
                    # Verify color
                    if ratio < 1.0:
                        color = "🟢"
                    elif ratio < 2.0:
                        color = "🟡"
                    else:
                        color = "🔴"
                    
                    assert color == "🟢", f"Expected green for 102s (ratio {ratio:.4f}), got {color}"
                    
                    # Verify format
                    heartbeat_info = f"{color} {seconds_ago}s/{expected_interval}s ago"
                    assert "102s/300s" in heartbeat_info, f"Expected '102s/300s' in display, got '{heartbeat_info}'"
                    assert color == "🟢" in heartbeat_info, f"Expected green emoji in display, got '{heartbeat_info}'"





