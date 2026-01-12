# Product Roadmap

**Last Updated:** 2026-01-10  
**Purpose:** Track epics, workstreams, and tasks for Photo Factory development

---

## Status & Priority Legend

| Status | Meaning |
|--------|---------|
| `Not Started` | Work has not begun |
| `In Progress` | Actively being developed |
| `Completed` | All tasks finished and verified |
| `Blocked` | Waiting on external dependency |
| `Cancelled` | No longer planned |

| Priority | Meaning |
|----------|---------|
| `High` | Critical path, required for core functionality |
| `Medium` | Important but not blocking |
| `Low` | Nice-to-have, can be deferred |

*Note: Emojis (✅, 🔄, ⏳) are visual aids only. The `Status` field is the source of truth.*

---

## Epic 0: Memory Bank Initialization ✅
**Status:** Completed | **Priority:** High

**Goal:** Create persistent context structure for seamless agent handoffs.

### Workstream 0.1: Directory Structure Setup
**Status:** Completed | **Priority:** High
- [x] Create `.cursor/` directory
- [x] Create `.cursor/memory/` for long-term context
- [x] Create `.cursor/active_sprint/` for short-term state

### Workstream 0.2: Context Population
**Status:** Completed | **Priority:** High
- [x] Write TECH_STACK.md from docker-compose and requirements
- [x] Write ARCHITECTURE.md with data flow and modules
- [x] Write PROJECT_BRIEF.md with Future Capabilities section
- [x] Initialize LESSONS_LEARNED.md with patterns found
- [x] Initialize DECISION_LOG.md with 6+ implicit ADRs
- [x] Write PRODUCT_ROADMAP.md with all Epics

### Workstream 0.3: Agent Protocol Enforcement
**Status:** Completed | **Priority:** High
- [x] Update `.cursorrules` with Memory Bank Protocol
- [x] Update `.cursorrules` with User Story Testing Protocol
- [x] Add startup protocol (print roadmap, await approval)
- [x] Add hierarchical todo format rule
- [x] Refactor to 4-pillar structure with RFC-2119 language (ADR-010)

### Workstream 0.4: User Story Testing Framework
**Status:** Completed | **Priority:** High
- [x] Add pytest-bdd to requirements.txt
- [x] Create `tests/conftest.py` (project root)
- [x] Create `tests/features/` directory
- [x] Create service-specific `tests/features/` directories
- [x] Define test markers (@unit, @integration, @slow)
- [x] Create sample .feature file template

---

## Epic 1: Core Ingestion (Librarian) ✅
**Status:** Completed | **Priority:** High

**Goal:** Automated photo/video ingestion with date-based organization.

### Workstream 1.1: File Watching
**Status:** Completed | **Priority:** High
- [x] Implement file system watcher using watchdog
- [x] Add stability delay for in-progress files
- [x] Implement periodic scan fallback

### Workstream 1.2: Metadata Extraction
**Status:** Completed | **Priority:** High
- [x] Implement ExifTool integration via PyExifTool
- [x] Add PIL/Pillow fallback for images
- [x] Add file mtime fallback
- [x] Extract GPS coordinates to JSONB

### Workstream 1.3: Duplicate Detection
**Status:** Completed | **Priority:** High
- [x] Implement SHA256 hash calculation
- [x] Check against database for existing hashes
- [x] Delete duplicates from inbox

### Workstream 1.4: File Organization
**Status:** Completed | **Priority:** High
- [x] Create `{YYYY}/{YYYY-MM-DD}/` folder structure
- [x] Handle filename collisions with suffixes
- [x] Use shutil.move for cross-device support

### Workstream 1.5: Database Integration
**Status:** Completed | **Priority:** High
- [x] Create `media_assets` table
- [x] Write records on successful ingestion
- [x] Implement status flags pattern

---

## Epic 2: Monitoring & Observability ✅
**Status:** Completed | **Priority:** High

**Goal:** Real-time visibility into system health and processing status.

### Workstream 2.1: Heartbeat System
**Status:** Completed | **Priority:** High
- [x] Create `system_status` table (fast lookup)
- [x] Create `system_status_history` table (time series)
- [x] Implement HeartbeatService class
- [x] Add heartbeat to Librarian (60s interval)
- [x] Add heartbeat to Dashboard (5min interval)

### Workstream 2.2: Infrastructure Monitoring
**Status:** Completed | **Priority:** High
- [x] Create service-monitor container
- [x] Monitor factory-db health
- [x] Monitor syncthing health
- [x] Update heartbeats for infrastructure services

