# KnowledgeBeast v3.0 Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace ChromaDB-based RAG service with KnowledgeBeast v3.0 PostgresBackend for unified database architecture.

**Architecture:** Wrap KnowledgeBeast's PostgresBackend in existing RAGService interface. Use Dagger to build custom Postgres image with pgvector extension. Multi-tenant collections using `commandcenter_{repository_id}` naming pattern.

**Tech Stack:** KnowledgeBeast v3.0, PostgresBackend, pgvector, Dagger, FastAPI, asyncpg

---

## Task 1: Update Backend Dependencies

**Files:**
- Modify: `backend/requirements.txt`

**Step 1: Write test for KnowledgeBeast availability**

Create: `backend/tests/test_dependencies.py`

```python
"""Test that required dependencies are available."""
import pytest


def test_knowledgebeast_available():
    """Test that KnowledgeBeast can be imported."""
    try:
        from knowledgebeast.backends.postgres import PostgresBackend
        assert PostgresBackend is not None
    except ImportError as e:
        pytest.fail(f"KnowledgeBeast not available: {e}")


def test_dagger_available():
    """Test that Dagger can be imported."""
    try:
        import dagger
        assert dagger is not None
    except ImportError as e:
        pytest.fail(f"Dagger not available: {e}")
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_dependencies.py -v`
Expected: FAIL with "No module named 'knowledgebeast'"

**Step 3: Update requirements.txt**

Modify: `backend/requirements.txt`

Remove these lines:
```
chromadb>=0.4.0,<0.5.0
langchain-chroma>=0.1.0,<0.2.0
```

Add these lines after the RAG section:
```
# KnowledgeBeast v3.0 for RAG
knowledgebeast>=3.0.0  # PostgresBackend with pgvector
dagger-io>=0.9.0       # For building custom Postgres image
```

**Step 4: Install dependencies**

Run: `cd backend && pip install -r requirements.txt`
Expected: KnowledgeBeast and dagger-io install successfully

**Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_dependencies.py -v`
Expected: 2 PASSED

**Step 6: Commit**

```bash
git add backend/requirements.txt backend/tests/test_dependencies.py
git commit -m "deps: Replace ChromaDB with KnowledgeBeast v3.0

- Remove: chromadb, langchain-chroma
- Add: knowledgebeast>=3.0.0, dagger-io>=0.9.0
- Add dependency availability tests

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Create Dagger Postgres Module

**Files:**
- Create: `backend/dagger_modules/__init__.py`
- Create: `backend/dagger_modules/postgres.py`
- Create: `backend/tests/dagger_modules/__init__.py`
- Create: `backend/tests/dagger_modules/test_postgres.py`

**Step 1: Write test for Dagger module**

Create: `backend/tests/dagger_modules/__init__.py` (empty file)

Create: `backend/tests/dagger_modules/test_postgres.py`

```python
"""Test Postgres Dagger module."""
import pytest


def test_postgres_config_dataclass():
    """Test PostgresConfig dataclass."""
    from backend.dagger_modules.postgres import PostgresConfig

    config = PostgresConfig(
        db_name="test",
        db_password="testpass",
        postgres_version="16",
        pgvector_version="v0.7.0"
    )

    assert config.db_name == "test"
    assert config.db_password == "testpass"
    assert config.postgres_version == "16"
    assert config.pgvector_version == "v0.7.0"


def test_postgres_stack_initialization():
    """Test PostgresStack can be initialized."""
    from backend.dagger_modules.postgres import PostgresStack, PostgresConfig

    config = PostgresConfig()
    stack = PostgresStack(config)

    assert stack.config == config
    assert stack._connection is None
    assert stack.client is None
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/dagger_modules/test_postgres.py -v`
Expected: FAIL with "No module named 'backend.dagger_modules.postgres'"

**Step 3: Create Dagger module**

Create: `backend/dagger_modules/__init__.py` (empty file)

Create: `backend/dagger_modules/postgres.py`

```python
"""Dagger module for building custom Postgres with pgvector."""
from dataclasses import dataclass
from typing import Optional

import dagger


@dataclass
class PostgresConfig:
    """Configuration for custom Postgres with pgvector."""
    db_name: str = "commandcenter"
    db_password: str = "changeme"
    postgres_version: str = "16"
    pgvector_version: str = "v0.7.0"


class PostgresStack:
    """Dagger stack for custom Postgres with pgvector extension."""

    def __init__(self, config: PostgresConfig):
        """Initialize Postgres stack.

        Args:
            config: PostgresConfig instance
        """
        self.config = config
        self._connection: Optional[dagger.Connection] = None
        self.client = None

    async def __aenter__(self):
        """Initialize Dagger client (async context manager entry)."""
        self._connection = dagger.Connection(dagger.Config())
        self.client = await self._connection.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup Dagger client (async context manager exit)."""
        if self._connection:
            await self._connection.__aexit__(exc_type, exc_val, exc_tb)

    async def build_postgres(self) -> dagger.Container:
        """Build Postgres container with pgvector extension.

        Returns:
            Dagger container with Postgres + pgvector
        """
        if not self.client:
            raise RuntimeError("Dagger client not initialized. Use async with context manager.")

        return (
            self.client.container()
            .from_(f"postgres:{self.config.postgres_version}")

            # Install build dependencies
            .with_exec(["apt-get", "update"])
            .with_exec([
                "apt-get", "install", "-y",
                "build-essential",
                f"postgresql-server-dev-{self.config.postgres_version}",
                "git"
            ])

            # Install pgvector
            .with_exec([
                "git", "clone", "--branch", self.config.pgvector_version,
                "https://github.com/pgvector/pgvector.git", "/tmp/pgvector"
            ])
            .with_workdir("/tmp/pgvector")
            .with_exec(["make"])
            .with_exec(["make", "install"])

            # Configure Postgres
            .with_env_variable("POSTGRES_DB", self.config.db_name)
            .with_env_variable("POSTGRES_PASSWORD", self.config.db_password)
            .with_exposed_port(5432)
        )
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/dagger_modules/test_postgres.py -v`
Expected: 2 PASSED

