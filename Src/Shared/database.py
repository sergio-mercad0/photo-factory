"""
Database connection and session management using SQLAlchemy.
"""
import logging
import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

logger = logging.getLogger("shared.database")

# Database connection string from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(
        user=os.getenv("DB_USERNAME", "photo_factory"),
        password=os.getenv("DB_PASSWORD", "photo_factory"),
        host=os.getenv("DB_HOST", "factory-db"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_DATABASE_NAME", "photo_factory"),
    ),
)

# Engine configuration
# Use NullPool for single-threaded services, QueuePool for multi-threaded
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        # Use QueuePool for connection pooling (better for concurrent access)
        _engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            echo=False,  # Set to True for SQL debugging
        )
        logger.info(f"Database engine created for {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'database'}")
    return _engine


def get_session_factory():
    """Get or create the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Usage:
        with get_db_session() as session:
            # Use session
            session.commit()
    """
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database():
    """
    Initialize database tables.
    
    Creates tables if they don't exist (simple migration strategy).
    Should be called on service startup.
    """
    from .models import Base
    
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

