# KnowledgeBeast v3.0 - Postgres Backend Upgrade

**Status**: Architecture Design
**Date**: 2025-10-23
**Projects Impacted**: KnowledgeBeast, CommandCenter, Performia (future), Veria (future)

---

## Executive Summary

Upgrade KnowledgeBeast from ChromaDB to Postgres-native hybrid search using **pgvector** (semantic search) and **ParadeDB** (BM25 keyword search). This provides:

- ✅ **Unified database**: No separate ChromaDB service
- ✅ **Better multi-tenancy**: Postgres schemas for isolation
- ✅ **Production-grade**: ACID transactions, backups, replication
- ✅ **Open source**: No vendor lock-in (vs TigerData)
- ✅ **Backward compatible**: Support both ChromaDB and Postgres backends

---

## Architecture Overview

### Current State (KnowledgeBeast v2.x)

```
┌─────────────────────────────────────────┐
│     KnowledgeBeast v2.3.2              │
│                                         │
│  ┌──────────────┐    ┌──────────────┐ │
│  │ Embedding    │    │ Vector Store │ │
│  │ Engine       │───▶│ (ChromaDB)   │ │
│  └──────────────┘    └──────────────┘ │
│                                         │
│  ┌──────────────┐    ┌──────────────┐ │
│  │ Document     │    │ Hybrid Query │ │
│  │ Repository   │◀───│ Engine       │ │
│  └──────────────┘    └──────────────┘ │
│                                         │
│  Storage: ChromaDB (separate service)  │
└─────────────────────────────────────────┘
```

### Target State (KnowledgeBeast v3.0)

```
┌─────────────────────────────────────────────────────────┐
│           KnowledgeBeast v3.0                           │
│                                                          │
│  ┌──────────────┐          ┌──────────────────────┐    │
│  │ Embedding    │          │  Backend Abstraction │    │
│  │ Engine       │          │  (Interface)         │    │
│  └──────────────┘          └──────────────────────┘    │
│         │                            │                  │
│         │                   ┌────────┴────────┐        │
│         │                   │                 │        │
│         │          ┌────────▼──────┐  ┌──────▼──────┐ │
│         │          │ ChromaDB      │  │ Postgres    │ │
│         │          │ Backend       │  │ Backend     │ │
│         │          │ (Legacy)      │  │ (New!)      │ │
│         │          └───────────────┘  └─────────────┘ │
│         │                                      │       │
│         │                              ┌───────▼───────┤
│         │                              │ pgvector      │
│         │                              │ + ParadeDB    │
│         │                              └───────────────┘
│         │                                              │
│  ┌──────▼──────┐    ┌──────────────┐                 │
│  │ Document    │    │ Hybrid Query │                 │
│  │ Repository  │◀───│ Engine       │                 │
│  └─────────────┘    └──────────────┘                 │
│                                                        │
│  Storage: PostgreSQL (unified database)               │
└─────────────────────────────────────────────────────────┘
```

---

## Technical Design

### 1. Backend Abstraction Layer

Create a pluggable backend system:

```python
# knowledgebeast/backends/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

class VectorBackend(ABC):
    """Abstract base class for vector storage backends"""

    @abstractmethod
    async def add_documents(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """Add documents with embeddings"""
        pass

    @abstractmethod
    async def query_vector(
        self,
        query_embedding: List[float],
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Vector similarity search
        Returns: List of (doc_id, distance/score) tuples
        """
        pass

    @abstractmethod
    async def query_keyword(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Keyword/BM25 search
        Returns: List of (doc_id, score) tuples
        """
        pass

    @abstractmethod
    async def delete_documents(self, ids: List[str]) -> None:
        """Delete documents by ID"""
        pass

    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """Get backend statistics"""
        pass
```

### 2. Postgres Backend Implementation

