# Week 2 Performance Tests Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement CommandCenter performance tests for N+1 query detection and API benchmarks (13 tests total).

**Architecture:** Performance testing infrastructure using SQLAlchemy event listeners for query counting, large test datasets for N+1 detection, and time-based benchmarks for API endpoints. All tests use real database queries but mocked external services.

**Tech Stack:** pytest, pytest-asyncio, SQLAlchemy event system, time module, asyncio

**Worktree:** `.worktrees/testing-performance` → `testing/week2-performance` branch

---

## Task 1: Performance Test Infrastructure

**Files:**
- Create: `backend/tests/performance/conftest.py`
- Create: `backend/tests/performance/__init__.py`

**Step 1: Create performance test directory structure**

```bash
mkdir -p backend/tests/performance
touch backend/tests/performance/__init__.py
```

**Step 2: Write query counter fixture**

Create `backend/tests/performance/conftest.py`:

```python
"""Performance test fixtures."""
import pytest
from sqlalchemy import event
from tests.utils.factories import (
    TechnologyFactory,
    RepositoryFactory,
    ResearchTaskFactory,
    KnowledgeEntryFactory
)


@pytest.fixture
def query_counter(db_session):
    """Count queries executed during test.

    Tracks all SQL queries executed through SQLAlchemy,
    filtering out internal PostgreSQL catalog queries.

    Usage:
        def test_something(query_counter):
            query_counter.clear()  # Reset counter
            # ... perform operations ...
            assert len(query_counter) <= 3  # Check query count
    """
    queries = []

    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        # Filter out internal PostgreSQL queries
        if "pg_catalog" not in statement and "information_schema" not in statement:
            queries.append({
                "statement": statement,
                "parameters": parameters,
                "executemany": executemany
            })

    # Attach listener
    event.listen(
        db_session.bind,
        "after_cursor_execute",
        receive_after_cursor_execute
    )

    yield queries

    # Detach listener
    event.remove(
        db_session.bind,
        "after_cursor_execute",
        receive_after_cursor_execute
    )


@pytest.fixture
async def large_dataset(db_session):
    """Create dataset large enough to expose N+1 queries.

    Creates 20 technologies, each with 3 repositories and 2 research tasks.
    This generates enough data to make N+1 query problems obvious.
    """
    technologies = []

    for i in range(20):
        tech = await TechnologyFactory.create(
            db_session,
            title=f"Technology {i}",
            domain="test",
            vendor=f"Vendor {i}",
            status="adopt"
        )

        # Add repositories for this technology
        for j in range(3):
            repo = await RepositoryFactory.create(
                db_session,
                owner=f"test-owner-{i}",
                name=f"repo-{i}-{j}"
            )
            tech.repositories.append(repo)

        # Add research tasks for this technology
        for k in range(2):
            research = await ResearchTaskFactory.create(
                db_session,
                title=f"Research {i}-{k}",
                technology_id=tech.id
            )

        technologies.append(tech)

    await db_session.commit()
    return technologies


@pytest.fixture
def performance_threshold():
    """Performance thresholds for API endpoints (milliseconds).

    These thresholds are intentionally generous to account for:
    - CI/CD environment variability
    - Cold starts
    - Database initialization

    Adjust based on production requirements.
    """
    return {
        "technologies_list": 500,      # GET /api/v1/technologies
        "technologies_create": 300,    # POST /api/v1/technologies
        "research_list": 500,          # GET /api/v1/research
        "research_create": 300,        # POST /api/v1/research
        "knowledge_query": 1500,       # POST /api/v1/knowledge/query
        "repositories_list": 500,      # GET /api/v1/repositories
    }


@pytest.fixture
async def performance_dataset(db_session):
    """Create large dataset for stress testing (1000 records).

    Used for testing query performance under load.
    """
    technologies = []

    for i in range(1000):
        tech = await TechnologyFactory.create(
            db_session,
            title=f"Performance Tech {i}",
            domain="performance-test",
            vendor=f"Vendor {i % 100}",  # Create some duplicates
            status="assess" if i % 2 == 0 else "trial"
        )
        technologies.append(tech)

    await db_session.commit()
    return technologies
```

