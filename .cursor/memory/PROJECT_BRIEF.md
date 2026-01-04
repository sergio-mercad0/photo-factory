# Project Brief

**Last Updated:** 2026-01-03  
**Purpose:** Define Photo Factory's mission, scope, and future direction

---

## Mission

**Photo Factory** is a self-hosted, automated photo and video management system that provides:
- **Automatic ingestion** from multiple devices
- **Date-based organization** using true capture metadata
- **Duplicate detection** to prevent storage waste
- **Full observability** through real-time monitoring

---

## Problem Solved

| Problem | Photo Factory Solution |
|---------|----------------------|
| Manual photo organization is tedious | Automatic organization by capture date |
| Cloud services lack control & privacy | Self-hosted with full data ownership |
| Duplicates waste storage space | SHA256 hash-based deduplication |
| Hard to know if sync is working | Real-time dashboard with heartbeats |
| Photos get lost or disorganized | Immutable originals with database catalog |

---

## Primary Directives

Per `.cursorrules`, all development must prioritize:

1. **Portability** - No hardcoded paths, works on any system
2. **Stability** - Idempotent operations, graceful error handling
3. **Automation** - Minimal manual intervention required

---

## Current Scope

### Core Features (Implemented ✅)

| Feature | Description | Status |
|---------|-------------|--------|
| **File Ingestion** | Watch `Photos_Inbox/` for new files | ✅ Implemented |
| **Date Organization** | Move to `Storage/Originals/{YYYY}/{YYYY-MM-DD}/` | ✅ Implemented |
| **Metadata Extraction** | Extract capture date and GPS from EXIF | ✅ Implemented |
| **Duplicate Detection** | SHA256 hash comparison | ✅ Implemented |
| **Database Catalog** | PostgreSQL with full asset metadata | ✅ Implemented |
| **Service Heartbeats** | Track service health in database | ✅ Implemented |
| **Monitoring Dashboard** | Streamlit UI with real-time status | ✅ Implemented |
| **Docker Deployment** | Containerized services with health checks | ✅ Implemented |
| **File Sync** | Syncthing for multi-device sync | ✅ Implemented |

### Supported File Types

| Category | Extensions |
|----------|------------|
| Images | .jpg, .jpeg, .png, .gif, .webp, .heic, .heif |
| RAW | .cr2, .nef, .arw, .dng, .raf, .orf |
| Video | .mp4, .mov, .avi, .mkv, .m4v |

### Monitored Services

| Service | Heartbeat Source | Interval |
|---------|------------------|----------|
| librarian | Self-reporting | 60s |
| dashboard | Self-reporting | 5min |
| factory-db | service-monitor | 5min |
| syncthing | service-monitor | 5min |

---

## Future Capabilities (Architectural Awareness)

**⚠️ PURPOSE:** These are listed to ensure current architectural decisions support future growth. **DO NOT plan implementation tasks for these yet.**

### 1. Reverse Geocoding
Convert GPS coordinates to human-readable place names.

**Architecture Consideration:**
- JSONB `location` field preserves raw coordinates (immutable)
- Geocoded labels stored in separate column or table
- `is_geocoded` flag tracks processing status

### 2. Thumbnail Generation
Create optimized thumbnails for gallery viewing.

**Architecture Consideration:**
- `Storage/Derivatives/` path reserved for processed files
- `is_thumbnailed` flag and `thumbnailed_at` timestamp ready
- Originals never modified (thumbnails are derivatives)

### 3. Facial Recognition
Identify and tag people in photos.

**Architecture Consideration:**
- JSONB fields can extend to face bounding box coordinates
- Separate `faces` table can link to `media_assets`
- ML service can run independently (Immich ML available)

### 4. Cloud Archival
Backup originals to S3, B2, GCS, or other cloud storage.

**Architecture Consideration:**
- `is_backed_up` flag and `backed_up_at` timestamp ready
- Backup service queries `WHERE is_backed_up = FALSE`
- Supports multiple backup destinations

### 5. Smart Albums
AI-generated photo collections by theme, event, or content.

**Architecture Consideration:**
- Flexible status flags pattern supports new processing stages
- JSONB fields can store ML-generated tags
- Separate `albums` and `album_photos` tables

### 6. Video Transcoding
Generate web-friendly derivatives for streaming.

**Architecture Consideration:**
- `Storage/Derivatives/` for transcoded videos
- `is_thumbnailed` pattern extensible to `is_transcoded`
- ffmpeg can be added to Dockerfile when needed

### 7. Mobile Sync (Direct)
Direct upload from phone apps without intermediate sync.

**Architecture Consideration:**
- Syncthing already handles multi-device sync
- API endpoint could accept direct uploads to `Photos_Inbox/`
- Authentication layer would be required

### 8. AI Curating
Automatic selection of best photos from a series.

**Architecture Consideration:**
- ML service scores photos for quality, composition
- `is_curated` flag tracks manual or AI curation
- Derivatives path for curated exports

### 9. AI Editing
Automatic enhancement and editing of photos.

**Architecture Consideration:**
- Non-destructive editing (originals preserved)
- Edited versions in `Storage/Derivatives/`
- Edit settings stored in JSONB for reproducibility
- "Smart Crop" (Saliency detection to center subject).
- "Distraction Removal" (Use Segmentation to identify and remove background bystanders).

### 10. AI Movies
Stitch together videos and photos to remmember moments in time

**Architecture Consideration:**
- Tags to draw themes and places from geolocation
- Video cutting and editing
- Music curation

---

## User Personas

### Primary: Home User
- Has thousands of photos on phone, tablet, laptop
- Wants automatic organization without cloud dependency
- Needs to know system is working (observability)
- Values privacy and data ownership

### Secondary: Power User
- Manages family photo archive (100K+ photos)
- Wants duplicate detection and deduplication
- Needs historical data for troubleshooting
- May extend system with custom services

---

## Success Metrics

| Metric | Target |
|--------|--------|
| File Processing Latency | < 30 seconds from drop to organized |
| Duplicate Detection Rate | 100% (based on content hash) |
| Service Uptime | 99.9% (tracked via heartbeats) |
| Manual Intervention | Near zero for normal operation |
| Dashboard Response Time | < 2 seconds for all views |

---

## Non-Goals (Explicit Exclusions)

| Feature | Reason |
|---------|--------|
| Cloud-first architecture | Self-hosted is primary directive |
| Mobile app development | Use existing sync apps (Syncthing) |
| Social sharing features | Privacy-focused, no public sharing |
| Photo editing UI | Should be automated, keep derivatives |
| Real-time collaboration | Single-user/family focus |

---

## Related Documentation

- `docs/DATABASE_SCHEMA.md` - Canonical database definitions
- `docs/MEDIA_ASSET_STATUS_DESIGN.md` - Status flag design
- `README.md` - Installation and usage
- `.cursorrules` - Development guidelines

---

**END OF PROJECT BRIEF**

