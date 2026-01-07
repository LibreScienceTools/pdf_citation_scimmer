"""Setup script for PDF Citation Extractor"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="pdf-citation-extractor",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Extract citation metadata from PDF files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pdf_citation_skimmer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyMuPDF>=1.23.0",
        "pypdf>=3.17.0",
        "requests>=2.31.0",
        "habanero>=1.2.6",
        "bibtexparser>=1.4.0",
        "click>=8.1.7",
        "tqdm>=4.66.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
        ],
        "grobid": [
            "grobid-client-python>=0.0.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "pdf-citation-extract=src.main:main",
        ],
    },
)