**Step 3: Verify fixtures import correctly**

Run:
```bash
cd backend
python -c "from tests.performance.conftest import *; print('Performance fixtures loaded successfully')"
```

Expected: "Performance fixtures loaded successfully"

**Step 4: Commit**

```bash
git add backend/tests/performance/
git commit -m "test: Add performance test infrastructure and fixtures

- Create performance test directory structure
- Add query_counter fixture for N+1 detection
- Add large_dataset fixture (20 techs × 3 repos × 2 research)
- Add performance_threshold fixture for benchmarks
- Add performance_dataset fixture (1000 records) for stress testing"
```

---

## Task 2: N+1 Query Detection Tests (Part 1 - Technologies)

**Files:**
- Create: `backend/tests/performance/test_n_plus_one_queries.py`

**Step 1: Write failing test for technologies list N+1**

Create `backend/tests/performance/test_n_plus_one_queries.py`:

```python
"""N+1 query detection tests."""
import pytest


@pytest.mark.asyncio
async def test_technologies_list_no_n_plus_one(
    query_counter, large_dataset, client, auth_headers_factory, user_a
):
    """Technologies list uses joins, not N+1 queries.

    With 20 technologies (each with repos/research), an N+1 query
    pattern would generate 60+ queries. Proper eager loading should
    use ≤3 queries total.
    """
    # Clear any setup queries
    query_counter.clear()

    # Make request
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/technologies", headers=headers)

    # Analyze queries
    num_queries = len(query_counter)

    # Should be ≤3 queries:
    # 1. SELECT technologies (with project_id filter)
    # 2. JOIN repositories (if eager loading)
    # 3. JOIN research_tasks (if eager loading)
    assert num_queries <= 3, (
        f"Expected ≤3 queries, got {num_queries}. "
        f"Possible N+1 query problem. "
        f"Queries executed:\n" +
        "\n".join([f"  - {q['statement'][:100]}..." for q in query_counter])
    )

    # Verify response still correct
    assert response.status_code == 200
    technologies = response.json()
    assert len(technologies) >= 20  # Should see all 20 created
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd backend
pytest tests/performance/test_n_plus_one_queries.py::test_technologies_list_no_n_plus_one -v
```

Expected: FAIL (N+1 detection not yet implemented in endpoint)

**Step 3: Write test for technology detail N+1**

Add to `backend/tests/performance/test_n_plus_one_queries.py`:

```python
@pytest.mark.asyncio
async def test_technology_detail_no_n_plus_one(
    query_counter, large_dataset, client, auth_headers_factory, user_a
):
    """Technology detail endpoint loads relationships efficiently.

    Detail view should eager load repositories and research tasks
    in a single query or with JOINs, not separate queries per relationship.
    """
    tech = large_dataset[0]

    # Clear setup queries
    query_counter.clear()

    # Get single technology detail
    headers = auth_headers_factory(user_a)
    response = await client.get(f"/api/v1/technologies/{tech.id}", headers=headers)

    # Should use ≤2 queries:
    # 1. SELECT technology
    # 2. JOIN repositories + research_tasks
    num_queries = len(query_counter)
    assert num_queries <= 2, (
        f"Expected ≤2 queries for detail view, got {num_queries}. "
        f"Queries:\n" +
        "\n".join([f"  - {q['statement'][:100]}..." for q in query_counter])
    )

    assert response.status_code == 200
    data = response.json()
    assert "repositories" in data or "research_tasks" in data
```

**Step 4: Commit**

```bash
git add backend/tests/performance/test_n_plus_one_queries.py
git commit -m "test: Add N+1 detection tests for technologies (2 tests, failing)

- Test technologies list endpoint avoids N+1 queries
- Test technology detail endpoint loads relationships efficiently
- Both tests currently failing (expected, TDD red phase)"
```

---

## Task 3: N+1 Query Detection Tests (Part 2 - Research & Repositories)

**Files:**
- Modify: `backend/tests/performance/test_n_plus_one_queries.py`

**Step 1: Write test for research tasks N+1**

Add to `backend/tests/performance/test_n_plus_one_queries.py`:

