"""Extract DOI (Digital Object Identifier) from PDF content"""

import re
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class DOIExtractor:
    """Extracts DOI from PDF text content."""

    def __init__(self, scan_pages: int = 3):
        """
        Initialize DOI extractor.

        Args:
            scan_pages: Number of pages to scan for DOI (default: 3)
        """
        self.scan_pages = scan_pages

        # Common DOI patterns
        self.patterns = [
            # Standard DOI pattern
            r"10\.\d{4,9}/[-._;()/:A-Z0-9]+",
            # DOI with doi: prefix
            r"doi:\s*10\.\d{4,9}/[-._;()/:A-Z0-9]+",
            # DOI with https://doi.org/
            r"https?://doi\.org/10\.\d{4,9}/[-._;()/:A-Z0-9]+",
            # DOI with dx.doi.org
            r"https?://dx\.doi\.org/10\.\d{4,9}/[-._;()/:A-Z0-9]+",
        ]

    def extract(self, pdf_path: Path) -> Optional[str]:
        """
        Extract DOI from PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            DOI string if found, None otherwise
        """
        try:
            doc = fitz.open(pdf_path)

            # Scan first N pages
            pages_to_scan = min(self.scan_pages, len(doc))

            for page_num in range(pages_to_scan):
                page = doc[page_num]
                text = page.get_text()

                # Try each pattern
                doi = self._find_doi_in_text(text)
                if doi:
                    doc.close()
                    logger.info(f"Found DOI in {pdf_path.name}: {doi}")
                    return doi

            doc.close()
            logger.warning(f"No DOI found in {pdf_path.name}")
            return None

        except Exception as e:
            logger.error(f"Error extracting DOI from {pdf_path}: {e}")
            return None

    def _find_doi_in_text(self, text: str) -> Optional[str]:
        """
        Find DOI in text using regex patterns.

        Args:
            text: Text to search

        Returns:
            Cleaned DOI string if found
        """
        for pattern in self.patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Clean and return the first match
                doi = self._clean_doi(matches[0])
                if doi:
                    return doi

        return None

    def _clean_doi(self, doi: str) -> str:
        """
        Clean DOI string by removing prefixes and URLs.

        Args:
            doi: Raw DOI string

        Returns:
            Cleaned DOI (just the identifier part)
        """
        # Remove URL prefixes
        doi = re.sub(r"https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)

        # Remove 'doi:' prefix
        doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)

        # Remove trailing punctuation that might have been captured
        doi = doi.rstrip(".,;:")

        # Trim whitespace
        doi = doi.strip()

        return doi

    def extract_multiple(self, pdf_path: Path) -> List[str]:
        """
        Extract all DOIs found in a PDF (useful for papers with references).

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of DOI strings
        """
        try:
            doc = fitz.open(pdf_path)
            dois = set()  # Use set to avoid duplicates

            pages_to_scan = min(self.scan_pages, len(doc))

            for page_num in range(pages_to_scan):
                page = doc[page_num]
                text = page.get_text()

                # Find all DOIs in text
                for pattern in self.patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        cleaned = self._clean_doi(match)
                        if cleaned:
                            dois.add(cleaned)

            doc.close()
            return list(dois)

        except Exception as e:
            logger.error(f"Error extracting DOIs from {pdf_path}: {e}")
            return []