```python
# knowledgebeast/backends/postgres.py
import asyncpg
from typing import List, Dict, Any, Tuple, Optional
from .base import VectorBackend

class PostgresBackend(VectorBackend):
    """
    Postgres backend using pgvector + ParadeDB

    Architecture:
    - pgvector: Vector similarity search (cosine distance)
    - ParadeDB (pg_search): BM25 keyword ranking
    - Reciprocal Rank Fusion: Hybrid search combining both

    Schema:
    CREATE TABLE documents (
        id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        embedding vector(384),  -- or 768 for larger models
        metadata JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
    CREATE INDEX ON documents USING bm25 (content);  -- ParadeDB
    """

    def __init__(
        self,
        connection_string: str,
        collection_name: str = "default",
        embedding_dimension: int = 384,
        pool_size: int = 10
    ):
        self.connection_string = connection_string
        self.collection_name = collection_name
        self.embedding_dimension = embedding_dimension
        self.pool_size = pool_size
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Initialize connection pool and ensure extensions"""
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=1,
            max_size=self.pool_size
        )

        async with self.pool.acquire() as conn:
            # Create extensions
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_search;")

            # Create table
            table_name = f"kb_{self.collection_name}_docs"
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding vector({self.embedding_dimension}),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # Create indexes
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.collection_name}_vector
                ON {table_name} USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """)

            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.collection_name}_bm25
                ON {table_name} USING bm25 (content)
                WITH (key_field='id');
            """)

    async def add_documents(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """Insert documents with embeddings"""
        table_name = f"kb_{self.collection_name}_docs"

        async with self.pool.acquire() as conn:
            await conn.executemany(
                f"""
                INSERT INTO {table_name} (id, content, embedding, metadata)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata
                """,
                [(id, doc, emb, meta) for id, doc, emb, meta in
                 zip(ids, documents, embeddings, metadatas)]
            )

    async def query_vector(
        self,
        query_embedding: List[float],
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """Vector similarity search using pgvector"""
        table_name = f"kb_{self.collection_name}_docs"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, embedding <=> $1 as distance
                FROM {table_name}
                ORDER BY embedding <=> $1
                LIMIT $2
                """,
                query_embedding,
                top_k
            )

        return [(row['id'], row['distance']) for row in rows]

    async def query_keyword(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """BM25 keyword search using ParadeDB"""
        table_name = f"kb_{self.collection_name}_docs"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, paradedb.score(id) as score
                FROM {table_name}
                WHERE content @@@ $1
                ORDER BY score DESC
                LIMIT $2
                """,
                query,
                top_k
            )

        return [(row['id'], row['score']) for row in rows]

    async def query_hybrid(
        self,
        query_embedding: List[float],
        query_text: str,
        alpha: float = 0.7,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Hybrid search using Reciprocal Rank Fusion (RRF)

        Args:
            query_embedding: Vector for semantic search
            query_text: Text for keyword search
            alpha: Blend factor (0=keyword only, 1=vector only)
            top_k: Number of results

        Returns:
            List of (doc_id, rrf_score) tuples
        """
        table_name = f"kb_{self.collection_name}_docs"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                WITH vector_search AS (
                    SELECT id,
                           ROW_NUMBER() OVER (ORDER BY embedding <=> $1) as rank
                    FROM {table_name}
                    ORDER BY embedding <=> $1
                    LIMIT 20
                ),
                keyword_search AS (
                    SELECT id,
                           ROW_NUMBER() OVER (ORDER BY paradedb.score(id) DESC) as rank
                    FROM {table_name}
                    WHERE content @@@ $2
                    LIMIT 20
                ),
                rrf_fusion AS (
                    SELECT
                        COALESCE(v.id, k.id) as id,
                        ($3 * COALESCE(1.0 / (60 + v.rank), 0)) +
                        ((1 - $3) * COALESCE(1.0 / (60 + k.rank), 0)) as score
                    FROM vector_search v
                    FULL OUTER JOIN keyword_search k ON v.id = k.id
                )
                SELECT id, score
                FROM rrf_fusion
                ORDER BY score DESC
                LIMIT $4
                """,
                query_embedding,
                query_text,
                alpha,
                top_k
            )

        return [(row['id'], row['score']) for row in rows]

    async def delete_documents(self, ids: List[str]) -> None:
        """Delete documents by ID"""
        table_name = f"kb_{self.collection_name}_docs"

        async with self.pool.acquire() as conn:
            await conn.execute(
                f"DELETE FROM {table_name} WHERE id = ANY($1)",
                ids
            )

    async def get_statistics(self) -> Dict[str, Any]:
        """Get backend statistics"""
        table_name = f"kb_{self.collection_name}_docs"

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT COUNT(*) as total FROM {table_name}"
            )

        return {
            "backend": "postgres",
            "collection": self.collection_name,
            "total_documents": row['total'],
            "embedding_dimension": self.embedding_dimension
        }

    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
```

