"""
Extract metadata (Date Taken) from media files.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, DATETIME_ORIGINAL
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def extract_date_taken(file_path: Path) -> Optional[datetime]:
    """
    Extract Date Taken from media file.
    
    Priority:
    1. EXIF DateTimeOriginal (for images)
    2. EXIF DateTime (for images)
    3. File modification time (fallback)
    
    Args:
        file_path: Path to the media file
    
    Returns:
        datetime object or None if extraction fails
    """
    # Try EXIF extraction for images
    if PIL_AVAILABLE:
        date_taken = _extract_exif_date(file_path)
        if date_taken:
            return date_taken
    
    # Fallback to file modification time
    try:
        mtime = file_path.stat().st_mtime
        return datetime.fromtimestamp(mtime)
    except (OSError, ValueError) as e:
        return None


def _extract_exif_date(file_path: Path) -> Optional[datetime]:
    """
    Extract date from EXIF metadata.
    
    Args:
        file_path: Path to image file
    
    Returns:
        datetime object or None
    """
    if not PIL_AVAILABLE:
        return None
    
    try:
        with Image.open(file_path) as img:
            exif = img._getexif()
            if not exif:
                return None
            
            # Try DateTimeOriginal first (most accurate)
            if DATETIME_ORIGINAL in exif:
                date_str = exif[DATETIME_ORIGINAL]
                return _parse_exif_datetime(date_str)
            
            # Fallback to DateTime
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "DateTime":
                    return _parse_exif_datetime(value)
    
    except (OSError, AttributeError, ValueError, KeyError):
        # Not an image, corrupted EXIF, or invalid date format
        return None
    
    return None


def _parse_exif_datetime(date_str: str) -> Optional[datetime]:
    """
    Parse EXIF datetime string to datetime object.
    
    EXIF format: "YYYY:MM:DD HH:MM:SS"
    
    Args:
        date_str: EXIF datetime string
    
    Returns:
        datetime object or None if parsing fails
    """
    try:
        # EXIF format: "YYYY:MM:DD HH:MM:SS"
        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    except (ValueError, AttributeError):
        return None


def get_date_path_components(date_taken: datetime) -> tuple[str, str]:
    """
    Get year and date folder components from datetime.
    
    Args:
        date_taken: datetime object
    
    Returns:
        Tuple of (YYYY, YYYY-MM-DD)
    """
    year = date_taken.strftime("%Y")
    date_folder = date_taken.strftime("%Y-%m-%d")
    return year, date_folder

