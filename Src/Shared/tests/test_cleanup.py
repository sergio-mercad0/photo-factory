"""
Tests for database cleanup functionality.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from Src.Shared.cleanup import cleanup_system_status_history, get_history_record_count


class TestCleanup:
    """Test cleanup functions."""
    
    def test_cleanup_deletes_old_records(self):
        """Test that cleanup deletes records older than retention period."""
        with patch('Src.Shared.cleanup.get_db_session') as mock_session_factory:
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session.commit = MagicMock()
            
            # Mock execute result
            mock_result = Mock()
            mock_result.rowcount = 42  # 42 records deleted
            mock_session.execute.return_value = mock_result
            
            mock_session_factory.return_value = mock_session
            
            deleted = cleanup_system_status_history(retention_days=60)
            
            assert deleted == 42
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()
    
    def test_cleanup_handles_no_records(self):
        """Test cleanup when no old records exist."""
        with patch('Src.Shared.cleanup.get_db_session') as mock_session_factory:
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session.commit = MagicMock()
            
            mock_result = Mock()
            mock_result.rowcount = 0
            mock_session.execute.return_value = mock_result
            
            mock_session_factory.return_value = mock_session
            
            deleted = cleanup_system_status_history(retention_days=60)
            
            assert deleted == 0
            mock_session.commit.assert_called_once()
    
    def test_get_history_record_count_all_services(self):
        """Test getting count for all services."""
        with patch('Src.Shared.cleanup.get_db_session') as mock_session_factory:
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            
            mock_result = Mock()
            mock_result.scalar.return_value = 100
            mock_session.execute.return_value = mock_result
            
            mock_session_factory.return_value = mock_session
            
            count = get_history_record_count()
            
            assert count == 100
            mock_session.execute.assert_called_once()
    
    def test_get_history_record_count_specific_service(self):
        """Test getting count for specific service."""
        with patch('Src.Shared.cleanup.get_db_session') as mock_session_factory:
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            
            mock_result = Mock()
            mock_result.scalar.return_value = 50
            mock_session.execute.return_value = mock_result
            
            mock_session_factory.return_value = mock_session
            
            count = get_history_record_count(service_name="librarian")
            
            assert count == 50
            # Verify the query included service_name filter
            call_args = mock_session.execute.call_args
            assert "service_name" in str(call_args)

