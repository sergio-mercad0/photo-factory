# Service Heartbeat Strategy

## Best Practice: Heartbeat Tracking for All Services

**Yes, it is best practice to add heartbeat tracking for all services** in the Photo Factory system. This provides:
- Complete observability across all services
- Historical data for troubleshooting
- Consistent monitoring approach
- Early detection of service failures

## Service Categories

### 1. Application Services (Built-in Heartbeat)

**Services that run Python code and can integrate heartbeat directly:**

- **librarian** ✅ (already implemented)
- **dashboard** ⚠️ (needs implementation)

**Implementation:** Use `HeartbeatService` class from `Src.Shared.heartbeat` (or create similar).

### 2. Infrastructure Services (Lightweight Heartbeat Scripts)

**Services that need external heartbeat monitoring:**

- **factory-db** (PostgreSQL) - Critical infrastructure
- **syncthing** - Critical for file ingestion
- **immich-server** (optional - external service)
- **immich-machine-learning** (optional - external service)
- **immich_postgres** (optional - external service)
- **immich_redis** (optional - external service)
- **homepage** (optional - external service)

**Implementation:** Create lightweight heartbeat scripts that:
- Check if service is running/healthy
- Update `system_status` and `system_status_history` tables
- Run periodically (every 5-10 minutes)

### 3. Heartbeat Requirements

**All heartbeats must:**
1. Write to `system_status` table (current state, fast lookup)
2. Write to `system_status_history` table (historical record)
3. Update every 5-10 minutes (configurable per service)
4. Include service name, status, and optional current_task
5. Handle database errors gracefully (don't crash if DB is down)

## Implementation Plan

### Phase 1: Application Services
1. ✅ Librarian (already done)
2. Add Dashboard heartbeat

### Phase 2: Critical Infrastructure
1. Add factory-db heartbeat script
2. Add syncthing heartbeat script

### Phase 3: Optional Services (Future)
- Add heartbeats for Immich services if needed
- Add homepage heartbeat if needed

## Service Name Mapping

| Container Name | Service Name (in DB) | Priority |
|----------------|---------------------|----------|
| `librarian` | `librarian` | ✅ Critical |
| `dashboard` | `dashboard` | ✅ Critical |
| `factory_postgres` | `factory-db` | ✅ Critical |
| `syncthing` | `syncthing` | ✅ Critical |
| `immich_server` | `immich-server` | ⚠️ Optional |
| `immich_machine_learning` | `immich-ml` | ⚠️ Optional |
| `immich_postgres` | `immich-db` | ⚠️ Optional |
| `immich_redis` | `immich-redis` | ⚠️ Optional |
| `homepage` | `homepage` | ⚠️ Optional |

## Heartbeat Script Template

For infrastructure services, create a simple script:

```python
# Src/Shared/heartbeat_monitor.py
"""
Generic heartbeat monitor for infrastructure services.

Can be used to monitor any service by checking if it's running/healthy.
"""
import time
import subprocess
from datetime import datetime
from Src.Shared.database import get_db_session
from Src.Shared.models import SystemStatus, SystemStatusHistory

def monitor_service(service_name: str, check_command: list, interval: float = 300.0):
    """
    Monitor a service and update heartbeat.
    
    Args:
        service_name: Name for system_status table
        check_command: Command to check service health (e.g., ["pg_isready", "-U", "photo_factory"])
        interval: Seconds between checks (default: 300 = 5 minutes)
    """
    while True:
        try:
            # Check if service is healthy
            result = subprocess.run(check_command, capture_output=True, timeout=5)
            is_healthy = result.returncode == 0
            
            status = "OK" if is_healthy else "ERROR"
            current_task = None
            
            # Update heartbeat
            heartbeat_time = datetime.now()
            with get_db_session() as session:
                # Update current status
                status_record = session.query(SystemStatus).filter(
                    SystemStatus.service_name == service_name
                ).first()
                
                if not status_record:
                    status_record = SystemStatus(service_name=service_name)
                    session.add(status_record)
                
                status_record.status = status
                status_record.current_task = current_task
                status_record.last_heartbeat = heartbeat_time
                
                # Add history record
                history_record = SystemStatusHistory(
                    service_name=service_name,
                    status=status,
                    current_task=current_task,
                    heartbeat_timestamp=heartbeat_time
                )
                session.add(history_record)
                session.commit()
        
        except Exception as e:
            # Log error but continue monitoring
            print(f"Error monitoring {service_name}: {e}")
        
        time.sleep(interval)
```