### Workstream 2.3: Dashboard UI
**Status:** Completed | **Priority:** High
- [x] Implement Streamlit dashboard
- [x] Add service selector
- [x] Display container status via Docker API
- [x] Display heartbeat information
- [x] Show media asset statistics
- [x] Show recent processed files
- [x] Add service logs view
- [x] Implement auto-refresh

### Workstream 2.4: Data Retention
**Status:** Completed | **Priority:** High
- [x] Create cleanup script for historical data
- [x] Set 60-day retention policy
- [x] Document cleanup procedures

---

## Epic 3: Docker Infrastructure ✅
**Status:** Completed | **Priority:** High

**Goal:** Containerized, portable deployment with health checks.

### Workstream 3.1: Core Containers
**Status:** Completed | **Priority:** High
- [x] Create Librarian Dockerfile (multi-stage)
- [x] Create Dashboard Dockerfile
- [x] Create service-monitor Dockerfile
- [x] Implement test gate in builds

### Workstream 3.2: Docker Compose
**Status:** Completed | **Priority:** High
- [x] Define all services in docker-compose.yml
- [x] Configure health checks
- [x] Set up volume mounts
- [x] Configure networking

### Workstream 3.3: Database Infrastructure
**Status:** Completed | **Priority:** High
- [x] Add factory-db service (PostgreSQL 15)
- [x] Configure persistence volumes
- [x] Add health check

### Workstream 3.4: File Sync Infrastructure
**Status:** Completed | **Priority:** High
- [x] Add Syncthing service
- [x] Configure volume mounts
- [x] Add health check
- [x] Document initial setup

---

## Epic 4: Media Enrichment Services ⏳
**Status:** Not Started | **Priority:** Low

**Goal:** Post-ingestion services that enrich metadata and generate derivatives.

### Workstream 4.1: Reverse Geocoding
**Status:** Not Started | **Priority:** Low
- [ ] Design geocoding table/column structure
- [ ] Choose geocoding provider (Nominatim, Google, etc.)
- [ ] Implement geocoding service
- [ ] Add rate limiting
- [ ] Query pending assets: `WHERE is_geocoded = FALSE AND location IS NOT NULL`
- [ ] Update `is_geocoded` flag on completion
- [ ] Add heartbeat tracking
- [ ] Create Dockerfile

### Workstream 4.2: Thumbnail Generation
**Status:** Not Started | **Priority:** Low
- [ ] Create `Storage/Derivatives/thumbnails/` structure
- [ ] Implement thumbnail generation (multiple sizes: 150px, 300px, 600px)
- [ ] Handle image orientation via EXIF
- [ ] Support video thumbnails (extract frame at 1s)
- [ ] Query pending assets: `WHERE is_thumbnailed = FALSE`
- [ ] Update `is_thumbnailed` flag on completion
- [ ] Add heartbeat tracking
- [ ] Create Dockerfile

---

## Epic 5: Cloud Backup ⏳
**Status:** Not Started | **Priority:** Low

**Goal:** Automated backup of originals to cloud storage.

### Workstream 5.1: Backup Service
**Status:** Not Started | **Priority:** Low
- [ ] Choose backup provider (S3, B2, GCS)
- [ ] Implement rclone or custom integration
- [ ] Add encryption support (client-side)
- [ ] Implement incremental backup (hash-based)

### Workstream 5.2: Backup Integration
**Status:** Not Started | **Priority:** Low
- [ ] Query pending assets: `WHERE is_backed_up = FALSE`
- [ ] Update `is_backed_up` flag on completion
- [ ] Add heartbeat tracking
- [ ] Create Dockerfile
- [ ] Add restore verification

---

## Epic 6: Enhanced Dashboard 🔄
**Status:** In Progress | **Priority:** Medium

**Goal:** Advanced monitoring and visualization features.

### Workstream 6.0: Flicker-Free Resource Monitoring
**Status:** Completed | **Priority:** High
- [x] Add psutil>=5.9.0 to requirements.txt
- [x] Update TECH_STACK.md with psutil entry (ADR-011)
- [x] Implement get_system_resources() function
- [x] Implement render_resource_header() with CPU/RAM/Disk metrics
- [x] Add CSS transitions for flicker-free auto-refresh
- [x] Refactor dashboard to container-based architecture (st.empty pattern)
- [x] Add unit tests for resource functions (test_dashboard_resources.py)
- [x] Add BDD feature file (resource_monitoring.feature)
- [x] Fix test boundary conditions to match implementation (<=)
- [x] Docker validation passed

