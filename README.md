
# PDF Citation Extractor

**Efficient reference management for scientists and researchers**

## Motivation
This project helps scientists to manage their references more efficiently. For example, I used to download literature as PDFs and saved them centrally in a directory. At another time, I write on a paper and needed to cite several articles previously saved as PDFs. To do this, I used Citavi or JabRef and passed the DOI to automatically add it to my library or I had to type it in manually.

This was a time consuming task because I had to do it for each individual PDF. With this PDF citation scimmer, I provide a solution for this problem. You take your PDFs and place them in a directory (organized by paper, topic, etc.) and let the program run. The program walks through every PDF in this directory and extracts metadata like DOI, author, year, etc. This metadata is stored in a `.bib` file, which can be imported to Citavi, JabRef, or Zotero.

## Key Features

### 1. Incremental Updates (Merge Mode)
- **Default behavior**: Automatically merges with existing `.bib` files
- Never loses existing entries - only adds new citations
- Prevents duplicate entries based on citation keys
- Use `--overwrite` flag if you need to replace the entire file

### 2. Failed Files Logging
- Creates `failed_extractions.log` in the output directory
- Lists all PDFs that failed metadata extraction
- Includes **would-be citation keys** for easy JabRef entry creation
- Provides **group information** for proper organization
- Helps you manually add missing references

### 3. Smart Metadata Extraction
- Multiple fallback strategies (embedded metadata, DOI lookup, GROBID)
- Automatic citation key generation
- JabRef group metadata support
- Flexible configuration options

## Quick Start

See [docs/QUICK_START.md](docs/QUICK_START.md) for detailed installation and usage instructions.

## Documentation

- [Quick Start Guide](docs/QUICK_START.md) - Get started in 5 minutes
- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Configuration Guide](docs/README.md) - All documentation index 
