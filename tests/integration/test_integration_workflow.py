"""Integration tests for complete extraction workflow"""

import pytest
import requests
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.main import CitationExtractor


@pytest.mark.integration
class TestIntegrationWorkflow:
    """Integration tests for end-to-end extraction workflows."""

    @patch("fitz.open")
    @patch("habanero.Crossref.works")
    def test_doi_to_crossref_workflow(
        self, mock_crossref_works, mock_fitz_open, sample_crossref_response, tmp_path
    ):
        """Test complete workflow: PDF → DOI extraction → CrossRef lookup."""
        # Mock PDF with DOI in first page
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "DOI: 10.1234/test.2023.001"
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_doc.metadata = {}
        mock_fitz_open.return_value = mock_doc

        # Mock CrossRef response
        mock_crossref_works.return_value = sample_crossref_response

        # Process PDF
        extractor = CitationExtractor()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()  # Create empty file

        metadata = extractor.process_pdf(pdf_path)

        assert metadata is not None
        assert metadata["doi"] == "10.1234/test.2023.001"
        assert metadata["title"] == "Deep Learning for Natural Language Processing"
        assert metadata["source"] == "crossref"

    @patch("fitz.open")
    def test_embedded_metadata_workflow(self, mock_fitz_open, tmp_path):
        """Test workflow using only embedded metadata (no DOI, no API call)."""
        # Mock PDF with rich embedded metadata but no DOI
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Paper without DOI"
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_doc.metadata = {
            "title": "Embedded Title",
            "author": "Embedded Author",
            "subject": "Computer Science",
        }
        mock_fitz_open.return_value = mock_doc

        # Process PDF
        extractor = CitationExtractor()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        metadata = extractor.process_pdf(pdf_path)

        assert metadata is not None
        assert metadata["title"] == "Embedded Title"
        assert metadata["author"] == "Embedded Author"
        assert metadata["source"] == "embedded"

    @patch("fitz.open")
    @patch("habanero.Crossref.works")
    def test_fallback_strategy(self, mock_crossref_works, mock_fitz_open, tmp_path):
        """Test fallback to embedded metadata when CrossRef fails."""
        # Mock PDF with DOI
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "DOI: 10.1234/invalid"
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_doc.metadata = {
            "title": "Fallback Title",
            "author": "Fallback Author",
        }
        mock_fitz_open.return_value = mock_doc

        # Mock CrossRef failure
        mock_crossref_works.return_value = None

        # Process PDF
        extractor = CitationExtractor()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        metadata = extractor.process_pdf(pdf_path)

        # Should fall back to embedded metadata
        assert metadata is not None
        assert metadata["title"] == "Fallback Title"
        assert metadata["source"] == "embedded"

    @patch("fitz.open")
    def test_directory_processing(self, mock_fitz_open, tmp_path):
        """Test processing multiple PDFs in a directory."""
        # Create test PDFs
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()

        for i in range(3):
            pdf_path = pdf_dir / f"paper{i}.pdf"
            pdf_path.touch()

        # Mock PDF responses
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "No DOI"
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_doc.metadata = {
            "title": f"Paper Title",
            "author": "Test Author",
        }
        mock_fitz_open.return_value = mock_doc

        # Process directory
        extractor = CitationExtractor()
        citations = extractor.process_directory(pdf_dir)

        assert len(citations) == 3
        for citation in citations:
            assert citation["title"] == "Paper Title"

    @patch("fitz.open")
    def test_export_workflow(self, mock_fitz_open, tmp_path):
        """Test complete workflow including export."""
        # Mock PDF
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Test"
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_doc.metadata = {
            "title": "Export Test",
            "author": "Test Author",
            "year": "2023",
        }
        mock_fitz_open.return_value = mock_doc

        # Create PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        # Process and export
        extractor = CitationExtractor()
        metadata = extractor.process_pdf(pdf_path)
        citations = [metadata] if metadata else []

        output_path = tmp_path / "output.bib"
        success = extractor.export_citations(citations, output_path)

        assert success is True
        assert output_path.exists()

        # Verify BibTeX content
        content = output_path.read_text()
        assert "Export Test" in content
        assert "Test Author" in content

    @patch("fitz.open")
    def test_error_handling_corrupt_pdf(self, mock_fitz_open, tmp_path):
        """Test handling of corrupt PDF files."""
        # Mock PDF that raises error
        mock_fitz_open.side_effect = Exception("Corrupted PDF")

        pdf_path = tmp_path / "corrupt.pdf"
        pdf_path.touch()

        extractor = CitationExtractor()
        metadata = extractor.process_pdf(pdf_path)

        assert metadata is None  # Should handle error gracefully

    @patch("fitz.open")
    def test_empty_directory(self, mock_fitz_open, tmp_path):
        """Test processing empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        extractor = CitationExtractor()
        citations = extractor.process_directory(empty_dir)

        assert citations == []

    @patch("fitz.open")
    @patch("habanero.Crossref.works")
    def test_partial_crossref_data(
        self, mock_crossref_works, mock_fitz_open, tmp_path
    ):
        """Test handling partial data from CrossRef."""
        # Mock PDF with DOI
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "DOI: 10.1234/test"
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_doc.metadata = {}
        mock_fitz_open.return_value = mock_doc

        # Mock minimal CrossRef response
        mock_crossref_works.return_value = {
            "message": {
                "title": ["Minimal Paper"],
                # Missing author, year, etc.
            }
        }

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        extractor = CitationExtractor()
        metadata = extractor.process_pdf(pdf_path)

        assert metadata is not None
        assert metadata["title"] == "Minimal Paper"
        assert metadata["author"] is None  # Missing data should be None

    @patch("fitz.open")
    @patch("requests.post")
    @patch("requests.get")
    def test_grobid_fallback_workflow(
        self, mock_get, mock_post, mock_fitz_open, sample_grobid_xml_response, tmp_path
    ):
        """Test GROBID fallback when DOI not found and no embedded metadata."""
        # Mock PDF without DOI and minimal metadata
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Paper content without DOI"
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_doc.metadata = {}  # No useful embedded metadata
        mock_fitz_open.return_value = mock_doc

        # Mock GROBID service availability
        mock_get.return_value.status_code = 200

        # Mock GROBID response
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = sample_grobid_xml_response

        # Process PDF with GROBID enabled
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        extractor = CitationExtractor()
        metadata = extractor.process_pdf(pdf_path)

        # Should fall back to GROBID
        assert metadata is not None
        assert metadata["title"] == "Deep Learning for Natural Language Processing"
        assert metadata["author"] == "John Smith and Jane Doe"
        assert metadata["source"] == "grobid"
        assert metadata["year"] == "2023"

    @patch("fitz.open")
    @patch("requests.post")
    @patch("requests.get")
    def test_grobid_service_unavailable(self, mock_get, mock_post, mock_fitz_open, tmp_path):
        """Test workflow when GROBID service is unavailable."""
        # Mock PDF without DOI
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Paper without DOI"
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_doc.metadata = {}
        mock_fitz_open.return_value = mock_doc

        # Mock GROBID service not available (use proper exception type)
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        extractor = CitationExtractor()
        metadata = extractor.process_pdf(pdf_path)

        # Should return None when all strategies fail
        assert metadata is None

    @patch("fitz.open")
    @patch("habanero.Crossref.works")
    @patch("requests.post")
    @patch("requests.get")
    def test_complete_workflow_with_grobid(
        self, mock_get, mock_post, mock_crossref_works, mock_fitz_open,
        sample_crossref_response, sample_grobid_xml_response, tmp_path
    ):
        """Test complete workflow: embedded → DOI lookup → GROBID fallback."""
        # Test 1: DOI found, CrossRef succeeds
        mock_doc1 = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "DOI: 10.1234/test.2023.001"
        mock_doc1.__getitem__.return_value = mock_page1
        mock_doc1.__len__.return_value = 1
        mock_doc1.metadata = {}
        mock_fitz_open.return_value = mock_doc1
        mock_crossref_works.return_value = sample_crossref_response

        pdf_path1 = tmp_path / "test1.pdf"
        pdf_path1.touch()

        extractor = CitationExtractor()
        metadata1 = extractor.process_pdf(pdf_path1)

        assert metadata1["source"] == "crossref"

        # Test 2: No DOI, GROBID succeeds
        mock_doc2 = MagicMock()
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "No DOI here"
        mock_doc2.__getitem__.return_value = mock_page2
        mock_doc2.__len__.return_value = 1
        mock_doc2.metadata = {}
        mock_fitz_open.return_value = mock_doc2

        mock_get.return_value.status_code = 200
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = sample_grobid_xml_response

        pdf_path2 = tmp_path / "test2.pdf"
        pdf_path2.touch()

        # Re-initialize to pick up GROBID
        extractor2 = CitationExtractor()
        metadata2 = extractor2.process_pdf(pdf_path2)

        assert metadata2["source"] == "grobid"
