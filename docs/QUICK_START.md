# PDF Citation Extractor - Quick Start Guide

**Version:** 0.2.0  
**Last Updated:** 2026-10-21

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for development)

### Install from Source

```bash
# Clone the repository (if not already cloned)
git clone https://github.com/yourusername/pdf_citation_skimmer.git
cd pdf_citation_skimmer

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode (optional)
pip install -e .
```

---

## Basic Usage

### Process a Directory of PDFs

```bash
# Process all PDFs in a directory and create references.bib
python -m src.main --dir ./papers --output references.bib

# Process with verbose logging
python -m src.main --dir ./papers --output references.bib --verbose
```

### Process a Single PDF

```bash
# Process a single PDF file
python -m src.main --pdf paper.pdf --output citation.bib
```

### Custom Configuration

```bash
# Use a custom config file
python -m src.main --dir ./papers --config my_config.yaml --output refs.bib
```

---

## NEW in v0.2.0: File Tracking Features

### Automatic File Tracking

The PDF Citation Extractor now automatically tracks your PDF files using unique identifiers (UUIDs). This provides several benefits:

1. **Persistent Identification**: Files are identified by UUID, not just citation keys
2. **Smart Merge**: Prevents duplicate entries even when citation keys change
3. **Missing File Cleanup**: Automatically removes entries for deleted files
4. **Cross-Session Tracking**: Maintains tracking information across different runs

### View Tracked Files

```bash
# Show all tracked files for a specific bib file
python -m src.main --output references.bib --show-tracker

# Output shows: UUID, file path, citation key, timestamps
```

### Clean Up Missing Files

```bash
# Remove entries for files that no longer exist
python -m src.main --output references.bib --cleanup-tracker
```

### Tracker File Location

The tracker stores a `.pdf_tracker.json` file in the same directory as your output `.bib` file. This file contains:
- UUID for each tracked file
- File paths (absolute and relative)
- File hashes (SHA-256)
- Citation keys
- Timestamps
- Additional metadata (group, source, etc.)

**Example tracker file location:**
```
output/
├── references.bib
└── .pdf_tracker.json    # <- Tracker file
```

---

## Manual Entry Preservation

### The Problem This Solves

You want to use the PDF Citation Extractor for most of your PDFs, but some files might:
- Have poor or missing metadata
- Be from sources without DOIs
- Require manual data entry

**Solution**: The scimmer now **preserves manually added JabRef entries** while managing automatically extracted ones.

### How It Works

The scimmer distinguishes between two types of entries:

| Entry Type | Has `pdf_uuid` Field? | Managed By | Preservation |
|------------|----------------------|------------|--------------|
| **Auto** (from PDFs) | ✅ Yes | Scimmer | Updated on re-processing |
| **Manual** (from JabRef) | ❌ No | You | **ALWAYS preserved** |

**This means you can safely mix automatic and manual workflows!**

### Complete Workflow Example

#### Step 1: Process Your PDFs
```bash
python -m src.main --dir ./papers --output references.bib
```

**Result:**
- ✅ Successfully processed PDFs → Added to `references.bib` with `pdf_uuid` fields
- ❌ Failed PDFs → Logged in `output/failed_extractions.log`

#### Step 2: Check for Failed Files
```bash
cat output/failed_extractions.log
```

You'll see clear instructions like:
```
File #1: difficult_paper.pdf
  Group: General
  Suggested BibTeX Key: difficultpaper
  Reason: No metadata extracted from any source

  ACTION REQUIRED: Add this file manually to JabRef!
  - BibTeX key: difficultpaper
  - Group: General
```

#### Step 3: Add Manual Entries in JabRef
1. Open `references.bib` in JabRef
2. For each failed file, create a new entry:
   - Use the **Suggested BibTeX Key** as the citation key
   - Add to the specified **Group**
   - Fill in metadata manually (title, author, year, etc.)
3. Save the file

**Note**: These manual entries will NOT have a `pdf_uuid` field - that's how the scimmer recognizes them!

#### Step 4: Add More PDFs Later
```bash
python -m src.main --dir ./new_papers --output references.bib
```

**Result:**
- ✅ New PDFs → Added to `references.bib` with `pdf_uuid` fields
- ✅ Existing auto entries → Updated if needed
- ✅ **Manual entries → PRESERVED EXACTLY AS YOU ADDED THEM**

### What You'll See in the CLI

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
   See 'output/failed_extractions.log' for detailed instructions.
   Manually added entries will be preserved in future runs.
