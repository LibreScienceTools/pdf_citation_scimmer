"""Unit tests for PDF metadata extractor"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.extractors.pdf_metadata import PDFMetadataExtractor


@pytest.mark.unit
class TestPDFMetadataExtractor:
    """Test suite for PDF metadata extraction functionality."""

    def test_init(self):
        """Test PDFMetadataExtractor initialization."""
        extractor = PDFMetadataExtractor()
        assert extractor.supported_fields is not None
        assert "title" in extractor.supported_fields
        assert "author" in extractor.supported_fields

    @patch("fitz.open")
    def test_extract_complete_metadata(self, mock_fitz_open, sample_pdf_metadata):
        """Test extracting complete metadata from PDF."""
        # Mock PDF with full metadata
        mock_doc = MagicMock()
        mock_doc.metadata = {
            "title": "Deep Learning for NLP",
            "author": "John Smith",
            "subject": "Machine Learning",
            "keywords": "deep learning, NLP",
            "creator": "LaTeX",
            "producer": "pdfTeX",
            "creationDate": "D:20230115120000",
            "modDate": "D:20230115120000",
        }
        mock_fitz_open.return_value = mock_doc

        extractor = PDFMetadataExtractor()
        result = extractor.extract(Path("test.pdf"))

        assert result["title"] == "Deep Learning for NLP"
        assert result["author"] == "John Smith"
        assert result["subject"] == "Machine Learning"
        assert result["keywords"] == "deep learning, NLP"
        mock_doc.close.assert_called_once()

    @patch("fitz.open")
    def test_extract_empty_metadata(self, mock_fitz_open):
        """Test extracting from PDF with no metadata."""
        mock_doc = MagicMock()
        mock_doc.metadata = {}
        mock_fitz_open.return_value = mock_doc

        extractor = PDFMetadataExtractor()
        result = extractor.extract(Path("test.pdf"))

        assert result["title"] is None
        assert result["author"] is None
        assert result["doi"] is None

    @patch("fitz.open")
    def test_extract_partial_metadata(self, mock_fitz_open):
        """Test extracting partial metadata."""
        mock_doc = MagicMock()
        mock_doc.metadata = {
            "title": "Test Paper",
            # Missing author and other fields
        }
        mock_fitz_open.return_value = mock_doc

        extractor = PDFMetadataExtractor()
        result = extractor.extract(Path("test.pdf"))

        assert result["title"] == "Test Paper"
        assert result["author"] is None

    def test_clean_field_removes_whitespace(self):
        """Test that field cleaning removes whitespace."""
        extractor = PDFMetadataExtractor()

        assert extractor._clean_field("  Test  ") == "Test"
        assert extractor._clean_field("\nTest\n") == "Test"
        assert extractor._clean_field("\tTest\t") == "Test"

    def test_clean_field_handles_empty_values(self):
        """Test that field cleaning handles empty/invalid values."""
        extractor = PDFMetadataExtractor()

        assert extractor._clean_field(None) is None
        assert extractor._clean_field("") is None
        assert extractor._clean_field("   ") is None
        assert extractor._clean_field("unknown") is None
        assert extractor._clean_field("Unknown") is None
        assert extractor._clean_field("UNKNOWN") is None

    def test_clean_field_handles_none_null(self):
        """Test that field cleaning handles 'none' and 'null' strings."""
        extractor = PDFMetadataExtractor()

        assert extractor._clean_field("none") is None
        assert extractor._clean_field("None") is None
        assert extractor._clean_field("null") is None
        assert extractor._clean_field("Null") is None

    @patch("fitz.open")
    def test_extract_doi_from_subject(self, mock_fitz_open):
        """Test extracting DOI from subject field."""
        mock_doc = MagicMock()
        mock_doc.metadata = {
            "title": "Test",
            "subject": "DOI: 10.1234/test.2023.001",
        }
        mock_fitz_open.return_value = mock_doc

        extractor = PDFMetadataExtractor()
        result = extractor.extract(Path("test.pdf"))

        assert result["doi"] == "10.1234/test.2023.001"

    @patch("fitz.open")
    def test_extract_handles_pdf_error(self, mock_fitz_open):
        """Test that extractor handles PDF errors gracefully."""
        mock_fitz_open.side_effect = Exception("Corrupted PDF")

        extractor = PDFMetadataExtractor()
        result = extractor.extract(Path("corrupt.pdf"))

        # Should return empty metadata on error
        assert result["title"] is None
        assert result["author"] is None

    def test_empty_metadata_structure(self):
        """Test empty metadata dictionary structure."""
        extractor = PDFMetadataExtractor()
        empty = extractor._empty_metadata()

        required_keys = [
            "title",
            "author",
            "subject",
            "keywords",
            "creator",
            "producer",
            "creation_date",
            "mod_date",
            "doi",
        ]

        for key in required_keys:
            assert key in empty
            assert empty[key] is None

    def test_has_useful_metadata_with_title(self):
        """Test checking for useful metadata with title."""
        extractor = PDFMetadataExtractor()
        metadata = {"title": "Test Paper", "author": None}

        assert extractor.has_useful_metadata(metadata) is True

    def test_has_useful_metadata_with_author(self):
        """Test checking for useful metadata with author."""
        extractor = PDFMetadataExtractor()
        metadata = {"title": None, "author": "John Doe"}

        assert extractor.has_useful_metadata(metadata) is True

    def test_has_useful_metadata_with_both(self):
        """Test checking for useful metadata with both title and author."""
        extractor = PDFMetadataExtractor()
        metadata = {"title": "Test", "author": "John Doe"}

        assert extractor.has_useful_metadata(metadata) is True

    def test_has_useful_metadata_empty(self):
        """Test checking for useful metadata with neither title nor author."""
        extractor = PDFMetadataExtractor()
        metadata = {"title": None, "author": None}

        assert extractor.has_useful_metadata(metadata) is False

    @patch("fitz.open")
    def test_extract_unicode_metadata(self, mock_fitz_open):
        """Test extracting metadata with Unicode characters."""
        mock_doc = MagicMock()
        mock_doc.metadata = {
            "title": "Über Machine Learning",
            "author": "François Müller",
        }
        mock_fitz_open.return_value = mock_doc

        extractor = PDFMetadataExtractor()
        result = extractor.extract(Path("test.pdf"))

        assert result["title"] == "Über Machine Learning"
        assert result["author"] == "François Müller"
