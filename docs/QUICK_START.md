# PDF Citation Extractor - Quick Start Guide

**Version:** 0.1.0  
**Last Updated:** 2026-10-20

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

### Install with pip

```bash
# From the project directory
pip install .

# Or directly from GitHub (if published)
pip install git+https://github.com/yourusername/pdf_citation_skimmer.git
```

---

## Basic Usage

### Process a Single PDF

```bash
# Using Python module
python -m src.main --pdf paper.pdf --output citation.bib

# Using installed command (if installed)
pdf-citation-extract --pdf paper.pdf --output citation.bib
```

### Process a Directory of PDFs

```bash
# Process all PDFs in a directory
python -m src.main --dir ./papers --output references.bib

# With verbose logging
python -m src.main --dir ./papers --output references.bib --verbose
```

### Use Custom Configuration

```bash
# Create a custom config file
cp config.yaml my_config.yaml
# Edit my_config.yaml with your settings

# Use custom config
python -m src.main --dir ./papers --config my_config.yaml
```

---

## Configuration

### Quick Configuration Reference

| Setting | Config Key | Default | Description |
|---------|------------|---------|-------------|
| CrossRef Email | `crossref_email` | `""` | Email for polite pool access |
| Output Format | `default_output_format` | `"bibtex"` | Export format (bibtex only) |
| Output Directory | `output_directory` | `"./output"` | Where to save output files |
| DOI Scan Pages | `extraction.doi_scan_pages` | `3` | Pages to scan for DOI |
| GROBID URL | `grobid_url` | `"http://localhost:8070"` | GROBID service URL |
| Strategies | `extraction.strategy` | `["embedded_metadata", "doi_lookup"]` | Extraction methods to try |

### Enable GROBID

GROBID is a machine learning service for extracting bibliographic data from PDFs.

```bash
# Install Docker (if not already installed)
# See: https://docs.docker.com/get-docker/

# Pull GROBID image
docker pull lfoppiano/grobid:0.8.0

# Run GROBID service
docker run -t --rm -p 8070:8070 lfoppiano/grobid:0.8.0

# Verify it's running
curl http://localhost:8070/api/isalive
# Should return: true

# Enable GROBID in config.yaml
# In config.yaml, add "grobid" to the strategy list:
extraction:
  strategy:
    - "embedded_metadata"
    - "doi_lookup"
    - "grobid"

# Process PDFs with GROBID
python -m src.main --dir ./papers --output references.bib
```

---

## Examples

### Example 1: Extract metadata from a single paper

```bash
python -m src.main --pdf "Smith_2020_DeepLearning.pdf" --output smith_2020.bib
```

### Example 2: Process an entire research library

```bash
# Process all PDFs in your papers directory
python -m src.main --dir ~/Documents/Papers --output library.bib

# Check the log for details
cat pdf_citation_extractor.log
```

### Example 3: Use CrossRef polite pool (faster access)

Edit `config.yaml`:
```yaml
crossref_email: "your.email@example.com"
```

Then run:
```bash
python -m src.main --dir ./papers --output references.bib --config config.yaml
```

### Example 4: Get verbose output

```bash
python -m src.main --pdf paper.pdf --output citation.bib --verbose
```

---

## Output Format

### BibTeX Output Example

For a paper with the following metadata:
- Title: "Deep Learning for Computer Vision"
- Authors: "John Doe and Jane Smith"
- Year: 2020
- Journal: "IEEE Transactions on Pattern Analysis"
- DOI: 10.1109/TPAMI.2020.123456

The output `citations.bib` will contain:

```bibtex
@article{Doe_2020_Deep,
  author = {John Doe and Jane Smith},
  title = {Deep Learning for Computer Vision},
  year = {2020},
  journal = {IEEE Transactions on Pattern Analysis},
  doi = {10.1109/TPAMI.2020.123456}
}
```

---

## Troubleshooting

### Common Issues

#### Issue: "No PDF files found in directory"
**Solution:** Ensure the directory path is correct and contains `.pdf` files (case-sensitive).

```bash
# Check if PDFs exist
ls ./papers/*.pdf
```

#### Issue: "Could not extract sufficient metadata"
**Solution:** The PDF may not have embedded metadata or a visible DOI. Try:
- Enable GROBID in your strategy list
- Manually add the DOI to the PDF if you know it

#### Issue: GROBID service not available
**Solution:** Start the GROBID Docker container:
```bash
docker run -t --rm -p 8070:8070 lfoppiano/grobid:0.8.0
```

#### Issue: CrossRef API rate limiting
**Solution:** Use the polite pool by setting your email in config.yaml:
```yaml
crossref_email: "your.email@example.com"
```

#### Issue: Missing dependencies
**Solution:** Install all required packages:
```bash
pip install -r requirements.txt
```

### Log File

All operations are logged to `pdf_citation_extractor.log`. Check this file for detailed error messages.

```bash
# View the log file
tail -f pdf_citation_extractor.log

# Filter for errors
grep -i error pdf_citation_extractor.log
```

---

## Tips and Best Practices

### 1. Organize Your PDFs

Create a dedicated directory for your PDF collection:
```bash
mkdir -p ~/Documents/Research/Papers
# Copy or move your PDFs here
```

### 2. Process Incrementally

Process new papers as you download them:
```bash
# Add a new paper and process it
python -m src.main --pdf new_paper.pdf --output new_paper.bib

# Append to your main bibliography
cat new_paper.bib >> library.bib
```

### 3. Backup Your Config

```bash
cp config.yaml config.yaml.backup
```

### 4. Use Different Configs for Different Projects

```bash
# Create project-specific configs
cp config.yaml project1_config.yaml
cp config.yaml project2_config.yaml

# Use the appropriate config for each project
python -m src.main --dir ./project1 --config project1_config.yaml
```

### 5. Check Metadata Quality

Some PDFs have better metadata than others. Check the quality:
```python
from pathlib import Path
from src.extractors import PDFMetadataExtractor

extractor = PDFMetadataExtractor()
metadata = extractor.extract(Path("paper.pdf"))
print(metadata)
```

---

## Command Reference

### Full Command Line Options

```
Usage: python -m src.main [OPTIONS]

  PDF Citation Metadata Extractor

  Extracts citation metadata from PDF files and exports to reference
  management formats.

Options:
  -d, --dir DIRECTORY       Directory containing PDF files to process
  -p, --pdf PATH           Single PDF file to process
  -o, --output PATH       Output file path (default: citations.bib)
  -f, --format TEXT       Output format (default: bibtex)
  -c, --config PATH       Path to config.yaml file
  -v, --verbose            Enable verbose logging
  --help                  Show this message and exit.
```

### Required Arguments

You must specify **either** `--dir` **or** `--pdf`, but not both.

### Examples

```bash
# Process a directory
python -m src.main -d ./papers -o references.bib

# Process a single file
python -m src.main -p paper.pdf -o paper.bib

# Process with custom config
python -m src.main -d ./papers -c my_config.yaml

# Verbose mode
python -m src.main -d ./papers -o refs.bib -v
```

---

## Next Steps

1. **Install the tool** using the instructions above
2. **Test with a sample PDF** to verify it works
3. **Configure** your settings in `config.yaml`
4. **Process your PDF collection**
5. **Import the BibTeX** into your reference manager (Zotero, Mendeley, etc.)

---

*For detailed API documentation, see [SOURCE_CODE_DOCUMENTATION.md](./SOURCE_CODE_DOCUMENTATION.md)*