```

### Key Benefits

1. **No data loss**: Manual entries are never accidentally removed
2. **Predictable**: Clear separation between auto and manual entries
3. **Transparent**: You know exactly what's happening
4. **Flexible**: Use automatic extraction when it works, manual entry when it doesn't
5. **Safe**: Default behavior preserves your manual work

### What Happens If...

| Scenario | Result |
|----------|--------|
| I add a manual entry with the same key as an auto entry | Manual entry is preserved, auto entry gets a unique key |
| I run with `--overwrite` | Manual entries are removed (you explicitly requested a clean slate) |
| I process the same PDF twice | Recognized by UUID, metadata updated but citation key preserved |
| I delete a manual entry in JabRef | Entry is removed (as expected) |
| I add a manual entry for a file that later gets processed | Manual entry is preserved (you might want to remove it manually) |

### Best Practices

1. **Always check the failed files log** after running the scimmer
2. **Use the suggested BibTeX keys** for consistency
3. **Add manual entries to the correct groups** for organization
4. **Run without `--overwrite`** to preserve your manual work
5. **Use `--overwrite` only when you want to start fresh**

---

## Advanced Usage

### Overwrite Existing File

By default, the tool merges new citations with existing ones. To overwrite:

```bash
python -m src.main --dir ./papers --output references.bib --overwrite
```

### Organize by Groups

The tool automatically organizes citations by subdirectory:

```
papers/
├── General/
│   ├── paper1.pdf
│   └── paper2.pdf
├── MachineLearning/
│   ├── ml_paper1.pdf
│   └── ml_paper2.pdf
└── Neuroscience/
    └── neuro_paper.pdf
```

When exported, citations will be grouped in the `.bib` file with comments:
```bibtex
% ===== Group: General =====

@article{...}

% ===== Group: MachineLearning =====

@article{...}

% ===== Group: Neuroscience =====

@article{...}
```

### Use GROBID for Advanced Extraction

GROBID is a machine learning service that can extract metadata from PDFs without proper embedded metadata:

```bash
# 1. Install Docker: https://docs.docker.com/get-docker/

# 2. Run GROBID service
docker pull lfoppiano/grobid:0.8.0
docker run -t --rm -p 8070:8070 lfoppiano/grobid:0.8.0

# 3. Enable GROBID in config.yaml
extraction:
  strategy:
    - "embedded_metadata"
    - "doi_lookup"
    - "grobid"  # Add this line

# 4. Process PDFs with GROBID
python -m src.main --dir ./papers --output references.bib
```

---

## Configuration

### Default Configuration

The tool uses sensible defaults. Create a `config.yaml` file for customization:

```yaml
# Email for CrossRef API (polite pool - faster response)
# Leave empty for public pool
crossref_email: ""

# Output settings
default_output_format: "bibtex"
output_directory: "./output"

# Extraction settings
extraction:
  # Number of pages to scan for DOI
  doi_scan_pages: 3

  # Fallback strategy order
  strategy:
    - "embedded_metadata"
    - "doi_lookup"
    - "grobid"  # Requires GROBID Docker service

# GROBID service URL
grobid_url: "http://localhost:8070"
```

### Strategy Order

The tool tries extraction strategies in order. First successful strategy is used:

1. **embedded_metadata**: Fastest, uses PDF document properties
2. **doi_lookup**: Scans PDF for DOI and queries CrossRef
3. **grobid**: Machine learning service (requires Docker)

---

## Output Files

### Main Output: .bib File

The primary output is a BibTeX file (`.bib`) that can be imported into:
- JabRef
- Zotero
- Citavi
- LaTeX editors
- Any reference manager that supports BibTeX

**Example output:**
```bibtex
@Comment{jabref-meta: databaseType:bibtex;}

@Comment{jabref-meta: grouping:
0 AllEntriesGroup:;
1 StaticGroup:General\;0\;1\;0x8a8a8aff\;\;\;;
1 StaticGroup:MachineLearning\;0\;1\;0x8a8a8aff\;\;\;;
}

% ===== Group: General =====

@article{Doe2023,
  author = {John Doe and Jane Smith},
  title = {Deep Learning Survey},
  year = {2023},
  journal = {Nature AI},
  volume = {1},
  pages = {1-10},
  doi = {10.1038/example},
  pdf_uuid = {abc123def456...}
}
```

### Failed Files Log

When extraction fails for some PDFs, a `failed_extractions.log` file is created in the output directory:

```
# PDF Citation Extraction - Failed Files
# Generated: 2026-10-21 14:30:45
# Output file: references.bib
#
# How to use this file with JabRef:
#   1. Open your .bib file in JabRef
#   2. For each failed file below, manually create an entry
#   3. Use the 'Would-be Citation Key' as the entry's BibTeX key
#   4. Add the entry to the specified 'Group'
#
# Total failed: 2

## Failed File #1
- **File**: problematic_paper.pdf
- **Group**: General
- **Would-be Citation Key**: problematicpaper
- **Reason**: No metadata extracted from any source (no DOI, no embedded metadata, GROBID unavailable)
- **Action**: Create entry manually in JabRef with key 'problematicpaper'

## Failed File #2
- **File**: corrupted.pdf
- **Group**: MachineLearning
- **Would-be Citation Key**: corrupted
- **Reason**: PDF file is corrupted or encrypted
- **Action**: Create entry manually in JabRef with key 'corrupted'
```

---

## Programmatic Usage

### Basic Example

```python
from pathlib import Path
from src.main import CitationExtractor