**Step 5: Commit**

```bash
git add backend/dagger_modules/ backend/tests/dagger_modules/
git commit -m "feat(dagger): Add Postgres builder with pgvector

- PostgresConfig dataclass for configuration
- PostgresStack for building custom Postgres image
- Includes pgvector v0.7.0 extension
- Async context manager support

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Add Configuration Settings

**Files:**
- Modify: `backend/app/config.py`
- Create: `backend/tests/test_config.py`

**Step 1: Write test for new config settings**

Create: `backend/tests/test_config.py`

```python
"""Test configuration settings."""
from app.config import settings


def test_embedding_model_config():
    """Test embedding model configuration."""
    assert hasattr(settings, 'EMBEDDING_MODEL')
    assert settings.EMBEDDING_MODEL == "all-MiniLM-L6-v2"


def test_embedding_dimension_config():
    """Test embedding dimension configuration."""
    assert hasattr(settings, 'EMBEDDING_DIMENSION')
    assert settings.EMBEDDING_DIMENSION == 384


def test_knowledge_collection_prefix():
    """Test knowledge collection prefix."""
    assert hasattr(settings, 'KNOWLEDGE_COLLECTION_PREFIX')
    assert settings.KNOWLEDGE_COLLECTION_PREFIX == "commandcenter"


def test_kb_pool_config():
    """Test KnowledgeBeast connection pool configuration."""
    assert hasattr(settings, 'KB_POOL_MIN_SIZE')
    assert hasattr(settings, 'KB_POOL_MAX_SIZE')
    assert settings.KB_POOL_MIN_SIZE == 2
    assert settings.KB_POOL_MAX_SIZE == 10
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_config.py -v`
Expected: FAIL with AttributeError for missing settings

**Step 3: Update config.py**

Modify: `backend/app/config.py`

Add after the database settings section:

```python
    # Knowledge base settings (KnowledgeBeast v3.0)
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    KNOWLEDGE_COLLECTION_PREFIX: str = "commandcenter"

    # Connection pool settings for KnowledgeBeast PostgresBackend
    KB_POOL_MIN_SIZE: int = 2
    KB_POOL_MAX_SIZE: int = 10
    KB_POOL_TIMEOUT: int = 30
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_config.py -v`
Expected: 4 PASSED

**Step 5: Commit**

```bash
git add backend/app/config.py backend/tests/test_config.py
git commit -m "feat(config): Add KnowledgeBeast configuration settings

- EMBEDDING_MODEL: all-MiniLM-L6-v2 (384 dimensions)
- KNOWLEDGE_COLLECTION_PREFIX: commandcenter
- KB_POOL_MIN_SIZE/MAX_SIZE: Connection pool settings
- Add configuration tests

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Rewrite RAG Service (Part 1: Initialization)

**Files:**
- Modify: `backend/app/services/rag_service.py`
- Create: `backend/tests/services/test_rag_service_init.py`

**Step 1: Write test for RAGService initialization**

Create: `backend/tests/services/test_rag_service_init.py`

```python
"""Test RAGService initialization with KnowledgeBeast."""
import pytest


@pytest.mark.asyncio
async def test_rag_service_creates_backend():
    """Test that RAGService creates PostgresBackend instance."""
    from app.services.rag_service import RAGService

    service = RAGService(repository_id=1)

    assert service.repository_id == 1
    assert service.collection_name == "commandcenter_1"
    assert service.backend is not None
    assert not service._initialized


@pytest.mark.asyncio
async def test_rag_service_initialize():
    """Test RAGService initialization."""
    from app.services.rag_service import RAGService
    from unittest.mock import AsyncMock, patch

    service = RAGService(repository_id=1)

    # Mock backend.initialize
    service.backend.initialize = AsyncMock()

    await service.initialize()

    assert service._initialized
    service.backend.initialize.assert_called_once()


@pytest.mark.asyncio
async def test_rag_service_collection_naming():
    """Test collection naming for multi-tenancy."""
    from app.services.rag_service import RAGService

    service1 = RAGService(repository_id=1)
    service2 = RAGService(repository_id=42)

    assert service1.collection_name == "commandcenter_1"
    assert service2.collection_name == "commandcenter_42"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/services/test_rag_service_init.py -v`
Expected: FAIL - old RAGService doesn't have these attributes

**Step 3: Backup old RAGService**

Run: `cd backend/app/services && cp rag_service.py rag_service.py.bak`

**Step 4: Rewrite RAGService (initialization only)**

