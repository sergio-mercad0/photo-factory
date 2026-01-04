"""
Migration script to add status tracking columns to media_assets table.

Run this once to add the new columns to existing databases.
"""
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from Src.Shared.database import get_db_session, init_database
from Src.Librarian.utils import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger("migration")


def migrate_add_status_columns():
    """Add status tracking columns to media_assets table."""
    logger.info("Starting migration: Add status columns to media_assets")
    
    # Initialize database (ensures tables exist)
    init_database()
    
    try:
        with get_db_session() as session:
            # Check if columns already exist
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'media_assets' AND column_name = 'is_ingested'
            """)
            result = session.execute(check_query).first()
            
            if result:
                logger.info("Status columns already exist. Migration not needed.")
                return
            
            logger.info("Adding status columns to media_assets table...")
            
            # Add status columns
            migration_sql = text("""
                ALTER TABLE media_assets
                ADD COLUMN IF NOT EXISTS is_ingested BOOLEAN DEFAULT TRUE,
                ADD COLUMN IF NOT EXISTS is_geocoded BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS is_thumbnailed BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS is_curated BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS is_backed_up BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS has_errors BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS error_message TEXT,
                ADD COLUMN IF NOT EXISTS geocoded_at TIMESTAMP,
                ADD COLUMN IF NOT EXISTS thumbnailed_at TIMESTAMP,
                ADD COLUMN IF NOT EXISTS curated_at TIMESTAMP,
                ADD COLUMN IF NOT EXISTS backed_up_at TIMESTAMP;
            """)
            
            session.execute(migration_sql)
            
            # Update existing records: set is_ingested = TRUE (they're already ingested)
            update_sql = text("""
                UPDATE media_assets 
                SET is_ingested = TRUE 
                WHERE is_ingested IS NULL;
            """)
            session.execute(update_sql)
            
            # Create indexes
            logger.info("Creating indexes for status columns...")
            index_sql = text("""
                CREATE INDEX IF NOT EXISTS idx_media_assets_is_geocoded ON media_assets(is_geocoded);
                CREATE INDEX IF NOT EXISTS idx_media_assets_is_backed_up ON media_assets(is_backed_up);
                CREATE INDEX IF NOT EXISTS idx_media_assets_has_errors ON media_assets(has_errors);
            """)
            session.execute(index_sql)
            
            session.commit()
            logger.info("Migration completed successfully!")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    migrate_add_status_columns()

