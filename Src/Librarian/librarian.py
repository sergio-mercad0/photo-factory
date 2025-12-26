"""
Librarian Ingest Service - Main entry point.

Watches Photos_Inbox and organizes files into Storage/Originals/{YYYY}/{YYYY-MM-DD}/
"""
import logging
import shutil
import signal
import sys
from pathlib import Path

from .collision_handler import (
    calculate_file_hash,
    check_duplicate_in_date_folder,
    handle_collision,
)
from .file_watcher import FileWatcher
from .metadata_extractor import extract_date_taken, get_date_path_components
from .utils import (
    ensure_directory_exists,
    get_storage_path,
    setup_logging,
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
        log_level: str = "INFO"
    ):
        """
        Initialize Librarian service.
        
        Args:
            stability_delay: Seconds to wait after file modification before processing
            min_file_age: Minimum age of file before considering it stable
            log_level: Logging level
        """
        self.log_level = log_level
        setup_logging(log_level)
        
        self.storage_path = get_storage_path()
        ensure_directory_exists(self.storage_path)
        
        self.file_watcher = FileWatcher(
            self.process_file,
            stability_delay=stability_delay,
            min_file_age=min_file_age
        )
        
        self.running = False
    
    def process_file(self, file_path: Path) -> None:
        """
        Process a single file from the inbox.
        
        Args:
            file_path: Path to file in Photos_Inbox
        """
        logger.info(f"Processing file: {file_path.name}")
        
        try:
            # Extract date taken
            date_taken = extract_date_taken(file_path)
            if not date_taken:
                logger.error(f"Could not extract date from {file_path.name}")
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
                
                except OSError as e:
                    logger.error(f"Failed to move file {file_path.name}: {e}", exc_info=True)
                    raise  # Re-raise to see the error in tests
        
        except Exception as e:
            logger.error(f"Error processing file {file_path.name}: {e}", exc_info=True)
    
    def start(self):
        """Start the service."""
        if self.running:
            logger.warning("Service is already running")
            return
        
        logger.info("Starting Librarian Ingest Service...")
        logger.info(f"Storage path: {self.storage_path}")
        
        self.running = True
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
        self.file_watcher.stop()
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
    
    args = parser.parse_args()
    
    service = LibrarianService(
        stability_delay=args.stability_delay,
        min_file_age=args.min_file_age,
        log_level=args.log_level
    )
    
    service.run()


if __name__ == "__main__":
    main()

