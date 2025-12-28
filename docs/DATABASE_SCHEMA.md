# Database Schema - Canonical Definition

**⚠️ CRITICAL: This file is the SOURCE OF TRUTH for all database table and column definitions.**

All code, migrations, queries, and documentation MUST reference this file for column meanings, data types, constraints, and usage guidelines. Any changes to the database schema MUST be reflected here first, then implemented in `Src/Shared/models.py`.

---

## Table: `media_assets`

**Purpose:** Media asset ledger - tracks all processed files. This is the source of truth for what files have been ingested.

### Columns

#### Primary Key
- **`id`** (UUID, PRIMARY KEY)
  - **Type:** `UUID(as_uuid=True)`
  - **Nullable:** No
  - **Default:** `uuid.uuid4()`
  - **Purpose:** Unique identifier for each media asset record
  - **Usage:** Never manually set; always auto-generated

#### File Identification
- **`file_hash`** (String(64), UNIQUE, INDEXED)
  - **Type:** `String(64)`
  - **Nullable:** No
  - **Unique:** Yes
  - **Indexed:** Yes
  - **Purpose:** SHA256 hash of file content (hexadecimal string)
  - **Usage:** Used for duplicate detection. Must be exactly 64 characters (SHA256 hex = 32 bytes × 2)
  - **Example:** `"a1b2c3d4e5f6..."` (64 chars)
  - **Constraint:** Must be unique across all records

- **`original_name`** (String(512))
  - **Type:** `String(512)`
  - **Nullable:** No
  - **Purpose:** Original filename as received in `Photos_Inbox`
  - **Usage:** Preserved exactly as received (including extension)
  - **Example:** `"IMG_20231225_123456.jpg"`

- **`original_path`** (Text)
  - **Type:** `Text`
  - **Nullable:** No
  - **Purpose:** Full absolute path where file was located in `Photos_Inbox`
  - **Usage:** Historical record of source location
  - **Example:** `"/app/Photos_Inbox/IMG_20231225_123456.jpg"`

- **`final_path`** (Text)
  - **Type:** `Text`
  - **Nullable:** No
  - **Purpose:** Full absolute path where file is stored in `Storage/Originals`
  - **Usage:** Current location of organized file
  - **Format:** `Storage/Originals/{YYYY}/{YYYY-MM-DD}/{filename}`
  - **Example:** `"/app/Storage/Originals/2023/2023-12-25/IMG_20231225_123456.jpg"`

#### File Metadata
- **`size_bytes`** (BigInteger)
  - **Type:** `BigInteger`
  - **Nullable:** No
  - **Purpose:** File size in bytes
  - **Usage:** For storage tracking and duplicate verification
  - **Example:** `5242880` (5 MB)

- **`captured_at`** (TIMESTAMP)
  - **Type:** `TIMESTAMP`
  - **Nullable:** Yes
  - **Indexed:** Yes (`idx_media_assets_captured_at`)
  - **Purpose:** True capture date/time extracted from EXIF metadata
  - **Usage:** Primary date for organizing files into `{YYYY}/{YYYY-MM-DD}/` folders
  - **Fallback:** If EXIF extraction fails, uses file modification time
  - **Format:** `YYYY-MM-DD HH:MM:SS` (timezone-aware if available)
  - **Example:** `2023-12-25 12:34:56`

- **`ingested_at`** (TIMESTAMP)
  - **Type:** `TIMESTAMP`
  - **Nullable:** No
  - **Default:** `func.now()` (server-side)
  - **Indexed:** Yes (`idx_media_assets_ingested_at`)
  - **Purpose:** Timestamp when Librarian service processed and moved the file
  - **Usage:** Tracks when file entered the system
  - **Format:** `YYYY-MM-DD HH:MM:SS`
  - **Note:** Automatically set by database on INSERT

