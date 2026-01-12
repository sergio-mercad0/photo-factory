"""
Unit tests for dashboard system resource monitoring functions.

This test suite covers:
- get_system_resources() - CPU, RAM, Disk metrics collection
- render_resource_header() - Header UI rendering with resource metrics

All tests use mocked psutil to ensure build-time safety (no real system calls).
"""
import pytest
from unittest.mock import MagicMock, patch, call


# =============================================================================
# Test: get_system_resources() - Unit Tests with Mocked psutil
# =============================================================================
@pytest.mark.unit
class TestGetSystemResources:
    """Unit tests for get_system_resources() function."""
    
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear Streamlit cache before each test."""
        # Import and clear cache to ensure fresh test data
        try:
            from Src.Dashboard.dashboard import get_system_resources
            get_system_resources.clear()
        except (ImportError, AttributeError):
            pass  # Cache may not exist in test context
        yield
    
    @patch('Src.Dashboard.dashboard.psutil')
    def test_returns_cpu_percent(self, mock_psutil):
        """Verify CPU percentage is returned correctly."""
        # Arrange
        mock_psutil.cpu_percent.return_value = 45.5
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=60.0, used=8 * 1024**3, total=16 * 1024**3
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            percent=70.0, used=500 * 1024**3, total=1000 * 1024**3
        )
        
        # Act
        from Src.Dashboard.dashboard import get_system_resources
        result = get_system_resources()
        
        # Assert
        assert result['cpu_percent'] == 45.5
        mock_psutil.cpu_percent.assert_called_once_with(interval=None)
    
    @patch('Src.Dashboard.dashboard.psutil')
    def test_returns_ram_metrics(self, mock_psutil):
        """Verify RAM percentage and GB values are returned."""
        # Arrange
        mock_psutil.cpu_percent.return_value = 10.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=62.5, used=10 * 1024**3, total=16 * 1024**3
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            percent=50.0, used=500 * 1024**3, total=1000 * 1024**3
        )
        
        # Act
        from Src.Dashboard.dashboard import get_system_resources
        result = get_system_resources()
        
        # Assert
        assert result['ram_percent'] == 62.5
        mock_psutil.virtual_memory.assert_called_once()
    
    @patch('Src.Dashboard.dashboard.psutil')
    def test_returns_disk_metrics(self, mock_psutil):
        """Verify Disk percentage and GB values are returned."""
        # Arrange
        mock_psutil.cpu_percent.return_value = 20.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=50.0, used=8 * 1024**3, total=16 * 1024**3
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            percent=75.0, used=750 * 1024**3, total=1000 * 1024**3
        )
        
        # Act
        from Src.Dashboard.dashboard import get_system_resources
        result = get_system_resources()
        
        # Assert
        assert result['disk_percent'] == 75.0
        mock_psutil.disk_usage.assert_called()
    
    @patch('Src.Dashboard.dashboard.psutil')
    def test_converts_bytes_to_gb_ram(self, mock_psutil):
        """Verify RAM bytes are correctly converted to GB."""
        # Arrange - Use exact byte values for precise GB conversion
        ram_used_bytes = 8 * (1024 ** 3)  # 8 GB
        ram_total_bytes = 16 * (1024 ** 3)  # 16 GB
        
        mock_psutil.cpu_percent.return_value = 10.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=50.0, used=ram_used_bytes, total=ram_total_bytes
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            percent=25.0, used=250 * 1024**3, total=1000 * 1024**3
        )
        
        # Act
        from Src.Dashboard.dashboard import get_system_resources
        result = get_system_resources()
        
        # Assert
        assert result['ram_used_gb'] == pytest.approx(8.0, rel=0.01)
        assert result['ram_total_gb'] == pytest.approx(16.0, rel=0.01)
    
    @patch('Src.Dashboard.dashboard.psutil')
    def test_converts_bytes_to_gb_disk(self, mock_psutil):
        """Verify Disk bytes are correctly converted to GB."""
        # Arrange - Use exact byte values for precise GB conversion
        disk_used_bytes = 250 * (1024 ** 3)  # 250 GB
        disk_total_bytes = 1000 * (1024 ** 3)  # 1 TB
        
        mock_psutil.cpu_percent.return_value = 10.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=50.0, used=8 * 1024**3, total=16 * 1024**3
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            percent=25.0, used=disk_used_bytes, total=disk_total_bytes
        )
        
        # Act
        from Src.Dashboard.dashboard import get_system_resources
        result = get_system_resources()
        
        # Assert
        assert result['disk_used_gb'] == pytest.approx(250.0, rel=0.01)
        assert result['disk_total_gb'] == pytest.approx(1000.0, rel=0.01)
    
    @patch('Src.Dashboard.dashboard.psutil')
    def test_returns_all_expected_keys(self, mock_psutil):
        """Verify all expected keys are present in the result dictionary."""
        # Arrange
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=60.0, used=8 * 1024**3, total=16 * 1024**3
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            percent=70.0, used=500 * 1024**3, total=1000 * 1024**3
        )
        
        # Act
        from Src.Dashboard.dashboard import get_system_resources
        result = get_system_resources()
        
        # Assert
        expected_keys = [
            'cpu_percent',
            'ram_percent',
            'ram_used_gb',
            'ram_total_gb',
            'disk_percent',
            'disk_used_gb',
            'disk_total_gb',
        ]
        for key in expected_keys:
            assert key in result, f"Missing expected key: {key}"
    
    @patch('Src.Dashboard.dashboard.psutil')
    def test_handles_disk_usage_root_path(self, mock_psutil):
        """Verify disk_usage is called with root path '/'."""
        # Arrange
        mock_psutil.cpu_percent.return_value = 30.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=40.0, used=6 * 1024**3, total=16 * 1024**3
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            percent=50.0, used=250 * 1024**3, total=500 * 1024**3
        )
        
        # Act
        from Src.Dashboard.dashboard import get_system_resources
        get_system_resources()
        
        # Assert - Should try '/' first
        mock_psutil.disk_usage.assert_called_with('/')
    
    @patch('Src.Dashboard.dashboard.psutil')
    def test_handles_disk_usage_windows_fallback(self, mock_psutil):
        """Verify disk_usage falls back to 'C:\\' on Windows if '/' fails."""
        # Arrange
        mock_psutil.cpu_percent.return_value = 30.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=40.0, used=6 * 1024**3, total=16 * 1024**3
        )
        
        # Make '/' fail, then 'C:\\' succeed
        def disk_usage_side_effect(path):
            if path == '/':
                raise Exception("Root path not found")
            return MagicMock(
                percent=50.0, used=250 * 1024**3, total=500 * 1024**3
            )
        
        mock_psutil.disk_usage.side_effect = disk_usage_side_effect
        
        # Act
        from Src.Dashboard.dashboard import get_system_resources
        result = get_system_resources()
        
        # Assert
        assert result['disk_percent'] == 50.0
        # Verify fallback to C:\\ was attempted
        assert mock_psutil.disk_usage.call_count == 2
    
    @patch('Src.Dashboard.dashboard.psutil')
    def test_handles_exception_gracefully(self, mock_psutil):
        """Verify function returns zeroed values on exception."""
        # Arrange - Make psutil raise an exception
        mock_psutil.cpu_percent.side_effect = Exception("System error")
        
        # Act
        from Src.Dashboard.dashboard import get_system_resources
        result = get_system_resources()
        
        # Assert - Should return zeroed values
        assert result['cpu_percent'] == 0.0
        assert result['ram_percent'] == 0.0
        assert result['ram_used_gb'] == 0.0
        assert result['ram_total_gb'] == 0.0
        assert result['disk_percent'] == 0.0
        assert result['disk_used_gb'] == 0.0
        assert result['disk_total_gb'] == 0.0
    
    @patch('Src.Dashboard.dashboard.psutil')
    def test_cpu_percent_interval_none_for_cached_value(self, mock_psutil):
        """Verify cpu_percent uses interval=None for non-blocking cached value."""
        # Arrange
        mock_psutil.cpu_percent.return_value = 25.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=50.0, used=8 * 1024**3, total=16 * 1024**3
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            percent=60.0, used=300 * 1024**3, total=500 * 1024**3
        )
        
        # Act
        from Src.Dashboard.dashboard import get_system_resources
        get_system_resources()
        
        # Assert - interval=None means non-blocking (uses cached value)
        mock_psutil.cpu_percent.assert_called_with(interval=None)
    
    @patch('Src.Dashboard.dashboard.psutil')
    def test_high_resource_usage_values(self, mock_psutil):
        """Verify high resource usage values are handled correctly."""
        # Arrange - Simulate high usage scenario
        mock_psutil.cpu_percent.return_value = 99.9
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=95.5, used=30.64 * 1024**3, total=32 * 1024**3
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            percent=98.0, used=980 * 1024**3, total=1000 * 1024**3
        )
        
        # Act
        from Src.Dashboard.dashboard import get_system_resources
        result = get_system_resources()
        
        # Assert
        assert result['cpu_percent'] == 99.9
        assert result['ram_percent'] == 95.5
        assert result['disk_percent'] == 98.0
    
    @patch('Src.Dashboard.dashboard.psutil')
    def test_zero_resource_values(self, mock_psutil):
        """Verify zero resource values are handled correctly."""
        # Arrange - Edge case with zeros
        mock_psutil.cpu_percent.return_value = 0.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=0.0, used=0, total=16 * 1024**3
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            percent=0.0, used=0, total=500 * 1024**3
        )
        
        # Act
        from Src.Dashboard.dashboard import get_system_resources
        result = get_system_resources()
        
        # Assert
        assert result['cpu_percent'] == 0.0
        assert result['ram_percent'] == 0.0
        assert result['ram_used_gb'] == 0.0
        assert result['disk_percent'] == 0.0
        assert result['disk_used_gb'] == 0.0


# =============================================================================
# Test: render_resource_header() - Output Validation Tests
# =============================================================================
@pytest.mark.unit
class TestRenderResourceHeader:
    """Unit tests for render_resource_header() function output validation."""
    
    @patch('Src.Dashboard.dashboard.get_available_services')
    @patch('Src.Dashboard.dashboard.get_system_resources')
    @patch('Src.Dashboard.dashboard.st')
    def test_creates_four_column_layout(self, mock_st, mock_resources, mock_services):
        """Verify header creates four columns: CPU, RAM, Disk, Selector."""
        # Arrange
        mock_resources.return_value = {
            'cpu_percent': 50.0,
            'ram_percent': 60.0,
            'ram_used_gb': 8.0,
            'ram_total_gb': 16.0,
            'disk_percent': 70.0,
            'disk_used_gb': 350.0,
            'disk_total_gb': 500.0,
        }
        mock_services.return_value = ['librarian', 'dashboard']
        
        # Setup mock columns
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols
        
        # Setup context managers for each column
        for col in mock_cols:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=None)
        
        # Act
        from Src.Dashboard.dashboard import render_resource_header
        render_resource_header()
        
        # Assert - Verify columns were created with expected ratio
        mock_st.columns.assert_called_once_with([1, 1.5, 1.5, 3])
    
    @patch('Src.Dashboard.dashboard.get_available_services')
    @patch('Src.Dashboard.dashboard.get_system_resources')
    @patch('Src.Dashboard.dashboard.st')
    def test_displays_cpu_metric(self, mock_st, mock_resources, mock_services):
        """Verify CPU metric is displayed with correct format."""
        # Arrange
        mock_resources.return_value = {
            'cpu_percent': 45.7,
            'ram_percent': 60.0,
            'ram_used_gb': 8.0,
            'ram_total_gb': 16.0,
            'disk_percent': 70.0,
            'disk_used_gb': 350.0,
            'disk_total_gb': 500.0,
        }
        mock_services.return_value = ['librarian']
        
        # Setup mock columns
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols
        
        for col in mock_cols:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=None)
        
        # Act
        from Src.Dashboard.dashboard import render_resource_header
        render_resource_header()
        
        # Assert - CPU should be called with "46%" (rounded from 45.7)
        cpu_metric_calls = [c for c in mock_st.metric.call_args_list if c[0][0] == "CPU"]
        assert len(cpu_metric_calls) >= 1, "CPU metric was not displayed"
        # Verify format is "X%" (no decimals)
        cpu_call = cpu_metric_calls[0]
        assert "%" in cpu_call[0][1], f"CPU value should contain %: {cpu_call}"
    
    @patch('Src.Dashboard.dashboard.get_available_services')
    @patch('Src.Dashboard.dashboard.get_system_resources')
    @patch('Src.Dashboard.dashboard.st')
    def test_displays_ram_metric_with_gb_delta(self, mock_st, mock_resources, mock_services):
        """Verify RAM metric shows percentage with used/total GB as delta."""
        # Arrange
        mock_resources.return_value = {
            'cpu_percent': 50.0,
            'ram_percent': 62.5,
            'ram_used_gb': 10.0,
            'ram_total_gb': 16.0,
            'disk_percent': 70.0,
            'disk_used_gb': 350.0,
            'disk_total_gb': 500.0,
        }
        mock_services.return_value = ['librarian']
        
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols
        
        for col in mock_cols:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=None)
        
        # Act
        from Src.Dashboard.dashboard import render_resource_header
        render_resource_header()
        
        # Assert - RAM should show GB in delta
        ram_metric_calls = [c for c in mock_st.metric.call_args_list if c[0][0] == "RAM"]
        assert len(ram_metric_calls) >= 1, "RAM metric was not displayed"
        ram_call = ram_metric_calls[0]
        # Check delta (third argument or keyword 'delta')
        if len(ram_call[0]) >= 3:
            delta = ram_call[0][2]
        else:
            delta = ram_call[1].get('delta', '')
        assert "GB" in str(delta), f"RAM delta should contain GB: {ram_call}"
    
    @patch('Src.Dashboard.dashboard.get_available_services')
    @patch('Src.Dashboard.dashboard.get_system_resources')
    @patch('Src.Dashboard.dashboard.st')
    def test_displays_disk_metric_with_gb_delta(self, mock_st, mock_resources, mock_services):
        """Verify Disk metric shows percentage with used/total GB as delta."""
        # Arrange
        mock_resources.return_value = {
            'cpu_percent': 50.0,
            'ram_percent': 60.0,
            'ram_used_gb': 8.0,
            'ram_total_gb': 16.0,
            'disk_percent': 75.0,
            'disk_used_gb': 375.0,
            'disk_total_gb': 500.0,
        }
        mock_services.return_value = ['librarian']
        
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols
        
        for col in mock_cols:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=None)
        
        # Act
        from Src.Dashboard.dashboard import render_resource_header
        render_resource_header()
        
        # Assert - Disk should show GB in delta
        disk_metric_calls = [c for c in mock_st.metric.call_args_list if c[0][0] == "Disk"]
        assert len(disk_metric_calls) >= 1, "Disk metric was not displayed"
        disk_call = disk_metric_calls[0]
        # Check delta
        if len(disk_call[0]) >= 3:
            delta = disk_call[0][2]
        else:
            delta = disk_call[1].get('delta', '')
        assert "GB" in str(delta), f"Disk delta should contain GB: {disk_call}"
    
    @patch('Src.Dashboard.dashboard.get_available_services')
    @patch('Src.Dashboard.dashboard.get_system_resources')
    @patch('Src.Dashboard.dashboard.st')
    def test_creates_service_selector(self, mock_st, mock_resources, mock_services):
        """Verify service selector is created with 'All Services' as first option."""
        # Arrange
        mock_resources.return_value = {
            'cpu_percent': 50.0,
            'ram_percent': 60.0,
            'ram_used_gb': 8.0,
            'ram_total_gb': 16.0,
            'disk_percent': 70.0,
            'disk_used_gb': 350.0,
            'disk_total_gb': 500.0,
        }
        mock_services.return_value = ['librarian', 'dashboard', 'factory_postgres']
        
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols
        
        for col in mock_cols:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=None)
        
        mock_st.selectbox.return_value = "All Services"
        
        # Act
        from Src.Dashboard.dashboard import render_resource_header
        result = render_resource_header()
        
        # Assert - Verify selectbox was called
        mock_st.selectbox.assert_called_once()
        call_kwargs = mock_st.selectbox.call_args
        
        # Verify options include "All Services" first
        options = call_kwargs[1].get('options', call_kwargs[0][1] if len(call_kwargs[0]) > 1 else [])
        assert options[0] == "All Services", f"First option should be 'All Services': {options}"
        
        # Verify all services are included
        assert "librarian" in options
        assert "dashboard" in options
    
    @patch('Src.Dashboard.dashboard.get_available_services')
    @patch('Src.Dashboard.dashboard.get_system_resources')
    @patch('Src.Dashboard.dashboard.st')
    def test_returns_selected_service(self, mock_st, mock_resources, mock_services):
        """Verify function returns the selected service from selector."""
        # Arrange
        mock_resources.return_value = {
            'cpu_percent': 50.0,
            'ram_percent': 60.0,
            'ram_used_gb': 8.0,
            'ram_total_gb': 16.0,
            'disk_percent': 70.0,
            'disk_used_gb': 350.0,
            'disk_total_gb': 500.0,
        }
        mock_services.return_value = ['librarian', 'dashboard']
        
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols
        
        for col in mock_cols:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=None)
        
        # Simulate user selecting "librarian"
        mock_st.selectbox.return_value = "librarian"
        
        # Act
        from Src.Dashboard.dashboard import render_resource_header
        result = render_resource_header()
        
        # Assert
        assert result == "librarian"
    
    @patch('Src.Dashboard.dashboard.get_available_services')
    @patch('Src.Dashboard.dashboard.get_system_resources')
    @patch('Src.Dashboard.dashboard.st')
    def test_handles_no_services_available(self, mock_st, mock_resources, mock_services):
        """Verify behavior when no services are available."""
        # Arrange
        mock_resources.return_value = {
            'cpu_percent': 50.0,
            'ram_percent': 60.0,
            'ram_used_gb': 8.0,
            'ram_total_gb': 16.0,
            'disk_percent': 70.0,
            'disk_used_gb': 350.0,
            'disk_total_gb': 500.0,
        }
        mock_services.return_value = []  # No services available
        
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols
        
        for col in mock_cols:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=None)
        
        # Act
        from Src.Dashboard.dashboard import render_resource_header
        result = render_resource_header()
        
        # Assert - Should show warning and return "All Services"
        mock_st.warning.assert_called_once()
        assert result == "All Services"
    
    @patch('Src.Dashboard.dashboard.get_available_services')
    @patch('Src.Dashboard.dashboard.get_system_resources')
    @patch('Src.Dashboard.dashboard.st')
    def test_cpu_format_no_decimals(self, mock_st, mock_resources, mock_services):
        """Verify CPU is formatted with no decimal places."""
        # Arrange
        mock_resources.return_value = {
            'cpu_percent': 45.789,  # Should round to 46%
            'ram_percent': 60.0,
            'ram_used_gb': 8.0,
            'ram_total_gb': 16.0,
            'disk_percent': 70.0,
            'disk_used_gb': 350.0,
            'disk_total_gb': 500.0,
        }
        mock_services.return_value = ['librarian']
        
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols
        
        for col in mock_cols:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=None)
        
        # Act
        from Src.Dashboard.dashboard import render_resource_header
        render_resource_header()
        
        # Assert - CPU should be "46%" not "45.789%"
        cpu_calls = [c for c in mock_st.metric.call_args_list if c[0][0] == "CPU"]
        assert len(cpu_calls) >= 1
        cpu_value = cpu_calls[0][0][1]
        assert cpu_value == "46%", f"Expected '46%', got '{cpu_value}'"
    
    @patch('Src.Dashboard.dashboard.get_available_services')
    @patch('Src.Dashboard.dashboard.get_system_resources')
    @patch('Src.Dashboard.dashboard.st')
    def test_ram_format_one_decimal(self, mock_st, mock_resources, mock_services):
        """Verify RAM GB values are formatted with one decimal place."""
        # Arrange
        mock_resources.return_value = {
            'cpu_percent': 50.0,
            'ram_percent': 62.5,
            'ram_used_gb': 10.123,  # Should show as 10.1
            'ram_total_gb': 16.456,  # Should show as 16.5
            'disk_percent': 70.0,
            'disk_used_gb': 350.0,
            'disk_total_gb': 500.0,
        }
        mock_services.return_value = ['librarian']
        
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols
        
        for col in mock_cols:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=None)
        
        # Act
        from Src.Dashboard.dashboard import render_resource_header
        render_resource_header()
        
        # Assert - RAM delta should have one decimal
        ram_calls = [c for c in mock_st.metric.call_args_list if c[0][0] == "RAM"]
        assert len(ram_calls) >= 1
        ram_call = ram_calls[0]
        if len(ram_call[0]) >= 3:
            delta = ram_call[0][2]
        else:
            delta = ram_call[1].get('delta', '')
        assert "10.1" in str(delta) or "16.5" in str(delta), f"RAM delta should have 1 decimal: {delta}"
    
    @patch('Src.Dashboard.dashboard.get_available_services')
    @patch('Src.Dashboard.dashboard.get_system_resources')
    @patch('Src.Dashboard.dashboard.st')
    def test_disk_format_no_decimals(self, mock_st, mock_resources, mock_services):
        """Verify Disk GB values are formatted with no decimal places."""
        # Arrange
        mock_resources.return_value = {
            'cpu_percent': 50.0,
            'ram_percent': 60.0,
            'ram_used_gb': 8.0,
            'ram_total_gb': 16.0,
            'disk_percent': 75.0,
            'disk_used_gb': 375.789,  # Should show as 376
            'disk_total_gb': 500.123,  # Should show as 500
        }
        mock_services.return_value = ['librarian']
        
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols
        
        for col in mock_cols:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=None)
        
        # Act
        from Src.Dashboard.dashboard import render_resource_header
        render_resource_header()
        
        # Assert - Disk delta should have no decimals
        disk_calls = [c for c in mock_st.metric.call_args_list if c[0][0] == "Disk"]
        assert len(disk_calls) >= 1
        disk_call = disk_calls[0]
        if len(disk_call[0]) >= 3:
            delta = disk_call[0][2]
        else:
            delta = disk_call[1].get('delta', '')
        # Should show whole numbers like "376/500 GB"
        assert "375.789" not in str(delta), f"Disk delta should not have decimals: {delta}"


# =============================================================================
# Test: Edge Cases and Error Scenarios
# =============================================================================
@pytest.mark.unit
class TestResourceMetricsEdgeCases:
    """Test edge cases and error scenarios for resource metrics."""
    
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear Streamlit cache before each test."""
        try:
            from Src.Dashboard.dashboard import get_system_resources
            get_system_resources.clear()
        except (ImportError, AttributeError):
            pass  # Cache may not exist in test context
        yield
    
    @patch('Src.Dashboard.dashboard.psutil')
    def test_very_small_system_memory(self, mock_psutil):
        """Test handling of very small memory values (embedded systems)."""
        # Arrange - Simulate 512MB system
        mock_psutil.cpu_percent.return_value = 80.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=90.0, 
            used=460 * 1024**2,  # 460 MB
            total=512 * 1024**2  # 512 MB
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            percent=50.0, used=4 * 1024**3, total=8 * 1024**3
        )
        
        # Act
        from Src.Dashboard.dashboard import get_system_resources
        result = get_system_resources()
        
        # Assert - Should handle small values correctly
        assert result['ram_used_gb'] == pytest.approx(0.449, rel=0.1)  # ~460MB in GB
        assert result['ram_total_gb'] == pytest.approx(0.5, rel=0.1)  # ~512MB in GB
    
    @patch('Src.Dashboard.dashboard.psutil')
    def test_very_large_disk_space(self, mock_psutil):
        """Test handling of very large disk values (multi-TB drives)."""
        # Arrange - Simulate 10TB drive
        mock_psutil.cpu_percent.return_value = 25.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=50.0, used=16 * 1024**3, total=32 * 1024**3
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            percent=40.0, 
            used=4000 * 1024**3,   # 4 TB used
            total=10000 * 1024**3  # 10 TB total
        )
        
        # Act
        from Src.Dashboard.dashboard import get_system_resources
        result = get_system_resources()
        
        # Assert
        assert result['disk_used_gb'] == pytest.approx(4000.0, rel=0.01)
        assert result['disk_total_gb'] == pytest.approx(10000.0, rel=0.01)
