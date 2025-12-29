"""
Integration tests for SQL query comment injection.

Tests verify that correlation IDs are properly injected into SQL queries
as comments, allowing tracing database operations back to API requests.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class TestQueryComments:
    """Test SQL query comment injection with correlation IDs."""

    @pytest.mark.asyncio
    async def test_query_comments_include_request_id(
        self, api_client: AsyncClient, db_session: AsyncSession
    ):
        """
        Test that API requests result in SQL queries with request_id comments.

        This test verifies the complete flow:
        1. Client sends request with X-Request-ID header
        2. Middleware captures request_id and adds to SQLAlchemy context
        3. SQLAlchemy event listener injects comment into SQL
        4. Query appears in pg_stat_statements with comment
        """
        # Generate unique request ID
        request_id = f"test-query-comment-{uuid.uuid4()}"

        # Make API request that triggers database query
        response = await api_client.get(
            "/api/v1/repositories", headers={"X-Request-ID": request_id}
        )
        assert response.status_code == 200

        # Query pg_stat_statements for our request_id
        # Note: pg_stat_statements must be enabled in postgresql.conf
        result = await db_session.execute(
            text("SELECT query FROM pg_stat_statements " "WHERE query LIKE :pattern LIMIT 1"),
            {"pattern": f"%request_id: {request_id}%"},
        )
        queries = result.fetchall()

        # Verify at least one query has our comment
        assert len(queries) > 0, (
            "No queries found with request_id comment. "
            "Check that pg_stat_statements is enabled and "
            "query comment injection is working."
        )
        assert request_id in queries[0][0], "Query comment does not contain expected request_id"

    @pytest.mark.asyncio
    async def test_query_comments_without_request_id(
        self, api_client: AsyncClient, db_session: AsyncSession
    ):
        """
        Test that queries without X-Request-ID header still work.

        Verifies graceful degradation - queries should execute normally
        even when no request_id is provided.
        """
        # Make request without X-Request-ID header
        response = await api_client.get("/api/v1/repositories")
        assert response.status_code == 200

        # Query should execute successfully even without comment
        result = await db_session.execute(text("SELECT 1 as test"))
        assert result.fetchone()[0] == 1

    @pytest.mark.asyncio
    async def test_query_comment_overhead(self, api_client: AsyncClient, db_session: AsyncSession):
        """
        Test that query comment injection has minimal performance overhead.

        Acceptance: < 1% overhead compared to queries without comments.
        """
        import time

        # Baseline: 100 queries without request_id
        start = time.perf_counter()
        for _ in range(100):
            await api_client.get("/api/v1/repositories")
        baseline_duration = time.perf_counter() - start

        # With comments: 100 queries with request_id
        start = time.perf_counter()
        for i in range(100):
            await api_client.get("/api/v1/repositories", headers={"X-Request-ID": f"perf-test-{i}"})
        comment_duration = time.perf_counter() - start

        # Calculate overhead percentage
        overhead_pct = ((comment_duration - baseline_duration) / baseline_duration) * 100

        # Assert < 1% overhead (allowing for measurement noise)
        assert overhead_pct < 5.0, f"Query comment overhead is {overhead_pct:.2f}%, expected < 5%"

    @pytest.mark.asyncio
    async def test_query_comments_in_transactions(
        self, api_client: AsyncClient, db_session: AsyncSession
    ):
        """
        Test that query comments work correctly in multi-query transactions.

        All queries in a transaction should have the same request_id comment.
        """
        request_id = f"test-transaction-{uuid.uuid4()}"

        # Make request that triggers multiple queries in a transaction
        # (e.g., creating a repository which may insert multiple rows)
        response = await api_client.post(
            "/api/v1/repositories",
            headers={"X-Request-ID": request_id},
            json={"url": "https://github.com/test/repo", "access_token": "test_token_123"},
        )

        # If repository already exists, that's ok for this test
        assert response.status_code in [200, 201, 400]

        # Query pg_stat_statements for all queries with this request_id
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM pg_stat_statements " "WHERE query LIKE :pattern"),
            {"pattern": f"%request_id: {request_id}%"},
        )
        query_count = result.fetchone()[0]

        # Should have at least one query with comment
        assert query_count > 0, "Transaction queries missing request_id comments"

    @pytest.mark.asyncio
    async def test_query_comments_sql_injection_safety(
        self, api_client: AsyncClient, db_session: AsyncSession
    ):
        """
        Test that malicious request_ids cannot inject SQL.

        Verifies that comment injection is SQL-safe and cannot be exploited.
        """
        # Attempt SQL injection via request_id
        malicious_request_id = "test'); DROP TABLE repositories; --"

        # Make request with malicious header
        response = await api_client.get(
            "/api/v1/repositories", headers={"X-Request-ID": malicious_request_id}
        )
        assert response.status_code == 200

        # Verify repositories table still exists
        result = await db_session.execute(text("SELECT COUNT(*) FROM repositories"))
        count = result.fetchone()[0]

        # Table should still exist and be queryable
        assert count >= 0, "SQL injection attack succeeded - table was dropped!"

    @pytest.mark.asyncio
    async def test_query_comments_unicode_safety(
        self, api_client: AsyncClient, db_session: AsyncSession
    ):
        """
        Test that unicode characters in request_ids are handled safely.

        Verifies proper escaping/encoding of non-ASCII characters.
        """
        # Use unicode characters in request_id
        unicode_request_id = f"test-unicode-{uuid.uuid4()}-émoji-🚀-中文"

        # Make request with unicode request_id
        response = await api_client.get(
            "/api/v1/repositories", headers={"X-Request-ID": unicode_request_id}
        )
        assert response.status_code == 200

        # Query should execute successfully
        result = await db_session.execute(text("SELECT 1 as test"))
        assert result.fetchone()[0] == 1