#### Location Data
- **`location`** (JSON)
  - **Type:** `JSON` (PostgreSQL JSONB)
  - **Nullable:** Yes
  - **Purpose:** GPS coordinates extracted from EXIF metadata (immutable source of truth)
  - **Format:** `{"lat": float, "lon": float}`
  - **Example:** `{"lat": 35.6762, "lon": 139.6503}` (Tokyo)
  - **Usage:** 
    - Store only raw coordinates during ingest
    - Reverse geocoding (city, country, etc.) is done in a separate process
    - This field is immutable - never update after initial ingest
  - **Constraints:** 
    - `lat` must be between -90 and 90
    - `lon` must be between -180 and 180

#### Processing Status Flags
- **`is_ingested`** (Boolean)
  - **Type:** `Boolean`
  - **Nullable:** No
  - **Default:** `True`
  - **Purpose:** Indicates Librarian service has completed processing
  - **Usage:** Always `True` if record exists (record is only created after successful ingest)
  - **Note:** This is the base status - all other flags depend on this being `True`

- **`is_geocoded`** (Boolean)
  - **Type:** `Boolean`
  - **Nullable:** No
  - **Default:** `False`
  - **Indexed:** Yes (`idx_media_assets_is_geocoded`)
  - **Purpose:** Indicates reverse geocoding has been completed
  - **Usage:** Set to `True` when geocoding service enriches location data
  - **Query:** `WHERE is_ingested = TRUE AND is_geocoded = FALSE AND location IS NOT NULL`

- **`is_thumbnailed`** (Boolean)
  - **Type:** `Boolean`
  - **Nullable:** No
  - **Default:** `False`
  - **Purpose:** Indicates thumbnails have been generated
  - **Usage:** Set to `True` when thumbnail service completes

- **`is_curated`** (Boolean)
  - **Type:** `Boolean`
  - **Nullable:** No
  - **Default:** `False`
  - **Purpose:** Indicates manual curation has been completed
  - **Usage:** Set to `True` when human curator marks as complete

- **`is_backed_up`** (Boolean)
  - **Type:** `Boolean`
  - **Nullable:** No
  - **Default:** `False`
  - **Indexed:** Yes (`idx_media_assets_is_backed_up`)
  - **Purpose:** Indicates backup to external storage has been completed
  - **Usage:** Set to `True` when backup service confirms successful backup
  - **Query:** `WHERE is_ingested = TRUE AND is_backed_up = FALSE`

- **`has_errors`** (Boolean)
  - **Type:** `Boolean`
  - **Nullable:** No
  - **Default:** `False`
  - **Indexed:** Yes (`idx_media_assets_has_errors`)
  - **Purpose:** Indicates any errors occurred during processing
  - **Usage:** Set to `True` if any service encounters an error
  - **Query:** `WHERE has_errors = TRUE` to find problematic files

- **`error_message`** (Text)
  - **Type:** `Text`
  - **Nullable:** Yes
  - **Purpose:** Human-readable error details when `has_errors = True`
  - **Usage:** Store error description, stack trace, or error code
  - **Format:** Free-form text
  - **Example:** `"EXIF extraction failed: Invalid JPEG structure"`

#### Status Timestamps
- **`geocoded_at`** (TIMESTAMP)
  - **Type:** `TIMESTAMP`
  - **Nullable:** Yes
  - **Purpose:** Timestamp when geocoding was completed
  - **Usage:** Set when `is_geocoded` changes from `False` to `True`
  - **Format:** `YYYY-MM-DD HH:MM:SS`

- **`thumbnailed_at`** (TIMESTAMP)
  - **Type:** `TIMESTAMP`
  - **Nullable:** Yes
  - **Purpose:** Timestamp when thumbnails were generated
  - **Usage:** Set when `is_thumbnailed` changes from `False` to `True`

- **`curated_at`** (TIMESTAMP)
  - **Type:** `TIMESTAMP`
  - **Nullable:** Yes
  - **Purpose:** Timestamp when curation was completed
  - **Usage:** Set when `is_curated` changes from `False` to `True`

- **`backed_up_at`** (TIMESTAMP)
  - **Type:** `TIMESTAMP`
  - **Nullable:** Yes
  - **Purpose:** Timestamp when backup was completed
  - **Usage:** Set when `is_backed_up` changes from `False` to `True`

