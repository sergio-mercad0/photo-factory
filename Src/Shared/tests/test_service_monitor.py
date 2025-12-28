"""
Tests for service monitor functionality.

Verifies that service monitor correctly checks infrastructure services
and updates heartbeat tables.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import subprocess

from Src.Shared.service_monitor import (
    check_factory_db,
    check_syncthing,
    update_heartbeat,
    monitor_loop
)
from Src.Shared.models import SystemStatus, SystemStatusHistory


class TestServiceHealthChecks:
    """Test health check functions for infrastructure services."""
    
    def test_check_factory_db_success(self):
        """Test successful factory-db health check."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            result = check_factory_db()
            
            assert result is True
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert 'pg_isready' in call_args[0][0]
            assert '-U' in call_args[0][0]
            assert '-h' in call_args[0][0]
            assert 'factory-db' in call_args[0][0]
    
    def test_check_factory_db_failure(self):
        """Test failed factory-db health check."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1)
            
            result = check_factory_db()
            
            assert result is False
    
    def test_check_factory_db_timeout(self):
        """Test factory-db health check with timeout."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired('pg_isready', 5)
            
            result = check_factory_db()
            
            assert result is False
    
    def test_check_syncthing_success(self):
        """Test successful Syncthing health check."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            result = check_syncthing()
            
            assert result is True
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert 'wget' in call_args[0][0]
            assert 'syncthing:8384' in call_args[0][0]
    
    def test_check_syncthing_failure(self):
        """Test failed Syncthing health check."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1)
            
            result = check_syncthing()
            
            assert result is False


class TestHeartbeatUpdate:
    """Test heartbeat update functionality."""
    
    def test_update_heartbeat_creates_new_record(self):
        """Test that update_heartbeat creates new record if none exists."""
        with patch('Src.Shared.service_monitor.get_db_session') as mock_session:
            mock_session_obj = Mock()
            mock_session_obj.__enter__ = Mock(return_value=mock_session_obj)
            mock_session_obj.__exit__ = Mock(return_value=False)
            mock_session.return_value = mock_session_obj
            
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None  # No existing record
            mock_session_obj.query.return_value = mock_query
            
            update_heartbeat("test-service", True, "Test task")
            
            # Verify new record was added
            assert mock_session_obj.add.call_count == 2  # SystemStatus + SystemStatusHistory
            add_calls = [call[0][0] for call in mock_session_obj.add.call_args_list]
            
            # Check SystemStatus was added
            status_added = [obj for obj in add_calls if isinstance(obj, SystemStatus)]
            assert len(status_added) == 1
            assert status_added[0].service_name == "test-service"
            assert status_added[0].status == "OK"
            assert status_added[0].current_task == "Test task"
            
            # Check SystemStatusHistory was added
            history_added = [obj for obj in add_calls if isinstance(obj, SystemStatusHistory)]
            assert len(history_added) == 1
            assert history_added[0].service_name == "test-service"
            assert history_added[0].status == "OK"
            assert history_added[0].current_task == "Test task"
            
            mock_session_obj.commit.assert_called_once()
    
    def test_update_heartbeat_updates_existing_record(self):
        """Test that update_heartbeat updates existing record."""
        with patch('Src.Shared.service_monitor.get_db_session') as mock_session:
            mock_session_obj = Mock()
            mock_session_obj.__enter__ = Mock(return_value=mock_session_obj)
            mock_session_obj.__exit__ = Mock(return_value=False)
            mock_session.return_value = mock_session_obj
            
            # Create existing status record
            existing_status = SystemStatus(
                service_name="test-service",
                status="OK",
                last_heartbeat=datetime.now() - timedelta(minutes=10)
            )
            
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = existing_status
            mock_session_obj.query.return_value = mock_query
            
            update_heartbeat("test-service", False, "Error task")
            
            # Verify existing record was updated
            assert existing_status.status == "ERROR"
            assert existing_status.current_task == "Error task"
            
            # Verify history record was added
            assert mock_session_obj.add.call_count == 1  # Only SystemStatusHistory
            add_calls = [call[0][0] for call in mock_session_obj.add.call_args_list]
            history_added = [obj for obj in add_calls if isinstance(obj, SystemStatusHistory)]
            assert len(history_added) == 1
            assert history_added[0].status == "ERROR"
            
            mock_session_obj.commit.assert_called_once()
    
    def test_update_heartbeat_handles_database_error(self):
        """Test that update_heartbeat handles database errors gracefully."""
        with patch('Src.Shared.service_monitor.get_db_session') as mock_session:
            mock_session.side_effect = Exception("Database connection failed")
            
            # Should not raise exception
            update_heartbeat("test-service", True, "Test task")
            
            # Function should complete without crashing


class TestMonitorLoop:
    """Test the main monitoring loop."""
    
    @patch('Src.Shared.service_monitor.time.sleep')
    @patch('Src.Shared.service_monitor.update_heartbeat')
    @patch('Src.Shared.service_monitor.check_syncthing')
    @patch('Src.Shared.service_monitor.check_factory_db')
    @patch('Src.Shared.service_monitor.init_database')
    def test_monitor_loop_checks_services(self, mock_init, mock_check_db, mock_check_syncthing, mock_update, mock_sleep):
        """Test that monitor loop checks both services."""
        # Setup mocks
        mock_check_db.return_value = True
        mock_check_syncthing.return_value = True
        mock_sleep.side_effect = [None, KeyboardInterrupt()]  # Run once, then interrupt
        
        try:
            monitor_loop(interval=0.1)
        except KeyboardInterrupt:
            pass
        
        # Verify database was initialized
        mock_init.assert_called_once()
        
        # Verify both services were checked
        assert mock_check_db.call_count >= 1
        assert mock_check_syncthing.call_count >= 1
        
        # Verify heartbeats were updated
        assert mock_update.call_count >= 2  # At least one for each service
        
        # Verify update calls
        update_calls = [call[0] for call in mock_update.call_args_list]
        service_names = [call[0] for call in update_calls]
        assert "factory-db" in service_names
        assert "syncthing" in service_names
    
    @patch('Src.Shared.service_monitor.time.sleep')
    @patch('Src.Shared.service_monitor.update_heartbeat')
    @patch('Src.Shared.service_monitor.check_syncthing')
    @patch('Src.Shared.service_monitor.check_factory_db')
    @patch('Src.Shared.service_monitor.init_database')
    def test_monitor_loop_handles_check_errors(self, mock_init, mock_check_db, mock_check_syncthing, mock_update, mock_sleep):
        """Test that monitor loop handles check errors gracefully."""
        # Setup mocks
        mock_check_db.side_effect = Exception("Check failed")
        mock_check_syncthing.return_value = True
        mock_sleep.side_effect = [None, KeyboardInterrupt()]  # Run once, then interrupt
        
        try:
            monitor_loop(interval=0.1)
        except KeyboardInterrupt:
            pass
        
        # Should continue running despite errors
        assert mock_sleep.call_count >= 1

