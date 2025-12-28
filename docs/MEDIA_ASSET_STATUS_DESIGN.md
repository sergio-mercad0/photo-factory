# Media Asset Status Tracking - Design Proposal

## Current State

Currently, `media_assets` table tracks files that have been:
- ✅ Detected in Photos_Inbox
- ✅ Moved to Storage/Originals
- ✅ Metadata extracted (date, location)
- ✅ Recorded in database

**Once a record exists in `media_assets`, the file is considered "processed" by Librarian.**

## Future Workflow Considerations

Potential future services/processes:
1. **Librarian** (current) - Ingest, organize, extract metadata
2. **Reverse Geocoding** - Convert lat/lon to human-readable locations
3. **Thumbnail Generation** - Create thumbnails for gallery
4. **Face Detection** - Identify people in photos
5. **Curation** - Manual review/flagging
6. **Backup** - Sync to cloud/backup location

## Design Options

### Option 1: Single Status Column (Enum)

**Schema:**
```sql
status VARCHAR(16) DEFAULT 'ingested'
-- Values: 'ingested', 'geocoded', 'thumbnailed', 'curated', 'backed_up', 'error'
```

**Pros:**
- ✅ Simple, one place to check
- ✅ Easy to query current state
- ✅ Enforces single state at a time
- ✅ Can add states without schema changes (if using VARCHAR)

**Cons:**
- ❌ Can't track multiple states simultaneously
- ❌ Hard to know which service completed what
- ❌ No history of state changes
- ❌ Enum values need to be coordinated across services

**Example:**
```sql
SELECT * FROM media_assets WHERE status = 'ingested';
SELECT * FROM media_assets WHERE status IN ('ingested', 'geocoded');
```

---

### Option 2: Individual Boolean Columns

**Schema:**
```sql
is_ingested BOOLEAN DEFAULT TRUE
is_geocoded BOOLEAN DEFAULT FALSE
is_thumbnailed BOOLEAN DEFAULT FALSE
is_curated BOOLEAN DEFAULT FALSE
is_backed_up BOOLEAN DEFAULT FALSE
has_errors BOOLEAN DEFAULT FALSE
```

**Pros:**
- ✅ Clear, explicit states
- ✅ Can track multiple states simultaneously
- ✅ Easy to query: `WHERE is_geocoded = FALSE`
- ✅ No coordination needed (each service manages its own column)

**Cons:**
- ❌ More columns as services are added
- ❌ Can't track "when" each state was achieved (without timestamps)
- ❌ Harder to enforce mutual exclusivity if needed

**Example:**
```sql
SELECT * FROM media_assets WHERE is_ingested = TRUE AND is_geocoded = FALSE;
SELECT COUNT(*) FROM media_assets WHERE is_backed_up = FALSE;
```

---

### Option 3: Per-Service Status Columns

**Schema:**
```sql
librarian_status VARCHAR(16) DEFAULT 'completed'  -- 'pending', 'processing', 'completed', 'error'
geocoding_status VARCHAR(16) DEFAULT NULL          -- 'pending', 'processing', 'completed', 'error', 'skipped'
thumbnail_status VARCHAR(16) DEFAULT NULL
curation_status VARCHAR(16) DEFAULT NULL
backup_status VARCHAR(16) DEFAULT NULL
```

**Pros:**
- ✅ Very clear which service did what
- ✅ Can track processing state (pending/processing/completed)
- ✅ Can track errors per service
- ✅ Can skip services (NULL = not applicable)

**Cons:**
- ❌ Many columns (one per service)
- ❌ Schema changes needed for each new service
- ❌ More complex queries

**Example:**
```sql
SELECT * FROM media_assets WHERE librarian_status = 'completed' AND geocoding_status IS NULL;
SELECT * FROM media_assets WHERE backup_status = 'error';
```

---

### Option 4: Status History Table (Time-Series)

**Schema:**
```sql
-- media_assets table (unchanged)
-- New table: media_asset_status_history
CREATE TABLE media_asset_status_history (
    id SERIAL PRIMARY KEY,
    asset_id UUID REFERENCES media_assets(id),
    service_name VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL,  -- 'pending', 'processing', 'completed', 'error'
    status_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Pros:**
- ✅ Complete history of all state changes
- ✅ Can track "when" each state was achieved
- ✅ Can track errors and messages
- ✅ No schema changes to media_assets for new services
- ✅ Most flexible

**Cons:**
- ❌ More complex queries (need joins)
- ❌ Slower current status lookup
- ❌ More storage

**Example:**
```sql
-- Current status (latest per service)
SELECT DISTINCT ON (asset_id, service_name) *
FROM media_asset_status_history
ORDER BY asset_id, service_name, created_at DESC;

