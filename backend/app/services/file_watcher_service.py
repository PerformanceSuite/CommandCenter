"""
File watcher service for monitoring local directories
"""

import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional, Callable, Dict
from dataclasses import dataclass
from pathlib import Path
import fnmatch

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import PyPDF2
from docx import Document

logger = logging.getLogger(__name__)

# Security: Maximum file size to process (100MB default)
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB

# Security: System directories that should never be watched
BLOCKED_PATH_PREFIXES = [
    "/etc",
    "/root",
    "/sys",
    "/proc",
    "/dev",
    "/boot",
    "/var/log",
    "/var/run",
]


@dataclass
class FileChangeEvent:
    """Represents a file system change event"""

    event_type: str  # created, modified, deleted
    file_path: str
    is_directory: bool


class FileWatcherService:
    """Service for monitoring file system changes"""

    def __init__(self, max_file_size_bytes: int = MAX_FILE_SIZE_BYTES):
        self.logger = logger
        self._last_processed: Dict[str, datetime] = {}
        self.max_file_size_bytes = max_file_size_bytes

    def _validate_watch_path(self, path: str) -> str:
        """
        Validate that a path is safe to watch.

        Args:
            path: Path to validate

        Returns:
            Resolved absolute path

        Raises:
            ValueError: If path is not safe to watch
        """
        try:
            # Resolve path to handle symlinks and relative paths
            resolved_path = Path(path).resolve()
            resolved_str = str(resolved_path)

            # Check against blocked system directories
            # Handle both direct paths and macOS symlinks (e.g., /etc -> /private/etc)
            for blocked_prefix in BLOCKED_PATH_PREFIXES:
                # Check direct match
                if resolved_str.startswith(blocked_prefix):
                    self.logger.error(
                        f"Attempted to watch blocked system directory: {resolved_str}"
                    )
                    raise ValueError(
                        f"Access denied: Cannot watch system directory {blocked_prefix}"
                    )
                # Check macOS /private prefix (e.g., /private/etc)
                private_prefix = f"/private{blocked_prefix}"
                if resolved_str.startswith(private_prefix):
                    self.logger.error(
                        f"Attempted to watch blocked system directory: {resolved_str}"
                    )
                    raise ValueError(
                        f"Access denied: Cannot watch system directory {blocked_prefix}"
                    )

            # Ensure path exists
            if not resolved_path.exists():
                raise ValueError(f"Path does not exist: {resolved_str}")

            # Ensure path is a directory for watching
            if not resolved_path.is_dir():
                raise ValueError(f"Path is not a directory: {resolved_str}")

            self.logger.info(f"Path validation passed: {resolved_str}")
            return resolved_str

        except Exception as e:
            self.logger.error(f"Path validation failed for {path}: {e}")
            raise

    def _validate_file_size(self, file_path: str) -> None:
        """
        Validate that a file is not too large to process.

        Args:
            file_path: Path to file

        Raises:
            ValueError: If file exceeds maximum size
        """
        try:
            file_size = os.path.getsize(file_path)

            if file_size > self.max_file_size_bytes:
                size_mb = file_size / (1024 * 1024)
                max_mb = self.max_file_size_bytes / (1024 * 1024)

                self.logger.error(
                    f"File size violation: {file_path} is {size_mb:.2f}MB, "
                    f"max allowed is {max_mb:.2f}MB"
                )

                raise ValueError(
                    f"File too large: {size_mb:.2f}MB exceeds maximum of {max_mb:.2f}MB"
                )

        except OSError as e:
            self.logger.error(f"Failed to check file size for {file_path}: {e}")
            raise ValueError(f"Cannot access file: {file_path}")

    def extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text content from various file types.

        Args:
            file_path: Path to file

        Returns:
            Extracted text content
        """
        # Security: Validate file size before processing
        try:
            self._validate_file_size(file_path)
        except ValueError as e:
            self.logger.error(f"File size validation failed: {e}")
            return ""

        file_ext = Path(file_path).suffix.lower()

        try:
            if file_ext == ".pdf":
                return self._extract_pdf(file_path)
            elif file_ext == ".docx":
                return self._extract_docx(file_path)
            elif file_ext in [".txt", ".md", ".markdown"]:
                return self._extract_text(file_path)
            else:
                self.logger.warning(f"Unsupported file type: {file_ext}")
                return ""

        except Exception as e:
            self.logger.error(f"Failed to extract text from {file_path}: {e}")
            return ""

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        with open(file_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text_parts = []

            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())

            return "\n\n".join(text_parts)

    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        doc = Document(file_path)
        text_parts = [para.text for para in doc.paragraphs]
        return "\n\n".join(text_parts)

    def _extract_text(self, file_path: str) -> str:
        """Extract text from plain text file"""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def should_process_file(self, file_path: str, patterns: List[str]) -> bool:
        """
        Check if file matches any of the allowed patterns.

        Args:
            file_path: Path to file
            patterns: List of glob patterns (e.g., ["*.pdf", "*.md"])

        Returns:
            True if file should be processed
        """
        filename = os.path.basename(file_path)

        for pattern in patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True

        return False

    def should_ignore_file(self, file_path: str, ignore_patterns: List[str]) -> bool:
        """
        Check if file matches any ignore patterns.

        Args:
            file_path: Path to file
            ignore_patterns: List of ignore patterns (e.g., [".git", "node_modules"])

        Returns:
            True if file should be ignored
        """
        for pattern in ignore_patterns:
            if pattern in file_path:
                return True

        return False

    def should_debounce(self, file_path: str, debounce_seconds: int = 2) -> bool:
        """
        Check if enough time has passed since last processing.

        Args:
            file_path: Path to file
            debounce_seconds: Seconds to wait between processing same file

        Returns:
            True if file should be processed (debounce period elapsed)
        """
        now = datetime.now()

        # Clean up old entries to prevent memory leak
        # Remove entries older than 1 hour when dict grows beyond 1000 entries
        if len(self._last_processed) > 1000:
            cutoff = now - timedelta(hours=1)
            self._last_processed = {
                k: v for k, v in self._last_processed.items() if v > cutoff
            }
            self.logger.debug(
                f"Cleaned up debounce cache, {len(self._last_processed)} entries remain"
            )

        if file_path in self._last_processed:
            time_since_last = now - self._last_processed[file_path]
            if time_since_last < timedelta(seconds=debounce_seconds):
                return False

        self._last_processed[file_path] = now
        return True


class FileChangeHandler(FileSystemEventHandler):
    """Handler for file system events"""

    def __init__(
        self,
        callback: Callable[[FileChangeEvent], None],
        patterns: List[str],
        ignore_patterns: List[str],
    ):
        self.callback = callback
        self.patterns = patterns
        self.ignore_patterns = ignore_patterns
        self.file_watcher = FileWatcherService()

    def on_created(self, event: FileSystemEvent):
        """Called when file is created"""
        if event.is_directory:
            return

        self._process_event("created", event.src_path)

    def on_modified(self, event: FileSystemEvent):
        """Called when file is modified"""
        if event.is_directory:
            return

        self._process_event("modified", event.src_path)

    def _process_event(self, event_type: str, file_path: str):
        """Process file system event"""
        # Check patterns
        if not self.file_watcher.should_process_file(file_path, self.patterns):
            return

        # Check ignore patterns
        if self.file_watcher.should_ignore_file(file_path, self.ignore_patterns):
            return

        # Debounce
        if not self.file_watcher.should_debounce(file_path, debounce_seconds=2):
            return

        # Trigger callback
        event = FileChangeEvent(
            event_type=event_type, file_path=file_path, is_directory=False
        )

        self.callback(event)


def start_watching(
    directory: str,
    callback: Callable[[FileChangeEvent], None],
    patterns: List[str] = None,
    ignore_patterns: List[str] = None,
) -> Observer:
    """
    Start watching directory for file changes.

    Args:
        directory: Directory to watch
        callback: Function to call when file changes
        patterns: File patterns to watch (default: all)
        ignore_patterns: Patterns to ignore (default: ['.git', '__pycache__'])

    Returns:
        Observer instance (call .stop() to stop watching)

    Raises:
        ValueError: If directory path is not safe to watch
    """
    # Security: Validate path before watching
    file_watcher_service = FileWatcherService()
    validated_directory = file_watcher_service._validate_watch_path(directory)

    if patterns is None:
        patterns = ["*"]

    if ignore_patterns is None:
        ignore_patterns = [".git", "__pycache__", ".DS_Store", "node_modules"]

    event_handler = FileChangeHandler(callback, patterns, ignore_patterns)

    observer = Observer()
    observer.schedule(event_handler, validated_directory, recursive=True)
    observer.start()

    logger.info(f"Started watching directory: {validated_directory}")

    return observer
