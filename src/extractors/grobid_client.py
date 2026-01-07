"""GROBID client for advanced PDF metadata extraction"""

import logging
import requests
from pathlib import Path
from typing import Dict, Optional
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


class GROBIDClient:
    """
    Client for GROBID service.

    GROBID (GeneRation Of BIbliographic Data) is a machine learning library
    for extracting, parsing, and restructuring raw documents into structured
    XML/TEI encoded documents.

    To use GROBID:
    1. Install Docker
    2. Run: docker pull lfoppiano/grobid:0.8.0
    3. Run: docker run -t --rm -p 8070:8070 lfoppiano/grobid:0.8.0
    4. Verify service is running with is_available()
    """

    # TEI namespace for XML parsing
    TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}

    def __init__(self, grobid_url: str = "http://localhost:8070"):
        """
        Initialize GROBID client.

        Args:
            grobid_url: URL of GROBID service
        """
        self.grobid_url = grobid_url.rstrip("/")
        self.available = self.is_available()

        if self.available:
            logger.info(f"GROBID service available at {self.grobid_url}")
        else:
            logger.warning(f"GROBID service not available at {self.grobid_url}")

    def process(self, pdf_path: Path) -> Optional[Dict]:
        """
        Process PDF using GROBID service to extract metadata.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Citation metadata dictionary or None
        """
        if not self.available:
            logger.warning("GROBID service is not available")
            return None

        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return None

        try:
            # Send PDF to GROBID processHeaderDocument endpoint
            url = f"{self.grobid_url}/api/processHeaderDocument"

            with open(pdf_path, "rb") as pdf_file:
                files = {"input": pdf_file}
                response = requests.post(url, files=files, timeout=30)

            if response.status_code != 200:
                logger.error(
                    f"GROBID request failed with status {response.status_code}"
                )
                return None

            # Parse XML response
            metadata = self._parse_tei_xml(response.text)

            if metadata:
                metadata["source"] = "grobid"
                metadata["pdf_file"] = pdf_path.name
                logger.info(f"Successfully extracted metadata from {pdf_path.name}")

            return metadata

        except requests.exceptions.Timeout:
            logger.error(f"GROBID request timed out for {pdf_path.name}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"GROBID request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing PDF with GROBID: {e}")
            return None

    def _parse_tei_xml(self, xml_content: str) -> Optional[Dict]:
        """
        Parse GROBID TEI XML response and extract metadata.

        Args:
            xml_content: XML string from GROBID response

        Returns:
            Metadata dictionary or None
        """
        try:
            root = ET.fromstring(xml_content)

            metadata = {}

            # Extract title
            title_elem = root.find(".//tei:titleStmt/tei:title", self.TEI_NS)
            if title_elem is not None and title_elem.text:
                metadata["title"] = title_elem.text.strip()

            # Extract authors
            authors = []
            for author in root.findall(".//tei:sourceDesc//tei:author", self.TEI_NS):
                # Try to get forename and surname
                forename = author.find(".//tei:forename", self.TEI_NS)
                surname = author.find(".//tei:surname", self.TEI_NS)

                if forename is not None and surname is not None:
                    full_name = f"{forename.text} {surname.text}".strip()
                    authors.append(full_name)
                elif surname is not None:
                    authors.append(surname.text.strip())

            if authors:
                metadata["author"] = " and ".join(authors)

            # Extract publication date/year
            date_elem = root.find(".//tei:publicationStmt/tei:date", self.TEI_NS)
            if date_elem is not None:
                # Try to get 'when' attribute first
                year = date_elem.get("when")
                if year:
                    # Extract just the year if it's a full date
                    metadata["year"] = year[:4] if len(year) >= 4 else year
                elif date_elem.text:
                    metadata["year"] = date_elem.text.strip()

            # Extract journal/publisher
            journal_elem = root.find(".//tei:monogr/tei:title", self.TEI_NS)
            if journal_elem is not None and journal_elem.text:
                metadata["journal"] = journal_elem.text.strip()

            # Extract DOI if present
            doi_elem = root.find(".//tei:idno[@type='DOI']", self.TEI_NS)
            if doi_elem is not None and doi_elem.text:
                metadata["doi"] = doi_elem.text.strip()

            # Extract abstract
            abstract_elem = root.find(".//tei:abstract", self.TEI_NS)
            if abstract_elem is not None:
                # Get all text content from abstract
                abstract_text = "".join(abstract_elem.itertext()).strip()
                if abstract_text:
                    metadata["abstract"] = abstract_text

            # Only return metadata if we got at least a title
            if "title" in metadata:
                logger.debug(f"Extracted metadata: {metadata}")
                return metadata
            else:
                logger.warning("No title found in GROBID response")
                return None

        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing TEI XML: {e}")
            return None

    def is_available(self) -> bool:
        """
        Check if GROBID service is available.

        Returns:
            True if service is reachable and responsive
        """
        try:
            url = f"{self.grobid_url}/api/isalive"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
