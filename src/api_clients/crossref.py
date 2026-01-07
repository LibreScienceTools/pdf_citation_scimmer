"""CrossRef API client for fetching citation metadata from DOI"""

from habanero import Crossref
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CrossRefClient:
    """Client for CrossRef API to fetch citation metadata."""

    def __init__(self, email: Optional[str] = None):
        """
        Initialize CrossRef client.

        Args:
            email: Email for polite pool (faster API access)
        """
        self.client = Crossref(mailto=email) if email else Crossref()

    def get_metadata(self, doi: str) -> Optional[Dict]:
        """
        Fetch metadata for a DOI from CrossRef.

        Args:
            doi: Digital Object Identifier

        Returns:
            Dictionary with citation metadata, or None if not found
        """
        try:
            logger.info(f"Querying CrossRef for DOI: {doi}")
            result = self.client.works(ids=doi)

            if not result or "message" not in result:
                logger.warning(f"No metadata found for DOI: {doi}")
                return None

            message = result["message"]

            # Extract and normalize metadata
            metadata = self._parse_crossref_response(message)
            metadata["doi"] = doi

            logger.info(f"Successfully retrieved metadata for DOI: {doi}")
            return metadata

        except Exception as e:
            logger.error(f"Error fetching metadata for DOI {doi}: {e}")
            return None

    def _parse_crossref_response(self, message: Dict) -> Dict:
        """
        Parse CrossRef API response into normalized metadata.

        Args:
            message: CrossRef API message object

        Returns:
            Normalized metadata dictionary
        """
        metadata = {}

        # Title
        if "title" in message and message["title"]:
            metadata["title"] = message["title"][0]
        else:
            metadata["title"] = None

        # Authors
        if "author" in message:
            authors = []
            for author in message["author"]:
                given = author.get("given", "")
                family = author.get("family", "")
                if family:
                    full_name = f"{given} {family}".strip()
                    authors.append(full_name)
            metadata["author"] = " and ".join(authors) if authors else None
        else:
            metadata["author"] = None

        # Publication year
        if "published-print" in message:
            date_parts = message["published-print"].get("date-parts", [[]])[0]
            metadata["year"] = str(date_parts[0]) if date_parts else None
        elif "published-online" in message:
            date_parts = message["published-online"].get("date-parts", [[]])[0]
            metadata["year"] = str(date_parts[0]) if date_parts else None
        elif "issued" in message:
            date_parts = message["issued"].get("date-parts", [[]])[0]
            metadata["year"] = str(date_parts[0]) if date_parts else None
        else:
            metadata["year"] = None

        # Journal/Container title
        if "container-title" in message and message["container-title"]:
            metadata["journal"] = message["container-title"][0]
        else:
            metadata["journal"] = None

        # Volume
        metadata["volume"] = message.get("volume")

        # Issue
        metadata["issue"] = message.get("issue")

        # Pages
        metadata["pages"] = message.get("page")

        # Publisher
        metadata["publisher"] = message.get("publisher")

        # Type (article, book, etc.)
        metadata["type"] = message.get("type")

        # Abstract
        metadata["abstract"] = message.get("abstract")

        # ISSN
        if "ISSN" in message and message["ISSN"]:
            metadata["issn"] = message["ISSN"][0]
        else:
            metadata["issn"] = None

        # ISBN (for books)
        if "ISBN" in message and message["ISBN"]:
            metadata["isbn"] = message["ISBN"][0]
        else:
            metadata["isbn"] = None

        # URL
        metadata["url"] = message.get("URL")

        return metadata

    def search_by_title(self, title: str, limit: int = 5) -> list:
        """
        Search CrossRef by title (useful when DOI is not available).

        Args:
            title: Publication title
            limit: Maximum number of results

        Returns:
            List of potential matches
        """
        try:
            logger.info(f"Searching CrossRef for title: {title}")
            results = self.client.works(query=title, limit=limit)

            if not results or "message" not in results:
                return []

            items = results["message"].get("items", [])
            matches = []

            for item in items:
                metadata = self._parse_crossref_response(item)
                if "DOI" in item:
                    metadata["doi"] = item["DOI"]
                matches.append(metadata)

            return matches

        except Exception as e:
            logger.error(f"Error searching CrossRef for title '{title}': {e}")
            return []