### Workstream 6.1: Pipeline Visualization
**Status:** Not Started | **Priority:** Low
- [ ] Show processing pipeline diagram (ingested → geocoded → thumbnailed → backed_up)
- [ ] Display queue lengths for each stage
- [ ] Add processing rate metrics (files/hour)

### Workstream 6.2: Historical Analytics
**Status:** Not Started | **Priority:** Low
- [ ] Uptime graphs from heartbeat history
- [ ] Processing volume charts (daily/weekly/monthly)
- [ ] Error rate tracking and trends

### Workstream 6.3: Alerting
**Status:** Not Started | **Priority:** Low
- [ ] Email notifications for errors
- [ ] Webhook support (Discord, Slack)
- [ ] Configurable alert thresholds

---

## Epic 7: Test Coverage Expansion ⏳
**Status:** Not Started | **Priority:** Medium

**Goal:** Comprehensive test coverage with BDD features for all services.

### Workstream 7.1: Build-Time Tests
**Status:** Not Started | **Priority:** Medium
- [ ] Unit tests for all Librarian modules
- [ ] Unit tests for Dashboard components
- [ ] Unit tests for Shared utilities
- [ ] Mocked integration tests
- [ ] Fast execution target (< 30s total)

### Workstream 7.2: Runtime Tests
**Status:** Not Started | **Priority:** Medium
- [ ] Full integration tests with database
- [ ] Real asset processing tests (photos, videos, RAW)
- [ ] Docker compose test environment
- [ ] End-to-end pipeline tests

### Workstream 7.3: BDD Feature Coverage
**Status:** Not Started | **Priority:** Medium
- [ ] Librarian ingestion scenarios
- [ ] Dashboard display scenarios
- [ ] Error handling scenarios
- [ ] Duplicate detection scenarios
- [ ] Step definitions for all features

---

## Backlog: Future Epics

*These epics are planned but not yet scheduled. Architectural implications are noted to ensure current code supports future capabilities.*

---

## Epic 8: Facial Recognition ⏳
**Status:** Not Started | **Priority:** Low

**Goal:** Detect faces in photos and enable person-based organization.

### Workstream 8.1: Face Detection
**Status:** Not Started | **Priority:** Low
- [ ] Integrate face detection library (dlib, OpenCV, InsightFace)
- [ ] Extract face embeddings (128/512-dimensional vectors)
- [ ] Store face bounding boxes in JSONB

### Workstream 8.2: Person Identification
**Status:** Not Started | **Priority:** Low
- [ ] Create `persons` table with embedding storage
- [ ] Implement face clustering for person discovery
- [ ] Add manual person tagging UI
- [ ] Generate albums by person

**Architectural Implications:**
- **Database:** Requires vector storage for face embeddings. Current PostgreSQL supports `pgvector` extension for similarity search. Schema should include: `faces` table (id, media_asset_id, embedding, bounding_box JSONB), `persons` table (id, name, representative_embedding).
- **Storage:** Face thumbnails in `Storage/Derivatives/faces/`.
- **Processing:** GPU recommended for inference; fallback to CPU acceptable but slow.
- **Current Support:** `location` JSONB pattern in `media_assets` can be extended to `faces` JSONB array.

---

## Epic 9: Smart Albums ⏳
**Status:** Not Started | **Priority:** Low

**Goal:** AI-generated collections based on events, themes, and content.

### Workstream 9.1: Event Detection
**Status:** Not Started | **Priority:** Low
- [ ] Cluster photos by time+location proximity
- [ ] Detect event boundaries (gaps > 4 hours)
- [ ] Generate event names from location/date

### Workstream 9.2: Theme Grouping
**Status:** Not Started | **Priority:** Low
- [ ] Implement image classification (scenes, objects)
- [ ] Create theme-based collections (beach, mountains, family)
- [ ] Add content tagging

**Architectural Implications:**
- **Database:** Requires `albums` table (id, name, type, criteria JSONB), `album_assets` junction table. Type enum: 'manual', 'event', 'person', 'theme'.
- **ML Models:** Scene classification (ResNet/EfficientNet), object detection (YOLO). Models stored in `Stack/App_Data/models/`.
- **Current Support:** JSONB pattern supports flexible criteria storage. Processing flags pattern (`is_classified`) works for queue management.

