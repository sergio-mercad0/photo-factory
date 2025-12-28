"""
SQLAlchemy models for Photo Factory database.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, BigInteger, Column, Integer, String, Text, TIMESTAMP, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class MediaAsset(Base):
    """
    Media asset ledger - tracks all processed files.
    
    This is the source of truth for what files have been ingested.
    """
    __tablename__ = "media_assets"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # File identification
    file_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA256 hex
    original_name = Column(String(512), nullable=False)
    original_path = Column(Text, nullable=False)  # Full path in Photos_Inbox
    final_path = Column(Text, nullable=False)  # Full path in Storage/Originals
    
    # File metadata
    size_bytes = Column(BigInteger, nullable=False)
    captured_at = Column(TIMESTAMP, nullable=True)  # True capture date from EXIF
    ingested_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    
    # Location (GPS coordinates only - immutable source of truth)
    location = Column(JSON, nullable=True)  # {"lat": float, "lon": float}
    
    # Timestamps
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_media_assets_captured_at", "captured_at"),
        Index("idx_media_assets_ingested_at", "ingested_at"),
    )
    
    def __repr__(self):
        return f"<MediaAsset(id={self.id}, file_hash={self.file_hash[:8]}..., name={self.original_name})>"


class SystemStatus(Base):
    """
    System heartbeat and status tracking.
    
    Services update this table periodically to report their status.
    Used for historical monitoring and dashboard visibility.
    """
    __tablename__ = "system_status"
    
    # Primary key
    service_name = Column(String(64), primary_key=True)  # e.g., "librarian", "dashboard"
    
    # Status information
    last_heartbeat = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
    status = Column(String(16), nullable=False, default="OK")  # "OK", "ERROR", "WARNING"
    current_task = Column(Text, nullable=True)  # What the service is currently doing
    
    # Timestamps
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemStatus(service={self.service_name}, status={self.status}, heartbeat={self.last_heartbeat})>"


class SystemStatusHistory(Base):
    """
    Historical time-series record of service heartbeats.
    
    Each heartbeat creates a new row, providing complete historical data
    for troubleshooting, uptime analysis, and trend detection.
    
    Records are automatically cleaned up after 60 days.
    """
    __tablename__ = "system_status_history"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Service identification
    service_name = Column(String(64), nullable=False, index=True)
    
    # Status information (snapshot at heartbeat time)
    status = Column(String(16), nullable=False)  # "OK", "ERROR", "WARNING"
    current_task = Column(Text, nullable=True)  # What the service was doing
    
    # Timestamp of this heartbeat
    heartbeat_timestamp = Column(TIMESTAMP, nullable=False, index=True)
    
    # Record creation timestamp
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    
    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_system_status_history_service_timestamp", "service_name", "heartbeat_timestamp"),
    )
    
    def __repr__(self):
        return f"<SystemStatusHistory(service={self.service_name}, status={self.status}, timestamp={self.heartbeat_timestamp})>"

