"""
Standalone script to run database cleanup tasks.

Can be run manually or scheduled via cron/systemd.
"""
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from Src.Shared.cleanup import cleanup_system_status_history, get_history_record_count
from Src.Shared.database import init_database
from Src.Librarian.utils import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger("cleanup_script")


def main():
    """Run cleanup tasks."""
    logger.info("Starting database cleanup...")
    
    # Initialize database (ensures tables exist)
    init_database()
    
    # Get count before cleanup
    count_before = get_history_record_count()
    logger.info(f"Records in system_status_history before cleanup: {count_before}")
    
    # Run cleanup (60 day retention)
    deleted = cleanup_system_status_history(retention_days=60)
    
    # Get count after cleanup
    count_after = get_history_record_count()
    logger.info(f"Records in system_status_history after cleanup: {count_after}")
    logger.info(f"Deleted {deleted} old records")
    
    logger.info("Cleanup completed successfully")


if __name__ == "__main__":
    main()