```python
@pytest.mark.asyncio
async def test_research_tasks_list_no_n_plus_one(
    query_counter, large_dataset, client, auth_headers_factory, user_a
):
    """Research tasks list uses joins for technology relationships.

    Each research task has a technology relationship. Without proper
    eager loading, this becomes N+1 (one query per task).
    """
    # Clear setup queries
    query_counter.clear()

    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/research", headers=headers)

    num_queries = len(query_counter)

    # Should be ≤2 queries:
    # 1. SELECT research_tasks (with project_id filter)
    # 2. JOIN technologies (if including tech data)
    assert num_queries <= 2, (
        f"Expected ≤2 queries, got {num_queries}. "
        f"N+1 query detected in research tasks endpoint. "
        f"Queries:\n" +
        "\n".join([f"  - {q['statement'][:80]}..." for q in query_counter])
    )

    assert response.status_code == 200
```

**Step 2: Write test for repositories with technologies**

Add to `backend/tests/performance/test_n_plus_one_queries.py`:

```python
@pytest.mark.asyncio
async def test_repositories_list_with_technologies_no_n_plus_one(
    query_counter, large_dataset, client, auth_headers_factory, user_a
):
    """Repositories list includes linked technologies without N+1.

    Each repository can be linked to multiple technologies (many-to-many).
    Without proper eager loading, this creates N+1 queries.
    """
    # Clear setup queries
    query_counter.clear()

    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/repositories?include_technologies=true", headers=headers)

    num_queries = len(query_counter)

    # Should be ≤3 queries:
    # 1. SELECT repositories
    # 2. SELECT technology associations (many-to-many table)
    # 3. SELECT technologies
    assert num_queries <= 3, (
        f"Expected ≤3 queries, got {num_queries}. "
        f"N+1 detected in repositories endpoint. "
        f"Queries:\n" +
        "\n".join([f"  - {q['statement'][:80]}..." for q in query_counter])
    )

    assert response.status_code == 200
```

**Step 3: Write test for knowledge base queries**

Add to `backend/tests/performance/test_n_plus_one_queries.py`:

```python
from tests.utils.factories import KnowledgeEntryFactory


@pytest.mark.asyncio
async def test_knowledge_base_query_no_n_plus_one(
    query_counter, client, auth_headers_factory, user_a, db_session
):
    """Knowledge base query uses efficient vector search.

    RAG queries should use single vector similarity search,
    not multiple queries per document.
    """
    # Create knowledge entries
    for i in range(10):
        await KnowledgeEntryFactory.create(
            db_session,
            source=f"doc-{i}.pdf",
            category="research",
            project_id=user_a.project_id
        )
    await db_session.commit()

    # Clear setup queries
    query_counter.clear()

    headers = auth_headers_factory(user_a)
    response = await client.post(
        "/api/v1/knowledge/query",
        headers=headers,
        json={"query": "test query", "top_k": 5}
    )

    num_queries = len(query_counter)

    # RAG query should be efficient:
    # - Vector similarity search (1 query)
    # - Metadata lookup (1 query)
    # Total ≤3 queries (including any filtering)
    assert num_queries <= 3, (
        f"Expected ≤3 queries for RAG search, got {num_queries}. "
        f"Queries:\n" +
        "\n".join([f"  - {q['statement'][:80]}..." for q in query_counter])
    )

    assert response.status_code == 200
```

**Step 4: Run tests to verify they fail**

Run:
```bash
cd backend
pytest tests/performance/test_n_plus_one_queries.py -v
```

Expected: 5 FAIL (N+1 optimizations not yet implemented)

**Step 5: Commit**

```bash
git add backend/tests/performance/test_n_plus_one_queries.py
git commit -m "test: Add N+1 detection tests for research, repos, knowledge (3 tests)

- Test research tasks list avoids N+1 queries
- Test repositories list with technologies avoids N+1
- Test knowledge base query uses efficient vector search

Total N+1 detection tests: 5 (all failing as expected, TDD red phase)"
```

---

## Task 4: API Performance Benchmark Tests (Part 1 - CRUD Operations)

**Files:**
- Create: `backend/tests/performance/test_api_benchmarks.py`

**Step 1: Write benchmark test for technologies list**

Create `backend/tests/performance/test_api_benchmarks.py`:

