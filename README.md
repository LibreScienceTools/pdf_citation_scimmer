# PDF Citation Extractor

**Efficient reference management for scientists and researchers**

**Version:** 0.2.0 | **Last Updated:** 2026-10-21

## Motivation

This project helps scientists to manage their references more efficiently. For example, I used to download literature as PDFs and saved them centrally in a directory. At another time, I write on a paper and needed to cite several articles previously saved as PDFs. To do this, I used Citavi or JabRef and passed the DOI to automatically add it to my library or I had to type it in manually.

This was a time consuming task because I had to do it for each individual PDF. With this PDF citation scimmer, I provide a solution for this problem. You take your PDFs and place them in a directory (organized by paper, topic, etc.) and let the program run. The program walks through every PDF in this directory and extracts metadata like DOI, author, year, etc. This metadata is stored in a `.bib` file, which can be imported to Citavi, JabRef, or Zotero.

## Key Features

### 1. ✨ NEW: File Tracking System (v0.2.0)
- **Persistent Identification**: Uses UUIDs to track PDF files independently of citation keys
- **Smart Merge**: Recognizes same files even when citation keys change in JabRef
- **Cross-Session Tracking**: Maintains tracking information across different program runs
- **Missing File Cleanup**: Automatically removes entries for deleted files

### 2. Incremental Updates (Merge Mode)
- **Default behavior**: Automatically merges with existing `.bib` files
- Never loses existing entries - only adds new citations
- Prevents duplicate entries based on UUIDs (NEW) and citation keys
- Use `--overwrite` flag if you need to replace the entire file

### 3. Failed Files Logging
- Creates `failed_extractions.log` in the output directory
- Lists all PDFs that failed metadata extraction
- Includes **would-be citation keys** for easy JabRef entry creation
- Provides **group information** for proper organization
- Helps you manually add missing references

### 4. Smart Metadata Extraction
- Multiple fallback strategies (embedded metadata, DOI lookup, GROBID)
- Automatic citation key generation
- **NEW**: JabRef group metadata support with native group structure
- Flexible configuration options
- UUID-based file identification

### 5. Quality Filtering (NEW in v0.2.0)
- **Automatic rejection** of low-quality metadata entries
- Prevents entries with generic titles ("Misc", "Untitled", "Unknown", "Document", "Article", "Paper", "Publication")
- Prevents entries with generic authors ("Unknown", "Anonymous", "None")
- Prevents entries with invalid years ("YYYY", "0000", out of range 1900-2100)
- **PII DOI pattern detection**: Rejects PII numbers masquerading as DOIs (e.g., `S0021-8502(97)10031-3`)
- Failed quality checks are logged in `failed_extractions.log` for manual addition
- Ensures only high-quality, reliable metadata is added to your library

### 6. CLI Interface
- Process directories or single PDFs
- Custom configuration support
- Verbose logging for debugging
- **NEW**: File tracker management commands

## Quick Start

See [docs/QUICK_START.md](docs/QUICK_START.md) for detailed installation and usage instructions.

## Basic Usage

```bash
# Process a directory of PDFs
python -m src.main --dir ./papers --output references.bib

# Process a single PDF
python -m src.main --pdf paper.pdf --output citation.bib

# Show tracked files (NEW in v0.2.0)
python -m src.main --output references.bib --show-tracker

# Clean up missing file entries (NEW in v0.2.0)
python -m src.main --output references.bib --cleanup-tracker
```

## Project Structure

```
pdf_citation_scimmer/
├── docs/                          # Documentation
│   ├── API_REFERENCE.md           # Complete API reference
│   ├── QUICK_START.md             # Quick start guide
│   ├── README.md                  # Documentation index
│   └── SOURCE_CODE_DOCUMENTATION.md  # Detailed source code docs
│
├── src/                           # Source code
│   ├── __init__.py                # Package initialization
│   ├── main.py                    # CLI and orchestrator
│   │
│   ├── api_clients/               # API clients
│   │   ├── __init__.py            # Module exports
│   │   └── crossref.py            # CrossRef API client
│   │
│   ├── extractors/                # Metadata extractors
│   │   ├── __init__.py            # Module exports
│   │   ├── pdf_metadata.py        # PDF embedded metadata
│   │   ├── doi_extractor.py        # DOI extraction from text
│   │   └── grobid_client.py       # GROBID service client
│   │
│   ├── exporters/                 # Export format handlers
│   │   ├── __init__.py            # Module exports
│   │   └── bibtex.py              # BibTeX exporter with JabRef support
│   │
│   └── trackers/                  # File tracking system (NEW v0.2.0)
│       ├── __init__.py            # Module exports
│       └── file_tracker.py        # File tracker with UUID support
│
├── tests/                         # Tests
├── example.py                     # Usage examples
├── setup.py                       # Package configuration
├── requirements.txt               # Production dependencies
└── requirements-dev.txt           # Development dependencies
```

## Supported Output Formats

| Format | Status | Notes |
|--------|--------|-------|
| BibTeX | ✅ Supported | Primary format, includes JabRef group metadata |
| RIS | 🚧 Planned | Coming in future versions |
| JSON | 🚧 Planned | Coming in future versions |

## Supported Metadata Sources

| Source | Status | Requirements |
|--------|--------|--------------|
| PDF Embedded Metadata | ✅ Built-in | PyMuPDF |
| DOI Lookup (CrossRef) | ✅ Built-in | habanero |
| GROBID ML Service | ✅ Optional | Docker + GROBID image |

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Optional: Install GROBID dependencies
pip install -r requirements.txt[grobid]
```

## Configuration

Create a `config.yaml` file:

```yaml
crossref_email: "your.email@example.com"  # For faster CrossRef API access
output_directory: "./output"
extraction:
  doi_scan_pages: 3
  strategy:
    - "embedded_metadata"
    - "doi_lookup"
    - "grobid"  # Enable if using GROBID
grobid_url: "http://localhost:8070"
```

## Documentation

- [Quick Start Guide](docs/QUICK_START.md) - Get started in 5 minutes
- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Source Code Documentation](docs/SOURCE_CODE_DOCUMENTATION.md) - Detailed source code documentation

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF processing
- [habanero](https://github.com/habanero-org/habanero) for CrossRef API access
- [bibtexparser](https://bibtexparser.readthedocs.io/) for BibTeX generation
- [GROBID](https://grobid.readthedocs.io/) for machine learning-based extraction

---

**Maintained with ❤️ for the scientific community**

*For support, questions, or issues, please see [docs/QUICK_START.md](docs/QUICK_START.md)*