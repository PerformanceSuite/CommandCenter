"""Project isolation security tests."""
import pytest
from tests.utils.factories import (
    KnowledgeEntryFactory,
    RepositoryFactory,
    ResearchTaskFactory,
    TechnologyFactory,
)

# NOTE: These tests are expected to fail until project-based isolation is fully implemented.
# They document the security requirements for multi-tenant data separation.


@pytest.mark.asyncio
@pytest.mark.xfail(reason="Project-based isolation not yet enforced on endpoints")
async def test_user_cannot_read_other_user_technologies(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot see User B's technologies."""
    # Create technology for User B
    tech_b = await TechnologyFactory.create(
        db_session, title="Secret Tech B", project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries technologies
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/technologies/", headers=headers)

    # Assert User B's technology not in results
    assert response.status_code == 200
    data = response.json()
    # Handle TechnologyListResponse format: {items: [...], total: N}
    items = data.get("items", data) if isinstance(data, dict) else data
    tech_ids = [t["id"] for t in items]
    assert tech_b.id not in tech_ids, "User A should not see User B's technology"


@pytest.mark.asyncio
@pytest.mark.xfail(reason="Project-based isolation not yet enforced on endpoints")
async def test_user_cannot_modify_other_user_technologies(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot update User B's technology."""
    # Create technology for User B
    tech_b = await TechnologyFactory.create(
        db_session, title="Tech B", project_id=user_b.project_id
    )
    await db_session.commit()

    # User A tries to modify User B's technology (uses PATCH, not PUT)
    headers = auth_headers_factory(user_a)
    response = await client.patch(
        f"/api/v1/technologies/{tech_b.id}", headers=headers, json={"title": "Hacked Title"}
    )

    # Should return 403 Forbidden or 404 Not Found (or 401 if auth fails)
    assert response.status_code in [
        401,
        403,
        404,
    ], f"User A should not be able to modify User B's technology, got {response.status_code}"


@pytest.mark.asyncio
@pytest.mark.xfail(reason="Project-based isolation not yet enforced on endpoints")
async def test_user_cannot_delete_other_user_technologies(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot delete User B's technology."""
    # Create technology for User B
    tech_b = await TechnologyFactory.create(
        db_session, title="Tech B Delete", project_id=user_b.project_id
    )
    await db_session.commit()

    # User A tries to delete User B's technology
    headers = auth_headers_factory(user_a)
    response = await client.delete(f"/api/v1/technologies/{tech_b.id}", headers=headers)

    # Should return 403 Forbidden or 404 Not Found (or 401 if auth fails)
    # Note: 204 without deleting is acceptable if isolation is enforced
    assert response.status_code in [
        401,
        403,
        404,
    ], f"User A should not be able to delete User B's technology, got {response.status_code}"


@pytest.mark.asyncio
@pytest.mark.xfail(reason="Project-based isolation not yet enforced on endpoints")
async def test_user_cannot_read_other_user_repositories(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot see User B's repositories."""
    # Create repository for User B
    repo_b = await RepositoryFactory.create(
        db_session, owner="user-b", name="secret-repo", project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries repositories
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/repositories/", headers=headers)

    # Assert User B's repository not in results
    assert response.status_code == 200
    data = response.json()
    # Handle possible list or wrapped response
    items = data.get("items", data) if isinstance(data, dict) else data
    repo_ids = [r["id"] for r in items]
    assert repo_b.id not in repo_ids, "User A should not see User B's repository"


@pytest.mark.asyncio
@pytest.mark.xfail(reason="Project-based isolation not yet enforced on endpoints")
async def test_user_cannot_read_other_user_research_tasks(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot see User B's research tasks."""
    # Create research task for User B
    research_b = await ResearchTaskFactory.create(
        db_session,
        title="Secret Research",
        description="Confidential",
        project_id=user_b.project_id,
    )
    await db_session.commit()

    # User A queries research tasks (correct endpoint is /research-tasks/)
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/research-tasks/", headers=headers)

    # Assert User B's research not in results
    assert response.status_code == 200
    data = response.json()
    # Handle possible list or wrapped response
    items = data.get("items", data) if isinstance(data, dict) else data
    research_ids = [r["id"] for r in items]
    assert research_b.id not in research_ids, "User A should not see User B's research"


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Project-based isolation not yet enforced, or KnowledgeBeast not installed"
)
async def test_user_cannot_read_other_user_knowledge_entries(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot see User B's knowledge entries."""
    # Create knowledge entry for User B
    knowledge_b = await KnowledgeEntryFactory.create(
        db_session,
        source_file="confidential.pdf",
        category="research",
        project_id=user_b.project_id,
    )
    await db_session.commit()

    # User A queries knowledge base (use /query endpoint for searching)
    headers = auth_headers_factory(user_a)
    # Note: /knowledge/ doesn't have a list all endpoint, so test with query
    response = await client.post(
        "/api/v1/knowledge/query", headers=headers, json={"query": "confidential", "limit": 100}
    )

    # Assert User B's knowledge not in results
    # Accept 200 with empty results or 404/401 if restricted
    if response.status_code == 200:
        data = response.json()
        items = data if isinstance(data, list) else data.get("items", data.get("results", []))
        entry_ids = [e.get("id") for e in items if isinstance(e, dict)]
        assert knowledge_b.id not in entry_ids, "User A should not see User B's knowledge"
    else:
        # 404 or 401 is acceptable - endpoint may not exist or require auth
        assert response.status_code in [401, 404]


@pytest.mark.asyncio
@pytest.mark.xfail(reason="Project-based isolation not yet enforced on endpoints")
async def test_technology_list_filtered_by_project(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """Technology list is filtered by user's project_id."""
    # Create technologies for both users
    tech_a1 = await TechnologyFactory.create(
        db_session, title="Tech A1", project_id=user_a.project_id
    )
    tech_a2 = await TechnologyFactory.create(
        db_session, title="Tech A2", project_id=user_a.project_id
    )
    tech_b1 = await TechnologyFactory.create(
        db_session, title="Tech B1", project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries technologies
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/technologies/", headers=headers)

    assert response.status_code == 200
    data = response.json()
    # Handle TechnologyListResponse format: {items: [...], total: N}
    items = data.get("items", data) if isinstance(data, dict) else data
    tech_ids = [t["id"] for t in items]

    # Should only see User A's technologies
    assert tech_a1.id in tech_ids
    assert tech_a2.id in tech_ids
    assert tech_b1.id not in tech_ids


@pytest.mark.asyncio
@pytest.mark.xfail(reason="Project-based isolation not yet enforced on endpoints")
async def test_repository_list_filtered_by_project(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """Repository list is filtered by user's project_id."""
    # Create repositories for both users
    repo_a = await RepositoryFactory.create(
        db_session, owner="user-a", name="repo-a", project_id=user_a.project_id
    )
    repo_b = await RepositoryFactory.create(
        db_session, owner="user-b", name="repo-b", project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries repositories
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/repositories/", headers=headers)

    assert response.status_code == 200
    data = response.json()
    # Handle possible list or wrapped response
    items = data.get("items", data) if isinstance(data, dict) else data
    repo_ids = [r["id"] for r in items]

    # Should only see User A's repositories
    assert repo_a.id in repo_ids
    assert repo_b.id not in repo_ids


@pytest.mark.asyncio
@pytest.mark.xfail(reason="Project-based isolation not yet enforced on endpoints")
async def test_research_list_filtered_by_project(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """Research task list is filtered by user's project_id."""
    # Create research tasks for both users
    research_a = await ResearchTaskFactory.create(
        db_session, title="Research A", project_id=user_a.project_id
    )
    research_b = await ResearchTaskFactory.create(
        db_session, title="Research B", project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries research tasks (correct endpoint is /research-tasks/)
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/research-tasks/", headers=headers)

    assert response.status_code == 200
    data = response.json()
    # Handle possible list or wrapped response
    items = data.get("items", data) if isinstance(data, dict) else data
    research_ids = [r["id"] for r in items]

    # Should only see User A's research
    assert research_a.id in research_ids
    assert research_b.id not in research_ids
