# Database Monitoring Design Analysis

## Current Architecture

**Current Design: Single Row Per Service (In-Place Updates)**
- `system_status` table: One row per service, updated in place
- Dashboard queries: Fast lookup by `service_name` (primary key)
- Real-time status: Docker API provides container health
- Historical data: **None** (only current state)

## Design Options

### Option 1: Time-Series Table (Historical Only)

**Schema:**
```sql
CREATE TABLE system_status_history (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL,
    current_task TEXT,
    heartbeat_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_service_timestamp ON system_status_history(service_name, heartbeat_timestamp DESC);
```

**Behavior:**
- Each heartbeat = new row
- Auto-rotate: DELETE rows older than 60 days
- Current status: Query `MAX(heartbeat_timestamp)` per service
- Historical queries: Full time-series data available

**Pros:**
- ✅ Complete historical record
- ✅ Can answer "when did service X go down?"
- ✅ Trend analysis (uptime, downtime patterns)
- ✅ Simple schema (one table)

**Cons:**
- ❌ Slower current status lookup (need MAX() query)
- ❌ Table grows (need cleanup job)
- ❌ More complex queries for dashboard

**Query Performance:**
```sql
-- Current status (slower)
SELECT DISTINCT ON (service_name) *
FROM system_status_history
ORDER BY service_name, heartbeat_timestamp DESC;

-- Historical (fast with index)
SELECT * FROM system_status_history
WHERE service_name = 'librarian'
  AND heartbeat_timestamp > NOW() - INTERVAL '7 days'
ORDER BY heartbeat_timestamp DESC;
```

---

### Option 2: Hybrid Design (Current + History)

**Schema:**
```sql
-- Fast lookup table (current state)
CREATE TABLE system_status (
    service_name VARCHAR(64) PRIMARY KEY,
    status VARCHAR(16) NOT NULL,
    current_task TEXT,
    last_heartbeat TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Historical table (time-series)
CREATE TABLE system_status_history (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL,
    current_task TEXT,
    heartbeat_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_service_timestamp ON system_status_history(service_name, heartbeat_timestamp DESC);
```

**Behavior:**
- `system_status`: Updated in place (fast dashboard queries)
- `system_status_history`: New row per heartbeat (historical record)
- Auto-rotate: DELETE from history older than 60 days
- Dashboard: Queries `system_status` for current state

**Pros:**
- ✅ Fast current status lookup (primary key)
- ✅ Complete historical record
- ✅ Best of both worlds
- ✅ Dashboard performance unchanged

**Cons:**
- ❌ Two tables to maintain
- ❌ Need to write to both tables (transaction)
- ❌ Slightly more complex code

**Implementation:**
```python
# In heartbeat service
with get_db_session() as session:
    # Update current status (fast lookup)
    current = session.query(SystemStatus).filter(...).first()
    current.last_heartbeat = datetime.now()
    current.status = self.status
    
    # Insert historical record
    history = SystemStatusHistory(
        service_name=self.service_name,
        status=self.status,
        current_task=self.current_task,
        heartbeat_timestamp=datetime.now()
    )
    session.add(history)
    
    session.commit()
```

---

### Option 3: Keep Current + Add History (Recommended)

**Hybrid with minimal changes:**
- Keep `system_status` as-is (fast current lookups)
- Add `system_status_history` for historical data
- Write to both in same transaction
- Dashboard continues using `system_status` (no changes needed)
- Historical queries use `system_status_history`

**Migration Path:**
1. Add `system_status_history` table
2. Update heartbeat service to write to both
3. Add cleanup job (delete >60 days)
4. Dashboard unchanged (still uses `system_status`)

---

## Recommendation: **Option 3 (Hybrid)**

### Rationale

1. **Performance:** Dashboard needs fast lookups (every 5 seconds). Primary key lookup is O(1).

2. **Historical Value:** 
   - Troubleshooting: "When did librarian stop responding?"
   - Uptime analysis: "What's the uptime % for last 30 days?"
   - Trend detection: "Is service getting slower?"

3. **Docker API Limitation:**
   - Docker only shows current state
   - No historical data if container restarts
   - Database provides persistence across restarts

4. **Minimal Code Changes:**
   - Dashboard queries unchanged
   - Only heartbeat service needs update
   - Backward compatible

### Implementation Plan

1. **Create history table:**
   ```sql
   CREATE TABLE system_status_history (
       id SERIAL PRIMARY KEY,
       service_name VARCHAR(64) NOT NULL,
       status VARCHAR(16) NOT NULL,
       current_task TEXT,
       heartbeat_timestamp TIMESTAMP NOT NULL,
       created_at TIMESTAMP DEFAULT NOW()
   );
   
   CREATE INDEX idx_service_timestamp 
       ON system_status_history(service_name, heartbeat_timestamp DESC);
   ```

2. **Update heartbeat service:**
   - Write to both `system_status` (current) and `system_status_history` (history)
   - Same transaction for consistency

3. **Add cleanup job:**
   - Scheduled task (cron or Python scheduler)
   - Delete rows older than 60 days
   - Run daily

4. **Dashboard:**
   - No changes needed (still uses `system_status`)
   - Future: Add "Historical View" tab using `system_status_history`

### Storage Estimate

**Assumptions:**
- 3 services
- Heartbeat every 60 seconds
- 60 days retention

**Calculation:**
- Rows per day: 3 services × 1440 heartbeats/day = 4,320 rows/day
- 60 days: 259,200 rows
- Row size: ~200 bytes
- Total: ~52 MB (negligible)

**Cleanup Query:**
```sql
DELETE FROM system_status_history
WHERE heartbeat_timestamp < NOW() - INTERVAL '60 days';
```

---

## Alternative: PostgreSQL Partitioning (Advanced)

For very high volume, use table partitioning:
```sql
CREATE TABLE system_status_history (
    id SERIAL,
    service_name VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL,
    current_task TEXT,
    heartbeat_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (id, heartbeat_timestamp)
) PARTITION BY RANGE (heartbeat_timestamp);

-- Monthly partitions
CREATE TABLE system_status_history_2025_01 
    PARTITION OF system_status_history
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

**Benefits:**
- Automatic partition pruning
- Easy to drop old partitions (DROP TABLE)
- Better query performance

**When to use:** If you have 10+ services or <10 second heartbeats.

---

## Decision Matrix

| Criteria | Option 1 (Time-Series) | Option 2 (Hybrid) | Option 3 (Current+History) |
|----------|----------------------|-------------------|---------------------------|
| Current Status Speed | ⚠️ Slower (MAX query) | ✅ Fast (PK lookup) | ✅ Fast (PK lookup) |
| Historical Data | ✅ Complete | ✅ Complete | ✅ Complete |
| Code Complexity | ✅ Simple | ⚠️ Medium | ✅ Low (minimal changes) |
| Dashboard Changes | ❌ Required | ✅ None | ✅ None |
| Storage | ✅ Efficient | ⚠️ 2x writes | ⚠️ 2x writes |
| Query Flexibility | ✅ Excellent | ✅ Excellent | ✅ Excellent |

**Winner: Option 3** - Best balance of performance, functionality, and minimal disruption.