-- Assets needing geocoding
SELECT ma.* FROM media_assets ma
LEFT JOIN (
    SELECT DISTINCT ON (asset_id) asset_id, status
    FROM media_asset_status_history
    WHERE service_name = 'geocoding'
    ORDER BY asset_id, created_at DESC
) g ON ma.id = g.asset_id
WHERE g.status IS NULL OR g.status != 'completed';
```

---

### Option 5: Hybrid (Current Status + History)

**Schema:**
```sql
-- media_assets table: Add current status columns
librarian_status VARCHAR(16) DEFAULT 'completed'
geocoding_status VARCHAR(16) DEFAULT NULL
-- ... other services

-- New table: media_asset_status_history (for history)
CREATE TABLE media_asset_status_history (
    id SERIAL PRIMARY KEY,
    asset_id UUID REFERENCES media_assets(id),
    service_name VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL,
    status_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Pros:**
- ✅ Fast current status lookup (columns in media_assets)
- ✅ Complete history (separate table)
- ✅ Best of both worlds

**Cons:**
- ❌ Most complex (two places to update)
- ❌ Need to maintain consistency

---

## Recommendation: **Option 2 (Boolean Columns) + Option 4 (History Table)**

### Rationale

1. **Boolean columns for current state:**
   - Simple, clear, fast queries
   - Each service manages its own column
   - Easy to see "what's done" at a glance
   - Can add timestamps later if needed

2. **History table for tracking:**
   - Complete audit trail
   - Track when each state was achieved
   - Track errors and messages
   - Useful for troubleshooting

3. **Implementation:**
   - Start with boolean columns (simple, immediate value)
   - Add history table later if needed (when troubleshooting becomes important)
   - Or implement both from the start if you want full observability

### Proposed Schema

```sql
-- Add to media_assets table:
ALTER TABLE media_assets ADD COLUMN is_ingested BOOLEAN DEFAULT TRUE;
ALTER TABLE media_assets ADD COLUMN is_geocoded BOOLEAN DEFAULT FALSE;
ALTER TABLE media_assets ADD COLUMN is_thumbnailed BOOLEAN DEFAULT FALSE;
ALTER TABLE media_assets ADD COLUMN is_curated BOOLEAN DEFAULT FALSE;
ALTER TABLE media_assets ADD COLUMN is_backed_up BOOLEAN DEFAULT FALSE;
ALTER TABLE media_assets ADD COLUMN has_errors BOOLEAN DEFAULT FALSE;
ALTER TABLE media_assets ADD COLUMN error_message TEXT;

-- Optional: Add timestamps for when each state was achieved
ALTER TABLE media_assets ADD COLUMN geocoded_at TIMESTAMP;
ALTER TABLE media_assets ADD COLUMN thumbnailed_at TIMESTAMP;
ALTER TABLE media_assets ADD COLUMN curated_at TIMESTAMP;
ALTER TABLE media_assets ADD COLUMN backed_up_at TIMESTAMP;

-- Optional: History table (for full audit trail)
CREATE TABLE media_asset_status_history (
    id SERIAL PRIMARY KEY,
    asset_id UUID REFERENCES media_assets(id),
    service_name VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL,  -- 'pending', 'processing', 'completed', 'error', 'skipped'
    status_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_asset_status_history_asset_id ON media_asset_status_history(asset_id);
CREATE INDEX idx_asset_status_history_service ON media_asset_status_history(service_name, created_at);
```

### Migration Strategy

1. **Phase 1:** Add boolean columns (backward compatible)
   - Existing records: `is_ingested = TRUE` (already processed)
   - New records: Set appropriate flags as services complete

2. **Phase 2:** Update Librarian to set `is_ingested = TRUE` on insert

3. **Phase 3:** Add history table (optional, for observability)

4. **Phase 4:** Future services update their respective columns

### Example Queries

**Find files needing geocoding:**
```sql
SELECT * FROM media_assets 
WHERE is_ingested = TRUE 
  AND is_geocoded = FALSE 
  AND location IS NOT NULL;
```

**Find files with errors:**
```sql
SELECT * FROM media_assets WHERE has_errors = TRUE;
```

**Find files ready for backup:**
```sql
SELECT * FROM media_assets 
WHERE is_ingested = TRUE 
  AND is_geocoded = TRUE 
  AND is_backed_up = FALSE;
```

**View status history:**
```sql
SELECT * FROM media_asset_status_history 
WHERE asset_id = '...' 
ORDER BY created_at DESC;
```

---

## Decision Matrix

| Criteria | Option 1 (Enum) | Option 2 (Boolean) | Option 3 (Per-Service) | Option 4 (History) | Option 5 (Hybrid) |
|----------|----------------|-------------------|----------------------|-------------------|------------------|
| Simplicity | ✅ Simple | ✅ Simple | ⚠️ Medium | ❌ Complex | ❌ Complex |
| Query Speed | ✅ Fast | ✅ Fast | ✅ Fast | ❌ Slower | ✅ Fast |
| Multiple States | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| History Tracking | ❌ No | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| Service Isolation | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Schema Changes | ⚠️ Medium | ⚠️ Medium | ❌ Many | ✅ None | ⚠️ Medium |

**Winner: Option 2 (Boolean Columns)** - Best balance of simplicity, performance, and flexibility.