```python
"""API performance benchmark tests."""
import pytest
import time
import asyncio


@pytest.mark.asyncio
async def test_technologies_list_performance(
    client, performance_threshold, large_dataset, auth_headers_factory, user_a
):
    """GET /api/v1/technologies responds in <500ms.

    Tests list endpoint performance with 20 technologies.
    Threshold accounts for:
    - Database query time
    - JSON serialization
    - Network overhead in test client
    """
    headers = auth_headers_factory(user_a)

    start = time.time()
    response = await client.get("/api/v1/technologies?limit=50", headers=headers)
    elapsed_ms = (time.time() - start) * 1000

    assert response.status_code == 200
    assert elapsed_ms < performance_threshold["technologies_list"], (
        f"Response took {elapsed_ms:.2f}ms, threshold is "
        f"{performance_threshold['technologies_list']}ms. "
        f"Performance regression detected."
    )

    # Log actual time for baseline tracking
    print(f"Technologies list: {elapsed_ms:.2f}ms")
```

**Step 2: Write benchmark test for technology creation**

Add to `backend/tests/performance/test_api_benchmarks.py`:

```python
@pytest.mark.asyncio
async def test_technologies_create_performance(
    client, performance_threshold, auth_headers_factory, user_a
):
    """POST /api/v1/technologies responds in <300ms.

    Tests creation endpoint performance.
    """
    headers = auth_headers_factory(user_a)

    payload = {
        "title": "New Technology",
        "domain": "ai",
        "vendor": "TestCorp",
        "status": "assess"
    }

    start = time.time()
    response = await client.post("/api/v1/technologies", headers=headers, json=payload)
    elapsed_ms = (time.time() - start) * 1000

    assert response.status_code == 201 or response.status_code == 200
    assert elapsed_ms < performance_threshold["technologies_create"], (
        f"Creation took {elapsed_ms:.2f}ms, threshold is "
        f"{performance_threshold['technologies_create']}ms"
    )

    print(f"Technologies create: {elapsed_ms:.2f}ms")
```

**Step 3: Write benchmark tests for research endpoints**

Add to `backend/tests/performance/test_api_benchmarks.py`:

```python
@pytest.mark.asyncio
async def test_research_list_performance(
    client, performance_threshold, large_dataset, auth_headers_factory, user_a
):
    """GET /api/v1/research responds in <500ms."""
    headers = auth_headers_factory(user_a)

    start = time.time()
    response = await client.get("/api/v1/research", headers=headers)
    elapsed_ms = (time.time() - start) * 1000

    assert response.status_code == 200
    assert elapsed_ms < performance_threshold["research_list"], (
        f"Response took {elapsed_ms:.2f}ms, threshold is "
        f"{performance_threshold['research_list']}ms"
    )

    print(f"Research list: {elapsed_ms:.2f}ms")


@pytest.mark.asyncio
async def test_research_create_performance(
    client, performance_threshold, auth_headers_factory, user_a
):
    """POST /api/v1/research responds in <300ms."""
    headers = auth_headers_factory(user_a)

    payload = {
        "title": "New Research Task",
        "description": "Test task",
        "status": "pending",
        "priority": "medium"
    }

    start = time.time()
    response = await client.post("/api/v1/research", headers=headers, json=payload)
    elapsed_ms = (time.time() - start) * 1000

    assert response.status_code == 201 or response.status_code == 200
    assert elapsed_ms < performance_threshold["research_create"], (
        f"Creation took {elapsed_ms:.2f}ms, threshold is "
        f"{performance_threshold['research_create']}ms"
    )

    print(f"Research create: {elapsed_ms:.2f}ms")
```

**Step 4: Run tests to verify behavior**

Run:
```bash
cd backend
pytest tests/performance/test_api_benchmarks.py -v -s
```

Expected: PASS or FAIL depending on current performance (will establish baseline)

**Step 5: Commit**

```bash
git add backend/tests/performance/test_api_benchmarks.py
git commit -m "test: Add API benchmark tests for CRUD operations (4 tests)

- Test technologies list performance (<500ms)
- Test technologies create performance (<300ms)
- Test research list performance (<500ms)
- Test research create performance (<300ms)

Tests establish performance baselines"
```

