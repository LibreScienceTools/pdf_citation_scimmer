# PDF Citation Extractor - API Reference

**Version:** 0.2.0  
**Last Updated:** 2026-10-21

---

## Overview

This document provides a complete API reference for the PDF Citation Extractor library. It covers all public classes, methods, parameters, and return values.

---

## Table of Contents

1. [Main Classes](#main-classes)
2. [API Clients](#api-clients)
3. [Extractors](#extractors)
4. [Exporters](#exporters)
5. [Trackers](#trackers)
6. [Type Definitions](#type-definitions)
7. [Exception Handling](#exception-handling)

---

## Manual Entry Preservation

**NEW in v0.2.0:** The PDF Citation Extractor now fully supports mixed workflows with manually added JabRef entries.

### Core Principle

> **Entries without `pdf_uuid` field are ALWAYS preserved**

This simple rule enables powerful mixed workflows:

### Entry Types

| Type | Has `pdf_uuid` | Managed By | Preservation |
|------|---------------|------------|--------------|
| Auto (from PDF) | ✅ Yes | Scimmer | Updated on re-processing |
| Manual (from JabRef) | ❌ No | User | **ALWAYS preserved** |

### How It Works

1. **Auto entries**: Successfully processed PDFs get a `pdf_uuid` field and are tracked
2. **Manual entries**: Entries you add in JabRef don't have `pdf_uuid` and are never touched
3. **Merge behavior**: When exporting, manual entries are always kept, auto entries are managed

### Example Workflow

```python
# First run: process PDFs
extractor = CitationExtractor()
citations = extractor.process_directory(Path("./papers"))
extractor.export_citations(citations, Path("refs.bib"))

# User adds manual entries in JabRef for files that failed
# (these entries won't have pdf_uuid field)

# Second run: process more PDFs
extractor.export_citations(new_citations, Path("refs.bib"))
# Manual entries are PRESERVED, new auto entries are added
```

### Failed Files

Files that fail processing are logged in `failed_extractions.log` with:
- Clear instructions for manual addition
- Suggested BibTeX keys
- Group information
- Reason for failure

**User must manually add these to JabRef** - they won't be processed automatically.

### CLI Feedback

The CLI now shows preservation status:
```
✅ Successfully exported to references.bib

Summary:
  - New auto-extracted citations: 15
  - Manual entries preserved: 2
  - Total entries in file: 17 (15 auto + 2 manual)

⚠️  3 files failed extraction.
   These MUST be added manually to JabRef.
   See 'failed_extractions.log' for detailed instructions.
```

---

## Main Classes

### `CitationExtractor`

**Module:** `src.main`  
**Purpose:** Main orchestrator class for citation extraction with file tracking

#### Constructor

```python
CitationExtractor(config_path: Optional[Path] = None)
```

**Parameters:**
- `config_path` (Optional[Path]): Path to configuration YAML file. If None, uses default config or `./config.yaml`

**Example:**
```python
from src.main import CitationExtractor
from pathlib import Path

# Using default config
extractor = CitationExtractor()

# Using custom config
custom_config = Path("my_config.yaml")
extractor = CitationExtractor(config_path=custom_config)
```

#### Methods

##### `process_pdf(pdf_path: Path) -> Optional[Dict]`

Process a single PDF file and extract citation metadata.

**Parameters:**
- `pdf_path` (Path): Path to the PDF file

**Returns:**
- `Dict`: Citation metadata dictionary on success
- `Dict` with `"_failed": True` on extraction failure (includes error details)
- `None`: Only in unexpected error cases (rare)

**Metadata Structure (Success):**
```python
{
    "title": str | None,
    "author": str | None,
    "year": str | None,
    "journal": str | None,
    "volume": str | None,
    "issue": str | None,
    "pages": str | None,
    "doi": str | None,
    "url": str | None,
    "abstract": str | None,
    "publisher": str | None,
    "type": str | None,
    "issn": str | None,
    "isbn": str | None,
    "source": str,  # "embedded", "crossref", or "grobid"
    "pdf_file": str  # Original filename
}
```

**NEW in v0.2.0:** Metadata may also include:
- `"pdf_uuid"`: UUID for file tracking (when processed with tracking)
- `"group"`: Group name for JabRef organization
- `"group_path"`: Relative path to group directory

**Failure Structure:**
```python
{
    "_failed": True,
    "pdf_path": str,  # Full path to the PDF file
    "error": str,     # Reason for failure
    "would_be_key": str  # Suggested citation key for manual entry
}
```

---

##### `process_directory(directory: Path, output_path: Optional[Path] = None) -> Dict[str, List[Dict]]`

**UPDATED in v0.2.0:** Process all PDF files in a directory with file tracking.

Process all PDF files in a directory and its subdirectories. Files are grouped by their immediate parent directory name. Files in the root directory are grouped under "General".

**Parameters:**
- `directory` (Path): Directory containing PDF files
- `output_path` (Optional[Path]): Optional path to the output bib-file. If provided, used to initialize the file tracker for persistent identification.

**Returns:**
- `Dict[str, List[Dict]]`: Dictionary mapping group names to lists of citation metadata
  - Groups are based on subdirectory names
  - Files in root directory are grouped under "General"
  - Failed extractions are stored in `extractor._last_failed_files`
  - Each metadata dict includes `pdf_uuid` for file tracking

**NEW Features:**
- Integrates with FileTracker for persistent file identification
- Automatically cleans up missing file entries from tracker
- Each processed file gets a UUID for future reference
- Better error handling and failure tracking

---

##### `export_citations(citations: Dict[str, List[Dict]], output_path: Path, format: str = "bibtex", overwrite: bool = False) -> bool`

**UPDATED in v0.2.0:** Export citations to a file with UUID-based merge support.

Export citations to a file with smart merge functionality.

**Parameters:**
- `citations` (Dict[str, List[Dict]]): Dictionary mapping group names to lists of citation metadata
- `output_path` (Path): Path to output file
- `format` (str): Export format (default: "bibtex")
- `overwrite` (bool): If True, overwrite existing file. If False (default), merge with existing entries.

**Returns:**
- `bool`: True if export successful, False otherwise

**NEW Features:**
- **UUID-based duplicate detection**: Recognizes same files even when citation keys change
- **Preserve manually added entries**: Entries without UUID are kept during merge
- **Fallback for malformed BibTeX**: If parsing fails, preserves original content
- **Enhanced JabRef metadata**: Generates comprehensive group metadata
- **Better logging**: Detailed counts of new, updated, and preserved entries

**Merge Behavior (overwrite=False):**
- Reads existing `.bib` file if it exists
- Parses all existing entries and preserves them
- Detects existing entries by UUID to prevent duplicates
- Entries without UUID (manually added) are preserved
- Adds only new, non-duplicate entries
- Maintains JabRef group metadata from existing file
- Writes all entries (existing + new) to the output file

---

##### `_generate_fallback_citation_key(pdf_path: Path) -> str`

**UPDATED in v0.2.0:** Generate a fallback citation key from PDF path.

**Parameters:**
- `pdf_path` (Path): Path to the PDF file

**Returns:**
- `str`: A valid BibTeX citation key based on the filename

**NEW Format:** Simplified to just use cleaned filename stem without year suffix.

**Key Generation:**
- Extracts the filename stem (without extension)
- Cleans special characters for BibTeX compatibility
- Removes spaces
- Format: `{CleanStem}`

**Example:**
```python
from pathlib import Path
from src.main import CitationExtractor

extractor = CitationExtractor()
key = extractor._generate_fallback_citation_key(Path("Smith_2023_DeepLearning.pdf"))
# Returns: "Smith2023DeepLearning"

key = extractor._generate_fallback_citation_key(Path("paper.pdf"))
# Returns: "paper"
```

---

##### `_write_failed_files_log(failed_files: List[Dict], output_path: Path) -> None`

Write a detailed log file of failed extractions.

**Parameters:**
- `failed_files` (List[Dict]): List of failure dictionaries from `_last_failed_files`
- `output_path` (Path): Path to the output .bib file (log written to same directory)

**Failure Dictionary Structure:**
```python
{
    "path": str,           # Full path to the PDF
    "relative_path": str,  # Path relative to input directory
    "group": str,          # Group name (subdirectory or "General")
    "error": str,          # Reason for failure
    "would_be_key": str    # Suggested BibTeX key for manual entry
}
```

---

##### `_get_file_tracker(self, output_dir: Path) -> FileTracker`

**NEW in v0.2.0:** Get or create file tracker for a specific output directory.

**Parameters:**
- `output_dir` (Path): Directory where the bib-file will be stored

**Returns:**
- FileTracker instance for the specified directory

---

##### `_process_pdf_with_tracking(self, pdf_path: Path, group_name: str, project_root: Path, file_tracker: FileTracker) -> Optional[Dict]`

**NEW in v0.2.0:** Process a single PDF file with file tracking.

**Parameters:**
- `pdf_path` (Path): Path to the PDF file
- `group_name` (str): Group name for the file
- `project_root` (Path): Root directory for relative path calculation
- `file_tracker` (FileTracker): FileTracker instance

**Returns:**
- Metadata dictionary with UUID, or the failure dict from process_pdf

---

##### `_ensure_unique_citation_key(self, base_key: str, existing_keys: set, new_keys: set) -> str`

**NEW in v0.2.0:** Ensure a citation key is unique by appending 'a', 'b', etc. if needed.

**Parameters:**
- `base_key` (str): The base citation key (e.g., "Author2023")
- `existing_keys` (set): Set of keys that already exist in the file
- `new_keys` (set): Set of keys already added in this batch

**Returns:**
- `str`: Unique citation key

---

## API Clients

### `CrossRefClient`

**Module:** `src.api_clients.crossref`  
**Purpose:** Client for CrossRef API to fetch metadata from DOI

#### Constructor

```python
CrossRefClient(email: Optional[str] = None)
```

**Parameters:**
- `email` (Optional[str]): Email address for CrossRef polite pool. Providing an email gives you access to the polite pool with higher rate limits.

---

#### Methods

##### `get_metadata(doi: str) -> Optional[Dict]`

Fetch metadata for a DOI from CrossRef.

**Parameters:**
- `doi` (str): Digital Object Identifier (e.g., "10.1038/nature12373")

**Returns:**
- `Optional[Dict]`: Normalized metadata dictionary, or None if DOI not found or API error

**Metadata Fields:**
```python
{
    "title": str | None,
    "author": str | None,  # Format: "First Last and First Last"
    "year": str | None,
    "journal": str | None,
    "volume": str | None,
    "issue": str | None,
    "pages": str | None,
    "publisher": str | None,
    "type": str | None,  # e.g., "journal-article", "book"
    "abstract": str | None,
    "issn": str | None,
    "isbn": str | None,
    "url": str | None,
    "doi": str  # The DOI itself
}
```

---

##### `search_by_title(title: str, limit: int = 5) -> list`

Search CrossRef by title when DOI is not available.

**Parameters:**
- `title` (str): Publication title or partial title to search for
- `limit` (int): Maximum number of results to return (default: 5)

**Returns:**
- `list`: List of metadata dictionaries (potential matches)

---

## Extractors

### `PDFMetadataExtractor`

**Module:** `src.extractors.pdf_metadata`  
**Purpose:** Extract embedded metadata from PDF files

#### Constructor

```python
PDFMetadataExtractor()
```

---

#### Methods

##### `extract(pdf_path: Path) -> Dict[str, Optional[str]]`

Extract metadata from a PDF file.

**Parameters:**
- `pdf_path` (Path): Path to the PDF file

**Returns:**
- `Dict[str, Optional[str]]`: Dictionary containing metadata fields

---

##### `has_useful_metadata(metadata: Dict[str, Optional[str]]) -> bool`

Check if metadata contains useful information.

**Parameters:**
- `metadata` (Dict[str, Optional[str]]): Metadata dictionary to check

**Returns:**
- `bool`: True if at least `title` or `author` is present and non-empty

---

### `DOIExtractor`

**Module:** `src.extractors.doi_extractor`  
**Purpose:** Extract DOI from PDF text content

#### Constructor

```python
DOIExtractor(scan_pages: int = 3)
```

**Parameters:**
- `scan_pages` (int): Number of pages to scan for DOI (default: 3)

---

#### Methods

##### `extract(pdf_path: Path) -> Optional[str]`

Extract a single DOI from PDF file.

**Parameters:**
- `pdf_path` (Path): Path to the PDF file

**Returns:**
- `Optional[str]`: DOI string if found, None otherwise

---

##### `extract_multiple(pdf_path: Path) -> List[str]`

Extract all DOIs found in a PDF.

**Parameters:**
- `pdf_path` (Path): Path to the PDF file

**Returns:**
- `List[str]`: List of unique DOI strings found in the PDF

---

### `GROBIDClient`

**Module:** `src.extractors.grobid_client`  
**Purpose:** Client for GROBID service for advanced PDF metadata extraction

#### Prerequisites

GROBID requires Docker:
```bash
# Install Docker: https://docs.docker.com/get-docker/
# Run GROBID:
docker pull lfoppiano/grobid:0.8.0
docker run -t --rm -p 8070:8070 lfoppiano/grobid:0.8.0
```

#### Constructor

```python
GROBIDClient(grobid_url: str = "http://localhost:8070")
```

**Parameters:**
- `grobid_url` (str): URL of GROBID service (default: "http://localhost:8070")

---

#### Methods

##### `process(pdf_path: Path) -> Optional[Dict]`

Process PDF using GROBID service to extract metadata.

**Parameters:**
- `pdf_path` (Path): Path to the PDF file

**Returns:**
- `Optional[Dict]`: Citation metadata dictionary, or None if processing failed

---

##### `is_available() -> bool`

Check if GROBID service is available.

**Returns:**
- `bool`: True if service responds to health check

---

## Exporters

### `BibTeXExporter`

**Module:** `src.exporters.bibtex`  
**Purpose:** Export citation metadata to BibTeX format

#### Constructor

```python
BibTeXExporter()
```

---

#### Methods

##### `export(citations: List[Dict], output_path: Path) -> bool`

Export citations to a BibTeX file.

**Parameters:**
- `citations` (List[Dict]): List of citation metadata dictionaries
- `output_path` (Path): Path to output .bib file

**Returns:**
- `bool`: True if export successful, False otherwise

---

##### `export_single(metadata: Dict) -> str`

Export a single citation to a BibTeX string.

**Parameters:**
- `metadata` (Dict): Citation metadata dictionary

**Returns:**
- `str`: BibTeX formatted string

---

##### `_generate_citation_key(metadata: Dict) -> str`

**UPDATED in v0.2.0:** Generate a base citation key from metadata.

**NEW Format:** `FirstAuthorLastNameYear` (without underscores)

**Parameters:**
- `metadata` (Dict): Citation metadata

**Returns:**
- `str`: Base citation key string

**Example:**
```python
metadata = {
    "author": "John Doe and Jane Smith",
    "year": "2020",
    "title": "The Impact of Machine Learning on Society"
}
key = exporter._generate_citation_key(metadata)
# Returns: "Doe2020"
```

---

##### `_create_bibtex_entry(metadata: Dict) -> Dict`

Create a BibTeX entry from metadata.

**NEW in v0.2.0:** Now includes `pdf_uuid` field if present in metadata for file tracking.

---

##### `_generate_jabref_group_metadata(citations: List[Dict]) -> str`

**NEW in v0.2.0:** Generate JabRef group metadata as @Comment entries.

**Parameters:**
- `citations` (List[Dict]): List of citation metadata dictionaries

**Returns:**
- `str`: String containing JabRef group metadata, or empty string if no groups

**Purpose:** Creates native JabRef groups that are displayed in the JabRef UI.

---

##### `_extract_existing_jabref_metadata(content: str) -> str`

**NEW in v0.2.0:** Extract JabRef metadata comments from existing BibTeX file content.

**Parameters:**
- `content` (str): The raw content of the .bib file

**Returns:**
- `str`: String containing JabRef metadata comments, or empty string if none found

---

## Trackers

### `FileTracker`

**NEW in v0.2.0:** File tracking system for persistent PDF-to-BibTeX identification.

**Module:** `src.trackers.file_tracker`  
**Purpose:** Tracks PDF files and their UUIDs for persistent identification across citation key changes

#### Constructor

```python
FileTracker(output_dir: Union[Path, str])
```

**Parameters:**
- `output_dir` (Union[Path, str]): Directory where the bib-file is stored. The tracker file (`.pdf_tracker.json`) will be created here.

**Attributes:**
- `output_dir` (Path): The output directory
- `tracker_path` (Path): Path to the `.pdf_tracker.json` file
- `entries` (Dict[str, FileTrackerEntry]): Dictionary of all tracked entries by UUID

**Example:**
```python
from src.trackers import FileTracker
from pathlib import Path

# Create tracker for output directory
tracker = FileTracker(output_dir=Path("./output"))
```

#### Methods

##### `generate_uuid(file_path: Path) -> str`

Generate a deterministic UUID for a file.

**Parameters:**
- `file_path` (Path): Path to the PDF file

**Returns:**
- `str`: Deterministic UUID string

**Behavior:**
- UUID is based on absolute path, last modified time, and file size
- Same file always gets the same UUID
- Uses UUID5 with NAMESPACE_URL for generation

---

##### `get_file_hash(file_path: Path) -> str`

Calculate SHA-256 hash of file content.

**Parameters:**
- `file_path` (Path): Path to the file

**Returns:**
- `str`: Hex-encoded SHA-256 hash

---

##### `register_file(file_path: Path, citation_key: str, project_root: Optional[Path] = None, metadata: Optional[Dict] = None) -> Tuple[str, bool]`

**Main Method:** Register a file and get its UUID.

**Parameters:**
- `file_path` (Path): Path to the PDF file
- `citation_key` (str): Current citation key for the BibTeX entry
- `project_root` (Optional[Path]): Root directory for calculating relative paths
- `metadata` (Optional[Dict]): Optional additional metadata to store (e.g., group, source)

**Returns:**
- `Tuple[str, bool]`: Tuple of (uuid, is_new) where is_new is True if this is the first time the file is being tracked

**Example:**
```python
uuid, is_new = tracker.register_file(
    file_path=Path("/path/to/paper.pdf"),
    citation_key="Author2023Title",
    project_root=Path("/path/to/project"),
    metadata={"group": "MachineLearning", "source": "crossref"}
)
print(f"UUID: {uuid}, Is new: {is_new}")
```

---

##### `get_uuid_by_path(file_path: Path) -> Optional[str]`

Get UUID for a given file path.

**Parameters:**
- `file_path` (Path): Path to look up

**Returns:**
- `Optional[str]`: UUID string or None if not found

---

##### `get_entry_by_path(file_path: Path) -> Optional[FileTrackerEntry]`

Get full entry for a given file path.

**Parameters:**
- `file_path` (Path): Path to look up

**Returns:**
- `Optional[FileTrackerEntry]`: FileTrackerEntry or None if not found

---

##### `get_path_by_uuid(uuid: str) -> Optional[Path]`

Get file path for a given UUID.

**Parameters:**
- `uuid` (str): UUID to look up

**Returns:**
- `Optional[Path]`: Path or None if not found

---

##### `get_entry(uuid: str) -> Optional[FileTrackerEntry]`

Get full entry for a UUID.

**Parameters:**
- `uuid` (str): UUID to look up

**Returns:**
- `Optional[FileTrackerEntry]`: FileTrackerEntry or None

---

##### `update_citation_key(uuid: str, new_citation_key: str) -> bool`

Update citation key for a tracked file.

**Purpose:** Useful when citation keys change in JabRef or other tools.

**Parameters:**
- `uuid` (str): UUID of the file
- `new_citation_key` (str): New citation key

**Returns:**
- `bool`: True if updated successfully, False if UUID not found

---

##### `list_all_entries() -> List[FileTrackerEntry]`

Get all tracked entries.

**Returns:**
- `List[FileTrackerEntry]`: List of all FileTrackerEntry objects

---

##### `remove_file(file_path: Path) -> bool`

Remove a file from tracking.

**Parameters:**
- `file_path` (Path): Path to remove

**Returns:**
- `bool`: True if removed successfully, False if not found

---

##### `cleanup_missing_files() -> int`

Remove entries for files that no longer exist.

**Purpose:** This should be called periodically to keep the tracker clean.

**Returns:**
- `int`: Number of entries removed

---

##### `get_files_by_group(group_name: str) -> List[FileTrackerEntry]`

Get all entries that belong to a specific group.

**Parameters:**
- `group_name` (str): Group name to filter by

**Returns:**
- `List[FileTrackerEntry]`: List of entries in the specified group

---

##### `get_updated_files(since: Optional[str] = None) -> List[FileTrackerEntry]`

Get files that have been updated since a specific time.

**Parameters:**
- `since` (Optional[str]): ISO timestamp string. If None, returns all files.

**Returns:**
- `List[FileTrackerEntry]`: List of entries updated since the specified time

---

##### `reset() -> None`

Clear all tracked entries.

**WARNING:** This will remove all tracking data!

---

### `FileTrackerEntry`

**NEW in v0.2.0:** Data class representing a tracked file entry.

**Module:** `src.trackers.file_tracker`  
**Type:** `dataclass`

**Attributes:**
- `uuid` (str): Unique identifier for this file (deterministic)
- `file_path` (str): Absolute path to the file
- `relative_path` (str): Path relative to project root (for portability)
- `file_hash` (str): SHA-256 hash of file content
- `file_size` (int): Size of file in bytes
- `last_modified` (str): ISO timestamp of last file modification
- `citation_key` (str): Current BibTeX citation key
- `first_seen` (str): ISO timestamp when file was first tracked
- `last_seen` (str): ISO timestamp when file was last processed
- `metadata` (Dict): Additional metadata dictionary (e.g., group, source)

**Example:**
```python
from src.trackers import FileTracker, FileTrackerEntry

# Access entry fields
entry: FileTrackerEntry = tracker.get_entry("some-uuid")
print(f"UUID: {entry.uuid}")
print(f"File: {entry.file_path}")
print(f"Citation Key: {entry.citation_key}")
print(f"Group: {entry.metadata.get('group')}")
```

---

## Type Definitions

### Metadata Dictionary

The metadata dictionary is the primary data structure used throughout the application. It contains the following fields:

```python
MetadataDict = TypedDict('MetadataDict', {
    # Core fields
    'title': Optional[str],
    'author': Optional[str],
    'year': Optional[str],
    
    # Journal/Publication fields
    'journal': Optional[str],
    'volume': Optional[str],
    'issue': Optional[str],
    'pages': Optional[str],
    'publisher': Optional[str],
    'type': Optional[str],
    
    # Identifiers
    'doi': Optional[str],
    'url': Optional[str],
    'issn': Optional[str],
    'isbn': Optional[str],
    
    # Content
    'abstract': Optional[str],
    
    # PDF-specific
    'subject': Optional[str],
    'keywords': Optional[str],
    'creator': Optional[str],
    'producer': Optional[str],
    'creation_date': Optional[str],
    'mod_date': Optional[str],
    
    # System fields
    'source': Optional[str],  # "embedded", "crossref", "grobid"
    'pdf_file': Optional[str]  # Original filename
    
    # NEW in v0.2.0: File tracking
    'pdf_uuid': Optional[str],  # UUID for persistent identification
    'group': Optional[str],     # Group name for organization
    'group_path': Optional[str] # Path to group directory
}, total=False)
```

### Config Dictionary

```python
ConfigDict = TypedDict('ConfigDict', {
    'crossref_email': Optional[str],
    'default_output_format': str,
    'output_directory': str,
    'extraction': Dict[str, Any],
    'grobid_url': str
})
```

---

## Exception Handling

The library does not raise custom exceptions. Instead, it follows these error handling patterns:

### 1. Return None for Expected Failures

Methods that perform lookups or extractions return `None` when the operation fails in an expected way:

```python
# DOI not found
doi = doi_extractor.extract(pdf_path)  # Returns None

# DOI not in CrossRef
metadata = crossref_client.get_metadata("invalid.doi")  # Returns None

# GROBID service unavailable
metadata = grobid_client.process(pdf_path)  # Returns None
```

### 2. Raise Exceptions for Unexpected Errors

Methods may raise standard Python exceptions for unexpected errors (file not found, network errors, etc.). These are caught and logged by the caller:

```python
# File not found
try:
    metadata = extractor.process_pdf(Path("nonexistent.pdf"))
except FileNotFoundError:
    print("PDF file not found")
```

### 3. Logging

All operations are logged using Python's `logging` module. Check `pdf_citation_extractor.log` for details.

---

## Complete Import Reference

```python
# Main module
from src.main import CitationExtractor

# API Clients
from src.api_clients import CrossRefClient
from src.api_clients.crossref import CrossRefClient

# Extractors
from src.extractors import (
    PDFMetadataExtractor,
    DOIExtractor,
    GROBIDClient
)
from src.extractors.pdf_metadata import PDFMetadataExtractor
from src.extractors.doi_extractor import DOIExtractor
from src.extractors.grobid_client import GROBIDClient

# Exporters
from src.exporters import BibTeXExporter
from src.exporters.bibtex import BibTeXExporter

# Trackers (NEW in v0.2.0)
from src.trackers import FileTracker, FileTrackerEntry
from src.trackers.file_tracker import FileTracker, FileTrackerEntry
```

---

## Version Compatibility

| Python Version | Supported | Notes |
|----------------|----------|-------|
| 3.8 | ✓ | Minimum supported version |
| 3.9 | ✓ | Fully supported |
| 3.10 | ✓ | Fully supported |
| 3.11 | ✓ | Fully supported |
| 3.12 | ? | Not tested |

---

## Changelog

### v0.2.0 (2026-10-21)
- **NEW**: FileTracker system for persistent PDF-to-BibTeX identification
- **NEW**: `trackers` module with `FileTracker` and `FileTrackerEntry` classes
- **NEW**: CLI options `--show-tracker` and `--cleanup-tracker`
- **NEW**: UUID-based merge logic in BibTeX exporter
- **NEW**: JabRef group metadata generation
- **NEW**: Methods in `CitationExtractor`: `_get_file_tracker`, `_process_pdf_with_tracking`, `_ensure_unique_citation_key`
- **UPDATED**: `process_directory` now accepts `output_path` parameter
- **UPDATED**: Fallback citation key generation (simplified format)
- **UPDATED**: `BibTeXExporter` includes UUID support and enhanced metadata

### v0.1.0 (2026-10-20)
- Initial release with embedded metadata, DOI lookup, and GROBID support
- Basic merge functionality
- Failed files logging
- CLI interface

---

*For usage examples and quick start guide, see [QUICK_START.md](./QUICK_START.md)*
*For detailed source code documentation, see [SOURCE_CODE_DOCUMENTATION.md](./SOURCE_CODE_DOCUMENTATION.md)*
