# PDF Citation Extractor - Documentation Index

**Version:** 0.2.0 | **Last Updated:** 2026-10-21

Welcome to the documentation for PDF Citation Extractor! This index provides an overview of all available documentation and guides you to the information you need.

---

## 📚 Documentation Overview

| Document | Purpose | Best For |
|----------|---------|----------|
| [Quick Start Guide](QUICK_START.md) | Get started quickly with installation and basic usage | New users, quick setup |
| [API Reference](API_REFERENCE.md) | Complete API documentation for all classes and methods | Developers, integration |
| [Source Code Documentation](SOURCE_CODE_DOCUMENTATION.md) | Detailed source code documentation | Developers, contributors |

---

## 🆕 What's New in v0.2.0

### Major New Features

1. **🎯 File Tracking System**
   - Persistent UUID-based identification of PDF files
   - Smart merge that recognizes same files even when citation keys change
   - Automatic cleanup of missing file entries
   - Cross-session tracking across program runs

2. **📊 Enhanced JabRef Support**
   - Native group metadata generation in BibTeX files
   - Automatic group organization based on directory structure
   - Better integration with JabRef's group features

3. **🔧 New CLI Options**
   - `--show-tracker`: View all tracked files
   - `--cleanup-tracker`: Remove entries for deleted files
   - Enhanced merge behavior with UUID support

4. **🛡️ Improved Error Handling**
   - Better handling of malformed BibTeX files
   - Preservation of manually added entries during merge
   - Enhanced failure tracking and logging

### Documentation Updates

- **API Reference**: Added complete documentation for the new `trackers` module
- **Source Code Documentation**: Updated with new features and architecture changes
- **Quick Start Guide**: Added sections for file tracking and new CLI options
- **Examples**: Updated with programmatic usage of file tracker

---

## 📖 Getting Started

If you're new to PDF Citation Extractor, start here:

1. **🚀 Quick Start**: [QUICK_START.md](QUICK_START.md)
   - Installation instructions
   - Basic usage examples
   - Common workflows

2. **⚡ Basic Usage**:
   ```bash
   # Process a directory of PDFs
   python -m src.main --dir ./papers --output references.bib
   
   # Process a single PDF
   python -m src.main --pdf paper.pdf --output citation.bib
   
   # Show tracked files (NEW!)
   python -m src.main --output references.bib --show-tracker
   ```

---

## 🔧 For Developers

If you want to integrate PDF Citation Extractor into your own projects or contribute to the codebase:

1. **📖 API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
   - Complete documentation for all classes and methods
   - Import references
   - Usage examples

2. **🏗️ Architecture**: [SOURCE_CODE_DOCUMENTATION.md](SOURCE_CODE_DOCUMENTATION.md)
   - Detailed module documentation
   - Architecture diagrams
   - Data flow explanations
   - Error handling strategies

3. **💻 Code Examples**:
   ```python
   # Basic usage
   from src.main import CitationExtractor
   extractor = CitationExtractor()
   citations = extractor.process_directory(Path("./papers"))
   
   # Use file tracker directly (NEW!)
   from src.trackers import FileTracker
   tracker = FileTracker(output_dir=Path("./output"))
   uuid, is_new = tracker.register_file(Path("paper.pdf"), "Author2023")
   ```

---

## 🎯 Feature Deep Dives

### File Tracking System (NEW in v0.2.0)

The file tracking system is a major new feature that provides persistent identification of PDF files:

**Benefits:**
- Files are identified by UUID, not just citation keys
- Prevents duplicate entries when re-processing same files
- Handles citation key changes gracefully
- Maintains tracking across different program runs

**Files:**
- Tracker file: `.pdf_tracker.json` (created in output directory)
- Contains: UUIDs, file paths, citation keys, metadata, timestamps

**CLI Commands:**
```bash
# Show all tracked files
python -m src.main --output references.bib --show-tracker

# Clean up missing files
python -m src.main --output references.bib --cleanup-tracker
```