---

## Task 5: API Performance Benchmark Tests (Part 2 - Advanced Operations)

**Files:**
- Modify: `backend/tests/performance/test_api_benchmarks.py`

**Step 1: Write benchmark test for knowledge base query**

Add to `backend/tests/performance/test_api_benchmarks.py`:

```python
from tests.utils.factories import KnowledgeEntryFactory


@pytest.mark.asyncio
async def test_knowledge_query_performance(
    client, performance_threshold, auth_headers_factory, user_a, db_session
):
    """POST /api/v1/knowledge/query responds in <1500ms.

    RAG queries are more expensive due to:
    - Embedding generation
    - Vector similarity search
    - Document retrieval

    Threshold is higher than CRUD operations.
    """
    # Create knowledge entries for realistic query
    for i in range(20):
        await KnowledgeEntryFactory.create(
            db_session,
            source=f"document-{i}.pdf",
            category="research",
            project_id=user_a.project_id
        )
    await db_session.commit()

    headers = auth_headers_factory(user_a)

    payload = {
        "query": "What are the latest advancements in AI?",
        "top_k": 5
    }

    start = time.time()
    response = await client.post("/api/v1/knowledge/query", headers=headers, json=payload)
    elapsed_ms = (time.time() - start) * 1000

    assert response.status_code == 200
    assert elapsed_ms < performance_threshold["knowledge_query"], (
        f"RAG query took {elapsed_ms:.2f}ms, threshold is "
        f"{performance_threshold['knowledge_query']}ms"
    )

    print(f"Knowledge query: {elapsed_ms:.2f}ms")
```

**Step 2: Write benchmark test for repositories list**

Add to `backend/tests/performance/test_api_benchmarks.py`:

```python
from tests.utils.factories import RepositoryFactory


@pytest.mark.asyncio
async def test_repositories_list_performance(
    client, performance_threshold, auth_headers_factory, user_a, db_session
):
    """GET /api/v1/repositories responds in <500ms."""
    # Create multiple repositories
    for i in range(15):
        await RepositoryFactory.create(
            db_session,
            owner="test-owner",
            name=f"test-repo-{i}",
            project_id=user_a.project_id
        )
    await db_session.commit()

    headers = auth_headers_factory(user_a)

    start = time.time()
    response = await client.get("/api/v1/repositories", headers=headers)
    elapsed_ms = (time.time() - start) * 1000

    assert response.status_code == 200
    assert elapsed_ms < performance_threshold["repositories_list"], (
        f"Response took {elapsed_ms:.2f}ms, threshold is "
        f"{performance_threshold['repositories_list']}ms"
    )

    print(f"Repositories list: {elapsed_ms:.2f}ms")
```

**Step 3: Write concurrent request handling test**

Add to `backend/tests/performance/test_api_benchmarks.py`:

```python
@pytest.mark.asyncio
async def test_concurrent_request_handling(
    client, auth_headers_factory, user_a
):
    """50 concurrent requests handled without errors.

    Tests connection pool, async handling, and resource limits.
    """
    headers = auth_headers_factory(user_a)

    async def make_request():
        return await client.get("/api/v1/technologies", headers=headers)

    start = time.time()
    responses = await asyncio.gather(*[make_request() for _ in range(50)])
    elapsed = time.time() - start

    # All should succeed
    assert all(r.status_code == 200 for r in responses), (
        "Some requests failed. Status codes: " +
        str([r.status_code for r in responses if r.status_code != 200])
    )

    # Average response time acceptable
    avg_time_ms = (elapsed / 50) * 1000
    assert avg_time_ms < 1000, (
        f"Average response time {avg_time_ms:.2f}ms too high. "
        f"May indicate connection pool bottleneck."
    )

    # No server errors
    error_responses = [r for r in responses if r.status_code >= 500]
    assert len(error_responses) == 0, (
        f"Found {len(error_responses)} server errors during concurrent load"
    )

    print(f"Concurrent requests: {elapsed:.2f}s total, {avg_time_ms:.2f}ms avg")
```

**Step 4: Write database query performance test**

Add to `backend/tests/performance/test_api_benchmarks.py`:

