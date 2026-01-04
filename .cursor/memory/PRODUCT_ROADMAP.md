# Product Roadmap

**Last Updated:** 2026-01-03  
**Purpose:** Track epics, workstreams, and tasks for Photo Factory development

---

## Roadmap Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Completed |
| 🔄 | In Progress |
| ⏳ | Pending |
| ❌ | Blocked/Cancelled |
| 🔥 | High Priority |
| 📋 | Low Priority |

---

## Epic 0: Memory Bank Initialization 🔥 ✅

**Goal:** Create persistent context structure for seamless agent handoffs.

### Workstream 0.1: Directory Structure Setup ✅
- [x] Create `.cursor/` directory
- [x] Create `.cursor/memory/` for long-term context
- [x] Create `.cursor/active_sprint/` for short-term state

### Workstream 0.2: Context Population 🔄
- [x] Write TECH_STACK.md from docker-compose and requirements
- [x] Write ARCHITECTURE.md with data flow and modules
- [x] Write PROJECT_BRIEF.md with Future Capabilities section
- [x] Initialize LESSONS_LEARNED.md with patterns found
- [x] Initialize DECISION_LOG.md with 6+ implicit ADRs
- [x] Write PRODUCT_ROADMAP.md with all Epics

### Workstream 0.3: Agent Protocol Enforcement ✅
- [x] Update `.cursorrules` with Section 9: Memory Bank Protocol
- [x] Update `.cursorrules` with Section 10: User Story Testing Protocol
- [x] Add startup protocol (print roadmap, await approval)
- [x] Add hierarchical todo format rule

### Workstream 0.4: User Story Testing Framework ✅
- [x] Add pytest-bdd to requirements.txt
- [x] Create `tests/conftest.py` (project root)
- [x] Create `tests/features/` directory
- [x] Create service-specific `tests/features/` directories
- [x] Define test markers (@unit, @integration, @slow)
- [x] Create sample .feature file template

---

## Epic 1: Core Ingestion (Librarian) ✅

**Goal:** Automated photo/video ingestion with date-based organization.

### Workstream 1.1: File Watching ✅
- [x] Implement file system watcher using watchdog
- [x] Add stability delay for in-progress files
- [x] Implement periodic scan fallback

### Workstream 1.2: Metadata Extraction ✅
- [x] Implement ExifTool integration via PyExifTool
- [x] Add PIL/Pillow fallback for images
- [x] Add file mtime fallback
- [x] Extract GPS coordinates to JSONB

### Workstream 1.3: Duplicate Detection ✅
- [x] Implement SHA256 hash calculation
- [x] Check against database for existing hashes
- [x] Delete duplicates from inbox

### Workstream 1.4: File Organization ✅
- [x] Create `{YYYY}/{YYYY-MM-DD}/` folder structure
- [x] Handle filename collisions with suffixes
- [x] Use shutil.move for cross-device support

### Workstream 1.5: Database Integration ✅
- [x] Create `media_assets` table
- [x] Write records on successful ingestion
- [x] Implement status flags pattern

---

## Epic 2: Monitoring & Observability ✅

**Goal:** Real-time visibility into system health and processing status.

### Workstream 2.1: Heartbeat System ✅
- [x] Create `system_status` table (fast lookup)
- [x] Create `system_status_history` table (time series)
- [x] Implement HeartbeatService class
- [x] Add heartbeat to Librarian (60s interval)
- [x] Add heartbeat to Dashboard (5min interval)

### Workstream 2.2: Infrastructure Monitoring ✅
- [x] Create service-monitor container
- [x] Monitor factory-db health
- [x] Monitor syncthing health
- [x] Update heartbeats for infrastructure services

### Workstream 2.3: Dashboard UI ✅
- [x] Implement Streamlit dashboard
- [x] Add service selector
- [x] Display container status via Docker API
- [x] Display heartbeat information
- [x] Show media asset statistics
- [x] Show recent processed files
- [x] Add service logs view
- [x] Implement auto-refresh

### Workstream 2.4: Data Retention ✅
- [x] Create cleanup script for historical data
- [x] Set 60-day retention policy
- [x] Document cleanup procedures

---

## Epic 3: Docker Infrastructure ✅

**Goal:** Containerized, portable deployment with health checks.

### Workstream 3.1: Core Containers ✅
- [x] Create Librarian Dockerfile (multi-stage)
- [x] Create Dashboard Dockerfile
- [x] Create service-monitor Dockerfile
- [x] Implement test gate in builds