**More Info:** [Quick Start Guide - File Tracking](QUICK_START.md#new-in-v020-file-tracking-features)

---

### Smart Merge Functionality (Enhanced in v0.2.0)

The improved merge functionality now:

- **UUID-based duplicate detection**: Recognizes same files even when citation keys change
- **Preserves manually added entries**: Entries without UUID are kept during merge
- **Handles malformed BibTeX**: Preserves original content when parsing fails
- **Better logging**: Detailed counts of new, updated, and preserved entries

**Example:**
```bash
# First run: creates references.bib with some entries
python -m src.main --dir ./papers --output references.bib

# Second run: adds only new files, preserves existing
python -m src.main --dir ./more_papers --output references.bib
```

---

### JabRef Integration (Enhanced in v0.2.0)

Better JabRef support with:

- **Native group metadata**: Generated as @Comment entries in BibTeX files
- **Group organization**: Automatic groups based on directory structure
- **Persistent identification**: UUID field in BibTeX entries for tracking

**JabRef Groups:**
```bibtex
@Comment{jabref-meta: grouping:
0 AllEntriesGroup:;
1 StaticGroup:MachineLearning\;0\;1\;0x8a8a8aff\;\;\;;
1 StaticGroup:Neuroscience\;0\;1\;0x8a8a8aff\;\;\;;
}
```

---

## 📋 Configuration Guide

### Configuration File (`config.yaml`)

```yaml
# CrossRef API
crossref_email: "your.email@example.com"  # For polite pool access

# Output settings
default_output_format: "bibtex"
output_directory: "./output"

# Extraction settings
extraction:
  doi_scan_pages: 3  # Number of pages to scan for DOI
  strategy:          # Fallback strategy order
    - "embedded_metadata"
    - "doi_lookup"
    - "grobid"      # Optional: requires Docker + GROBID

# GROBID service
grobid_url: "http://localhost:8070"

# Cache settings (future feature)
cache:
  enabled: false
  directory: "./.cache"
```

### Extraction Strategies

The tool tries strategies in order until one succeeds:

1. **embedded_metadata**: Fastest, uses PDF document properties
2. **doi_lookup**: Scans PDF for DOI and queries CrossRef
3. **grobid**: Machine learning service for challenging PDFs

**Recommended:** Enable all three for maximum success rate

---

## 🚀 Advanced Usage

### Process Different Directory Structures

```bash
# Flat directory
python -m src.main --dir ./all_papers --output all.bib

# Nested by topic
python -m src.main --dir ./papers_by_topic --output by_topic.bib

# Nested by year
python -m src.main --dir ./papers_by_year --output by_year.bib
```

### Use GROBID for Advanced Extraction

```bash
# 1. Install Docker: https://docs.docker.com/get-docker/

# 2. Run GROBID service
docker pull lfoppiano/grobid:0.8.0
docker run -t --rm -p 8070:8070 lfoppiano/grobid:0.8.0

# 3. Process PDFs with GROBID enabled
python -m src.main --dir ./papers --output refs.bib
```

### Handle Failed Extractions

```bash
# Process directory - failed files will be logged
python -m src.main --dir ./papers --output refs.bib

# Check the failed_extractions.log file
cat output/failed_extractions.log

# Manually add entries to JabRef using the suggested citation keys
```

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| No metadata extracted | Try enabling GROBID, check PDF quality |
| CrossRef API slow | Add email to config for polite pool access |
| GROBID not working | Verify Docker is running, check port 8070 |
| Permission errors | Ensure PDFs are readable, output directory writable |
| Duplicate entries | Enable file tracking, use UUID-based merge |

**Verbose Mode:**
```bash
python -m src.main --dir ./papers --output refs.bib --verbose
```

---

## 📖 Documentation Structure

```
docs/
├── README.md                      # This file - documentation index
├── QUICK_START.md                 # Quick start guide
│   ├── Installation               # Setup instructions
│   ├── Basic Usage                # Common commands
│   ├── NEW: File Tracking         # v0.2.0 features
│   ├── Advanced Usage             # Special cases
│   ├── Programmatic Usage          # Python API
│   └── Troubleshooting            # Common issues
│
├── API_REFERENCE.md               # Complete API reference
│   ├── Main Classes               # CitationExtractor
│   ├── API Clients                # CrossRefClient
│   ├── Extractors                 # PDF, DOI, GROBID
│   ├── Exporters                  # BibTeXExporter
│   ├── NEW: Trackers              # FileTracker (v0.2.0)
│   ├── Type Definitions           # Data structures
│   └── Exception Handling         # Error patterns
│
└── SOURCE_CODE_DOCUMENTATION.md   # Detailed source docs
    ├── Project Overview           # Architecture
    ├── Module Documentation       # All modules
    ├── Class Reference            # Quick reference
    ├── Configuration              # Config options
    ├── Dependencies               # Required packages
    ├── Data Flow                  # Processing diagrams
    ├── Error Handling             # Strategies
    └── Logging                    # Log configuration
```

---

## 🎓 Learning Path

### For New Users
1. **Start Here**: [Quick Start Guide](QUICK_START.md)
2. **Basic Usage**: Try the examples in the Quick Start
3. **Configuration**: Set up your `config.yaml` file
4. **Process Files**: Run the tool on your PDF collection

### For Developers
1. **Understand Architecture**: [Source Code Documentation](SOURCE_CODE_DOCUMENTATION.md)
2. **Learn API**: [API Reference](API_REFERENCE.md)
3. **Try Examples**: [example.py](../example.py)
4. **Integrate**: Use the library in your own projects

### For Contributors
1. **Read Source Code Docs**: [SOURCE_CODE_DOCUMENTATION.md](SOURCE_CODE_DOCUMENTATION.md)
2. **Study API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
3. **Check Tests**: [tests/](../tests/)
4. **Understand Patterns**: Error handling, logging, configuration

---

## 📞 Need Help?

- **First**: Check this documentation
- **Then**: Run with `--verbose` for detailed logging
- **Next**: Review the `pdf_citation_extractor.log` file
- **Finally**: Check [GitHub Issues](https://github.com/yourusername/pdf_citation_skimmer/issues)

---

## 🔗 Related Documents

- [Main README](../README.md) - Project overview and motivation
- [setup.py](../setup.py) - Package configuration and dependencies
- [requirements.txt](../requirements.txt) - Production dependencies
- [requirements-dev.txt](../requirements-dev.txt) - Development dependencies

---

## 📝 Documentation Conventions

| Format | Meaning |
|--------|---------|
| `code` | File names, commands, code snippets |
| **Bold** | Important terms, new features |
| *Italic* | Emphasis, notes |
| 🆕 | New in current version |
| ✅ | Supported, available |
| 🚧 | Planned, under development |
| ❌ | Not supported, deprecated |

---

**Happy Reading! 📚**

*Last updated: 2026-10-21 for v0.2.0*