Modify: `backend/app/services/rag_service.py`

Replace entire file with:

```python
"""RAG service using KnowledgeBeast v3.0 PostgresBackend.

This service wraps KnowledgeBeast's PostgresBackend to provide
knowledge base functionality with unified Postgres database.
"""

from typing import List, Dict, Any, Optional

from knowledgebeast.backends.postgres import PostgresBackend
from app.config import settings


class RAGService:
    """Service for knowledge base RAG operations using KnowledgeBeast."""

    def __init__(self, repository_id: int):
        """Initialize RAG service for a specific repository.

        Args:
            repository_id: Repository ID for multi-tenant isolation
        """
        self.repository_id = repository_id
        self.collection_name = f"{settings.KNOWLEDGE_COLLECTION_PREFIX}_{repository_id}"

        # Initialize KnowledgeBeast PostgresBackend
        self.backend = PostgresBackend(
            connection_string=settings.DATABASE_URL,
            collection_name=self.collection_name,
            embedding_dimension=settings.EMBEDDING_DIMENSION,
            pool_size=settings.KB_POOL_MAX_SIZE,
            pool_min_size=settings.KB_POOL_MIN_SIZE,
        )
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize backend (creates schema if needed)."""
        if not self._initialized:
            await self.backend.initialize()
            self._initialized = True

    async def close(self) -> None:
        """Close backend connection."""
        if self._initialized:
            await self.backend.close()
            self._initialized = False

    # Placeholder methods - will implement in next tasks
    async def query(self, question: str, category: Optional[str] = None, k: int = 5) -> List[Dict[str, Any]]:
        """Query the knowledge base (not yet implemented)."""
        raise NotImplementedError("To be implemented in next task")

    async def add_document(self, content: str, metadata: Dict[str, Any], chunk_size: int = 1000) -> int:
        """Add document (not yet implemented)."""
        raise NotImplementedError("To be implemented in next task")

    async def delete_by_source(self, source: str) -> bool:
        """Delete by source (not yet implemented)."""
        raise NotImplementedError("To be implemented in next task")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics (not yet implemented)."""
        raise NotImplementedError("To be implemented in next task")
```

**Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/services/test_rag_service_init.py -v`
Expected: 3 PASSED

**Step 6: Commit**

```bash
git add backend/app/services/rag_service.py backend/tests/services/test_rag_service_init.py
git commit -m "refactor(rag): Rewrite RAGService initialization for KnowledgeBeast

- Use PostgresBackend instead of ChromaDB
- Multi-tenant collection naming: commandcenter_{repo_id}
- Async initialization support
- Placeholder methods for remaining functionality

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Implement RAG Service Query Method

**Files:**
- Modify: `backend/app/services/rag_service.py`
- Create: `backend/tests/services/test_rag_service_query.py`

**Step 1: Write test for query method**

Create: `backend/tests/services/test_rag_service_query.py`

```python
"""Test RAGService query functionality."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_query_calls_backend_hybrid_search():
    """Test that query uses hybrid search."""
    from app.services.rag_service import RAGService

    service = RAGService(repository_id=1)
    service._initialized = True

    # Mock backend and embedding
    service.backend.query_hybrid = AsyncMock(return_value=[
        ("doc1", 0.95, {"source": "test.md", "category": "docs"}),
        ("doc2", 0.85, {"source": "test2.md", "category": "docs"})
    ])

    with patch('app.services.rag_service.embed_text') as mock_embed:
        mock_embed.return_value = [0.1] * 384

        results = await service.query("test question", k=5)

        # Verify embedding was generated
        mock_embed.assert_called_once_with("test question", model_name="all-MiniLM-L6-v2")

        # Verify backend was called
        service.backend.query_hybrid.assert_called_once()
        call_args = service.backend.query_hybrid.call_args
        assert call_args.kwargs['query_text'] == "test question"
        assert call_args.kwargs['top_k'] == 5
        assert call_args.kwargs['alpha'] == 0.7


@pytest.mark.asyncio
async def test_query_with_category_filter():
    """Test query with category filtering."""
    from app.services.rag_service import RAGService

    service = RAGService(repository_id=1)
    service._initialized = True

    service.backend.query_hybrid = AsyncMock(return_value=[])

    with patch('app.services.rag_service.embed_text') as mock_embed:
        mock_embed.return_value = [0.1] * 384

        await service.query("test", category="docs", k=3)

        call_args = service.backend.query_hybrid.call_args
        assert call_args.kwargs['where'] == {"category": "docs"}


@pytest.mark.asyncio
async def test_query_auto_initializes():
    """Test that query auto-initializes if needed."""
    from app.services.rag_service import RAGService

    service = RAGService(repository_id=1)
    assert not service._initialized

    service.backend.initialize = AsyncMock()
    service.backend.query_hybrid = AsyncMock(return_value=[])

    with patch('app.services.rag_service.embed_text') as mock_embed:
        mock_embed.return_value = [0.1] * 384

        await service.query("test")

        service.backend.initialize.assert_called_once()
        assert service._initialized
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/services/test_rag_service_query.py -v`
Expected: FAIL - NotImplementedError or mock issues

**Step 3: Implement query method**

Modify: `backend/app/services/rag_service.py`

Add this import at the top:
```python
from knowledgebeast import embed_text
```

