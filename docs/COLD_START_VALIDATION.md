# Cold Start Validation Procedure

This document describes the procedure for validating the Photo Factory system after a fresh Windows boot and Docker restart.

## Purpose

Verify that all services start correctly from a cold state, ensuring:
- Docker containers build and start properly
- Services connect to dependencies (database, Docker API)
- Health checks pass
- Dashboard displays correct data
- No manual intervention required

## Procedure

### 1. Prerequisites

- Windows system with Docker Desktop installed
- All services defined in `Stack/App_Data/docker-compose.yml`
- Environment variables configured in `Stack/App_Data/.env`

### 2. Cold Start Steps

**Option A: Full Cleanup (Recommended for true cold start test)**

1. **Clean up existing containers and images:**
   ```powershell
   cd D:\Photo_Factory\Stack\App_Data
   .\cleanup_for_cold_start.ps1
   ```
   - This script safely removes containers and images
   - **Data volumes are preserved** (database, Syncthing config, etc.)
   - You can choose to remove images for a full rebuild test

2. **Reboot Windows** (or ensure Docker Desktop is stopped)

3. **Start Docker Desktop**
   - Wait for Docker to fully start (whale icon in system tray)

4. **Navigate to docker-compose directory:**
   ```powershell
   cd D:\Photo_Factory\Stack\App_Data
   ```

5. **Build all services:**
   ```powershell
   docker-compose build
   ```
   - This will run tests during build (Build Gate Protocol)
   - All builds must succeed

6. **Start all services:**
   ```powershell
   docker-compose up -d
   ```

**Option B: Quick Restart (without cleanup)**

If you just want to test restart without full cleanup:

1. **Stop all services:**
   ```powershell
   cd D:\Photo_Factory\Stack\App_Data
   docker-compose down
   ```

2. **Restart Docker Desktop** (or reboot Windows)

3. **Start services:**
   ```powershell
   docker-compose up -d
   ```

6. **Wait for health checks:**
   ```powershell
   docker-compose ps
   ```
   - Wait until all services show "healthy" status
   - This may take 1-2 minutes for services with `start_period: 60s`

7. **Verify services are running:**
   ```powershell
   docker-compose ps
   ```
   - All services should show "Up" status
   - Health checks should show "healthy" (where applicable)

### 3. Validation Checklist

- [ ] **Database (factory-db):**
  - Container is running
  - Health check passes
  - Can connect: `docker exec factory_postgres psql -U photo_factory -d photo_factory -c "SELECT 1;"`

- [ ] **Librarian Service:**
  - Container is running
  - Health check passes
  - Logs show: "Librarian service started"
  - Heartbeat appears in database: `docker exec factory_postgres psql -U photo_factory -d photo_factory -c "SELECT * FROM system_status WHERE service_name='librarian';"`

- [ ] **Dashboard Service:**
  - Container is running
  - Health check passes
  - Accessible at: `http://localhost:8501` or `http://photo.server:8501`
  - Displays system overview
  - Shows services status
  - Database connection shows "🟢 Connected"
  - Docker status shows "🟢 Available"

- [ ] **Syncthing Service:**
  - Container is running
  - Health check passes
  - Accessible at: `http://localhost:8384`

- [ ] **Other Services:**
  - Immich services (if configured)
  - Homepage (if configured)
  - All show healthy status

### 4. Functional Tests

1. **Test Librarian Processing:**
   - Place a test file in `D:\Photo_Factory\Photos_Inbox\`
   - Wait 5-10 seconds
   - Verify file appears in `D:\Photo_Factory\Storage\Originals\{YYYY}\{YYYY-MM-DD}\`
   - Check dashboard shows updated asset count

2. **Test Dashboard Auto-refresh:**
   - Open dashboard
   - Set auto-refresh to 5 seconds
   - Verify page refreshes automatically
   - Verify heartbeat times update

3. **Test Service Logs:**
   - Select a service in dashboard
   - Verify logs are displayed
   - Verify logs update on refresh

### 5. Troubleshooting

**If services fail to start:**
- Check Docker Desktop is running
- Check `docker-compose logs <service>` for errors
- Verify `.env` file has correct values
- Check port conflicts: `netstat -ano | findstr :8501`

**If health checks fail:**
- Check service logs: `docker-compose logs <service>`
- Verify dependencies are running (e.g., database for librarian)
- Wait longer (some services have 60s start period)

**If dashboard shows errors:**
- Check database connection: `docker-compose logs dashboard`
- Check Docker API access: Verify `/var/run/docker.sock` is mounted
- Clear browser cache

## Expected Results

After a successful cold start:
- All services start automatically
- All health checks pass
- Dashboard displays correct data
- No manual intervention required
- System is ready for production use

## When to Run

- After major system changes
- After Windows updates
- Before deploying to production
- When troubleshooting startup issues
- As part of regular maintenance (monthly)

