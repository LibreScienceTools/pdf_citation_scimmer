# PDF Citation Extractor - Source Code Documentation

**Version:** 0.2.0  
**Last Updated:** 2026-10-21  
**Project:** pdf_citation_scimmer

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Manual Entry Preservation](#manual-entry-preservation)
4. [Quality Filtering (NEW)](#quality-filtering-new-in-v020)
5. [Module Documentation](#module-documentation)
   - [5.1 Main Module (`main.py`)](#51-main-module-mainpy)
   - [5.2 API Clients](#52-api-clients)
   - [5.3 Extractors](#53-extractors)
   - [5.4 Exporters](#54-exporters)
   - [5.5 Trackers](#55-trackers)
6. [Class Reference](#class-reference)
7. [Configuration](#configuration)
8. [Dependencies](#dependencies)
9. [Data Flow](#data-flow)
10. [Error Handling](#error-handling)
11. [Logging](#logging)

---

## Project Overview

The **PDF Citation Extractor** is a command-line tool that extracts citation metadata from PDF files and exports it to reference management formats (currently BibTeX). It uses a multi-strategy approach to extract metadata:

1. **Embedded Metadata**: Extracts metadata directly from the PDF's document properties
2. **DOI Lookup**: Scans PDF content for DOI identifiers and queries the CrossRef API
3. **GROBID Processing**: Uses the GROBID machine learning service for advanced extraction (optional)

**NEW in v0.2.0:** The tool now includes a **File Tracker** system that maintains persistent links between PDF files and their BibTeX entries using UUIDs. This ensures that files can be identified even when citation keys change in tools like JabRef.

The tool is designed for researchers and academics who need to quickly extract bibliographic information from collections of PDF papers.

---

## Architecture

```
src/
├── __init__.py           # Package initialization and version
├── main.py              # CLI entry point and orchestrator
├── api_clients/
│   ├── __init__.py      # API clients module exports
│   └── crossref.py      # CrossRef API client
├── extractors/
│   ├── __init__.py      # Extractor module exports
│   ├── pdf_metadata.py  # PDF embedded metadata extractor
│   ├── doi_extractor.py  # DOI extraction from PDF text
│   └── grobid_client.py  # GROBID service client
├── exporters/
│   ├── __init__.py      # Exporter module exports
│   └── bibtex.py        # BibTeX format exporter
└── trackers/
    ├── __init__.py      # Tracker module exports
    └── file_tracker.py   # File tracking system for persistent identification
```

### Key Design Principles

- **Modular Design**: Each extraction method, API client, exporter, and tracker is a separate class
- **Fallback Strategy**: Multiple extraction strategies with automatic fallback
- **Configurable**: YAML-based configuration for customization
- **CLI-First**: Command-line interface with Click library
- **Logging**: Comprehensive logging to file and console
- **Progress Tracking**: tqdm progress bars for batch processing
- **Persistent Tracking**: UUID-based file tracking that survives citation key changes
- **Incremental Updates**: Smart merge functionality that preserves existing BibTeX entries
- **Manual Entry Preservation**: Entries without UUID are always preserved, allowing mixed automatic/manual workflows

---

## Manual Entry Preservation

### Overview

The PDF Citation Extractor now **fully supports mixed workflows** where you can combine automatically extracted entries with manually added entries in JabRef. This is achieved through a simple but powerful mechanism:

- **Auto entries** (from successfully processed PDFs) have a `pdf_uuid` field
- **Manual entries** (added by you in JabRef) do NOT have a `pdf_uuid` field
- The scimmer **always preserves** entries without `pdf_uuid` during merge operations

### Key Principles

1. **Auto entries are managed**: Files processed successfully get UUIDs and are tracked
2. **Manual entries are sacred**: Entries without UUIDs are never removed or modified
3. **Failed files are explicit**: Files that fail processing are logged clearly for manual addition
4. **Merge is smart**: UUID-based detection prevents duplicates even when citation keys change

### Entry Types

| Entry Type | Has `pdf_uuid`? | Managed By | Behavior |
|------------|-----------------|------------|----------|
| Auto (from PDF) | ✅ Yes | Scimmer | Updated on re-processing, tracked via UUID |
| Manual (from JabRef) | ❌ No | User | **ALWAYS preserved**, never modified |
| Failed (needs manual) | N/A | N/A | Logged in `failed_extractions.log` |

### Workflow

#### 1. First Run - Process PDFs
```bash
# Process your PDF directory
python -m src.main --dir ./papers --output references.bib
```

**Result:**
- Successfully processed PDFs → Added to `references.bib` with `pdf_uuid` fields
- Failed PDFs → Logged in `output/failed_extractions.log`

#### 2. Add Manual Entries in JabRef
- Open `references.bib` in JabRef
- Add entries manually (these won't have `pdf_uuid` fields)
- Save the file

#### 3. Second Run - Process More PDFs
```bash
# Process more PDFs - manual entries are preserved
python -m src.main --dir ./more_papers --output references.bib
```

**Result:**
- New PDFs → Added to `references.bib` with `pdf_uuid` fields
- Existing auto entries → Updated if needed (UUID-based matching)
- **Manual entries → PRESERVED EXACTLY AS THEY WERE**

### Failed Files Handling

When a PDF cannot be processed automatically (no embedded metadata, no DOI found, etc.), it is **not silently ignored**. Instead:

1. **Detailed logging**: All failed files are logged in `failed_extractions.log`
2. **Clear instructions**: The log file contains step-by-step instructions for manual addition
3. **Suggested citation keys**: Each failed file has a suggested BibTeX key
4. **Group information**: Each failed file includes its group for proper organization

#### Example Log File Content:
```
======================================================================
IMPORTANT: These files could NOT be processed automatically.
You MUST add them manually to JabRef using the information below.
======================================================================

HOW TO ADD MANUALLY:
1. Open your .bib file in JabRef
2. For each file below, create a new entry
3. Use the 'Suggested BibTeX Key' as the entry's citation key
4. Add the entry to the specified 'Group'
5. Fill in the metadata manually (title, author, year, etc.)

Total files that need manual addition: 2

----------------------------------------------------------------------
FAILED FILES:
----------------------------------------------------------------------

File #1: problematic_paper.pdf
  Group: General
  Suggested BibTeX Key: problematicpaper
  Full Path: /papers/problematic_paper.pdf
  Reason: No metadata extracted from any source

  ACTION REQUIRED: Add this file manually to JabRef!
  - BibTeX key: problematicpaper
  - Group: General
```

### CLI Output

The CLI now provides clear feedback about preservation:

```
✅ Successfully exported to references.bib

Summary:
  - New auto-extracted citations: 15
  - Groups: 3
    - General: 5 citations
    - MachineLearning: 7 citations
    - Neuroscience: 3 citations
  - Output format: bibtex
  - Output file: references.bib
  - Manual entries preserved: 2
  - Total entries in file: 17 (15 auto + 2 manual)

⚠️  3 files failed extraction.
   These MUST be added manually to JabRef.
   See 'failed_extractions.log' for detailed instructions.
   Manually added entries will be preserved in future runs.
```

### Technical Implementation

The preservation logic is implemented in `_export_to_bibtex` method:

1. **Separation**: Existing entries are explicitly separated into manual (no UUID) vs auto (with UUID)
2. **Foundation**: Manual entries form the foundation of `all_entries` and are never removed
3. **Merging**: Auto entries are merged on top, with UUID-based duplicate detection
4. **Verification**: Final count verification ensures all manual entries were preserved

#### Code Flow:
```python
# Step 1: Separate existing entries
manual_entries = {k: v for k, v in existing_entries.items() if "pdf_uuid" not in v}
auto_entries = {k: v for k, v in existing_entries.items() if "pdf_uuid" in v}

# Step 2: Start with manual entries (they are sacred)
all_entries = dict(manual_entries)

# Step 3: Add auto entries (managed by scimmer)
all_entries.update(auto_entries)

# Step 4: Add/update new auto entries
# ... processing logic ...

# Step 5: Final verification
final_manual_count = sum(1 for e in all_entries.values() if "pdf_uuid" not in e)
assert final_manual_count == len(manual_entries)  # Must be preserved!
```

### Benefits

1. **No data loss**: Manual entries are never accidentally removed
2. **Predictable**: Clear separation between auto and manual entries
3. **Transparent**: Users know exactly what's happening via logs and CLI output
4. **Flexible**: Supports any workflow (all auto, all manual, or mixed)
5. **Safe**: Default behavior preserves manual entries

### Edge Cases Handled

| Scenario | Behavior |
|----------|----------|
| Manual entry with same key as auto entry | Manual entry is preserved, auto gets unique key |
| Parsing failure of existing .bib | Manual entries still preserved from successful parse |
| Overwrite mode (`--overwrite`) | Manual entries are removed (user explicitly requested clean slate) |
| Multiple runs | Manual entries survive across all runs |
| Mixed auto/manual in JabRef | Both types coexist peacefully |

---

## Quality Filtering (NEW in v0.2.0)

### Overview

To prevent low-quality metadata from polluting your reference library, the PDF Citation Extractor now includes **automatic quality filtering**. This feature identifies and rejects metadata entries that are likely to be incorrect, incomplete, or of poor quality.

### What Gets Filtered?

The following types of metadata are automatically rejected and treated as extraction failures:

| Category | Examples | Rationale |
|----------|----------|-----------|
| **Generic Titles** | "Misc", "Untitled", "Unknown", "Document", "Article", "Paper", "Publication" | These indicate missing or placeholder metadata |
| **Generic Authors** | "Unknown", "Anonymous", "None", "No author", "Author" | Author information is critical for citations |
| **Invalid Years** | "YYYY", "Unknown", "0000", "0", "1900", out of range (1900-2100) | Year validation ensures temporal accuracy |
| **PII DOI Patterns** | `S0021-8502(97)10031-3`, `S1234-5678(99)12345-6` | PII numbers are not valid DOIs; they need manual resolution |
| **Empty Fields** | Empty or whitespace-only title/author | Critical fields must have meaningful content |

### Pattern Matching Details

#### PII DOI Detection

The system uses a regex pattern to detect PII (Publisher Item Identifier) numbers that are sometimes mistakenly extracted as DOIs:

```python
pattern = r'^S\d{4}-\d{4}\(\d{2}\)\d+-\d+$'
```

This matches patterns like:
- `S0021-8502(97)10031-3`
- `S1234-5678(99)12345-6`
- `S1234-5678(20)123-456`

These are NOT valid DOIs and should be resolved manually through the publisher's website.

### Behavior

1. **Automatic Rejection**: Metadata that fails quality checks is treated exactly like any other extraction failure
2. **Logged for Manual Addition**: Failed entries are logged in `failed_extractions.log` with all available information
3. **No UUID Assigned**: Failed entries do NOT receive a `pdf_uuid`, so they won't interfere with manual entries
4. **Clear Feedback**: The log file includes the reason for failure (e.g., "Low quality metadata from CrossRef (suspect or incomplete data)")

### Example Workflow

```bash
# Process PDFs - some may fail quality checks
python -m src.main --dir ./papers --output references.bib
```

**Result:**
- High-quality metadata → Added to `references.bib` with `pdf_uuid`
- Low-quality metadata → Logged in `failed_extractions.log`

**In `failed_extractions.log`:**
```
File #1: low_quality_paper.pdf
  Group: General
  Suggested BibTeX Key: lowqualitypaper
  Full Path: /papers/low_quality_paper.pdf
  Reason: Low quality metadata from CrossRef (suspect or incomplete data)
  
  ACTION REQUIRED: Add this file manually to JabRef!
```

### Implementation

The quality filtering is implemented in the `_is_high_quality_metadata()` method of the `CitationExtractor` class:

```python
def _is_high_quality_metadata(self, metadata: Dict) -> bool:
    """
    Check if extracted metadata meets basic quality standards.
    Returns False if metadata is too low quality to be useful.
    """
    # Check for empty/missing critical fields
    if not metadata.get("title") and not metadata.get("author"):
        return False
    
    # Check for bad titles (only if title exists)
    if "title" in metadata:
        title = str(metadata["title"]).strip().lower()
        if not title:  # Empty after stripping
            return False
        if title in ["misc", "untitled", "document", "unknown", ...]:
            return False
    
    # Similar checks for authors, years, DOI patterns, etc.
    # ...
    
    return True
```

Quality checks are integrated into the `process_pdf()` method at each extraction strategy:
- After CrossRef metadata retrieval
- After embedded metadata extraction
- After GROBID processing

### Benefits

1. **Prevents Garbage In**: Stops low-quality metadata from entering your reference library
2. **Encourages Manual Review**: Forces you to manually verify suspicious entries
3. **Maintains Data Integrity**: Only reliable, high-quality metadata is automatically added
4. **Transparent**: All rejections are logged with clear reasons
5. **Safe**: Quality-filtered entries are handled the same as other failures (preserving manual entries)

### Edge Cases

| Scenario | Outcome |
|----------|---------|
| PDF has PII DOI only | Rejected, logged for manual addition |
| CrossRef returns "Unknown" year | Rejected, logged for manual addition |
| Embedded metadata has title "Document" | Rejected, logged for manual addition |
| All fields missing | Rejected, logged for manual addition |
| Partial but valid metadata | Accepted if passes quality checks |

---

## Module Documentation

---

### 5.1 Main Module (`main.py`)

**Purpose:** Provides the command-line interface and orchestrates the citation extraction process with file tracking.

#### Classes

##### `CitationExtractor`

**Description:** Main orchestrator class that coordinates all extraction, export, and tracking operations.

**Attributes:**
- `config` (Dict): Loaded configuration from YAML file
- `pdf_extractor` (PDFMetadataExtractor): Extractor for embedded PDF metadata
- `doi_extractor` (DOIExtractor): Extractor for DOI from PDF text
- `crossref_client` (CrossRefClient): Client for CrossRef API
- `bibtex_exporter` (BibTeXExporter): Exporter for BibTeX format
- `grobid_client` (GROBIDClient, optional): Client for GROBID service
- `_last_failed_files` (List[Dict]): Tracks files that failed extraction in the last run
- `file_tracker` (FileTracker, optional): File tracker for persistent identification

**Methods:**

```python
def __init__(self, config_path: Optional[Path] = None)
```
Initialize the extractor with configuration. Loads config from specified path or default location.

**Parameters:**
- `config_path`: Path to config.yaml file (optional)

**Example:**
```python
from src.main import CitationExtractor
extractor = CitationExtractor()
```

---

```python
def _get_file_tracker(self, output_dir: Path) -> FileTracker
```
Get or create file tracker for a specific output directory.

**NEW in v0.2.0:** This method ensures that each output directory has its own file tracker instance.

**Parameters:**
- `output_dir`: Directory where the bib-file will be stored

**Returns:**
- FileTracker instance for the specified directory

---

```python
def _ensure_unique_citation_key(self, base_key: str, existing_keys: set, new_keys: set) -> str
```
Ensure a citation key is unique by appending 'a', 'b', etc. if needed.

**NEW in v0.2.0:** Handles duplicate citation key detection and resolution.

**Parameters:**
- `base_key`: The base citation key (e.g., "Author2023")
- `existing_keys`: Set of keys that already exist in the file
- `new_keys`: Set of keys already added in this batch

**Returns:**
- Unique citation key

---

```python
def _generate_fallback_citation_key(self, pdf_path: Path) -> str
```
Generate a fallback citation key from PDF filename when extraction fails.

**UPDATED in v0.2.0:** Simplified format to just use cleaned filename stem without year suffix.

**Purpose:** Creates a valid BibTeX key that can be used to identify the PDF in JabRef when automatic extraction fails.

**Parameters:**
- `pdf_path`: Path to the PDF file

**Returns:**
- `str`: BibTeX-compatible citation key

**Algorithm:**
1. Extracts the filename stem (without extension)
2. Removes special characters (replaces with nothing)
3. Removes spaces
4. Returns cleaned stem or "UNKNOWN" if empty

**Example:**
```python
key = extractor._generate_fallback_citation_key(Path("Smith_2023_DeepLearning.pdf"))
# Returns: "Smith2023DeepLearning"

key = extractor._generate_fallback_citation_key(Path("paper.pdf"))
# Returns: "paper"
```

---

```python
def _write_failed_files_log(self, failed_files: List[Dict], output_path: Path) -> None
```
Write a detailed log of failed extractions for manual JabRef entry creation.

**Purpose:** Helps users identify which PDFs failed extraction and provides information needed to manually create entries in JabRef.

**Parameters:**
- `failed_files`: List of failure dictionaries (from `_last_failed_files`)
- `output_path`: Path to the output .bib file

**Log File Location:**
- If `output_path.parent` exists (not current directory): uses that as log directory
- Otherwise: uses `config.output_directory` (default: `./output`)
- Log filename: `failed_extractions.log`

**Log File Contents:**
- Timestamp of extraction
- Output file reference
- JabRef usage instructions
- Total count of failed files
- For each failed file:
  - Relative path
  - Group name (for JabRef organization)
  - Would-be citation key (for BibTeX ID)
  - Error reason
  - Suggested action

---

```python
def _process_pdf_with_tracking(self, pdf_path: Path, group_name: str,
                               project_root: Path, file_tracker: FileTracker) -> Optional[Dict]
```
**NEW in v0.2.0:** Process a single PDF file with file tracking.

This wraps process_pdf and registers the file with the tracker using UUIDs.

**Parameters:**
- `pdf_path`: Path to the PDF file
- `group_name`: Group name for the file
- `project_root`: Root directory for relative path calculation
- `file_tracker`: FileTracker instance

**Returns:**
- Metadata dictionary with UUID, or the failure dict from process_pdf

**Behavior:**
- Processes the PDF normally
- Generates or retrieves UUID from the file tracker
- Registers file with tracker including citation key, group, and metadata
- Adds `pdf_uuid` field to metadata for persistent identification

---

```python
def process_pdf(self, pdf_path: Path) -> Optional[Dict]
```
Process a single PDF file through all extraction strategies.

**Parameters:**
- `pdf_path`: Path to PDF file

**Returns:**
- `Dict`: Citation metadata dictionary on success
- `Dict`: Failure dictionary with `"_failed": True` on extraction failure (includes error details and fallback citation key)
- `None`: Only in unexpected error cases (rare)

**Strategy Order:**
1. Extract embedded metadata from PDF
2. Extract DOI and query CrossRef
3. Use GROBID if enabled and previous strategies failed
4. On failure: Generate fallback citation key from filename

**Failure Dictionary Structure:**
```python
{
    "_failed": True,
    "pdf_path": str,       # Full path to the PDF file
    "error": str,         # Reason for extraction failure
    "would_be_key": str   # Fallback citation key for manual entry creation
}
```

---

```python
def process_directory(self, directory: Path, output_path: Optional[Path] = None) -> Dict[str, List[Dict]]
```
**UPDATED in v0.2.0:** Process all PDF files in a directory with file tracking.

Process all PDF files in a directory and its subdirectories. Files are grouped by their immediate parent directory name. Files in the root directory are grouped under "General".

**NEW:** Now accepts `output_path` parameter to initialize the file tracker in the same directory as the output file.

**Parameters:**
- `directory`: Directory to search for PDF files
- `output_path`: Optional path to the output bib-file. If provided, used to initialize the file tracker.

**Returns:**
- Dictionary mapping group names to lists of citation metadata

**NEW Features:**
- Integrates with FileTracker for persistent file identification
- Cleans up missing file entries from tracker
- Tracks UUIDs for each processed file
- Provides better error handling and failure tracking

**Failure Tracking:**
Failed extractions are stored in `self._last_failed_files` as a list of dictionaries with:
- `path`: Full path to the failed PDF
- `relative_path`: Path relative to the input directory
- `group`: Group name the file would belong to
- `error`: Reason for failure
- `would_be_key`: Fallback citation key for manual JabRef entry creation

---

```python
def _export_to_bibtex(self, citations: Dict[str, List[Dict]], output_path: Path, overwrite: bool = False) -> bool
```
**UPDATED in v0.2.0:** Export grouped citations to BibTeX file with advanced merge support.

**NEW Features:**
- **UUID-based duplicate detection**: Recognizes same files even when citation keys change
- **Preserve manually added entries**: Entries without UUID are kept during merge
- **Fallback for malformed BibTeX**: If parsing fails, preserves original content
- **Enhanced JabRef metadata**: Generates comprehensive group metadata
- **Better logging**: Detailed counts of new, updated, and preserved entries

**Parameters:**
- `citations`: Dictionary mapping group names to lists of citation metadata
- `output_path`: Path to output .bib file
- `overwrite`: If True, overwrite existing file. If False (default), merge with existing.

**Returns:**
- True if successful, False otherwise

**Merge Behavior (overwrite=False):**
When merge mode is enabled (default):
- Reads existing `.bib` file if it exists
- Parses all existing entries and preserves them
- Detects existing entries by UUID to prevent duplicates
- Entries without UUID (manually added) are preserved
- Adds only new, non-duplicate entries
- Maintains JabRef group metadata from existing file
- Writes all entries (existing + new) to the output file

**Overwrite Behavior (overwrite=True):**
When overwrite is True:
- Creates a fresh file
- All existing entries are discarded
- Only new citations are written to the file

**UUID-Based Merge Logic:**
1. Builds mapping of UUID to entry ID for existing entries
2. For each new citation, checks if UUID already exists
3. If UUID found: updates existing entry with new metadata but preserves citation key
4. If no UUID: adds as new entry with unique citation key
5. Ensures entries without UUID (manually added) are preserved

---

```python
def export_citations(self, citations: Dict[str, List[Dict]], output_path: Path, 
                     format: str = "bibtex", overwrite: bool = False) -> bool
```
Export citations to file.

**Parameters:**
- `citations`: Dictionary mapping group names to lists of citation metadata
- `output_path`: Output file path
- `format`: Export format (currently only 'bibtex' supported)
- `overwrite`: If True, overwrite existing file. If False (default), merge with existing.

**Returns:**
- True if successful

---

#### CLI Commands

The CLI is built using Click library and provides the following interface:

```bash
# Process a directory of PDFs
python -m src.main --dir ./papers --output references.bib

# Process a single PDF
python -m src.main --pdf paper.pdf --output citation.bib

# Use custom config
python -m src.main --dir ./papers --config my_config.yaml

# Enable verbose logging
python -m src.main --dir ./papers --verbose

# Overwrite existing file
python -m src.main --dir ./papers --output references.bib --overwrite

# Show tracked files
python -m src.main --output references.bib --show-tracker

# Clean up missing file entries
python -m src.main --output references.bib --cleanup-tracker
```

**CLI Options:**

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--dir` | `-d` | Path | - | Directory containing PDF files |
| `--pdf` | `-p` | Path | - | Single PDF file to process |
| `--output` | `-o` | Path | `citations.bib` | Output file path |
| `--format` | `-f` | Choice | `bibtex` | Output format |
| `--config` | `-c` | Path | - | Path to config.yaml file |
| `--verbose` | `-v` | Flag | False | Enable verbose logging |
| `--overwrite` | - | Flag | False | Overwrite existing file instead of merging |
| `--show-tracker` | - | Flag | False | Show all tracked files and exit |
| `--cleanup-tracker` | - | Flag | False | Clean up missing file entries and exit |

**Note:** Either `--dir` or `--pdf` must be specified, but not both.

---

### 5.2 API Clients

#### Module: `api_clients/__init__.py`

**Exports:** `CrossRefClient`

---

#### Module: `api_clients/crossref.py`

**Purpose:** Provides CrossRef API client for fetching metadata from DOI identifiers.

**Dependencies:**
- `habanero` library (CrossRef Python client)

##### Class: `CrossRefClient`

**Description:** Client for querying the CrossRef API to retrieve publication metadata.

**Attributes:**
- `client` (Crossref): Habanero CrossRef client instance

**Methods:**

```python
def __init__(self, email: Optional[str] = None)
```
Initialize CrossRef client.

**Parameters:**
- `email`: Email for polite pool (faster API access). When provided, requests are made through the "polite pool" which has higher rate limits.

**Example:**
```python
from src.api_clients import CrossRefClient
client = CrossRefClient(email="user@example.com")
```

---

```python
def get_metadata(self, doi: str) -> Optional[Dict]
```
Fetch metadata for a DOI from CrossRef.

**Parameters:**
- `doi`: Digital Object Identifier (e.g., "10.1038/nature12373")

**Returns:**
- Dictionary with normalized citation metadata, or None if not found

**Metadata Fields Extracted:**
- `title`: Publication title
- `author`: Authors (formatted as "First Last and First Last")
- `year`: Publication year
- `journal`: Journal/container title
- `volume`: Volume number
- `issue`: Issue number
- `pages`: Page range
- `publisher`: Publisher
- `type`: Publication type (article, book, etc.)
- `abstract`: Abstract text
- `issn`: ISSN identifier
- `isbn`: ISBN identifier (for books)
- `url`: URL
- `doi`: The DOI itself

**Example:**
```python
metadata = client.get_metadata("10.1038/nature12373")
# Returns: {'title': '...', 'author': '...', 'year': '2020', ...}
```

---

```python
def _parse_crossref_response(self, message: Dict) -> Dict
```
Parse CrossRef API response into normalized metadata format.

**Parameters:**
- `message`: CrossRef API message object from works() response

**Returns:**
- Normalized metadata dictionary

---

```python
def search_by_title(self, title: str, limit: int = 5) -> list
```
Search CrossRef by title when DOI is not available.

**Parameters:**
- `title`: Publication title or partial title
- `limit`: Maximum number of results to return (default: 5)

**Returns:**
- List of potential matches (each as metadata dictionary)

---

### 5.3 Extractors

#### Module: `extractors/__init__.py`

**Exports:**
- `PDFMetadataExtractor`
- `DOIExtractor`
- `GROBIDClient`

---

#### Module: `extractors/pdf_metadata.py`

**Purpose:** Extract embedded metadata from PDF files using PyMuPDF.

**Dependencies:**
- `PyMuPDF` (fitz)

##### Class: `PDFMetadataExtractor`

**Description:** Extracts document properties and metadata embedded in PDF files.

**Attributes:**
- `supported_fields`: List of supported PDF metadata fields

**Methods:**

```python
def __init__(self)
```
Initialize the PDF metadata extractor.

---

```python
def extract(self, pdf_path: Path) -> Dict[str, Optional[str]]
```
Extract metadata from a PDF file.

**Parameters:**
- `pdf_path`: Path to the PDF file

**Returns:**
- Dictionary containing metadata fields:
  - `title`: Document title
  - `author`: Author information
  - `subject`: Subject/description
  - `keywords`: Keywords
  - `creator`: Creator application
  - `producer`: Producer application
  - `creation_date`: Creation timestamp
  - `mod_date`: Modification timestamp
  - `doi`: DOI if found in metadata (optional)

---

```python
def _clean_field(self, field: Optional[str]) -> Optional[str]
```
Clean and normalize a metadata field.

**Parameters:**
- `field`: Raw metadata field value

**Returns:**
- Cleaned field or None if empty/invalid

**Cleaning Rules:**
- Strips leading/trailing whitespace
- Returns None for empty, "unknown", "none", or "null" values

---

```python
def has_useful_metadata(self, metadata: Dict[str, Optional[str]]) -> bool
```
Check if metadata contains useful information.

**Parameters:**
- `metadata`: Metadata dictionary to check

**Returns:**
- True if at least `title` or `author` is present and non-empty

---

#### Module: `extractors/doi_extractor.py`

**Purpose:** Extract DOI (Digital Object Identifier) from PDF text content.

**Dependencies:**
- `PyMuPDF` (fitz)
- `re` (regex)

##### Class: `DOIExtractor`

**Description:** Scans PDF text content to find DOI identifiers using regex patterns.

**Attributes:**
- `scan_pages` (int): Number of pages to scan (default: 3)
- `patterns` (List[str]): List of regex patterns for DOI detection

**DOI Patterns:**
1. Standard DOI: `10\.\d{4,9}/[-._;()/:A-Z0-9]+`
2. DOI with prefix: `doi:\s*10\.\d{4,9}/[-._;()/:A-Z0-9]+`
3. DOI with URL: `https?://doi\.org/10\.\d{4,9}/[-._;()/:A-Z0-9]+`
4. DOI with dx.doi.org: `https?://dx\.doi\.org/10\.\d{4,9}/[-._;()/:A-Z0-9]+`

**Methods:**

```python
def __init__(self, scan_pages: int = 3)
```
Initialize DOI extractor.

**Parameters:**
- `scan_pages`: Number of pages to scan for DOI (default: 3)

---

```python
def extract(self, pdf_path: Path) -> Optional[str]
```
Extract a single DOI from PDF file.

**Parameters:**
- `pdf_path`: Path to the PDF file

**Returns:**
- DOI string if found, None otherwise

**Behavior:**
- Opens PDF with PyMuPDF
- Scans first N pages (configurable)
- Returns first DOI found
- Closes PDF after extraction

---

```python
def extract_multiple(self, pdf_path: Path) -> List[str]
```
Extract all DOIs found in a PDF.

**Parameters:**
- `pdf_path`: Path to the PDF file

**Returns:**
- List of unique DOI strings found in the PDF

**Use Case:** Useful for extracting DOIs from reference lists in papers.

---

```python
def _clean_doi(self, doi: str) -> str
```
Clean DOI string by removing prefixes and URLs.

**Parameters:**
- `doi`: Raw DOI string with possible prefixes

**Returns:**
- Cleaned DOI (just the identifier part)

**Cleaning Rules:**
- Removes `https://doi.org/` and `http://doi.org/` prefixes
- Removes `https://dx.doi.org/` and `http://dx.doi.org/` prefixes
- Removes `doi:` prefix
- Removes trailing punctuation (.,;:)
- Trims whitespace

---

#### Module: `extractors/grobid_client.py`

**Purpose:** Client for GROBID service for advanced PDF metadata extraction.

**Dependencies:**
- `requests` library
- `xml.etree.ElementTree`

##### Class: `GROBIDClient`

**Description:** Client for the GROBID (GeneRation Of BIbliographic Data) machine learning service. GROBID can extract bibliographic data from PDFs that lack proper metadata.

**Requirements:**
- Docker must be installed and running
- GROBID Docker image must be running: `lfoppiano/grobid:0.8.0`
- Service runs on port 8070 by default

**Setup Commands:**
```bash
# Pull GROBID image
docker pull lfoppiano/grobid:0.8.0

# Run GROBID service
docker run -t --rm -p 8070:8070 lfoppiano/grobid:0.8.0

# Verify service is running
curl http://localhost:8070/api/isalive
```

**Attributes:**
- `grobid_url` (str): URL of GROBID service (default: "http://localhost:8070")
- `available` (bool): Whether the service is reachable
- `TEI_NS` (dict): TEI XML namespace for parsing

**Methods:**

```python
def __init__(self, grobid_url: str = "http://localhost:8070")
```
Initialize GROBID client.

**Parameters:**
- `grobid_url`: URL of GROBID service

**Behavior:**
- Checks if service is available during initialization
- Logs availability status

---

```python
def process(self, pdf_path: Path) -> Optional[Dict]
```
Process PDF using GROBID service to extract metadata.

**Parameters:**
- `pdf_path`: Path to PDF file

**Returns:**
- Citation metadata dictionary or None if processing failed

**API Endpoint:**
- POST to `{grobid_url}/api/processHeaderDocument`

---

```python
def is_available(self) -> bool
```
Check if GROBID service is available.

**Returns:**
- True if service responds to health check

**Health Check Endpoint:**
- GET `{grobid_url}/api/isalive`

---

### 5.4 Exporters

#### Module: `exporters/__init__.py`

**Exports:** `BibTeXExporter`

---

#### Module: `exporters/bibtex.py`

**Purpose:** Exports citation metadata to BibTeX format.

**Dependencies:**
- `bibtexparser` library

##### Class: `BibTeXExporter`

**Description:** Converts citation metadata dictionaries to BibTeX format.

**Attributes:**
- `entry_types` (Dict): Mapping from CrossRef types to BibTeX entry types

**Entry Type Mapping:**
```python
{
    "journal-article": "article",
    "book": "book",
    "book-chapter": "inbook",
    "proceedings-article": "inproceedings",
    "report": "techreport",
    "dissertation": "phdthesis",
}
```

**Methods:**

```python
def __init__(self)
```
Initialize BibTeX exporter.

---

```python
def _extract_existing_jabref_metadata(self, content: str) -> str
```
**NEW in v0.2.0:** Extract JabRef metadata comments from existing BibTeX file content.

**Purpose:** Preserves existing JabRef metadata (groups, preferences, etc.) when merging.

**Parameters:**
- `content`: The raw content of the .bib file

**Returns:**
- String containing JabRef metadata comments, or empty string if none found

---

```python
def export(self, citations: List[Dict], output_path: Path) -> bool
```
Export citations to BibTeX file.

**Parameters:**
- `citations`: List of citation metadata dictionaries
- `output_path`: Path to output .bib file

**Returns:**
- True if successful, False otherwise

**Features:**
- Creates BibDatabase from citations
- Writes to UTF-8 encoded file
- Uses proper indentation (2 spaces)
- Sorts entries by ID, author, title
- Generates JabRef group metadata

---

```python
def _create_bibtex_entry(self, metadata: Dict) -> Dict
```
Create a BibTeX entry from metadata.

**Parameters:**
- `metadata`: Citation metadata dictionary

**Returns:**
- BibTeX entry dictionary

**NEW in v0.2.0:** Now includes `pdf_uuid` field if present in metadata for file tracking.

**Entry Structure:**
```python
{
    "ID": "CitationKey",
    "ENTRYTYPE": "article",
    "author": "Author Name",
    "title": "Paper Title",
    "year": "2020",
    "journal": "Journal Name",
    "pdf_uuid": "UUID_for_tracking",  # NEW in v0.2.0
    # ... other fields
}
```

---

```python
def _get_entry_type(self, crossref_type: str) -> str
```
Map CrossRef type to BibTeX entry type.

**Parameters:**
- `crossref_type`: CrossRef publication type

**Returns:**
- BibTeX entry type (default: "misc" if unknown)

---

```python
def _generate_citation_key(self, metadata: Dict) -> str
```
Generate a base citation key from metadata.

**UPDATED in v0.2.0:** New format without underscores: `FirstAuthorLastNameYear`

**Note:** Uniqueness (adding 'a', 'b', etc.) is handled at a higher level in the merge logic, not here.

**Parameters:**
- `metadata`: Citation metadata

**Returns:**
- Base citation key string (may need suffix added for uniqueness)

**Algorithm:**
1. Extract first author's last name (last word of first author)
2. Extract year (or "YYYY" if not available)
3. Combine: `{author_part}{year_part}`
4. Remove special characters (keep only alphanumeric)

**Example:**
```python
metadata = {
    "author": "John Doe and Jane Smith",
    "year": "2020",
    "title": "The Impact of Machine Learning"
}
key = exporter._generate_citation_key(metadata)
# Returns: "Doe2020"
```

---

```python
def _clean_entry(self, entry: Dict) -> Dict
```
Clean BibTeX entry by removing None values.

**Parameters:**
- `entry`: BibTeX entry

**Returns:**
- Cleaned entry

---

```python
def _generate_jabref_group_metadata(self, citations: List[Dict]) -> str
```
**NEW in v0.2.0:** Generate JabRef group metadata as @Comment entries.

**Purpose:** Creates native JabRef groups that are displayed in the JabRef UI.

**Parameters:**
- `citations`: List of citation metadata dictionaries

**Returns:**
- String containing JabRef group metadata, or empty string if no groups

**Group Metadata Format:**
```bibtex
@Comment{jabref-meta: databaseType:bibtex;}

@Comment{jabref-meta: grouping:
0 AllEntriesGroup:;
1 StaticGroup:GroupName\;0\;1\;0x8a8a8aff\;\;\;;
}
```

**Group Depth:**
- Groups are sorted by depth first, then by name
- Default depth is 1 if not specified in citation metadata
- StaticGroup format: `{depth} StaticGroup:{escaped_name}\\;0\\;1\\;0x8a8a8aff\\;\\;\\;;`

---

```python
def export_single(self, metadata: Dict) -> str
```
Export a single citation to BibTeX string.

**Parameters:**
- `metadata`: Citation metadata dictionary

**Returns:**
- BibTeX formatted string

**Use Case:** Useful for displaying or returning a single citation without writing to file.

---

### 5.5 Trackers

#### Module: `trackers/__init__.py`

**NEW in v0.2.0:** Exports FileTracker and FileTrackerEntry

---

#### Module: `trackers/file_tracker.py`

**NEW in v0.2.0:** File tracking system for persistent PDF-to-BibTeX identification.

**Purpose:** Provides a tracking system that maintains persistent links between PDF files and their BibTeX entries using UUIDs. This ensures that files can be identified even when citation keys change in tools like JabRef.

**Storage:** The tracker stores a JSON file (`.pdf_tracker.json`) in the same directory as the output bib-file.

**Tracked Information:**
- UUID for each tracked file (deterministic, based on file path + metadata)
- File paths (absolute and relative)
- File hashes (SHA-256 of content)
- Citation keys
- File sizes and modification timestamps
- Timestamps for tracking when files were first/last seen
- Additional metadata (group, source, etc.)

**Key Benefits:**
1. **Persistent Identification**: Same file always gets same UUID
2. **Citation Key Independence**: Files can be identified even when citation keys change
3. **Smart Merge**: Prevents duplicate entries when re-processing same files
4. **Missing File Cleanup**: Automatically removes entries for deleted files
5. **Cross-Session Tracking**: Tracks files across different program runs

#### Data Classes

##### `FileTrackerEntry`

**Description:** Represents a tracked file entry in the tracker system.

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

---

##### Class: `FileTracker`

**Description:** Tracks PDF files and their UUIDs for persistent identification.

**Constants:**
- `TRACKER_FILE` = ".pdf_tracker.json"
- `BIBTEX_UUID_FIELD` = "pdf_uuid" (Custom BibTeX field name for UUID)

**Methods:**

```python
def __init__(self, output_dir: Union[Path, str])
```
Initialize the file tracker.

**Parameters:**
- `output_dir`: Directory where the bib-file is stored. The tracker file (`.pdf_tracker.json`) will be created here.

**Example:**
```python
from src.trackers import FileTracker
tracker = FileTracker(output_dir="/path/to/output")
```

---

```python
def generate_uuid(self, file_path: Path) -> str
```
Generate a deterministic UUID for a file.

**Purpose:** The UUID is based on the absolute path, last modified time, and file size. This ensures the same file always gets the same UUID, making it stable across sessions and independent of citation key changes.

**Parameters:**
- `file_path`: Path to the PDF file

**Returns:**
- Deterministic UUID string (using UUID5 with NAMESPACE_URL)

**Algorithm:**
```python
abs_path = file_path.resolve()
stat = abs_path.stat()
unique_string = f"{abs_path}|{stat.st_mtime}|{stat.st_size}"
return str(uuid.uuid5(uuid.NAMESPACE_URL, unique_string))
```

---

```python
def get_file_hash(self, file_path: Path) -> str
```
Calculate SHA-256 hash of file content.

**Parameters:**
- `file_path`: Path to the file

**Returns:**
- Hex-encoded SHA-256 hash

---

```python
def register_file(self, file_path: Path, citation_key: str,
                  project_root: Optional[Path] = None,
                  metadata: Optional[Dict] = None) -> Tuple[str, bool]
```
Register a file and get its UUID.

**Main Method:** This is the primary method for tracking files. It will:
- Generate or retrieve the UUID for the file
- Update the file's metadata in the tracker
- Save the tracker state to disk

**Parameters:**
- `file_path`: Path to the PDF file
- `citation_key`: Current citation key for the BibTeX entry
- `project_root`: Root directory for calculating relative paths
- `metadata`: Optional additional metadata to store (e.g., group, source)

**Returns:**
- Tuple of `(uuid, is_new)` where `is_new` is True if this is the first time the file is being tracked

**Example:**
```python
uuid, is_new = tracker.register_file(
    file_path=Path("/path/to/paper.pdf"),
    citation_key="Author_2023_Title",
    project_root=Path("/path/to/project"),
    metadata={"group": "MachineLearning", "source": "crossref"}
)
print(f"UUID: {uuid}, Is new: {is_new}")
```

---

```python
def get_uuid_by_path(self, file_path: Path) -> Optional[str]
```
Get UUID for a given file path.

**Parameters:**
- `file_path`: Path to look up

**Returns:**
- UUID string or None if not found

---

```python
def get_entry_by_path(self, file_path: Path) -> Optional[FileTrackerEntry]
```
Get full entry for a given file path.

**Parameters:**
- `file_path`: Path to look up

**Returns:**
- FileTrackerEntry or None if not found

---

```python
def get_path_by_uuid(self, uuid: str) -> Optional[Path]
```
Get file path for a given UUID.

**Parameters:**
- `uuid`: UUID to look up

**Returns:**
- Path or None if not found

---

```python
def get_entry(self, uuid: str) -> Optional[FileTrackerEntry]
```
Get full entry for a UUID.

**Parameters:**
- `uuid`: UUID to look up

**Returns:**
- FileTrackerEntry or None

---

```python
def update_citation_key(self, uuid: str, new_citation_key: str) -> bool
```
Update citation key for a tracked file.

**Purpose:** Useful when citation keys change in JabRef or other tools.

**Parameters:**
- `uuid`: UUID of the file
- `new_citation_key`: New citation key

**Returns:**
- True if updated successfully, False if UUID not found

---

```python
def list_all_entries(self) -> List[FileTrackerEntry]
```
Get all tracked entries.

**Returns:**
- List of all FileTrackerEntry objects

---

```python
def remove_file(self, file_path: Path) -> bool
```
Remove a file from tracking.

**Parameters:**
- `file_path`: Path to remove

**Returns:**
- True if removed successfully, False if not found

---

```python
def cleanup_missing_files(self) -> int
```
Remove entries for files that no longer exist.

**Purpose:** This should be called periodically to keep the tracker clean.

**Returns:**
- Number of entries removed

**Example:**
```python
removed = tracker.cleanup_missing_files()
print(f"Cleaned up {removed} missing file entries")
```

---

```python
def get_files_by_group(self, group_name: str) -> List[FileTrackerEntry]
```
Get all entries that belong to a specific group.

**Parameters:**
- `group_name`: Group name to filter by

**Returns:**
- List of entries in the specified group

---

```python
def get_updated_files(self, since: Optional[str] = None) -> List[FileTrackerEntry]
```
Get files that have been updated since a specific time.

**Parameters:**
- `since`: ISO timestamp string. If None, returns all files.

**Returns:**
- List of entries updated since the specified time

---

```python
def reset(self) -> None
```
Clear all tracked entries.

**WARNING:** This will remove all tracking data!

---

## Class Reference

### Quick Reference Table

| Class | Module | Purpose | Key Methods |
|-------|--------|---------|--------------|
| `CitationExtractor` | main.py | Orchestrator | `process_pdf()`, `process_directory()`, `export_citations()` |
| `CrossRefClient` | api_clients/crossref.py | CrossRef API | `get_metadata()`, `search_by_title()` |
| `PDFMetadataExtractor` | extractors/pdf_metadata.py | PDF metadata | `extract()`, `has_useful_metadata()` |
| `DOIExtractor` | extractors/doi_extractor.py | DOI extraction | `extract()`, `extract_multiple()` |
| `GROBIDClient` | extractors/grobid_client.py | GROBID service | `process()`, `is_available()` |
| `BibTeXExporter` | exporters/bibtex.py | BibTeX export | `export()`, `export_single()` |
| `FileTracker` | trackers/file_tracker.py | File tracking | `register_file()`, `cleanup_missing_files()` |
| `FileTrackerEntry` | trackers/file_tracker.py | Tracker data | Data class for tracked files |

---

## Configuration

### Configuration File: `config.yaml`

```yaml
# Email for CrossRef API (polite pool - faster response)
# Leave empty for public pool
crossref_email: ""

# Output settings
default_output_format: "bibtex"  # bibtex, ris, json (only bibtex currently supported)
output_directory: "./output"

# Extraction settings
extraction:
  # Number of pages to scan for DOI
  doi_scan_pages: 3

  # Fallback strategy order
  strategy:
    - "embedded_metadata"
    - "doi_lookup"
    - "grobid"  # Requires GROBID Docker service running

# GROBID service configuration
grobid_url: "http://localhost:8070"

# Cache settings (future feature)
cache:
  enabled: false
  directory: "./.cache"
```

### Default Configuration

If no config file is found, the following defaults are used:

```python
{
    "crossref_email": None,
    "default_output_format": "bibtex",
    "output_directory": "./output",
    "extraction": {
        "doi_scan_pages": 3,
        "strategy": ["embedded_metadata", "doi_lookup"]
    }
}
```

---

## Dependencies

### Production Dependencies (`requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| PyMuPDF | >=1.23.0 | PDF processing (fitz) |
| pypdf | >=3.17.0 | Alternative PDF processing |
| requests | >=2.31.0 | HTTP requests |
| habanero | >=1.2.6 | CrossRef API client |
| bibtexparser | >=1.4.0 | BibTeX export |
| click | >=8.1.7 | CLI interface |
| tqdm | >=4.66.0 | Progress bars |
| python-dotenv | >=1.0.0 | Environment variables |
| pyyaml | >=6.0.1 | YAML configuration |

### Development Dependencies (`requirements-dev.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=7.4.0 | Testing |
| black | >=23.7.0 | Code formatting |
| flake8 | >=6.1.0 | Linting |
| mypy | >=1.5.0 | Type checking |

### Optional Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| grobid-client-python | >=0.0.5 | GROBID client (alternative to requests-based client) |

---

## Data Flow

### Single PDF Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      CitationExtractor.process_pdf()            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Strategy 1: Embedded Metadata                 │
│                 PDFMetadataExtractor.extract()                  │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
    Has useful metadata?                 No/Not enough
          (title or author)                    │
              │                               ▼
              ▼                 ┌─────────────────────────────┐
┌─────────────────────┐     │         Strategy 2: DOI        │
│   Return metadata    │     │      DOIExtractor.extract()     │
│   (source=embedded)  │     └─────────────────────────────┘
└─────────────────────┘                   │
                                      ▼
                            Found DOI?
                  ┌─────────────────┴─────────────────┐
                  ▼                                     ▼
            Yes                                   No
                  │                                     │
                  ▼                                     ▼
    ┌─────────────────────┐       ┌─────────────────────────┐
    │ CrossRefClient       │       │      Strategy 3: GROBID     │
    │ get_metadata(doi)    │       │   GROBIDClient.process()   │
    └─────────────────────┘       └─────────────────────────┘
            │                                     │
            ▼                                     ▼
    Metadata returned              Metadata returned
            │                                     │
            └─────────────┬─────────────────┘
                          ▼
                  Merge metadata (CrossRef takes precedence)
                          │
                          ▼
                Return citation metadata
```

### Batch Processing Flow with File Tracking (NEW in v0.2.0)

```
┌─────────────────────────────────────────────────────────────┐
│                 CitationExtractor.process_directory()          │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
    Find all PDF files in          No PDF files found
    directory                          │
              │                               ▼
              ▼                     Log warning & return []
┌─────────────────────────────────────────────────────────────┐
│                   For each PDF file:                            │
│                    _process_pdf_with_tracking()                  │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
       Success (metadata)              Failed (failure dict)
              │                               │
              ▼                               ▼
    Register with FileTracker     Add to _last_failed_files
    (get or create UUID)                │
              │                               │
              ▼                               ▼
    Add pdf_uuid to metadata     Track failure details
    Add group information              │
              │                               │
              └─────────────┬─────────────────┘
                            ▼
              ┌───────────────────────────────────────┐
              │  FileTracker.cleanup_missing_files()     │
              │  (Remove entries for deleted files)      │
              └───────────────────────────────────────┘
                            ▼
              ┌───────────────────────────────────────┐
              │  Display summary: successful vs failed   │
              │  (Write failed_extractions.log later)    │
              └───────────────────────────────────────┘
```

### Export Flow with UUID-Based Merge (NEW in v0.2.0)

```
┌─────────────────────────────────────────────────────────────┐
│                 CitationExtractor._export_to_bibtex()           │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
    overwrite=False?                    overwrite=True
              │                               │
              ▼                               ▼
    Read existing .bib file      Create fresh file
    (if exists)                    │
              │                               │
              ▼                               ▼
    Parse existing entries           Discard all existing
    Build UUID->entry mapping        entries
              │
              ▼
    For each new citation:
        1. Check if pdf_uuid exists in mapping
        2. If yes: Update existing entry
                   (preserve citation key, update metadata)
        3. If no: Add as new entry with unique key
        4. Preserve entries without UUID (manually added)
              │
              ▼
    Generate JabRef group metadata
              │
              ▼
    Write to file:
    1. JabRef metadata comments
    2. Group header comments
    3. All entries (existing + new + updated)
```

---

## Error Handling

The application uses comprehensive error handling with the following strategies:

### 1. try-except Blocks

All external operations (file I/O, API calls, PDF processing) are wrapped in try-except blocks with appropriate logging.

**Example from `main.py`:**
```python
try:
    metadata = self.process_pdf(pdf_path)
    if metadata:
        citations.append(metadata)
    else:
        failed_files.append(pdf_path.name)
except Exception as e:
    logger.error(f"Error processing {pdf_path.name}: {e}")
    failed_files.append(pdf_path.name)
```

### 2. Logging Levels

| Level | Usage | Example |
|-------|-------|---------|
| DEBUG | Detailed debugging information | Variable values, detailed processing steps |
| INFO | Normal operation messages | File processing started, metadata found |
| WARNING | Non-critical issues | No DOI found, service unavailable |
| ERROR | Recoverable errors | API failures, file read errors |

### 3. Graceful Degradation

The application uses a fallback strategy:

1. **Embedded Metadata**: Fastest, works for well-formatted PDFs
2. **DOI Lookup**: Requires DOI in PDF, queries external API
3. **GROBID**: Machine learning service for challenging PDFs (optional)

If one strategy fails, the next is tried automatically.

### 4. Failure Tracking and Logging

**Enhanced Error Handling:** The application now tracks detailed failure information to help users manually fix issues.

#### Failure Dictionary Structure
When extraction fails, methods return a failure dictionary instead of None:

```python
# process_pdf() on failure returns:
{
    "_failed": True,
    "pdf_path": "/path/to/file.pdf",
    "error": "No metadata extracted from any source",
    "would_be_key": "file_YYYY"
}
```

#### Failed Files Log
The `_write_failed_files_log()` method creates a comprehensive log file (`failed_extractions.log`) in the output directory with:
- Timestamp and output file reference
- JabRef-specific instructions for manual entry creation
- List of all failed files with would-be citation keys

This allows users to:
1. Identify which PDFs need manual attention
2. Create JabRef entries with the correct citation keys
3. Organize entries into the correct groups

### 5. Robust Merge Error Handling (NEW in v0.2.0)

When merging with existing BibTeX files, the application now:
- **Preserves original content on parse failure**: If bibtexparser cannot parse the existing file, the original content is preserved and new entries are appended
- **Handles malformed BibTeX**: Detects files with content but 0 parsed entries and treats them as parse failures
- **Protects manually added entries**: Entries without UUID (manually added) are preserved even during merge operations

---

## Logging

### Configuration

```python
# From main.py
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pdf_citation_extractor.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)
```

### Log Files

- **File**: `pdf_citation_extractor.log`
- **Format**: `YYYY-MM-DD HH:MM:SS - module.name - LEVEL - message`
- **Rotation**: Not implemented (file grows indefinitely)

### Verbose Mode

Enable verbose logging with `--verbose` or `-v` flag:

```python
if verbose:
    logging.getLogger().setLevel(logging.DEBUG)
```

### Log Messages

**Common Log Messages:**

| Module | Level | Message | Meaning |
|--------|-------|---------|---------|
| main | INFO | "Processing: {filename}" | PDF processing started |
| main | INFO | "Found DOI: {doi}" | DOI extracted from PDF |
| main | INFO | "Using embedded metadata" | Using PDF metadata |
| main | INFO | "Tracked new file: {filename} -> UUID: {uuid}" | NEW: File registered with tracker |
| main | WARNING | "Could not extract sufficient metadata" | All strategies failed |
| main | DEBUG | "Recognized existing entry via UUID {uuid}..." | NEW: UUID-based duplicate detection |
| crossref | INFO | "Querying CrossRef for DOI: {doi}" | CrossRef API call |
| crossref | WARNING | "No metadata found for DOI" | DOI not in CrossRef |
| doi_extractor | INFO | "Found DOI in {filename}: {doi}" | DOI found in PDF |
| doi_extractor | WARNING | "No DOI found in {filename}" | No DOI in PDF |
| grobid | INFO | "GROBID service available" | Service is running |
| grobid | WARNING | "GROBID service not available" | Service not running |
| file_tracker | DEBUG | "Cleaned up missing file: {path}" | NEW: Missing file cleanup |

---

## Usage Examples

### Programmatic Usage

```python
from pathlib import Path
from src.main import CitationExtractor

# Initialize extractor
extractor = CitationExtractor()

# Process a single PDF
metadata = extractor.process_pdf(Path("paper.pdf"))
print(metadata)

# Process a directory with file tracking
extractor = CitationExtractor()
citations = extractor.process_directory(Path("./papers"), output_path=Path("references.bib"))
print(f"Extracted {len(citations)} citations")

# Export to BibTeX
extractor.export_citations(citations, Path("output.bib"))
```

### Using File Tracker Directly

```python
from pathlib import Path
from src.trackers import FileTracker

# Create tracker for output directory
tracker = FileTracker(output_dir=Path("./output"))

# Register files
uuid1, is_new1 = tracker.register_file(
    Path("/path/to/paper1.pdf"),
    citation_key="Author_2023_Title",
    project_root=Path("/path/to/project"),
    metadata={"group": "MachineLearning", "source": "crossref"}
)

# List all tracked files
all_entries = tracker.list_all_entries()
for entry in all_entries:
    print(f"UUID: {entry.uuid}, File: {entry.file_path}, Key: {entry.citation_key}")

# Clean up missing files
removed = tracker.cleanup_missing_files()
print(f"Removed {removed} missing entries")
```

### Using Individual Components

```python
from pathlib import Path
from src.extractors import PDFMetadataExtractor, DOIExtractor
from src.api_clients import CrossRefClient

# Extract PDF metadata
pdf_extractor = PDFMetadataExtractor()
metadata = pdf_extractor.extract(Path("paper.pdf"))

# Extract DOI
doi_extractor = DOIExtractor()
doi = doi_extractor.extract(Path("paper.pdf"))

# Query CrossRef
crossref = CrossRefClient()
if doi:
    crossref_metadata = crossref.get_metadata(doi)
```

### Using Exporters

```python
from src.exporters import BibTeXExporter

# Export single citation
metadata = {
    "author": "John Doe",
    "title": "A Great Paper",
    "year": "2020",
    "journal": "Nature",
    "doi": "10.1038/example",
    "pdf_uuid": "abc123..."  # NEW: UUID for tracking
}

exporter = BibTeXExporter()

# Export to file
citations = [metadata]
exporter.export(citations, Path("output.bib"))

# Get as string
bibtex_str = exporter.export_single(metadata)
print(bibtex_str)
```

### CLI Usage with New Features

```bash
# Process directory with file tracking (automatic)
python -m src.main --dir ./papers --output references.bib

# Show all tracked files for a bib file
python -m src.main --output references.bib --show-tracker

# Clean up missing file entries
python -m src.main --output references.bib --cleanup-tracker

# Overwrite existing file (skip merge)
python -m src.main --dir ./papers --output references.bib --overwrite

# Verbose mode for debugging
python -m src.main --dir ./papers --output references.bib --verbose
```

---

## File Structure Summary

```
src/
├── __init__.py              # Package init, version
├── main.py                 # CLI entry point, CitationExtractor
│
├── api_clients/
│   ├── __init__.py         # Module exports (CrossRefClient)
│   └── crossref.py         # CrossRefClient class
│
├── extractors/
│   ├── __init__.py         # Module exports (PDFMetadataExtractor, DOIExtractor, GROBIDClient)
│   ├── pdf_metadata.py     # PDFMetadataExtractor class
│   ├── doi_extractor.py     # DOIExtractor class
│   └── grobid_client.py    # GROBIDClient class
│
├── exporters/
│   ├── __init__.py         # Module exports (BibTeXExporter)
│   └── bibtex.py           # BibTeXExporter class with JabRef group metadata
│
└── trackers/
    ├── __init__.py         # Module exports (FileTracker, FileTrackerEntry)
    └── file_tracker.py     # FileTracker class and FileTrackerEntry dataclass
```

**Total Lines of Code:** ~2,000 lines (including trackers module)

---

## Migration Guide (v0.1.0 to v0.2.0)

### For Users

1. **New `.pdf_tracker.json` files**: You'll notice new tracker files appearing in your output directories. These contain file tracking information and can be safely deleted if you want to reset tracking.

2. **New CLI options**: Use `--show-tracker` to view tracked files and `--cleanup-tracker` to remove entries for deleted files.

3. **Improved merge behavior**: The tool now better preserves existing BibTeX entries and handles duplicates more intelligently using UUIDs.

4. **Fallback citation keys**: The format has changed from `Filename_Year` to just `Filename` (cleaned).

### For Developers

1. **New module**: Import from `src.trackers` for file tracking functionality.

2. **New metadata field**: BibTeX entries now include `pdf_uuid` field for file tracking.

3. **Updated merge logic**: The `_export_to_bibtex` method now handles UUID-based duplicate detection.

4. **New methods**: `CitationExtractor` has new methods for file tracking (`_get_file_tracker`, `_process_pdf_with_tracking`, `_ensure_unique_citation_key`).

---

## Changelog

### v0.2.0 (2026-10-21)
- **NEW**: FileTracker system for persistent PDF-to-BibTeX identification using UUIDs
- **NEW**: CLI options `--show-tracker` and `--cleanup-tracker`
- **NEW**: JabRef group metadata generation in BibTeX exporter
- **NEW**: UUID-based merge logic to prevent duplicates and preserve manually added entries
- **NEW**: Enhanced failure tracking with file tracking integration
- **UPDATED**: Fallback citation key generation (simplified format)
- **UPDATED**: Process directory now accepts `output_path` parameter for tracker initialization
- **IMPROVED**: Error handling for malformed BibTeX files
- **IMPROVED**: Logging with file tracking information

### v0.1.0 (2026-10-20)
- Initial release with embedded metadata, DOI lookup, and GROBID support
- Basic merge functionality
- Failed files logging
- CLI interface

---

*Documentation generated for PDF Citation Extractor v0.2.0*