Replace the query method placeholder:
```python
    async def query(
        self,
        question: str,
        category: Optional[str] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Query the knowledge base using hybrid search.

        Args:
            question: Natural language question
            category: Filter by category (optional)
            k: Number of results to return

        Returns:
            List of relevant document chunks with metadata
        """
        if not self._initialized:
            await self.initialize()

        # Build metadata filter
        where = {"category": category} if category else None

        # Generate query embedding
        query_embedding = await embed_text(
            question,
            model_name=settings.EMBEDDING_MODEL
        )

        # Use hybrid search (vector + keyword)
        results = await self.backend.query_hybrid(
            query_embedding=query_embedding,
            query_text=question,
            top_k=k,
            alpha=0.7,  # 70% vector, 30% keyword
            where=where
        )

        # Format results to match existing API
        return [
            {
                "id": doc_id,
                "score": float(score),
                "metadata": metadata,
                "category": metadata.get("category", "unknown"),
                "source": metadata.get("source", "unknown"),
            }
            for doc_id, score, metadata in results
        ]
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/services/test_rag_service_query.py -v`
Expected: 3 PASSED

**Step 5: Commit**

```bash
git add backend/app/services/rag_service.py backend/tests/services/test_rag_service_query.py
git commit -m "feat(rag): Implement query method with hybrid search

- Generate embeddings using KnowledgeBeast embed_text
- Use hybrid search (70% vector, 30% keyword)
- Support category filtering via metadata
- Auto-initialize if needed
- Add comprehensive tests

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Implement Remaining RAG Service Methods

**Files:**
- Modify: `backend/app/services/rag_service.py`
- Create: `backend/tests/services/test_rag_service_methods.py`

**Step 1: Write tests for remaining methods**

Create: `backend/tests/services/test_rag_service_methods.py`

```python
"""Test RAGService add_document, delete_by_source, get_statistics."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_add_document_chunks_and_embeds():
    """Test add_document chunks text and generates embeddings."""
    from app.services.rag_service import RAGService

    service = RAGService(repository_id=1)
    service._initialized = True
    service.backend.add_documents = AsyncMock()

    with patch('app.services.rag_service.embed_texts') as mock_embed:
        mock_embed.return_value = [[0.1] * 384, [0.2] * 384]

        chunks_added = await service.add_document(
            content="This is a test document. It has multiple sentences.",
            metadata={"source": "test.md", "category": "docs"},
            chunk_size=50
        )

        # Should create chunks
        assert chunks_added >= 1

        # Should call embed_texts
        mock_embed.assert_called_once()

        # Should call backend.add_documents
        service.backend.add_documents.assert_called_once()


@pytest.mark.asyncio
async def test_delete_by_source():
    """Test delete_by_source calls backend correctly."""
    from app.services.rag_service import RAGService

    service = RAGService(repository_id=1)
    service._initialized = True
    service.backend.delete_documents = AsyncMock(return_value=5)

    result = await service.delete_by_source("test.md")

    assert result is True
    service.backend.delete_documents.assert_called_once_with(
        where={"source": "test.md"}
    )


@pytest.mark.asyncio
async def test_delete_by_source_no_documents():
    """Test delete_by_source returns False when nothing deleted."""
    from app.services.rag_service import RAGService

    service = RAGService(repository_id=1)
    service._initialized = True
    service.backend.delete_documents = AsyncMock(return_value=0)

    result = await service.delete_by_source("nonexistent.md")

    assert result is False


@pytest.mark.asyncio
async def test_get_statistics():
    """Test get_statistics returns backend stats."""
    from app.services.rag_service import RAGService

    service = RAGService(repository_id=1)
    service._initialized = True
    service.backend.get_statistics = AsyncMock(return_value={
        "document_count": 42,
        "collection_name": "commandcenter_1",
        "embedding_dimension": 384,
        "backend_type": "postgres"
    })

    stats = await service.get_statistics()

    assert stats["total_chunks"] == 42
    assert stats["backend"] == "postgres"
    assert stats["collection_name"] == "commandcenter_1"
    assert stats["embedding_model"] == "all-MiniLM-L6-v2"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/services/test_rag_service_methods.py -v`
Expected: FAIL - NotImplementedError

**Step 3: Implement remaining methods**

Modify: `backend/app/services/rag_service.py`

Add import:
```python
from knowledgebeast import embed_texts
from langchain.text_splitter import RecursiveCharacterTextSplitter
```

Replace placeholder methods:

```python
    async def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_size: int = 1000
    ) -> int:
        """Add a document to the knowledge base.

        Args:
            content: Document content
            metadata: Document metadata
            chunk_size: Size of text chunks

        Returns:
            Number of chunks added
        """
        if not self._initialized:
            await self.initialize()

        # Split into chunks using LangChain
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = text_splitter.split_text(content)

        if not chunks:
            return 0

        # Generate embeddings for all chunks
        embeddings = await embed_texts(chunks, model_name=settings.EMBEDDING_MODEL)

        # Prepare for bulk insert
        source = metadata.get('source', 'unknown')
        ids = [f"{source}_{i}" for i in range(len(chunks))]
        metadatas = [metadata.copy() for _ in chunks]

        # Add to backend
        await self.backend.add_documents(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )

        return len(chunks)

    async def delete_by_source(self, source: str) -> bool:
        """Delete documents by source file.

        Args:
            source: Source file path

        Returns:
            True if documents were deleted
        """
        if not self._initialized:
            await self.initialize()

        # Delete using metadata filter
        count = await self.backend.delete_documents(
            where={"source": source}
        )

        return count > 0

    async def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics.

        Returns:
            Statistics dictionary
        """
        if not self._initialized:
            await self.initialize()

        stats = await self.backend.get_statistics()

        return {
            "total_chunks": stats["document_count"],
            "backend": "postgres",
            "collection_name": self.collection_name,
            "embedding_model": settings.EMBEDDING_MODEL,
            "embedding_dimension": settings.EMBEDDING_DIMENSION,
        }
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/services/test_rag_service_methods.py -v`
Expected: 4 PASSED

**Step 5: Commit**

```bash
git add backend/app/services/rag_service.py backend/tests/services/test_rag_service_methods.py
git commit -m "feat(rag): Implement add_document, delete, and statistics

