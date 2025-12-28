"""
Tests for heartbeat service with history table functionality.

Verifies that heartbeats are written to both system_status and system_status_history.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from Src.Librarian.heartbeat import HeartbeatService
from Src.Shared.models import SystemStatus, SystemStatusHistory


class TestHeartbeatHistory:
    """Test heartbeat service writes to both current and history tables."""
    
    def test_heartbeat_writes_to_both_tables(self, mock_database):
        """Test that heartbeat updates both system_status and system_status_history."""
        service = HeartbeatService(service_name="test_service", interval=60.0)
        service.set_status("OK")
        service.set_current_task("testing")
        
        # Mock the session to track what gets added/updated
        mock_session = mock_database
        mock_status_record = Mock(spec=SystemStatus)
        mock_status_record.service_name = "test_service"
        mock_status_record.status = "OK"
        mock_status_record.current_task = None
        mock_status_record.last_heartbeat = None
        
        # Mock query for existing status
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None  # No existing record
        mock_session.query.return_value = mock_query
        
        # Call the update method
        service._update_heartbeat()
        
        # Verify both tables were written to
        # 1. SystemStatus should be added (new record)
        assert mock_session.add.call_count >= 1, "Should add at least one record"
        
        # Verify SystemStatusHistory was added
        add_calls = [call[0][0] for call in mock_session.add.call_args_list]
        history_added = any(isinstance(obj, SystemStatusHistory) for obj in add_calls)
        assert history_added, "SystemStatusHistory record should be added"
        
        # Verify SystemStatus was added or updated
        status_added = any(isinstance(obj, SystemStatus) for obj in add_calls)
        assert status_added, "SystemStatus record should be added"
        
        # Verify commit was called
        mock_session.commit.assert_called_once()
    
    def test_heartbeat_updates_existing_status_and_adds_history(self, mock_database):
        """Test that existing status is updated and new history record is added."""
        service = HeartbeatService(service_name="test_service", interval=60.0)
        service.set_status("OK")
        
        # Mock existing status record
        existing_status = Mock(spec=SystemStatus)
        existing_status.service_name = "test_service"
        existing_status.status = "ERROR"  # Old status
        existing_status.current_task = None
        existing_status.last_heartbeat = datetime.now() - timedelta(minutes=5)
        
        mock_session = mock_database
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = existing_status
        mock_session.query.return_value = mock_query
        
        # Update heartbeat
        service._update_heartbeat()
        
        # Verify existing status was updated
        assert existing_status.status == "OK", "Status should be updated"
        assert existing_status.last_heartbeat is not None, "Heartbeat timestamp should be set"
        
        # Verify history record was added
        add_calls = [call[0][0] for call in mock_session.add.call_args_list]
        history_added = any(isinstance(obj, SystemStatusHistory) for obj in add_calls)
        assert history_added, "New history record should be added"
        
        mock_session.commit.assert_called_once()
    
    def test_heartbeat_includes_all_fields_in_history(self, mock_database):
        """Test that history record includes all relevant fields."""
        service = HeartbeatService(service_name="test_service", interval=60.0)
        service.set_status("WARNING")
        service.set_current_task("Processing large file")
        
        mock_session = mock_database
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query
        
        service._update_heartbeat()
        
        # Find the history record that was added
        add_calls = [call[0][0] for call in mock_session.add.call_args_list]
        history_records = [obj for obj in add_calls if isinstance(obj, SystemStatusHistory)]
        
        assert len(history_records) == 1, "Should add exactly one history record"
        history = history_records[0]
        
        assert history.service_name == "test_service"
        assert history.status == "WARNING"
        assert history.current_task == "Processing large file"
        assert history.heartbeat_timestamp is not None
        assert isinstance(history.heartbeat_timestamp, datetime)

