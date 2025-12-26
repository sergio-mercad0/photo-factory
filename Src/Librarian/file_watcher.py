"""
File watching with stability checks.
"""
import logging
import time
from pathlib import Path
from threading import Event, Thread
from typing import Callable, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from .utils import get_inbox_path

logger = logging.getLogger("librarian.file_watcher")


class StableFileHandler(FileSystemEventHandler):
    """
    Handle file system events with stability checks.
    
    Only processes files that have been stable (unchanged) for a specified duration.
    """
    
    def __init__(
        self,
        process_callback: Callable[[Path], None],
        stability_delay: float = 5.0,
        min_file_age: float = 2.0
    ):
        """
        Initialize stable file handler.
        
        Args:
            process_callback: Function to call when file is ready for processing
            stability_delay: Seconds to wait after last modification before processing
            min_file_age: Minimum age of file before considering it stable
        """
        super().__init__()
        self.process_callback = process_callback
        self.stability_delay = stability_delay
        self.min_file_age = min_file_age
        
        # Track files: {file_path: (file_mtime, registration_time)}
        self.pending_files: dict[Path, tuple[float, float]] = {}
        self.processing_files: set[Path] = set()
        
        # Thread for checking stability
        self._stop_event = Event()
        self._check_thread: Optional[Thread] = None
    
    def start(self):
        """Start the stability check thread."""
        self._stop_event.clear()
        if self._check_thread is None or not self._check_thread.is_alive():
            self._check_thread = Thread(target=self._stability_check_loop, daemon=True)
            self._check_thread.start()
            logger.info("Stable file handler started")
    
    def stop(self):
        """Stop the stability check thread."""
        self._stop_event.set()
        if self._check_thread:
            self._check_thread.join(timeout=5.0)
        logger.info("Stable file handler stopped")
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        self._register_file(file_path)
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        self._register_file(file_path)
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename."""
        if event.is_directory:
            return
        
        # New location after move
        file_path = Path(event.dest_path)
        self._register_file(file_path)
    
    def _register_file(self, file_path: Path):
        """Register a file for stability checking."""
        try:
            # Check if file exists and is readable
            if not file_path.exists() or not file_path.is_file():
                return
            
            # Skip if already processing
            if file_path in self.processing_files:
                return
            
            # Record current modification time and registration time
            mtime = file_path.stat().st_mtime
            registration_time = time.time()
            self.pending_files[file_path] = (mtime, registration_time)
            logger.info(f"Registered file for stability check: {file_path.name}")
        
        except (OSError, AttributeError) as e:
            logger.warning(f"Could not register file {file_path}: {e}")
    
    def _stability_check_loop(self):
        """Continuously check pending files for stability."""
        while not self._stop_event.is_set():
            current_time = time.time()
            stable_files = []
            
            # Check each pending file
            for file_path, (last_mtime, registration_time) in list(self.pending_files.items()):
                try:
                    # Check if file still exists
                    if not file_path.exists():
                        self.pending_files.pop(file_path, None)
                        continue
                    
                    # Get current modification time
                    current_mtime = file_path.stat().st_mtime
                    
                    # Check if file was modified since registration
                    if current_mtime != last_mtime:
                        # File was modified - update timestamp and reset registration time
                        new_registration = time.time()
                        self.pending_files[file_path] = (current_mtime, new_registration)
                        continue
                    
                    # File hasn't changed - check if it's stable
                    time_since_modification = current_time - current_mtime
                    time_since_registration = current_time - registration_time
                    
                    # Must be old enough (since last modification) and stable long enough (since registration)
                    if (time_since_modification >= self.min_file_age and
                        time_since_registration >= self.stability_delay):
                        # File is stable - mark for processing
                        stable_files.append(file_path)
                        self.pending_files.pop(file_path, None)
                        self.processing_files.add(file_path)
                
                except (OSError, AttributeError) as e:
                    logger.warning(f"Error checking stability for {file_path}: {e}")
                    self.pending_files.pop(file_path, None)
            
            # Process stable files
            for file_path in stable_files:
                try:
                    logger.info(f"File is stable, processing: {file_path.name}")
                    self.process_callback(file_path)
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}", exc_info=True)
                finally:
                    self.processing_files.discard(file_path)
            
            # Sleep before next check
            self._stop_event.wait(1.0)  # Check every second


class FileWatcher:
    """
    Watch Photos_Inbox directory for new files.
    
    Uses watchdog for real-time file system events, with periodic scanning
    as a fallback to catch any missed files.
    """
    
    def __init__(
        self,
        process_callback: Callable[[Path], None],
        stability_delay: float = 5.0,
        min_file_age: float = 2.0,
        periodic_scan_interval: float = 60.0
    ):
        """
        Initialize file watcher.
        
        Args:
            process_callback: Function to call when file is ready for processing
            stability_delay: Seconds to wait after last modification
            min_file_age: Minimum age of file before considering stable
            periodic_scan_interval: Seconds between periodic scans (fallback)
        """
        self.inbox_path = get_inbox_path()
        self.process_callback = process_callback
        self.stability_delay = stability_delay
        self.min_file_age = min_file_age
        self.periodic_scan_interval = periodic_scan_interval
        
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[StableFileHandler] = None
        self.scan_thread: Optional[Thread] = None
        self._stop_scan = Event()
    
    def start(self):
        """Start watching for files."""
        # Ensure inbox exists
        self.inbox_path.mkdir(parents=True, exist_ok=True)
        
        # Create event handler
        self.event_handler = StableFileHandler(
            self.process_callback,
            self.stability_delay,
            self.min_file_age
        )
        self.event_handler.start()
        
        # Create observer for real-time file system events
        self.observer = Observer()
        self.observer.schedule(self.event_handler, str(self.inbox_path), recursive=True)
        self.observer.start()
        
        # Start periodic scanning thread as fallback
        self._stop_scan.clear()
        self.scan_thread = Thread(target=self._periodic_scan_loop, daemon=True)
        self.scan_thread.start()
        
        logger.info(f"File watcher started on {self.inbox_path} (scan interval: {self.periodic_scan_interval}s)")
    
    def stop(self):
        """Stop watching for files."""
        # Stop periodic scanning
        self._stop_scan.set()
        if self.scan_thread:
            self.scan_thread.join(timeout=5.0)
        
        # Stop file system observer
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5.0)
        
        # Stop event handler
        if self.event_handler:
            self.event_handler.stop()
        
        logger.info("File watcher stopped")
    
    def process_existing_files(self):
        """Process any files already in the inbox."""
        if not self.inbox_path.exists():
            return
        
        logger.info("Processing existing files in inbox...")
        self._scan_and_register_files()
    
    def _scan_and_register_files(self):
        """Scan inbox directory and register all files for processing."""
        if not self.inbox_path.exists():
            return
        
        files_found = 0
        for file_path in self.inbox_path.rglob("*"):
            if file_path.is_file():
                # Register for stability check
                if self.event_handler:
                    self.event_handler._register_file(file_path)
                    files_found += 1
        
        if files_found > 0:
            logger.debug(f"Registered {files_found} file(s) from inbox scan")
    
    def _periodic_scan_loop(self):
        """Periodically scan inbox directory as fallback for missed files."""
        logger.info(f"Periodic scan thread started (interval: {self.periodic_scan_interval}s)")
        
        while not self._stop_scan.is_set():
            try:
                # Perform scan
                self._scan_and_register_files()
            except Exception as e:
                logger.error(f"Error during periodic scan: {e}", exc_info=True)
            
            # Wait for next scan interval
            self._stop_scan.wait(self.periodic_scan_interval)

