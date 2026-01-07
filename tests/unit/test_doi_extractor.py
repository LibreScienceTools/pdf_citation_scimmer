"""Unit tests for DOI extractor"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.extractors.doi_extractor import DOIExtractor


@pytest.mark.unit
class TestDOIExtractor:
    """Test suite for DOI extraction functionality."""

    def test_init_default_scan_pages(self):
        """Test DOIExtractor initialization with default scan pages."""
        extractor = DOIExtractor()
        assert extractor.scan_pages == 3

    def test_init_custom_scan_pages(self):
        """Test DOIExtractor initialization with custom scan pages."""
        extractor = DOIExtractor(scan_pages=5)
        assert extractor.scan_pages == 5

    def test_clean_doi_removes_url_prefix(self):
        """Test cleaning DOI removes URL prefixes."""
        extractor = DOIExtractor()

        test_cases = [
            ("https://doi.org/10.1234/test", "10.1234/test"),
            ("http://doi.org/10.1234/test", "10.1234/test"),
            ("https://dx.doi.org/10.1234/test", "10.1234/test"),
            ("http://dx.doi.org/10.1234/test", "10.1234/test"),
        ]

        for input_doi, expected in test_cases:
            result = extractor._clean_doi(input_doi)
            assert result == expected

    def test_clean_doi_removes_prefix(self):
        """Test cleaning DOI removes 'doi:' prefix."""
        extractor = DOIExtractor()

        test_cases = [
            ("doi: 10.1234/test", "10.1234/test"),
            ("DOI: 10.1234/test", "10.1234/test"),
            ("doi:10.1234/test", "10.1234/test"),
        ]

        for input_doi, expected in test_cases:
            result = extractor._clean_doi(input_doi)
            assert result == expected

    def test_clean_doi_removes_trailing_punctuation(self):
        """Test cleaning DOI removes trailing punctuation."""
        extractor = DOIExtractor()

        test_cases = [
            ("10.1234/test.", "10.1234/test"),
            ("10.1234/test,", "10.1234/test"),
            ("10.1234/test;", "10.1234/test"),
            ("10.1234/test:", "10.1234/test"),
        ]

        for input_doi, expected in test_cases:
            result = extractor._clean_doi(input_doi)
            assert result == expected

    def test_find_doi_in_text_standard_pattern(self, sample_doi_text):
        """Test finding DOI with standard pattern in text."""
        extractor = DOIExtractor()
        doi = extractor._find_doi_in_text(sample_doi_text)
        assert doi == "10.1234/test.2023.001"

    def test_find_doi_in_text_with_variants(self, sample_doi_variants):
        """Test finding DOI with different format variants."""
        extractor = DOIExtractor()

        for variant in sample_doi_variants:
            text = f"This is a paper. {variant} More text here."
            doi = extractor._find_doi_in_text(text)
            assert doi == "10.1234/test.2023.001"

    def test_find_doi_in_text_no_match(self):
        """Test finding DOI returns None when no DOI present."""
        extractor = DOIExtractor()
        text = "This is a paper without a DOI."
        doi = extractor._find_doi_in_text(text)
        assert doi is None

    @patch("fitz.open")
    def test_extract_doi_from_pdf(self, mock_fitz_open):
        """Test extracting DOI from PDF file."""
        # Mock PDF document
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "DOI: 10.1234/test.2023.001"
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_doc

        extractor = DOIExtractor()
        pdf_path = Path("test.pdf")
        doi = extractor.extract(pdf_path)

        assert doi == "10.1234/test.2023.001"
        mock_doc.close.assert_called_once()

    @patch("fitz.open")
    def test_extract_no_doi_found(self, mock_fitz_open):
        """Test extracting DOI returns None when not found."""
        # Mock PDF without DOI
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "This is a paper without a DOI."
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_doc

        extractor = DOIExtractor()
        pdf_path = Path("test.pdf")
        doi = extractor.extract(pdf_path)

        assert doi is None

    @patch("fitz.open")
    def test_extract_scans_multiple_pages(self, mock_fitz_open):
        """Test that extractor scans configured number of pages."""
        # Mock multi-page PDF with DOI on page 2
        mock_doc = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "First page without DOI"
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "DOI: 10.1234/found.on.page2"

        mock_doc.__getitem__.side_effect = lambda idx: [mock_page1, mock_page2][idx]
        mock_doc.__len__.return_value = 5
        mock_fitz_open.return_value = mock_doc

        extractor = DOIExtractor(scan_pages=2)
        pdf_path = Path("test.pdf")
        doi = extractor.extract(pdf_path)

        assert doi == "10.1234/found.on.page2"
        assert mock_doc.__getitem__.call_count == 2  # Should scan 2 pages

    @patch("fitz.open")
    def test_extract_handles_pdf_error(self, mock_fitz_open):
        """Test that extractor handles PDF errors gracefully."""
        mock_fitz_open.side_effect = Exception("Corrupted PDF")

        extractor = DOIExtractor()
        pdf_path = Path("corrupt.pdf")
        doi = extractor.extract(pdf_path)

        assert doi is None

    @patch("fitz.open")
    def test_extract_multiple_dois(self, mock_fitz_open):
        """Test extracting multiple DOIs from PDF."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = """
        Paper DOI: 10.1234/test.2023.001
        References:
        [1] 10.5678/ref1
        [2] 10.9012/ref2
        """
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_doc

        extractor = DOIExtractor()
        pdf_path = Path("test.pdf")
        dois = extractor.extract_multiple(pdf_path)

        assert len(dois) == 3
        assert "10.1234/test.2023.001" in dois
        assert "10.5678/ref1" in dois
        assert "10.9012/ref2" in dois

    def test_doi_pattern_coverage(self):
        """Test that DOI patterns cover common formats."""
        extractor = DOIExtractor()

        test_dois = [
            "10.1000/xyz123",
            "10.1234/test-2023",
            "10.1234/test_2023",
            "10.1234/test.2023.001",
            "10.1234/(test)2023",
            "10.1234/test/sub/path",
        ]

        for doi in test_dois:
            text = f"Paper DOI: {doi}"
            result = extractor._find_doi_in_text(text)
            assert result is not None, f"Failed to extract DOI: {doi}"
