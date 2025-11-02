"""
Unit tests for FileWatcherService
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from app.services.file_watcher_service import FileWatcherService, FileChangeEvent


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def file_watcher():
    """Create FileWatcherService instance"""
    return FileWatcherService()


def test_extract_text_from_pdf(file_watcher, temp_dir):
    """Test extracting text from PDF file"""
    # Create a dummy PDF file for size validation
    pdf_path = os.path.join(temp_dir, "test.pdf")
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4 dummy content")

    # Mock PDF reader
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "PDF content here"
    mock_pdf.pages = [mock_page]

    with patch("app.services.file_watcher_service.PyPDF2.PdfReader", return_value=mock_pdf):
        content = file_watcher.extract_text_from_file(pdf_path)

    assert content == "PDF content here"


def test_extract_text_from_markdown(file_watcher, temp_dir):
    """Test extracting text from Markdown file"""
    md_path = os.path.join(temp_dir, "test.md")

    with open(md_path, "w") as f:
        f.write("# Header\n\nMarkdown content")

    content = file_watcher.extract_text_from_file(md_path)

    assert "# Header" in content
    assert "Markdown content" in content


def test_extract_text_from_docx(file_watcher, temp_dir):
    """Test extracting text from DOCX file"""
    # Create a dummy DOCX file for size validation
    docx_path = os.path.join(temp_dir, "test.docx")
    with open(docx_path, "wb") as f:
        f.write(b"PK dummy docx content")

    mock_doc = MagicMock()
    mock_para = MagicMock()
    mock_para.text = "DOCX paragraph content"
    mock_doc.paragraphs = [mock_para]

    with patch("app.services.file_watcher_service.Document", return_value=mock_doc):
        content = file_watcher.extract_text_from_file(docx_path)

    assert content == "DOCX paragraph content"


def test_should_process_file_with_allowed_patterns(file_watcher):
    """Test file pattern matching"""
    patterns = ["*.pdf", "*.md", "*.txt"]

    assert file_watcher.should_process_file("/path/doc.pdf", patterns) == True
    assert file_watcher.should_process_file("/path/readme.md", patterns) == True
    assert file_watcher.should_process_file("/path/notes.txt", patterns) == True
    assert file_watcher.should_process_file("/path/image.png", patterns) == False


def test_should_ignore_file_with_ignore_patterns(file_watcher):
    """Test file ignore patterns"""
    ignore_patterns = [".git", "node_modules", "__pycache__"]

    assert file_watcher.should_ignore_file("/path/.git/config", ignore_patterns) == True
    assert (
        file_watcher.should_ignore_file("/path/node_modules/pkg/file.js", ignore_patterns) == True
    )
    assert file_watcher.should_ignore_file("/path/__pycache__/module.pyc", ignore_patterns) == True
    assert file_watcher.should_ignore_file("/path/src/main.py", ignore_patterns) == False


def test_detect_file_changes(file_watcher, temp_dir):
    """Test detecting file creation"""
    test_file = os.path.join(temp_dir, "test.md")

    # Create file
    with open(test_file, "w") as f:
        f.write("Test content")

    # Simulate file event
    event = FileChangeEvent(event_type="created", file_path=test_file, is_directory=False)

    assert event.event_type == "created"
    assert event.file_path == test_file
    assert event.is_directory == False


def test_debounce_rapid_changes(file_watcher):
    """Test debouncing rapid file changes"""
    from datetime import datetime, timedelta

    file_path = "/path/test.md"

    # Record first change
    file_watcher._last_processed[file_path] = datetime.now()

    # Immediate second change should be debounced
    should_process = file_watcher.should_debounce(file_path, debounce_seconds=2)

    assert should_process == False

    # Change after debounce period should be processed
    file_watcher._last_processed[file_path] = datetime.now() - timedelta(seconds=3)
    should_process = file_watcher.should_debounce(file_path, debounce_seconds=2)

    assert should_process == True


# Security Tests


def test_path_traversal_rejected(file_watcher, temp_dir):
    """Test that path traversal attempts are rejected"""
    # Create a directory structure that simulates path traversal
    # We'll create: temp_dir/safe/subdir and try to traverse to /etc
    safe_dir = os.path.join(temp_dir, "safe")
    os.makedirs(safe_dir)

    # Attempt path traversal to /etc (which exists on most systems)
    # The validation should reject this because it resolves to /etc
    traversal_path = os.path.join(safe_dir, "..", "..", "..", "..", "etc")

    # Should reject because it resolves to a blocked path
    # Note: This test assumes /etc exists on the system
    with pytest.raises(ValueError, match="(Access denied|Path does not exist)"):
        file_watcher._validate_watch_path(traversal_path)


def test_absolute_system_path_rejected(file_watcher):
    """Test that system directories cannot be watched"""
    from app.services.file_watcher_service import BLOCKED_PATH_PREFIXES

    # Test only paths that exist on the system
    tested_at_least_one = False
    for blocked_path in BLOCKED_PATH_PREFIXES:
        if os.path.exists(blocked_path):
            tested_at_least_one = True
            with pytest.raises(ValueError, match="Access denied"):
                file_watcher._validate_watch_path(blocked_path)

    # If no blocked paths exist, create a test to verify the logic works
    if not tested_at_least_one:
        # At minimum, test that /etc would be blocked (common path)
        # We'll use a mock to simulate its existence
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_dir", return_value=True):
                with patch("pathlib.Path.resolve", return_value=Path("/etc")):
                    with pytest.raises(ValueError, match="Access denied"):
                        file_watcher._validate_watch_path("/etc")


def test_nonexistent_path_rejected(file_watcher, temp_dir):
    """Test that nonexistent paths are rejected"""
    nonexistent_path = os.path.join(temp_dir, "nonexistent", "directory")

    with pytest.raises(ValueError, match="Path does not exist"):
        file_watcher._validate_watch_path(nonexistent_path)


def test_file_instead_of_directory_rejected(file_watcher, temp_dir):
    """Test that files cannot be watched (only directories)"""
    # Create a file
    test_file = os.path.join(temp_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("test")

    with pytest.raises(ValueError, match="Path is not a directory"):
        file_watcher._validate_watch_path(test_file)


def test_valid_path_accepted(file_watcher, temp_dir):
    """Test that valid directory paths are accepted"""
    # Create a safe directory
    safe_dir = os.path.join(temp_dir, "safe_directory")
    os.makedirs(safe_dir)

    # Should not raise an exception
    validated_path = file_watcher._validate_watch_path(safe_dir)

    assert validated_path == str(Path(safe_dir).resolve())


def test_oversized_file_rejected(file_watcher, temp_dir):
    """Test that files exceeding size limit are rejected"""
    # Create a file
    large_file = os.path.join(temp_dir, "large_file.txt")

    # Create a 200MB file (larger than 100MB limit)
    with open(large_file, "wb") as f:
        f.write(b"0" * (200 * 1024 * 1024))

    # Should raise ValueError
    with pytest.raises(ValueError, match="File too large"):
        file_watcher._validate_file_size(large_file)


def test_file_size_validation_in_extract(file_watcher, temp_dir):
    """Test that file size is validated during extraction"""
    # Create a large file
    large_file = os.path.join(temp_dir, "large.md")

    # Create a 200MB file
    with open(large_file, "wb") as f:
        f.write(b"0" * (200 * 1024 * 1024))

    # Should return empty string (error logged)
    content = file_watcher.extract_text_from_file(large_file)

    assert content == ""


def test_file_size_configurable(temp_dir):
    """Test that file size limits can be configured"""
    # Create file watcher with 1MB limit
    file_watcher = FileWatcherService(max_file_size_bytes=1024 * 1024)

    # Create a 2MB file
    large_file = os.path.join(temp_dir, "large_file.txt")
    with open(large_file, "wb") as f:
        f.write(b"0" * (2 * 1024 * 1024))

    # Should be rejected with custom limit
    with pytest.raises(ValueError, match="File too large"):
        file_watcher._validate_file_size(large_file)


def test_normal_size_file_accepted(file_watcher, temp_dir):
    """Test that normal-sized files pass validation"""
    # Create a small file
    normal_file = os.path.join(temp_dir, "normal.txt")
    with open(normal_file, "w") as f:
        f.write("This is a normal sized file")

    # Should not raise an exception
    file_watcher._validate_file_size(normal_file)
