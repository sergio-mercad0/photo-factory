# Librarian Service - Context & Architecture

**⚠️ CRITICAL: This file is the SOURCE OF TRUTH for the Librarian module architecture, decisions, and implementation status.**

**Last Updated:** 2025-12-28  
**Purpose:** Handoff document for agents taking over Librarian development

---

## 1. Architecture Decisions (The "Why")

### Database Choice: PostgreSQL (Not SQLite)

**Decision:** Use PostgreSQL as the primary database.

**Rationale:**
- **JSONB Support:** Native JSONB type for flexible location data storage
- **Concurrency:** Better handling of concurrent writes from multiple services
- **Scalability:** Can handle large media asset catalogs efficiently
- **Production-Ready:** Industry-standard for production applications
- **Docker Integration:** Runs as containerized service (`factory_postgres`)

**Implementation Status:** ✅ **IMPLEMENTED**
- Database service: `factory-db` (PostgreSQL 15-alpine) in `docker-compose.yml`
- Connection: SQLAlchemy with `psycopg2-binary`
- Schema: Defined in `Src/Shared/models.py` and `docs/DATABASE_SCHEMA.md`

---

### Storage Strategy: "The Show Room" (Strategy A)

**Decision:** Use `Storage/Originals` as read-only source of truth, separate from `Storage/Derivatives` (future gallery).

**Rationale:**
- **Immutability:** Originals are never modified after ingest
- **Separation of Concerns:** Originals (source) vs Derivatives (processed/gallery)
- **Backup Strategy:** Only need to backup Originals (derivatives can be regenerated)
- **File Organization:** `Storage/Originals/{YYYY}/{YYYY-MM-DD}/{filename}`

**Implementation Status:** ✅ **IMPLEMENTED**
- Librarian writes to `Storage/Originals/{YYYY}/{YYYY-MM-DD}/`
- Files are moved (not copied) from `Photos_Inbox` to `Storage/Originals`
- `Storage/Derivatives` is planned but not yet implemented

**Path Resolution:**
- Uses `pathlib.Path` with relative paths from project root
- Never uses absolute paths (per `.cursorrules` portability requirement)
- Base path: `Storage/Originals` (resolved relative to project root)

---

### Metadata Strategy: JSONB for Location, Float for Coordinates

**Decision:** Store GPS coordinates as JSONB `{"lat": float, "lon": float}` in `location` column.

**Rationale:**
- **Flexibility:** JSONB allows future expansion (altitude, accuracy, etc.) without schema changes
- **PostgreSQL Native:** JSONB is optimized for querying and indexing
- **Immutable Source:** Raw GPS coordinates are never modified after ingest
- **Reverse Geocoding:** Human-readable labels (city, country) stored separately (future work)

**Implementation Status:** ✅ **IMPLEMENTED**
- Schema: `location = Column(JSON, nullable=True)` in `MediaAsset` model
- Format: `{"lat": 35.6762, "lon": 139.6503}` (Tokyo example)
- Constraints: `lat` between -90 and 90, `lon` between -180 and 180
- Extraction: From EXIF GPS tags via PyExifTool

**Future Work:**
- Reverse geocoding service will enrich location data (separate table/column)
- Location field remains immutable (source of truth)

---

### Tooling Choice: PyExifTool + PIL (NOT ffmpeg/pyav)

**Decision:** Use `PyExifTool` (Python wrapper for `exiftool`) and `PIL/Pillow` for metadata extraction.

**Rationale:**
- **Comprehensive:** ExifTool handles images, videos, RAW files (CR2, NEF, etc.)
- **Proven:** Industry-standard tool for metadata extraction
- **Python Integration:** PyExifTool provides clean Python API
- **Fallback Chain:** PIL/Pillow as fallback for images, file mtime as last resort
- **NOT Using:** `ffmpeg` or `pyav` (not needed for metadata extraction, only for video processing if needed later)

**Implementation Status:** ✅ **IMPLEMENTED**
- Primary: `PyExifTool` (via `exiftool` Python package)
- Fallback: `PIL/Pillow` for images
- Last Resort: File modification time
- Docker: `libimage-exiftool-perl` installed in Dockerfile

**Extraction Priority:**
1. PyExifTool (comprehensive - images, videos, RAW)
2. PIL/Pillow (images only, fallback)
3. File modification time (last resort)

**Date Extraction Tags (in priority order):**
- `EXIF:DateTimeOriginal` (most accurate)
- `EXIF:CreateDate`
- `QuickTime:CreateDate` (videos)
- `XMP:DateCreated`
- `IPTC:DateCreated`
- `File:FileModifyDate` (last resort)

**Location Extraction Tags:**
- `EXIF:GPSLatitude` / `EXIF:GPSLongitude`
- `GPS:GPSLatitude` / `GPS:GPSLongitude`
- `Composite:GPSLatitude` / `Composite:GPSLongitude`

**Note:** `ffmpeg` is NOT currently installed or used. If video processing is needed in the future, it can be added to the Dockerfile.

---

## 2. Current Implementation Status (The "What")

