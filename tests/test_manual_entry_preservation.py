"""Tests for manual entry preservation in BibTeX export.

This test suite ensures that manually added entries (without pdf_uuid) 
are always preserved during merge operations.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.main import CitationExtractor
from src.exporters import BibTeXExporter


@pytest.fixture
def temp_bib_file():
    """Create a temporary .bib file with manual entries"""
    tmp_dir = Path(tempfile.mkdtemp())
    bib_file = tmp_dir / "test.bib"
    yield bib_file, tmp_dir
    shutil.rmtree(tmp_dir)


@pytest.fixture
def extractor():
    """Create a CitationExtractor instance"""
    return CitationExtractor()


@pytest.fixture
def sample_manual_bib_content():
    """Sample BibTeX content with manual entries (no pdf_uuid)"""
    return """@Comment{jabref-meta: databaseType:bibtex;}

@article{ManualEntry1,
    author = {Smith, John},
    title = {A Manual Paper},
    journal = {Manual Journal},
    year = {2020}
}

@article{ManualEntry2,
    author = {Doe, Jane},
    title = {Another Manual Paper},
    journal = {Another Journal},
    year = {2021}
}

@book{ManualBook1,
    author = {Brown, Charlie},
    title = {A Manual Book},
    publisher = {Manual Publisher},
    year = {2019}
}"""


@pytest.fixture
def sample_manual_bib_with_auto():
    """Sample BibTeX content with both manual and auto entries"""
    return """@Comment{jabref-meta: databaseType:bibtex;}

@article{ManualEntry1,
    author = {Smith, John},
    title = {A Manual Paper},
    journal = {Manual Journal},
    year = {2020}
}

@article{AutoEntry1,
    author = {Auto, Author},
    title = {An Auto Paper},
    journal = {Auto Journal},
    year = {2022},
    pdf_uuid = {auto-uuid-123}
}

@article{ManualEntry2,
    author = {Doe, Jane},
    title = {Another Manual Paper},
    journal = {Another Journal},
    year = {2021}
}"""


class TestManualEntryPreservation:
    """Tests for preserving manual entries during export"""

    def test_manual_entries_preserved_in_merge(self, extractor, temp_bib_file):
        """Test that manual entries are preserved when merging new citations"""
        bib_file, tmp_dir = temp_bib_file
        
        # Write initial .bib file with manual entries
        manual_content = """@article{ManualEntry1,
    author = {Smith, John},
    title = {A Manual Paper},
    journal = {Manual Journal},
    year = {2020}
}

@article{ManualEntry2,
    author = {Doe, Jane},
    title = {Another Manual Paper},
    journal = {Another Journal},
    year = {2021}
}"""
        bib_file.write_text(manual_content)
        
        # Create some test citations to add
        test_citations = {
            "General": [
                {
                    "author": "Test Author",
                    "title": "Test Paper",
                    "year": "2023",
                    "journal": "Test Journal",
                    "pdf_uuid": "test-uuid-456"
                }
            ]
        }
        
        # Export with merge (overwrite=False)
        success = extractor.export_citations(test_citations, bib_file, format="bibtex", overwrite=False)
        
        assert success, "Export should succeed"
        
        # Read the result
        result_content = bib_file.read_text()
        
        # Check that manual entries are preserved
        assert "ManualEntry1" in result_content, "ManualEntry1 should be preserved"
        assert "ManualEntry2" in result_content, "ManualEntry2 should be preserved"
        assert "A Manual Paper" in result_content, "Manual entry title should be preserved"
        assert "Another Manual Paper" in result_content, "Manual entry title should be preserved"
        
        # Check that auto entry was added
        assert "Test Author" in result_content, "Auto entry should be added"
        assert "Test Paper" in result_content, "Auto entry title should be added"
        
    def test_manual_entries_preserved_with_complex_metadata(self, extractor, temp_bib_file):
        """Test preservation with complex manual entry metadata"""
        bib_file, tmp_dir = temp_bib_file
        
        # Write .bib with complex manual entries
        manual_content = """@inproceedings{ManualConf2020,
    author = {Smith, John and Doe, Jane},
    title = {Complex Paper Title with Special Chars: {A} Test},
    booktitle = {Proceedings of the Conference},
    year = {2020},
    pages = {1-10},
    publisher = {ACM},
    address = {New York, NY, USA},
    month = {June},
    note = {This is a manual entry with notes},
    abstract = {This is an abstract with special characters: {test}}
}