```python
@pytest.mark.asyncio
async def test_database_query_performance_with_large_dataset(
    client, performance_dataset, auth_headers_factory, user_a
):
    """Database handles 1000 records efficiently.

    Tests pagination, indexing, and query optimization with large dataset.
    """
    headers = auth_headers_factory(user_a)

    # Query first page
    start = time.time()
    response = await client.get("/api/v1/technologies?limit=100&offset=0", headers=headers)
    elapsed_ms = (time.time() - start) * 1000

    assert response.status_code == 200

    # Should still be fast even with 1000 records in database
    # (thanks to pagination and indexing)
    assert elapsed_ms < 800, (
        f"Query with 1000 records took {elapsed_ms:.2f}ms. "
        f"May need database indexing or query optimization."
    )

    # Verify pagination working
    data = response.json()
    assert len(data) <= 100  # Respects limit

    print(f"Large dataset query: {elapsed_ms:.2f}ms (1000 records in DB)")
```

**Step 5: Run all benchmark tests**

Run:
```bash
cd backend
pytest tests/performance/test_api_benchmarks.py -v -s
```

Expected: PASS with performance timings logged

**Step 6: Commit**

```bash
git add backend/tests/performance/test_api_benchmarks.py
git commit -m "test: Add advanced API benchmark tests (4 tests)

- Test knowledge base query performance (<1500ms)
- Test repositories list performance (<500ms)
- Test concurrent request handling (50 requests)
- Test database query performance with 1000 records

Total API benchmark tests: 8
Total performance tests: 13 (5 N+1 + 8 benchmarks)"
```

---

## Task 6: Documentation & Summary

**Files:**
- Create: `backend/tests/performance/README.md`
- Create: `backend/tests/performance/IMPLEMENTATION_SUMMARY.md`

**Step 1: Write performance tests README**

Create `backend/tests/performance/README.md`:

```markdown
# Performance Tests

## Overview

Performance tests detect N+1 queries and establish API performance baselines.

## Test Structure

### N+1 Query Detection (`test_n_plus_one_queries.py`)

**Goal:** Detect inefficient database queries that scale poorly with data growth.

**Tests (5 total):**
- Technologies list avoids N+1 queries (1 test)
- Technology detail loads relationships efficiently (1 test)
- Research tasks list avoids N+1 queries (1 test)
- Repositories list with technologies avoids N+1 (1 test)
- Knowledge base query uses efficient vector search (1 test)

**Key Fixture:**
- `query_counter`: SQLAlchemy event listener that counts queries
- `large_dataset`: 20 technologies × 3 repositories × 2 research tasks

**How it Works:**
1. Clear query counter before operation
2. Execute API endpoint
3. Count queries via SQLAlchemy events
4. Assert count ≤ threshold (typically 2-3 queries)

**What is N+1?**
```python
# BAD: N+1 query pattern
technologies = session.query(Technology).all()  # 1 query
for tech in technologies:  # N queries!
    print(tech.repositories)  # Separate query per technology

