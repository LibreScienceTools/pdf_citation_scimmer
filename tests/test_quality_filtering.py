"""
Unit tests for metadata quality filtering.

Tests for the _is_high_quality_metadata method that identifies low-quality
metadata entries that should be treated as extraction failures.
"""

import pytest
from pathlib import Path
import re
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.main import CitationExtractor


class TestQualityFiltering:
    """Test suite for metadata quality filtering functionality."""

    @pytest.fixture
    def extractor(self):
        """Create a CitationExtractor instance with quality filtering method."""
        # Create instance - we only need the _is_high_quality_metadata method
        return CitationExtractor()

    def test_high_quality_metadata_passes(self, extractor):
        """Test that valid, high-quality metadata passes quality check."""
        metadata = {
            "title": "A Comprehensive Study on Machine Learning",
            "author": "John Doe and Jane Smith",
            "year": "2023",
            "doi": "10.1000/xyz123",
            "journal": "Journal of AI Research"
        }
        assert extractor._is_high_quality_metadata(metadata) == True

    def test_high_quality_minimal_metadata_passes(self, extractor):
        """Test that minimal but valid metadata passes quality check."""
        metadata = {
            "title": "Research Paper",
            "author": "Researcher Name"
        }
        assert extractor._is_high_quality_metadata(metadata) == True

    # Tests for generic titles
    def test_generic_title_misc_fails(self, extractor):
        """Test that 'Misc' title is rejected."""
        metadata = {"title": "Misc", "author": "John Doe", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_generic_title_unknown_fails(self, extractor):
        """Test that 'Unknown' title is rejected."""
        metadata = {"title": "Unknown", "author": "John Doe", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_generic_title_untitled_fails(self, extractor):
        """Test that 'Untitled' title is rejected."""
        metadata = {"title": "Untitled", "author": "John Doe", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_generic_title_document_fails(self, extractor):
        """Test that 'Document' title is rejected."""
        metadata = {"title": "Document", "author": "John Doe", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_generic_title_no_title_fails(self, extractor):
        """Test that 'No title' title is rejected."""
        metadata = {"title": "No title", "author": "John Doe", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_generic_title_case_insensitive(self, extractor):
        """Test that title matching is case-insensitive."""
        metadata = {"title": "MISC", "author": "John Doe", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == False

    # Tests for PII DOI patterns (the specific issue mentioned by user)
    def test_pii_doi_pattern_basic_fails(self, extractor):
        """Test that basic PII DOI pattern is rejected."""
        metadata = {
            "title": "Some Paper",
            "author": "John Doe",
            "year": "2023",
            "doi": "S0021-8502(97)10031-3"
        }
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_pii_doi_pattern_variation1_fails(self, extractor):
        """Test another PII DOI pattern variation."""
        metadata = {
            "title": "Some Paper",
            "author": "John Doe",
            "year": "2023",
            "doi": "S1234-5678(99)12345-6"
        }
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_pii_doi_pattern_variation2_fails(self, extractor):
        """Test PII DOI pattern with different year."""
        metadata = {
            "title": "Some Paper",
            "author": "John Doe",
            "year": "2023",
            "doi": "S1234-5678(20)123-456"
        }
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_pii_doi_pattern_with_leading_zeros(self, extractor):
        """Test PII DOI pattern with leading zeros (user's example)."""
        metadata = {
            "title": "Some Paper",
            "author": "John Doe",
            "year": "2023",
            "doi": "S0021-8502(97)10031-3"
        }
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_valid_doi_passes(self, extractor):
        """Test that valid DOI format passes."""
        metadata = {
            "title": "Some Paper",
            "author": "John Doe",
            "year": "2023",
            "doi": "10.1000/xyz123"
        }
        assert extractor._is_high_quality_metadata(metadata) == True

    def test_valid_doi_with_slashes_passes(self, extractor):
        """Test that valid DOI with slashes passes."""
        metadata = {
            "title": "Some Paper",
            "author": "John Doe",
            "year": "2023",
            "doi": "10.1016/j.foo.2023.01.001"
        }
        assert extractor._is_high_quality_metadata(metadata) == True

    def test_no_doi_passes(self, extractor):
        """Test that missing DOI doesn't cause failure if other fields are good."""
        metadata = {
            "title": "Some Paper",
            "author": "John Doe",
            "year": "2023"
        }
        assert extractor._is_high_quality_metadata(metadata) == True

    # Tests for generic authors
    def test_generic_author_unknown_fails(self, extractor):
        """Test that 'Unknown' author is rejected."""
        metadata = {"title": "Good Title", "author": "Unknown", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_generic_author_anonymous_fails(self, extractor):
        """Test that 'Anonymous' author is rejected."""
        metadata = {"title": "Good Title", "author": "Anonymous", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_generic_author_none_fails(self, extractor):
        """Test that 'None' author is rejected."""
        metadata = {"title": "Good Title", "author": "None", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == False

    # Tests for bad years
    def test_bad_year_yyyy_fails(self, extractor):
        """Test that 'YYYY' year is rejected."""
        metadata = {"title": "Good Title", "author": "John Doe", "year": "YYYY"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_bad_year_unknown_fails(self, extractor):
        """Test that 'Unknown' year is rejected."""
        metadata = {"title": "Good Title", "author": "John Doe", "year": "Unknown"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_bad_year_0000_fails(self, extractor):
        """Test that '0000' year is rejected."""
        metadata = {"title": "Good Title", "author": "John Doe", "year": "0000"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_bad_year_1900_fails(self, extractor):
        """Test that '1900' year is rejected."""
        metadata = {"title": "Good Title", "author": "John Doe", "year": "1900"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_year_out_of_range_low_fails(self, extractor):
        """Test that year < 1900 is rejected."""
        metadata = {"title": "Good Title", "author": "John Doe", "year": "1899"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_year_out_of_range_high_fails(self, extractor):
        """Test that year > 2100 is rejected."""
        metadata = {"title": "Good Title", "author": "John Doe", "year": "2101"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_valid_year_passes(self, extractor):
        """Test that valid year passes."""
        metadata = {"title": "Good Title", "author": "John Doe", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == True

    def test_valid_year_range_passes(self, extractor):
        """Test that years in valid range pass."""
        for year in ["1950", "2000", "2023", "2050", "2099"]:
            metadata = {"title": "Good Title", "author": "John Doe", "year": year}
            assert extractor._is_high_quality_metadata(metadata) == True

    # Tests for missing critical fields
    def test_missing_both_title_and_author_fails(self, extractor):
        """Test that metadata missing both title and author is rejected."""
        metadata = {"year": "2023", "doi": "10.1000/xyz"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_missing_title_but_has_author_passes(self, extractor):
        """Test that metadata with only author passes."""
        metadata = {"author": "John Doe", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == True

    def test_missing_author_but_has_title_passes(self, extractor):
        """Test that metadata with only title passes."""
        metadata = {"title": "Good Title", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == True

    def test_empty_metadata_fails(self, extractor):
        """Test that completely empty metadata is rejected."""
        metadata = {}
        assert extractor._is_high_quality_metadata(metadata) == False

    # Tests for generic journals
    def test_generic_journal_unknown_fails(self, extractor):
        """Test that 'Unknown' journal is rejected."""
        metadata = {
            "title": "Good Title",
            "author": "John Doe",
            "year": "2023",
            "journal": "Unknown"
        }
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_generic_journal_misc_fails(self, extractor):
        """Test that 'Misc' journal is rejected."""
        metadata = {
            "title": "Good Title",
            "author": "John Doe",
            "year": "2023",
            "journal": "Misc"
        }
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_valid_journal_passes(self, extractor):
        """Test that valid journal passes."""
        metadata = {
            "title": "Good Title",
            "author": "John Doe",
            "year": "2023",
            "journal": "Nature"
        }
        assert extractor._is_high_quality_metadata(metadata) == True

    # Edge cases
    def test_whitespace_title(self, extractor):
        """Test that title with only whitespace fails."""
        metadata = {"title": "   ", "author": "John Doe", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_whitespace_author(self, extractor):
        """Test that author with only whitespace fails."""
        metadata = {"title": "Good Title", "author": "   ", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_empty_string_title_fails(self, extractor):
        """Test that empty string title fails."""
        metadata = {"title": "", "author": "John Doe", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_empty_string_author_fails(self, extractor):
        """Test that empty string author fails."""
        metadata = {"title": "Good Title", "author": "", "year": "2023"}
        assert extractor._is_high_quality_metadata(metadata) == False

    def test_year_range_string_passes(self, extractor):
        """Test that year range as string passes."""
        metadata = {"title": "Good Title", "author": "John Doe", "year": "2020-2023"}
        assert extractor._is_high_quality_metadata(metadata) == True


class TestPIIPatternMatching:
    """Test the PII DOI pattern matching specifically."""

    def test_pii_pattern_regex(self):
        """Test that the PII pattern regex matches expected formats."""
        pattern = r'^S\d{4}-\d{4}\(\d{2}\)\d+-\d+$'
        
        # Should match
        matching = [
            "S0021-8502(97)10031-3",
            "S1234-5678(99)12345-6",
            "S1234-5678(20)123-456",
            "S0000-0000(00)0-0",
            "S9999-9999(99)999999-9",
        ]
        for doi in matching:
            assert re.match(pattern, doi), f"Pattern should match: {doi}"
        
        # Should NOT match
        non_matching = [
            "10.1000/xyz123",
            "10.1016/j.foo.2023.01.001",
            "S1234-5678(99)12345",  # Missing trailing hyphen and digits
            "S12345678(99)12345-6",  # Missing hyphen after S
            "1234-5678(99)12345-6",  # Missing S prefix
            "S123-5678(99)12345-6",  # Only 3 digits before hyphen
            "S12345-5678(99)12345-6",  # 5 digits before hyphen
            "S1234-5678(999)12345-6",  # 3 digits in parentheses
            "S1234-5678(9)12345-6",  # 1 digit in parentheses
            "",  # Empty string
            "S00218502(97)10031-3",  # Missing hyphen after S prefix
        ]
        for doi in non_matching:
            assert not re.match(pattern, doi), f"Pattern should NOT match: {doi}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