@phdthesis{ManualThesis2019,
    author = {Brown, Charlie},
    title = {A PhD Thesis with \\LaTeX Commands},
    school = {University of Test},
    year = {2019},
    address = {Test City},
    month = {January}
}"""
        bib_file.write_text(manual_content)
        
        # Add auto citations
        test_citations = {
            "General": [
                {
                    "author": "Auto Author",
                    "title": "Auto Paper",
                    "year": "2023",
                    "journal": "Auto Journal",
                    "pdf_uuid": "auto-uuid-789"
                }
            ]
        }
        
        # Export with merge
        success = extractor.export_citations(test_citations, bib_file, format="bibtex", overwrite=False)
        
        assert success, "Export should succeed"
        
        # Read result
        result_content = bib_file.read_text()
        
        # Check manual entries preserved
        assert "ManualConf2020" in result_content
        assert "ManualThesis2019" in result_content
        assert "Complex Paper Title" in result_content
        assert "A PhD Thesis" in result_content
        assert "This is a manual entry with notes" in result_content
        
        # Check auto entry added
        assert "Auto Author" in result_content

    def test_multiple_manual_entries_preserved(self, extractor, temp_bib_file):
        """Test preservation of many manual entries"""
        bib_file, tmp_dir = temp_bib_file
        
        # Create 10 manual entries
        manual_entries = []
        for i in range(10):
            manual_entries.append(f"""@article{{Manual{i},
    author = {{Author, Test{i}}},
    title = {{Manual Paper {i}}},
    journal = {{Test Journal}},
    year = {{202{i}}}
}}""")
        
        manual_content = "\n\n".join(manual_entries)
        bib_file.write_text(manual_content)
        
        # Add some auto entries
        test_citations = {
            "General": [
                {
                    "author": f"Auto Author {i}",
                    "title": f"Auto Paper {i}",
                    "year": "2023",
                    "journal": "Auto Journal",
                    "pdf_uuid": f"auto-uuid-{i}"
                }
                for i in range(5)
            ]
        }
        
        # Export with merge
        success = extractor.export_citations(test_citations, bib_file, format="bibtex", overwrite=False)
        
        assert success, "Export should succeed"
        
        # Read result
        result_content = bib_file.read_text()
        
        # Check all manual entries preserved
        for i in range(10):
            assert f"Manual{i}" in result_content, f"Manual{i} should be preserved"
            assert f"Manual Paper {i}" in result_content, f"Manual Paper {i} should be preserved"
        
        # Check auto entries added
        for i in range(5):
            assert f"Auto Author {i}" in result_content, f"Auto Author {i} should be added"

    def test_manual_entries_with_same_key_as_auto_preserved(self, extractor, temp_bib_file):
        """Test that manual entries are preserved even if auto entry has same key"""
        bib_file, tmp_dir = temp_bib_file
        
        # Write manual entry
        manual_content = """@article{TestKey2023,
    author = {Manual, Author},
    title = {Manual Paper},
    journal = {Manual Journal},
    year = {2023}
}"""
        bib_file.write_text(manual_content)
        
        # Try to add auto entry with same key
        test_citations = {
            "General": [
                {
                    "author": "Auto Author",
                    "title": "Auto Paper",
                    "year": "2023",
                    "journal": "Auto Journal",
                    "pdf_uuid": "auto-uuid-same-key"
                }
            ]
        }
        
        # The auto entry will get a different key due to _ensure_unique_citation_key
        success = extractor.export_citations(test_citations, bib_file, format="bibtex", overwrite=False)
        
        assert success, "Export should succeed"
        
        # Read result
        result_content = bib_file.read_text()
        
        # Manual entry should be preserved
        assert "Manual, Author" in result_content, "Manual author should be preserved"
        assert "Manual Paper" in result_content, "Manual title should be preserved"
        
        # Auto entry should be added with different key
        assert "Auto Author" in result_content, "Auto author should be added"


class TestFailedFilesLogging:
    """Tests for failed files logging"""

    def test_failed_files_log_created(self, extractor, temp_bib_file):
        """Test that failed files log is created with proper content"""
        bib_file, tmp_dir = temp_bib_file
        
        # Create failed files list
        failed_files = [
            {
                "path": "/test/path/file1.pdf",
                "relative_path": "file1.pdf",
                "group": "General",
                "error": "No metadata found",
                "would_be_key": "file1"
            },
            {
                "path": "/test/path/subdir/file2.pdf",
                "relative_path": "subdir/file2.pdf",
                "group": "subdir",
                "error": "PDF corrupted",
                "would_be_key": "file2"
            }
        ]
        
        # Write failed files log
        extractor._write_failed_files_log(failed_files, bib_file)
        
        # Check log file exists
        log_file = tmp_dir / "failed_extractions.log"
        assert log_file.exists(), "Failed files log should be created"
        
        # Check log content
        log_content = log_file.read_text()
        
        # Check for clear instructions
        assert "IMPORTANT" in log_content
        assert "MUST add them manually" in log_content
        assert "JabRef" in log_content
        assert "ACTION REQUIRED" in log_content
        
        # Check for file details
        assert "file1.pdf" in log_content
        assert "file2.pdf" in log_content
        assert "No metadata found" in log_content
        assert "PDF corrupted" in log_content
        assert "file1" in log_content  # would_be_key
        assert "file2" in log_content  # would_be_key

    def test_failed_files_log_clear_instructions(self, extractor, temp_bib_file):
        """Test that failed files log has very clear instructions"""
        bib_file, tmp_dir = temp_bib_file
        
        failed_files = [
            {
                "path": "/test/file.pdf",
                "relative_path": "file.pdf",
                "group": "General",
                "error": "No DOI found",
                "would_be_key": "testfile"
            }
        ]
        
        extractor._write_failed_files_log(failed_files, bib_file)
        
        log_file = tmp_dir / "failed_extractions.log"
        log_content = log_file.read_text()
        
        # Check for step-by-step instructions
        assert "1. Open your .bib file in JabRef" in log_content
        assert "2. For each file below, create a new entry" in log_content
        assert "3. Use the 'Suggested BibTeX Key'" in log_content
        assert "4. Add the entry to the specified 'Group'" in log_content
        
        # Check for emphasis
        assert "IMPORTANT" in log_content
        assert "MUST" in log_content
        assert "ACTION REQUIRED" in log_content


class TestBibTeXExporterManualPreservation:
    """Tests for BibTeXExporter's role in manual entry preservation"""

    def test_create_entry_without_uuid(self, temp_bib_file):
        """Test that BibTeXExporter can create entries without UUID"""
        bib_file, tmp_dir = temp_bib_file
        
        exporter = BibTeXExporter()
        
        # Create a manual entry (no pdf_uuid)
        manual_metadata = {
            "author": "Manual Author",
            "title": "Manual Paper",
            "year": "2023",
            "journal": "Manual Journal"
            # No pdf_uuid - this is a manual entry
        }
        
        entry = exporter._create_bibtex_entry(manual_metadata)
        
        assert entry is not None
        assert "ID" in entry
        assert "ENTRYTYPE" in entry
        assert "pdf_uuid" not in entry  # Should not have UUID
        assert "author" in entry
        assert entry["author"] == "Manual Author"

    def test_create_entry_with_uuid(self, temp_bib_file):
        """Test that BibTeXExporter can create entries with UUID"""
        exporter = BibTeXExporter()
        
        # Create an auto entry (with pdf_uuid)
        auto_metadata = {
            "author": "Auto Author",
            "title": "Auto Paper",
            "year": "2023",
            "journal": "Auto Journal",
            "pdf_uuid": "test-uuid-123"
        }
        
        entry = exporter._create_bibtex_entry(auto_metadata)
        
        assert entry is not None
        assert "pdf_uuid" in entry
        assert entry["pdf_uuid"] == "test-uuid-123"


