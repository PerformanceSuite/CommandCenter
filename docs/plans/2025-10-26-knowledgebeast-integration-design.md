# KnowledgeBeast v3.0 Integration into CommandCenter

**Date:** 2025-10-26
**Author:** Design Session (Brainstorming Skill)
**Status:** Approved - Ready for Implementation
**Version:** 1.0

---

## Executive Summary

Replace CommandCenter's current ChromaDB-based RAG service with KnowledgeBeast v3.0 PostgresBackend, providing unified database architecture, better performance, and production-grade vector search capabilities.

**Key Benefits:**
- ✅ Unified database: All data (repos, tech, research, knowledge) in one Postgres instance
- ✅ Better performance: HNSW indexes, native Postgres full-text search
- ✅ Production-ready: ACID transactions, backups, replication
- ✅ No ChromaDB service: Simpler deployment, lower memory footprint
- ✅ Future-proof: Leverages ongoing KnowledgeBeast improvements

---

## Approach: Full Replacement

**Selected Strategy:** Clean replacement of existing RAG service with KnowledgeBeast PostgresBackend.

**Rationale:**
- CommandCenter likely has minimal/no existing ChromaDB data
- Simpler codebase (single implementation path)
- No configuration complexity (vs. multi-backend approach)
- Leverages all KnowledgeBeast v3.0 improvements immediately

**Trade-offs Accepted:**
- Breaking change: Any existing ChromaDB data will not be migrated (acceptable - likely none exists)
- All-in commitment: No fallback to ChromaDB (acceptable - KnowledgeBeast v3.0 is production-ready)

---

## Architecture

### Current State (v2.x)

```
┌─────────────────────────────────────┐
│       CommandCenter Backend         │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  app/services/rag_service.py │  │
│  │  - Direct ChromaDB usage     │  │
│  │  - HuggingFace embeddings    │  │
│  │  - LangChain wrappers        │  │
│  └──────────────────────────────┘  │
│           │                         │
│           ▼                         │
│  ┌──────────────────────────────┐  │
│  │     ChromaDB Service         │  │
│  │  (Separate vector store)     │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘

Postgres: Repos, Technologies, Research
ChromaDB: Knowledge base (separate service)
```

### Target State (v3.0)

```
┌─────────────────────────────────────────────┐
│         CommandCenter Backend               │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  app/services/rag_service.py         │  │
│  │  - Uses KnowledgeBeast               │  │
│  │  - PostgresBackend                   │  │
│  │  - Same API surface                  │  │
│  └──────────────────────────────────────┘  │
│           │                                 │
│           ▼                                 │
│  ┌──────────────────────────────────────┐  │
│  │   KnowledgeBeast v3.0                │  │
│  │   PostgresBackend                    │  │
│  └──────────────────────────────────────┘  │
│           │                                 │
│           ▼                                 │
│  ┌──────────────────────────────────────┐  │
│  │   PostgreSQL Database                │  │
│  │   - Repos, Tech, Research (existing) │  │
│  │   - Knowledge vectors (NEW!)         │  │
│  │   - pgvector extension               │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘

UNIFIED DATABASE: Everything in Postgres
```

---

## Database Schema

**Schema Automatically Created by KnowledgeBeast:**

KnowledgeBeast v3.0 PostgresBackend includes a production-ready schema template (`postgres_schema.sql`) that creates:

