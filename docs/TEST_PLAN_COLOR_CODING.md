# Test Plan: Dashboard Heartbeat Color Coding Verification

## Problem Statement
The dashboard is showing incorrect colors for heartbeat displays. For example, syncthing at 109s (109/300 = 0.36) should show green but is showing yellow.

## Objective
Verify that the color coding logic correctly assigns colors based on ratio calculations and that the frontend displays the correct colors.

## Test Strategy

### Phase 1: Unit Tests - Color Logic Verification
**Location:** `Src/Dashboard/tests/test_dashboard_color_coding.py`

Test cases to verify the color assignment logic:

1. **Test syncthing at 109s (should be GREEN)**
   - Mock: `last_heartbeat = now - 109 seconds`
   - Expected interval: 300s
   - Expected ratio: 109/300 = 0.363
   - Expected color: 🟢 (green, ratio < 1.0)

2. **Test syncthing at 250s (should be GREEN)**
   - Mock: `last_heartbeat = now - 250 seconds`
   - Expected interval: 300s
   - Expected ratio: 250/300 = 0.833
   - Expected color: 🟢 (green, ratio < 1.0)

3. **Test syncthing at 350s (should be YELLOW)**
   - Mock: `last_heartbeat = now - 350 seconds`
   - Expected interval: 300s
   - Expected ratio: 350/300 = 1.167
   - Expected color: 🟡 (yellow, 1.0 <= ratio < 2.0)

4. **Test syncthing at 600s (should be RED)**
   - Mock: `last_heartbeat = now - 600 seconds`
   - Expected interval: 300s
   - Expected ratio: 600/300 = 2.0
   - Expected color: 🔴 (red, ratio >= 2.0)

5. **Test librarian at 41s (should be GREEN)**
   - Mock: `last_heartbeat = now - 41 seconds`
   - Expected interval: 60s
   - Expected ratio: 41/60 = 0.683
   - Expected color: 🟢 (green, ratio < 1.0)

6. **Test librarian at 90s (should be YELLOW)**
   - Mock: `last_heartbeat = now - 90 seconds`
   - Expected interval: 60s
   - Expected ratio: 90/60 = 1.5
   - Expected color: 🟡 (yellow, 1.0 <= ratio < 2.0)

7. **Test librarian at 120s (should be RED)**
   - Mock: `last_heartbeat = now - 120 seconds`
   - Expected interval: 60s
   - Expected ratio: 120/60 = 2.0
   - Expected color: 🔴 (red, ratio >= 2.0)

8. **Test syncthing with 5-minute (300s) interval - comprehensive coverage**
   - **Test syncthing at 109s (should be GREEN)**
     - Mock: `last_heartbeat = now - 109 seconds`
     - Expected interval: 300s (5 minutes)
     - Expected ratio: 109/300 = 0.363
     - Expected color: 🟢 (green, ratio < 1.0)
     - **This is the reported bug case - should be green but showing yellow**
   
   - **Test syncthing at 250s (should be GREEN)**
     - Mock: `last_heartbeat = now - 250 seconds`
     - Expected interval: 300s
     - Expected ratio: 250/300 = 0.833
     - Expected color: 🟢 (green, ratio < 1.0)
   
   - **Test syncthing at 299s (should be GREEN - just under threshold)**
     - Mock: `last_heartbeat = now - 299 seconds`
     - Expected interval: 300s
     - Expected ratio: 299/300 = 0.997
     - Expected color: 🟢 (green, ratio < 1.0)
   
   - **Test syncthing at 300s (should be YELLOW - exactly at interval)**
     - Mock: `last_heartbeat = now - 300 seconds`
     - Expected interval: 300s
     - Expected ratio: 300/300 = 1.0
     - Expected color: 🟡 (yellow, 1.0 <= ratio < 2.0)
   
   - **Test syncthing at 350s (should be YELLOW)**
     - Mock: `last_heartbeat = now - 350 seconds`
     - Expected interval: 300s
     - Expected ratio: 350/300 = 1.167
     - Expected color: 🟡 (yellow, 1.0 <= ratio < 2.0)
   
   - **Test syncthing at 450s (should be YELLOW)**
     - Mock: `last_heartbeat = now - 450 seconds`
     - Expected interval: 300s
     - Expected ratio: 450/300 = 1.5
     - Expected color: 🟡 (yellow, 1.0 <= ratio < 2.0)
   
   - **Test syncthing at 599s (should be YELLOW - just under 2x threshold)**
     - Mock: `last_heartbeat = now - 599 seconds`
     - Expected interval: 300s
     - Expected ratio: 599/300 = 1.997
     - Expected color: 🟡 (yellow, 1.0 <= ratio < 2.0)
   
   - **Test syncthing at 600s (should be RED - exactly 2x interval)**
     - Mock: `last_heartbeat = now - 600 seconds`
     - Expected interval: 300s
     - Expected ratio: 600/300 = 2.0
     - Expected color: 🔴 (red, ratio >= 2.0)
   
   - **Test syncthing at 900s (should be RED - 3x interval)**
     - Mock: `last_heartbeat = now - 900 seconds`
     - Expected interval: 300s
     - Expected ratio: 900/300 = 3.0
     - Expected color: 🔴 (red, ratio >= 2.0)

