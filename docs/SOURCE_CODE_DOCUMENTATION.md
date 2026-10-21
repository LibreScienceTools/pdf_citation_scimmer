# PDF Citation Extractor - Source Code Documentation

**Version:** 0.1.0  
**Last Updated:** 2026-10-20  
**Project:** pdf_citation_scimmer

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Module Documentation](#module-documentation)
   - [3.1 Main Module (`main.py`)](#31-main-module-mainpy)
   - [3.2 API Clients](#32-api-clients)
   - [3.3 Extractors](#33-extractors)
   - [3.4 Exporters](#34-exporters)
4. [Class Reference](#class-reference)
5. [Configuration](#configuration)
6. [Dependencies](#dependencies)
7. [Data Flow](#data-flow)
8. [Error Handling](#error-handling)
9. [Logging](#logging)

---

## Project Overview

The **PDF Citation Extractor** is a command-line tool that extracts citation metadata from PDF files and exports it to reference management formats (currently BibTeX). It uses a multi-strategy approach to extract metadata:

1. **Embedded Metadata**: Extracts metadata directly from the PDF's document properties
2. **DOI Lookup**: Scans PDF content for DOI identifiers and queries the CrossRef API
3. **GROBID Processing**: Uses the GROBID machine learning service for advanced extraction (optional)

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
└── exporters/
    ├── __init__.py      # Exporter module exports
    └── bibtex.py         # BibTeX format exporter
```

### Key Design Principles

- **Modular Design**: Each extraction method, API client, and exporter is a separate class
- **Fallback Strategy**: Multiple extraction strategies with automatic fallback
- **Configurable**: YAML-based configuration for customization
- **CLI-First**: Command-line interface with Click library
- **Logging**: Comprehensive logging to file and console
- **Progress Tracking**: tqdm progress bars for batch processing

---

## Module Documentation

---

### 3.1 Main Module (`main.py`)

**Purpose:** Provides the command-line interface and orchestrates the citation extraction process.

#### Classes

##### `CitationExtractor`

**Description:** Main orchestrator class that coordinates all extraction and export operations.

**Attributes:**
- `config` (Dict): Loaded configuration from YAML file
- `pdf_extractor` (PDFMetadataExtractor): Extractor for embedded PDF metadata
- `doi_extractor` (DOIExtractor): Extractor for DOI from PDF text
- `crossref_client` (CrossRefClient): Client for CrossRef API
- `bibtex_exporter` (BibTeXExporter): Exporter for BibTeX format
- `grobid_client` (GROBIDClient, optional): Client for GROBID service

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
def _load_config(self, config_path: Optional[Path]) -> Dict
```
Load configuration from YAML file with fallback to defaults.

**Parameters:**
- `config_path`: Path to config.yaml file

**Returns:**
- Dictionary with configuration settings

---

```python
def _default_config(self) -> Dict
```
Return default configuration values.

**Returns:**
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

```python
def process_pdf(self, pdf_path: Path) -> Optional[Dict]
```
Process a single PDF file through all extraction strategies.

**Parameters:**
- `pdf_path`: Path to PDF file

**Returns:**
- Citation metadata dictionary or None if extraction failed

**Strategy Order:**
1. Extract embedded metadata from PDF
2. Extract DOI and query CrossRef
3. Use GROBID if enabled and previous strategies failed

**Example:**
```python
metadata = extractor.process_pdf(Path("paper.pdf"))
```

---

```python
def process_directory(self, directory: Path) -> List[Dict]
```
Process all PDF files in a directory.

**Parameters:**
- `directory`: Directory containing PDF files

**Returns:**
- List of citation metadata dictionaries

**Features:**
- Scans directory for `.pdf` files
- Displays progress bar using tqdm
- Logs successful and failed extractions
- Returns aggregated results

---

```python
def export_citations(self, citations: List[Dict], 
                     output_path: Path, 
                     format: str = "bibtex") -> bool
```
Export citations to file.

**Parameters:**
- `citations`: List of citation metadata dictionaries
- `output_path`: Output file path
- `format`: Export format (default: "bibtex")

**Returns:**
- True if successful, False otherwise

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

**Note:** Either `--dir` or `--pdf` must be specified, but not both.

---

### 3.2 API Clients

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

**Note:** This method handles the various date formats and nested structures in CrossRef responses.

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

**Example:**
```python
matches = client.search_by_title("Deep Learning", limit=3)
```

---

### 3.3 Extractors

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

**Example:**
```python
from src.extractors import PDFMetadataExtractor
extractor = PDFMetadataExtractor()
metadata = extractor.extract(Path("paper.pdf"))
```

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

**Example:**
```python
if extractor.has_useful_metadata(metadata):
    # Metadata is useful
    pass
```

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
def _find_doi_in_text(self, text: str) -> Optional[str]
```
Find DOI in text using regex patterns.

**Parameters:**
- `text`: Text to search for DOIs

**Returns:**
- Cleaned DOI string if found

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

**Example:**
```python
raw_doi = "https://doi.org/10.1038/nature12373"
clean_doi = extractor._clean_doi(raw_doi)
# Returns: "10.1038/nature12373"
```

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

**Features:**
- Validates PDF existence
- Checks service availability
- Handles timeouts (30 seconds)
- Parses TEI XML response

---

```python
def _parse_tei_xml(self, xml_content: str) -> Optional[Dict]
```
Parse GROBID TEI XML response and extract metadata.

**Parameters:**
- `xml_content`: XML string from GROBID response

**Returns:**
- Metadata dictionary or None if parsing failed

**TEI XML Structure:**
- Title: `.//tei:titleStmt/tei:title`
- Authors: `.//tei:sourceDesc//tei:author` with `tei:forename` and `tei:surname`
- Date: `.//tei:publicationStmt/tei:date` with `when` attribute
- Journal: `.//tei:monogr/tei:title`
- DOI: `.//tei:idno[@type='DOI']`
- Abstract: `.//tei:abstract`

---

```python
def is_available(self) -> bool
```
Check if GROBID service is available.

**Returns:**
- True if service responds to health check

**Health Check Endpoint:**
- GET `{grobid_url}/api/isalive`

**Example:**
```python
from src.extractors import GROBIDClient
client = GROBIDClient()
if client.available:
    metadata = client.process(Path("paper.pdf"))
```

---

### 3.4 Exporters

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

---

```python
def _create_bibtex_entry(self, metadata: Dict) -> Dict
```
Create a BibTeX entry from metadata.

**Parameters:**
- `metadata`: Citation metadata dictionary

**Returns:**
- BibTeX entry dictionary

**Entry Structure:**
```python
{
    "ID": "CitationKey",
    "ENTRYTYPE": "article",
    "author": "Author Name",
    "title": "Paper Title",
    "year": "2020",
    "journal": "Journal Name",
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
Generate a citation key from metadata.

**Format:** `FirstAuthorLastName_Year_FirstTitleWord`

**Parameters:**
- `metadata`: Citation metadata

**Returns:**
- Citation key string

**Algorithm:**
1. Extract first author's last name (last word of first author)
2. Extract year (or "YYYY" if not available)
3. Extract first significant word from title (excluding articles)
4. Combine: `{author_part}_{year_part}_{title_part}`
5. Remove special characters (keep only alphanumeric and underscore)

**Example:**
```python
metadata = {
    "author": "John Doe and Jane Smith",
    "year": "2020",
    "title": "The Impact of Machine Learning"
}
key = exporter._generate_citation_key(metadata)
# Returns: "Doe_2020_Impact"
```

---

```python
def _clean_entry(self, entry: Dict) -> Dict
```
Clean BibTeX entry by removing None values.

**Parameters:**
- `entry`: BibTeX entry dictionary

**Returns:**
- Cleaned entry with None values removed

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

### Batch Processing Flow

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
│                    process_pdf(pdf_path)                        │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
       Success (metadata)              Failed (None/exception)
              │                               │
              ▼                               ▼
    Add to citations list        Add to failed_files list
              │                               │
              └─────────────┬─────────────────┘
                            ▼
              ┌───────────────────────────────────────┐
              │  Display summary: successful vs failed   │
              └───────────────────────────────────────┘
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

### 4. None Handling

All methods return `None` or empty structures rather than raising exceptions for expected failures:

```python
# DOIExtractor
def extract(self, pdf_path: Path) -> Optional[str]:
    # Returns None if DOI not found

# CrossRefClient
def get_metadata(self, doi: str) -> Optional[Dict]:
    # Returns None if DOI not in CrossRef

# GROBIDClient
def process(self, pdf_path: Path) -> Optional[Dict]:
    # Returns None if processing fails
```

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
| main | WARNING | "Could not extract sufficient metadata" | All strategies failed |
| crossref | INFO | "Querying CrossRef for DOI: {doi}" | CrossRef API call |
| crossref | WARNING | "No metadata found for DOI" | DOI not in CrossRef |
| doi_extractor | INFO | "Found DOI in {filename}: {doi}" | DOI found in PDF |
| doi_extractor | WARNING | "No DOI found in {filename}" | No DOI in PDF |
| grobid | INFO | "GROBID service available" | Service is running |
| grobid | WARNING | "GROBID service not available" | Service not running |

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

# Process a directory
citations = extractor.process_directory(Path("./papers"))
print(f"Extracted {len(citations)} citations")

# Export to BibTeX
extractor.export_citations(citations, Path("output.bib"))
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
    "doi": "10.1038/example"
}

exporter = BibTeXExporter()

# Export to file
citations = [metadata]
exporter.export(citations, Path("output.bib"))

# Get as string
bibtex_str = exporter.export_single(metadata)
print(bibtex_str)
```

---

## File Structure Summary

```
src/
├── __init__.py              # Package init, version
├── main.py                 # CLI entry point, CitationExtractor
│
├── api_clients/
│   ├── __init__.py         # Module exports
│   └── crossref.py         # CrossRefClient class
│
├── extractors/
│   ├── __init__.py         # Module exports
│   ├── pdf_metadata.py     # PDFMetadataExtractor class
│   ├── doi_extractor.py     # DOIExtractor class
│   └── grobid_client.py    # GROBIDClient class
│
└── exporters/
    ├── __init__.py         # Module exports
    └── bibtex.py            # BibTeXExporter class
```

**Total Lines of Code:** ~1,100 lines (excluding blank lines and comments)

---

*Documentation generated for PDF Citation Extractor v0.1.0*
