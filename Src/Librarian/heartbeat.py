"""
Heartbeat service for Librarian.

Updates system_status table periodically to report service health.
"""
import logging
import threading
import time
from typing import Optional

from Src.Shared.database import get_db_session
from Src.Shared.models import SystemStatus

logger = logging.getLogger("librarian.heartbeat")


class HeartbeatService:
    """
    Service that periodically updates system_status table with heartbeat.
    
    Runs in a separate thread and updates the database every interval seconds.
    """
    
    def __init__(self, service_name: str = "librarian", interval: float = 60.0):
        """
        Initialize heartbeat service.
        
        Args:
            service_name: Name of the service (for system_status table)
            interval: Seconds between heartbeats (default: 60 seconds = 1 minute)
        """
        self.service_name = service_name
        self.interval = interval
        self.current_task: Optional[str] = None
        self.status = "OK"
        
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
    
    def set_current_task(self, task: Optional[str]):
        """Update the current task description."""
        self.current_task = task
    
    def set_status(self, status: str):
        """Update the service status (OK, ERROR, WARNING)."""
        self.status = status
    
    def _update_heartbeat(self):
        """Update heartbeat in database."""
        try:
            with get_db_session() as session:
                # Get or create system_status record
                status_record = session.query(SystemStatus).filter(
                    SystemStatus.service_name == self.service_name
                ).first()
                
                if not status_record:
                    status_record = SystemStatus(service_name=self.service_name)
                    session.add(status_record)
                
                # Update fields
                from datetime import datetime
                status_record.status = self.status
                status_record.current_task = self.current_task
                status_record.last_heartbeat = datetime.now()  # Explicitly update heartbeat timestamp
                
                session.commit()
                logger.debug(f"Heartbeat updated: {self.service_name} - {self.status}")
        
        except Exception as e:
            logger.error(f"Failed to update heartbeat: {e}", exc_info=True)
    
    def _heartbeat_loop(self):
        """Main heartbeat loop (runs in thread)."""
        logger.info(f"Heartbeat service started (interval: {self.interval}s)")
        
        while not self._stop_event.is_set():
            try:
                self._update_heartbeat()
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}", exc_info=True)
            
            # Wait for next interval (or stop if event is set)
            self._stop_event.wait(self.interval)
        
        logger.info("Heartbeat service stopped")
    
    def start(self):
        """Start the heartbeat service."""
        if self._running:
            logger.warning("Heartbeat service is already running")
            return
        
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()
        logger.info("Heartbeat service started")
    
    def stop(self):
        """Stop the heartbeat service."""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=5.0)
        
        logger.info("Heartbeat service stopped")

