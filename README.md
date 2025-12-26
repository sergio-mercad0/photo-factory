# Photo Factory

A robust photo and video management system with automated ingestion and organization.

## Project Structure

```
Photo_Factory/
├── Src/
│   └── Librarian/          # Python automation code (Git Tracked)
│       └── librarian.py    # Main ingest service
├── Stack/                  # Infrastructure (Git Tracked)
│   └── App_Data/           # Docker configs, databases, .env
├── Photos_Inbox/           # Input drop zone (Git Ignored)
└── Storage/                # Vault (Git Ignored)
    └── Originals/          # Organized photos by date
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Photo_Factory
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create required directories:**
   The service will create directories automatically, but you can create them manually:
   ```bash
   mkdir Photos_Inbox
   mkdir -p Storage/Originals
   ```

## Usage

### Librarian Ingest Service

The Librarian service watches `Photos_Inbox` and automatically organizes files into `Storage/Originals/{YYYY}/{YYYY-MM-DD}/` based on the Date Taken metadata.

#### Running the Service

**Basic usage:**
```bash
python -m Src.Librarian.librarian
```

**With custom options:**
```bash
python -m Src.Librarian.librarian \
    --stability-delay 5.0 \
    --min-file-age 2.0 \
    --log-level INFO
```

#### Command Line Options

- `--stability-delay`: Seconds to wait after file modification before processing (default: 5.0)
- `--min-file-age`: Minimum age of file before considering it stable (default: 2.0)
- `--log-level`: Logging level - DEBUG, INFO, WARNING, ERROR (default: INFO)

#### How It Works

1. **File Detection**: Watches `Photos_Inbox` for new files
2. **Stability Check**: Waits for files to be stable (unchanged for stability-delay seconds)
3. **Metadata Extraction**: Extracts Date Taken from EXIF (images) or uses file modification time
4. **Collision Handling**: 
   - Calculates SHA256 hash of file content
   - Checks for duplicates (same hash = skip, delete from inbox)
   - Handles name collisions (same name, different content = rename with suffix)
5. **Organization**: Moves files to `Storage/Originals/{YYYY}/{YYYY-MM-DD}/`

#### Duplicate Handling

- **True Duplicates** (same content hash): Automatically deleted from inbox
- **Name Collisions** (same name, different content): Renamed with `_1`, `_2`, etc. suffix

## Environment Variables

No environment variables are required for the Librarian service. All paths are resolved relative to the project root.

## Dependencies

- **watchdog** (>=3.0.0): File system event monitoring
- **Pillow** (>=10.0.0): Image metadata extraction (EXIF)

See `requirements.txt` for complete list.

## Testing

### Running Tests

The project includes a comprehensive pytest test suite located in `Src/Librarian/tests/`.

**Run all tests:**
```bash
pytest Src/Librarian/tests/
```

**Run with verbose output:**
```bash
pytest Src/Librarian/tests/ -v
```

**Run specific test file:**
```bash
pytest Src/Librarian/tests/test_librarian_integration.py
```

### Test Coverage

The test suite covers:
- **Date Sorting**: Files organized into correct `YYYY/YYYY-MM-DD` folders
- **Deduplication**: Identical files (same hash) are detected and deleted from inbox
- **Name Collisions**: Files with same name but different content are renamed with `_1`, `_2` suffixes
- **Metadata Extraction**: Date extraction from EXIF and file modification time fallback
- **Hash Calculation**: SHA256 hashing for duplicate detection

### Test Safety

All tests use `tmp_path` fixtures and **never touch the real filesystem**. The `Photos_Inbox` and `Storage` directories are never modified during testing.

## Development

### Project Rules

See `.cursorrules` for detailed development guidelines, including:
- Version control protocol
- Pathing and portability rules
- Documentation requirements
- Error handling standards

### Code Structure

- `Src/Librarian/librarian.py`: Main service entry point
- `Src/Librarian/file_watcher.py`: File watching with stability checks
- `Src/Librarian/metadata_extractor.py`: EXIF/date extraction
- `Src/Librarian/collision_handler.py`: Hash calculation and duplicate detection
- `Src/Librarian/utils.py`: Path resolution and logging utilities
- `Src/Librarian/tests/`: Comprehensive pytest test suite

## License

[Add license information here]