### Dockerfile: ✅ BUILT AND WORKING

**Status:** Dockerfile exists and is functional.

**Location:** `Src/Librarian/Dockerfile`

**Features:**
- **Multi-stage build:** Builder stage runs tests, Runtime stage is minimal
- **Test Gate:** Build fails if tests fail (`pytest Src/Librarian/tests/ -v`)
- **Dependencies:** `libimage-exiftool-perl`, `postgresql-client`
- **Security:** Runs as non-root user (`librarian`, UID 1000)
- **Python:** Python 3.11-slim-bookworm base image

**Build Command:**
```bash
cd D:\Photo_Factory\Stack\App_Data
docker-compose build librarian
```

**Runtime Command:**
```bash
docker-compose up -d librarian
```

**NOT Included:**
- `ffmpeg` (not needed for current metadata extraction)
- Video processing tools (future work if needed)

---

### Database Schema: ✅ IMPLEMENTED

**Status:** `media_assets` table schema is fully implemented with JSONB location column.

**Location:** `Src/Shared/models.py` (implementation) and `docs/DATABASE_SCHEMA.md` (canonical definition)

**Key Columns:**
- `id` (UUID, PRIMARY KEY)
- `file_hash` (String(64), UNIQUE, INDEXED) - SHA256 hex
- `original_name`, `original_path`, `final_path` (Text)
- `size_bytes` (BigInteger)
- `captured_at` (TIMESTAMP, nullable, INDEXED) - True capture date from EXIF
- `ingested_at` (TIMESTAMP, server default) - When Librarian processed file
- **`location` (JSON/JSONB, nullable)** - `{"lat": float, "lon": float}` ✅ IMPLEMENTED
- Status flags: `is_ingested`, `is_geocoded`, `is_thumbnailed`, `is_curated`, `is_backed_up`, `has_errors`
- Timestamps: `geocoded_at`, `thumbnailed_at`, `curated_at`, `backed_up_at`

**Indexes:**
- `idx_media_assets_captured_at` (for date-based queries)
- `idx_media_assets_ingested_at` (for ingestion tracking)
- `idx_media_assets_is_geocoded` (for geocoding queue)
- `idx_media_assets_is_backed_up` (for backup queue)
- `idx_media_assets_has_errors` (for error tracking)

**Database Initialization:**
- `Src/Shared/database.py` - `init_database()` creates all tables
- Called automatically by Librarian on startup
- Uses SQLAlchemy `Base.metadata.create_all()`

---

### Librarian Logic: ✅ IMPLEMENTED - "True Date" Extraction

**Status:** Librarian extracts true capture date from EXIF metadata with comprehensive fallback chain.

**Location:** `Src/Librarian/metadata_extractor.py`

**Implementation:**
- ✅ Extracts `EXIF:DateTimeOriginal` (true capture date) as primary source
- ✅ Fallback chain: ExifTool → PIL → File mtime
- ✅ Handles images, videos, RAW files (CR2, NEF, etc.)
- ✅ Organizes files by true date: `Storage/Originals/{YYYY}/{YYYY-MM-DD}/`
- ✅ Stores `captured_at` timestamp in database

**Date Extraction Flow:**
1. Try PyExifTool (comprehensive metadata)
2. If date not found, try PIL/Pillow (images only)
3. If still not found, use file modification time (last resort)
4. Log warning if using fallback (mtime)

**Location Extraction:**
- Extracts GPS coordinates from EXIF tags
- Stores as JSONB: `{"lat": float, "lon": float}`
- Validates coordinates (lat: -90 to 90, lon: -180 to 180)

**File Processing Flow:**
1. File detected in `Photos_Inbox` (via `FileWatcher`)
2. Stability check (wait for file to be stable/unmodified)
3. Metadata extraction (date + location)
4. Hash calculation (SHA256 for duplicate detection)
5. Collision handling (duplicates vs name collisions)
6. Move to `Storage/Originals/{YYYY}/{YYYY-MM-DD}/`
7. Create database record in `media_assets`

---

## 3. The Immediate Next Steps (The "How")

### Priority 1: Verify System Health After Container Pause

**Task:** Ensure all services start correctly after Docker was paused.

**Steps:**
1. Start Docker Desktop (if not running)
2. Start Photo Factory stack: `cd D:\Photo_Factory\Stack\App_Data && docker-compose up -d`
3. Verify all containers are healthy: `docker-compose ps`
4. Check Librarian logs: `docker logs librarian --tail 50`
5. Verify database connection: `docker exec factory_postgres psql -U photo_factory -d photo_factory -c "SELECT COUNT(*) FROM media_assets;"`
6. Test file processing: Drop a test image in `Photos_Inbox/` and verify it moves to `Storage/Originals/`

**Expected Outcome:** All services running, Librarian processing files, database accessible.

---

### Priority 2: Review and Validate Current Implementation

**Task:** Verify that the current implementation matches the architecture decisions.

