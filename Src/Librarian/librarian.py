"""
Librarian Ingest Service - Main entry point.

Watches Photos_Inbox and organizes files into Storage/Originals/{YYYY}/{YYYY-MM-DD}/
"""
import logging
import shutil
import signal
import sys
from datetime import datetime
from pathlib import Path

from Src.Shared.database import get_db_session, init_database, check_database_connection
from Src.Shared.models import MediaAsset

from .collision_handler import (
    calculate_file_hash,
    check_duplicate_in_date_folder,
    handle_collision,
)
from .file_watcher import FileWatcher
from .heartbeat import HeartbeatService
from .metadata_extractor import extract_metadata, get_date_path_components
from .utils import (
    ensure_directory_exists,
    get_storage_path,
    setup_logging,
    should_process_file,
)

logger = logging.getLogger("librarian")


class LibrarianService:
    """
    Main service that orchestrates file watching and organization.
    """
    
    def __init__(
        self,
        stability_delay: float = 5.0,
        min_file_age: float = 2.0,
        log_level: str = "INFO",
        periodic_scan_interval: float = 60.0,
        heartbeat_interval: float = 60.0
    ):
        """
        Initialize Librarian service.
        
        Args:
            stability_delay: Seconds to wait after file modification before processing
            min_file_age: Minimum age of file before considering it stable
            log_level: Logging level
            periodic_scan_interval: Seconds between periodic scans (fallback for missed files)
            heartbeat_interval: Seconds between heartbeat updates (default: 60s = 1 minute)
        """
        self.log_level = log_level
        setup_logging(log_level)
        
        # Initialize database
        logger.info("Initializing database...")
        try:
            init_database()
            if check_database_connection():
                logger.info("Database connection successful")
            else:
                logger.warning("Database connection check failed, but continuing...")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}", exc_info=True)
            logger.warning("Continuing without database (files will still be processed)")
        
        self.storage_path = get_storage_path()
        ensure_directory_exists(self.storage_path)
        
        # Initialize heartbeat service
        self.heartbeat = HeartbeatService(service_name="librarian", interval=heartbeat_interval)
        
        self.file_watcher = FileWatcher(
            self.process_file,
            stability_delay=stability_delay,
            min_file_age=min_file_age,
            periodic_scan_interval=periodic_scan_interval
        )
        
        self.running = False
    
    def process_file(self, file_path: Path) -> None:
        """
        Process a single file from the inbox.
        
        Args:
            file_path: Path to file in Photos_Inbox
        """
        # Safety check: apply deny list filter
        if not should_process_file(file_path):
            logger.debug(f"Skipping file (deny list): {file_path.name}")
            return
        
        logger.info(f"Processing file: {file_path.name}")
        
        # Update heartbeat with current task
        self.heartbeat.set_current_task(f"Processing {file_path.name}")
        
        try:
            # Extract comprehensive metadata (date and location)
            metadata = extract_metadata(file_path)
            date_taken = metadata.get("captured_at")
            location = metadata.get("location")
            
            if not date_taken:
                logger.error(f"Could not extract date from {file_path.name}")
                self.heartbeat.set_current_task(None)
                return
            
            # Get destination path components
            year, date_folder = get_date_path_components(date_taken)
            destination_dir = self.storage_path / year / date_folder
            ensure_directory_exists(destination_dir)
            
            # Calculate file hash
            file_hash = calculate_file_hash(file_path)
            if not file_hash:
                logger.error(f"Could not calculate hash for {file_path.name}")
                return
            
            # Determine destination filename
            destination_file = destination_dir / file_path.name
            
            # Handle collisions and duplicates
            should_move, final_destination, reason = handle_collision(
                file_path,
                destination_file,
                file_hash
            )
            
            if not should_move:
                # True duplicate - delete from inbox (Option A)
                logger.info(f"Skipping duplicate: {file_path.name} - {reason}")
                try:
                    file_path.unlink()
                    logger.info(f"Deleted duplicate from inbox: {file_path.name}")
                except OSError as e:
                    logger.error(f"Failed to delete duplicate {file_path.name}: {e}")
                return
            
            # Check for duplicate in entire date folder (not just same filename)
            existing_duplicate = check_duplicate_in_date_folder(
                destination_dir,
                file_hash,
                exclude_path=final_destination
            )
            
            if existing_duplicate:
                # Duplicate found elsewhere in date folder
                logger.info(
                    f"Duplicate found in date folder: {file_path.name} "
                    f"matches {existing_duplicate.name}"
                )
                try:
                    file_path.unlink()
                    logger.info(f"Deleted duplicate from inbox: {file_path.name}")
                except OSError as e:
                    logger.error(f"Failed to delete duplicate {file_path.name}: {e}")
                return
            
            # Move file to destination
            if final_destination:
                try:
                    # Ensure parent directory exists
                    ensure_directory_exists(final_destination.parent)
                    
                    # Verify source file exists before moving
                    if not file_path.exists():
                        logger.error(f"Source file does not exist: {file_path}")
                        return
                    
                    # Move file (use shutil.move for cross-device support)
                    # shutil.move handles both same-filesystem (rename) and cross-device (copy+delete) moves
                    shutil.move(str(file_path), str(final_destination))
                    logger.info(
                        f"Moved file: {file_path.name} -> {final_destination}"
                    )
                    if reason != "No collision":
                        logger.info(f"Reason: {reason}")
                    
                    # Write to database (after successful move)
                    # If DB fails, log error but don't lose the file (already moved)
                    try:
                        self._write_to_database(
                            file_hash=file_hash,
                            original_name=file_path.name,
                            original_path=str(file_path),
                            final_path=str(final_destination),
                            size_bytes=final_destination.stat().st_size,
                            captured_at=date_taken,
                            location=location
                        )
                    except Exception as db_error:
                        logger.error(
                            f"Failed to write {file_path.name} to database: {db_error}",
                            exc_info=True
                        )
                        # Don't fail the entire operation - file is already moved
                
                except OSError as e:
                    logger.error(f"Failed to move file {file_path.name}: {e}", exc_info=True)
                    raise  # Re-raise to see the error in tests
        
        except Exception as e:
            logger.error(f"Error processing file {file_path.name}: {e}", exc_info=True)
            self.heartbeat.set_status("ERROR")
        finally:
            # Clear current task
            self.heartbeat.set_current_task(None)
            self.heartbeat.set_status("OK")
    
    def _write_to_database(
        self,
        file_hash: str,
        original_name: str,
        original_path: str,
        final_path: str,
        size_bytes: int,
        captured_at: datetime,
        location: dict = None
    ):
        """
        Write media asset to database.
        
        Sets is_ingested = True since Librarian has successfully processed the file.
        """
        """
        Write media asset to database.
        
        Args:
            file_hash: SHA256 hash of file
            original_name: Original filename
            original_path: Full path in Photos_Inbox
            final_path: Full path in Storage/Originals
            size_bytes: File size in bytes
            captured_at: Date taken from metadata
            location: GPS coordinates dict or None
        """
        try:
            with get_db_session() as session:
                # Check if asset already exists (by hash)
                existing = session.query(MediaAsset).filter(
                    MediaAsset.file_hash == file_hash
                ).first()
                
                if existing:
                    logger.debug(f"Asset already in database: {file_hash[:8]}...")
                    return
                
                # Create new asset record
                asset = MediaAsset(
                    file_hash=file_hash,
                    original_name=original_name,
                    original_path=original_path,
                    final_path=final_path,
                    size_bytes=size_bytes,
                    captured_at=captured_at,
                    location=location
                )
                
                session.add(asset)
                session.commit()
                logger.debug(f"Asset written to database: {original_name}")
        
        except Exception as e:
            logger.error(f"Database write failed: {e}", exc_info=True)
            raise
    
    def start(self):
        """Start the service."""
        if self.running:
            logger.warning("Service is already running")
            return
        
        logger.info("Starting Librarian Ingest Service...")
        logger.info(f"Storage path: {self.storage_path}")
        
        self.running = True
        
        # Start heartbeat service
        self.heartbeat.start()
        
        # Start file watcher
        self.file_watcher.start()
        
        # Process any existing files
        self.file_watcher.process_existing_files()
        
        logger.info("Librarian service started. Press Ctrl+C to stop.")
    
    def stop(self):
        """Stop the service."""
        if not self.running:
            return
        
        logger.info("Stopping Librarian service...")
        self.running = False
        
        # Stop file watcher
        self.file_watcher.stop()
        
        # Stop heartbeat service
        self.heartbeat.stop()
        
        logger.info("Librarian service stopped.")
    
    def run(self):
        """Run the service until interrupted."""
        # Set up signal handlers
        def signal_handler(sig, frame):
            logger.info("Received interrupt signal")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            self.start()
            
            # Keep running
            while self.running:
                import time
                time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Librarian Ingest Service - Organize photos by date"
    )
    parser.add_argument(
        "--stability-delay",
        type=float,
        default=5.0,
        help="Seconds to wait after file modification before processing (default: 5.0)"
    )
    parser.add_argument(
        "--min-file-age",
        type=float,
        default=2.0,
        help="Minimum age of file before considering stable (default: 2.0)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--periodic-scan-interval",
        type=float,
        default=60.0,
        help="Seconds between periodic scans (default: 60.0)"
    )
    
    args = parser.parse_args()
    
    service = LibrarianService(
        stability_delay=args.stability_delay,
        min_file_age=args.min_file_age,
        log_level=args.log_level,
        periodic_scan_interval=args.periodic_scan_interval
    )
    
    service.run()


if __name__ == "__main__":
    main()

