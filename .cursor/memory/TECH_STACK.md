# Tech Stack

**Last Updated:** 2026-01-03  
**Purpose:** Technology choices for Photo Factory

---

## Core Language & Runtime

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11 | Primary language for all services |
| **Docker** | Compose v2 | Container orchestration |

---

## Container Infrastructure

### Docker Services (docker-compose.yml)

| Service | Image/Build | Purpose | Port |
|---------|-------------|---------|------|
| **factory-db** | `postgres:15-alpine` | Photo Factory database (metadata, heartbeats) | 5432 (internal) |
| **librarian** | Custom Dockerfile | Photo ingestion & organization | - |
| **dashboard** | Custom Dockerfile | Streamlit monitoring UI | 8501 |
| **syncthing** | `syncthing/syncthing:1.27` | File synchronization from devices | 8384, 22000 |
| **service-monitor** | Custom Dockerfile | Infrastructure heartbeat tracking | - |
| **immich-server** | `ghcr.io/immich-app/immich-server` | Photo gallery & management | 2283 |
| **immich-machine-learning** | `ghcr.io/immich-app/immich-machine-learning:*-cuda` | ML inference (face detection, etc.) | - |
| **database** | `tensorchord/pgvecto-rs:pg14-v0.2.0` | Immich database (with vector support) | - |
| **redis** | `redis:6.2-alpine` | Immich cache | - |
| **homepage** | `ghcr.io/gethomepage/homepage:latest` | Dashboard homepage | 3000 |

### Custom Docker Images

All custom images use **multi-stage builds** with:
1. **Builder Stage:** Install deps, copy code, run `pytest` (build gate)
2. **Runtime Stage:** Minimal image with only production code

Base Image: `python:3.11-slim-bookworm`

---

## Python Dependencies (requirements.txt)

### File Operations
| Package | Version | Purpose |
|---------|---------|---------|
| **watchdog** | ≥3.0.0 | File system event monitoring |
| **Pillow** | ≥10.0.0 | Image processing & EXIF extraction (fallback) |
| **PyExifTool** | ≥0.5.0 | Comprehensive metadata extraction (images, videos, RAW) |

### Database
| Package | Version | Purpose |
|---------|---------|---------|
| **sqlalchemy** | ≥2.0.0 | ORM and database abstraction |
| **psycopg2-binary** | ≥2.9.0 | PostgreSQL adapter |

### Dashboard
| Package | Version | Purpose |
|---------|---------|---------|
| **streamlit** | ≥1.28.0 | Web-based monitoring dashboard |
| **pandas** | ≥2.0.0 | Data manipulation for dashboard |
| **streamlit-autorefresh** | ≥0.0.6 | Auto-refresh component |
| **docker** | ≥6.1.0 | Docker API for container status |

### Testing
| Package | Version | Purpose |
|---------|---------|---------|
| **pytest** | ≥7.0.0 | Testing framework |

---

## External Tools

| Tool | Installed In | Purpose |
|------|--------------|---------|
| **exiftool** | Docker (libimage-exiftool-perl) | Metadata extraction (primary) |
| **postgresql-client** | Docker | Database health checks |

---

## Database Technology

### Photo Factory Database (factory-db)
- **Engine:** PostgreSQL 15 (Alpine)
- **ORM:** SQLAlchemy 2.0
- **Features:** 
  - JSONB for flexible location data
  - Server-side timestamps
  - Composite indexes for performance

### Immich Database (database)
- **Engine:** PostgreSQL 14 with pgvecto.rs extension
- **Purpose:** Vector embeddings for ML features
- **Separate from:** Photo Factory database

---

## Storage Architecture

| Path | Purpose | Docker Mount |
|------|---------|--------------|
| `Photos_Inbox/` | Drop zone for incoming files | ✅ Mounted to Librarian & Syncthing |
| `Storage/Originals/` | Organized immutable originals | ✅ Mounted to Librarian |
| `Storage/Derivatives/` | Processed/gallery files (future) | - |
| `Stack/App_Data/` | Docker configs, DB data, .env | ✅ Various services |

---

## Networking

| Port | Service | Protocol |
|------|---------|----------|
| 8501 | Dashboard | HTTP |
| 8384 | Syncthing Web UI | HTTP |
| 22000 | Syncthing Sync | TCP/UDP |
| 21027 | Syncthing Discovery | UDP |
| 2283 | Immich Server | HTTP |
| 3000 | Homepage | HTTP |

---

## Version Pinning Policy

Per `.cursorrules`:
- **NEVER** use `:latest` for Docker images
- Always pin to specific versions (e.g., `postgres:15-alpine`, `syncthing/syncthing:1.27`)
- Python packages use `>=X.Y.Z` for flexibility with major version bounds

---

## GPU Support

| Service | GPU Usage |
|---------|-----------|
| immich-server | NVIDIA GPU (CUDA) |
| immich-machine-learning | NVIDIA GPU (CUDA) |

Configured via Docker `deploy.resources.reservations.devices`.

---

**END OF TECH STACK**

