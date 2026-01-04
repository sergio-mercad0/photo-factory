"""
Extract metadata (Date Taken, Location) from media files using PyExifTool.

Supports images, videos, RAW files (CR2, NEF, etc.) with comprehensive fallback chain.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from exiftool import ExifToolHelper
    EXIFTOOL_AVAILABLE = True
except ImportError:
    EXIFTOOL_AVAILABLE = False

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, DATETIME_ORIGINAL
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger("librarian.metadata")


def extract_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract comprehensive metadata from media file.
    
    Priority:
    1. PyExifTool (comprehensive - images, videos, RAW)
    2. PIL/Pillow (images only, fallback)
    3. File modification time (last resort)
    
    Args:
        file_path: Path to the media file
    
    Returns:
        Dictionary with:
        - captured_at: datetime or None
        - location: {"lat": float, "lon": float} or None
    """
    result = {
        "captured_at": None,
        "location": None,
    }
    
    # Try PyExifTool first (most comprehensive)
    if EXIFTOOL_AVAILABLE:
        exif_data = _extract_with_exiftool(file_path)
        if exif_data:
            result["captured_at"] = exif_data.get("captured_at")
            result["location"] = exif_data.get("location")
            
            # If we got both, we're done
            if result["captured_at"] and result["location"]:
                return result
    
    # Fallback to PIL for images (if ExifTool didn't work or isn't available)
    if PIL_AVAILABLE and not result["captured_at"]:
        date_taken = _extract_with_pil(file_path)
        if date_taken:
            result["captured_at"] = date_taken
    
    # Last resort: file modification time
    if not result["captured_at"]:
        try:
            mtime = file_path.stat().st_mtime
            result["captured_at"] = datetime.fromtimestamp(mtime)
            logger.warning(f"Using file mtime for {file_path.name} (metadata extraction failed)")
        except (OSError, ValueError) as e:
            logger.error(f"Could not extract date from {file_path.name}: {e}")
    
    return result


def _extract_with_exiftool(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract metadata using PyExifTool.
    
    Args:
        file_path: Path to media file
    
    Returns:
        Dictionary with captured_at and location, or None if extraction fails
    """
    if not EXIFTOOL_AVAILABLE:
        return None
    
    try:
        with ExifToolHelper() as et:
            metadata = et.get_metadata(str(file_path))
            
            if not metadata or len(metadata) == 0:
                return None
            
            # Get first result (usually only one file)
            tags = metadata[0]
            
            result = {
                "captured_at": None,
                "location": None,
            }
            
            # Extract date (try multiple EXIF tags)
            date_tags = [
                "EXIF:DateTimeOriginal",
                "EXIF:CreateDate",
                "QuickTime:CreateDate",
                "XMP:DateCreated",
                "IPTC:DateCreated",
                "File:FileModifyDate",  # Last resort
            ]
            
            for tag in date_tags:
                if tag in tags:
                    date_str = tags[tag]
                    parsed_date = _parse_exiftool_datetime(date_str)
                    if parsed_date:
                        result["captured_at"] = parsed_date
                        break
            
            # Extract location (GPS coordinates)
            lat = None
            lon = None
            
            # Try various GPS tag formats
            gps_tags = [
                ("EXIF:GPSLatitude", "EXIF:GPSLongitude"),
                ("GPS:GPSLatitude", "GPS:GPSLongitude"),
                ("Composite:GPSLatitude", "Composite:GPSLongitude"),
            ]
            
            for lat_tag, lon_tag in gps_tags:
                if lat_tag in tags and lon_tag in tags:
                    try:
                        lat = float(tags[lat_tag])
                        lon = float(tags[lon_tag])
                        break
                    except (ValueError, TypeError):
                        continue
            
            # If we got coordinates, store them
            if lat is not None and lon is not None:
                result["location"] = {"lat": lat, "lon": lon}
            
            return result if result["captured_at"] or result["location"] else None
    
    except Exception as e:
        logger.warning(f"ExifTool extraction failed for {file_path.name}: {e}")
        return None


def _extract_with_pil(file_path: Path) -> Optional[datetime]:
    """
    Extract date using PIL/Pillow (images only, fallback).
    
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


def _parse_exiftool_datetime(date_str: str) -> Optional[datetime]:
    """
    Parse datetime string from ExifTool.
    
    ExifTool returns dates in various formats:
    - "2025:12:27 14:30:00"
    - "2025-12-27T14:30:00"
    - "2025-12-27 14:30:00"
    
    Args:
        date_str: Date string from ExifTool
    
    Returns:
        datetime object or None
    """
    if not date_str:
        return None
    
    # Try common formats
    formats = [
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date string: {date_str}")
    return None


def _parse_exif_datetime(date_str: str) -> Optional[datetime]:
    """
    Parse datetime string from EXIF metadata.
    
    Args:
        date_str: Date string from EXIF (format: "YYYY:MM:DD HH:MM:SS")
    
    Returns:
        datetime object or None
    """
    if not date_str:
        return None
    
    try:
        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def extract_date_taken(file_path: Path) -> Optional[datetime]:
    """
    Extract Date Taken from media file (backward compatibility).
    
    Args:
        file_path: Path to the media file
    
    Returns:
        datetime object or None if extraction fails
    """
    metadata = extract_metadata(file_path)
    return metadata.get("captured_at")


def get_date_path_components(date_taken: datetime) -> tuple[str, str]:
    """
    Get year and date folder components from datetime.
    
    Args:
        date_taken: datetime object
    
    Returns:
        Tuple of (year, date_folder) where date_folder is "YYYY-MM-DD"
    """
    year = str(date_taken.year)
    date_folder = date_taken.strftime("%Y-%m-%d")
    return year, date_folder
