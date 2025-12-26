"""
Utility functions for path resolution and logging.
"""
import logging
from pathlib import Path
from typing import Optional

# Resolve project root relative to this file
# This file is at: Src/Librarian/utils.py
# Project root is: Src/Librarian/../../ = project root
_PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()


def get_project_root() -> Path:
    """Return the absolute path to the project root."""
    return _PROJECT_ROOT


def get_inbox_path() -> Path:
    """Return the absolute path to Photos_Inbox."""
    return _PROJECT_ROOT / "Photos_Inbox"


def get_storage_path() -> Path:
    """Return the absolute path to Storage/Originals."""
    return _PROJECT_ROOT / "Storage" / "Originals"


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("librarian")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger


def ensure_directory_exists(path: Path) -> None:
    """
    Create directory if it doesn't exist (idempotent).
    
    Args:
        path: Directory path to ensure exists
    """
    path.mkdir(parents=True, exist_ok=True)

