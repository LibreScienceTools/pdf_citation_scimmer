# PDF Citation Extractor - Documentation

**Version:** 0.1.0  
**Last Updated:** 2026-10-20

---

## Welcome to the PDF Citation Extractor Documentation

This directory contains comprehensive documentation for the PDF Citation Extractor project.

---

## Documentation Overview

| Document | Description | Audience |
|----------|-------------|----------|
| [QUICK_START.md](./QUICK_START.md) | Get started quickly with installation and basic usage | New users |
| [API_REFERENCE.md](./API_REFERENCE.md) | Complete API reference for all classes and methods | Developers |
| [SOURCE_CODE_DOCUMENTATION.md](./SOURCE_CODE_DOCUMENTATION.md) | Detailed source code documentation | Maintainers, contributors |

---

## Quick Links

- **[Quick Start Guide](./QUICK_START.md)** - Install and use the tool in 5 minutes
- **[API Reference](./API_REFERENCE.md)** - Complete programming API documentation
- **[Source Code Documentation](./SOURCE_CODE_DOCUMENTATION.md)** - In-depth code analysis

---

## Documentation Structure

```
docs/
├── README.md                          # This file
├── QUICK_START.md                     # Quick start guide
├── API_REFERENCE.md                   # API reference
└── SOURCE_CODE_DOCUMENTATION.md      # Source code documentation
```

---

## Getting Started

### 1. Install the Project

```bash
# See QUICK_START.md for detailed instructions
pip install -r requirements.txt
```

### 2. Run Your First Extraction

```bash
# Process a single PDF
python -m src.main --pdf paper.pdf --output citation.bib

# Process a directory
python -m src.main --dir ./papers --output references.bib
```

### 3. Explore the API

```python
from src.main import CitationExtractor
from pathlib import Path

extractor = CitationExtractor()
metadata = extractor.process_pdf(Path("paper.pdf"))
print(metadata)
```

---

## Documentation Standards

This documentation follows these standards:

### Writing Style
- **Clear and concise**: Avoid unnecessary jargon
- **Practical**: Include working code examples
- **Complete**: Document all public methods and attributes
- **Consistent**: Use consistent formatting and terminology

### Code Examples
- All examples are tested and should work
- Examples use real class and method names
- Examples include imports when necessary
- Examples show both usage and expected output

### Structure
- **Table of Contents**: Every document has a TOC
- **Cross-references**: Links between related documents
- **Sections**: Logical grouping of related information

---

## Contributing to Documentation

### Reporting Issues

If you find errors or omissions in the documentation:
1. Check if the issue is already reported
2. Open a new issue with:
   - Document name
   - Section or page number
   - Description of the issue
   - Suggested fix (if any)

### Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b docs/your-change`)
3. Make your changes
4. Test your examples (if adding code examples)
5. Commit your changes (`git commit -m "Update docs: your change"`)
6. Push to the branch (`git push origin docs/your-change`)
7. Open a Pull Request

### Documentation Guidelines

- **Be accurate**: Test all code examples
- **Be complete**: Document all public APIs
- **Be clear**: Use simple, direct language
- **Be consistent**: Follow existing patterns and style
- **Keep it updated**: Update docs when code changes

---

## Additional Resources

- **Project README**: [../README.md](../README.md) - Main project readme
- **Configuration**: [../config.yaml](../config.yaml) - Default configuration
- **Setup**: [../setup.py](../setup.py) - Package setup
- **Requirements**: [../requirements.txt](../requirements.txt) - Dependencies

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-10-20 | Initial documentation release |

---

## License

This documentation is licensed under the same license as the PDF Citation Extractor project. See the main [LICENSE](../LICENSE) file for details.

---

*Documentation for PDF Citation Extractor v0.1.0*
