"""Unit tests for CrossRef API client"""

import pytest
from unittest.mock import MagicMock, patch
import responses

from src.api_clients.crossref import CrossRefClient


@pytest.mark.unit
class TestCrossRefClient:
    """Test suite for CrossRef API client."""

    def test_init_no_email(self):
        """Test initialization without email."""
        client = CrossRefClient()
        assert client.client is not None

    def test_init_with_email(self):
        """Test initialization with email for polite pool."""
        client = CrossRefClient(email="test@example.com")
        assert client.client is not None

    @patch("habanero.Crossref.works")
    def test_get_metadata_success(self, mock_works, sample_crossref_response):
        """Test successful metadata retrieval."""
        mock_works.return_value = sample_crossref_response

        client = CrossRefClient()
        metadata = client.get_metadata("10.1234/test.2023.001")

        assert metadata is not None
        assert metadata["title"] == "Deep Learning for Natural Language Processing"
        assert metadata["author"] == "John Smith and Jane Doe"
        assert metadata["year"] == "2023"
        assert metadata["doi"] == "10.1234/test.2023.001"

    @patch("habanero.Crossref.works")
    def test_get_metadata_not_found(self, mock_works):
        """Test handling DOI not found."""
        mock_works.return_value = None

        client = CrossRefClient()
        metadata = client.get_metadata("10.invalid/notfound")

        assert metadata is None

    @patch("habanero.Crossref.works")
    def test_get_metadata_api_error(self, mock_works):
        """Test handling API errors."""
        mock_works.side_effect = Exception("API Error")

        client = CrossRefClient()
        metadata = client.get_metadata("10.1234/test")

        assert metadata is None

    def test_parse_crossref_response_complete(self, sample_crossref_response):
        """Test parsing complete CrossRef response."""
        client = CrossRefClient()
        message = sample_crossref_response["message"]
        metadata = client._parse_crossref_response(message)

        assert metadata["title"] == "Deep Learning for Natural Language Processing"
        assert metadata["author"] == "John Smith and Jane Doe"
        assert metadata["year"] == "2023"
        assert metadata["journal"] == "Journal of Machine Learning Research"
        assert metadata["volume"] == "24"
        assert metadata["issue"] == "3"
        assert metadata["pages"] == "123-145"
        assert metadata["publisher"] == "JMLR.org"

    def test_parse_crossref_response_minimal(self):
        """Test parsing minimal CrossRef response."""
        client = CrossRefClient()
        message = {
            "title": ["Minimal Paper"],
        }
        metadata = client._parse_crossref_response(message)

        assert metadata["title"] == "Minimal Paper"
        assert metadata["author"] is None
        assert metadata["year"] is None

    def test_parse_crossref_response_multiple_authors(self):
        """Test parsing response with multiple authors."""
        client = CrossRefClient()
        message = {
            "author": [
                {"given": "John", "family": "Smith"},
                {"given": "Jane", "family": "Doe"},
                {"given": "Bob", "family": "Johnson"},
            ]
        }
        metadata = client._parse_crossref_response(message)

        assert metadata["author"] == "John Smith and Jane Doe and Bob Johnson"

    def test_parse_crossref_response_no_given_name(self):
        """Test parsing author without given name."""
        client = CrossRefClient()
        message = {
            "author": [
                {"family": "Smith"},
            ]
        }
        metadata = client._parse_crossref_response(message)

        assert metadata["author"] == "Smith"

    def test_parse_crossref_response_date_variations(self):
        """Test parsing different date formats."""
        client = CrossRefClient()

        # Test published-print
        message1 = {"published-print": {"date-parts": [[2023, 3, 15]]}}
        assert client._parse_crossref_response(message1)["year"] == "2023"

        # Test published-online
        message2 = {"published-online": {"date-parts": [[2022, 5, 10]]}}
        assert client._parse_crossref_response(message2)["year"] == "2022"

        # Test issued
        message3 = {"issued": {"date-parts": [[2021, 1, 1]]}}
        assert client._parse_crossref_response(message3)["year"] == "2021"

    def test_parse_crossref_response_multiple_titles(self):
        """Test parsing response with multiple titles (uses first)."""
        client = CrossRefClient()
        message = {
            "title": ["Main Title", "Alternative Title"],
        }
        metadata = client._parse_crossref_response(message)

        assert metadata["title"] == "Main Title"

    def test_parse_crossref_response_issn(self):
        """Test parsing ISSN field."""
        client = CrossRefClient()
        message = {
            "ISSN": ["1234-5678", "8765-4321"],
        }
        metadata = client._parse_crossref_response(message)

        assert metadata["issn"] == "1234-5678"

    def test_parse_crossref_response_isbn(self):
        """Test parsing ISBN field (for books)."""
        client = CrossRefClient()
        message = {
            "ISBN": ["978-1234567890"],
        }
        metadata = client._parse_crossref_response(message)

        assert metadata["isbn"] == "978-1234567890"

    @patch("habanero.Crossref.works")
    def test_search_by_title_success(self, mock_works):
        """Test searching by title."""
        mock_works.return_value = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1234/result1",
                        "title": ["First Result"],
                        "author": [{"given": "John", "family": "Smith"}],
                    },
                    {
                        "DOI": "10.5678/result2",
                        "title": ["Second Result"],
                    },
                ]
            }
        }

        client = CrossRefClient()
        results = client.search_by_title("Deep Learning", limit=2)

        assert len(results) == 2
        assert results[0]["title"] == "First Result"
        assert results[0]["doi"] == "10.1234/result1"
        assert results[1]["title"] == "Second Result"

    @patch("habanero.Crossref.works")
    def test_search_by_title_no_results(self, mock_works):
        """Test searching with no results."""
        mock_works.return_value = {
            "message": {"items": []}
        }

        client = CrossRefClient()
        results = client.search_by_title("Nonexistent Paper")

        assert results == []

    @patch("habanero.Crossref.works")
    def test_search_by_title_error(self, mock_works):
        """Test search error handling."""
        mock_works.side_effect = Exception("Search error")

        client = CrossRefClient()
        results = client.search_by_title("Test")

        assert results == []

    def test_parse_crossref_response_all_types(self):
        """Test parsing different publication types."""
        client = CrossRefClient()

        types = [
            "journal-article",
            "book-chapter",
            "proceedings-article",
            "posted-content",
        ]

        for pub_type in types:
            message = {"type": pub_type}
            metadata = client._parse_crossref_response(message)
            assert metadata["type"] == pub_type
