# Agent Handoff: Dashboard Heartbeat System Status Check

## Context

We are working on the Photo Factory project, specifically fixing dashboard heartbeat display issues. We completed Steps 1-3 of a 4-step plan and need to continue with Step 4.

## Completed Work (Steps 1-3)

**Step 1: ✅ COMPLETED** - Removed garbage code
- Reverted dashboard heartbeat logic from complex ratio-based color coding to simple time-based thresholds
- Deleted test files: `test_dashboard_color_coding.py`, `test_dashboard_heartbeat_display.py`, `docs/TEST_PLAN_COLOR_CODING.md`
- Created new test: `test_heartbeat_display_simple.py` to verify restored simple logic
- **Commit:** `d419f3b` - "refactor: revert to working heartbeat logic and add fraction format"

**Step 2: ✅ COMPLETED** - Added all services to dashboard
- Updated `get_available_services()` to include all Photo Factory and Immich services
- Services now included: librarian, dashboard, factory_postgres, syncthing, service_monitor, immich_server, immich_machine_learning, immich_redis, immich_postgres, homepage

**Step 3: ✅ COMPLETED** - Added fraction format to heartbeat column
- Changed heartbeat display from `{seconds_ago}s ago` to `{seconds_ago}s/{expected_interval}s ago`
- Applied to: All Services table, Librarian metric, Service-specific view
- Example: `🟢 42s/60s ago` (librarian) or `🟡 102s/300s ago` (syncthing)

## Current System Status (Investigation Results)

### Running Containers (10 total)
- ✅ `service_monitor` - Up 57 minutes
- ✅ `librarian` - Up 3 hours (healthy)
- ✅ `dashboard` - Up 11 minutes (healthy)
- ✅ `factory_postgres` - Up 23 hours (healthy)
- ✅ `syncthing` - Up 23 hours (healthy)
- ✅ `immich_server`, `immich_machine_learning`, `immich_redis`, `immich_postgres`, `homepage` - All running

### Database Heartbeat Entries (system_status table)
**Only 3 services have heartbeats in database:**
1. ✅ `factory-db` - Last heartbeat: 3m52s ago (OK)
2. ✅ `librarian` - Last heartbeat: 55s ago (OK, updates every 60s)
3. ✅ `syncthing` - Last heartbeat: 3m53s ago (OK, updated by service_monitor)

**Missing heartbeats:**
- ❌ `dashboard` - **NOT in database** (should be writing heartbeats every 5 minutes)
- ⚠️ `service_monitor` - Expected to NOT have its own heartbeat (per cursor rules)

### Service Monitor Status
- Container is running
- Logs show: Started at 22:13:00, initialized database tables
- **Issue:** No recent activity logs visible (should be updating factory-db and syncthing every 5 minutes)
- Last updates: factory-db (3m52s ago), syncthing (3m53s ago) - suggests service_monitor IS working

### Dashboard Heartbeat Status
- Code shows heartbeat initialization in `dashboard.py`:
  - `_init_heartbeat()` function exists (line 350)
  - Uses `HeartbeatService(service_name="dashboard", interval=300.0)`
  - Should start automatically on dashboard load
- **Issue:** No "Dashboard heartbeat service started" log message found
- **Issue:** No `dashboard` entry in `system_status` table
- **Conclusion:** Dashboard heartbeat is NOT working despite code being present

## Next Steps (Step 4)

**Step 4: Start from KNOWN BROKEN state - acknowledge broken, understand data-to-presentation pipeline, top-down troubleshooting**

### Tasks:
1. **Acknowledge the broken state:**
   - Dashboard heartbeat is not writing to database
   - Only 3 of 4 expected services have heartbeats (missing: dashboard)

2. **Understand the data-to-presentation pipeline:**
   - Trace: `HeartbeatService` → Database (`system_status`) → Dashboard query (`get_service_heartbeat`) → Display formatting
   - Verify each step works independently

3. **Top-down troubleshooting (starting from presentation layer):**
   - Test display logic with mocked values first (verify formatting works)
   - Then verify database queries return correct data
   - Then verify HeartbeatService writes correctly
   - Finally verify dashboard initialization calls heartbeat start

4. **Fix dashboard heartbeat:**
   - Debug why `_init_heartbeat()` is not working
   - Check if Streamlit's execution model prevents background threads
   - Verify database connection in dashboard context
   - Ensure heartbeat service actually starts and writes

## Key Files to Review

- `Src/Dashboard/dashboard.py` - Lines 347-369 (heartbeat initialization)
- `Src/Shared/heartbeat_service.py` - HeartbeatService implementation
- `Src/Shared/service_monitor.py` - Service monitor implementation
- `Stack/App_Data/docker-compose.yml` - Service definitions

## Expected Behavior

**Services that SHOULD have heartbeats:**
- `librarian` - ✅ Working (60s interval)
- `dashboard` - ❌ **BROKEN** (300s interval, not writing)
- `factory-db` - ✅ Working (monitored by service_monitor, 300s interval)
- `syncthing` - ✅ Working (monitored by service_monitor, 300s interval)

**Services that should NOT have heartbeats:**
- `service_monitor` - ✅ Correct (per cursor rules, it monitors others but doesn't report itself)

## Testing Approach

1. First, verify display logic works with mocked data
2. Then verify database queries work
3. Then verify HeartbeatService writes work
4. Finally, fix dashboard initialization

## Git Status

- Last commit: `d419f3b` - "refactor: revert to working heartbeat logic and add fraction format"
- Working directory should be clean (all changes committed)
- Branch: main (or current branch)

## Questions to Answer

1. Why is dashboard heartbeat not initializing?
2. Is Streamlit blocking background threads?
3. Does dashboard have database access?
4. Should we test with mocked values first to verify display logic?

---

**Start by investigating why dashboard heartbeat is not writing to the database, then proceed with Step 4's top-down troubleshooting approach.**