- add_document: Chunks text, generates embeddings, bulk insert
- delete_by_source: Delete by metadata filter
- get_statistics: Return backend stats in expected format
- Use LangChain for text splitting
- Add comprehensive tests for all methods

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: Update Docker Compose for Dagger Postgres

**Files:**
- Create: `backend/scripts/build-postgres.py`
- Modify: `docker-compose.yml`
- Create: `backend/Dockerfile.postgres`

**Step 1: Create Dagger build script**

Create: `backend/scripts/build-postgres.py`

```python
#!/usr/bin/env python3
"""Build custom Postgres image with pgvector using Dagger."""
import asyncio
import sys
from pathlib import Path

# Add dagger_modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "dagger_modules"))

from postgres import PostgresStack, PostgresConfig


async def main():
    """Build and export Postgres image with pgvector."""
    print("Building custom Postgres image with pgvector...")

    config = PostgresConfig(
        db_name="commandcenter",
        db_password="postgres",  # Will be overridden by .env
        postgres_version="16",
        pgvector_version="v0.7.0"
    )

    async with PostgresStack(config) as stack:
        print("Building container...")
        container = await stack.build_postgres()

        print("Exporting to Docker...")
        # Export as tar for local Docker import
        await container.export("./postgres-pgvector.tar")

        print("✅ Postgres image built and exported to postgres-pgvector.tar")
        print("\nTo use:")
        print("  docker load < postgres-pgvector.tar")
        print("  docker-compose up -d postgres")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Build failed: {e}", file=sys.stderr)
        sys.exit(1)
```

**Step 2: Make script executable**

Run: `chmod +x backend/scripts/build-postgres.py`

**Step 3: Create Dockerfile for reference**

Create: `backend/Dockerfile.postgres`

```dockerfile
# Custom Postgres with pgvector
# Built by Dagger - see backend/scripts/build-postgres.py
# This Dockerfile is for documentation only

FROM postgres:16

# Install build dependencies
RUN apt-get update && \
    apt-get install -y build-essential postgresql-server-dev-16 git && \
    rm -rf /var/lib/apt/lists/*

# Install pgvector v0.7.0
RUN git clone --branch v0.7.0 https://github.com/pgvector/pgvector.git /tmp/pgvector && \
    cd /tmp/pgvector && \
    make && \
    make install && \
    rm -rf /tmp/pgvector

# Note: Actual image is built by Dagger for reproducibility
```

**Step 4: Update docker-compose.yml**

Modify: `docker-compose.yml`

Find the postgres service and update it:

```yaml
  postgres:
    # Custom Postgres with pgvector extension
    # Build with: python backend/scripts/build-postgres.py
    # Or use pre-built image: commandcenter-postgres:latest
    image: commandcenter-postgres:latest
    build:
      context: ./backend
      dockerfile: Dockerfile.postgres
    environment:
      POSTGRES_DB: commandcenter
      POSTGRES_USER: commandcenter
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U commandcenter"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - commandcenter
```

**Step 5: Test Dagger build script (dry run)**

