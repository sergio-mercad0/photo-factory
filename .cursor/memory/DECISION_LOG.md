# Decision Log

**Last Updated:** 2026-01-03  
**Purpose:** Architecture Decision Records (ADRs) for Photo Factory

---

## How to Use This Document

**When to add a DECISION:**
- New technology choice
- Architecture pattern selection
- Schema design decision
- Infrastructure choice

**When to add to LESSONS_LEARNED instead:**
- Bug fixes and their causes
- Operational constraints discovered
- Performance insights
- Debugging tips

---

## ADR-001: PostgreSQL over SQLite

**Date:** 2024-12-28  
**Status:** Accepted  
**Author:** Initial Architecture

### Context
Choosing database for media asset tracking and system status.

### Decision
Use PostgreSQL 15 (Alpine) as the primary database.

### Rationale
- **JSONB Support:** Native JSONB type for flexible location data storage
- **Concurrency:** Better handling of concurrent writes from multiple services
- **Scalability:** Can handle large media asset catalogs efficiently
- **Production-Ready:** Industry-standard for production applications
- **Docker Integration:** Runs as containerized service

### Alternatives Considered
| Option | Pros | Cons |
|--------|------|------|
| SQLite | Simple, no server | Poor concurrency, limited types |
| MySQL | Widely used | Less flexible JSON, licensing |
| MongoDB | Native JSON | Overkill, different paradigm |

### Consequences
- Requires Docker service (`factory-db`)
- More setup than SQLite
- Enables future capabilities (vector search, full-text)

---

## ADR-002: Docker Compose for Orchestration

**Date:** 2024-12-28 (Implicit)  
**Status:** Accepted  
**Author:** Initial Architecture

### Context
Need container orchestration for multi-service architecture.

### Decision
Use Docker Compose with project root as build context.

### Rationale
- **Simple Local Development:** Single command to start all services
- **Portable:** Works on Windows, Mac, Linux
- **Infrastructure as Code:** Version-controlled configuration
- **Health Checks:** Built-in container health monitoring
- **Networking:** Automatic service discovery

### Alternatives Considered
| Option | Pros | Cons |
|--------|------|------|
| Kubernetes | Scalable, production-grade | Overkill for home use |
| Docker Swarm | Simpler than K8s | Less ecosystem support |
| Bare metal | No container overhead | Not portable, hard to manage |

### Consequences
- All services containerized
- Health checks mandatory
- Volumes for persistence
- Build context at project root

---

## ADR-003: Originals vs Derivatives Separation

**Date:** 2024-12-28 (Implicit)  
**Status:** Accepted  
**Author:** Initial Architecture

### Context
Need storage strategy for processed photos.

### Decision
Separate `Storage/Originals` (immutable source) from `Storage/Derivatives` (processed).

### Rationale
- **Immutability:** Originals are never modified after ingest
- **Separation of Concerns:** Source files vs processed files
- **Backup Strategy:** Only backup Originals (derivatives regenerable)
- **Data Integrity:** Original EXIF preserved forever

### Storage Structure
```
Storage/
├── Originals/           # Immutable, organized by date
│   └── {YYYY}/
│       └── {YYYY-MM-DD}/
│           └── filename.jpg
└── Derivatives/         # Processed files (future)
    └── thumbnails/
    └── transcoded/
    └── edited/
```

### Consequences
- Librarian writes only to Originals
- Future services write to Derivatives
- Clear backup scope (Originals only)

---

## ADR-004: JSONB for Extensible Metadata

**Date:** 2024-12-28 (Implicit)  
**Status:** Accepted  
**Author:** Initial Architecture

### Context
Need to store GPS coordinates with room for future expansion.

### Decision
Use PostgreSQL JSONB for `location` field in `media_assets`.

### Rationale
- **Flexibility:** Can add altitude, accuracy, heading without schema migration
- **Native Queries:** PostgreSQL JSONB operators (`->`, `->>`, `@>`)
- **Indexable:** Can create GIN indexes on JSONB fields
- **Future-Proof:** Facial recognition coordinates, ML tags

### Format
```json
{
  "lat": 35.6762,
  "lon": 139.6503,
  // Future fields (no schema change needed):
  "altitude": 150.5,
  "accuracy": 5.0,
  "heading": 45.0
}
```

### Alternatives Considered
| Option | Pros | Cons |
|--------|------|------|
| Separate columns | Clear schema | Schema migration for new fields |
| TEXT JSON | Simple | No operators, no indexing |
| PostGIS | Powerful geo | Overkill, complex setup |

### Consequences
- Flexible queries for location data
- Future-proof for facial recognition coordinates
- Smart album metadata can use same pattern

---

## ADR-005: Status Flags Pattern

**Date:** 2024-12-28 (Implicit)  
**Status:** Accepted  
**Author:** Initial Architecture

### Context
Need to track multi-stage processing pipeline.

### Decision
Use boolean flags (`is_X`) with corresponding timestamps (`X_at`) for each processing stage.

