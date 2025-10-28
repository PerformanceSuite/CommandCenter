"""Postgres backend implementation using pgvector.

This backend provides production-grade vector storage with:
- asyncpg for async database operations
- pgvector for vector similarity search
- ACID transactions and PostgreSQL reliability
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import asyncpg

from knowledgebeast.backends.base import VectorBackend

logger = logging.getLogger(__name__)


class PostgresBackend(VectorBackend):
    """Postgres backend using pgvector.

    Features:
    - pgvector for vector similarity search (cosine distance)
    - PostgreSQL full-text search for keyword search (safe with plainto_tsquery)
    - Reciprocal Rank Fusion for hybrid search
    - ACID transactions and production reliability
    - Connection pooling for concurrency
    - Async context manager support for automatic cleanup

    Usage:
        # Manual initialization
        backend = PostgresBackend(connection_string="postgresql://...")
        await backend.initialize()
        # ... use backend ...
        await backend.close()

        # Context manager (recommended)
        async with PostgresBackend(connection_string="postgresql://...") as backend:
            # Automatically initialized and cleaned up
            results = await backend.query_vector(embedding)
    """

    def __init__(
        self,
        connection_string: str,
        collection_name: str = "default",
        embedding_dimension: int = 384,
        pool_size: int = 10,
        pool_min_size: int = 2,
    ):
        """Initialize Postgres backend.

        Args:
            connection_string: PostgreSQL connection string
                (e.g., "postgresql://user:pass@localhost/dbname")
            collection_name: Collection/table name prefix
            embedding_dimension: Embedding vector dimension (default: 384)
            pool_size: Maximum connection pool size (default: 10)
            pool_min_size: Minimum connection pool size (default: 2)
        """
        self.connection_string = connection_string
        self.collection_name = collection_name
        self.embedding_dimension = embedding_dimension
        self.pool_size = pool_size
        self.pool_min_size = pool_min_size
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize database connection pool and schema.

        Must be called before using the backend.
        Creates connection pool and sets up database schema.
        """
        if self._initialized:
            return

        # Create connection pool
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=self.pool_min_size,
            max_size=self.pool_size,
            command_timeout=60,
        )

        # Create schema
        await self._create_schema()

        self._initialized = True
        logger.info(
            f"Initialized PostgresBackend: collection='{self.collection_name}', "
            f"dimension={self.embedding_dimension}"
        )

    def _build_where_clause(
        self,
        where: Optional[Dict[str, Any]],
        param_offset: int = 1,
    ) -> Tuple[str, List[Any]]:
        """Build WHERE clause for metadata filtering.

        Args:
            where: Metadata filter dictionary
            param_offset: Starting parameter number for query placeholders

        Returns:
            Tuple of (where_clause_string, additional_params)
        """
        if not where:
            return ("", [])

        return (f"metadata @> ${param_offset}", [where])

    async def _create_schema(self) -> None:
        """Create database schema from SQL template."""
        # Read schema SQL
        schema_path = Path(__file__).parent / "postgres_schema.sql"
        schema_sql = schema_path.read_text()

        # Replace template variables
        schema_sql = schema_sql.replace("{collection_name}", self.collection_name)
        schema_sql = schema_sql.replace("{embedding_dimension}", str(self.embedding_dimension))

        # Execute schema creation with idempotency handling
        # Execute statements individually without transaction for better error recovery
        async with self.pool.acquire() as conn:
            try:
                # Smart SQL statement splitting that respects dollar-quoted strings
                statements = []
                current_statement = []
                in_dollar_quote = False
                dollar_quote_tag = None

                lines = schema_sql.split('\n')
                for line in lines:
                    # Check for dollar-quote delimiters
                    if '$$' in line:
                        if not in_dollar_quote:
                            # Starting a dollar-quoted string
                            in_dollar_quote = True
                            dollar_quote_tag = '$$'
                        elif dollar_quote_tag and dollar_quote_tag in line:
                            # Ending a dollar-quoted string
                            in_dollar_quote = False
                            dollar_quote_tag = None

                    current_statement.append(line)

                    # If we're not in a dollar-quoted string and line ends with semicolon,
                    # this is a statement boundary
                    if not in_dollar_quote and line.rstrip().endswith(';'):
                        stmt = '\n'.join(current_statement).strip()
                        if stmt:
                            statements.append(stmt)
                        current_statement = []

                # Add any remaining statement
                if current_statement:
                    stmt = '\n'.join(current_statement).strip()
                    if stmt and not stmt.startswith('--'):
                        statements.append(stmt)

                # Execute each statement with individual error handling
                for statement in statements:
                    if statement and not statement.startswith('--'):
                        try:
                            await conn.execute(statement)
                        except Exception as e:
                            error_msg = str(e).lower()
                            # Ignore "already exists" for CREATE statements (idempotency)
                            if any(x in error_msg for x in ["already exists", "duplicate"]):
                                logger.debug(f"Ignoring idempotent CREATE error: {error_msg}")
                            # Ignore "does not exist" ONLY for DROP statements (idempotency)
                            elif "does not exist" in error_msg and statement.strip().upper().startswith("DROP"):
                                logger.debug(f"Ignoring idempotent DROP error: {error_msg}")
                            else:
                                logger.error(f"Failed to execute statement: {statement[:100]}... Error: {error_msg}")
                                raise
            except Exception as e:
                # Final catch for any non-idempotent errors
                logger.error(f"Failed to create schema: {e}")
                raise

        logger.info(f"Schema ready for collection '{self.collection_name}'")

    async def add_documents(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Add documents with embeddings to Postgres.

        Uses INSERT ... ON CONFLICT DO UPDATE for upsert behavior.

        Args:
            ids: Document IDs
            embeddings: Embedding vectors
            documents: Document text content
            metadatas: Document metadata (stored as JSONB)

        Raises:
            ValueError: If input lists have mismatched lengths
            RuntimeError: If backend not initialized
        """
        if not self._initialized:
            raise RuntimeError("Backend not initialized. Call initialize() first.")

        if not (len(ids) == len(embeddings) == len(documents) == len(metadatas)):
            raise ValueError("All input lists must have the same length")

        # Prepare data for bulk insert
        # Convert embeddings to pgvector string format
        records = [
            (doc_id, '[' + ','.join(str(x) for x in embedding) + ']', document, json.dumps(metadata))
            for doc_id, embedding, document, metadata in zip(ids, embeddings, documents, metadatas)
        ]

        # Upsert SQL (insert or update on conflict)
        sql = f"""
            INSERT INTO {self.collection_name}_documents (id, embedding, document, metadata)
            VALUES ($1, $2::vector, $3, $4::jsonb)
            ON CONFLICT (id) DO UPDATE SET
                embedding = EXCLUDED.embedding,
                document = EXCLUDED.document,
                metadata = EXCLUDED.metadata
        """

        async with self.pool.acquire() as conn:
            await conn.executemany(sql, records)

        logger.debug(f"Added {len(ids)} documents to '{self.collection_name}'")

    async def query_vector(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict[str, Any], str]]:
        """Perform vector similarity search using pgvector.

        Uses cosine distance for similarity (lower distance = higher similarity).

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            where: Optional metadata filter (e.g., {"source": "docs"})

        Returns:
            List of (doc_id, similarity_score, metadata, document) tuples

        Raises:
            RuntimeError: If backend not initialized
        """
        if not self._initialized:
            raise RuntimeError("Backend not initialized. Call initialize() first.")

        # Build WHERE clause for metadata filtering
        where_clause, where_params = self._build_where_clause(where, param_offset=3)

        # Convert embedding list to pgvector string format: '[1.0, 2.0, 3.0]'
        embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'
        params = [embedding_str, top_k] + where_params

        # Add WHERE keyword if there's a clause
        if where_clause:
            where_clause = f"WHERE {where_clause}"

        # Query with cosine distance (pgvector operator: <=>)
        sql = f"""
            SELECT id, embedding <=> $1::vector as distance, metadata, document
            FROM {self.collection_name}_documents
            {where_clause}
            ORDER BY distance
            LIMIT $2
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)

        # Convert distance to similarity score
        results = []
        for row in rows:
            # Similarity = 1 / (1 + distance)
            similarity = 1.0 / (1.0 + row["distance"])
            # Deserialize metadata if it's a string (asyncpg may return JSONB as string)
            metadata = row["metadata"]
            if isinstance(metadata, str):
                import json
                metadata = json.loads(metadata)
            results.append((row["id"], similarity, metadata, row["document"]))

        return results

    async def query_keyword(
        self,
        query: str,
        top_k: int = 10,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict[str, Any], str]]:
        """Perform full-text keyword search using PostgreSQL.

        Uses ts_rank for relevance scoring with plainto_tsquery for safe query handling.
        plainto_tsquery automatically sanitizes user input and handles special characters.

        Args:
            query: Search query string
            top_k: Number of results to return
            where: Optional metadata filter

        Returns:
            List of (doc_id, relevance_score, metadata, document) tuples

        Raises:
            RuntimeError: If backend not initialized
        """
        if not self._initialized:
            raise RuntimeError("Backend not initialized. Call initialize() first.")

        # Build WHERE clause for metadata filtering
        where_clause, where_params = self._build_where_clause(where, param_offset=3)
        params = [query, top_k] + where_params

        # Add AND to where_clause if it exists (since we have a base WHERE already)
        if where_clause:
            where_clause = f"AND {where_clause}"

        # Full-text search with ts_rank
        # Uses plainto_tsquery which is safer than to_tsquery (auto-sanitizes input)
        sql = f"""
            SELECT
                id,
                ts_rank(to_tsvector('english', document), plainto_tsquery('english', $1)) as rank,
                metadata,
                document
            FROM {self.collection_name}_documents
            WHERE to_tsvector('english', document) @@ plainto_tsquery('english', $1)
            {where_clause}
            ORDER BY rank DESC
            LIMIT $2
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)

        import json
        results = []
        for row in rows:
            # Deserialize metadata if it's a string
            metadata = row["metadata"]
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            results.append((row["id"], float(row["rank"]), metadata, row["document"]))
        return results

    async def query_hybrid(
        self,
        query_embedding: List[float],
        query_text: str,
        top_k: int = 10,
        alpha: float = 0.7,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict[str, Any], str]]:
        """Perform hybrid search combining vector and keyword search.

        Uses Reciprocal Rank Fusion (RRF) to combine results.

        Args:
            query_embedding: Query vector for semantic search
            query_text: Query string for keyword search
            top_k: Number of results to return
            alpha: Weight for vector search (0-1)
            where: Optional metadata filter

        Returns:
            List of (doc_id, combined_score, metadata, document) tuples

        Raises:
            ValueError: If alpha not in [0, 1]
            RuntimeError: If backend not initialized
        """
        if not 0 <= alpha <= 1:
            raise ValueError(f"alpha must be in [0, 1], got {alpha}")

        if not self._initialized:
            raise RuntimeError("Backend not initialized. Call initialize() first.")

        # Get both result sets (expand to 20 for better RRF coverage)
        vector_results = await self.query_vector(query_embedding, top_k=20, where=where)
        keyword_results = await self.query_keyword(query_text, top_k=20, where=where)

        # Reciprocal Rank Fusion
        k = 60  # RRF constant

        # Build ranking maps
        vector_ranks = {doc_id: i + 1 for i, (doc_id, _, _, _) in enumerate(vector_results)}
        keyword_ranks = {doc_id: i + 1 for i, (doc_id, _, _, _) in enumerate(keyword_results)}

        # Collect all unique doc IDs
        all_ids = set(vector_ranks.keys()) | set(keyword_ranks.keys())

        # Build metadata and document maps
        vector_meta = {doc_id: meta for doc_id, _, meta, _ in vector_results}
        keyword_meta = {doc_id: meta for doc_id, _, meta, _ in keyword_results}
        vector_docs = {doc_id: doc for doc_id, _, _, doc in vector_results}
        keyword_docs = {doc_id: doc for doc_id, _, _, doc in keyword_results}

        # Compute RRF scores
        rrf_scores = {}
        metadata_map = {}
        document_map = {}

        for doc_id in all_ids:
            vec_rank = vector_ranks.get(doc_id, 1000)  # Large rank if not found
            key_rank = keyword_ranks.get(doc_id, 1000)

            rrf_score = (
                alpha * (1.0 / (k + vec_rank)) +
                (1 - alpha) * (1.0 / (k + key_rank))
            )
            rrf_scores[doc_id] = rrf_score
            metadata_map[doc_id] = vector_meta.get(doc_id) or keyword_meta.get(doc_id, {})
            document_map[doc_id] = vector_docs.get(doc_id) or keyword_docs.get(doc_id, "")

        # Sort by RRF score and return top_k
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [(doc_id, score, metadata_map.get(doc_id, {}), document_map.get(doc_id, ""))
                for doc_id, score in sorted_results[:top_k]]

    async def delete_documents(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Delete documents from the database.

        Args:
            ids: List of document IDs to delete
            where: Metadata filter (e.g., {"source": "test"})

        Returns:
            Number of documents deleted

        Raises:
            ValueError: If neither ids nor where specified
            RuntimeError: If backend not initialized
        """
        if not self._initialized:
            raise RuntimeError("Backend not initialized. Call initialize() first.")

        if ids is None and where is None:
            raise ValueError("Must specify either ids or where filter")

        # Build DELETE SQL
        where_clauses = []
        params = []

        if ids:
            placeholders = ", ".join(f"${i+1}" for i in range(len(ids)))
            where_clauses.append(f"id IN ({placeholders})")
            params.extend(ids)

        if where:
            where_clauses.append(f"metadata @> ${len(params) + 1}")
            params.append(where)

        where_clause = " AND ".join(where_clauses)
        sql = f"DELETE FROM {self.collection_name}_documents WHERE {where_clause}"

        async with self.pool.acquire() as conn:
            result = await conn.execute(sql, *params)

        # Parse result string like "DELETE 5" -> 5
        count = int(result.split()[-1])
        logger.debug(f"Deleted {count} documents from '{self.collection_name}'")
        return count

    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the collection.

        Returns:
            Dictionary with stats like document count, collection name, etc.

        Raises:
            RuntimeError: If backend not initialized
        """
        if not self._initialized:
            raise RuntimeError("Backend not initialized. Call initialize() first.")

        sql = f"SELECT COUNT(*) FROM {self.collection_name}_documents"

        async with self.pool.acquire() as conn:
            doc_count = await conn.fetchval(sql)

        return {
            "document_count": doc_count,
            "collection_name": self.collection_name,
            "embedding_dimension": self.embedding_dimension,
            "backend_type": "postgres",
        }

    async def get_health(self) -> Dict[str, Any]:
        """Check backend health and availability.

        Returns:
            Dictionary with health status and connection info

        """
        if not self._initialized or not self.pool:
            return {
                "status": "unhealthy",
                "backend_available": False,
                "error": "Backend not initialized",
            }

        try:
            # Simple query to check database connectivity
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            return {
                "status": "healthy",
                "backend_available": True,
                "collection": self.collection_name,
                "embedding_dimension": self.embedding_dimension,
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "backend_available": False,
                "error": str(e),
            }

    async def close(self) -> None:
        """Close connection pool and cleanup resources."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self._initialized = False
            logger.info(f"Closed PostgresBackend for collection '{self.collection_name}'")

    async def __aenter__(self):
        """Async context manager entry - initializes the backend."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - closes the backend."""
        await self.close()
        return False  # Don't suppress exceptions
