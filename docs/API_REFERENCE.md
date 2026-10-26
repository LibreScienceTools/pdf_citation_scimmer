# PDF Citation Extractor - API Reference

**Version:** 0.1.0  
**Last Updated:** 2026-10-20

---

## Overview

This document provides a complete API reference for the PDF Citation Extractor library. It covers all public classes, methods, parameters, and return values.

---

## Table of Contents

1. [Main Classes](#main-classes)
2. [API Clients](#api-clients)
3. [Extractors](#extractors)
4. [Exporters](#exporters)
5. [Type Definitions](#type-definitions)
6. [Exception Handling](#exception-handling)

---

## Main Classes

### `CitationExtractor`

**Module:** `src.main`  
**Purpose:** Main orchestrator class for citation extraction

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

**Failure Structure:**
```python
{
    "_failed": True,
    "pdf_path": str,  # Full path to the PDF file
    "error": str,     # Reason for failure
    "would_be_key": str  # Suggested citation key for manual entry
}
```

**Example:**
```python
from pathlib import Path
from src.main import CitationExtractor

extractor = CitationExtractor()
result = extractor.process_pdf(Path("paper.pdf"))

if result and not result.get("_failed"):
    # Success
    print(f"Title: {result['title']}")
    print(f"Authors: {result['author']}")
    print(f"Year: {result['year']}")
elif result and result.get("_failed"):
    # Failed - handle the error
    print(f"Failed to extract: {result['error']}")
    print(f"Suggested citation key: {result['would_be_key']}")
```

---

##### `process_directory(directory: Path) -> Dict[str, List[Dict]]`

Process all PDF files in a directory and its subdirectories.

**Parameters:**
- `directory` (Path): Directory containing PDF files

**Returns:**
- `Dict[str, List[Dict]]`: Dictionary mapping group names to lists of citation metadata
  - Groups are based on subdirectory names
  - Files in root directory are grouped under "General"
  - Failed extractions are stored in `extractor._last_failed_files`

**Behavior:**
- Scans directory recursively for files with `.pdf` extension
- Displays progress bar using tqdm
- Logs successful and failed extractions
- Returns grouped citations (only successful extractions)
- Failed files are tracked and can be accessed via `_last_failed_files` attribute

**Example:**
```python
from pathlib import Path
from src.main import CitationExtractor

extractor = CitationExtractor()
citations = extractor.process_directory(Path("./papers"))

print(f"Successfully extracted {sum(len(c) for c in citations.values())} citations")
for group_name, group_citations in citations.items():
    print(f"\n{group_name}:")
    for citation in group_citations:
        print(f"  - {citation['pdf_file']}: {citation.get('title', 'No title')}")

# Access failed files if any
if extractor._last_failed_files:
    print(f"\nFailed: {len(extractor._last_failed_files)} files")
    for failure in extractor._last_failed_files:
        print(f"  - {failure['relative_path']}: {failure['error']}")
```

---

##### `export_citations(citations: Dict[str, List[Dict]], output_path: Path, format: str = "bibtex", overwrite: bool = False) -> bool`

Export citations to a file.

**Parameters:**
- `citations` (Dict[str, List[Dict]]): Dictionary mapping group names to lists of citation metadata
- `output_path` (Path): Path to output file
- `format` (str): Export format (default: "bibtex")
- `overwrite` (bool): If True, overwrite existing file. If False (default), merge with existing entries.

**Returns:**
- `bool`: True if export successful, False otherwise

**Supported Formats:**
- `"bibtex"`: BibTeX format (currently the only supported format)

**Merge Behavior (overwrite=False):**
- Reads existing `.bib` file if it exists
- Preserves all existing entries
- Adds only new, non-duplicate entries
- Duplicates are detected by citation keys
- JabRef group metadata is preserved

**Overwrite Behavior (overwrite=True):**
- Replaces the entire output file
- All existing entries are lost
- Creates a fresh `.bib` file with only the new citations

**Example:**
```python
from pathlib import Path
from src.main import CitationExtractor

extractor = CitationExtractor()
citations = extractor.process_directory(Path("./papers"))

# Export to BibTeX
success = extractor.export_citations(
    citations, 
    Path("references.bib"),
    format="bibtex"
)

if success:
    print("Export successful!")
```

---

##### `_generate_fallback_citation_key(pdf_path: Path) -> str`

Generate a fallback citation key from PDF path when metadata extraction fails.

**Parameters:**
- `pdf_path` (Path): Path to the PDF file

**Returns:**
- `str`: A valid BibTeX citation key based on the filename

**Key Generation:**
- Extracts the filename stem (without extension)
- Attempts to extract year from filename (patterns: `19xx`, `20xx`)
- Cleans special characters for BibTeX compatibility
- Format: `{CleanStem}_{YearOrYYYY}`

**Example:**
```python
from pathlib import Path
from src.main import CitationExtractor

extractor = CitationExtractor()
key = extractor._generate_fallback_citation_key(Path("Smith_2023_DeepLearning.pdf"))
# Returns: "Smith_2023_DeepLearning_2023"

key = extractor._generate_fallback_citation_key(Path("paper.pdf"))
# Returns: "paper_YYYY" (no year found in filename)
```

##### `_write_failed_files_log(failed_files: List[Dict], output_path: Path) -> None`

Write a detailed log file of failed extractions.

**Parameters:**
- `failed_files` (List[Dict]): List of failure dictionaries from `_last_failed_files`
- `output_path` (Path): Path to the output .bib file (log written to same directory)

**Behavior:**
- Creates `failed_extractions.log` in the output directory
- Log file location:
  - If `output_path` has a parent directory: uses that directory
  - Otherwise: uses `config.output_directory` (default: `./output`)
- Log format includes JabRef-specific instructions
- Each failure entry includes: file path, group, would-be citation key, error reason

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

**Example:**
```python
from pathlib import Path
from src.main import CitationExtractor

extractor = CitationExtractor()
failed = [
    {
        "path": "/papers/smith.pdf",
        "relative_path": "smith.pdf",
        "group": "General",
        "error": "No DOI found",
        "would_be_key": "smith_YYYY"
    }
]
extractor._write_failed_files_log(failed, Path("output/refs.bib"))
# Creates: output/failed_extractions.log
```

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

**Example:**
```python
from src.api_clients import CrossRefClient

# Public pool (no email)
client = CrossRefClient()

# Polite pool (with email)
client = CrossRefClient(email="researcher@example.com")
```

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

**Example:**
```python
from src.api_clients import CrossRefClient

client = CrossRefClient(email="user@example.com")
metadata = client.get_metadata("10.1038/nature12373")

if metadata:
    print(f"Title: {metadata['title']}")
    print(f"Authors: {metadata['author']}")
    print(f"Published in: {metadata['journal']} ({metadata['year']})")
```

---

##### `search_by_title(title: str, limit: int = 5) -> list`

Search CrossRef by title when DOI is not available.

**Parameters:**
- `title` (str): Publication title or partial title to search for
- `limit` (int): Maximum number of results to return (default: 5)

**Returns:**
- `list`: List of metadata dictionaries (potential matches)

**Example:**
```python
from src.api_clients import CrossRefClient

client = CrossRefClient()
matches = client.search_by_title("Deep Learning Survey", limit=3)

for match in matches:
    print(f"Title: {match.get('title')}")
    print(f"DOI: {match.get('doi')}")
    print(f"Year: {match.get('year')}")
    print("---")
```

---

## Extractors

### `PDFMetadataExtractor`

**Module:** `src.extractors.pdf_metadata`  
**Purpose:** Extract embedded metadata from PDF files

#### Constructor

```python
PDFMetadataExtractor()
```

**Example:**
```python
from src.extractors import PDFMetadataExtractor

extractor = PDFMetadataExtractor()
```

#### Methods

##### `extract(pdf_path: Path) -> Dict[str, Optional[str]]`

Extract metadata from a PDF file.

**Parameters:**
- `pdf_path` (Path): Path to the PDF file

**Returns:**
- `Dict[str, Optional[str]]`: Dictionary containing metadata fields:
  - `title`: Document title
  - `author`: Author information
  - `subject`: Subject/description
  - `keywords`: Keywords
  - `creator`: Creator application
  - `producer`: Producer application
  - `creation_date`: Creation timestamp
  - `mod_date`: Modification timestamp
  - `doi`: DOI if found in metadata

**Example:**
```python
from pathlib import Path
from src.extractors import PDFMetadataExtractor

extractor = PDFMetadataExtractor()
metadata = extractor.extract(Path("paper.pdf"))

print("PDF Metadata:")
for key, value in metadata.items():
    if value:
        print(f"  {key}: {value}")
```

---

##### `has_useful_metadata(metadata: Dict[str, Optional[str]]) -> bool`

Check if metadata contains useful information.

**Parameters:**
- `metadata` (Dict[str, Optional[str]]): Metadata dictionary to check

**Returns:**
- `bool`: True if at least `title` or `author` is present and non-empty

**Example:**
```python
from src.extractors import PDFMetadataExtractor

extractor = PDFMetadataExtractor()
metadata = extractor.extract(Path("paper.pdf"))

if extractor.has_useful_metadata(metadata):
    print("This PDF has useful metadata")
else:
    print("Metadata is insufficient")
```

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

**Example:**
```python
from src.extractors import DOIExtractor

# Scan first 3 pages (default)
extractor = DOIExtractor()

# Scan first 5 pages
extractor = DOIExtractor(scan_pages=5)
```

#### Methods

##### `extract(pdf_path: Path) -> Optional[str]`

Extract a single DOI from PDF file.

**Parameters:**
- `pdf_path` (Path): Path to the PDF file

**Returns:**
- `Optional[str]`: DOI string if found, None otherwise

**Behavior:**
- Opens PDF and scans the first N pages (as configured)
- Uses regex patterns to find DOI identifiers
- Returns the first DOI found
- Closes the PDF file after extraction

**Example:**
```python
from pathlib import Path
from src.extractors import DOIExtractor

extractor = DOIExtractor()
doi = extractor.extract(Path("paper.pdf"))

if doi:
    print(f"Found DOI: {doi}")
else:
    print("No DOI found in the first 3 pages")
```

---

##### `extract_multiple(pdf_path: Path) -> List[str]`

Extract all DOIs found in a PDF.

**Parameters:**
- `pdf_path` (Path): Path to the PDF file

**Returns:**
- `List[str]`: List of unique DOI strings found in the PDF

**Use Case:** Extract DOIs from reference lists in papers

**Example:**
```python
from pathlib import Path
from src.extractors import DOIExtractor

extractor = DOIExtractor()
dois = extractor.extract_multiple(Path("review_paper.pdf"))

print(f"Found {len(dois)} DOIs in references:")
for doi in dois:
    print(f"  - {doi}")
```

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

**Attributes:**
- `grobid_url` (str): The configured GROBID URL
- `available` (bool): Whether the GROBID service is reachable (checked on init)

**Example:**
```python
from src.extractors import GROBIDClient

# Using default URL (localhost:8070)
client = GROBIDClient()

# Using custom URL
client = GROBIDClient(grobid_url="http://grobid.example.com:8070")

# Check if service is available
if client.available:
    print("GROBID service is running!")
else:
    print("GROBID service is not available")
```

#### Methods

##### `process(pdf_path: Path) -> Optional[Dict]`

Process PDF using GROBID service to extract metadata.

**Parameters:**
- `pdf_path` (Path): Path to the PDF file

**Returns:**
- `Optional[Dict]`: Citation metadata dictionary, or None if processing failed

**Behavior:**
- Checks if GROBID service is available
- Validates PDF file exists
- Sends PDF to GROBID via HTTP POST
- Parses TEI XML response
- Returns normalized metadata

**Example:**
```python
from pathlib import Path
from src.extractors import GROBIDClient

client = GROBIDClient()

if client.available:
    metadata = client.process(Path("paper.pdf"))
    if metadata:
        print(f"Title: {metadata.get('title')}")
        print(f"Authors: {metadata.get('author')}")
        print(f"Year: {metadata.get('year')}")
```

---

##### `is_available() -> bool`

Check if GROBID service is available.

**Returns:**
- `bool`: True if service responds to health check

**Example:**
```python
from src.extractors import GROBIDClient

client = GROBIDClient()
if client.is_available():
    print("GROBID is ready!")
else:
    print("Start GROBID service first")
```

---

## Exporters

### `BibTeXExporter`

**Module:** `src.exporters.bibtex`  
**Purpose:** Export citation metadata to BibTeX format

#### Constructor

```python
BibTeXExporter()
```

**Example:**
```python
from src.exporters import BibTeXExporter

exporter = BibTeXExporter()
```

#### Methods

##### `export(citations: List[Dict], output_path: Path) -> bool`

Export citations to a BibTeX file.

**Parameters:**
- `citations` (List[Dict]): List of citation metadata dictionaries
- `output_path` (Path): Path to output .bib file

**Returns:**
- `bool`: True if export successful, False otherwise

**Example:**
```python
from pathlib import Path
from src.exporters import BibTeXExporter

exporter = BibTeXExporter()

citations = [
    {
        "title": "Deep Learning",
        "author": "John Doe",
        "year": "2020",
        "journal": "Nature",
        "doi": "10.1038/example"
    }
]

success = exporter.export(citations, Path("output.bib"))
if success:
    print("Exported successfully!")
```

---

##### `export_single(metadata: Dict) -> str`

Export a single citation to a BibTeX string.

**Parameters:**
- `metadata` (Dict): Citation metadata dictionary

**Returns:**
- `str`: BibTeX formatted string

**Example:**
```python
from src.exporters import BibTeXExporter

exporter = BibTeXExporter()

metadata = {
    "title": "A Great Paper",
    "author": "Jane Smith",
    "year": "2021",
    "journal": "Science"
}

bibtex_str = exporter.export_single(metadata)
print(bibtex_str)
```

**Output:**
```bibtex
@article{Smith_2021_Great,
  author = {Jane Smith},
  title = {A Great Paper},
  year = {2021},
  journal = {Science}
}
```

---

##### `_generate_citation_key(metadata: Dict) -> str`

Generate a citation key from metadata.

**Parameters:**
- `metadata` (Dict): Citation metadata

**Returns:**
- `str`: Citation key string

**Format:** `FirstAuthorLastName_Year_FirstTitleWord`

**Example:**
```python
from src.exporters import BibTeXExporter

exporter = BibTeXExporter()

metadata = {
    "author": "John Doe and Jane Smith",
    "year": "2020",
    "title": "The Impact of Machine Learning on Society"
}

key = exporter._generate_citation_key(metadata)
# Returns: "Doe_2020_Impact"
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

*For usage examples and quick start guide, see [QUICK_START.md](./QUICK_START.md)*
*For detailed source code documentation, see [SOURCE_CODE_DOCUMENTATION.md](./SOURCE_CODE_DOCUMENTATION.md)*