### Phase 2: Integration Tests - Full Display Logic
**Location:** `Src/Dashboard/tests/test_dashboard_color_coding.py`

Test the complete flow from `get_all_services_status()` to the status_data table:

1. **Test status_data table includes correct color**
   - Mock `get_all_services_status()` to return services with specific heartbeat times
   - Call the main display logic that creates `status_data`
   - Verify the `heartbeat_info` field contains the correct color emoji
   - Verify the format is `"{color} {seconds_ago}/{expected_interval}s ago"`

2. **Test service name mapping for syncthing**
   - Verify that container name "syncthing" correctly maps to service name "syncthing"
   - Verify that the expected_interval is correctly retrieved (300s)
   - Verify the ratio calculation uses the correct interval

3. **Test edge cases**
   - Test at exactly 1.0 ratio (should be yellow)
   - Test at exactly 2.0 ratio (should be red)
   - Test with missing service_name (should use default 300s)
   - Test with None heartbeat (should show "N/A")

### Phase 3: End-to-End Test - Mock Database Values
**Location:** `Src/Dashboard/tests/test_dashboard_color_coding.py`

Mock the database to return specific heartbeat values and verify the full pipeline:

1. **Mock database with syncthing at 109s**
   - Mock `get_service_heartbeat("syncthing")` to return `last_heartbeat = now - 109s`
   - Verify `get_all_services_status()` returns correct heartbeat data
   - Verify the display logic calculates ratio = 109/300 = 0.363
   - Verify the color assigned is 🟢

2. **Mock database with syncthing at 350s**
   - Mock `get_service_heartbeat("syncthing")` to return `last_heartbeat = now - 350s`
   - Verify ratio = 350/300 = 1.167
   - Verify color is 🟡

3. **Mock database with librarian at 90s**
   - Mock `get_service_heartbeat("librarian")` to return `last_heartbeat = now - 90s`
   - Verify ratio = 90/60 = 1.5
   - Verify color is 🟡

## Implementation Details

### Test Structure
```python
class TestColorCodingLogic:
    """Test the color coding logic directly."""
    
    def test_syncthing_109s_should_be_green(self):
        # Test ratio calculation and color assignment
        pass
    
    def test_syncthing_350s_should_be_yellow(self):
        pass
    
    # ... more test cases

class TestColorCodingDisplay:
    """Test the full display pipeline."""
    
    def test_status_data_includes_correct_color(self):
        # Test the status_data table creation
        pass
    
    def test_service_name_mapping_syncthing(self):
        # Test service name resolution
        pass

class TestColorCodingEndToEnd:
    """Test with mocked database."""
    
    def test_syncthing_109s_from_database(self):
        # Mock database, verify full pipeline
        pass
```

### Key Functions to Test
1. **Color calculation logic** (lines 514-524 in dashboard.py):
   - `time_since = datetime.now() - svc["heartbeat"]["last_heartbeat"]`
   - `seconds_ago = int(time_since.total_seconds())`
   - `ratio = seconds_ago / expected_interval`
   - Color assignment based on ratio

2. **Service name mapping** (lines 500-512):
   - Verify `service_name_for_interval` is correctly derived
   - Verify `expected_interval` is correctly retrieved from `service_intervals` dict

3. **Status data creation** (lines 476-526):
   - Verify `heartbeat_info` string format
   - Verify color emoji is included

## Expected Outcomes

1. **All unit tests pass** - Color logic works correctly
2. **Integration tests pass** - Full display pipeline works
3. **End-to-end tests pass** - Database mocking works correctly
4. **Identify the bug** - If tests fail, we'll know exactly where the issue is

## Success Criteria

### Syncthing (5-minute / 300s interval):
- ✅ Syncthing at 109s shows 🟢 (green) - **CRITICAL: This is the reported bug**
- ✅ Syncthing at 250s shows 🟢 (green)
- ✅ Syncthing at 299s shows 🟢 (green) - edge case: just under threshold
- ✅ Syncthing at 300s shows 🟡 (yellow) - edge case: exactly at interval
- ✅ Syncthing at 350s shows 🟡 (yellow)
- ✅ Syncthing at 450s shows 🟡 (yellow)
- ✅ Syncthing at 599s shows 🟡 (yellow) - edge case: just under 2x threshold
- ✅ Syncthing at 600s shows 🔴 (red) - edge case: exactly 2x interval
- ✅ Syncthing at 900s shows 🔴 (red)

### Librarian (1-minute / 60s interval):
- ✅ Librarian at 41s shows 🟢 (green)
- ✅ Librarian at 90s shows 🟡 (yellow)
- ✅ Librarian at 120s shows 🔴 (red)

### General:
- ✅ All edge cases handled correctly
- ✅ Service name mapping works correctly
- ✅ Ratio calculations are accurate

## Next Steps After Tests

1. If tests pass but UI shows wrong colors → Frontend rendering issue
2. If tests fail → Fix the logic in dashboard.py
3. If service name mapping fails → Fix the mapping logic
4. If ratio calculation fails → Fix the calculation

## Files to Create/Modify

1. **Create:** `Src/Dashboard/tests/test_dashboard_color_coding.py`
   - Comprehensive test suite for color coding

2. **Modify:** `Src/Dashboard/dashboard.py` (if bugs found)
   - Fix color calculation logic
   - Fix service name mapping
   - Fix ratio calculation