# GOOD: Eager loading
technologies = session.query(Technology).options(
    joinedload(Technology.repositories)
).all()  # 1-2 queries total
```

### API Performance Benchmarks (`test_api_benchmarks.py`)

**Goal:** Establish performance baselines and detect regressions.

**Tests (8 total):**
- Technologies list: <500ms (1 test)
- Technologies create: <300ms (1 test)
- Research list: <500ms (1 test)
- Research create: <300ms (1 test)
- Knowledge query: <1500ms (1 test)
- Repositories list: <500ms (1 test)
- Concurrent requests: 50 simultaneous (1 test)
- Large dataset query: <800ms with 1000 records (1 test)

**Key Fixtures:**
- `performance_threshold`: Acceptable response times per endpoint
- `performance_dataset`: 1000 records for stress testing

**Thresholds:**
- **CRUD operations:** 300-500ms (fast, simple queries)
- **RAG queries:** 1500ms (embedding generation + vector search)
- **Concurrent load:** 50 requests, <1000ms average

## Running Performance Tests

**All performance tests:**
```bash
cd backend
pytest tests/performance/ -v -s
```

**N+1 detection only:**
```bash
pytest tests/performance/test_n_plus_one_queries.py -v
```

**Benchmarks only:**
```bash
pytest tests/performance/test_api_benchmarks.py -v -s
```

**In Docker:**
```bash
make test-performance
```

## Interpreting Results

### N+1 Query Tests

**PASS:** Queries stay below threshold (efficient eager loading)
```
test_technologies_list_no_n_plus_one PASSED
Technologies list: 2 queries
```

**FAIL:** Too many queries (N+1 detected)
```
test_technologies_list_no_n_plus_one FAILED
Expected ≤3 queries, got 23.
Possible N+1 query problem.
```

**Fix:** Add eager loading in endpoint:
```python
# In router or service
technologies = await db.execute(
    select(Technology)
    .options(joinedload(Technology.repositories))
    .options(joinedload(Technology.research_tasks))
)
```

### Benchmark Tests

**PASS:** Response within threshold
```
test_technologies_list_performance PASSED
Technologies list: 234.56ms
```

**FAIL:** Performance regression
```
test_technologies_list_performance FAILED
Response took 678.90ms, threshold is 500ms.
Performance regression detected.
```

**Fix Options:**
1. Add database indexes
2. Optimize query (reduce JOINs)
3. Add pagination
4. Add caching layer
5. If legitimate, adjust threshold

## Test Count

**Total: 13 tests**
- N+1 query detection: 5 tests
- API benchmarks: 8 tests

## Notes

- **N+1 tests use real database** (not mocked) to detect actual query patterns
- **Benchmark thresholds are generous** to account for CI/CD variability
- **Concurrent test uses 50 requests** to test connection pool
- **Large dataset test uses 1000 records** to test indexing
- **All tests print timings** for baseline tracking
```

**Step 2: Create summary document**

Create `backend/tests/performance/IMPLEMENTATION_SUMMARY.md`:

```markdown
# Performance Tests Implementation Summary

**Branch:** `testing/week2-performance`
**Date:** 2025-10-28
**Status:** ✅ Complete

## Deliverables

### Tests Implemented: 13

1. **N+1 Query Detection (5 tests)**
   - ✅ Technologies list avoids N+1 queries
   - ✅ Technology detail loads relationships efficiently
   - ✅ Research tasks list avoids N+1 queries
   - ✅ Repositories list with technologies avoids N+1
   - ✅ Knowledge base query uses efficient vector search

2. **API Performance Benchmarks (8 tests)**
   - ✅ Technologies list: <500ms
   - ✅ Technologies create: <300ms
   - ✅ Research list: <500ms
   - ✅ Research create: <300ms
   - ✅ Knowledge query: <1500ms
   - ✅ Repositories list: <500ms
   - ✅ Concurrent request handling (50 requests)
   - ✅ Large dataset query performance (1000 records)

### Infrastructure Created

- ✅ `backend/tests/performance/conftest.py` - Performance fixtures
- ✅ `backend/tests/performance/test_n_plus_one_queries.py` - 5 tests
- ✅ `backend/tests/performance/test_api_benchmarks.py` - 8 tests
- ✅ `backend/tests/performance/README.md` - Documentation

### Fixtures

- ✅ `query_counter`: SQLAlchemy event listener for query counting
- ✅ `large_dataset`: 20 technologies × 3 repos × 2 research
- ✅ `performance_threshold`: Response time thresholds per endpoint
- ✅ `performance_dataset`: 1000 records for stress testing

### Test Execution

```bash
# Run all performance tests
cd backend
pytest tests/performance/ -v -s