**Steps:**
1. Verify `media_assets` table has `location` column as JSONB
2. Verify metadata extraction uses PyExifTool (not ffmpeg)
3. Verify files are organized by true date (`captured_at` from EXIF)
4. Verify storage path is `Storage/Originals/{YYYY}/{YYYY-MM-DD}/`
5. Review test coverage: `pytest Src/Librarian/tests/ -v`

**Expected Outcome:** All architecture decisions are correctly implemented.

---

### Priority 3: Document Any Gaps or Future Work

**Task:** Identify what's missing or planned but not yet implemented.

**Known Gaps:**
- `ffmpeg` not installed (not needed for metadata, but may be needed for video processing later)
- `Storage/Derivatives` not implemented (future gallery work)
- Reverse geocoding service not implemented (location labels)
- Thumbnail generation service not implemented
- Face detection service not implemented
- Backup service not implemented

**Documentation:**
- Update this file if any gaps are discovered
- Add to `docs/` if new architecture decisions are made

---

## 4. Dev Cheatsheet

### Build the Container

```bash
cd D:\Photo_Factory\Stack\App_Data
docker-compose build librarian
```

**Note:** Build runs tests automatically (Stage 1). If tests fail, build fails.

### Run Tests Locally (Without Docker)

```bash
cd D:\Photo_Factory
pytest Src/Librarian/tests/ -v
```

**Prerequisites:**
- Python 3.11+
- Dependencies installed: `pip install -r requirements.txt`
- `exiftool` installed on system (or use Docker)

### Start All Services

```bash
cd D:\Photo_Factory\Stack\App_Data
docker-compose up -d
```

### Stop All Services

```bash
cd D:\Photo_Factory\Stack\App_Data
docker-compose down
```

### View Librarian Logs

```bash
docker logs librarian --tail 50 -f
```

### Check Database

```bash
# Connect to database
docker exec -it factory_postgres psql -U photo_factory -d photo_factory

# Or use the helper script
cd D:\Photo_Factory\Stack\App_Data
.\view_db.ps1 status
```

### Test File Processing

1. Drop a test image in `D:\Photo_Factory\Photos_Inbox\`
2. Wait 5-10 seconds (stability delay)
3. Check `D:\Photo_Factory\Storage\Originals\{YYYY}\{YYYY-MM-DD}\` for the file
4. Verify database record: `docker exec factory_postgres psql -U photo_factory -d photo_factory -c "SELECT original_name, captured_at, location FROM media_assets ORDER BY ingested_at DESC LIMIT 1;"`

---

## 5. Key Files Reference

### Core Implementation
- `Src/Librarian/librarian.py` - Main service entry point
- `Src/Librarian/metadata_extractor.py` - Date and location extraction
- `Src/Librarian/file_watcher.py` - File system watching
- `Src/Librarian/collision_handler.py` - Duplicate and collision handling
- `Src/Librarian/utils.py` - Utility functions

### Shared Components
- `Src/Shared/models.py` - SQLAlchemy models (MediaAsset, SystemStatus, etc.)
- `Src/Shared/database.py` - Database connection and initialization
- `Src/Shared/heartbeat_service.py` - Heartbeat tracking for services

### Configuration
- `Src/Librarian/Dockerfile` - Container build definition
- `Stack/App_Data/docker-compose.yml` - Service orchestration
- `requirements.txt` - Python dependencies

### Documentation
- `docs/DATABASE_SCHEMA.md` - **CANONICAL** database schema definition
- `docs/MEDIA_ASSET_STATUS_DESIGN.md` - Status tracking design
- `README.md` - Project overview and usage

### Tests
- `Src/Librarian/tests/` - All test files
- `Src/Librarian/tests/conftest.py` - Test fixtures and mocks
- `Src/Librarian/tests/test_metadata_extractor.py` - Metadata extraction tests
- `Src/Librarian/tests/test_librarian.py` - Integration tests

---

## 6. Architecture Principles

### Portability (Primary Directive)
- **NO absolute paths** in code (use `pathlib.Path` relative to `__file__`)
- **NO hardcoded paths** (use environment variables or relative paths)
- **Exception:** `.env` file can contain absolute paths for Docker volumes

### Stability
- **Idempotent operations:** Running processes twice shouldn't break anything
- **Error handling:** Services continue operating even if database is temporarily unavailable
- **Graceful degradation:** File processing continues even if metadata extraction fails

### Automation
- **Test Gate:** Docker build fails if tests fail
- **Health Checks:** All services have Docker health checks
- **Heartbeat Tracking:** All services report status to `system_status` table

---

## 7. Known Issues & Future Work

### Known Issues
- None currently documented
- **Last Verified:** 2025-12-30 - All services healthy, database accessible, file processing operational

### Future Work
1. **Video Processing:** May need `ffmpeg` for video metadata extraction or transcoding
2. **Reverse Geocoding:** Service to convert GPS coordinates to human-readable locations
3. **Thumbnail Generation:** Service to create thumbnails for gallery
4. **Face Detection:** Service to identify people in photos
5. **Backup Service:** Automated backup to cloud/external storage
6. **Derivatives Storage:** `Storage/Derivatives` for processed/gallery files

---

**END OF CONTEXT DOCUMENT**

