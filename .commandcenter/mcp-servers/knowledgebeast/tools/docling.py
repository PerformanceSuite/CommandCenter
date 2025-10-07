"""
Docling Document Processing Tools

Integration with Docling for advanced document processing.
Supports multiple document formats with intelligent content extraction.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import mimetypes

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.rag_service import RAGService


class DoclingProcessor:
    """
    Docling document processing for KnowledgeBeast

    Provides advanced document processing with support for:
    - PDF documents (via Docling)
    - Microsoft Word (.docx)
    - Markdown (.md)
    - Plain text (.txt)
    - Code files (multiple languages)
    - Batch processing
    """

    def __init__(self, rag_service: RAGService):
        """
        Initialize Docling processor

        Args:
            rag_service: RAG service instance
        """
        self.rag_service = rag_service

        # Lazy import docling (optional dependency)
        self._docling_available = False
        try:
            import docling
            self._docling_available = True
        except ImportError:
            pass

    def _is_docling_available(self) -> bool:
        """Check if Docling is available"""
        return self._docling_available

    async def process_document(
        self,
        file_path: str,
        category: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a document using appropriate handler

        Args:
            file_path: Path to document
            category: Document category
            metadata: Additional metadata

        Returns:
            Processing result
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine file type and process accordingly
        extension = file_path_obj.suffix.lower()

        if extension == ".pdf":
            return await self._process_pdf(file_path_obj, category, metadata)
        elif extension == ".docx":
            return await self._process_docx(file_path_obj, category, metadata)
        elif extension in [".md", ".markdown"]:
            return await self._process_markdown(file_path_obj, category, metadata)
        elif extension in [".txt", ".text"]:
            return await self._process_text(file_path_obj, category, metadata)
        elif extension in [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"]:
            return await self._process_code(file_path_obj, category, metadata)
        else:
            # Try generic text processing
            return await self._process_text(file_path_obj, category, metadata)

    async def _process_pdf(
        self,
        file_path: Path,
        category: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process PDF document using Docling

        Args:
            file_path: Path to PDF file
            category: Category
            metadata: Additional metadata

        Returns:
            Processing result
        """
        if not self._is_docling_available():
            return {
                "success": False,
                "error": "Docling not installed. Install with: pip install docling"
            }

        try:
            from docling.document_converter import DocumentConverter

            # Convert PDF to markdown using Docling
            converter = DocumentConverter()
            result = converter.convert(str(file_path))

            # Extract text content
            content = result.document.export_to_markdown()

            # Prepare metadata
            doc_metadata = metadata or {}
            doc_metadata["source"] = str(file_path)
            doc_metadata["filename"] = file_path.name
            doc_metadata["type"] = "pdf"
            if category:
                doc_metadata["category"] = category

            # Add to knowledge base
            chunks_added = await self.rag_service.add_document(
                content=content,
                metadata=doc_metadata
            )

            return {
                "success": True,
                "file": str(file_path),
                "type": "pdf",
                "chunks_added": chunks_added,
                "processor": "docling"
            }

        except Exception as e:
            return {
                "success": False,
                "file": str(file_path),
                "error": str(e)
            }

    async def _process_docx(
        self,
        file_path: Path,
        category: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process Microsoft Word document

        Args:
            file_path: Path to DOCX file
            category: Category
            metadata: Additional metadata

        Returns:
            Processing result
        """
        try:
            import docx2txt

            # Extract text from DOCX
            content = docx2txt.process(str(file_path))

            # Prepare metadata
            doc_metadata = metadata or {}
            doc_metadata["source"] = str(file_path)
            doc_metadata["filename"] = file_path.name
            doc_metadata["type"] = "docx"
            if category:
                doc_metadata["category"] = category

            # Add to knowledge base
            chunks_added = await self.rag_service.add_document(
                content=content,
                metadata=doc_metadata
            )

            return {
                "success": True,
                "file": str(file_path),
                "type": "docx",
                "chunks_added": chunks_added,
                "processor": "docx2txt"
            }

        except ImportError:
            # Fallback: try to read as text
            return await self._process_text(file_path, category, metadata)
        except Exception as e:
            return {
                "success": False,
                "file": str(file_path),
                "error": str(e)
            }

    async def _process_markdown(
        self,
        file_path: Path,
        category: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process Markdown document

        Args:
            file_path: Path to Markdown file
            category: Category
            metadata: Additional metadata

        Returns:
            Processing result
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # Prepare metadata
            doc_metadata = metadata or {}
            doc_metadata["source"] = str(file_path)
            doc_metadata["filename"] = file_path.name
            doc_metadata["type"] = "markdown"
            if category:
                doc_metadata["category"] = category

            # Extract title from first heading if present
            lines = content.split("\n")
            for line in lines:
                if line.startswith("# "):
                    doc_metadata["title"] = line[2:].strip()
                    break

            # Add to knowledge base
            chunks_added = await self.rag_service.add_document(
                content=content,
                metadata=doc_metadata
            )

            return {
                "success": True,
                "file": str(file_path),
                "type": "markdown",
                "chunks_added": chunks_added,
                "processor": "native"
            }

        except Exception as e:
            return {
                "success": False,
                "file": str(file_path),
                "error": str(e)
            }

    async def _process_text(
        self,
        file_path: Path,
        category: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process plain text document

        Args:
            file_path: Path to text file
            category: Category
            metadata: Additional metadata

        Returns:
            Processing result
        """
        try:
            # Try UTF-8 first
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Fallback to latin-1
                content = file_path.read_text(encoding="latin-1")

            # Prepare metadata
            doc_metadata = metadata or {}
            doc_metadata["source"] = str(file_path)
            doc_metadata["filename"] = file_path.name
            doc_metadata["type"] = "text"
            if category:
                doc_metadata["category"] = category

            # Add to knowledge base
            chunks_added = await self.rag_service.add_document(
                content=content,
                metadata=doc_metadata
            )

            return {
                "success": True,
                "file": str(file_path),
                "type": "text",
                "chunks_added": chunks_added,
                "processor": "native"
            }

        except Exception as e:
            return {
                "success": False,
                "file": str(file_path),
                "error": str(e)
            }

    async def _process_code(
        self,
        file_path: Path,
        category: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process code file

        Args:
            file_path: Path to code file
            category: Category
            metadata: Additional metadata

        Returns:
            Processing result
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # Prepare metadata
            doc_metadata = metadata or {}
            doc_metadata["source"] = str(file_path)
            doc_metadata["filename"] = file_path.name
            doc_metadata["type"] = "code"
            doc_metadata["language"] = file_path.suffix[1:]  # Remove dot
            if category:
                doc_metadata["category"] = category
            else:
                doc_metadata["category"] = "code"

            # Add to knowledge base
            chunks_added = await self.rag_service.add_document(
                content=content,
                metadata=doc_metadata
            )

            return {
                "success": True,
                "file": str(file_path),
                "type": "code",
                "language": doc_metadata["language"],
                "chunks_added": chunks_added,
                "processor": "native"
            }

        except Exception as e:
            return {
                "success": False,
                "file": str(file_path),
                "error": str(e)
            }

    async def batch_process(
        self,
        file_paths: List[str],
        category: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process multiple documents in batch

        Args:
            file_paths: List of file paths
            category: Category for all documents
            metadata: Additional metadata for all documents

        Returns:
            Batch processing results
        """
        results = {
            "total_files": len(file_paths),
            "successful": 0,
            "failed": 0,
            "total_chunks": 0,
            "files": []
        }

        for file_path in file_paths:
            try:
                result = await self.process_document(file_path, category, metadata)

                if result.get("success"):
                    results["successful"] += 1
                    results["total_chunks"] += result.get("chunks_added", 0)
                else:
                    results["failed"] += 1

                results["files"].append(result)

            except Exception as e:
                results["failed"] += 1
                results["files"].append({
                    "success": False,
                    "file": file_path,
                    "error": str(e)
                })

        return results

    async def extract_metadata(
        self,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Extract metadata from a document without ingesting

        Args:
            file_path: Path to document

        Returns:
            Extracted metadata
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        metadata = {
            "filename": file_path_obj.name,
            "extension": file_path_obj.suffix,
            "size_bytes": file_path_obj.stat().st_size,
            "modified": file_path_obj.stat().st_mtime,
            "mime_type": mimetypes.guess_type(str(file_path_obj))[0]
        }

        # Try to extract additional metadata based on type
        extension = file_path_obj.suffix.lower()

        if extension == ".md":
            try:
                content = file_path_obj.read_text(encoding="utf-8")
                lines = content.split("\n")
                for line in lines:
                    if line.startswith("# "):
                        metadata["title"] = line[2:].strip()
                        break
            except Exception:
                pass

        return metadata
