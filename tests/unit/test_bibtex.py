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

    def test_group_field_in_entry(self):
        """Test that group field is added to BibTeX entry."""
        exporter = BibTeXExporter()
        metadata = {
            "author": "John Smith",
            "title": "Test Paper",
            "year": "2023",
            "group": "MachineLearning",
        }

        entry = exporter._create_bibtex_entry(metadata)
        assert entry.get("groups") == "MachineLearning"

    def test_group_prefix_in_citation_key(self):
        """Test that group name is prepended to citation key."""
        exporter = BibTeXExporter()
        metadata = {
            "author": "John Smith",
            "title": "Deep Learning",
            "year": "2023",
            "group": "MachineLearning",
        }

        entry = exporter._create_bibtex_entry(metadata)
        assert entry["ID"].startswith("MachineLearning_")

    def test_group_prefix_sanitizes_spaces(self):
        """Test that group name with spaces is sanitized for citation key."""
        exporter = BibTeXExporter()
        metadata = {
            "author": "John Smith",
            "title": "Test Paper",
            "year": "2023",
            "group": "Machine Learning",
        }

        entry = exporter._create_bibtex_entry(metadata)
        assert entry["ID"].startswith("Machine_Learning_")
        assert entry.get("groups") == "Machine Learning"

    def test_group_prefix_sanitizes_hyphens(self):
        """Test that group name with hyphens is sanitized for citation key."""
        exporter = BibTeXExporter()
        metadata = {
            "author": "John Smith",
            "title": "Test Paper",
            "year": "2023",
            "group": "Machine-Learning",
        }

        entry = exporter._create_bibtex_entry(metadata)
        assert entry["ID"].startswith("Machine_Learning_")
        assert entry.get("groups") == "Machine-Learning"

    def test_generate_jabref_group_metadata_no_groups(self):
        """Test JabRef metadata generation with no groups."""
        exporter = BibTeXExporter()
        citations = [
            {"author": "John Smith", "title": "Test Paper", "year": "2023"},
            {"author": "Jane Doe", "title": "Another Paper", "year": "2022"},
        ]
        result = exporter._generate_jabref_group_metadata(citations)
        assert result == ""

    def test_generate_jabref_group_metadata_single_group(self):
        """Test JabRef metadata generation with a single group."""
        exporter = BibTeXExporter()
        citations = [
            {"author": "John Smith", "title": "Test Paper", "year": "2023", "group": "MachineLearning", "group_depth": 1},
        ]
        result = exporter._generate_jabref_group_metadata(citations)
        assert "@Comment{jabref-meta: databaseType:bibtex;}" in result
        assert "@Comment{jabref-meta: grouping:" in result
        assert "0 AllEntriesGroup:;" in result
        assert "1 StaticGroup:MachineLearning\\;0x8a8a8aff\\;\\;\\;;" in result

    def test_generate_jabref_group_metadata_multiple_groups(self):
        """Test JabRef metadata generation with multiple groups at same depth."""
        exporter = BibTeXExporter()
        citations = [
            {"author": "John Smith", "title": "Paper 1", "year": "2023", "group": "MachineLearning", "group_depth": 1},
            {"author": "Jane Doe", "title": "Paper 2", "year": "2022", "group": "DeepLearning", "group_depth": 1},
        ]
        result = exporter._generate_jabref_group_metadata(citations)
        assert "@Comment{jabref-meta: databaseType:bibtex;}" in result
        assert "0 AllEntriesGroup:;" in result
        # Groups at same depth should have same index
        assert "1 StaticGroup:DeepLearning\\;0x8a8a8aff\\;\\;\\;;" in result
        assert "1 StaticGroup:MachineLearning\\;0x8a8a8aff\\;\\;\\;;" in result

    def test_generate_jabref_group_metadata_duplicate_groups(self):
        """Test JabRef metadata generation deduplicates groups."""
        exporter = BibTeXExporter()
        citations = [
            {"author": "John Smith", "title": "Paper 1", "year": "2023", "group": "MachineLearning", "group_depth": 1},
            {"author": "Jane Doe", "title": "Paper 2", "year": "2022", "group": "MachineLearning", "group_depth": 1},
            {"author": "Bob Jones", "title": "Paper 3", "year": "2021", "group": "MachineLearning", "group_depth": 1},
        ]
        result = exporter._generate_jabref_group_metadata(citations)
        # Should only have one group entry, not three
        assert result.count("StaticGroup:MachineLearning") == 1
        assert "0 AllEntriesGroup:;" in result
        assert "1 StaticGroup:MachineLearning\\;0x8a8a8aff\\;\\;\\;;" in result

    def test_export_contains_jabref_metadata(self, tmp_path):
        """Test that exported file contains JabRef metadata."""
        exporter = BibTeXExporter()
        citations = [
            {"author": "John Smith", "title": "Test Paper", "year": "2023", "group": "MachineLearning", "group_depth": 1},
        ]
        output_file = tmp_path / "test.bib"
        result = exporter.export(citations, output_file)
        
        assert result is True
        content = output_file.read_text()
        assert "@Comment{jabref-meta: databaseType:bibtex;}" in content
        assert "@Comment{jabref-meta: grouping:" in content
        assert "StaticGroup:MachineLearning" in content

    def test_export_single_contains_jabref_metadata(self):
        """Test that single export contains JabRef metadata."""
        exporter = BibTeXExporter()
        metadata = {
            "author": "John Smith",
            "title": "Test Paper",
            "year": "2023",
            "group": "MachineLearning",
            "group_depth": 1,
        }
        result = exporter.export_single(metadata)
        assert "@Comment{jabref-meta: databaseType:bibtex;}" in result
        assert "@Comment{jabref-meta: grouping:" in result
        assert "StaticGroup:MachineLearning" in result
        # Also verify groups field still exists
        assert "groups = {MachineLearning}" in result

    def test_export_no_groups_no_jabref_metadata(self, tmp_path):
        """Test that export without groups doesn't add JabRef metadata."""
        exporter = BibTeXExporter()
        citations = [
            {"author": "John Smith", "title": "Test Paper", "year": "2023"},
        ]
        output_file = tmp_path / "test.bib"
        result = exporter.export(citations, output_file)
        
        assert result is True
        content = output_file.read_text()
        # Should not have JabRef metadata when no groups
        assert "@Comment{jabref-meta:" not in content

    def test_generate_jabref_group_metadata_with_depths(self):
        """Test JabRef metadata generation with groups at different depths."""
        exporter = BibTeXExporter()
        citations = [
            {"author": "John Smith", "title": "Paper 1", "year": "2023", "group": "test", "group_depth": 1},
            {"author": "Jane Doe", "title": "Paper 2", "year": "2022", "group": "sub", "group_depth": 2},
            {"author": "Bob Jones", "title": "Paper 3", "year": "2021", "group": "other", "group_depth": 1},
        ]
        result = exporter._generate_jabref_group_metadata(citations)
        assert "@Comment{jabref-meta: databaseType:bibtex;}" in result
        assert "@Comment{jabref-meta: grouping:" in result
        assert "0 AllEntriesGroup:;" in result
        # Both "other" and "test" should be at depth 1
        assert "1 StaticGroup:other\\;0x8a8a8aff\\;\\;\\;;" in result
        assert "1 StaticGroup:test\\;0x8a8a8aff\\;\\;\\;;" in result
        # "sub" should be at depth 2
        assert "2 StaticGroup:sub\\;0x8a8a8aff\\;\\;\\;;" in result

    def test_generate_jabref_group_metadata_default_depth(self):
        """Test that group_depth defaults to 1 when not provided."""
        exporter = BibTeXExporter()
        citations = [
            {"author": "John Smith", "title": "Test Paper", "year": "2023", "group": "MachineLearning"},
        ]
        result = exporter._generate_jabref_group_metadata(citations)
        assert "@Comment{jabref-meta: databaseType:bibtex;}" in result
        assert "0 AllEntriesGroup:;" in result
        # Should default to depth 1
        assert "1 StaticGroup:MachineLearning\\;0x8a8a8aff\\;\\;\\;;" in result

    def test_generate_jabref_group_metadata_mixed_depths(self):
        """Test JabRef metadata generation with groups at various depths."""
        exporter = BibTeXExporter()
        citations = [
            {"author": "John Smith", "title": "Paper 1", "year": "2023", "group": "root", "group_depth": 1},
            {"author": "Jane Doe", "title": "Paper 2", "year": "2022", "group": "level2", "group_depth": 2},
            {"author": "Bob Jones", "title": "Paper 3", "year": "2021", "group": "level3", "group_depth": 3},
            {"author": "Alice Brown", "title": "Paper 4", "year": "2020", "group": "another", "group_depth": 1},
        ]
        result = exporter._generate_jabref_group_metadata(citations)
        assert "0 AllEntriesGroup:;" in result
        # Groups at depth 1
        assert "1 StaticGroup:another\\;0x8a8a8aff\\;\\;\\;;" in result
        assert "1 StaticGroup:root\\;0x8a8a8aff\\;\\;\\;;" in result
        # Group at depth 2
        assert "2 StaticGroup:level2\\;0x8a8a8aff\\;\\;\\;;" in result
        # Group at depth 3
        assert "3 StaticGroup:level3\\;0x8a8a8aff\\;\\;\\;;" in result
