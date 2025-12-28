"""
Unified service monitor for all infrastructure services.

Monitors factory-db, syncthing, and other infrastructure services.
"""
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from Src.Shared.database import get_db_session, init_database
from Src.Shared.models import SystemStatus, SystemStatusHistory
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("service_monitor")


def check_factory_db() -> bool:
    """Check if factory-db (PostgreSQL) is healthy."""
    try:
        db_user = os.getenv("FACTORY_DB_USER", "photo_factory")
        result = subprocess.run(
            ["pg_isready", "-U", db_user, "-h", "factory-db"],
            capture_output=True,
            timeout=5,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking factory-db: {e}")
        return False


def check_syncthing() -> bool:
    """Check if Syncthing is healthy."""
    try:
        result = subprocess.run(
            ["wget", "--no-verbose", "--tries=1", "--spider", "http://syncthing:8384/"],
            capture_output=True,
            timeout=5,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking syncthing: {e}")
        return False


def update_heartbeat(service_name: str, is_healthy: bool, current_task: str = None):
    """Update heartbeat for a service."""
    try:
        heartbeat_time = datetime.now()
        status = "OK" if is_healthy else "ERROR"
        
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
            
            logger.debug(f"Heartbeat updated: {service_name} - {status}")
    
    except Exception as e:
        logger.error(f"Failed to update heartbeat for {service_name}: {e}", exc_info=True)


def monitor_loop(interval: float = 300.0):
    """Main monitoring loop."""
    logger.info("Starting infrastructure service monitor")
    
    # Initialize database
    init_database()
    
    while True:
        try:
            # Monitor factory-db
            db_healthy = check_factory_db()
            update_heartbeat("factory-db", db_healthy, "Database check" if db_healthy else "Database check failed")
            
            # Monitor syncthing
            syncthing_healthy = check_syncthing()
            update_heartbeat("syncthing", syncthing_healthy, "Syncthing check" if syncthing_healthy else "Syncthing check failed")
            
        except KeyboardInterrupt:
            logger.info("Stopping service monitor")
            break
        except Exception as e:
            logger.error(f"Error in monitor loop: {e}", exc_info=True)
        
        time.sleep(interval)


if __name__ == "__main__":
    interval = float(os.getenv("MONITOR_INTERVAL", "300.0"))
    monitor_loop(interval)

