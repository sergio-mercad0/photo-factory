"""
Infrastructure service monitor for services that can't integrate heartbeat directly.

Monitors external services (PostgreSQL, Syncthing, etc.) and updates heartbeat tables.
"""
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from Src.Shared.heartbeat_service import HeartbeatService
from Src.Librarian.utils import setup_logging

logger = logging.getLogger("shared.infrastructure_monitor")


class InfrastructureMonitor:
    """
    Monitor infrastructure services and update heartbeat.
    
    Runs health check command and updates system_status based on result.
    """
    
    def __init__(self, service_name: str, check_command: List[str], interval: float = 300.0):
        """
        Initialize infrastructure monitor.
        
        Args:
            service_name: Name for system_status table
            check_command: Command to check service health (e.g., ["pg_isready", "-U", "photo_factory"])
            interval: Seconds between checks (default: 300 = 5 minutes)
        """
        self.service_name = service_name
        self.check_command = check_command
        self.heartbeat = HeartbeatService(service_name=service_name, interval=interval)
    
    def check_service_health(self) -> bool:
        """
        Check if service is healthy.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            result = subprocess.run(
                self.check_command,
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error checking {self.service_name}: {e}")
            return False
    
    def monitor_loop(self):
        """Main monitoring loop."""
        logger.info(f"Starting infrastructure monitor for {self.service_name}")
        self.heartbeat.start()
        
        try:
            while True:
                is_healthy = self.check_service_health()
                
                if is_healthy:
                    self.heartbeat.set_status("OK")
                    self.heartbeat.set_current_task("Service healthy")
                else:
                    self.heartbeat.set_status("ERROR")
                    self.heartbeat.set_current_task("Service check failed")
                
                # Wait for next check
                time.sleep(self.heartbeat.interval)
        
        except KeyboardInterrupt:
            logger.info(f"Stopping infrastructure monitor for {self.service_name}")
            self.heartbeat.stop()


def monitor_factory_db(interval: float = 300.0):
    """Monitor factory-db (PostgreSQL) service."""
    import os
    from Src.Shared.database import init_database
    
    # Initialize database
    init_database()
    
    db_user = os.getenv("FACTORY_DB_USER", "photo_factory")
    monitor = InfrastructureMonitor(
        service_name="factory-db",
        check_command=["pg_isready", "-U", db_user, "-h", "factory-db"],
        interval=interval
    )
    monitor.monitor_loop()


def monitor_syncthing(interval: float = 300.0):
    """Monitor Syncthing service."""
    from Src.Shared.database import init_database
    
    # Initialize database
    init_database()
    
    monitor = InfrastructureMonitor(
        service_name="syncthing",
        check_command=["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8384/"],
        interval=interval
    )
    monitor.monitor_loop()


if __name__ == "__main__":
    setup_logging()
    
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m Src.Shared.infrastructure_monitor <service_name>")
        print("Available services: factory-db, syncthing")
        sys.exit(1)
    
    service = sys.argv[1]
    if service == "factory-db":
        monitor_factory_db()
    elif service == "syncthing":
        monitor_syncthing()
    else:
        print(f"Unknown service: {service}")
        sys.exit(1)