#### System Timestamps
- **`created_at`** (TIMESTAMP)
  - **Type:** `TIMESTAMP`
  - **Nullable:** No
  - **Default:** `func.now()` (server-side)
  - **Purpose:** Record creation timestamp
  - **Usage:** Tracks when database record was created
  - **Note:** Automatically set by database on INSERT

---

## Table: `system_status`

**Purpose:** Fast-lookup table for current service heartbeat and status. Updated in-place for efficient dashboard queries.

### Columns

#### Primary Key
- **`service_name`** (String(64), PRIMARY KEY)
  - **Type:** `String(64)`
  - **Nullable:** No
  - **Primary Key:** Yes
  - **Purpose:** Unique identifier for each service
  - **Values:** 
    - `"librarian"` - Photo ingestion service
    - `"dashboard"` - Monitoring dashboard
    - `"factory-db"` - Photo Factory database
    - `"syncthing"` - File synchronization service
  - **Usage:** Used as lookup key for current service status

#### Status Information
- **`last_heartbeat`** (TIMESTAMP)
  - **Type:** `TIMESTAMP`
  - **Nullable:** No
  - **Default:** `func.now()` (server-side)
  - **On Update:** `func.now()` (auto-updated)
  - **Purpose:** Timestamp of most recent heartbeat from service
  - **Usage:** 
    - Calculate time since last heartbeat: `NOW() - last_heartbeat`
    - Dashboard displays: Green (≤60s), Yellow (60-180s), Red (>180s)
  - **Format:** `YYYY-MM-DD HH:MM:SS`
  - **Update Frequency:** Every 5-10 minutes (configurable per service)

- **`status`** (String(16))
  - **Type:** `String(16)`
  - **Nullable:** No
  - **Default:** `"OK"`
  - **Purpose:** Current service status
  - **Valid Values:**
    - `"OK"` - Service is healthy and functioning
    - `"ERROR"` - Service encountered an error
    - `"WARNING"` - Service is degraded but functional
  - **Usage:** Dashboard displays status indicator based on this value

- **`current_task`** (Text)
  - **Type:** `Text`
  - **Nullable:** Yes
  - **Purpose:** Human-readable description of what the service is currently doing
  - **Usage:** Optional field for service activity description
  - **Examples:**
    - `"Processing files in Photos_Inbox"`
    - `"Database check"`
    - `"Syncthing check"`
    - `"Dashboard running"`
  - **Note:** Can be `NULL` if service has no specific task to report

#### System Timestamps
- **`updated_at`** (TIMESTAMP)
  - **Type:** `TIMESTAMP`
  - **Nullable:** No
  - **Default:** `func.now()` (server-side)
  - **On Update:** `func.now()` (auto-updated)
  - **Purpose:** Timestamp when record was last updated
  - **Usage:** Tracks when status information changed
  - **Note:** Automatically updated by database on UPDATE

---

## Table: `system_status_history`

**Purpose:** Historical time-series record of service heartbeats. Each heartbeat creates a new row for complete historical data.

### Columns

#### Primary Key
- **`id`** (Integer, PRIMARY KEY, AUTO_INCREMENT)
  - **Type:** `Integer`
  - **Nullable:** No
  - **Primary Key:** Yes
  - **Auto Increment:** Yes
  - **Purpose:** Unique identifier for each historical record
  - **Usage:** Never manually set; always auto-generated

#### Service Identification
- **`service_name`** (String(64), INDEXED)
  - **Type:** `String(64)`
  - **Nullable:** No
  - **Indexed:** Yes (part of composite index)
  - **Purpose:** Service identifier (same values as `system_status.service_name`)
  - **Usage:** Filter historical records by service
  - **Query:** `WHERE service_name = 'librarian'`

#### Status Information (Snapshot)
- **`status`** (String(16))
  - **Type:** `String(16)`
  - **Nullable:** No
  - **Purpose:** Service status at the time of this heartbeat
  - **Valid Values:** Same as `system_status.status` (`"OK"`, `"ERROR"`, `"WARNING"`)
  - **Usage:** Historical record of status at specific point in time

