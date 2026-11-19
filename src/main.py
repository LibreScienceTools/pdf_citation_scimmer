"""Main CLI interface for PDF Citation Extractor"""

import click
import yaml
import logging
import datetime
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from tqdm import tqdm

from src.extractors import PDFMetadataExtractor, DOIExtractor, GROBIDClient
from src.api_clients import CrossRefClient
from src.exporters import BibTeXExporter
from src.trackers import FileTracker

# Import bibtexparser for custom parser
import bibtexparser
from bibtexparser.bparser import BibTexParser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pdf_citation_extractor.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def _create_bibtex_parser():
    """
    Create a BibTexParser that accepts non-standard entry types (for biblatex support).
    
    Returns:
        BibTexParser configured to accept all entry types
    """
    return BibTexParser(ignore_nonstandard_types=False)


class CitationExtractor:
    """Main citation extraction orchestrator."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the citation extractor.

        Args:
            config_path: Path to config.yaml file
        """
        self.config = self._load_config(config_path)

        # Initialize components
        self.pdf_extractor = PDFMetadataExtractor()
        self.doi_extractor = DOIExtractor(
            scan_pages=self.config["extraction"]["doi_scan_pages"]
        )
        self.crossref_client = CrossRefClient(
            email=self.config.get("crossref_email") or None
        )
        self.bibtex_exporter = BibTeXExporter()

        # Initialize GROBID client if enabled in strategy
        strategies = self.config.get("extraction", {}).get("strategy", [])
        if "grobid" in strategies:
            grobid_url = self.config.get("grobid_url", "http://localhost:8070")
            self.grobid_client = GROBIDClient(grobid_url=grobid_url)
        else:
            self.grobid_client = None
        
        # Track failed files for logging
        self._last_failed_files = []
        
        # File tracker - will be initialized with output_dir when needed
        self.file_tracker: Optional[FileTracker] = None

    def _get_file_tracker(self, output_dir: Path) -> FileTracker:
        """
        Get or create file tracker for a specific output directory.
        
        Args:
            output_dir: Directory where the bib-file will be stored
            
        Returns:
            FileTracker instance for the specified directory
        """
        if self.file_tracker is None or self.file_tracker.output_dir != output_dir:
            self.file_tracker = FileTracker(output_dir=output_dir)
        return self.file_tracker

    def _ensure_unique_citation_key(self, base_key: str, existing_keys: set, new_keys: set) -> str:
        """
        Ensure a citation key is unique by appending 'a', 'b', etc. if needed.
        
        Args:
            base_key: The base citation key (e.g., "Author_2023")
            existing_keys: Set of keys that already exist in the file
            new_keys: Set of keys already added in this batch
            
        Returns:
            Unique citation key
        """
        # Check if base key is available
        if base_key not in existing_keys and base_key not in new_keys:
            new_keys.add(base_key)
            return base_key
        
        # Find next available suffix
        suffix = 'a'
        while True:
            candidate_key = f"{base_key}{suffix}"
            if candidate_key not in existing_keys and candidate_key not in new_keys:
                new_keys.add(candidate_key)
                return candidate_key
            # Increment suffix: a, b, c, ... z, aa, ab, etc.
            if suffix == 'z':
                suffix = 'aa'
            else:
                suffix = chr(ord(suffix) + 1)

    def _generate_fallback_citation_key(self, pdf_path: Path) -> str:
        """
        Generate a fallback citation key from PDF path when metadata extraction fails.
        This helps identify the file in JabRef later.
        
        Format: {CleanFileStem} (since no author/year available)
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            A valid BibTeX citation key
        """
        # Get the stem (filename without extension)
        stem = pdf_path.stem
        
        # Clean for BibTeX (remove special chars, replace spaces with nothing)
        clean_stem = re.sub(r'[^a-zA-Z0-9]', '', stem)
        clean_stem = clean_stem.strip()
        
        # Build citation key
        citation_key = clean_stem if clean_stem else "UNKNOWN"
        
        # Ensure it's not empty
        if not citation_key:
            citation_key = "UNKNOWN"
        
        return citation_key

    def _is_high_quality_metadata(self, metadata: Dict) -> bool:
        """
        Check if extracted metadata meets basic quality standards.
        Returns False if metadata is too low quality to be useful.
        
        Low quality metadata includes:
        - Missing or generic titles ("Misc", "Untitled", "Unknown")
        - Missing or generic authors ("Unknown", "Anonymous")
        - Invalid years ("YYYY", "Unknown", "0000")
        - PII numbers as DOI (S1234-5678(99)12345-6 format)
        - Missing critical fields
        
        Args:
            metadata: Citation metadata dictionary
            
        Returns:
            True if metadata is high quality, False otherwise
        """
        # Must have at least title or author
        if not metadata.get("title") and not metadata.get("author"):
            logger.debug("Low quality: Missing both title and author")
            return False

        # Check for bad titles (only if title exists)
        if "title" in metadata:
            title = str(metadata["title"]).strip().lower()
            # Reject empty titles (after stripping)
            if not title:
                logger.debug("Low quality: Empty title")
                return False
            bad_titles = ["misc", "untitled", "document", "unknown", "no title", "title", 
                         "article", "paper", "publication"]
            if title in bad_titles:
                logger.debug(f"Low quality: Generic title '{title}'")
                return False

        # Check for bad authors (only if author exists)
        if "author" in metadata:
            author = str(metadata["author"]).strip().lower()
            # Reject empty authors (after stripping)
            if not author:
                logger.debug("Low quality: Empty author")
                return False
            bad_authors = ["unknown", "anonymous", "none", "no author", "author"]
            if author in bad_authors:
                logger.debug(f"Low quality: Generic author '{author}'")
                return False

        # Check for bad years (only if year exists)
        if "year" in metadata:
            year = str(metadata["year"]).strip()
            bad_years = ["YYYY", "Unknown", "0000", "0", "1900"]
            if year in bad_years:
                logger.debug(f"Low quality: Bad year '{year}'")
                return False
            
            # Check for valid year range (if it's a number)
            try:
                year_num = int(year)
                if year_num < 1900 or year_num > 2100:
                    logger.debug(f"Low quality: Year out of range '{year}'")
                    return False
            except ValueError:
                # If year is not a number, it might be a string like "2023-2024"
                # Only reject if it's in our bad_years list
                pass

        # Check for PII numbers as DOI (S1234-5678(99)12345-6 format)
        doi = str(metadata.get("doi", "")).strip()
        if doi:
            # PII pattern: S1234-5678(99)12345-6
            if re.match(r'^S\d{4}-\d{4}\(\d{2}\)\d+-\d+$', doi):
                logger.debug(f"Low quality: PII number as DOI '{doi}'")
                return False

        # Check for bad journals (if present)
        journal = str(metadata.get("journal", "")).strip().lower()
        if journal:
            bad_journals = ["unknown", "misc", "none", "no journal", "journal", ""]
            if journal in bad_journals:
                logger.debug(f"Low quality: Generic journal '{journal}'")
                return False

        # If all checks passed, it's high quality
        return True

    def _write_failed_files_log(self, failed_files: List[Dict], output_path: Path) -> None:
        """
        Write a detailed log file of failed extractions.
        Emphasizes that these files MUST be added manually to JabRef.
        
        Args:
            failed_files: List of failure dictionaries with keys: path, relative_path, group, error, would_be_key
            output_path: Path to the output .bib file (we write log in same directory)
        """
        if not failed_files:
            return
        
        # Determine log file location
        if output_path.parent != Path("."):
            log_dir = output_path.parent
        else:
            log_dir = Path(self.config.get("output_directory", "./output"))
        
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "failed_extractions.log"
        
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("# " + "="*70 + "\n")
            f.write("# PDF CITATION EXTRACTOR - FAILED FILES REPORT\n")
            f.write("# " + "="*70 + "\n\n")
            
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Output file: {output_path}\n\n")
            
            f.write("="*70 + "\n")
            f.write("IMPORTANT: These files could NOT be processed automatically.\n")
            f.write("You MUST add them manually to JabRef using the information below.\n")
            f.write("="*70 + "\n\n")
            
            f.write("HOW TO ADD MANUALLY:\n")
            f.write("1. Open your .bib file in JabRef\n")
            f.write("2. For each file below, create a new entry\n")
            f.write("3. Use the 'Suggested BibTeX Key' as the entry's citation key\n")
            f.write("4. Add the entry to the specified 'Group'\n")
            f.write("5. Fill in the metadata manually (title, author, year, etc.)\n")
            f.write("   - You can find metadata by searching for the DOI or title online\n")
            f.write("   - Or extract it manually from the PDF file\n\n")
            
            f.write(f"Total files that need manual addition: {len(failed_files)}\n\n")
            
            f.write("-"*70 + "\n")
            f.write("FAILED FILES:\n")
            f.write("-"*70 + "\n\n")
            
            for i, failure in enumerate(failed_files, 1):
                f.write(f"File #{i}: {failure['relative_path']}\n")
                f.write(f"  Group: {failure['group']}\n")
                f.write(f"  Suggested BibTeX Key: {failure['would_be_key']}\n")
                f.write(f"  Full Path: {failure['path']}\n")
                f.write(f"  Reason: {failure['error']}\n")
                f.write(f"\n")
                f.write(f"  ACTION REQUIRED: Add this file manually to JabRef!\n")
                f.write(f"  - BibTeX key: {failure['would_be_key']}\n")
                f.write(f"  - Group: {failure['group']}\n")
                f.write(f"\n")
            
            f.write("-"*70 + "\n")
            f.write("NOTES:\n")
            f.write("- Once added manually, these entries will be PRESERVED in future runs\n")
            f.write("  (the scimmer recognizes manually added entries by their lack of pdf_uuid field)\n")
            f.write("- Failed files are typically PDFs without embedded metadata or DOI\n")
            f.write("- You can try to extract metadata manually or search for the paper online\n")
            f.write("="*70 + "\n")

    def _format_failed_files_cli(self, failed_files: List[Dict]) -> str:
        """
        Format failed files for CLI output.
        
        Args:
            failed_files: List of failure dictionaries with keys: path, relative_path, group, error, would_be_key
            
        Returns:
            Formatted string for CLI output
        """
        if not failed_files:
            return ""
        
        lines = []
        lines.append("")
        lines.append(f"! {len(failed_files)} files failed extraction:")
        lines.append("")
        
        for i, failure in enumerate(failed_files, 1):
            lines.append(f"   [{i}] {failure['relative_path']}")
            lines.append(f"       Group: {failure['group']}")
            lines.append(f"       Error: {failure['error']}")
            lines.append(f"       Suggested key: {failure['would_be_key']}")
        
        lines.append("")
        lines.append("   These files need manual addition to JabRef.")
        lines.append("   See failed_extractions.log for detailed instructions.")
        lines.append("")
        
        return "\n".join(lines)

    def _load_config(self, config_path: Optional[Path]) -> Dict:
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.warning(f"Could not load config file: {e}. Using defaults.")
            return self._default_config()

    def _default_config(self) -> Dict:
        """Return default configuration."""
        return {
            "crossref_email": None,
            "default_output_format": "bibtex",
            "output_directory": "./output",
            "extraction": {"doi_scan_pages": 3, "strategy": ["embedded_metadata", "doi_lookup"]},
        }

    def process_pdf(self, pdf_path: Path) -> Optional[Dict]:
        """
        Process a single PDF file and extract citation metadata.
        
        NEW: Includes quality assessment - low quality metadata is treated as failure.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Citation metadata dictionary, failure dictionary, or None if extraction failed
        """
        logger.info(f"Processing: {pdf_path.name}")

        # Strategy 1: Try embedded metadata first
        metadata = self.pdf_extractor.extract(pdf_path)

        # Strategy 2: Extract DOI and query CrossRef
        doi = metadata.get("doi") or self.doi_extractor.extract(pdf_path)

        if doi:
            logger.info(f"Found DOI: {doi}")
            crossref_metadata = self.crossref_client.get_metadata(doi)

            if crossref_metadata:
                # Merge metadata (CrossRef takes precedence)
                metadata.update(crossref_metadata)
                metadata["source"] = "crossref"
                metadata["pdf_file"] = pdf_path.name
                
                # NEW: Check metadata quality
                if not self._is_high_quality_metadata(metadata):
                    fallback_key = self._generate_fallback_citation_key(pdf_path)
                    logger.warning(f"Low quality metadata from CrossRef for {pdf_path.name}")
                    return {
                        "_failed": True,
                        "pdf_path": str(pdf_path),
                        "error": "Low quality metadata from CrossRef (suspect or incomplete data)",
                        "would_be_key": fallback_key
                    }
                
                return metadata

        # If we have useful embedded metadata, use it
        if self.pdf_extractor.has_useful_metadata(metadata):
            logger.info(f"Using embedded metadata for {pdf_path.name}")
            metadata["source"] = "embedded"
            metadata["pdf_file"] = pdf_path.name
            
            # NEW: Check metadata quality for embedded metadata
            if not self._is_high_quality_metadata(metadata):
                fallback_key = self._generate_fallback_citation_key(pdf_path)
                logger.warning(f"Low quality embedded metadata for {pdf_path.name}")
                return {
                    "_failed": True,
                    "pdf_path": str(pdf_path),
                    "error": "Low quality embedded metadata (suspect or incomplete data)",
                    "would_be_key": fallback_key
                }
            
            return metadata

        # Strategy 3: GROBID fallback for PDFs without DOI or embedded metadata
        if self.grobid_client and self.grobid_client.available:
            logger.info(f"Trying GROBID extraction for {pdf_path.name}")
            grobid_metadata = self.grobid_client.process(pdf_path)
            if grobid_metadata:
                grobid_metadata["source"] = "grobid"
                grobid_metadata["pdf_file"] = pdf_path.name
                
                # NEW: Check metadata quality for GROBID
                if not self._is_high_quality_metadata(grobid_metadata):
                    fallback_key = self._generate_fallback_citation_key(pdf_path)
                    logger.warning(f"Low quality metadata from GROBID for {pdf_path.name}")
                    return {
                        "_failed": True,
                        "pdf_path": str(pdf_path),
                        "error": "Low quality metadata from GROBID (suspect or incomplete data)",
                        "would_be_key": fallback_key
                    }
                
                return grobid_metadata
        
        # All strategies failed - return failure info with fallback citation key
        fallback_key = self._generate_fallback_citation_key(pdf_path)
        logger.warning(f"Could not extract sufficient metadata from {pdf_path.name}")
        return {
            "_failed": True,
            "pdf_path": str(pdf_path),
            "error": "No metadata extracted from any source (no DOI, no embedded metadata, GROBID unavailable)",
            "would_be_key": fallback_key
        }

    def _process_pdf_with_tracking(self, pdf_path: Path, group_name: str,
                                   project_root: Path, file_tracker: FileTracker) -> Optional[Dict]:
        """
        Process a single PDF file with file tracking.
        
        This wraps process_pdf and registers the file with the tracker.
        
        Args:
            pdf_path: Path to the PDF file
            group_name: Group name for the file
            project_root: Root directory for relative path calculation
            file_tracker: FileTracker instance
            
        Returns:
            Metadata dictionary with UUID, or the failure dict from process_pdf
        """
        # Process the PDF normally
        result = self.process_pdf(pdf_path)
        
        if result and not result.get("_failed"):
            # Generate citation key for tracking
            citation_key = result.get("ID")
            if not citation_key:
                citation_key = self._generate_fallback_citation_key(pdf_path)
            
            # Register with tracker
            file_uuid, is_new = file_tracker.register_file(
                pdf_path,
                citation_key,
                project_root=project_root,
                metadata={
                    "group": group_name,
                    "source": result.get("source", "unknown")
                }
            )
            
            # Add UUID to metadata
            result["pdf_uuid"] = file_uuid
            
            if is_new:
                logger.debug(f"Tracked new file: {pdf_path.name} -> UUID: {file_uuid[:8]}...")
        
        return result

    def process_directory(self, directory: Path, output_path: Optional[Path] = None) -> Dict[str, List[Dict]]:
        """
        Process all PDF files in a directory and its subdirectories.
        Files are grouped by their immediate parent directory name.
        Files in the root directory are grouped under "General".

        Args:
            directory: Directory to search for PDF files
            output_path: Optional path to the output bib-file. If provided, used to
                        initialize the file tracker in the same directory.

        Returns:
            Dictionary mapping group names to lists of citation metadata
        """
        # Find all PDF files recursively
        pdf_files = list(directory.rglob("*.pdf"))

        if not pdf_files:
            logger.warning(f"No PDF files found in {directory}")
            return {"General": []}

        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")

        # Determine output directory for tracker
        if output_path:
            output_dir = output_path.parent
        else:
            output_dir = Path(self.config.get("output_directory", "./output"))
        
        # Initialize file tracker for this output directory
        file_tracker = self._get_file_tracker(output_dir)
        
        # Group citations by parent directory
        grouped_citations: Dict[str, List[Dict]] = {}
        failed_files = []  # List of dicts with failure details
        
        # Clear previous failed files
        self._last_failed_files = []

        # Process each PDF with progress bar
        for pdf_path in tqdm(pdf_files, desc="Processing PDFs", unit="file"):
            try:
                # Get path relative to the root directory
                relative_path = pdf_path.relative_to(directory)
                
                # Determine group name: use parent directory name, or "General" for root
                if relative_path.parent == Path("."):
                    group_name = "General"
                else:
                    group_name = relative_path.parent.name
                
                # Process the PDF and register with tracker
                result = self._process_pdf_with_tracking(
                    pdf_path, group_name, directory, file_tracker
                )
                
                if result and not result.get("_failed"):
                    # Success - add group information to metadata
                    metadata = result
                    metadata["group"] = group_name
                    metadata["group_path"] = str(relative_path.parent)
                    
                    # Add to appropriate group
                    if group_name not in grouped_citations:
                        grouped_citations[group_name] = []
                    grouped_citations[group_name].append(metadata)
                elif result and result.get("_failed"):
                    # Failed with details from process_pdf
                    failure = {
                        "path": str(pdf_path),
                        "relative_path": str(relative_path),
                        "group": group_name,
                        "error": result.get("error", "Unknown error"),
                        "would_be_key": result.get("would_be_key", "UNKNOWN")
                    }
                    failed_files.append(failure)
                    self._last_failed_files.append(failure)
                    logger.warning(f"Failed: {pdf_path.name} - {failure['error']}")
                else:
                    # Should not happen, but handle it
                    failure = {
                        "path": str(pdf_path),
                        "relative_path": str(relative_path),
                        "group": group_name,
                        "error": "Unexpected: process_pdf returned None",
                        "would_be_key": self._generate_fallback_citation_key(pdf_path)
                    }
                    failed_files.append(failure)
                    self._last_failed_files.append(failure)
                    logger.warning(f"Failed: {pdf_path.name} - Unexpected error")
                    
            except Exception as e:
                # Unexpected error during processing
                relative_path = pdf_path.relative_to(directory)
                group_name = "General" if relative_path.parent == Path(".") else relative_path.parent.name
                failure = {
                    "path": str(pdf_path),
                    "relative_path": str(relative_path),
                    "group": group_name,
                    "error": str(e),
                    "would_be_key": self._generate_fallback_citation_key(pdf_path)
                }
                failed_files.append(failure)
                self._last_failed_files.append(failure)
                logger.error(f"Error processing {pdf_path.name}: {e}")

        # Cleanup missing files from tracker
        cleaned = file_tracker.cleanup_missing_files()
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} missing file entries from tracker")

        # Summary
        total_success = sum(len(c) for c in grouped_citations.values())
        logger.info(
            f"\nProcessing complete: {total_success} successful, {len(failed_files)} failed"
        )
        if failed_files:
            failed_paths = [f["relative_path"] for f in failed_files]
            logger.warning(f"Failed files: {', '.join(failed_paths[:5])}{'...' if len(failed_paths) > 5 else ''}")

        # If we have no citations at all, return empty "General" group
        if not grouped_citations:
            return {"General": []}

        return grouped_citations

    def _export_to_bibtex(self, citations: Dict[str, List[Dict]], output_path: Path, overwrite: bool = False) -> bool:
        """
        Export grouped citations to BibTeX file with group comments.
        By default, merges with existing file to avoid overwriting entries.
        
        IMPORTANT: Manual entries (without pdf_uuid) are ALWAYS preserved.
        Auto entries (with pdf_uuid) are managed by the scimmer.

        Args:
            citations: Dictionary mapping group names to lists of citation metadata
            output_path: Path to output .bib file
            overwrite: If True, overwrite existing file. If False (default), merge with existing.

        Returns:
            True if successful, False otherwise
        """
        import bibtexparser
        from bibtexparser.bibdatabase import BibDatabase
        from bibtexparser.bwriter import BibTexWriter

        try:
            # Step 1: Read existing file if it exists and we're not overwriting
            existing_entries = {}  # Dict[citation_key, entry_dict]
            existing_content = ""
            parse_failed = False  # Track if parsing failed
            
            # NEW: Clearly separate manual entries (no UUID) from auto entries (with UUID)
            manual_entries = {}  # Entries without pdf_uuid - ALWAYS preserved
            auto_entries = {}    # Entries with pdf_uuid - managed by scimmer
            
            if not overwrite and output_path.exists():
                with open(output_path, "r", encoding="utf-8") as f:
                    existing_content = f.read()
                
                # NEW: Extract original entry types (preserve case for biblatex)
                import re
                entry_type_map = {}  # entry_id -> original entry type
                entry_pattern = r'@([a-zA-Z]+)\s*\{([^,\s]+)'
                for match in re.finditer(entry_pattern, existing_content):
                    entry_type = match.group(1)
                    entry_id = match.group(2).strip()
                    entry_type_map[entry_id] = entry_type
                
                # Parse existing BibTeX file (support biblatex entry types)
                try:
                    parser = _create_bibtex_parser()
                    existing_db = bibtexparser.loads(existing_content, parser=parser)
                    existing_entries = {entry["ID"]: entry for entry in existing_db.entries}
                    
                    # NEW: Fix entry types to preserve original case
                    for entry_id, entry in existing_entries.items():
                        if entry_id in entry_type_map:
                            original_type = entry_type_map[entry_id]
                            entry["ENTRYTYPE"] = original_type
                    
                    # NEW: Explicitly separate manual vs auto entries
                    for entry_id, entry in existing_entries.items():
                        if "pdf_uuid" in entry:
                            auto_entries[entry_id] = entry
                            logger.debug(f"Found auto entry with UUID: {entry_id}")
                        else:
                            manual_entries[entry_id] = entry
                            logger.debug(f"Found manual entry (no UUID): {entry_id}")
                    
                    # Check if file has content but 0 entries parsed (likely malformed)
                    if existing_content.strip() and not existing_entries:
                        logger.warning(f"BibTeX file appears to have content but parsed 0 entries (possible malformed BibTeX)")
                        logger.warning(f"Preserving original content to avoid data loss")
                        parse_failed = True
                    else:
                        logger.info(f"Found {len(auto_entries)} auto entries and {len(manual_entries)} manual entries in {output_path}")
                except Exception as e:
                    logger.error(f"Could not parse existing BibTeX file: {e}")
                    logger.error(f"Preserving original content to avoid data loss")
                    parse_failed = True
            
            # NEW: If we have existing entries but parsing failed, try to preserve them
            if parse_failed and existing_entries:
                # If we have entries from a previous successful parse, use them
                for entry_id, entry in existing_entries.items():
                    if "pdf_uuid" in entry:
                        auto_entries[entry_id] = entry
                    else:
                        manual_entries[entry_id] = entry
                logger.info(f"Recovered {len(auto_entries) + len(manual_entries)} entries after parse failure")
            
            # Step 2: Build all entries (new + existing)
            # Create a mapping of UUID to entry for duplicate detection (only for auto entries)
            uuid_to_entry = {}
            for entry_id, entry in auto_entries.items():
                if "pdf_uuid" in entry:
                    uuid_to_entry[entry["pdf_uuid"]] = entry_id
                    logger.debug(f"Tracked auto entry with UUID {entry['pdf_uuid'][:8]}... (key: {entry_id})")
            
            # Collect all auto entry keys for duplicate detection
            existing_auto_keys = set(auto_entries.keys())
            # Track keys we're adding to detect duplicates among new entries
            new_keys_added = set()
            
            # NEW: Start with manual entries - they are ALWAYS preserved
            all_entries = dict(manual_entries)
            
            # Add existing auto entries
            all_entries.update(auto_entries)
            
            new_count = 0
            updated_count = 0
            
            for group_name, group_citations in citations.items():
                for citation in group_citations:
                    # Generate base citation key first
                    base_entry = self.bibtex_exporter._create_bibtex_entry(citation)
                    if not base_entry:
                        continue
                    
                    # Get or generate a unique citation key
                    entry_id = self._ensure_unique_citation_key(
                        base_entry["ID"], 
                        existing_auto_keys, 
                        new_keys_added
                    )
                    
                    # Create final entry with unique key
                    entry = self.bibtex_exporter._create_bibtex_entry(citation)
                    entry["ID"] = entry_id
                    
                    entry_uuid = entry.get("pdf_uuid")
                    
                    # Only process entries that have UUIDs (from successfully tracked files)
                    if not entry_uuid:
                        logger.warning(f"Entry {entry_id} has no UUID, skipping (should not happen)")
                        continue
                    
                    # Check if this UUID already exists (file was already processed)
                    if entry_uuid in uuid_to_entry:
                        # Same file, different citation key - keep the existing entry
                        # but ensure it has the UUID
                        existing_entry_id = uuid_to_entry[entry_uuid]
                        existing_entry = all_entries[existing_entry_id]
                        
                        # Ensure the existing entry has the UUID
                        if "pdf_uuid" not in existing_entry:
                            existing_entry["pdf_uuid"] = entry_uuid
                        
                        # Keep the existing citation key (user may have customized it in JabRef)
                        # Don't overwrite it with the generated one
                        # But update other metadata fields
                        for key, value in entry.items():
                            if key != "ID" and key != "pdf_uuid":
                                # Only update if the field is missing or empty in existing
                                if key not in existing_entry or not existing_entry[key]:
                                    existing_entry[key] = value
                        
                        updated_count += 1
                        logger.info(f"Recognized existing auto entry via UUID {entry_uuid[:8]}... (keeping JabRef citation key: {existing_entry_id})")
                        
                    elif entry_id in all_entries:
                        # Entry already exists by citation key
                        existing_entry = all_entries[entry_id]
                        if "pdf_uuid" not in existing_entry and entry_uuid:
                            existing_entry["pdf_uuid"] = entry_uuid
                            updated_count += 1
                            logger.debug(f"Updated entry {entry_id} with UUID")
                        # Keep the existing entry
                        logger.debug(f"Entry already exists: {entry_id}, keeping existing")
                    else:
                        # New auto entry
                        all_entries[entry_id] = entry
                        new_count += 1
                        
                        # Track this UUID
                        uuid_to_entry[entry_uuid] = entry_id
                        existing_auto_keys.add(entry_id)
            
            # Step 3: Generate JabRef metadata
            all_citation_data = []
            for group_name, group_citations in citations.items():
                all_citation_data.extend(group_citations)
            
            jabref_metadata = self.bibtex_exporter._generate_jabref_group_metadata(all_citation_data)
            
            # If we kept existing entries, try to preserve their JabRef metadata
            if existing_content and not overwrite:
                existing_jabref = self.bibtex_exporter._extract_existing_jabref_metadata(existing_content)
                if existing_jabref and not jabref_metadata:
                    jabref_metadata = existing_jabref
            
            # Step 4: Write to file - Option 1: Write all entries together
            writer = BibTexWriter()
            writer.indent = "  "
            writer.order_entries_by = ("ID", "author", "title")
            
            # Build final database with ALL entries (existing + new)
            db = BibDatabase()
            db.entries = list(all_entries.values())
            
            # Write everything to file
            with open(output_path, "w", encoding="utf-8") as bibfile:
                # If parsing failed, preserve original content
                if parse_failed:
                    bibfile.write(existing_content)
                    bibfile.write("\n\n")
                    # Add group comments for new citations
                    for group_name, group_citations in citations.items():
                        if group_citations:
                            bibfile.write(f"% ===== Group: {group_name} =====\n\n")
                    # Write new entries
                    bibfile.write(writer.write(db))
                else:
                    # Normal case: write JabRef metadata first
                    if jabref_metadata:
                        bibfile.write(jabref_metadata)
                        bibfile.write("\n")
                    
                    # Add group comments for the new citation groups
                    for group_name, group_citations in citations.items():
                        if group_citations:  # Only add group header if there are citations
                            bibfile.write(f"% ===== Group: {group_name} =====\n\n")
                    
                    # Write all entries (existing + new)
                    bibfile.write(writer.write(db))

            if parse_failed:
                logger.warning(f"Exported to {output_path} (preserved original content + {new_count} new entries)")
            else:
                logger.info(f"Exported to {output_path} ({new_count} new entries, {updated_count} updated, {len(all_entries) - new_count - updated_count} existing preserved)")
            return True

        except Exception as e:
            logger.error(f"Error exporting to BibTeX: {e}")
            return False

    def export_citations(
        self, citations: Dict[str, List[Dict]], output_path: Path, 
        format: str = "bibtex", overwrite: bool = False
    ) -> bool:
        """
        Export citations to file.

        Args:
            citations: Dictionary mapping group names to lists of citation metadata
            output_path: Output file path
            format: Export format (currently only 'bibtex' supported)
            overwrite: If True, overwrite existing file. If False (default), merge with existing.

        Returns:
            True if successful
        """
        if format == "bibtex":
            return self._export_to_bibtex(citations, output_path, overwrite)
        else:
            logger.error(f"Unsupported export format: {format}")
            return False


