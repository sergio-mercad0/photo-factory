# Lessons Learned

**Last Updated:** 2026-01-03  
**Purpose:** Technical patterns, gotchas, and operational wisdom discovered during development

---

## Development Patterns

### 1. Path Resolution Pattern

**Pattern:** Always use `pathlib.Path` relative to `__file__`

```python
# ✅ CORRECT - Portable across systems
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent.parent
STORAGE_PATH = BASE_DIR / "Storage" / "Originals"

# ❌ WRONG - Breaks on different machines
STORAGE_PATH = Path("D:/Photo_Factory/Storage/Originals")
```

**Why:** Absolute paths break when project is moved or run on different systems. Relative paths from `__file__` work everywhere.

---

### 2. SQLAlchemy Session Context Manager

**Pattern:** Always use context manager for database sessions

```python
# ✅ CORRECT - Session automatically closed
with get_db_session() as session:
    result = session.query(Model).all()
    # Process result while session is open

# ❌ WRONG - Session may leak
session = get_db_session()
result = session.query(Model).all()
# Forgot to close session
```

**Why:** Context manager ensures session cleanup even on exceptions. Prevents connection pool exhaustion.

---

### 3. Detached Instance Pattern (Streamlit/SQLAlchemy)

**Pattern:** Convert ORM objects to dicts before returning from cached functions

```python
# ✅ CORRECT - Returns dict, works after session closes
@st.cache_data(ttl=5)
def get_recent_assets(limit: int = 10):
    with get_db_session() as session:
        assets = session.query(MediaAsset).limit(limit).all()
        return [
            {
                "id": str(asset.id),
                "original_name": asset.original_name,
                "ingested_at": asset.ingested_at,
            }
            for asset in assets
        ]

# ❌ WRONG - Returns ORM objects, causes DetachedInstanceError
@st.cache_data(ttl=5)
def get_recent_assets(limit: int = 10):
    with get_db_session() as session:
        return session.query(MediaAsset).limit(limit).all()
```

**Why:** SQLAlchemy ORM objects are bound to their session. After session closes, accessing attributes raises `DetachedInstanceError`.

---

### 4. Heartbeat Freshness Calculation

**Pattern:** Always calculate time since heartbeat using current time, not preserved timestamps

```python
# ✅ CORRECT - Fresh calculation
time_since = datetime.now() - heartbeat["last_heartbeat"]
seconds_ago = int(time_since.total_seconds())

# ❌ WRONG - Stale if cached
cached_age = heartbeat["seconds_ago"]  # Gets stale immediately
```

**Why:** Dashboard auto-refreshes every few seconds. If time calculation is cached, the "seconds ago" value becomes stale.

---

### 5. Docker Multi-Stage Build Pattern

**Pattern:** Use multi-stage builds with test gate in builder stage

```dockerfile
# Stage 1: Builder (runs tests)
FROM python:3.11-slim-bookworm AS builder
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY Src/ ./Src/
RUN pytest Src/*/tests/ -v  # Build fails if tests fail

# Stage 2: Runtime (minimal image)
FROM python:3.11-slim-bookworm
COPY --from=builder /app/Src ./Src
CMD ["python", "-m", "Src.Service.main"]
```

**Why:** Ensures no broken code gets containerized. Tests run during build, not runtime.

---

### 6. Health Check Simplicity Pattern

**Pattern:** Health checks should be lightweight process checks, not comprehensive tests

```yaml
# ✅ CORRECT - Lightweight
healthcheck:
  test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
  interval: 2m

# ❌ WRONG - Too heavy for health checks
healthcheck:
  test: ["CMD", "pytest", "tests/", "-v"]
  interval: 30s
```

**Why:** Health checks run frequently. Heavy checks consume resources and may cause false negatives under load.

---

## Operational Gotchas

### 1. Syncthing Configuration Directory

**Gotcha:** Syncthing creates `config.xml` on first run. Don't commit it to git.

**Solution:** Add `syncthing_config/` contents to `.gitignore` (except structure).

