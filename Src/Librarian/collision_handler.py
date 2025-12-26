"""
Handle file collisions and duplicates using content hashing.
"""
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple

from .utils import get_storage_path, ensure_directory_exists

logger = logging.getLogger("librarian.collision_handler")


def calculate_file_hash(file_path: Path, chunk_size: int = 8192) -> Optional[str]:
    """
    Calculate SHA256 hash of file content.
    
    Args:
        file_path: Path to file
        chunk_size: Size of chunks to read (for memory efficiency)
    
    Returns:
        Hex digest of SHA256 hash, or None if file cannot be read
    """
    sha256 = hashlib.sha256()
    
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (OSError, IOError) as e:
        logger.error(f"Failed to calculate hash for {file_path}: {e}")
        return None


def find_existing_file_by_hash(destination_dir: Path, target_hash: str) -> Optional[Path]:
    """
    Search for existing file with matching hash in destination directory.
    
    Args:
        destination_dir: Directory to search in
        target_hash: Hash to search for
    
    Returns:
        Path to existing file with matching hash, or None if not found
    """
    if not destination_dir.exists():
        return None
    
    for file_path in destination_dir.iterdir():
        if not file_path.is_file():
            continue
        
        existing_hash = calculate_file_hash(file_path)
        if existing_hash == target_hash:
            return file_path
    
    return None


def generate_unique_filename(destination_dir: Path, base_name: str) -> Path:
    """
    Generate a unique filename in destination directory.
    
    If base_name exists, appends _1, _2, etc. until unique.
    
    Args:
        destination_dir: Target directory
        base_name: Desired filename
    
    Returns:
        Path to unique filename
    """
    destination_path = destination_dir / base_name
    
    if not destination_path.exists():
        return destination_path
    
    # Extract stem and suffix
    stem = destination_path.stem
    suffix = destination_path.suffix
    
    # Try numbered variants
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        candidate = destination_dir / new_name
        
        if not candidate.exists():
            return candidate
        
        counter += 1
        
        # Safety limit (should never hit this)
        if counter > 10000:
            raise RuntimeError(f"Could not generate unique filename for {base_name} in {destination_dir}")


def handle_collision(
    source_file: Path,
    destination_file: Path,
    file_hash: str
) -> Tuple[bool, Optional[Path], str]:
    """
    Handle file collision/duplicate detection.
    
    Args:
        source_file: Source file path
        destination_file: Intended destination path
        file_hash: SHA256 hash of source file
        destination_dir: Destination directory
    
    Returns:
        Tuple of:
        - (bool) True if file should be moved, False if duplicate
        - (Optional[Path]) Final destination path (None if duplicate)
        - (str) Reason message
    """
    # Check if destination file exists
    if not destination_file.exists():
        # No collision - safe to move
        return True, destination_file, "No collision"
    
    # Collision detected - check if it's a true duplicate
    existing_hash = calculate_file_hash(destination_file)
    
    if existing_hash == file_hash:
        # True duplicate - same content
        logger.info(f"Duplicate detected: {source_file.name} (hash: {file_hash[:8]}...)")
        return False, None, "Duplicate: same content as existing file"
    
    # Name collision with different content - need to rename
    logger.warning(
        f"Name collision: {source_file.name} has different content. "
        f"Existing hash: {existing_hash[:8] if existing_hash else 'unknown'}..., "
        f"New hash: {file_hash[:8]}..."
    )
    
    unique_path = generate_unique_filename(destination_file.parent, destination_file.name)
    return True, unique_path, f"Name collision: renamed to {unique_path.name}"


def check_duplicate_in_date_folder(
    date_folder: Path,
    file_hash: str,
    exclude_path: Optional[Path] = None
) -> Optional[Path]:
    """
    Check if file with same hash exists anywhere in date folder.
    
    Args:
        date_folder: Date folder to search (YYYY-MM-DD)
        file_hash: Hash to search for
        exclude_path: Path to exclude from search (e.g., intended destination)
    
    Returns:
        Path to duplicate file if found, None otherwise
    """
    if not date_folder.exists():
        return None
    
    for file_path in date_folder.iterdir():
        if not file_path.is_file():
            continue
        
        # Skip the file we're checking against
        if exclude_path and file_path == exclude_path:
            continue
        
        existing_hash = calculate_file_hash(file_path)
        if existing_hash == file_hash:
            return file_path
    
    return None

