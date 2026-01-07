"""End-to-end tests for CLI functionality"""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.main import main


@pytest.mark.e2e
class TestE2ECLI:
    """End-to-end tests for command-line interface."""

    def test_cli_help(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "PDF Citation Metadata Extractor" in result.output
        assert "--dir" in result.output
        assert "--pdf" in result.output

    @patch("fitz.open")
    def test_cli_single_pdf(self, mock_fitz_open):
        """Test CLI with single PDF file."""
        runner = CliRunner()

        # Mock PDF
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Test"
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_doc.metadata = {
            "title": "CLI Test Paper",
            "author": "Test Author",
        }
        mock_fitz_open.return_value = mock_doc

        with runner.isolated_filesystem():
            # Create test PDF
            pdf_path = Path("test.pdf")
            pdf_path.touch()

            # Run CLI
            result = runner.invoke(
                main, ["--pdf", "test.pdf", "--output", "citation.bib"]
            )

            assert result.exit_code == 0
            assert Path("citation.bib").exists()
            assert "Successfully exported" in result.output

    @patch("fitz.open")
    def test_cli_directory(self, mock_fitz_open):
        """Test CLI with directory of PDFs."""
        runner = CliRunner()

        # Mock PDF
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Test"
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_doc.metadata = {
            "title": "Test Paper",
            "author": "Test Author",
        }
        mock_fitz_open.return_value = mock_doc

        with runner.isolated_filesystem():
            # Create test directory with PDFs
            pdf_dir = Path("pdfs")
            pdf_dir.mkdir()
            (pdf_dir / "paper1.pdf").touch()
            (pdf_dir / "paper2.pdf").touch()

            # Run CLI
            result = runner.invoke(
                main, ["--dir", "pdfs", "--output", "references.bib"]
            )

            assert result.exit_code == 0
            assert Path("references.bib").exists()
            assert "2" in result.output  # Should process 2 PDFs

    def test_cli_no_input_error(self):
        """Test CLI error when no input specified."""
        runner = CliRunner()
        result = runner.invoke(main, ["--output", "test.bib"])

        assert result.exit_code == 1
        assert "Must specify either --dir or --pdf" in result.output

    def test_cli_both_inputs_error(self):
        """Test CLI error when both --dir and --pdf specified."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            Path("test.pdf").touch()
            Path("pdfs").mkdir()

            result = runner.invoke(
                main, ["--dir", "pdfs", "--pdf", "test.pdf", "--output", "test.bib"]
            )

            assert result.exit_code == 1
            assert "Cannot specify both" in result.output

    @patch("fitz.open")
    def test_cli_verbose_mode(self, mock_fitz_open):
        """Test CLI with verbose logging."""
        runner = CliRunner()

        # Mock PDF
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Test"
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_doc.metadata = {"title": "Test"}
        mock_fitz_open.return_value = mock_doc

        with runner.isolated_filesystem():
            pdf_path = Path("test.pdf")
            pdf_path.touch()

            result = runner.invoke(
                main, ["--pdf", "test.pdf", "--output", "test.bib", "--verbose"]
            )

            # Verbose mode should succeed (logging is tested elsewhere)
            assert result.exit_code == 0

    @patch("fitz.open")
    def test_cli_custom_output_path(self, mock_fitz_open):
        """Test CLI with custom output path."""
        runner = CliRunner()

        # Mock PDF
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Test"
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_doc.metadata = {"title": "Test", "author": "Author"}
        mock_fitz_open.return_value = mock_doc

        with runner.isolated_filesystem():
            pdf_path = Path("test.pdf")
            pdf_path.touch()

            # Create subdirectory for output
            output_dir = Path("output")
            output_dir.mkdir()

            result = runner.invoke(
                main, ["--pdf", "test.pdf", "--output", "output/custom.bib"]
            )

            assert result.exit_code == 0
            assert Path("output/custom.bib").exists()

    @patch("fitz.open")
    def test_cli_no_citations_extracted(self, mock_fitz_open):
        """Test CLI when no citations can be extracted."""
        runner = CliRunner()

        # Mock PDF with no useful metadata
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "No DOI"
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_doc.metadata = {}  # No metadata
        mock_fitz_open.return_value = mock_doc

        with runner.isolated_filesystem():
            pdf_path = Path("empty.pdf")
            pdf_path.touch()

            result = runner.invoke(
                main, ["--pdf", "empty.pdf", "--output", "test.bib"]
            )

            assert result.exit_code == 1
            assert "No citations extracted" in result.output

    @patch("fitz.open")
    @patch("habanero.Crossref.works")
    def test_cli_with_doi_lookup(
        self, mock_crossref, mock_fitz_open, sample_crossref_response
    ):
        """Test CLI with full DOI → CrossRef workflow."""
        runner = CliRunner()

        # Mock PDF with DOI
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "DOI: 10.1234/test.2023.001"
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_doc.metadata = {}
        mock_fitz_open.return_value = mock_doc

        # Mock CrossRef
        mock_crossref.return_value = sample_crossref_response

        with runner.isolated_filesystem():
            pdf_path = Path("test.pdf")
            pdf_path.touch()

            result = runner.invoke(
                main, ["--pdf", "test.pdf", "--output", "citation.bib"]
            )

            assert result.exit_code == 0
            assert Path("citation.bib").exists()

            # Verify BibTeX contains CrossRef data
            content = Path("citation.bib").read_text()
            assert "Deep Learning for Natural Language Processing" in content