class TestEdgeCases:
    """Tests for edge cases in manual entry preservation"""

    def test_empty_bib_file_preservation(self, extractor, temp_bib_file):
        """Test preservation when starting with empty .bib file"""
        bib_file, tmp_dir = temp_bib_file
        
        # Start with empty file
        bib_file.write_text("")
        
        # Add auto citations
        test_citations = {
            "General": [
                {
                    "author": "Test Author",
                    "title": "Test Paper",
                    "year": "2023",
                    "pdf_uuid": "test-uuid-123"
                }
            ]
        }
        
        # Export with merge
        success = extractor.export_citations(test_citations, bib_file, format="bibtex", overwrite=False)
        
        assert success, "Export should succeed"
        
        # Read result
        result_content = bib_file.read_text()
        
        # Should have the auto entry
        assert "Test Author" in result_content
        assert "Test Paper" in result_content

    def test_overwrite_mode_removes_manual_entries(self, extractor, temp_bib_file):
        """Test that overwrite mode removes manual entries (expected behavior)"""
        bib_file, tmp_dir = temp_bib_file
        
        # Write manual entry
        manual_content = """@article{ManualEntry,
    author = {Smith, John},
    title = {Manual Paper},
    year = {2020}
}"""
        bib_file.write_text(manual_content)
        
        # Add auto citations with overwrite
        test_citations = {
            "General": [
                {
                    "author": "Auto Author",
                    "title": "Auto Paper",
                    "year": "2023",
                    "pdf_uuid": "auto-uuid-123"
                }
            ]
        }
        
        # Export with overwrite=True
        success = extractor.export_citations(test_citations, bib_file, format="bibtex", overwrite=True)
        
        assert success, "Export should succeed"
        
        # Read result
        result_content = bib_file.read_text()
        
        # Manual entry should be REMOVED (overwrite mode)
        assert "ManualEntry" not in result_content
        assert "Manual Paper" not in result_content
        
        # Auto entry should be present
        assert "Auto Author" in result_content
        assert "Auto Paper" in result_content

    def test_manual_entries_survive_multiple_exports(self, extractor, temp_bib_file):
        """Test that manual entries survive multiple export operations"""
        bib_file, tmp_dir = temp_bib_file
        
        # Start with manual entry
        manual_content = """@article{ManualEntry,
    author = {Smith, John},
    title = {Manual Paper},
    year = {2020}
}"""
        bib_file.write_text(manual_content)
        
        # First export - add some auto entries
        test_citations_1 = {
            "General": [
                {
                    "author": "Auto1",
                    "title": "Paper1",
                    "year": "2021",
                    "pdf_uuid": "uuid-1"
                }
            ]
        }
        extractor.export_citations(test_citations_1, bib_file, format="bibtex", overwrite=False)
        
        # Second export - add more auto entries
        test_citations_2 = {
            "General": [
                {
                    "author": "Auto2",
                    "title": "Paper2",
                    "year": "2022",
                    "pdf_uuid": "uuid-2"
                }
            ]
        }
        extractor.export_citations(test_citations_2, bib_file, format="bibtex", overwrite=False)
        
        # Third export - add more auto entries
        test_citations_3 = {
            "General": [
                {
                    "author": "Auto3",
                    "title": "Paper3",
                    "year": "2023",
                    "pdf_uuid": "uuid-3"
                }
            ]
        }
        extractor.export_citations(test_citations_3, bib_file, format="bibtex", overwrite=False)
        
        # Check final result
        result_content = bib_file.read_text()
        
        # Manual entry should still be there
        assert "ManualEntry" in result_content
        assert "Manual Paper" in result_content
        
        # All auto entries should be there
        assert "Auto1" in result_content
        assert "Auto2" in result_content
        assert "Auto3" in result_content