@click.command()
@click.option(
    "--dir",
    "-d",
    "directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Directory containing PDF files to process",
)
@click.option(
    "--pdf",
    "-p",
    "pdf_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Single PDF file to process",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=click.Path(path_type=Path),
    default="citations.bib",
    help="Output file path (default: citations.bib)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["bibtex"], case_sensitive=False),
    default="bibtex",
    help="Output format (default: bibtex)",
)
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to config.yaml file",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing .bib file instead of merging (default: merge with existing)",
)
@click.option(
    "--show-tracker",
    is_flag=True,
    default=False,
    help="Show all tracked files for the output directory and exit",
)
@click.option(
    "--cleanup-tracker",
    is_flag=True,
    default=False,
    help="Clean up missing file entries from the tracker and exit",
)
def main(
    directory: Optional[Path],
    pdf_file: Optional[Path],
    output_path: Path,
    output_format: str,
    config_path: Optional[Path],
    verbose: bool,
    overwrite: bool,
    show_tracker: bool = False,
    cleanup_tracker: bool = False,
):
    """
    PDF Citation Metadata Extractor

    Extracts citation metadata from PDF files and exports to reference management formats.

    Examples:

      # Process a directory of PDFs
      python -m src.main --dir ./papers --output references.bib

      # Process a single PDF
      python -m src.main --pdf paper.pdf --output citation.bib

      # Use custom config
      python -m src.main --dir ./papers --config my_config.yaml
    """
    # Set logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle tracker-only operations
    if show_tracker or cleanup_tracker:
        from src.trackers import FileTracker
        
        # Determine output directory
        output_dir = output_path.parent if output_path else Path.cwd()
        tracker = FileTracker(output_dir=output_dir)
        
        if show_tracker:
            entries = tracker.list_all_entries()
            click.echo(f"\nTracked files in {output_dir}:\n")
            click.echo(f"Total: {len(entries)} files\n")
            
            for entry in entries:
                click.echo(f"UUID: {entry.uuid[:8]}...")
                display_path = entry.relative_path if entry.relative_path else entry.file_path
                click.echo(f"  Path: {display_path}")
                click.echo(f"  Citation Key: {entry.citation_key}")
                click.echo(f"  First Seen: {entry.first_seen}")
                click.echo(f"  Last Seen: {entry.last_seen}")
                click.echo()
            return
        
        if cleanup_tracker:
            removed = tracker.cleanup_missing_files()
            click.echo(f"\nCleaned up {removed} missing file entries from tracker")
            return

    # Validate input
    if not directory and not pdf_file:
        click.echo("Error: Must specify either --dir or --pdf", err=True)
        raise click.Abort()

    if directory and pdf_file:
        click.echo("Error: Cannot specify both --dir and --pdf", err=True)
        raise click.Abort()

    # Initialize extractor
    click.echo("Initializing PDF Citation Extractor...")
    extractor = CitationExtractor(config_path)

    # Process PDFs
    failed_files = []  # Track failed files for single PDF processing
    
    if pdf_file:
        click.echo(f"\nProcessing single PDF: {pdf_file.name}")
        
        # Initialize tracker for single file processing
        output_dir = output_path.parent if output_path else Path.cwd()
        file_tracker = extractor._get_file_tracker(output_dir)
        
        # Process with tracking
        result = extractor._process_pdf_with_tracking(
            pdf_file, 
            "General", 
            pdf_file.parent,  # Use parent as project root for relative path
            file_tracker
        )
        
        # Cleanup tracker
        file_tracker.cleanup_missing_files() #issue1: maybe filetracker deletes manual entries here
        
        if result and not result.get("_failed"):
            # Success
            metadata = result
            # Wrap single citation in "General" group
            citations = {"General": [metadata]}
        elif result and result.get("_failed"):
            # Failed - track it
            failure = {
                "path": str(pdf_file),
                "relative_path": pdf_file.name,
                "group": "General",
                "error": result.get("error", "Unknown error"),
                "would_be_key": result.get("would_be_key", "UNKNOWN")
            }
            failed_files.append(failure)
            extractor._last_failed_files = failed_files
            # Print failed file details to CLI
            click.echo(extractor._format_failed_files_cli(failed_files), err=False)
            raise click.Abort()
        else:
            # Unexpected None
            click.echo(f"Failed to extract metadata from {pdf_file.name}", err=True)
            raise click.Abort()

    elif directory:
        click.echo(f"\nProcessing directory: {directory}")
        citations = extractor.process_directory(directory, output_path=output_path)
        
        # Check if we have any citations at all
        if not any(citations.values()):
            click.echo("\nNo citations extracted. Check the log for details.", err=True)
            # Write failed files log even if all failed
            if extractor._last_failed_files:
                extractor._write_failed_files_log(extractor._last_failed_files, output_path)
                # Print failed file details to CLI
                click.echo(extractor._format_failed_files_cli(extractor._last_failed_files), err=False)
            raise click.Abort()

    # Export results
    if citations:
        click.echo(f"\nExporting to {output_path}...")

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        success = extractor.export_citations(citations, output_path, output_format, overwrite)

        if success:
            # Write failed files log if any failures occurred
            if extractor._last_failed_files:
                extractor._write_failed_files_log(extractor._last_failed_files, output_path)
                click.echo(f"\n⚠️  Failed files log: {output_path.parent / 'failed_extractions.log'}")
                click.echo(extractor._format_failed_files_cli(extractor._last_failed_files), err=False)
            
            # Count total citations across all groups
            total_auto_count = sum(len(c) for c in citations.values())
            group_count = len(citations)
            
            click.echo(f"\n✅ Successfully exported to {output_path}")
            click.echo(f"\nSummary:")
            click.echo(f"  - New auto-extracted citations: {total_auto_count}")
            click.echo(f"  - Groups: {group_count}")
            for group_name, group_citations in citations.items():
                click.echo(f"    - {group_name}: {len(group_citations)} citations")
            click.echo(f"  - Output format: {output_format}")
            click.echo(f"  - Output file: {output_path}")
            
            # NEW: Show manual entry preservation info
            if output_path.exists() and not overwrite:
                try:
                    # Count manual entries in the final file
                    import bibtexparser
                    with open(output_path, "r", encoding="utf-8") as f:
                        final_content = f.read()
                    parser = _create_bibtex_parser()
                    final_db = bibtexparser.loads(final_content, parser=parser)
                    manual_count = sum(1 for e in final_db.entries if "pdf_uuid" not in e)
                    auto_count = len(final_db.entries) - manual_count
                    
                    if manual_count > 0:
                        click.echo(f"  - Manual entries preserved: {manual_count}")
                    click.echo(f"  - Total entries in file: {len(final_db.entries)} ({auto_count} auto + {manual_count} manual)")
                except Exception as e:
                    logger.debug(f"Could not count entries for summary: {e}")
            
            # NEW: Clear instructions for failed files
            if extractor._last_failed_files:
                click.echo(f"\n📝 {len(extractor._last_failed_files)} files could not be processed automatically.")
                click.echo("   These MUST be added manually to JabRef.")
                click.echo("   See 'failed_extractions.log' for detailed instructions.")
                click.echo("   Manually added entries will be preserved in future runs.")
        else:
            click.echo("Export failed", err=True)
            raise click.Abort()


if __name__ == "__main__":
    main()