---

## Epic 10: Video Transcoding ⏳
**Status:** Not Started | **Priority:** Low

**Goal:** Generate web-friendly video formats and streaming-ready files.

### Workstream 10.1: Transcoding Service
**Status:** Not Started | **Priority:** Low
- [ ] Integrate FFmpeg for transcoding
- [ ] Generate web-friendly formats (H.264/MP4, WebM)
- [ ] Create resolution variants (1080p, 720p, 480p)
- [ ] Extract video thumbnails (sprite sheets)

### Workstream 10.2: Streaming Support
**Status:** Not Started | **Priority:** Low
- [ ] Generate HLS/DASH segments
- [ ] Create manifest files
- [ ] Implement adaptive bitrate

**Architectural Implications:**
- **Dependencies:** FFmpeg MUST be installed in container (not currently present; add `ffmpeg` to Dockerfile).
- **Storage:** Transcoded files in `Storage/Derivatives/transcoded/{resolution}/`. HLS segments in `Storage/Derivatives/streaming/`.
- **Database:** Add `is_transcoded`, `transcoded_at` flags to `media_assets`. Add `video_metadata` JSONB column (duration, bitrate, codec).
- **Current Support:** Derivatives folder structure planned in ADR-003. Status flags pattern ready to extend.

---

## Epic 11: Mobile Integration ⏳
**Status:** Not Started | **Priority:** Low

**Goal:** Direct upload from mobile devices and mobile app support.

### Workstream 11.1: Upload API
**Status:** Not Started | **Priority:** Low
- [ ] Create REST API for uploads (FastAPI service)
- [ ] Implement authentication (API keys, OAuth)
- [ ] Add upload queue and progress tracking
- [ ] Support resumable uploads (tus protocol)

### Workstream 11.2: Mobile Notifications
**Status:** Not Started | **Priority:** Low
- [ ] Push notifications for processing completion
- [ ] Mobile app evaluation (PhotoPrism app, custom)
- [ ] Offline upload queue

**Architectural Implications:**
- **New Service:** Requires new `api-gateway` service in docker-compose. Port exposure and reverse proxy (Traefik/Nginx) needed.
- **Database:** Add `upload_source` column to `media_assets` (enum: 'syncthing', 'api', 'manual'). Add `api_keys` table for authentication.
- **Security:** API endpoints MUST use HTTPS. Rate limiting required.
- **Current Support:** Photos_Inbox can receive uploads from API; Librarian will process them normally.

---

## Epic 12: AI Enhancement ⏳
**Status:** Not Started | **Priority:** Low

**Goal:** Automatic photo enhancement and editing suggestions.

### Workstream 12.1: Auto-Enhancement
**Status:** Not Started | **Priority:** Low
- [ ] Implement auto-exposure correction
- [ ] Add white balance adjustment
- [ ] Apply noise reduction
- [ ] Suggest crop improvements

### Workstream 12.2: Non-Destructive Editing
**Status:** Not Started | **Priority:** Low
- [ ] Store edit parameters as JSONB (not pixel changes)
- [ ] Generate enhanced derivatives on demand
- [ ] Allow edit reversion

**Architectural Implications:**
- **Storage:** Enhanced images in `Storage/Derivatives/enhanced/`. Edit parameters in database, not file system.
- **Database:** Add `edit_params` JSONB column to `media_assets`. Store enhancement steps as array: `[{"op": "exposure", "value": 0.5}, {"op": "crop", "bounds": {...}}]`.
- **Processing:** ML models for enhancement (OpenCV, Pillow, or ML-based like ESRGAN). GPU acceleration beneficial.
- **Immutability:** Originals MUST remain untouched per ADR-003. All enhancements are derivatives.

---

## Milestone Timeline

| Quarter | Focus | Epics |
|---------|-------|-------|
| Q1 2026 | Foundation | Epic 0 (Memory Bank) ✅, Epic 7 (Test Coverage) |
| Q2 2026 | Enrichment | Epic 4 (Media Enrichment), Epic 5 (Cloud Backup) |
| Q3 2026 | Enhancement | Epic 6 (Enhanced Dashboard), Epic 10 (Video Transcoding) |
| Q4 2026 | Intelligence | Epic 8 (Facial Recognition), Epic 9 (Smart Albums) |
| Q1 2027 | Integration | Epic 11 (Mobile), Epic 12 (AI Enhancement) |

---

**END OF PRODUCT ROADMAP**