### 3. ChromaDB Backend (Legacy Support)

```python
# knowledgebeast/backends/chromadb.py
from .base import VectorBackend
from chromadb import Client, Settings

class ChromaDBBackend(VectorBackend):
    """Legacy ChromaDB backend for backward compatibility"""

    def __init__(
        self,
        persist_directory: str,
        collection_name: str = "default"
    ):
        self.client = Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

    # Implement all abstract methods using ChromaDB API...
```

---

## Migration Strategy

### Phase 1: Add Backend Abstraction (v3.0.0-alpha)
1. Create `knowledgebeast/backends/` module
2. Implement `VectorBackend` abstract class
3. Wrap existing ChromaDB code in `ChromaDBBackend`
4. Update `HybridQueryEngine` to use backend abstraction
5. **No breaking changes yet** - defaults to ChromaDB

### Phase 2: Implement Postgres Backend (v3.0.0-beta)
1. Implement `PostgresBackend` with pgvector + ParadeDB
2. Add configuration for backend selection
3. Create migration utility: `kb-migrate chromadb postgres`
4. Update tests to run against both backends
5. Benchmark Postgres vs ChromaDB

### Phase 3: Production Release (v3.0.0)
1. Document Postgres setup (extensions, schemas)
2. Update README with backend comparison
3. Provide migration guide for existing users
4. Release with both backends supported
5. Deprecation notice: ChromaDB backend will be removed in v4.0

---

## Configuration Changes

### Current (v2.x)
```python
from knowledgebeast import HybridQueryEngine, DocumentRepository

repo = DocumentRepository()
engine = HybridQueryEngine(
    repo,
    model_name="all-MiniLM-L6-v2"
)
```

### New (v3.0) - ChromaDB (default)
```python
from knowledgebeast import HybridQueryEngine, DocumentRepository
from knowledgebeast.backends import ChromaDBBackend

backend = ChromaDBBackend(
    persist_directory="./chroma_db",
    collection_name="my_kb"
)

repo = DocumentRepository()
engine = HybridQueryEngine(
    repo,
    backend=backend,  # New parameter!
    model_name="all-MiniLM-L6-v2"
)
```

### New (v3.0) - Postgres
```python
from knowledgebeast import HybridQueryEngine, DocumentRepository
from knowledgebeast.backends import PostgresBackend

backend = PostgresBackend(
    connection_string="postgresql://user:pass@localhost/kb",
    collection_name="my_kb",
    embedding_dimension=384
)

await backend.initialize()  # Create tables, indexes

repo = DocumentRepository()
engine = HybridQueryEngine(
    repo,
    backend=backend,
    model_name="all-MiniLM-L6-v2"
)
```

---

## Multi-Project Integration

### CommandCenter
```python
# hub/backend/app/config.py
class Settings(BaseSettings):
    knowledgebeast_backend: str = "postgres"  # or "chromadb"
    database_url: str  # Shared Postgres instance

# hub/backend/app/services/knowledgebeast_service.py
if settings.knowledgebeast_backend == "postgres":
    backend = PostgresBackend(
        connection_string=settings.database_url,
        collection_name=f"project_{project_id}",
        embedding_dimension=384
    )
else:
    backend = ChromaDBBackend(
        persist_directory=settings.kb_db_path,
        collection_name=f"project_{project_id}"
    )
```

