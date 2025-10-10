"""
Docling Integration Service
Processes various document formats (PDF, Markdown, text) into clean text for RAG
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import tempfile
import os

# Lazy imports - only import when DoclingService is instantiated
try:
    from docling.document_converter import DocumentConverter, PipelineOptions

    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    DocumentConverter = None
    PipelineOptions = None


class DoclingService:
    """Service for processing documents using Docling"""

    def __init__(self):
        """
        Initialize Docling service

        Raises:
            ImportError: If Docling is not installed
        """
        if not DOCLING_AVAILABLE:
            raise ImportError(
                "Docling not installed. " "Install with: pip install docling"
            )

        # Initialize document converter with default options
        # Docling v1.20.0 API simplified - no need for format-specific options
        self.converter = DocumentConverter()

    async def process_pdf(self, content: bytes) -> str:
        """
        Process PDF file and extract text

        Args:
            content: PDF file content as bytes

        Returns:
            Extracted and cleaned text content
        """
        # Create temporary file for PDF processing
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Convert PDF to document
            result = self.converter.convert(tmp_path)

            # Extract text from all pages
            text_content = []

            # Get document structure
            if hasattr(result, "document") and result.document:
                doc = result.document

                # Extract text from document body
                if hasattr(doc, "export_to_markdown"):
                    # Use markdown export for better structure preservation
                    text_content.append(doc.export_to_markdown())
                elif hasattr(doc, "export_to_text"):
                    text_content.append(doc.export_to_text())
                else:
                    # Fallback: extract from pages
                    for page in doc.pages:
                        if hasattr(page, "text"):
                            text_content.append(page.text)

            # Join all text content
            full_text = "\n\n".join(text_content)

            # Clean up extracted text
            full_text = self._clean_text(full_text)

            return full_text

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    async def process_markdown(self, content: str) -> str:
        """
        Process Markdown file

        Args:
            content: Markdown content as string

        Returns:
            Cleaned markdown text
        """
        # For markdown, we mostly just clean it up
        # Docling can also parse markdown but for simple cases, cleaning is sufficient
        return self._clean_text(content)

    async def process_text(self, content: str) -> str:
        """
        Process plain text file

        Args:
            content: Text content as string

        Returns:
            Cleaned text
        """
        return self._clean_text(content)

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content

        Args:
            text: Raw text content

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            # Strip whitespace from each line
            line = line.strip()

            # Skip empty lines but preserve paragraph breaks
            if line or (cleaned_lines and cleaned_lines[-1]):
                cleaned_lines.append(line)

        # Join lines with single newlines
        cleaned_text = "\n".join(cleaned_lines)

        # Replace multiple consecutive newlines with double newline (paragraph break)
        import re

        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

        # Remove common PDF artifacts
        cleaned_text = re.sub(r"\x0c", "", cleaned_text)  # Form feed
        cleaned_text = re.sub(
            r"[\x00-\x08\x0b-\x0c\x0e-\x1f]", "", cleaned_text
        )  # Control chars

        return cleaned_text.strip()

    async def extract_metadata(self, content: bytes, file_type: str) -> Dict[str, Any]:
        """
        Extract metadata from document

        Args:
            content: File content as bytes
            file_type: File extension/type

        Returns:
            Document metadata
        """
        metadata = {
            "file_size": len(content),
            "file_type": file_type,
        }

        if file_type.lower() == "pdf":
            # Create temporary file for metadata extraction
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name

            try:
                # Convert and extract metadata
                result = self.converter.convert(tmp_path)

                if hasattr(result, "document") and result.document:
                    doc = result.document

                    # Extract available metadata
                    if hasattr(doc, "metadata"):
                        doc_metadata = doc.metadata
                        if hasattr(doc_metadata, "title"):
                            metadata["title"] = doc_metadata.title
                        if hasattr(doc_metadata, "author"):
                            metadata["author"] = doc_metadata.author
                        if hasattr(doc_metadata, "creation_date"):
                            metadata["creation_date"] = str(doc_metadata.creation_date)

                    # Page count
                    if hasattr(doc, "pages"):
                        metadata["page_count"] = len(doc.pages)

            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        return metadata

    async def process_with_chunking(
        self,
        content: bytes,
        file_type: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        Process document and return chunks with metadata

        Args:
            content: File content as bytes
            file_type: File extension/type
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks

        Returns:
            List of chunks with metadata
        """
        # Process document based on type
        if file_type.lower() == "pdf":
            text_content = await self.process_pdf(content)
        elif file_type.lower() in ["md", "markdown"]:
            text_content = await self.process_markdown(content.decode("utf-8"))
        else:
            text_content = await self.process_text(content.decode("utf-8"))

        # Extract metadata
        metadata = await self.extract_metadata(content, file_type)

        # Simple chunking (can be enhanced with langchain text splitter)
        chunks = []
        text_length = len(text_content)

        for i in range(0, text_length, chunk_size - chunk_overlap):
            chunk_text = text_content[i : i + chunk_size]

            chunk_metadata = metadata.copy()
            chunk_metadata.update(
                {
                    "chunk_index": len(chunks),
                    "chunk_start": i,
                    "chunk_end": min(i + chunk_size, text_length),
                }
            )

            chunks.append({"content": chunk_text, "metadata": chunk_metadata})

        return chunks