- **`current_task`** (Text)
  - **Type:** `Text`
  - **Nullable:** Yes
  - **Purpose:** Task description at the time of this heartbeat
  - **Usage:** Historical record of what service was doing

#### Timestamps
- **`heartbeat_timestamp`** (TIMESTAMP, INDEXED)
  - **Type:** `TIMESTAMP`
  - **Nullable:** No
  - **Indexed:** Yes (part of composite index)
  - **Purpose:** Timestamp when this heartbeat occurred
  - **Usage:** 
    - Time-series analysis
    - Uptime calculations
    - Trend detection
  - **Format:** `YYYY-MM-DD HH:MM:SS`
  - **Query:** `WHERE heartbeat_timestamp >= NOW() - INTERVAL '24 hours'`

- **`created_at`** (TIMESTAMP)
  - **Type:** `TIMESTAMP`
  - **Nullable:** No
  - **Default:** `func.now()` (server-side)
  - **Purpose:** Record creation timestamp
  - **Usage:** Tracks when database record was created
  - **Note:** Usually same as `heartbeat_timestamp`, but separate for audit purposes

### Indexes
- **`idx_system_status_history_service_timestamp`** (Composite)
  - **Columns:** `service_name`, `heartbeat_timestamp`
  - **Purpose:** Efficient queries filtering by service and time range
  - **Query Example:** `WHERE service_name = 'librarian' AND heartbeat_timestamp >= '2023-12-01'`

### Data Retention
- **Retention Period:** 60 days (configurable)
- **Cleanup:** Run `Src.Shared.cleanup_script` periodically
- **Rationale:** Prevents unbounded table growth while maintaining sufficient history for troubleshooting

---

## Usage Guidelines

### Column Naming Conventions
- Use `snake_case` for all column names
- Boolean flags: Prefix with `is_` (e.g., `is_ingested`, `is_geocoded`)
- Timestamps: Suffix with `_at` (e.g., `ingested_at`, `geocoded_at`)
- Status fields: Use descriptive names (e.g., `status`, `current_task`)

### Data Type Guidelines
- **UUIDs:** Use PostgreSQL `UUID` type for primary keys
- **Timestamps:** Use `TIMESTAMP` (timezone-aware if needed)
- **Text:** Use `Text` for variable-length strings, `String(n)` for fixed-length
- **JSON:** Use PostgreSQL `JSON` or `JSONB` for structured data
- **Booleans:** Use `Boolean` type (not integers)

### Constraints
- **Primary Keys:** Always use UUID or auto-incrementing integer
- **Foreign Keys:** Not currently used (filesystem is source of truth)
- **Unique Constraints:** Only on `file_hash` (content deduplication)
- **Indexes:** Add for frequently queried columns (see index definitions above)

### Migration Guidelines
1. **Schema Changes:** Update this file FIRST, then `Src/Shared/models.py`
2. **New Columns:** Document purpose, type, constraints, and usage
3. **Column Removal:** Mark as deprecated first, remove in next major version
4. **Data Migrations:** Create migration script in `Src/Shared/migrate_*.py`

### Query Patterns
- **Find duplicates:** `WHERE file_hash = ?`
- **Find pending geocoding:** `WHERE is_ingested = TRUE AND is_geocoded = FALSE AND location IS NOT NULL`
- **Find pending backup:** `WHERE is_ingested = TRUE AND is_backed_up = FALSE`
- **Find errors:** `WHERE has_errors = TRUE`
- **Recent assets:** `ORDER BY ingested_at DESC LIMIT 10`
- **Service heartbeat:** `WHERE service_name = ?` in `system_status`
- **Service history:** `WHERE service_name = ? AND heartbeat_timestamp >= ?` in `system_status_history`

---

## Version History

- **2024-12-28:** Initial schema documentation
- **2024-12-28:** Added status tracking columns (`is_*`, `*_at` timestamps)
- **2024-12-28:** Added `system_status` and `system_status_history` tables

