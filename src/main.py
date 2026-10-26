"""Main CLI interface for PDF Citation Extractor"""

import click
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm

from src.extractors import PDFMetadataExtractor, DOIExtractor, GROBIDClient
from src.api_clients import CrossRefClient
from src.exporters import BibTeXExporter

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

        Args:
            pdf_path: Path to PDF file

        Returns:
            Citation metadata dictionary or None if extraction failed
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
                return metadata

        # If we have useful embedded metadata, use it
        if self.pdf_extractor.has_useful_metadata(metadata):
            logger.info(f"Using embedded metadata for {pdf_path.name}")
            metadata["source"] = "embedded"
            metadata["pdf_file"] = pdf_path.name
            return metadata

        # Strategy 3: GROBID fallback for PDFs without DOI or embedded metadata
        if self.grobid_client and self.grobid_client.available:
            logger.info(f"Trying GROBID extraction for {pdf_path.name}")
            grobid_metadata = self.grobid_client.process(pdf_path)
            if grobid_metadata:
                return grobid_metadata

        logger.warning(f"Could not extract sufficient metadata from {pdf_path.name}")
        return None

    def process_directory(self, directory: Path) -> Dict[str, List[Dict]]:
        """
        Process all PDF files in a directory and its subdirectories.
        Files are grouped by their immediate parent directory name.
        Files in the root directory are grouped under "General".

        Args:
            directory: Directory to search for PDF files

        Returns:
            Dictionary mapping group names to lists of citation metadata
        """
        # Find all PDF files recursively
        pdf_files = list(directory.rglob("*.pdf"))

        if not pdf_files:
            logger.warning(f"No PDF files found in {directory}")
            return {"General": []}

        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")

        # Group citations by parent directory
        grouped_citations: Dict[str, List[Dict]] = {}
        failed_files = []

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
                
                # Process the PDF
                metadata = self.process_pdf(pdf_path)
                if metadata:
                    # Add group information to metadata
                    metadata["group"] = group_name
                    metadata["group_path"] = str(relative_path.parent)
                    
                    # Add to appropriate group
                    if group_name not in grouped_citations:
                        grouped_citations[group_name] = []
                    grouped_citations[group_name].append(metadata)
                else:
                    failed_files.append(str(pdf_path))
            except Exception as e:
                logger.error(f"Error processing {pdf_path.name}: {e}")
                failed_files.append(str(pdf_path))

        # Summary
        total_success = sum(len(c) for c in grouped_citations.values())
        logger.info(
            f"\nProcessing complete: {total_success} successful, {len(failed_files)} failed"
        )
        if failed_files:
            logger.warning(f"Failed files: {', '.join(failed_files[:5])}{'...' if len(failed_files) > 5 else ''}")

        # If we have no citations at all, return empty "General" group
        if not grouped_citations:
            return {"General": []}

        return grouped_citations

    def _export_to_bibtex(self, citations: Dict[str, List[Dict]], output_path: Path, overwrite: bool = False) -> bool:
        """
        Export grouped citations to BibTeX file with group comments.
        By default, merges with existing file to avoid overwriting entries.

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
            
            if not overwrite and output_path.exists():
                with open(output_path, "r", encoding="utf-8") as f:
                    existing_content = f.read()
                
                # Parse existing BibTeX file
                try:
                    existing_db = bibtexparser.loads(existing_content)
                    existing_entries = {entry["ID"]: entry for entry in existing_db.entries}
                    logger.info(f"Found {len(existing_entries)} existing entries in {output_path}")
                except Exception as e:
                    logger.warning(f"Could not parse existing BibTeX file, starting fresh: {e}")
                    existing_entries = {}
            
            # Step 2: Build all entries (new + existing)
            all_entries = dict(existing_entries)  # Start with existing
            new_count = 0
            
            for group_name, group_citations in citations.items():
                for citation in group_citations:
                    entry = self.bibtex_exporter._create_bibtex_entry(citation)
                    if entry:
                        entry_id = entry["ID"]
                        if entry_id in all_entries:
                            # Entry already exists, skip it
                            logger.debug(f"Skipping duplicate entry: {entry_id}")
                        else:
                            # New entry
                            all_entries[entry_id] = entry
                            new_count += 1
            
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
                # Write JabRef metadata first
                if jabref_metadata:
                    bibfile.write(jabref_metadata)
                    bibfile.write("\n")
                
                # Add group comments for the new citation groups
                for group_name, group_citations in citations.items():
                    if group_citations:  # Only add group header if there are citations
                        bibfile.write(f"% ===== Group: {group_name} =====\n\n")
                
                # Write all entries (existing + new)
                bibfile.write(writer.write(db))

            logger.info(f"Exported to {output_path} ({new_count} new entries, {len(existing_entries)} existing preserved)")
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
def main(
    directory: Optional[Path],
    pdf_file: Optional[Path],
    output_path: Path,
    output_format: str,
    config_path: Optional[Path],
    verbose: bool,
    overwrite: bool,
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
    if pdf_file:
        click.echo(f"\nProcessing single PDF: {pdf_file.name}")
        metadata = extractor.process_pdf(pdf_file)
        if metadata:
            # Wrap single citation in "General" group
            citations = {"General": [metadata]}
        else:
            click.echo(f"Failed to extract metadata from {pdf_file.name}", err=True)
            raise click.Abort()

    elif directory:
        click.echo(f"\nProcessing directory: {directory}")
        citations = extractor.process_directory(directory)
        
        # Check if we have any citations at all
        if not any(citations.values()):
            click.echo("\nNo citations extracted. Check the log for details.", err=True)
            raise click.Abort()

    # Export results
    if citations:
        click.echo(f"\nExporting to {output_path}...")

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        success = extractor.export_citations(citations, output_path, output_format, overwrite)

        if success:
            # Count total citations across all groups
            total_count = sum(len(c) for c in citations.values())
            group_count = len(citations)
            
            click.echo(f"Successfully exported to {output_path}")
            click.echo(f"\nSummary:")
            click.echo(f"  - Total citations: {total_count}")
            click.echo(f"  - Groups: {group_count}")
            for group_name, group_citations in citations.items():
                click.echo(f"    - {group_name}: {len(group_citations)} citations")
            click.echo(f"  - Output format: {output_format}")
            click.echo(f"  - Output file: {output_path}")
        else:
            click.echo("Export failed", err=True)
            raise click.Abort()


if __name__ == "__main__":
    main()