```sql
-- Per-collection documents table
-- Collection naming: commandcenter_{repository_id}
CREATE TABLE IF NOT EXISTS {collection_name}_documents (
    id TEXT PRIMARY KEY,
    embedding vector({embedding_dimension}),  -- 384 for all-MiniLM-L6-v2
    document TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HNSW index for fast vector similarity search
CREATE INDEX IF NOT EXISTS {collection_name}_embedding_idx
    ON {collection_name}_documents
    USING hnsw (embedding vector_cosine_ops);

-- GIN index for full-text search
CREATE INDEX IF NOT EXISTS {collection_name}_document_idx
    ON {collection_name}_documents
    USING gin (to_tsvector('english', document));

-- GIN index for metadata filtering
CREATE INDEX IF NOT EXISTS {collection_name}_metadata_idx
    ON {collection_name}_documents
    USING gin (metadata);

-- Auto-update trigger for updated_at
CREATE TRIGGER update_{collection_name}_updated_at
    BEFORE UPDATE ON {collection_name}_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Multi-tenancy Strategy:**
- Each CommandCenter repository gets its own collection: `commandcenter_{repo_id}_documents`
- Separate tables for data isolation
- All in same database (shared connection pool)

**Built-in Features:**
- ✅ HNSW indexes (faster than IVFFlat for typical dataset sizes)
- ✅ Audit columns (created_at, updated_at with auto-trigger)
- ✅ Metadata indexing (fast filtering by category, source, etc.)
- ✅ Full-text search indexes (GIN for PostgreSQL ts_vector)

---

## Dagger Integration

### Why Dagger?

PostgreSQL doesn't include pgvector by default. We need a custom Postgres image with the extension pre-installed.

**Dagger Benefits:**
- ✅ Reproducible builds across dev, test, prod
- ✅ Fast startup (extensions pre-compiled and cached)
- ✅ Can push image to registry for distribution
- ✅ Follows Universal Dagger Pattern (established in docs)
- ✅ Same approach used by KnowledgeBeast tests

### Dagger Module Structure

**New file:** `backend/dagger_modules/postgres.py`

```python
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
    """Dagger stack for custom Postgres with pgvector."""

    def __init__(self, config: PostgresConfig):
        self.config = config
        self._connection: Optional[dagger.Connection] = None
        self.client = None

    async def __aenter__(self):
        """Initialize Dagger client."""
        self._connection = dagger.Connection(dagger.Config())
        self.client = await self._connection.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup Dagger client."""
        if self._connection:
            await self._connection.__aexit__(exc_type, exc_val, exc_tb)

    async def build_postgres(self) -> dagger.Container:
        """Build Postgres with pgvector extension."""
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

**Build Script:** `backend/scripts/build-postgres.py`

```python
#!/usr/bin/env python3
"""Build custom Postgres image with pgvector using Dagger."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "dagger_modules"))

from postgres import PostgresStack, PostgresConfig


async def main():
    """Build and export Postgres image."""
    config = PostgresConfig()

    async with PostgresStack(config) as stack:
        container = await stack.build_postgres()

        # Export to Docker
        await container.export("./postgres-pgvector.tar")
        print("✅ Built and exported postgres-pgvector.tar")

        # Optional: Push to registry
        # await container.publish("registry.example.com/commandcenter-postgres:latest")


if __name__ == "__main__":
    asyncio.run(main())
```

### Docker Compose Integration

**Updated:** `docker-compose.yml`

```yaml
services:
  postgres:
    # Option 1: Use Dagger-built image (recommended)
    build:
      context: ./backend
      dockerfile: Dockerfile.postgres-dagger

    # Option 2: Pre-built image from registry
    # image: registry.example.com/commandcenter-postgres:latest

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
```

**New file:** `backend/Dockerfile.postgres-dagger`

```dockerfile
# Dagger-built Postgres with pgvector
# Build with: python backend/scripts/build-postgres.py
FROM postgres:16

# Copy pgvector extension (pre-compiled by Dagger)
COPY --from=pgvector /usr/share/postgresql/16/extension /usr/share/postgresql/16/extension
COPY --from=pgvector /usr/lib/postgresql/16/lib /usr/lib/postgresql/16/lib

