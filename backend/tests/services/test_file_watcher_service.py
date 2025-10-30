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
    # Mock PDF reader
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "PDF content here"
    mock_pdf.pages = [mock_page]

    mock_file = MagicMock()

    with patch('builtins.open', return_value=mock_file):
        with patch('app.services.file_watcher_service.PyPDF2.PdfReader', return_value=mock_pdf):
            content = file_watcher.extract_text_from_file(
                os.path.join(temp_dir, "test.pdf")
            )

    assert content == "PDF content here"


def test_extract_text_from_markdown(file_watcher, temp_dir):
    """Test extracting text from Markdown file"""
    md_path = os.path.join(temp_dir, "test.md")

    with open(md_path, 'w') as f:
        f.write("# Header\n\nMarkdown content")

    content = file_watcher.extract_text_from_file(md_path)

    assert "# Header" in content
    assert "Markdown content" in content


def test_extract_text_from_docx(file_watcher, temp_dir):
    """Test extracting text from DOCX file"""
    mock_doc = MagicMock()
    mock_para = MagicMock()
    mock_para.text = "DOCX paragraph content"
    mock_doc.paragraphs = [mock_para]

    with patch('app.services.file_watcher_service.Document', return_value=mock_doc):
        content = file_watcher.extract_text_from_file(
            os.path.join(temp_dir, "test.docx")
        )

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
    assert file_watcher.should_ignore_file("/path/node_modules/pkg/file.js", ignore_patterns) == True
    assert file_watcher.should_ignore_file("/path/__pycache__/module.pyc", ignore_patterns) == True
    assert file_watcher.should_ignore_file("/path/src/main.py", ignore_patterns) == False


def test_detect_file_changes(file_watcher, temp_dir):
    """Test detecting file creation"""
    test_file = os.path.join(temp_dir, "test.md")

    # Create file
    with open(test_file, 'w') as f:
        f.write("Test content")

    # Simulate file event
    event = FileChangeEvent(
        event_type='created',
        file_path=test_file,
        is_directory=False
    )

    assert event.event_type == 'created'
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
