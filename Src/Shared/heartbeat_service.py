"""
Shared heartbeat service for all Photo Factory services.

All services should use this to update system_status and system_status_history tables.
"""
import logging
import threading
import time
from datetime import datetime
from typing import Optional

from Src.Shared.database import get_db_session
from Src.Shared.models import SystemStatus, SystemStatusHistory

logger = logging.getLogger("shared.heartbeat")


class HeartbeatService:
    """
    Service that periodically updates system_status table with heartbeat.
    
    Writes to both:
    - system_status: Fast lookup table (updated in place)
    - system_status_history: Historical time-series (new row per heartbeat)
    
    Runs in a separate thread and updates the database every interval seconds.
    """
    
    def __init__(self, service_name: str, interval: float = 300.0):
        """
        Initialize heartbeat service.
        
        Args:
            service_name: Name of the service (for system_status table)
            interval: Seconds between heartbeats (default: 300 seconds = 5 minutes)
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
        """
        Update heartbeat in database.
        
        Writes to both:
        - system_status: Fast lookup table (updated in place)
        - system_status_history: Historical time-series (new row per heartbeat)
        """
        try:
            heartbeat_time = datetime.now()
            
            with get_db_session() as session:
                # 1. Update current status table (fast lookup for dashboard)
                status_record = session.query(SystemStatus).filter(
                    SystemStatus.service_name == self.service_name
                ).first()
                
                if not status_record:
                    status_record = SystemStatus(service_name=self.service_name)
                    session.add(status_record)
                
                status_record.status = self.status
                status_record.current_task = self.current_task
                status_record.last_heartbeat = heartbeat_time
                
                # 2. Insert historical record (time-series for analysis)
                history_record = SystemStatusHistory(
                    service_name=self.service_name,
                    status=self.status,
                    current_task=self.current_task,
                    heartbeat_timestamp=heartbeat_time
                )
                session.add(history_record)
                
                session.commit()
                logger.debug(f"Heartbeat updated: {self.service_name} - {self.status}")
        
        except Exception as e:
            logger.error(f"Failed to update heartbeat: {e}", exc_info=True)
    
    def _heartbeat_loop(self):
        """Main heartbeat loop (runs in thread)."""
        logger.info(f"Heartbeat service started for {self.service_name} (interval: {self.interval}s)")
        
        # Write initial heartbeat immediately (don't wait for first interval)
        try:
            self._update_heartbeat()
        except Exception as e:
            logger.error(f"Error writing initial heartbeat: {e}", exc_info=True)
        
        while not self._stop_event.is_set():
            # Wait for next interval (or stop if event is set)
            self._stop_event.wait(self.interval)
            
            # Check if we should stop (event might have been set during wait)
            if self._stop_event.is_set():
                break
            
            try:
                self._update_heartbeat()
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}", exc_info=True)
        
        logger.info(f"Heartbeat service stopped for {self.service_name}")
    
    def start(self):
        """Start the heartbeat service."""
        if self._running:
            logger.warning(f"Heartbeat service for {self.service_name} is already running")
            return
        
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()
        logger.info(f"Heartbeat service started for {self.service_name}")
    
    def stop(self):
        """Stop the heartbeat service."""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=5.0)
        
        logger.info(f"Heartbeat service stopped for {self.service_name}")