### Performia (Future)
```python
# Song library search with Postgres backend
backend = PostgresBackend(
    connection_string="postgresql://performia:pass@localhost/performia",
    collection_name="song_library"
)

# Hybrid search: "Find songs like Yesterday by Beatles"
# - Vector search: Musical similarity
# - Keyword search: Exact lyric matches
```

### Veria (Future)
```python
# Compliance policy search with Postgres backend
backend = PostgresBackend(
    connection_string="postgresql://veria:pass@localhost/veria",
    collection_name="compliance_policies"
)

# Hybrid search: "MiCA Article 4.2 stablecoin requirements"
# - Vector search: Semantic policy matching
# - Keyword search: Exact regulatory citations
```

---

## Testing Strategy

### Unit Tests
- Test each backend independently
- Mock database connections
- Verify abstract interface compliance

### Integration Tests
- Test both backends with same test suite
- Verify result equivalence (within tolerance)
- Test migration utility

### Performance Benchmarks
```
Benchmark Suite:
- 10k documents, 100 concurrent queries
- P50, P95, P99 latency
- Memory usage
- Index build time

Expected Results:
- Postgres: < 50ms P99 (vs ChromaDB ~100ms)
- Memory: Lower (no separate service)
- Scale: Better (production Postgres features)
```

---

## Rollout Plan

### Week 1: Architecture & ChromaDB Backend
- [ ] Create backend abstraction layer
- [ ] Implement ChromaDBBackend wrapper
- [ ] Update HybridQueryEngine to use backends
- [ ] All tests passing (no functionality changes)

### Week 2: Postgres Backend Implementation
- [ ] Implement PostgresBackend
- [ ] Add pgvector + ParadeDB integration
- [ ] Implement Reciprocal Rank Fusion
- [ ] Unit tests for Postgres backend

### Week 3: Migration & Testing
- [ ] Create migration utility
- [ ] Integration tests (both backends)
- [ ] Performance benchmarks
- [ ] Documentation updates

### Week 4: CommandCenter Integration
- [ ] Update CommandCenter to KB v3.0
- [ ] Test in CommandCenter environment
- [ ] Migration guide for existing data
- [ ] Production deployment

---

## Success Criteria

✅ **Functionality**
- Both backends pass 100% of existing tests
- Hybrid search produces equivalent results (within 5% NDCG@10)
- Migration utility successfully converts ChromaDB → Postgres

✅ **Performance**
- Postgres backend P99 latency < 100ms
- Memory usage < ChromaDB (no separate service)
- Can handle 500+ concurrent queries/sec

✅ **Production Readiness**
- Comprehensive documentation
- Example configurations for all projects
- Backward compatibility maintained
- Clear deprecation timeline

---

## Open Questions

1. **ParadeDB Installation**: How to distribute ParadeDB extension?
   - Option A: Docker image with pre-installed extensions
   - Option B: Installation script for bare metal
   - Option C: Document manual installation steps

2. **Embedding Dimension**: Support both 384 and 768?
   - Currently: 384 (all-MiniLM-L6-v2)
   - Future: 768 (larger models)
   - Solution: Make dimension configurable per backend

3. **Multi-tenancy**: Schema-per-project vs table-per-project?
   - Option A: Separate schemas (`kb_project1`, `kb_project2`)
   - Option B: Prefixed tables (`kb_project1_docs`, `kb_project2_docs`)
   - Recommendation: **Option B** (simpler, fewer privileges needed)

---

## Next Steps

1. Review this architecture document
2. Get approval for approach
3. Start implementation in KnowledgeBeast repository
4. Track progress via GitHub project board
5. Release v3.0.0-alpha for testing

**Ready to proceed?**
