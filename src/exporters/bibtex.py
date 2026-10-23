"""BibTeX format exporter for citation metadata"""

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bwriter import BibTexWriter
from pathlib import Path
from typing import List, Dict
import re
import logging

logger = logging.getLogger(__name__)


class BibTeXExporter:
    """Exports citation metadata to BibTeX format."""

    def __init__(self):
        """Initialize BibTeX exporter."""
        self.entry_types = {
            "journal-article": "article",
            "book": "book",
            "book-chapter": "inbook",
            "proceedings-article": "inproceedings",
            "report": "techreport",
            "dissertation": "phdthesis",
        }

    def export(self, citations: List[Dict], output_path: Path) -> bool:
        """
        Export citations to BibTeX file.

        Args:
            citations: List of citation metadata dictionaries
            output_path: Path to output .bib file

        Returns:
            True if successful, False otherwise
        """
        try:
            db = BibDatabase()
            db.entries = []

            for citation in citations:
                entry = self._create_bibtex_entry(citation)
                if entry:
                    db.entries.append(entry)

            # Write to file
            writer = BibTexWriter()
            writer.indent = "  "
            writer.order_entries_by = ("ID", "author", "title")

            # Generate JabRef group metadata
            jabref_metadata = self._generate_jabref_group_metadata(citations)

            with open(output_path, "w", encoding="utf-8") as bibfile:
                # Write JabRef metadata first
                if jabref_metadata:
                    bibfile.write(jabref_metadata)
                    bibfile.write("\n")
                # Write BibTeX entries
                bibfile.write(writer.write(db))

            logger.info(f"Exported {len(db.entries)} citations to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting to BibTeX: {e}")
            return False

    def _create_bibtex_entry(self, metadata: Dict) -> Dict:
        """
        Create a BibTeX entry from metadata.

        Args:
            metadata: Citation metadata dictionary

        Returns:
            BibTeX entry dictionary
        """
        # Determine entry type
        entry_type = self._get_entry_type(metadata.get("type"))

        # Generate citation key
        citation_key = self._generate_citation_key(metadata)
        
        # Prepend group name to citation key if present
        if metadata.get("group"):
            # Sanitize group name for BibTeX key (replace spaces and special chars)
            group_prefix = metadata["group"].replace(" ", "_").replace("-", "_")
            citation_key = f"{group_prefix}_{citation_key}"

        # Build entry
        entry = {
            "ID": citation_key,
            "ENTRYTYPE": entry_type,
        }

        # Add required and optional fields
        field_mapping = {
            "author": "author",
            "title": "title",
            "year": "year",
            "journal": "journal",
            "volume": "volume",
            "issue": "number",
            "pages": "pages",
            "publisher": "publisher",
            "doi": "doi",
            "url": "url",
            "abstract": "abstract",
            "issn": "issn",
            "isbn": "isbn",
            "group": "groups",
        }

        for meta_field, bib_field in field_mapping.items():
            if metadata.get(meta_field):
                entry[bib_field] = str(metadata[meta_field])

        # Clean up the entry
        entry = self._clean_entry(entry)

        return entry

    def _get_entry_type(self, crossref_type: str) -> str:
        """
        Map CrossRef type to BibTeX entry type.

        Args:
            crossref_type: CrossRef publication type

        Returns:
            BibTeX entry type
        """
        if not crossref_type:
            return "misc"

        return self.entry_types.get(crossref_type, "misc")

    def _generate_citation_key(self, metadata: Dict) -> str:
        """
        Generate a citation key from metadata.

        Format: FirstAuthorLastName_Year_FirstTitleWord

        Args:
            metadata: Citation metadata

        Returns:
            Citation key string
        """
        # Extract first author's last name
        author_part = "Unknown"
        if metadata.get("author"):
            # Get first author
            first_author = metadata["author"].split(" and ")[0].strip()
            # Extract last name (assume last word is last name)
            parts = first_author.split()
            if parts:
                author_part = parts[-1]

        # Extract year
        year_part = metadata.get("year", "YYYY")

        # Extract first significant word from title
        title_part = "NoTitle"
        if metadata.get("title"):
            # Remove common articles and get first significant word
            title_words = metadata["title"].split()
            for word in title_words:
                cleaned_word = re.sub(r"[^a-zA-Z0-9]", "", word)
                if cleaned_word and cleaned_word.lower() not in ["a", "an", "the"]:
                    title_part = cleaned_word
                    break

        # Combine parts
        citation_key = f"{author_part}_{year_part}_{title_part}"

        # Clean the key (remove special characters)
        citation_key = re.sub(r"[^a-zA-Z0-9_]", "", citation_key)

        return citation_key

    def _clean_entry(self, entry: Dict) -> Dict:
        """
        Clean BibTeX entry (remove None values, etc.).

        Args:
            entry: BibTeX entry

        Returns:
            Cleaned entry
        """
        # Remove None values
        cleaned = {k: v for k, v in entry.items() if v is not None}

        # Ensure title has proper capitalization protection
        if "title" in cleaned:
            # BibTeX lowercases titles, so we protect proper nouns with {}
            # For now, we'll just keep the title as-is
            # More sophisticated protection could be added here
            pass

        return cleaned

    def _generate_jabref_group_metadata(self, citations: List[Dict]) -> str:
        """
        Generate JabRef group metadata as @Comment entries.

        JabRef stores groups as special @Comment entries in the BibTeX file.
        This allows JabRef to display native groups in its UI.

        Args:
            citations: List of citation metadata dictionaries

        Returns:
            String containing JabRef group metadata, or empty string if no groups
        """
        # Extract unique group names with their depth from citations
        groups_with_depth = {}
        for citation in citations:
            if citation.get("group"):
                group_name = citation["group"]
                group_depth = citation.get("group_depth", 1)  # Default to 1 if not provided
                # Use group name as key, store depth
                if group_name not in groups_with_depth:
                    groups_with_depth[group_name] = group_depth

        if not groups_with_depth:
            # No groups to export
            return ""

        # Sort groups by depth first, then by name for consistent output
        sorted_groups = sorted(groups_with_depth.items(), key=lambda x: (x[1], x[0]))
        
        # Build the grouping metadata
        grouping_lines = ["0 AllEntriesGroup:;"]
        
        for group_name, depth in sorted_groups:
            # Escape backslashes for BibTeX
            escaped_group = group_name.replace("\\", "\\\\")
            # Use depth as the index (level)
            grouping_lines.append(f"{depth} StaticGroup:{escaped_group}\\;0\\;1\\;0x8a8a8aff\\;\\;\\;;")

        grouping_content = "\n".join(grouping_lines)
        metadata = f"@Comment{{jabref-meta: databaseType:bibtex;}}\n\n@Comment{{jabref-meta: grouping:\n{grouping_content}\n}}"
        return metadata

    def export_single(self, metadata: Dict) -> str:
        """
        Export a single citation to BibTeX string.

        Args:
            metadata: Citation metadata dictionary

        Returns:
            BibTeX formatted string
        """
        db = BibDatabase()
        entry = self._create_bibtex_entry(metadata)
        db.entries = [entry] if entry else []

        writer = BibTexWriter()
        writer.indent = "  "

        # Generate JabRef group metadata for single entry
        jabref_metadata = self._generate_jabref_group_metadata([metadata])

        # Combine metadata and BibTeX entries
        result = writer.write(db)
        if jabref_metadata:
            result = jabref_metadata + "\n" + result

        return result
