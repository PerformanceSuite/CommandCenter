"""Project isolation security tests."""
import pytest
from tests.utils.factories import (
    TechnologyFactory,
    RepositoryFactory,
    ResearchTaskFactory,
    KnowledgeEntryFactory
)


@pytest.mark.asyncio
async def test_user_cannot_read_other_user_technologies(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot see User B's technologies."""
    # Create technology for User B
    tech_b = await TechnologyFactory.create(
        db_session,
        title="Secret Tech B",
        domain="ai",
        project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries technologies
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/technologies", headers=headers)

    # Assert User B's technology not in results
    assert response.status_code == 200
    tech_ids = [t["id"] for t in response.json()]
    assert tech_b.id not in tech_ids, "User A should not see User B's technology"


@pytest.mark.asyncio
async def test_user_cannot_modify_other_user_technologies(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot update User B's technology."""
    # Create technology for User B
    tech_b = await TechnologyFactory.create(
        db_session,
        title="Tech B",
        domain="cloud",
        project_id=user_b.project_id
    )
    await db_session.commit()

    # User A tries to modify User B's technology
    headers = auth_headers_factory(user_a)
    response = await client.put(
        f"/api/v1/technologies/{tech_b.id}",
        headers=headers,
        json={"title": "Hacked Title"}
    )

    # Should return 403 Forbidden or 404 Not Found
    assert response.status_code in [403, 404], (
        "User A should not be able to modify User B's technology"
    )


@pytest.mark.asyncio
async def test_user_cannot_delete_other_user_technologies(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot delete User B's technology."""
    # Create technology for User B
    tech_b = await TechnologyFactory.create(
        db_session,
        title="Tech B Delete",
        domain="audio",
        project_id=user_b.project_id
    )
    await db_session.commit()

    # User A tries to delete User B's technology
    headers = auth_headers_factory(user_a)
    response = await client.delete(
        f"/api/v1/technologies/{tech_b.id}",
        headers=headers
    )

    # Should return 403 Forbidden or 404 Not Found
    assert response.status_code in [403, 404], (
        "User A should not be able to delete User B's technology"
    )


@pytest.mark.asyncio
async def test_user_cannot_read_other_user_repositories(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot see User B's repositories."""
    # Create repository for User B
    repo_b = await RepositoryFactory.create(
        db_session,
        owner="user-b",
        name="secret-repo",
        project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries repositories
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/repositories", headers=headers)

    # Assert User B's repository not in results
    assert response.status_code == 200
    repo_ids = [r["id"] for r in response.json()]
    assert repo_b.id not in repo_ids, "User A should not see User B's repository"


@pytest.mark.asyncio
async def test_user_cannot_read_other_user_research_tasks(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot see User B's research tasks."""
    # Create research task for User B
    research_b = await ResearchTaskFactory.create(
        db_session,
        title="Secret Research",
        description="Confidential",
        project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries research tasks
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/research", headers=headers)

    # Assert User B's research not in results
    assert response.status_code == 200
    research_ids = [r["id"] for r in response.json()]
    assert research_b.id not in research_ids, "User A should not see User B's research"


@pytest.mark.asyncio
async def test_user_cannot_read_other_user_knowledge_entries(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot see User B's knowledge entries."""
    # Create knowledge entry for User B
    knowledge_b = await KnowledgeEntryFactory.create(
        db_session,
        source="confidential.pdf",
        category="research",
        project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries knowledge base
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/knowledge/entries", headers=headers)

    # Assert User B's knowledge not in results
    assert response.status_code == 200
    entry_ids = [e["id"] for e in response.json()]
    assert knowledge_b.id not in entry_ids, "User A should not see User B's knowledge"