# Note: Actual implementation will use Dagger SDK directly
# This Dockerfile is for reference - Dagger builds the image programmatically
```

---

## Implementation Changes

### 1. Dependencies (`backend/requirements.txt`)

**Remove:**
```
chromadb>=0.4.0,<0.5.0
langchain-chroma>=0.1.0,<0.2.0
```

**Add:**
```
knowledgebeast>=3.0.0  # Or git+https://github.com/user/knowledgebeast.git@v3.0.0
dagger-io>=0.9.0       # For building custom Postgres image
```

**Keep:**
```
sentence-transformers>=2.3.0,<3.0.0  # Used by KnowledgeBeast
langchain>=0.1.0,<0.2.0              # For document processing
langchain-community>=0.0.10,<0.1.0
```

### 2. Service Layer (`backend/app/services/rag_service.py`)

**Complete rewrite** - wrap KnowledgeBeast PostgresBackend:

```python
"""RAG service using KnowledgeBeast v3.0 PostgresBackend."""

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
        self.collection_name = f"commandcenter_{repository_id}"

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

    async def query(
        self,
        question: str,
        category: Optional[str] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Query the knowledge base.

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

        # Use hybrid search (vector + keyword)
        # Note: KnowledgeBeast handles embedding generation internally
        from knowledgebeast import embed_text
        query_embedding = await embed_text(
            question,
            model_name=settings.EMBEDDING_MODEL
        )

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
                "content": doc_id,  # Note: Need to fetch actual content
                "metadata": metadata,
                "score": float(score),
                "category": metadata.get("category", "unknown"),
                "source": metadata.get("source", "unknown"),
            }
            for doc_id, score, metadata in results
        ]

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

        # Use LangChain for chunking (existing behavior)
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = text_splitter.split_text(content)

        # Generate embeddings
        from knowledgebeast import embed_texts
        embeddings = await embed_texts(chunks, model_name=settings.EMBEDDING_MODEL)

        # Prepare for bulk insert
        ids = [f"{metadata.get('source', 'unknown')}_{i}" for i in range(len(chunks))]
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
            True if successful
        """
        if not self._initialized:
            await self.initialize()

        # Delete using metadata filter
        count = await self.backend.delete_documents(
            where={"source": source}
        )

        return count > 0

    async def get_categories(self) -> List[str]:
        """Get list of all categories in the knowledge base."""
        # Note: This requires custom query - not in VectorBackend interface
        # Could be added to KnowledgeBeast or implemented here
        pass

    async def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        if not self._initialized:
            await self.initialize()

        stats = await self.backend.get_statistics()

        return {
            "total_chunks": stats["document_count"],
            "categories": {},  # Would need custom query
            "embedding_model": settings.EMBEDDING_MODEL,
            "backend": "postgres",
            "collection_name": self.collection_name,
        }

    async def close(self):
        """Close backend connection."""
        if self._initialized:
            await self.backend.close()
            self._initialized = False
```

### 3. Configuration (`backend/app/config.py`)

**Add settings:**

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Knowledge base settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    KNOWLEDGE_COLLECTION_PREFIX: str = "commandcenter"

    # Connection pool settings for KnowledgeBeast
    KB_POOL_MIN_SIZE: int = 2
    KB_POOL_MAX_SIZE: int = 10
    KB_POOL_TIMEOUT: int = 30
```

### 4. API Routes (`backend/app/routers/knowledge.py`)

**No changes required** - existing endpoints remain the same, only the underlying service changes.

Endpoints:
- `POST /api/v1/knowledge/query` - Query knowledge base
- `POST /api/v1/knowledge/documents` - Add document
- `DELETE /api/v1/knowledge/documents` - Delete documents
- `GET /api/v1/knowledge/statistics` - Get statistics

---

## Migration Strategy

### Data Migration

**Decision:** No migration needed
- CommandCenter is early stage
- Likely no significant ChromaDB data exists
- Fresh start with Postgres provides clean state

**If data exists:**
1. Export from ChromaDB via LangChain
2. Re-index through KnowledgeBeast API
3. Verify document counts match

### Deployment Sequence

1. **Build Dagger Postgres image**
   ```bash
   python backend/scripts/build-postgres.py
   ```

2. **Update docker-compose**
   - Use Dagger-built Postgres image
   - Remove ChromaDB service

3. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Start services**
   ```bash
   docker-compose up -d
   ```

5. **Verify health**
   ```bash
   curl http://localhost:8000/api/v1/knowledge/statistics
   ```

### Rollback Plan

**If issues arise:**
1. Revert to git commit before integration
2. Restore ChromaDB docker-compose service
3. Restore old requirements.txt
4. Restart services

**Risk:** Low - KnowledgeBeast v3.0 is production-tested (87% coverage, 21/21 tests passing)

---

## Testing Strategy

### Unit Tests

Update existing tests in `backend/tests/services/test_rag_service.py`:

```python
import pytest
from app.services.rag_service import RAGService

@pytest.mark.asyncio
async def test_rag_service_initialization():
    """Test RAG service initializes correctly."""
    service = RAGService(repository_id=1)
    await service.initialize()

    stats = await service.get_statistics()
    assert stats["backend"] == "postgres"
    assert stats["collection_name"] == "commandcenter_1"

    await service.close()

@pytest.mark.asyncio
async def test_add_and_query_document():
    """Test adding and querying documents."""
    service = RAGService(repository_id=1)
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

    await service.close()
```

### Integration Tests

Test against real Postgres with pgvector (using Dagger):

```python
# backend/tests/integration/test_knowledgebeast_integration.py
import pytest
from tests.dagger_modules.postgres import PostgresStack, PostgresConfig

@pytest.mark.asyncio
async def test_full_integration_with_dagger():
    """Test RAG service against real Postgres."""
    config = PostgresConfig(db_name="test_kb")

    async with PostgresStack(config) as stack:
        # Create service pointing to Dagger Postgres
        service = RAGService(repository_id=1)
        service.backend.connection_string = stack.connection_string

        await service.initialize()

        # Full workflow test
        chunks = await service.add_document(
            content="Test content",
            metadata={"source": "test.md"}
        )
        results = await service.query("test")

        assert len(results) > 0

        await service.close()
```

### Manual Testing Checklist

- [ ] Postgres container starts with pgvector extension
- [ ] RAG service initializes schema correctly
- [ ] Documents can be added via API
- [ ] Queries return relevant results
- [ ] Metadata filtering works
- [ ] Statistics endpoint returns correct counts
- [ ] Frontend knowledge base UI works

---

## Success Criteria

### Functionality
- ✅ All existing API endpoints work identically
- ✅ Query results are as good or better than ChromaDB
- ✅ Documents persist across service restarts
- ✅ Multi-repository isolation works (separate collections)

### Performance
- ✅ Query latency < 100ms P99
- ✅ Bulk document ingestion handles 1000+ docs
- ✅ Memory usage lower than ChromaDB setup (no separate service)

### Production Readiness
- ✅ Connection pooling configured
- ✅ Health checks pass
- ✅ Logs show proper initialization
- ✅ Database backups include knowledge base data

---

## Future Enhancements

**Not in scope for initial integration, but enabled by this architecture:**

1. **ParadeDB for BM25** - Upgrade from Postgres full-text to ParadeDB's superior BM25
2. **Multi-model embeddings** - Support 768-dim models alongside 384-dim
3. **Cross-repository search** - Query across all repositories in one call
4. **Analytics** - Track popular queries, query performance metrics
5. **Incremental re-indexing** - Only re-embed changed documents

---

## References

- **KnowledgeBeast v3.0 Docs:** `/Users/danielconnolly/Projects/KnowledgeBeast/README.md`
- **PostgresBackend Source:** `/Users/danielconnolly/Projects/KnowledgeBeast/knowledgebeast/backends/postgres.py`
- **Dagger Pattern:** `docs/UNIVERSAL_DAGGER_PATTERN.md`
- **Current RAG Service:** `backend/app/services/rag_service.py`

---

## Appendix: Key Decisions Log

| Decision | Rationale |
|----------|-----------|
| Full replacement (not multi-backend) | Simpler codebase, no existing data to migrate |
| Use Dagger for Postgres image | Reproducible builds, follows established pattern |
| HNSW index (not IVFFlat) | Better for typical dataset sizes, no tuning needed |
| Keep same API surface | No frontend changes, transparent to users |
| Collection naming: `commandcenter_{repo_id}` | Multi-tenant isolation, clear ownership |
| Connection pooling: 2-10 connections | Balance between concurrency and resource usage |
| Embedding model: all-MiniLM-L6-v2 | Same as before, 384 dims, proven performance |

---

**Status:** Design approved - Ready for implementation planning
