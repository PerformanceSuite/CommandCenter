"""
Integration tests for file watcher ingestion
"""
import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.models.ingestion_source import IngestionSource, SourceType
from app.models.project import Project
from app.services.file_watcher_service import FileChangeEvent
from app.tasks.ingestion_tasks import process_file_change


@pytest.fixture
def temp_watch_dir():
    """Create temporary directory for file watching"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def file_watcher_source(
    db_session: Session, sample_project: Project, temp_watch_dir: str
) -> IngestionSource:
    """Create a file watcher ingestion source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.FILE_WATCHER,
        name="Research Documents",
        path=temp_watch_dir,
        priority=7,
        enabled=True,
        config={"patterns": ["*.pdf", "*.md", "*.txt"], "ignore": [".git", "__pycache__"]},
    )
    db_session.add(source)
    db_session.commit()
    return source


def test_process_new_markdown_file(
    db_session: Session, file_watcher_source: IngestionSource, temp_watch_dir: str
):
    """Test processing newly created Markdown file"""
    # Create test file
    md_file = os.path.join(temp_watch_dir, "notes.md")
    with open(md_file, "w") as f:
        f.write("# Research Notes\n\nImportant findings about the topic...")

    # Simulate file change event
    event = FileChangeEvent(event_type="created", file_path=md_file, is_directory=False)

    result = process_file_change(file_watcher_source.id, event)

    assert result["status"] == "success"
    assert result["documents_ingested"] == 1

    # Verify source updated
    db_session.refresh(file_watcher_source)
    assert file_watcher_source.documents_ingested == 1


def test_process_pdf_file(
    db_session: Session, file_watcher_source: IngestionSource, temp_watch_dir: str
):
    """Test processing PDF file"""
    from unittest.mock import MagicMock, patch

    pdf_file = os.path.join(temp_watch_dir, "paper.pdf")
    Path(pdf_file).touch()  # Create empty file

    # Mock PDF extraction
    with patch(
        "app.services.file_watcher_service.FileWatcherService.extract_text_from_file",
        return_value="PDF content extracted",
    ):
        event = FileChangeEvent(event_type="created", file_path=pdf_file, is_directory=False)

        result = process_file_change(file_watcher_source.id, event)

    assert result["status"] == "success"


def test_ignore_non_matching_files(file_watcher_source: IngestionSource, temp_watch_dir: str):
    """Test that non-matching files are ignored"""
    # Create file that doesn't match patterns
    img_file = os.path.join(temp_watch_dir, "image.png")
    Path(img_file).touch()

    event = FileChangeEvent(event_type="created", file_path=img_file, is_directory=False)

    result = process_file_change(file_watcher_source.id, event)

    assert result["status"] == "skipped"