---

### 2. PostgreSQL Data Directory Permissions

**Gotcha:** Windows Docker volumes may have permission issues with PostgreSQL.

**Solution:** Use named volumes or ensure directory permissions are correct before first run.

---

### 3. Streamlit Reruns Everything

**Gotcha:** Streamlit reruns the entire script on every interaction.

**Solution:** 
- Use `@st.cache_data` for data functions
- Use `@st.cache_resource` for persistent objects (like heartbeat service)
- Store state in `st.session_state`

---

### 4. File Watcher Stability Delay

**Gotcha:** Files being synced may be incomplete when detected.

**Solution:** Wait for file to be stable (unchanged for N seconds) before processing.

```python
# Wait for file stability
STABILITY_DELAY = 5.0  # seconds
MIN_FILE_AGE = 2.0  # seconds
```

---

### 5. Cross-Device File Moves

**Gotcha:** `Path.rename()` fails across different drives/devices.

**Solution:** Use `shutil.move()` which handles copy+delete for cross-device moves.

```python
# ✅ CORRECT - Works across devices
shutil.move(str(source), str(destination))

# ❌ WRONG - Fails if different drives
source.rename(destination)
```

---

### 6. Docker Compose Build Context

**Gotcha:** Docker build context must include all needed files. Relative imports may fail.

**Solution:** Set build context to project root, not service directory.

```yaml
# ✅ CORRECT
librarian:
  build:
    context: ../../  # Project root
    dockerfile: Src/Librarian/Dockerfile

# ❌ WRONG
librarian:
  build:
    context: .  # Only service directory
    dockerfile: Dockerfile
```

---

## Testing Patterns

### 1. Sandbox Testing Rule

**Pattern:** Tests NEVER touch real `Photos_Inbox` or `Storage`

```python
# ✅ CORRECT - Uses tmp_path fixture
def test_file_processing(tmp_path):
    inbox = tmp_path / "inbox"
    storage = tmp_path / "storage"
    inbox.mkdir()
    storage.mkdir()
    # Test with temporary directories

# ❌ WRONG - Touches real directories
def test_file_processing():
    inbox = Path("Photos_Inbox")  # NEVER
```

---

### 2. Database Mocking Pattern

**Pattern:** Mock database for unit tests, use real DB for integration tests

```python
# Unit test - mock DB
@pytest.fixture
def mock_session():
    with patch("Src.Shared.database.get_db_session"):
        yield

# Integration test - real DB (in Docker)
@pytest.mark.integration
def test_with_database():
    # Runs in container with real PostgreSQL
```

---

## Performance Insights

### 1. Batch Processing vs Event-Driven

**Insight:** For large backlogs, batch processing is faster than event-driven.

**Pattern:** 
- Event-driven for real-time new files
- Periodic scan for catching missed files
- Batch mode for initial import

---

### 2. Hash Calculation Cost

**Insight:** SHA256 hashing large video files is slow.

**Pattern:** 
- Calculate hash once, store in database
- Use hash for duplicate detection
- Consider streaming hash for very large files

---

### 3. EXIF Extraction Cost

**Insight:** ExifTool subprocess is slower than PIL for simple images.

**Pattern:**
- ExifTool for comprehensive extraction (videos, RAW)
- PIL as fast fallback for common image formats
- File mtime as last resort

---

## Debugging Tips

### 1. Check Container Logs

```bash
docker logs librarian --tail 50 -f
```

### 2. Verify Database Connection

```bash
docker exec factory_postgres psql -U photo_factory -d photo_factory -c "SELECT 1;"
```

### 3. Check Heartbeats

```bash
docker exec factory_postgres psql -U photo_factory -d photo_factory -c "SELECT * FROM system_status;"
```

### 4. Force Container Restart

```bash
docker-compose restart librarian
```

### 5. Clear Streamlit Cache

Press 'C' in terminal or click "Clear Cache" in sidebar.

---

**END OF LESSONS LEARNED**

