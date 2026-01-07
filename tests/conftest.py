"""Pytest configuration and shared fixtures"""

import pytest
import json
from pathlib import Path
from typing import Dict

# Test data directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"
PDFS_DIR = FIXTURES_DIR / "pdfs"
RESPONSES_DIR = FIXTURES_DIR / "responses"


@pytest.fixture
def sample_pdf_metadata() -> Dict:
    """Sample PDF metadata for testing."""
    return {
        "title": "Deep Learning for Natural Language Processing",
        "author": "John Smith and Jane Doe",
        "subject": "Machine Learning",
        "keywords": "deep learning, NLP, transformers",
        "creator": "LaTeX with hyperref",
        "producer": "pdfTeX-1.40.21",
        "creation_date": "D:20230115120000",
        "mod_date": "D:20230115120000",
        "doi": "10.1234/test.2023.001",
    }


@pytest.fixture
def sample_crossref_response() -> Dict:
    """Sample CrossRef API response for testing."""
    return {
        "message": {
            "DOI": "10.1234/test.2023.001",
            "title": ["Deep Learning for Natural Language Processing"],
            "author": [
                {"given": "John", "family": "Smith"},
                {"given": "Jane", "family": "Doe"},
            ],
            "published-print": {"date-parts": [[2023, 3, 15]]},
            "container-title": ["Journal of Machine Learning Research"],
            "volume": "24",
            "issue": "3",
            "page": "123-145",
            "publisher": "JMLR.org",
            "type": "journal-article",
            "ISSN": ["1532-4435"],
            "URL": "https://jmlr.org/papers/v24/23-001.html",
        }
    }


@pytest.fixture
def sample_bibtex_entry() -> str:
    """Sample BibTeX entry for validation testing."""
    return """@article{Smith_2023_Deep,
  author = {John Smith and Jane Doe},
  title = {Deep Learning for Natural Language Processing},
  year = {2023},
  journal = {Journal of Machine Learning Research},
  volume = {24},
  number = {3},
  pages = {123-145},
  doi = {10.1234/test.2023.001},
  url = {https://jmlr.org/papers/v24/23-001.html}
}
"""


@pytest.fixture
def sample_doi_text() -> str:
    """Sample text containing DOI for extraction testing."""
    return """
    Research Paper Title

    John Smith, Jane Doe

    DOI: 10.1234/test.2023.001

    Abstract: This is a sample abstract...
    """


@pytest.fixture
def sample_doi_variants() -> list:
    """Different DOI format variants for testing."""
    return [
        "10.1234/test.2023.001",
        "doi: 10.1234/test.2023.001",
        "DOI: 10.1234/test.2023.001",
        "https://doi.org/10.1234/test.2023.001",
        "http://dx.doi.org/10.1234/test.2023.001",
    ]


@pytest.fixture
def sample_grobid_xml_response() -> str:
    """Sample GROBID TEI XML response for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc>
            <titleStmt>
                <title>Deep Learning for Natural Language Processing</title>
            </titleStmt>
            <publicationStmt>
                <date when="2023-03-15"/>
            </publicationStmt>
            <sourceDesc>
                <biblStruct>
                    <analytic>
                        <author>
                            <persName>
                                <forename>John</forename>
                                <surname>Smith</surname>
                            </persName>
                        </author>
                        <author>
                            <persName>
                                <forename>Jane</forename>
                                <surname>Doe</surname>
                            </persName>
                        </author>
                        <idno type="DOI">10.1234/test.2023.001</idno>
                    </analytic>
                    <monogr>
                        <title>Journal of Machine Learning Research</title>
                    </monogr>
                </biblStruct>
            </sourceDesc>
        </fileDesc>
        <profileDesc>
            <abstract>
                <p>This paper presents a comprehensive study of deep learning techniques for natural language processing tasks.</p>
            </abstract>
        </profileDesc>
    </teiHeader>
</TEI>"""


@pytest.fixture
def sample_grobid_metadata() -> Dict:
    """Sample parsed GROBID metadata for testing."""
    return {
        "title": "Deep Learning for Natural Language Processing",
        "author": "John Smith and Jane Doe",
        "year": "2023",
        "journal": "Journal of Machine Learning Research",
        "doi": "10.1234/test.2023.001",
        "abstract": "This paper presents a comprehensive study of deep learning techniques for natural language processing tasks.",
        "source": "grobid",
    }


@pytest.fixture
def temp_pdf_dir(tmp_path):
    """Create a temporary directory for PDF testing."""
    pdf_dir = tmp_path / "test_pdfs"
    pdf_dir.mkdir()
    return pdf_dir


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for output files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_crossref_success_response():
    """Load mock CrossRef success response from file."""
    response_file = RESPONSES_DIR / "crossref_success.json"
    if response_file.exists():
        with open(response_file) as f:
            return json.load(f)
    return None


@pytest.fixture
def mock_crossref_error_response():
    """Load mock CrossRef error response from file."""
    response_file = RESPONSES_DIR / "crossref_error.json"
    if response_file.exists():
        with open(response_file) as f:
            return json.load(f)
    return {"status": "error", "message-type": "resource-not-found"}


# Markers for test categorization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "network: Tests requiring network")
    config.addinivalue_line("markers", "requires_pdf: Tests requiring PDF files")
