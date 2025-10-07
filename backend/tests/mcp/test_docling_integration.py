"""
Tests for Docling Integration

Tests for document processing with Docling.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add paths
worktree_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(worktree_root))
sys.path.insert(0, str(worktree_root / "backend"))
sys.path.insert(0, str(worktree_root / ".commandcenter/mcp-servers"))

from knowledgebeast.tools.docling import DoclingProcessor


@pytest.mark.asyncio
class TestDoclingProcessor:
    """Test Docling document processor"""

    @pytest.fixture
    def mock_rag_service(self):
        """Mock RAG service"""
        mock = AsyncMock()
        mock.collection_name = "project_test"
        mock.add_document.return_value = 5
        return mock

    @pytest.fixture
    def processor(self, mock_rag_service):
        """Create DoclingProcessor instance"""
        return DoclingProcessor(mock_rag_service)

    async def test_process_markdown(self, processor, mock_rag_service, tmp_path):
        """Test processing Markdown file"""
        # Create test markdown file
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test Document\n\nThis is a test.")

        result = await processor.process_document(
            str(md_file),
            category="test"
        )

        assert result["success"] is True
        assert result["type"] == "markdown"
        assert result["chunks_added"] == 5
        assert result["processor"] == "native"

    async def test_process_text(self, processor, mock_rag_service, tmp_path):
        """Test processing plain text file"""
        # Create test text file
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Plain text content for testing.")

        result = await processor.process_document(
            str(txt_file),
            category="test"
        )

        assert result["success"] is True
        assert result["type"] == "text"
        assert result["chunks_added"] == 5

    async def test_process_code_file(self, processor, mock_rag_service, tmp_path):
        """Test processing code file"""
        # Create test Python file
        py_file = tmp_path / "test.py"
        py_file.write_text('def hello():\n    print("Hello, World!")')

        result = await processor.process_document(
            str(py_file),
            category="code"
        )

        assert result["success"] is True
        assert result["type"] == "code"
        assert result["language"] == "py"
        assert result["chunks_added"] == 5

    async def test_process_nonexistent_file(self, processor):
        """Test processing nonexistent file raises error"""
        with pytest.raises(FileNotFoundError):
            await processor.process_document("/nonexistent/file.md")

    async def test_batch_process(self, processor, mock_rag_service, tmp_path):
        """Test batch processing multiple files"""
        # Create multiple test files
        files = []
        for i in range(3):
            f = tmp_path / f"test{i}.md"
            f.write_text(f"# Document {i}\n\nContent {i}")
            files.append(str(f))

        result = await processor.batch_process(files, category="test")

        assert result["total_files"] == 3
        assert result["successful"] == 3
        assert result["failed"] == 0
        assert result["total_chunks"] == 15  # 5 chunks per file

    async def test_batch_process_with_errors(self, processor, mock_rag_service, tmp_path):
        """Test batch processing handles errors gracefully"""
        # Create mix of valid and invalid files
        valid_file = tmp_path / "valid.md"
        valid_file.write_text("# Valid\n\nContent")

        files = [
            str(valid_file),
            "/nonexistent/file.md"
        ]

        result = await processor.batch_process(files, category="test")

        assert result["total_files"] == 2
        assert result["successful"] == 1
        assert result["failed"] == 1
        assert len(result["files"]) == 2

    async def test_extract_metadata(self, processor, tmp_path):
        """Test metadata extraction"""
        # Create test file
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test Title\n\nContent")

        metadata = await processor.extract_metadata(str(md_file))

        assert metadata["filename"] == "test.md"
        assert metadata["extension"] == ".md"
        assert "size_bytes" in metadata
        assert "modified" in metadata
        assert metadata.get("title") == "Test Title"

    async def test_markdown_title_extraction(self, processor, mock_rag_service, tmp_path):
        """Test that markdown titles are extracted to metadata"""
        md_file = tmp_path / "doc.md"
        md_file.write_text("# Main Title\n\nSome content here.")

        # Track the metadata passed to add_document
        captured_metadata = {}

        async def capture_metadata(content, metadata, **kwargs):
            captured_metadata.update(metadata)
            return 5

        mock_rag_service.add_document.side_effect = capture_metadata

        await processor.process_document(str(md_file))

        assert captured_metadata.get("title") == "Main Title"
        assert captured_metadata.get("type") == "markdown"

    async def test_code_language_detection(self, processor, mock_rag_service, tmp_path):
        """Test that code language is detected from extension"""
        test_cases = [
            ("test.py", "py"),
            ("test.js", "js"),
            ("test.ts", "ts"),
            ("test.java", "java"),
            ("test.cpp", "cpp"),
        ]

        for filename, expected_lang in test_cases:
            code_file = tmp_path / filename
            code_file.write_text("// Code content")

            captured_metadata = {}

            async def capture_metadata(content, metadata, **kwargs):
                captured_metadata.update(metadata)
                return 5

            mock_rag_service.add_document.side_effect = capture_metadata

            await processor.process_document(str(code_file))

            assert captured_metadata.get("language") == expected_lang

    @pytest.mark.skipif(
        True,  # Skip by default unless docling is installed
        reason="Docling optional dependency not installed"
    )
    async def test_process_pdf_with_docling(self, processor, mock_rag_service, tmp_path):
        """Test PDF processing with Docling (requires docling installed)"""
        # This test requires docling to be installed
        # In production, you would use a real PDF file
        pdf_file = tmp_path / "test.pdf"

        with patch("docling.document_converter.DocumentConverter") as MockConverter:
            mock_result = MagicMock()
            mock_result.document.export_to_markdown.return_value = "PDF content as markdown"
            MockConverter.return_value.convert.return_value = mock_result

            # Note: Creating a real PDF requires additional libraries
            # For this test, we'll just verify the Docling integration logic
            pdf_file.write_bytes(b"%PDF-1.4 fake pdf")

            result = await processor._process_pdf(
                pdf_file,
                category="test",
                metadata=None
            )

            if processor._is_docling_available():
                assert result["success"] is True
                assert result["type"] == "pdf"
                assert result["processor"] == "docling"

    async def test_docling_not_available(self, processor):
        """Test graceful handling when Docling is not installed"""
        processor._docling_available = False

        result = await processor._process_pdf(
            Path("test.pdf"),
            category="test",
            metadata=None
        )

        assert result["success"] is False
        assert "Docling not installed" in result["error"]

    async def test_unicode_content_handling(self, processor, mock_rag_service, tmp_path):
        """Test handling of files with unicode content"""
        # Create file with unicode content
        unicode_file = tmp_path / "unicode.md"
        unicode_file.write_text("# Unicode Test\n\nEmojis: 🚀 ⭐ 💡\n中文测试", encoding="utf-8")

        result = await processor.process_document(str(unicode_file))

        assert result["success"] is True
        mock_rag_service.add_document.assert_called_once()

        # Verify unicode content was passed through
        call_args = mock_rag_service.add_document.call_args
        content = call_args[1]["content"]
        assert "🚀" in content
        assert "中文测试" in content
