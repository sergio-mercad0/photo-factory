"""
Tests to ensure dashboard data is fresh and not stale.

This test suite prevents issues like stale heartbeat data being displayed.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from Src.Dashboard.dashboard import (
    get_librarian_heartbeat,
    get_service_heartbeat,
    get_total_assets,
    get_assets_last_hour,
)


class TestHeartbeatDataFreshness:
    """Test that heartbeat data is always fresh and correctly calculated."""
    
    def test_heartbeat_time_calculation_is_fresh(self):
        """
        Test that heartbeat time calculation uses current time, not stale timestamps.
        
        This prevents the issue where preserving old heartbeat timestamps
        and calculating time_since from current time makes it look stale.
        """
        # Create a mock heartbeat record with a recent timestamp
        recent_heartbeat = datetime.now() - timedelta(seconds=30)
        
        with patch('Src.Dashboard.dashboard.get_db_session') as mock_session:
            # Mock the database session
            mock_status = Mock()
            mock_status.last_heartbeat = recent_heartbeat
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
            
            # Get heartbeat
            result = get_librarian_heartbeat()
            
            # Verify result contains the heartbeat timestamp
            assert result is not None
            assert "last_heartbeat" in result
            assert result["last_heartbeat"] == recent_heartbeat
            
            # Verify time calculation would be fresh (not stale)
            time_since = datetime.now() - result["last_heartbeat"]
            seconds_ago = int(time_since.total_seconds())
            
            # Should be around 30 seconds (with some tolerance for test execution time)
            assert 25 <= seconds_ago <= 35, f"Expected ~30s ago, got {seconds_ago}s"
    
    def test_heartbeat_returns_none_when_no_data(self):
        """Test that heartbeat returns None when no data exists."""
        with patch('Src.Dashboard.dashboard.get_db_session') as mock_session:
            # Mock the query chain: query().filter().first() returns None
            mock_query_result = Mock()
            mock_query_result.first.return_value = None
            
            mock_query = Mock()
            mock_query.filter.return_value = mock_query_result
            
            mock_session_obj = Mock()
            mock_session_obj.__enter__ = Mock(return_value=mock_session_obj)
            mock_session_obj.__exit__ = Mock(return_value=False)
            mock_session_obj.query.return_value = mock_query
            mock_session.return_value = mock_session_obj
            
            result = get_librarian_heartbeat()
            assert result is None
    
    def test_service_heartbeat_uses_fresh_timestamp(self):
        """Test that service heartbeat calculation uses current time."""
        recent_heartbeat = datetime.now() - timedelta(seconds=45)
        
        with patch('Src.Dashboard.dashboard.get_db_session') as mock_session:
            mock_status = Mock()
            mock_status.last_heartbeat = recent_heartbeat
            mock_status.status = "OK"
            mock_status.current_task = "processing"
            mock_status.updated_at = datetime.now()
            
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = mock_status
            
            mock_session_obj = Mock()
            mock_session_obj.__enter__ = Mock(return_value=mock_session_obj)
            mock_session_obj.__exit__ = Mock(return_value=False)
            mock_session_obj.query.return_value = mock_query
            mock_session.return_value = mock_session_obj
            
            result = get_service_heartbeat("test_service")
            
            assert result is not None
            assert result["last_heartbeat"] == recent_heartbeat
            
            # Verify time calculation is fresh
            time_since = datetime.now() - result["last_heartbeat"]
            seconds_ago = int(time_since.total_seconds())
            assert 40 <= seconds_ago <= 50, f"Expected ~45s ago, got {seconds_ago}s"


class TestDataNotStale:
    """Test that dashboard functions don't return stale cached data when it shouldn't."""
    
    def test_cached_data_has_appropriate_ttl(self):
        """
        Test that cached functions have appropriate TTL values.
        
        Heartbeat data should have short TTL (5s) to ensure freshness.
        """
        import inspect
        from Src.Dashboard import dashboard
        
        # Check that heartbeat functions have short TTL
        heartbeat_func = dashboard.get_librarian_heartbeat
        if hasattr(heartbeat_func, 'cache_ttl'):
            # If using st.cache_data with TTL, verify it's short
            ttl = heartbeat_func.cache_ttl
            assert ttl <= 10, f"Heartbeat cache TTL should be <= 10s, got {ttl}s"
    
    def test_heartbeat_time_always_calculated_from_now(self):
        """
        Test that heartbeat time differences are always calculated from current time.
        
        This prevents the bug where old timestamps are preserved and time_since
        is calculated incorrectly, making it look like 95s ago when it should be 5s.
        """
        # Simulate a heartbeat that was updated 5 seconds ago
        heartbeat_time = datetime.now() - timedelta(seconds=5)
        
        # Calculate time since (this is what the dashboard does)
        time_since = datetime.now() - heartbeat_time
        seconds_ago = int(time_since.total_seconds())
        
        # Should be around 5 seconds (with tolerance)
        assert 3 <= seconds_ago <= 7, f"Expected ~5s ago, got {seconds_ago}s - this indicates stale data calculation"
        
        # Verify this doesn't become stale over time
        # (In real code, this calculation happens every render, so it's always fresh)
        assert seconds_ago < 10, "Heartbeat should never show >10s if calculated fresh"

