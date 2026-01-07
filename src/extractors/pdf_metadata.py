"""Extract embedded metadata from PDF files"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PDFMetadataExtractor:
    """Extracts embedded metadata from PDF files."""

    def __init__(self):
        self.supported_fields = [
            "title",
            "author",
            "subject",
            "creator",
            "producer",
            "creationDate",
            "modDate",
            "keywords",
        ]

    def extract(self, pdf_path: Path) -> Dict[str, Optional[str]]:
        """
        Extract metadata from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary containing metadata fields
        """
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata

            # Clean and normalize metadata
            cleaned_metadata = {
                "title": self._clean_field(metadata.get("title")),
                "author": self._clean_field(metadata.get("author")),
                "subject": self._clean_field(metadata.get("subject")),
                "keywords": self._clean_field(metadata.get("keywords")),
                "creator": self._clean_field(metadata.get("creator")),
                "producer": self._clean_field(metadata.get("producer")),
                "creation_date": self._clean_field(metadata.get("creationDate")),
                "mod_date": self._clean_field(metadata.get("modDate")),
                "doi": None,  # Will be populated by DOIExtractor if found
            }

            # Check for DOI in metadata (some PDFs embed it)
            if metadata.get("subject"):
                # Sometimes DOI is in subject field
                potential_doi = self._extract_doi_from_text(metadata.get("subject"))
                if potential_doi:
                    cleaned_metadata["doi"] = potential_doi

            doc.close()

            logger.info(f"Extracted metadata from {pdf_path.name}")
            return cleaned_metadata

        except Exception as e:
            logger.error(f"Error extracting metadata from {pdf_path}: {e}")
            return self._empty_metadata()

    def _clean_field(self, field: Optional[str]) -> Optional[str]:
        """Clean and normalize a metadata field."""
        if not field:
            return None

        # Remove leading/trailing whitespace
        cleaned = field.strip()

        # Return None if empty after cleaning
        if not cleaned or cleaned.lower() in ["unknown", "none", "null"]:
            return None

        return cleaned

    def _extract_doi_from_text(self, text: str) -> Optional[str]:
        """Extract DOI from text if present."""
        import re

        doi_pattern = r"10\.\d{4,9}/[-._;()/:A-Z0-9]+"
        match = re.search(doi_pattern, text, re.IGNORECASE)
        return match.group(0) if match else None

    def _empty_metadata(self) -> Dict[str, Optional[str]]:
        """Return empty metadata dictionary."""
        return {
            "title": None,
            "author": None,
            "subject": None,
            "keywords": None,
            "creator": None,
            "producer": None,
            "creation_date": None,
            "mod_date": None,
            "doi": None,
        }

    def has_useful_metadata(self, metadata: Dict[str, Optional[str]]) -> bool:
        """
        Check if metadata contains useful information.

        Returns True if at least title or author is present.
        """
        return bool(metadata.get("title") or metadata.get("author"))