# Initialize extractor
extractor = CitationExtractor()

# Process a single PDF
metadata = extractor.process_pdf(Path("paper.pdf"))
print(metadata)

# Process a directory with file tracking
citations = extractor.process_directory(
    Path("./papers"), 
    output_path=Path("references.bib")
)

# Export to BibTeX
extractor.export_citations(citations, Path("references.bib"))
```

### Handle Failed Extractions

```python
from pathlib import Path
from src.main import CitationExtractor

extractor = CitationExtractor()

# Process directory
citations = extractor.process_directory(Path("./papers"))

# Check for failures
if extractor._last_failed_files:
    print(f"Failed to extract {len(extractor._last_failed_files)} files")
    for failure in extractor._last_failed_files:
        print(f"  {failure['relative_path']}: {failure['error']}")
        print(f"    Suggested key: {failure['would_be_key']}")
```

### Use File Tracker Directly

```python
from pathlib import Path
from src.trackers import FileTracker

# Create tracker
tracker = FileTracker(output_dir=Path("./output"))

# Register a file
uuid, is_new = tracker.register_file(
    Path("paper.pdf"),
    citation_key="Author2023Title",
    project_root=Path("."),
    metadata={"group": "General", "source": "embedded"}
)

# List all tracked files
all_entries = tracker.list_all_entries()
for entry in all_entries:
    print(f"UUID: {entry.uuid}")
    print(f"  File: {entry.file_path}")
    print(f"  Key: {entry.citation_key}")
    print(f"  Group: {entry.metadata.get('group')}")

# Clean up missing files
removed = tracker.cleanup_missing_files()
print(f"Removed {removed} missing entries")
```

---

## Troubleshooting

### No Metadata Extracted

If the tool can't extract metadata from your PDFs:

1. **Check PDF quality**: Some PDFs have minimal or no metadata
2. **Enable DOI scanning**: Make sure `doi_scan_pages` is set high enough
3. **Try GROBID**: Enable GROBID for advanced extraction
4. **Check file permissions**: Ensure the tool can read your PDF files
5. **Use verbose mode**: Run with `--verbose` to see detailed processing information

### CrossRef API Issues

If CrossRef API is slow or fails:
- **Provide an email**: Use `--config` with `crossref_email` set to your email for polite pool access
- **Check network connection**: Ensure you have internet access
- **Retry later**: CrossRef may have rate limits

### GROBID Not Working

If GROBID extraction fails:
1. **Verify Docker is running**: `docker --version`
2. **Check GROBID container**: `docker ps` (should show grobid container)
3. **Test GROBID service**: `curl http://localhost:8070/api/isalive`
4. **Check port**: Ensure port 8070 is available

### Permission Issues

If you get permission errors:
- **On Linux/Mac**: Use `chmod` to make PDFs readable
- **On Windows**: Run from elevated command prompt if needed
- **Check directory permissions**: Ensure the tool can create output files

---

## Best Practices

### Organizing Your PDFs

1. **Use meaningful directory structure**: Organize by topic, project, or author
2. **Use consistent naming**: Include author, year, and title in filenames when possible
3. **Avoid special characters**: Use underscores or hyphens instead of spaces and special characters

### Using with JabRef

1. **Import the .bib file**: File → Import → BibTeX
2. **Groups are preserved**: The tool generates JabRef group metadata
3. **Manual entries**: Use the failed files log to create manual entries for problematic PDFs
4. **Citation keys**: The tool generates citation keys automatically

### Regular Maintenance

1. **Clean up tracker**: Periodically run `--cleanup-tracker` to remove entries for deleted files
2. **Check failed files log**: Review and manually add problematic PDFs
3. **Update regularly**: Keep the tool updated for bug fixes and new features

---

## Migration from v0.1.0 to v0.2.0

### What's New

1. **File Tracker**: New `.pdf_tracker.json` files will appear in your output directories
2. **UUID field**: BibTeX entries now include `pdf_uuid` field for tracking
3. **New CLI options**: `--show-tracker` and `--cleanup-tracker`
4. **Improved merge**: Better handling of existing entries and duplicates

### What's Changed

1. **Fallback citation keys**: Format changed from `Filename_Year` to just `Filename`
2. **Group metadata**: JabRef groups are now generated as @Comment entries
3. **Merge behavior**: UUID-based duplicate detection instead of just citation keys

### Backward Compatibility

- All existing functionality is preserved
- New tracker files are created automatically
- Old `.bib` files can still be read and updated
- No changes required to existing workflows

---

## Additional Resources

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Source Code Documentation](SOURCE_CODE_DOCUMENTATION.md) - Detailed source code documentation
- [Project README](../README.md) - Main project documentation

---

## Support

For issues, questions, or suggestions:
- Check the [GitHub Issues](https://github.com/yourusername/pdf_citation_skimmer/issues)
- Review this documentation
- Enable verbose logging (`--verbose`) for detailed information

---

*Happy citing! 📚*