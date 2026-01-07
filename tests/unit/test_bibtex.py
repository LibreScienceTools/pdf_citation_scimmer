"""Unit tests for BibTeX exporter"""

import pytest
from pathlib import Path

from src.exporters.bibtex import BibTeXExporter


@pytest.mark.unit
class TestBibTeXExporter:
    """Test suite for BibTeX export functionality."""

    def test_init(self):
        """Test BibTeXExporter initialization."""
        exporter = BibTeXExporter()
        assert exporter.entry_types is not None

    def test_get_entry_type_journal_article(self):
        """Test mapping journal-article to BibTeX type."""
        exporter = BibTeXExporter()
        result = exporter._get_entry_type("journal-article")
        assert result == "article"

    def test_get_entry_type_book(self):
        """Test mapping book to BibTeX type."""
        exporter = BibTeXExporter()
        result = exporter._get_entry_type("book")
        assert result == "book"

    def test_get_entry_type_unknown(self):
        """Test mapping unknown type defaults to misc."""
        exporter = BibTeXExporter()
        result = exporter._get_entry_type("unknown-type")
        assert result == "misc"

    def test_get_entry_type_none(self):
        """Test mapping None type defaults to misc."""
        exporter = BibTeXExporter()
        result = exporter._get_entry_type(None)
        assert result == "misc"

    def test_generate_citation_key_complete(self):
        """Test generating citation key with complete metadata."""
        exporter = BibTeXExporter()
        metadata = {
            "author": "John Smith and Jane Doe",
            "year": "2023",
            "title": "Deep Learning for Natural Language Processing",
        }
        key = exporter._generate_citation_key(metadata)
        assert key == "Smith_2023_Deep"

    def test_generate_citation_key_no_author(self):
        """Test generating citation key without author."""
        exporter = BibTeXExporter()
        metadata = {
            "year": "2023",
            "title": "Deep Learning for NLP",
        }
        key = exporter._generate_citation_key(metadata)
        assert key == "Unknown_2023_Deep"

    def test_generate_citation_key_no_year(self):
        """Test generating citation key without year."""
        exporter = BibTeXExporter()
        metadata = {
            "author": "John Smith",
            "title": "Deep Learning",
        }
        key = exporter._generate_citation_key(metadata)
        assert key == "Smith_YYYY_Deep"

    def test_generate_citation_key_no_title(self):
        """Test generating citation key without title."""
        exporter = BibTeXExporter()
        metadata = {
            "author": "John Smith",
            "year": "2023",
        }
        key = exporter._generate_citation_key(metadata)
        assert key == "Smith_2023_NoTitle"

    def test_generate_citation_key_removes_special_chars(self):
        """Test that citation key removes special characters."""
        exporter = BibTeXExporter()
        metadata = {
            "author": "Müller, François",
            "year": "2023",
            "title": "Über Deep Learning!",
        }
        key = exporter._generate_citation_key(metadata)
        # Should remove special chars
        assert "," not in key
        assert "!" not in key

    def test_generate_citation_key_skips_articles(self):
        """Test that citation key skips common articles."""
        exporter = BibTeXExporter()
        metadata = {
            "author": "Smith",
            "year": "2023",
            "title": "The Analysis of a Novel Approach",
        }
        key = exporter._generate_citation_key(metadata)
        # Should skip "The", "a" and use "Analysis"
        assert "Analysis" in key

    def test_create_bibtex_entry_article(self, sample_crossref_response):
        """Test creating BibTeX entry for article."""
        exporter = BibTeXExporter()
        metadata = {
            "type": "journal-article",
            "title": "Test Paper",
            "author": "John Smith",
            "year": "2023",
            "journal": "Test Journal",
            "volume": "10",
            "doi": "10.1234/test",
        }

        entry = exporter._create_bibtex_entry(metadata)

        assert entry["ENTRYTYPE"] == "article"
        assert entry["title"] == "Test Paper"
        assert entry["author"] == "John Smith"
        assert entry["year"] == "2023"
        assert entry["journal"] == "Test Journal"
        assert entry["volume"] == "10"
        assert entry["doi"] == "10.1234/test"

    def test_create_bibtex_entry_minimal(self):
        """Test creating BibTeX entry with minimal metadata."""
        exporter = BibTeXExporter()
        metadata = {
            "title": "Test Paper",
        }

        entry = exporter._create_bibtex_entry(metadata)

        assert entry["ENTRYTYPE"] == "misc"
        assert entry["title"] == "Test Paper"
        assert "author" not in entry  # Should not include None values

    def test_clean_entry_removes_none(self):
        """Test that entry cleaning removes None values."""
        exporter = BibTeXExporter()
        entry = {
            "ID": "test",
            "title": "Test",
            "author": None,
            "year": "2023",
        }

        cleaned = exporter._clean_entry(entry)

        assert "title" in cleaned
        assert "year" in cleaned
        assert "author" not in cleaned

    def test_export_single_citation(self, tmp_path):
        """Test exporting single citation to file."""
        exporter = BibTeXExporter()
        metadata = {
            "type": "journal-article",
            "title": "Test Paper",
            "author": "John Smith",
            "year": "2023",
            "journal": "Test Journal",
            "doi": "10.1234/test",
        }

        output_file = tmp_path / "test.bib"
        result = exporter.export([metadata], output_file)

        assert result is True
        assert output_file.exists()

        # Verify content
        content = output_file.read_text()
        assert "@article{" in content
        assert "title = {Test Paper}" in content or "title={Test Paper}" in content

    def test_export_multiple_citations(self, tmp_path):
        """Test exporting multiple citations to file."""
        exporter = BibTeXExporter()
        citations = [
            {
                "title": "Paper 1",
                "author": "Author 1",
                "year": "2023",
            },
            {
                "title": "Paper 2",
                "author": "Author 2",
                "year": "2022",
            },
        ]

        output_file = tmp_path / "test.bib"
        result = exporter.export(citations, output_file)

        assert result is True

        content = output_file.read_text()
        assert "Paper 1" in content
        assert "Paper 2" in content

    def test_export_empty_list(self, tmp_path):
        """Test exporting empty citation list."""
        exporter = BibTeXExporter()
        output_file = tmp_path / "test.bib"
        result = exporter.export([], output_file)

        assert result is True
        assert output_file.exists()

    def test_export_single_string(self):
        """Test exporting single citation as string."""
        exporter = BibTeXExporter()
        metadata = {
            "type": "journal-article",
            "title": "Test Paper",
            "author": "John Smith",
            "year": "2023",
        }

        bibtex_string = exporter.export_single(metadata)

        assert "@article{" in bibtex_string or "@misc{" in bibtex_string
        assert "Test Paper" in bibtex_string
        assert "John Smith" in bibtex_string

    def test_field_mapping(self):
        """Test all field mappings are correct."""
        exporter = BibTeXExporter()
        metadata = {
            "author": "John Smith",
            "title": "Test",
            "year": "2023",
            "journal": "Journal",
            "volume": "10",
            "issue": "2",
            "pages": "1-10",
            "publisher": "Publisher",
            "doi": "10.1234/test",
            "url": "https://example.com",
            "abstract": "Abstract text",
            "issn": "1234-5678",
            "isbn": "978-1234567890",
        }

        entry = exporter._create_bibtex_entry(metadata)

        # Check CrossRef field names mapped to BibTeX field names
        assert entry.get("number") == "2"  # issue -> number
        assert entry.get("pages") == "1-10"

    def test_multiple_authors_formatting(self):
        """Test that multiple authors are preserved."""
        exporter = BibTeXExporter()
        metadata = {
            "author": "John Smith and Jane Doe and Bob Johnson",
            "title": "Test",
            "year": "2023",
        }

        entry = exporter._create_bibtex_entry(metadata)
        assert entry["author"] == "John Smith and Jane Doe and Bob Johnson"