Run: `cd backend && python scripts/build-postgres.py --help 2>&1 || echo "Script exists"`
Expected: Script runs (may fail if Docker not running, that's OK for now)

**Step 6: Commit**

```bash
git add backend/scripts/build-postgres.py backend/Dockerfile.postgres docker-compose.yml
chmod +x backend/scripts/build-postgres.py
git commit -m "feat(docker): Add Dagger-based Postgres build with pgvector

- Dagger build script: backend/scripts/build-postgres.py
- Dockerfile for reference: backend/Dockerfile.postgres
- Update docker-compose to use custom Postgres image
- Builds Postgres 16 + pgvector v0.7.0

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 8: Integration Test with Real Postgres

**Files:**
- Create: `backend/tests/integration/test_rag_integration.py`

**Step 1: Write integration test**

Create: `backend/tests/integration/__init__.py` (empty file)

Create: `backend/tests/integration/test_rag_integration.py`

```python
"""Integration test for RAGService with real Postgres via Dagger."""
import pytest
import sys
from pathlib import Path

# Add dagger_modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dagger_modules"))

from postgres import PostgresStack, PostgresConfig


@pytest.mark.asyncio
@pytest.mark.integration
async def test_rag_service_with_real_postgres():
    """Test RAGService against real Postgres with pgvector (via Dagger)."""
    from app.services.rag_service import RAGService
    from app.config import settings

    # Create test Postgres with Dagger
    config = PostgresConfig(
        db_name="test_kb",
        db_password="testpass"
    )

    async with PostgresStack(config) as stack:
        # Wait for Postgres to be ready
        import asyncio
        await asyncio.sleep(2)

        # Create service pointing to Dagger Postgres
        # Note: This requires Dagger Postgres to be accessible
        # In CI, this would use the Dagger-managed container

        service = RAGService(repository_id=1)

        # Override connection string for test
        original_db_url = settings.DATABASE_URL
        settings.DATABASE_URL = f"postgresql://postgres:testpass@localhost:5432/test_kb"
        service.backend.connection_string = settings.DATABASE_URL

        try:
            # Initialize
            await service.initialize()

            # Add document
            chunks = await service.add_document(
                content="This is a test document about Python programming.",
                metadata={"source": "test.md", "category": "docs"}
            )
            assert chunks > 0

            # Query
            results = await service.query("Python programming", k=5)
            assert len(results) > 0
            assert results[0]["category"] == "docs"

            # Statistics
            stats = await service.get_statistics()
            assert stats["total_chunks"] >= chunks
            assert stats["backend"] == "postgres"

            # Delete
            deleted = await service.delete_by_source("test.md")
            assert deleted is True

            # Verify deletion
            stats_after = await service.get_statistics()
            assert stats_after["total_chunks"] == 0

        finally:
            # Cleanup
            await service.close()
            settings.DATABASE_URL = original_db_url


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multi_tenant_isolation():
    """Test that different repositories have isolated collections."""
    from app.services.rag_service import RAGService

    service1 = RAGService(repository_id=1)
    service2 = RAGService(repository_id=2)

    # Collections should be different
    assert service1.collection_name == "commandcenter_1"
    assert service2.collection_name == "commandcenter_2"
    assert service1.collection_name != service2.collection_name
```

**Step 2: Add pytest marker configuration**

Create/modify: `backend/pytest.ini`

```ini
[pytest]
markers =
    integration: Integration tests requiring real infrastructure (Dagger)
    asyncio: Async test support

# Run integration tests with: pytest -m integration
# Skip integration tests with: pytest -m "not integration"
```

**Step 3: Run integration test**

Run: `cd backend && pytest tests/integration/test_rag_integration.py -m integration -v`
Expected: May skip if Dagger not available, but test structure is valid

**Step 4: Commit**

```bash
git add backend/tests/integration/ backend/pytest.ini
git commit -m "test(rag): Add integration tests with real Postgres

- Full RAGService workflow test via Dagger Postgres
- Multi-tenant isolation verification
- Add pytest integration marker
- Tests: add, query, stats, delete operations

Run with: pytest -m integration

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 9: Update API Router Tests

**Files:**
- Modify: `backend/tests/routers/test_knowledge.py` (if exists)

**Step 1: Check if router tests exist**

Run: `ls -la backend/tests/routers/test_knowledge.py 2>&1 || echo "No existing router tests"`

**Step 2: If tests exist, update them**

If `backend/tests/routers/test_knowledge.py` exists, update imports and mocks to use new RAGService.

If not, create minimal router test:

Create: `backend/tests/routers/__init__.py` (empty if doesn't exist)

Create: `backend/tests/routers/test_knowledge.py`

```python
"""Test knowledge base router endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


@pytest.fixture
def mock_rag_service():
    """Mock RAGService for router tests."""
    with patch('app.routers.knowledge.RAGService') as mock:
        instance = mock.return_value
        instance.initialize = AsyncMock()
        instance.query = AsyncMock(return_value=[
            {
                "id": "doc1",
                "score": 0.95,
                "metadata": {"source": "test.md"},
                "category": "docs",
                "source": "test.md"
            }
        ])
        instance.add_document = AsyncMock(return_value=5)
        instance.delete_by_source = AsyncMock(return_value=True)
        instance.get_statistics = AsyncMock(return_value={
            "total_chunks": 42,
            "backend": "postgres",
            "collection_name": "commandcenter_1"
        })
        instance.close = AsyncMock()
        yield instance


def test_query_endpoint_uses_rag_service(client: TestClient, mock_rag_service):
    """Test /api/v1/knowledge/query endpoint."""
    response = client.post(
        "/api/v1/knowledge/query",
        json={"question": "test query", "k": 5}
    )

    assert response.status_code == 200
    assert len(response.json()) > 0


def test_statistics_endpoint(client: TestClient, mock_rag_service):
    """Test /api/v1/knowledge/statistics endpoint."""
    response = client.get("/api/v1/knowledge/statistics")

    assert response.status_code == 200
    data = response.json()
    assert data["backend"] == "postgres"
    assert "total_chunks" in data
```

**Step 3: Run router tests**

Run: `cd backend && pytest tests/routers/test_knowledge.py -v`
Expected: PASS (using mocks)

**Step 4: Commit**

```bash
git add backend/tests/routers/
git commit -m "test(api): Update knowledge router tests for new RAGService

- Mock new RAGService methods
- Test query, statistics endpoints
- Verify PostgresBackend integration

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 10: Update Documentation

**Files:**
- Modify: `CLAUDE.md`
- Modify: `backend/README.md`
- Create: `docs/KNOWLEDGEBEAST_INTEGRATION.md`

**Step 1: Update CLAUDE.md**

Modify: `CLAUDE.md`

Find the RAGService section and update:

```markdown
**RAGService** (`app/services/rag_service.py`):
- KnowledgeBeast v3.0 PostgresBackend for unified database
- Vector search via pgvector (HNSW indexes)
- Full-text search via PostgreSQL ts_vector
- Hybrid search using Reciprocal Rank Fusion (RRF)
- Multi-tenant collections: commandcenter_{repository_id}
- Methods: `query()`, `add_document()`, `get_statistics()`
- **Dependencies**: `pip install knowledgebeast>=3.0.0`
```

**Step 2: Update backend README**

Modify: `backend/README.md`

Add section about KnowledgeBeast integration (or update existing RAG section):

```markdown
## Knowledge Base (KnowledgeBeast v3.0)

CommandCenter uses KnowledgeBeast v3.0 PostgresBackend for RAG functionality.

**Features:**
- Unified database: All data in PostgreSQL (no separate vector store)
- Vector search: pgvector with HNSW indexes
- Full-text search: PostgreSQL ts_vector
- Hybrid search: Reciprocal Rank Fusion (70% vector, 30% keyword)
- Multi-tenancy: Separate collections per repository

**Setup:**

1. Build custom Postgres image with pgvector:
   ```bash
   python backend/scripts/build-postgres.py
   docker load < postgres-pgvector.tar
   ```

2. Start services:
   ```bash
   docker-compose up -d
   ```

3. Verify pgvector extension:
   ```bash
   docker-compose exec postgres psql -U commandcenter -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

**Configuration:**

See `backend/app/config.py`:
- `EMBEDDING_MODEL`: all-MiniLM-L6-v2 (384 dimensions)
- `KB_POOL_MAX_SIZE`: 10 connections
- `KNOWLEDGE_COLLECTION_PREFIX`: commandcenter

**Testing:**

```bash
# Unit tests
pytest tests/services/test_rag_service*.py

# Integration tests (requires Dagger + Docker)
pytest -m integration tests/integration/test_rag_integration.py
```
```

**Step 3: Create integration documentation**

Create: `docs/KNOWLEDGEBEAST_INTEGRATION.md`

```markdown
# KnowledgeBeast v3.0 Integration Guide

**Status:** ✅ Integrated (2025-10-26)

## Overview

CommandCenter uses KnowledgeBeast v3.0 PostgresBackend to provide unified database architecture for all data, including vector embeddings.

**Previous Architecture:** ChromaDB (separate service)
**Current Architecture:** KnowledgeBeast PostgresBackend (unified Postgres)

## Benefits

- ✅ Unified database: repos, technologies, research, AND knowledge vectors
- ✅ Better performance: HNSW indexes (faster than IVFFlat)
- ✅ Production-ready: ACID transactions, backups, replication
- ✅ Simpler deployment: No separate ChromaDB service
- ✅ Multi-tenancy: Collection per repository (commandcenter_{repo_id})

## Architecture

```
┌─────────────────────────────────────┐
│   CommandCenter Backend             │
│                                     │
│   RAGService → KnowledgeBeast       │
│                PostgresBackend      │
│                    ↓                │
│   ┌─────────────────────────────┐  │
│   │   PostgreSQL Database       │  │
│   │   - Repos, Tech, Research   │  │
│   │   - Knowledge Vectors       │  │
│   │   - pgvector extension      │  │
│   └─────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Database Schema

KnowledgeBeast automatically creates tables:

```sql
-- Per repository collection
CREATE TABLE commandcenter_{repo_id}_documents (
    id TEXT PRIMARY KEY,
    embedding vector(384),
    document TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- HNSW index for vector similarity
CREATE INDEX ... USING hnsw (embedding vector_cosine_ops);

-- GIN indexes for full-text and metadata
CREATE INDEX ... USING gin (to_tsvector('english', document));
CREATE INDEX ... USING gin (metadata);
```

## Setup

### 1. Build Custom Postgres Image

```bash
cd backend
python scripts/build-postgres.py
docker load < postgres-pgvector.tar
```

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Verify Extension

```bash
docker-compose exec postgres psql -U commandcenter -c "\\dx"
```

Should show `vector` extension.

## API Usage

No changes to API endpoints - transparent upgrade:

```bash
# Query knowledge base
curl -X POST http://localhost:8000/api/v1/knowledge/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I setup authentication?", "k": 5}'

# Add document
curl -X POST http://localhost:8000/api/v1/knowledge/documents \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Authentication setup guide...",
    "metadata": {"source": "docs/auth.md", "category": "docs"}
  }'

# Get statistics
curl http://localhost:8000/api/v1/knowledge/statistics
```

## Configuration

See `.env`:

```bash
# KnowledgeBeast settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
KNOWLEDGE_COLLECTION_PREFIX=commandcenter

# Connection pool
KB_POOL_MIN_SIZE=2
KB_POOL_MAX_SIZE=10
```

## Migration from ChromaDB

No migration needed for fresh installations.

If migrating existing ChromaDB data:
1. Export via LangChain API
2. Re-import through `/api/v1/knowledge/documents`
3. Verify document counts match

## Troubleshooting

**Issue:** `pgvector` extension not found

**Solution:**
```bash
# Rebuild Postgres image
python backend/scripts/build-postgres.py
docker-compose down -v
docker-compose up -d
```

**Issue:** Connection pool exhausted

**Solution:** Increase `KB_POOL_MAX_SIZE` in `.env`

**Issue:** Slow queries

**Solution:** Check index usage:
```sql
EXPLAIN ANALYZE
SELECT id FROM commandcenter_1_documents
ORDER BY embedding <=> '[...]' LIMIT 10;
```

## References

- Design: `docs/plans/2025-10-26-knowledgebeast-integration-design.md`
- KnowledgeBeast: https://github.com/user/knowledgebeast
- pgvector: https://github.com/pgvector/pgvector
```

**Step 4: Commit**

```bash
git add CLAUDE.md backend/README.md docs/KNOWLEDGEBEAST_INTEGRATION.md
git commit -m "docs: Update documentation for KnowledgeBeast integration

- Update CLAUDE.md RAGService description
- Add KnowledgeBeast setup to backend README
- Create comprehensive integration guide
- Include setup, API usage, troubleshooting

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 11: Final Verification

**Files:**
- Create: `backend/tests/test_full_integration.py`

**Step 1: Create full integration verification test**

Create: `backend/tests/test_full_integration.py`

```python
"""Full integration verification test."""
import pytest


def test_all_dependencies_available():
    """Verify all required dependencies are installed."""
    # KnowledgeBeast
    from knowledgebeast.backends.postgres import PostgresBackend
    from knowledgebeast import embed_text, embed_texts

    # Dagger
    import dagger

    # LangChain (still used for chunking)
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    # Standard libraries
    import asyncpg

    assert PostgresBackend is not None
    assert embed_text is not None
    assert dagger is not None


def test_config_has_kb_settings():
    """Verify configuration has KnowledgeBeast settings."""
    from app.config import settings

    assert hasattr(settings, 'EMBEDDING_MODEL')
    assert hasattr(settings, 'EMBEDDING_DIMENSION')
    assert hasattr(settings, 'KNOWLEDGE_COLLECTION_PREFIX')
    assert hasattr(settings, 'KB_POOL_MAX_SIZE')


def test_rag_service_imports():
    """Verify RAGService can be imported and instantiated."""
    from app.services.rag_service import RAGService

    service = RAGService(repository_id=1)
    assert service is not None
    assert service.collection_name == "commandcenter_1"


def test_dagger_module_imports():
    """Verify Dagger module can be imported."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent / "dagger_modules"))

    from postgres import PostgresStack, PostgresConfig

    config = PostgresConfig()
    stack = PostgresStack(config)

    assert config is not None
    assert stack is not None


@pytest.mark.asyncio
async def test_rag_service_lifecycle():
    """Test RAGService initialization and cleanup."""
    from app.services.rag_service import RAGService
    from unittest.mock import AsyncMock

    service = RAGService(repository_id=1)

    # Mock backend
    service.backend.initialize = AsyncMock()
    service.backend.close = AsyncMock()

    # Initialize
    await service.initialize()
    assert service._initialized
    service.backend.initialize.assert_called_once()

    # Close
    await service.close()
    assert not service._initialized
    service.backend.close.assert_called_once()


def test_backward_compatibility():
    """Verify API surface matches old RAGService."""
    from app.services.rag_service import RAGService
    import inspect

    service = RAGService(repository_id=1)

    # Check required methods exist
    assert hasattr(service, 'query')
    assert hasattr(service, 'add_document')
    assert hasattr(service, 'delete_by_source')
    assert hasattr(service, 'get_statistics')
    assert hasattr(service, 'initialize')
    assert hasattr(service, 'close')

    # Check methods are async
    assert inspect.iscoroutinefunction(service.query)
    assert inspect.iscoroutinefunction(service.add_document)
    assert inspect.iscoroutinefunction(service.delete_by_source)
    assert inspect.iscoroutinefunction(service.get_statistics)
```

**Step 2: Run all tests**

Run: `cd backend && pytest tests/test_full_integration.py -v`
Expected: All tests PASS

**Step 3: Run full test suite**

Run: `cd backend && pytest tests/ -v --ignore=tests/integration`
Expected: All unit tests PASS (skip integration tests for speed)

**Step 4: Commit**

```bash
git add backend/tests/test_full_integration.py
git commit -m "test: Add final integration verification tests

- Verify all dependencies available
- Test RAGService lifecycle
- Check backward compatibility
- Validate configuration settings
- Run with: pytest tests/test_full_integration.py

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Summary

**Total Tasks:** 11
**Estimated Time:** 2-3 hours (with TDD)
**Commits:** 11 atomic commits

**Verification Steps:**

1. All tests pass: `pytest tests/ -v --ignore=tests/integration`
2. Dagger build works: `python backend/scripts/build-postgres.py`
3. Docker Compose starts: `docker-compose up -d`
4. API responds: `curl http://localhost:8000/api/v1/knowledge/statistics`

**Next Steps After Implementation:**

1. Build and push Postgres image to registry
2. Run integration tests with real Postgres
3. Performance benchmarking vs ChromaDB
4. Update production deployment docs

---

**Plan complete and saved to `docs/plans/2025-10-26-knowledgebeast-integration.md`.**