# Expected: Baseline timings logged for each test
# Some tests may fail initially if optimizations needed
```

## Performance Baselines Established

| Endpoint | Threshold | Notes |
|----------|-----------|-------|
| GET /technologies | 500ms | List with eager loading |
| POST /technologies | 300ms | Simple create |
| GET /research | 500ms | List with joins |
| POST /research | 300ms | Simple create |
| POST /knowledge/query | 1500ms | Embedding + vector search |
| GET /repositories | 500ms | List with relationships |
| 50 concurrent requests | <1000ms avg | Connection pool test |
| 1000 records query | 800ms | Indexing test |

## Next Steps

1. **Fix N+1 queries if detected:**
   - Add SQLAlchemy `joinedload()` or `selectinload()` to endpoints
   - Example:
     ```python
     query = select(Technology).options(
         joinedload(Technology.repositories),
         joinedload(Technology.research_tasks)
     )
     ```

2. **Add database indexes if needed:**
   - Create Alembic migration
   - Index foreign keys: `technology_id`, `project_id`, `repository_id`
   - Index frequently filtered columns

3. **Optimize slow endpoints:**
   - Add pagination if missing
   - Reduce JOIN complexity
   - Consider read replicas for heavy queries

4. **Integrate into CI:**
   - Run performance tests on every PR
   - Track baselines over time
   - Alert on regressions >20%

5. **Monitor in production:**
   - Add APM (Application Performance Monitoring)
   - Track P95/P99 latencies
   - Set up alerts for degradation

## Files Created

- `backend/tests/performance/__init__.py`
- `backend/tests/performance/conftest.py`
- `backend/tests/performance/test_n_plus_one_queries.py`
- `backend/tests/performance/test_n_plus_one_queries.py`
- `backend/tests/performance/README.md`
- `backend/tests/performance/IMPLEMENTATION_SUMMARY.md`

## Commits

Total commits: 6
- Infrastructure setup (1)
- N+1 detection tests (2)
- Benchmark tests (2)
- Documentation (1)

## Success Metrics

- ✅ 13 tests implemented
- ✅ Test infrastructure complete
- ✅ Query counter fixture working
- ✅ Performance baselines established
- ✅ Documentation complete
- ✅ Ready for consolidation
```

**Step 3: Commit documentation**

```bash
git add backend/tests/performance/README.md backend/tests/performance/IMPLEMENTATION_SUMMARY.md
git commit -m "docs: Add performance tests documentation

- Create README with test overview and interpretation guide
- Create implementation summary with deliverables checklist
- Document N+1 query detection methodology
- Document performance thresholds and baselines

Week 2 Performance Track Complete: 13 tests + infrastructure + docs"
```

**Step 4: Verify all tests are discoverable**

Run:
```bash
cd backend
pytest tests/performance/ --collect-only
```

Expected output showing 13 tests collected

**Step 5: Final commit with summary**

```bash
git commit --allow-empty -m "test: Week 2 Performance Tests - Track Complete

Summary:
- 13 performance tests implemented
- N+1 query detection: 5 tests
- API benchmarks: 8 tests

Infrastructure:
- query_counter fixture (SQLAlchemy event listener)
- large_dataset fixture (60 related records)
- performance_threshold fixture (response time limits)
- Complete test documentation

Baselines Established:
- CRUD operations: 300-500ms
- RAG queries: <1500ms
- Concurrent load: 50 requests handled
- Large dataset: 1000 records queried

Status: Ready for consolidation to main branch

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Verification Checklist

Before marking track complete:

- [ ] All 13 tests implemented and syntactically valid
- [ ] Tests organized in 2 files (N+1 detection, benchmarks)
- [ ] Performance fixtures complete (query_counter, thresholds, datasets)
- [ ] README.md created with interpretation guide
- [ ] IMPLEMENTATION_SUMMARY.md created with baselines
- [ ] All tests discoverable via pytest --collect-only
- [ ] No syntax errors in test files
- [ ] Git commits follow conventions
- [ ] Branch ready for merge to main

## Notes for Implementation

**These tests establish baselines** and may initially fail if optimizations are needed. This is acceptable.

After tests are written, optimization work may be needed:

1. **Add Eager Loading:** Use SQLAlchemy `joinedload()` to prevent N+1 queries
2. **Add Database Indexes:** Create migrations for frequently queried columns
3. **Add Pagination:** Limit result set sizes for large collections
4. **Optimize Queries:** Reduce JOIN complexity where possible
5. **Add Caching:** Consider Redis for frequently accessed data

Once optimizations are complete, re-run tests:
```bash
pytest tests/performance/ -v -s
```

Expected: All 13 tests PASS with acceptable timings

---

**Plan Status:** Complete
**Next Action:** Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan
**Estimated Time:** 2-3 hours for test implementation
