"""Unit tests for GROBID client"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import requests

from src.extractors.grobid_client import GROBIDClient


@pytest.mark.unit
class TestGROBIDClient:
    """Test suite for GROBID client."""

    @patch("requests.get")
    def test_init_service_available(self, mock_get):
        """Test initialization when GROBID service is available."""
        mock_get.return_value.status_code = 200

        client = GROBIDClient()

        assert client.grobid_url == "http://localhost:8070"
        assert client.available is True
        mock_get.assert_called_once_with("http://localhost:8070/api/isalive", timeout=5)

    @patch("requests.get")
    def test_init_service_unavailable(self, mock_get):
        """Test initialization when GROBID service is unavailable."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection refused")

        client = GROBIDClient()

        assert client.available is False

    @patch("requests.get")
    def test_init_custom_url(self, mock_get):
        """Test initialization with custom GROBID URL."""
        mock_get.return_value.status_code = 200

        client = GROBIDClient(grobid_url="http://custom:9000")

        assert client.grobid_url == "http://custom:9000"
        mock_get.assert_called_once_with("http://custom:9000/api/isalive", timeout=5)

    @patch("requests.get")
    def test_init_url_trailing_slash(self, mock_get):
        """Test that trailing slash is removed from URL."""
        mock_get.return_value.status_code = 200

        client = GROBIDClient(grobid_url="http://localhost:8070/")

        assert client.grobid_url == "http://localhost:8070"

    @patch("requests.get")
    def test_is_available_success(self, mock_get):
        """Test is_available returns True when service is up."""
        mock_get.return_value.status_code = 200

        client = GROBIDClient()

        assert client.is_available() is True

    @patch("requests.get")
    def test_is_available_failure(self, mock_get):
        """Test is_available returns False on connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        # Don't call is_available during init
        with patch.object(GROBIDClient, 'is_available', return_value=False):
            client = GROBIDClient()

        assert client.is_available() is False

    @patch("requests.get")
    def test_is_available_timeout(self, mock_get):
        """Test is_available returns False on timeout."""
        mock_get.side_effect = requests.exceptions.Timeout()

        with patch.object(GROBIDClient, 'is_available', return_value=False):
            client = GROBIDClient()

        assert client.is_available() is False

    @patch("requests.post")
    @patch("requests.get")
    @patch("builtins.open", new_callable=mock_open, read_data=b"PDF content")
    def test_process_success(self, mock_file, mock_get, mock_post, sample_grobid_xml_response, tmp_path):
        """Test successful PDF processing."""
        mock_get.return_value.status_code = 200
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = sample_grobid_xml_response

        client = GROBIDClient()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        metadata = client.process(pdf_path)

        assert metadata is not None
        assert metadata["title"] == "Deep Learning for Natural Language Processing"
        assert metadata["author"] == "John Smith and Jane Doe"
        assert metadata["year"] == "2023"
        assert metadata["source"] == "grobid"
        assert metadata["pdf_file"] == "test.pdf"

    @patch("requests.get")
    def test_process_service_unavailable(self, mock_get, tmp_path):
        """Test processing when service is unavailable."""
        mock_get.side_effect = requests.exceptions.RequestException()

        client = GROBIDClient()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        metadata = client.process(pdf_path)

        assert metadata is None

    @patch("requests.get")
    def test_process_pdf_not_found(self, mock_get):
        """Test processing non-existent PDF."""
        mock_get.return_value.status_code = 200

        client = GROBIDClient()
        pdf_path = Path("/nonexistent/file.pdf")

        metadata = client.process(pdf_path)

        assert metadata is None

    @patch("requests.post")
    @patch("requests.get")
    @patch("builtins.open", new_callable=mock_open, read_data=b"PDF content")
    def test_process_grobid_error(self, mock_file, mock_get, mock_post, tmp_path):
        """Test handling GROBID API error response."""
        mock_get.return_value.status_code = 200
        mock_post.return_value.status_code = 500

        client = GROBIDClient()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        metadata = client.process(pdf_path)

        assert metadata is None

    @patch("requests.post")
    @patch("requests.get")
    @patch("builtins.open", new_callable=mock_open, read_data=b"PDF content")
    def test_process_timeout(self, mock_file, mock_get, mock_post, tmp_path):
        """Test handling timeout during processing."""
        mock_get.return_value.status_code = 200
        mock_post.side_effect = requests.exceptions.Timeout()

        client = GROBIDClient()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        metadata = client.process(pdf_path)

        assert metadata is None

    @patch("requests.post")
    @patch("requests.get")
    @patch("builtins.open", new_callable=mock_open, read_data=b"PDF content")
    def test_process_request_exception(self, mock_file, mock_get, mock_post, tmp_path):
        """Test handling request exception."""
        mock_get.return_value.status_code = 200
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        client = GROBIDClient()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        metadata = client.process(pdf_path)

        assert metadata is None

    @patch("requests.get")
    def test_parse_tei_xml_complete(self, mock_get, sample_grobid_xml_response):
        """Test parsing complete TEI XML response."""
        mock_get.return_value.status_code = 200

        client = GROBIDClient()
        metadata = client._parse_tei_xml(sample_grobid_xml_response)

        assert metadata is not None
        assert metadata["title"] == "Deep Learning for Natural Language Processing"
        assert metadata["author"] == "John Smith and Jane Doe"
        assert metadata["year"] == "2023"
        assert metadata["journal"] == "Journal of Machine Learning Research"
        assert metadata["doi"] == "10.1234/test.2023.001"
        assert "abstract" in metadata

    @patch("requests.get")
    def test_parse_tei_xml_minimal(self, mock_get):
        """Test parsing minimal TEI XML with only title."""
        mock_get.return_value.status_code = 200

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt>
                        <title>Minimal Title</title>
                    </titleStmt>
                </fileDesc>
            </teiHeader>
        </TEI>"""

        client = GROBIDClient()
        metadata = client._parse_tei_xml(xml)

        assert metadata is not None
        assert metadata["title"] == "Minimal Title"
        assert "author" not in metadata

    @patch("requests.get")
    def test_parse_tei_xml_no_title(self, mock_get):
        """Test parsing XML without title returns None."""
        mock_get.return_value.status_code = 200

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt></titleStmt>
                </fileDesc>
            </teiHeader>
        </TEI>"""

        client = GROBIDClient()
        metadata = client._parse_tei_xml(xml)

        assert metadata is None

    @patch("requests.get")
    def test_parse_tei_xml_invalid(self, mock_get):
        """Test parsing invalid XML."""
        mock_get.return_value.status_code = 200

        client = GROBIDClient()
        metadata = client._parse_tei_xml("Invalid XML <not>closed")

        assert metadata is None

    @patch("requests.get")
    def test_parse_tei_xml_single_author(self, mock_get):
        """Test parsing single author."""
        mock_get.return_value.status_code = 200

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt><title>Test</title></titleStmt>
                    <sourceDesc>
                        <biblStruct>
                            <analytic>
                                <author>
                                    <persName>
                                        <forename>John</forename>
                                        <surname>Doe</surname>
                                    </persName>
                                </author>
                            </analytic>
                        </biblStruct>
                    </sourceDesc>
                </fileDesc>
            </teiHeader>
        </TEI>"""

        client = GROBIDClient()
        metadata = client._parse_tei_xml(xml)

        assert metadata["author"] == "John Doe"

    @patch("requests.get")
    def test_parse_tei_xml_surname_only(self, mock_get):
        """Test parsing author with surname only."""
        mock_get.return_value.status_code = 200

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt><title>Test</title></titleStmt>
                    <sourceDesc>
                        <biblStruct>
                            <analytic>
                                <author>
                                    <persName>
                                        <surname>Smith</surname>
                                    </persName>
                                </author>
                            </analytic>
                        </biblStruct>
                    </sourceDesc>
                </fileDesc>
            </teiHeader>
        </TEI>"""

        client = GROBIDClient()
        metadata = client._parse_tei_xml(xml)

        assert metadata["author"] == "Smith"

    @patch("requests.get")
    def test_parse_tei_xml_date_when_attribute(self, mock_get):
        """Test parsing date from 'when' attribute."""
        mock_get.return_value.status_code = 200

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt><title>Test</title></titleStmt>
                    <publicationStmt>
                        <date when="2023-05-15"/>
                    </publicationStmt>
                </fileDesc>
            </teiHeader>
        </TEI>"""

        client = GROBIDClient()
        metadata = client._parse_tei_xml(xml)

        assert metadata["year"] == "2023"

    @patch("requests.get")
    def test_parse_tei_xml_date_text(self, mock_get):
        """Test parsing date from element text."""
        mock_get.return_value.status_code = 200

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt><title>Test</title></titleStmt>
                    <publicationStmt>
                        <date>2022</date>
                    </publicationStmt>
                </fileDesc>
            </teiHeader>
        </TEI>"""

        client = GROBIDClient()
        metadata = client._parse_tei_xml(xml)

        assert metadata["year"] == "2022"

    @patch("requests.get")
    def test_parse_tei_xml_with_abstract(self, mock_get):
        """Test parsing abstract from XML."""
        mock_get.return_value.status_code = 200

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt><title>Test Paper</title></titleStmt>
                </fileDesc>
                <profileDesc>
                    <abstract>
                        <p>This is the abstract text.</p>
                    </abstract>
                </profileDesc>
            </teiHeader>
        </TEI>"""

        client = GROBIDClient()
        metadata = client._parse_tei_xml(xml)

        assert "abstract" in metadata
        assert "This is the abstract text." in metadata["abstract"]

    @patch("requests.get")
    def test_parse_tei_xml_with_doi(self, mock_get):
        """Test parsing DOI from XML."""
        mock_get.return_value.status_code = 200

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt><title>Test</title></titleStmt>
                    <sourceDesc>
                        <biblStruct>
                            <idno type="DOI">10.1234/example</idno>
                        </biblStruct>
                    </sourceDesc>
                </fileDesc>
            </teiHeader>
        </TEI>"""

        client = GROBIDClient()
        metadata = client._parse_tei_xml(xml)

        assert metadata["doi"] == "10.1234/example"

    @patch("requests.get")
    def test_parse_tei_xml_with_journal(self, mock_get):
        """Test parsing journal title from XML."""
        mock_get.return_value.status_code = 200

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <teiHeader>
                <fileDesc>
                    <titleStmt><title>Test</title></titleStmt>
                    <sourceDesc>
                        <biblStruct>
                            <monogr>
                                <title>Nature</title>
                            </monogr>
                        </biblStruct>
                    </sourceDesc>
                </fileDesc>
            </teiHeader>
        </TEI>"""

        client = GROBIDClient()
        metadata = client._parse_tei_xml(xml)

        assert metadata["journal"] == "Nature"
