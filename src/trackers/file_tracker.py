"""File tracking system for PDF-Citation-Scimmer

This module provides a tracking system that maintains persistent links between
PDF files and their BibTeX entries using UUIDs. This ensures that files can
be identified even when citation keys change in tools like JabRef.

The tracker stores a JSON file (.pdf_tracker.json) in the same directory as
the output bib-file, containing:
- UUID for each tracked file (deterministic, based on file path + metadata)
- File paths (absolute and relative)
- File hashes (SHA-256 of content)
- Citation keys
- Timestamps for tracking when files were first/last seen
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class FileTrackerEntry:
    """Represents a tracked file entry in the tracker system.
    
    Attributes:
        uuid: Unique identifier for this file (deterministic)
        file_path: Absolute path to the file
        relative_path: Path relative to project root (for portability)
        file_hash: SHA-256 hash of file content
        file_size: Size of file in bytes
        last_modified: ISO timestamp of last file modification
        citation_key: Current BibTeX citation key
        first_seen: ISO timestamp when file was first tracked
        last_seen: ISO timestamp when file was last processed
        metadata: Additional metadata dictionary
    """
    uuid: str
    file_path: str
    relative_path: str
    file_hash: str
    file_size: int
    last_modified: str
    citation_key: str
    first_seen: str
    last_seen: str
    metadata: Dict


class FileTracker:
    """Tracks PDF files and their UUIDs for persistent identification.
    
    The tracker creates a .pdf_tracker.json file in the output directory
    that maintains a mapping between files and their metadata, including
    UUIDs that remain stable even when citation keys change.
    
    Example usage:
        >>> tracker = FileTracker(output_dir="/path/to/output")
        >>> uuid, is_new = tracker.register_file(
        ...     file_path=Path("/path/to/paper.pdf"),
        ...     citation_key="Author_2023_Title"
        ... )
        >>> print(f"UUID: {uuid}, Is new: {is_new}")
    """

    TRACKER_FILE = ".pdf_tracker.json"
    BIBTEX_UUID_FIELD = "pdf_uuid"  # Custom BibTeX field name for UUID

    def __init__(self, output_dir: Union[Path, str]):
        """Initialize the file tracker.
        
        Args:
            output_dir: Directory where the bib-file is stored.
                       The tracker file (.pdf_tracker.json) will be created here.
        """
        self.output_dir = Path(output_dir)
        self.tracker_path = self.output_dir / self.TRACKER_FILE
        self.entries: Dict[str, FileTrackerEntry] = {}
        self._load()

    def _load(self) -> None:
        """Load tracker data from the JSON file."""
        if self.tracker_path.exists():
            try:
                with open(self.tracker_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.entries = {
                        uuid: FileTrackerEntry(**entry_data)
                        for uuid, entry_data in data.items()
                    }
                logger.info(f"Loaded {len(self.entries)} tracked files from {self.tracker_path}")
            except Exception as e:
                logger.warning(f"Could not load tracker file {self.tracker_path}: {e}")
                self.entries = {}
        else:
            self.entries = {}

    def _save(self) -> None:
        """Save tracker data to the JSON file."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        data = {uuid: asdict(entry) for uuid, entry in self.entries.items()}
        with open(self.tracker_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Saved {len(self.entries)} entries to {self.tracker_path}")

    def generate_uuid(self, file_path: Path) -> str:
        """Generate a deterministic UUID for a file.
        
        The UUID is based on the absolute path, last modified time, and file size.
        This ensures the same file always gets the same UUID, making it stable
        across sessions and independent of citation key changes.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Deterministic UUID string
        """
        abs_path = file_path.resolve()
        stat = abs_path.stat()
        unique_string = f"{abs_path}|{stat.st_mtime}|{stat.st_size}"
        return str(uuid.uuid5(uuid.NAMESPACE_URL, unique_string))

    def get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hex-encoded SHA-256 hash
        """
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def register_file(self, file_path: Path, citation_key: str,
                      project_root: Optional[Path] = None,
                      metadata: Optional[Dict] = None) -> Tuple[str, bool]:
        """Register a file and get its UUID.
        
        This is the main method for tracking files. It will:
        - Generate or retrieve the UUID for the file
        - Update the file's metadata in the tracker
        - Save the tracker state to disk
        
        Args:
            file_path: Path to the PDF file
            citation_key: Current citation key for the BibTeX entry
            project_root: Root directory for calculating relative paths
            metadata: Optional additional metadata to store
            
        Returns:
            Tuple of (uuid, is_new) where is_new is True if this is the first
            time the file is being tracked.
        """
        abs_path = file_path.resolve()
        now = datetime.now().isoformat()
        file_uuid = self.generate_uuid(abs_path)

        # Calculate relative path if project root provided
        relative_path = ""
        if project_root:
            try:
                relative_path = str(abs_path.relative_to(Path(project_root).resolve()))
            except ValueError:
                # File is outside project root, use absolute path
                relative_path = str(abs_path)

        # Check if file already tracked
        if file_uuid in self.entries:
            # Update existing entry
            entry = self.entries[file_uuid]
            entry.last_seen = now
            entry.citation_key = citation_key
            entry.file_path = str(abs_path)
            entry.relative_path = relative_path
            if metadata:
                entry.metadata.update(metadata or {})
            self._save()
            return file_uuid, False

        # Create new entry
        try:
            stat = abs_path.stat()
            file_size = stat.st_size
            last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
            file_hash = self.get_file_hash(abs_path)
        except Exception as e:
            logger.warning(f"Could not get file stats for {abs_path}: {e}")
            file_size = 0
            last_modified = now
            file_hash = ""

        new_entry = FileTrackerEntry(
            uuid=file_uuid,
            file_path=str(abs_path),
            relative_path=relative_path,
            file_hash=file_hash,
            file_size=file_size,
            last_modified=last_modified,
            citation_key=citation_key,
            first_seen=now,
            last_seen=now,
            metadata=metadata or {}
        )
        
        self.entries[file_uuid] = new_entry
        self._save()
        logger.debug(f"Tracked new file: {abs_path} -> UUID: {file_uuid[:8]}...")
        return file_uuid, True

    def get_uuid_by_path(self, file_path: Path) -> Optional[str]:
        """Get UUID for a given file path.
        
        Args:
            file_path: Path to look up
            
        Returns:
            UUID string or None if not found
        """
        abs_path = file_path.resolve()
        for entry in self.entries.values():
            if Path(entry.file_path).resolve() == abs_path:
                return entry.uuid
        return None

    def get_entry_by_path(self, file_path: Path) -> Optional[FileTrackerEntry]:
        """Get full entry for a given file path.
        
        Args:
            file_path: Path to look up
            
        Returns:
            FileTrackerEntry or None if not found
        """
        uuid = self.get_uuid_by_path(file_path)
        if uuid:
            return self.entries.get(uuid)
        return None

    def get_path_by_uuid(self, uuid: str) -> Optional[Path]:
        """Get file path for a given UUID.
        
        Args:
            uuid: UUID to look up
            
        Returns:
            Path or None if not found
        """
        if uuid in self.entries:
            return Path(self.entries[uuid].file_path)
        return None

    def get_entry(self, uuid: str) -> Optional[FileTrackerEntry]:
        """Get full entry for a UUID.
        
        Args:
            uuid: UUID to look up
            
        Returns:
            FileTrackerEntry or None
        """
        return self.entries.get(uuid)

    def update_citation_key(self, uuid: str, new_citation_key: str) -> bool:
        """Update citation key for a tracked file.
        
        This is useful when citation keys change in JabRef or other tools.
        
        Args:
            uuid: UUID of the file
            new_citation_key: New citation key
            
        Returns:
            True if updated successfully, False if UUID not found
        """
        if uuid in self.entries:
            self.entries[uuid].citation_key = new_citation_key
            self.entries[uuid].last_seen = datetime.now().isoformat()
            self._save()
            return True
        return False

    def list_all_entries(self) -> List[FileTrackerEntry]:
        """Get all tracked entries.
        
        Returns:
            List of all FileTrackerEntry objects
        """
        return list(self.entries.values())

    def remove_file(self, file_path: Path) -> bool:
        """Remove a file from tracking.
        
        Args:
            file_path: Path to remove
            
        Returns:
            True if removed successfully, False if not found
        """
        uuid = self.get_uuid_by_path(file_path)
        if uuid:
            del self.entries[uuid]
            self._save()
            logger.debug(f"Removed tracking for {file_path}")
            return True
        return False

    def cleanup_missing_files(self) -> int:
        """Remove entries for files that no longer exist.
        
        This should be called periodically to keep the tracker clean.
        
        Returns:
            Number of entries removed
        """
        removed = 0
        for uuid, entry in list(self.entries.items()):
            if not Path(entry.file_path).exists():
                del self.entries[uuid]
                removed += 1
                logger.debug(f"Cleaned up missing file: {entry.file_path}")
        
        if removed > 0:
            self._save()
            logger.info(f"Cleaned up {removed} missing file entries from tracker")
        
        return removed

    def get_files_by_group(self, group_name: str) -> List[FileTrackerEntry]:
        """Get all entries that belong to a specific group.
        
        Args:
            group_name: Group name to filter by
            
        Returns:
            List of entries in the specified group
        """
        return [
            entry for entry in self.entries.values()
            if entry.metadata.get("group") == group_name
        ]

    def get_updated_files(self, since: Optional[str] = None) -> List[FileTrackerEntry]:
        """Get files that have been updated since a specific time.
        
        Args:
            since: ISO timestamp string. If None, returns all files.
            
        Returns:
            List of entries updated since the specified time
        """
        if since is None:
            return list(self.entries.values())
        
        try:
            since_dt = datetime.fromisoformat(since)
            # Parse entry timestamps and compare (both should be naive or both aware)
            result = []
            for entry in self.entries.values():
                entry_dt = datetime.fromisoformat(entry.last_seen)
                # Normalize both to naive for comparison
                if entry_dt.tzinfo is not None:
                    entry_dt = entry_dt.replace(tzinfo=None)
                if since_dt.tzinfo is not None:
                    since_dt_normalized = since_dt.replace(tzinfo=None)
                else:
                    since_dt_normalized = since_dt
                if entry_dt >= since_dt_normalized:
                    result.append(entry)
            return result
        except (ValueError, TypeError):
            # If there's an error parsing the timestamp, return all files
            return list(self.entries.values())

    def reset(self) -> None:
        """Clear all tracked entries.
        
        WARNING: This will remove all tracking data!
        """
        self.entries = {}
        if self.tracker_path.exists():
            self.tracker_path.unlink()
        logger.info("File tracker has been reset")
