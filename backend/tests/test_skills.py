"""Tests for skills API."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_skill(authenticated_client: AsyncClient):
    """Can create a skill."""
    response = await authenticated_client.post(
        "/api/v1/skills",
        json={
            "slug": "test-skill",
            "name": "Test Skill",
            "description": "A test skill",
            "content": "# Test Skill\n\nThis is a test.",
            "category": "workflow",
            "tags": ["test"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "test-skill"
    assert data["usage_count"] == 0


@pytest.mark.asyncio
async def test_get_skill_by_slug(authenticated_client: AsyncClient):
    """Can get a skill by slug."""
    # First create
    await authenticated_client.post(
        "/api/v1/skills",
        json={"slug": "findable-skill", "name": "Findable Skill", "content": "# Content"},
    )

    # Then find
    response = await authenticated_client.get(
        "/api/v1/skills/by-slug/findable-skill",
    )
    assert response.status_code == 200
    assert response.json()["slug"] == "findable-skill"


@pytest.mark.asyncio
async def test_list_skills(authenticated_client: AsyncClient):
    """Can list skills."""
    # Create a skill
    await authenticated_client.post(
        "/api/v1/skills",
        json={"slug": "list-test-skill", "name": "List Test Skill", "content": "# Content"},
    )

    # List skills
    response = await authenticated_client.get(
        "/api/v1/skills",
    )
    assert response.status_code == 200
    skills = response.json()
    assert isinstance(skills, list)
    assert len(skills) > 0


@pytest.mark.asyncio
async def test_update_skill(authenticated_client: AsyncClient):
    """Can update a skill."""
    # Create skill
    create_resp = await authenticated_client.post(
        "/api/v1/skills",
        json={"slug": "update-test", "name": "Update Test", "content": "# Original Content"},
    )
    skill_id = create_resp.json()["id"]

    # Update skill
    response = await authenticated_client.patch(
        f"/api/v1/skills/{skill_id}", json={"name": "Updated Name", "content": "# Updated Content"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["content"] == "# Updated Content"


@pytest.mark.asyncio
async def test_delete_skill(authenticated_client: AsyncClient):
    """Can delete a skill."""
    # Create skill
    create_resp = await authenticated_client.post(
        "/api/v1/skills",
        json={"slug": "delete-test", "name": "Delete Test", "content": "# Content"},
    )
    skill_id = create_resp.json()["id"]

    # Delete skill
    response = await authenticated_client.delete(
        f"/api/v1/skills/{skill_id}",
    )
    assert response.status_code == 204

    # Verify deleted
    get_resp = await authenticated_client.get(
        f"/api/v1/skills/{skill_id}",
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_record_usage(authenticated_client: AsyncClient):
    """Can record skill usage."""
    # Create skill
    create_resp = await authenticated_client.post(
        "/api/v1/skills", json={"slug": "usage-test", "name": "Usage Test", "content": "# Content"}
    )
    skill_id = create_resp.json()["id"]

    # Record usage
    response = await authenticated_client.post(
        "/api/v1/skills/usage", json={"skill_id": skill_id, "outcome": "success"}
    )
    assert response.status_code == 201

    # Check count updated
    skill_resp = await authenticated_client.get(
        f"/api/v1/skills/{skill_id}",
    )
    data = skill_resp.json()
    assert data["usage_count"] == 1
    assert data["success_count"] == 1
    assert data["effectiveness_score"] > 0


@pytest.mark.asyncio
async def test_record_multiple_usages(authenticated_client: AsyncClient):
    """Effectiveness score updates correctly."""
    # Create skill
    create_resp = await authenticated_client.post(
        "/api/v1/skills",
        json={"slug": "effectiveness-test", "name": "Effectiveness Test", "content": "# Content"},
    )
    skill_id = create_resp.json()["id"]

    # Record 2 successes
    await authenticated_client.post(
        "/api/v1/skills/usage", json={"skill_id": skill_id, "outcome": "success"}
    )
    await authenticated_client.post(
        "/api/v1/skills/usage", json={"skill_id": skill_id, "outcome": "success"}
    )

    # Record 1 failure
    await authenticated_client.post(
        "/api/v1/skills/usage", json={"skill_id": skill_id, "outcome": "failure"}
    )

    # Check effectiveness score (2/3 = 0.666...)
    skill_resp = await authenticated_client.get(
        f"/api/v1/skills/{skill_id}",
    )
    data = skill_resp.json()
    assert data["usage_count"] == 3
    assert data["success_count"] == 2
    assert data["failure_count"] == 1
    assert abs(data["effectiveness_score"] - 0.666) < 0.01


@pytest.mark.asyncio
async def test_search_skills(authenticated_client: AsyncClient):
    """Can search skills."""
    # Create skills
    await authenticated_client.post(
        "/api/v1/skills",
        json={
            "slug": "parallel-agent",
            "name": "Parallel Agents",
            "content": "Multi-agent patterns",
            "category": "workflow",
        },
    )
    await authenticated_client.post(
        "/api/v1/skills",
        json={
            "slug": "single-agent",
            "name": "Single Agent",
            "content": "Simple patterns",
            "category": "pattern",
        },
    )

    # Search by query
    response = await authenticated_client.post("/api/v1/skills/search", json={"query": "parallel"})
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert any(s["slug"] == "parallel-agent" for s in results)

    # Search by category
    response = await authenticated_client.post(
        "/api/v1/skills/search", json={"category": "pattern"}
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert any(s["slug"] == "single-agent" for s in results)


@pytest.mark.asyncio
async def test_duplicate_slug_rejected(authenticated_client: AsyncClient):
    """Cannot create skill with duplicate slug."""
    # Create first skill
    await authenticated_client.post(
        "/api/v1/skills",
        json={"slug": "duplicate-test", "name": "First Skill", "content": "# Content"},
    )

    # Try to create duplicate
    response = await authenticated_client.post(
        "/api/v1/skills",
        json={"slug": "duplicate-test", "name": "Second Skill", "content": "# Content"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_nonexistent_skill(authenticated_client: AsyncClient):
    """Returns 404 for nonexistent skill."""
    response = await authenticated_client.get(
        "/api/v1/skills/99999",
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_by_effectiveness(authenticated_client: AsyncClient):
    """Can filter skills by effectiveness score."""
    # Create skill with high effectiveness
    create_resp = await authenticated_client.post(
        "/api/v1/skills",
        json={"slug": "high-effectiveness", "name": "High Effectiveness", "content": "# Content"},
    )
    skill_id = create_resp.json()["id"]

    # Record 3 successes
    for _ in range(3):
        await authenticated_client.post(
            "/api/v1/skills/usage", json={"skill_id": skill_id, "outcome": "success"}
        )

    # Create skill with low effectiveness
    create_resp2 = await authenticated_client.post(
        "/api/v1/skills",
        json={"slug": "low-effectiveness", "name": "Low Effectiveness", "content": "# Content"},
    )
    skill_id2 = create_resp2.json()["id"]

    # Record 1 success, 2 failures
    await authenticated_client.post(
        "/api/v1/skills/usage", json={"skill_id": skill_id2, "outcome": "success"}
    )
    for _ in range(2):
        await authenticated_client.post(
            "/api/v1/skills/usage", json={"skill_id": skill_id2, "outcome": "failure"}
        )

    # Search for high effectiveness skills (>0.8)
    response = await authenticated_client.post(
        "/api/v1/skills/search", json={"min_effectiveness": 0.8}
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert any(s["slug"] == "high-effectiveness" for s in results)
    assert not any(s["slug"] == "low-effectiveness" for s in results)
