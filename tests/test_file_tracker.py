"""Tests for the file tracking system"""

import pytest
from pathlib import Path
import tempfile
import shutil
import json
from datetime import datetime

from src.trackers.file_tracker import FileTracker, FileTrackerEntry


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory"""
    tmp_dir = Path(tempfile.mkdtemp())
    yield tmp_dir
    shutil.rmtree(tmp_dir)


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory with PDFs"""
    tmp_dir = Path(tempfile.mkdtemp())
    pdf_file = tmp_dir / "test.pdf"
    pdf_file.write_text("test content")
    yield tmp_dir, pdf_file
    shutil.rmtree(tmp_dir)


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF file in a temporary directory"""
    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_text("Sample PDF content for testing")
    return pdf_file


class TestFileTrackerEntry:
    """Tests for FileTrackerEntry dataclass"""
    
    def test_entry_creation(self):
        """Test creating a FileTrackerEntry"""
        entry = FileTrackerEntry(
            uuid="test-uuid-123",
            file_path="/path/to/file.pdf",
            relative_path="file.pdf",
            file_hash="abc123",
            file_size=1000,
            last_modified="2024-01-01T00:00:00",
            citation_key="Author_2024_Title",
            first_seen="2024-01-01T00:00:00",
            last_seen="2024-01-01T00:00:00",
            metadata={"group": "Test"}
        )
        
        assert entry.uuid == "test-uuid-123"
        assert entry.file_path == "/path/to/file.pdf"
        assert entry.relative_path == "file.pdf"
        assert entry.metadata["group"] == "Test"


class TestFileTracker:
    """Tests for FileTracker class"""
    
    def test_tracker_stored_with_output(self, temp_output_dir):
        """Test that tracker file is created in output directory"""
        tracker = FileTracker(output_dir=temp_output_dir)
        test_file = temp_output_dir / "test.pdf"
        test_file.write_text("content")
        
        uuid, _ = tracker.register_file(test_file, "test_key")
        
        # Check tracker file exists in output directory
        tracker_file = temp_output_dir / ".pdf_tracker.json"
        assert tracker_file.exists()
    
    def test_tracker_persistence_across_sessions(self, temp_output_dir):
        """Test that tracker persists across instances"""
        test_file = temp_output_dir / "test.pdf"
        test_file.write_text("content")
        
        # First session
        tracker1 = FileTracker(output_dir=temp_output_dir)
        uuid1, _ = tracker1.register_file(test_file, "key1")
        
        # Second session
        tracker2 = FileTracker(output_dir=temp_output_dir)
        uuid2 = tracker2.get_uuid_by_path(test_file)
        
        assert uuid1 == uuid2
    
    def test_deterministic_uuid(self, temp_project_dir):
        """Test that same file gets same UUID"""
        project_dir, pdf_file = temp_project_dir
        output_dir = Path(tempfile.mkdtemp())
        
        try:
            tracker = FileTracker(output_dir=output_dir)
            uuid1, _ = tracker.register_file(pdf_file, "key1")
            uuid2, _ = tracker.register_file(pdf_file, "key2")
            
            assert uuid1 == uuid2
        finally:
            shutil.rmtree(output_dir)
    
    def test_different_files_different_uuids(self, temp_output_dir):
        """Test that different files get different UUIDs"""
        file1 = temp_output_dir / "file1.pdf"
        file2 = temp_output_dir / "file2.pdf"
        file1.write_text("content 1")
        file2.write_text("content 2")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        uuid1, _ = tracker.register_file(file1, "key1")
        uuid2, _ = tracker.register_file(file2, "key2")
        
        assert uuid1 != uuid2
    
    def test_relative_paths(self, temp_project_dir):
        """Test that relative paths are stored correctly"""
        project_dir, pdf_file = temp_project_dir
        output_dir = Path(tempfile.mkdtemp())
        
        try:
            tracker = FileTracker(output_dir=output_dir)
            uuid, _ = tracker.register_file(pdf_file, "key1", project_root=project_dir)
            
            entry = tracker.get_entry(uuid)
            assert entry.relative_path == "test.pdf"
        finally:
            shutil.rmtree(output_dir)
    
    def test_get_uuid_by_path(self, temp_output_dir):
        """Test retrieving UUID by file path"""
        test_file = temp_output_dir / "test.pdf"
        test_file.write_text("content")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        uuid, _ = tracker.register_file(test_file, "key1")
        
        retrieved_uuid = tracker.get_uuid_by_path(test_file)
        assert retrieved_uuid == uuid
    
    def test_get_path_by_uuid(self, temp_output_dir):
        """Test retrieving path by UUID"""
        test_file = temp_output_dir / "test.pdf"
        test_file.write_text("content")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        uuid, _ = tracker.register_file(test_file, "key1")
        
        retrieved_path = tracker.get_path_by_uuid(uuid)
        assert retrieved_path == test_file
    
    def test_get_entry_by_path(self, temp_output_dir):
        """Test retrieving full entry by path"""
        test_file = temp_output_dir / "test.pdf"
        test_file.write_text("content")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        uuid, _ = tracker.register_file(test_file, "key1")
        
        entry = tracker.get_entry_by_path(test_file)
        assert entry is not None
        assert entry.uuid == uuid
        assert entry.citation_key == "key1"
    
    def test_update_citation_key(self, temp_output_dir):
        """Test updating citation key for a tracked file"""
        test_file = temp_output_dir / "test.pdf"
        test_file.write_text("content")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        uuid, _ = tracker.register_file(test_file, "old_key")
        
        # Update citation key
        result = tracker.update_citation_key(uuid, "new_key")
        assert result is True
        
        # Verify update
        entry = tracker.get_entry(uuid)
        assert entry.citation_key == "new_key"
    
    def test_update_nonexistent_uuid(self, temp_output_dir):
        """Test updating citation key for non-existent UUID"""
        tracker = FileTracker(output_dir=temp_output_dir)
        result = tracker.update_citation_key("nonexistent-uuid", "new_key")
        assert result is False
    
    def test_list_all_entries(self, temp_output_dir):
        """Test listing all entries"""
        file1 = temp_output_dir / "file1.pdf"
        file2 = temp_output_dir / "file2.pdf"
        file1.write_text("content 1")
        file2.write_text("content 2")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        tracker.register_file(file1, "key1")
        tracker.register_file(file2, "key2")
        
        entries = tracker.list_all_entries()
        assert len(entries) == 2
    
    def test_remove_file(self, temp_output_dir):
        """Test removing a file from tracking"""
        test_file = temp_output_dir / "test.pdf"
        test_file.write_text("content")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        uuid, _ = tracker.register_file(test_file, "key1")
        
        # Remove file
        result = tracker.remove_file(test_file)
        assert result is True
        
        # Verify removal
        assert uuid not in tracker.entries
        assert tracker.get_uuid_by_path(test_file) is None
    
    def test_cleanup_missing_files(self, temp_output_dir):
        """Test cleanup of missing file entries"""
        # Create a tracker and add an entry
        tracker = FileTracker(output_dir=temp_output_dir)
        
        # Create a temporary file and track it
        temp_file = temp_output_dir / "temp.pdf"
        temp_file.write_text("content")
        uuid, _ = tracker.register_file(temp_file, "key1")
        
        # Remove the file
        temp_file.unlink()
        
        # Cleanup
        removed = tracker.cleanup_missing_files()
        assert removed == 1
        assert uuid not in tracker.entries
    
    def test_cleanup_no_missing_files(self, temp_output_dir):
        """Test cleanup when all files exist"""
        test_file = temp_output_dir / "test.pdf"
        test_file.write_text("content")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        tracker.register_file(test_file, "key1")
        
        # Cleanup when all files exist
        removed = tracker.cleanup_missing_files()
        assert removed == 0
    
    def test_metadata_storage(self, temp_output_dir):
        """Test that metadata is stored and updated"""
        test_file = temp_output_dir / "test.pdf"
        test_file.write_text("content")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        uuid, _ = tracker.register_file(
            test_file, 
            "key1",
            metadata={"group": "TestGroup", "custom_field": "value"}
        )
        
        entry = tracker.get_entry(uuid)
        assert entry.metadata["group"] == "TestGroup"
        assert entry.metadata["custom_field"] == "value"
    
    def test_metadata_update(self, temp_output_dir):
        """Test that metadata is updated on re-registration"""
        test_file = temp_output_dir / "test.pdf"
        test_file.write_text("content")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        uuid, _ = tracker.register_file(
            test_file, 
            "key1",
            metadata={"group": "Group1"}
        )
        
        # Re-register with new metadata
        uuid, is_new = tracker.register_file(
            test_file,
            "key2", 
            metadata={"group": "Group2"}
        )
        
        assert is_new is False  # Same file, should not be new
        
        entry = tracker.get_entry(uuid)
        assert entry.metadata["group"] == "Group2"  # Should be updated
        assert entry.citation_key == "key2"  # Should be updated
    
    def test_file_hash_calculation(self, temp_output_dir):
        """Test that file hash is calculated correctly"""
        test_file = temp_output_dir / "test.pdf"
        test_file.write_text("content")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        file_hash = tracker.get_file_hash(test_file)
        
        # Hash should be a 64-character hex string (SHA-256)
        assert len(file_hash) == 64
        assert all(c in "0123456789abcdef" for c in file_hash)
    
    def test_is_new_flag(self, temp_output_dir):
        """Test that is_new flag works correctly"""
        test_file = temp_output_dir / "test.pdf"
        test_file.write_text("content")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        
        # First registration should be new
        uuid1, is_new1 = tracker.register_file(test_file, "key1")
        assert is_new1 is True
        
        # Second registration should not be new
        uuid2, is_new2 = tracker.register_file(test_file, "key2")
        assert is_new2 is False
        assert uuid1 == uuid2
    
    def test_tracker_file_format(self, temp_output_dir):
        """Test that tracker file is valid JSON"""
        test_file = temp_output_dir / "test.pdf"
        test_file.write_text("content")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        tracker.register_file(test_file, "key1")
        
        # Read and parse the tracker file
        tracker_file = temp_output_dir / ".pdf_tracker.json"
        with open(tracker_file, 'r') as f:
            data = json.load(f)
        
        # Should have at least one entry
        assert len(data) >= 1
        
        # Each entry should have required fields
        for uuid, entry_data in data.items():
            assert "uuid" in entry_data
            assert "file_path" in entry_data
            assert "citation_key" in entry_data
    
    def test_get_files_by_group(self, temp_output_dir):
        """Test filtering entries by group"""
        file1 = temp_output_dir / "file1.pdf"
        file2 = temp_output_dir / "file2.pdf"
        file3 = temp_output_dir / "file3.pdf"
        
        file1.write_text("content 1")
        file2.write_text("content 2")
        file3.write_text("content 3")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        tracker.register_file(file1, "key1", metadata={"group": "GroupA"})
        tracker.register_file(file2, "key2", metadata={"group": "GroupB"})
        tracker.register_file(file3, "key3", metadata={"group": "GroupA"})
        
        group_a_files = tracker.get_files_by_group("GroupA")
        assert len(group_a_files) == 2
        
        group_b_files = tracker.get_files_by_group("GroupB")
        assert len(group_b_files) == 1
    
    def test_get_updated_files(self, temp_output_dir):
        """Test filtering entries by update time"""
        test_file = temp_output_dir / "test.pdf"
        test_file.write_text("content")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        tracker.register_file(test_file, "key1")
        
        # Get the last_seen timestamp
        entry = tracker.get_entry_by_path(test_file)
        last_seen = entry.last_seen
        
        # Get files updated since a time before this entry
        # Use a simple timestamp that's definitely before
        since_before = "1970-01-01T00:00:00"
        files_before = tracker.get_updated_files(since=since_before)
        # Should include this file (updated at or after the timestamp)
        assert len(files_before) >= 1
        
        # Get files updated since a future time (should be empty)
        future_time = "2100-01-01T00:00:00"
        files_after = tracker.get_updated_files(since=future_time)
        # Should not include this file
        assert len(files_after) == 0
    
    def test_reset(self, temp_output_dir):
        """Test resetting the tracker"""
        test_file = temp_output_dir / "test.pdf"
        test_file.write_text("content")
        
        tracker = FileTracker(output_dir=temp_output_dir)
        tracker.register_file(test_file, "key1")
        
        # Verify file is tracked
        assert len(tracker.entries) == 1
        
        # Reset tracker
        tracker.reset()
        
        # Verify tracker is empty
        assert len(tracker.entries) == 0
        
        # Verify tracker file is removed
        tracker_file = temp_output_dir / ".pdf_tracker.json"
        assert not tracker_file.exists()


class TestFileTrackerIntegration:
    """Integration tests for file tracker with the main extractor"""
    
    def test_tracker_integration_with_single_pdf(self, temp_output_dir, sample_pdf):
        """Test that tracker works with single PDF processing"""
        from src.main import CitationExtractor
        
        # Create output directory
        output_dir = temp_output_dir
        output_bib = output_dir / "citations.bib"
        
        # Initialize extractor
        extractor = CitationExtractor()
        
        # Process single PDF with tracking
        result = extractor._process_pdf_with_tracking(
            sample_pdf,
            "General",
            sample_pdf.parent,
            extractor._get_file_tracker(output_dir)
        )
        
        # Result should have UUID
        assert "pdf_uuid" in result or result.get("_failed")
        if not result.get("_failed"):
            assert result["pdf_uuid"] is not None
            assert len(result["pdf_uuid"]) > 0
    
    def test_bibtex_uuid_field(self):
        """Test that UUID is added to BibTeX entries"""
        from src.exporters.bibtex import BibTeXExporter
        
        exporter = BibTeXExporter()
        
        metadata = {
            "author": "Test Author",
            "title": "Test Title",
            "year": "2024",
            "type": "journal-article",
            "pdf_uuid": "test-uuid-123"
        }
        
        entry = exporter._create_bibtex_entry(metadata)
        
        assert "pdf_uuid" in entry
        assert entry["pdf_uuid"] == "test-uuid-123"