### Rationale
- **Clear Queue Queries:** `WHERE is_geocoded = FALSE AND location IS NOT NULL`
- **Extensible:** Each new service adds its own flag
- **Idempotent:** Re-processing sets same flag value
- **Observable:** Dashboard can show pipeline progress

### Current Flags
| Flag | Timestamp | Service | Purpose |
|------|-----------|---------|---------|
| `is_ingested` | `ingested_at` | Librarian | File moved and cataloged |
| `is_geocoded` | `geocoded_at` | (future) | Location enriched |
| `is_thumbnailed` | `thumbnailed_at` | (future) | Thumbnails generated |
| `is_curated` | `curated_at` | (future) | Manual/AI curation done |
| `is_backed_up` | `backed_up_at` | (future) | Cloud backup complete |
| `has_errors` | - | Any | Error during processing |

### Alternatives Considered
| Option | Pros | Cons |
|--------|------|------|
| Single status enum | Simple | Can't track partial progress |
| Separate status table | Normalized | Join overhead |
| Message queue | Decoupled | Infrastructure complexity |

### Consequences
- Each service knows exactly what to process
- Dashboard shows pipeline visualization
- Easy to add new stages

---

## ADR-006: PyExifTool over FFmpeg for Metadata

**Date:** 2024-12-28  
**Status:** Accepted  
**Author:** Initial Architecture

### Context
Need to extract metadata from images, videos, and RAW files.

### Decision
Use PyExifTool (Python wrapper for `exiftool`) as primary extraction tool.

### Rationale
- **Comprehensive:** Handles images, videos, RAW (CR2, NEF, etc.)
- **Industry Standard:** ExifTool is the de-facto metadata tool
- **Python API:** Clean integration via PyExifTool package
- **Fallback Chain:** PIL/Pillow for images, file mtime as last resort

### Extraction Priority
1. **PyExifTool** - Comprehensive (all file types)
2. **PIL/Pillow** - Fast fallback (images only)
3. **File mtime** - Last resort

### Date Tags (Priority Order)
1. `EXIF:DateTimeOriginal` (most accurate)
2. `EXIF:CreateDate`
3. `QuickTime:CreateDate` (videos)
4. `XMP:DateCreated`
5. `IPTC:DateCreated`
6. `File:FileModifyDate` (fallback)

### Alternatives Considered
| Option | Pros | Cons |
|--------|------|------|
| FFmpeg/FFprobe | Video-focused | Not ideal for images/RAW |
| PIL only | Fast, simple | Images only, limited tags |
| ExifRead | Pure Python | Less comprehensive |

### Consequences
- `libimage-exiftool-perl` installed in Docker
- FFmpeg NOT needed for metadata (can add later for transcoding)
- Reliable extraction across all file types

---

## ADR-007: Dual Heartbeat Strategy

**Date:** 2024-12-28  
**Status:** Accepted  
**Author:** Architecture Review

### Context
Need to track service health for both real-time display and historical analysis.

### Decision
Combine Docker API (real-time) with database heartbeats (historical).

### Rationale
- **Real-time:** Docker knows immediately if container is running
- **Historical:** Database tracks trends, detects patterns
- **Separation:** Real-time = Docker, Historical = Database
- **Flexible Intervals:** Different services can have different intervals

### Implementation
| Source | Purpose | Latency |
|--------|---------|---------|
| Docker API | Container running/healthy | Immediate |
| `system_status` | Current heartbeat | Seconds |
| `system_status_history` | Trend analysis | Minutes/Hours |

### Heartbeat Intervals
| Service | Interval | Rationale |
|---------|----------|-----------|
| librarian | 60s | Actively processing files |
| dashboard | 5min | Just needs to be alive |
| factory-db | 5min | Stable infrastructure |
| syncthing | 5min | Stable infrastructure |

### Consequences
- Dashboard polls Docker for immediate status
- Heartbeat thread in each service updates database
- Historical data enables uptime calculations

---

## ADR-008: Multi-Stage Docker Builds with Test Gate

**Date:** 2024-12-28  
**Status:** Accepted  
**Author:** Initial Architecture

### Context
Need to ensure code quality before deployment.

### Decision
Use multi-stage Docker builds where Stage 1 runs pytest and fails build if tests fail.

### Rationale
- **Build Gate:** Bad code cannot become a container
- **Fast Feedback:** Tests run during `docker build`
- **Minimal Runtime:** Production image has no test dependencies
- **CI/CD Ready:** Same pattern works in pipelines

### Dockerfile Structure
```dockerfile
# Stage 1: Builder
FROM python:3.11-slim-bookworm AS builder
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY Src/ ./Src/
RUN pytest Src/*/tests/ -v  # FAILS BUILD IF TESTS FAIL

# Stage 2: Runtime
FROM python:3.11-slim-bookworm
COPY --from=builder /app/Src ./Src
CMD ["python", "-m", "Src.Service.main"]
```

### Consequences
- Every `docker build` runs tests
- Slower builds but guaranteed quality
- Tests must be fast for reasonable build times

---

**END OF DECISION LOG**

