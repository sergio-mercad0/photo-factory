"""
Database cleanup utilities for Photo Factory.

Provides functions to clean up old historical data according to retention policies.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text

from .database import get_db_session

logger = logging.getLogger("shared.cleanup")


def cleanup_system_status_history(retention_days: int = 60) -> int:
    """
    Clean up old records from system_status_history table.
    
    Deletes records older than the specified retention period.
    
    Args:
        retention_days: Number of days to retain (default: 60)
    
    Returns:
        Number of records deleted
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        with get_db_session() as session:
            # Delete old records
            result = session.execute(
                text("""
                    DELETE FROM system_status_history
                    WHERE heartbeat_timestamp < :cutoff_date
                """),
                {"cutoff_date": cutoff_date}
            )
            deleted_count = result.rowcount
            session.commit()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old system_status_history records (older than {retention_days} days)")
            else:
                logger.debug(f"No old system_status_history records to clean up (retention: {retention_days} days)")
            
            return deleted_count
    
    except Exception as e:
        logger.error(f"Failed to cleanup system_status_history: {e}", exc_info=True)
        return 0


def get_history_record_count(service_name: Optional[str] = None) -> int:
    """
    Get count of records in system_status_history table.
    
    Args:
        service_name: Optional service name to filter by
    
    Returns:
        Number of records
    """
    try:
        with get_db_session() as session:
            if service_name:
                result = session.execute(
                    text("SELECT COUNT(*) FROM system_status_history WHERE service_name = :service_name"),
                    {"service_name": service_name}
                )
            else:
                result = session.execute(text("SELECT COUNT(*) FROM system_status_history"))
            
            count = result.scalar()
            return count if count is not None else 0
    
    except Exception as e:
        logger.error(f"Failed to get history record count: {e}", exc_info=True)
        return 0

