# File Tracking Feature Implementation Summary

## Overview

This document summarizes the implementation of the UUID-based file tracking feature for PDF-Citation-Scimmer. This feature addresses the problem where citations changed in JabRef are not recognized by the scimmer because there was no persistent link between PDF files and BibTeX entries.

## What Was Implemented

### 1. New Tracker Module (`src/trackers/`)

Created a new module with the following components:

- **`src/trackers/__init__.py`**: Module initialization
- **`src/trackers/file_tracker.py`**: Core tracking functionality
  - `FileTrackerEntry` dataclass: Represents a tracked file with all metadata
  - `FileTracker` class: Manages file registration and tracking

### 2. Key Features

#### Deterministic UUID Generation
- UUIDs are generated using UUID5 (name-based) from file path + modification time + file size
- Same file always gets the same UUID, ensuring stability
- UUIDs are independent of citation keys, making them JabRef-proof

#### Tracker File Storage
- Tracker data is stored in `.pdf_tracker.json` in the **same directory as the output bib-file**
- This makes the tracker project-specific and portable
- Format: JSON with UUID as key, FileTrackerEntry data as value

#### File Metadata Tracking
Each tracked file stores:
- UUID (deterministic identifier)
- Absolute file path
- Relative path (from project root for portability)
- SHA-256 hash of file content
- File size and modification timestamp
- Current citation key
- First seen and last seen timestamps
- Custom metadata (group, source, etc.)

### 3. Integration Points

#### BibTeX Exporter (`src/exporters/bibtex.py`)
- Added `pdf_uuid` field to BibTeX entries when present in metadata
- Field is preserved through export/import cycles

#### Main Extractor (`src/main.py`)
- Added `_get_file_tracker()` method to manage tracker instances
- Added `_process_pdf_with_tracking()` method to register files during processing
- Modified `process_directory()` to:
  - Accept optional `output_path` parameter
  - Initialize tracker with output directory
  - Clean up missing file entries after processing
- Modified single PDF processing to use tracking
- Added CLI options:
  - `--show-tracker`: Display all tracked files for an output directory
  - `--cleanup-tracker`: Remove entries for missing files

### 4. CLI Usage

#### Process PDFs with Tracking (Automatic)
```bash
# Process directory - tracker is automatically created in output directory
python -m src.main --dir ./papers --output ./papers/citations.bib

# Process single PDF
python -m src.main --pdf paper.pdf --output citations.bib
```

#### View Tracked Files
```bash
# Show all tracked files for a project
python -m src.main --show-tracker --output ./papers/citations.bib
```

#### Clean Up Missing Files
```bash
# Remove entries for files that no longer exist
python -m src.main --cleanup-tracker --output ./papers/citations.bib
```

### 5. BibTeX Entry Format

BibTeX entries now include the `pdf_uuid` field:

```bibtex
@article{Author_2023_Title,
  author = {Author},
  title = {Title},
  year = {2023},
  journal = {Journal},
  pdf_uuid = {a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8},
  groups = {Papers}
}
```

### 6. Tracker File Format (`.pdf_tracker.json`)

```json
{
  "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8": {
    "uuid": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
    "file_path": "/absolute/path/to/papers/article.pdf",
    "relative_path": "papers/article.pdf",
    "file_hash": "abc123...",
    "file_size": 1024,
    "last_modified": "2024-01-01T12:00:00",
    "citation_key": "Author_2023_Title",
    "first_seen": "2024-01-01T12:00:00",
    "last_seen": "2024-01-02T12:00:00",
    "metadata": {
      "group": "Papers",
      "source": "crossref"
    }
  }
}
```

### 7. Testing

Created comprehensive test suite (`tests/test_file_tracker.py`) with 25 tests covering:

- Tracker initialization and persistence
- UUID generation (deterministic, unique)
- Path handling (absolute, relative)
- File operations (register, retrieve, update, remove)
- Cleanup functionality
- Metadata storage and updates
- Integration with BibTeX exporter
- Error handling

All tests pass successfully.

## How It Solves the Original Problem

### Problem
When citations are modified in JabRef:
1. Citation keys may change
2. PDF files are no longer recognized by the scimmer
3. Re-processing creates duplicate entries

### Solution
With the file tracking system:
1. Each PDF file gets a **stable UUID** that doesn't change
2. The UUID is stored in both the BibTeX entry and the tracker file
3. Even if citation keys change in JabRef, the UUID remains the same
4. The scimmer can identify files by UUID, preventing duplicates

## File Structure

```
pdf_citation_scimmer/
├── src/
│   ├── trackers/
│   │   ├── __init__.py          # Module initialization
│   │   └── file_tracker.py      # Core tracking logic
│   ├── exporters/
│   │   └── bibtex.py            # Modified: Add pdf_uuid field
│   └── main.py                  # Modified: Tracker integration
├── tests/
│   └── test_file_tracker.py     # Comprehensive test suite
└── output/
    ├── citations.bib            # Contains pdf_uuid fields
    └── .pdf_tracker.json        # Tracker data (NEW)
```

## Benefits

✅ **JabRef-Proof**: UUIDs don't change when JabRef modifies citations
✅ **Portable**: Tracker file stays with your project
✅ **Automatic**: No manual setup required
✅ **Non-Breaking**: Existing workflows continue to work
✅ **Persistent**: File identification works across sessions
✅ **Clean**: Automatic cleanup of missing files

## Future Enhancements

Possible future improvements:
- CLI command to manually add/update files in tracker
- Tracker validation and repair utilities
- Integration with version control systems
- File content change detection via hash comparison
- Automatic re-processing of changed files

## Commit Information

```
commit 8bcccca
feat: implement UUID-based file tracking system

- Add new src/trackers/ module with FileTracker class
- Generate deterministic UUIDs for each PDF file based on path + metadata
- Store tracker data in .pdf_tracker.json alongside output bib-file
- Add pdf_uuid field to BibTeX entries for persistent file identification
- Integrate tracking into directory and single-file processing
- Add CLI options: --show-tracker and --cleanup-tracker
- Track relative paths for portability across systems
- Add comprehensive test suite for file tracker

The file tracking system ensures that PDF files can be identified
even when citation keys change in JabRef or other reference managers.
```
