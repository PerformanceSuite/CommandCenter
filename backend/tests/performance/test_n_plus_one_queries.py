"""N+1 query detection tests."""
import pytest
from tests.utils.factories import KnowledgeEntryFactory


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
        f"Queries executed:\n"
        + "\n".join([f"  - {q['statement'][:100]}..." for q in query_counter])
    )

    # Verify response still correct
    assert response.status_code == 200
    technologies = response.json()
    assert len(technologies) >= 20  # Should see all 20 created


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
    assert (
        num_queries <= 2
    ), f"Expected ≤2 queries for detail view, got {num_queries}. " f"Queries:\n" + "\n".join(
        [f"  - {q['statement'][:100]}..." for q in query_counter]
    )

    assert response.status_code == 200
    data = response.json()
    assert "repositories" in data or "research_tasks" in data


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
        f"Queries:\n" + "\n".join([f"  - {q['statement'][:80]}..." for q in query_counter])
    )

    assert response.status_code == 200


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
        f"Queries:\n" + "\n".join([f"  - {q['statement'][:80]}..." for q in query_counter])
    )

    assert response.status_code == 200


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
            project_id=user_a.project_id,
            title=f"Knowledge Entry {i}",
            source_file=f"doc-{i}.pdf",
            category="research",
        )
    await db_session.commit()

    # Clear setup queries
    query_counter.clear()

    headers = auth_headers_factory(user_a)
    response = await client.post(
        "/api/v1/knowledge/query", headers=headers, json={"query": "test query", "top_k": 5}
    )

    num_queries = len(query_counter)

    # RAG query should be efficient:
    # - Vector similarity search (1 query)
    # - Metadata lookup (1 query)
    # Total ≤3 queries (including any filtering)
    assert (
        num_queries <= 3
    ), f"Expected ≤3 queries for RAG search, got {num_queries}. " f"Queries:\n" + "\n".join(
        [f"  - {q['statement'][:80]}..." for q in query_counter]
    )

    assert response.status_code == 200
