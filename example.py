"""Example script demonstrating programmatic usage of PDF Citation Extractor"""

from pathlib import Path
from src.main import CitationExtractor

def main():
    """Example usage of the Citation Extractor."""

    # Initialize the extractor
    print("Initializing Citation Extractor...")
    extractor = CitationExtractor()

    # Example 1: Process a single PDF
    print("\n=== Example 1: Single PDF ===")
    pdf_path = Path("example_paper.pdf")

    if pdf_path.exists():
        metadata = extractor.process_pdf(pdf_path)

        if metadata:
            print(f"Successfully extracted metadata:")
            print(f"  Title: {metadata.get('title')}")
            print(f"  Author: {metadata.get('author')}")
            print(f"  Year: {metadata.get('year')}")
            print(f"  DOI: {metadata.get('doi')}")
            print(f"  Source: {metadata.get('source')}")

            # Export single citation
            output = Path("single_citation.bib")
            extractor.export_citations([metadata], output)
            print(f"\n✓ Exported to {output}")
        else:
            print("Failed to extract metadata")
    else:
        print(f"PDF not found: {pdf_path}")

    # Example 2: Process a directory
    print("\n=== Example 2: Directory Processing ===")
    pdf_dir = Path("test_pdfs")

    if pdf_dir.exists() and pdf_dir.is_dir():
        citations = extractor.process_directory(pdf_dir)

        print(f"\nExtracted {len(citations)} citations")

        # Show summary
        for i, citation in enumerate(citations, 1):
            title = citation.get('title', 'Unknown')[:50]
            source = citation.get('source', 'unknown')
            print(f"  {i}. {title}... (from {source})")

        # Export all citations
        if citations:
            output = Path("all_citations.bib")
            extractor.export_citations(citations, output)
            print(f"\n✓ Exported {len(citations)} citations to {output}")
    else:
        print(f"Directory not found: {pdf_dir}")
        print("Create a 'test_pdfs' directory and add some PDF files to test.")

    # Example 3: Accessing individual components
    print("\n=== Example 3: Using Individual Components ===")

    if pdf_path.exists():
        # DOI Extraction
        doi = extractor.doi_extractor.extract(pdf_path)
        if doi:
            print(f"DOI found: {doi}")

            # Query CrossRef directly
            crossref_data = extractor.crossref_client.get_metadata(doi)
            if crossref_data:
                print(f"CrossRef lookup successful!")
                print(f"  Journal: {crossref_data.get('journal')}")
                print(f"  Volume: {crossref_data.get('volume')}")
                print(f"  Pages: {crossref_data.get('pages')}")

        # Embedded metadata extraction
        embedded_meta = extractor.pdf_extractor.extract(pdf_path)
        has_metadata = extractor.pdf_extractor.has_useful_metadata(embedded_meta)
        print(f"\nEmbedded metadata useful: {has_metadata}")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