### Workstream 3.2: Docker Compose ✅
- [x] Define all services in docker-compose.yml
- [x] Configure health checks
- [x] Set up volume mounts
- [x] Configure networking

### Workstream 3.3: Database Infrastructure ✅
- [x] Add factory-db service (PostgreSQL 15)
- [x] Configure persistence volumes
- [x] Add health check

### Workstream 3.4: File Sync Infrastructure ✅
- [x] Add Syncthing service
- [x] Configure volume mounts
- [x] Add health check
- [x] Document initial setup

---

## Epic 4: Reverse Geocoding ⏳ 📋

**Goal:** Convert GPS coordinates to human-readable place names.

### Workstream 4.1: Geocoding Service ⏳
- [ ] Design geocoding table/column structure
- [ ] Choose geocoding provider (Nominatim, Google, etc.)
- [ ] Implement geocoding service
- [ ] Add rate limiting

### Workstream 4.2: Integration ⏳
- [ ] Query pending assets: `WHERE is_geocoded = FALSE AND location IS NOT NULL`
- [ ] Update `is_geocoded` flag on completion
- [ ] Add heartbeat tracking
- [ ] Create Dockerfile

---

## Epic 5: Thumbnail Generation ⏳ 📋

**Goal:** Generate optimized thumbnails for gallery viewing.

### Workstream 5.1: Thumbnail Service ⏳
- [ ] Create `Storage/Derivatives/thumbnails/` structure
- [ ] Implement thumbnail generation (multiple sizes)
- [ ] Handle image orientation
- [ ] Support video thumbnails

### Workstream 5.2: Integration ⏳
- [ ] Query pending assets: `WHERE is_thumbnailed = FALSE`
- [ ] Update `is_thumbnailed` flag on completion
- [ ] Add heartbeat tracking
- [ ] Create Dockerfile

---

## Epic 6: Cloud Backup ⏳ 📋

**Goal:** Automated backup of originals to cloud storage.

### Workstream 6.1: Backup Service ⏳
- [ ] Choose backup providers (S3, B2, GCS)
- [ ] Implement rclone or custom integration
- [ ] Add encryption support
- [ ] Implement incremental backup

### Workstream 6.2: Integration ⏳
- [ ] Query pending assets: `WHERE is_backed_up = FALSE`
- [ ] Update `is_backed_up` flag on completion
- [ ] Add heartbeat tracking
- [ ] Create Dockerfile

---

## Epic 7: Enhanced Dashboard ⏳ 📋

**Goal:** Advanced monitoring and visualization features.

### Workstream 7.1: Pipeline Visualization ⏳
- [ ] Show processing pipeline diagram
- [ ] Display queue lengths for each stage
- [ ] Add processing rate metrics

### Workstream 7.2: Historical Analytics ⏳
- [ ] Uptime graphs from heartbeat history
- [ ] Processing volume charts
- [ ] Error rate tracking

### Workstream 7.3: Alerting ⏳
- [ ] Email notifications for errors
- [ ] Webhook support (Discord, Slack)
- [ ] Configurable alert thresholds

---

## Epic 8: Testing Infrastructure ⏳ 📋

**Goal:** Comprehensive test coverage with BDD features.

### Workstream 8.1: Build-Time Tests ⏳
- [ ] Unit tests for all modules
- [ ] Mocked integration tests
- [ ] Fast execution (< 30s)

### Workstream 8.2: Runtime Tests ⏳
- [ ] Full integration tests with database
- [ ] Real asset processing tests
- [ ] Docker compose test environment

### Workstream 8.3: BDD Features ⏳
- [ ] User story feature files
- [ ] Step definitions
- [ ] pytest-bdd integration

---

## Backlog (Future Epics)

### Epic 9: Facial Recognition
- Face detection and extraction
- Person identification and tagging
- Album generation by person

### Epic 10: Smart Albums
- AI-generated collections
- Event detection
- Theme/content grouping

### Epic 11: Video Transcoding
- Web-friendly formats
- Resolution variants
- Streaming support

### Epic 12: Mobile Integration
- Direct upload API
- Mobile app evaluation
- Push notifications

### Epic 13: AI Editing
- Auto-enhancement
- Crop suggestions
- Color correction

---

## Milestone Timeline

| Quarter | Focus |
|---------|-------|
| Q1 2026 | Memory Bank, Testing Infrastructure |
| Q2 2026 | Geocoding, Thumbnails |
| Q3 2026 | Cloud Backup, Enhanced Dashboard |
| Q4 2026 | Facial Recognition, Smart Albums |

---

**END OF PRODUCT ROADMAP**

