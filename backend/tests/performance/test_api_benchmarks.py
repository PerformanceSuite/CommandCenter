"""API endpoint performance benchmarks."""
import time

import pytest
from sqlalchemy import select


@pytest.mark.asyncio
async def test_technology_list_response_time(
    performance_threshold, large_dataset, client, auth_headers_factory, user_a
):
    """Technology list endpoint responds within threshold (500ms)."""
    headers = auth_headers_factory(user_a)

    start = time.time()
    # Use trailing slash to avoid 307 redirect
    response = await client.get("/api/v1/technologies/", headers=headers)
    elapsed = (time.time() - start) * 1000  # Convert to ms

    assert response.status_code == 200
    assert elapsed < performance_threshold["list"], (
        f"Technology list took {elapsed:.0f}ms, "
        f"exceeds {performance_threshold['list']}ms threshold"
    )


@pytest.mark.asyncio
async def test_repository_detail_response_time(
    performance_threshold, large_dataset, client, auth_headers_factory, user_a, db_session
):
    """Repository detail endpoint responds within threshold (500ms)."""
    from app.models.repository import Repository

    # Get a repository ID from the dataset using SQLAlchemy 2.x style
    stmt = select(Repository).where(Repository.project_id == user_a.project_id).limit(1)
    result = await db_session.execute(stmt)
    repo = result.scalar_one_or_none()

    if repo is None:
        pytest.skip("No repositories found in large_dataset for this user")

    headers = auth_headers_factory(user_a)

    start = time.time()
    response = await client.get(f"/api/v1/repositories/{repo.id}", headers=headers)
    elapsed = (time.time() - start) * 1000

    assert response.status_code == 200
    assert elapsed < performance_threshold["detail"], (
        f"Repository detail took {elapsed:.0f}ms, "
        f"exceeds {performance_threshold['detail']}ms threshold"
    )


@pytest.mark.asyncio
async def test_research_task_list_pagination_performance(
    performance_threshold, performance_dataset, client, auth_headers_factory, user_a
):
    """Research task list with pagination performs within threshold (500ms)."""
    headers = auth_headers_factory(user_a)

    start = time.time()
    # Use correct endpoint: /research-tasks/ (not /research/)
    response = await client.get("/api/v1/research-tasks/", headers=headers)
    elapsed = (time.time() - start) * 1000

    assert response.status_code == 200
    assert elapsed < performance_threshold["list"], (
        f"Research list with pagination took {elapsed:.0f}ms, "
        f"exceeds {performance_threshold['list']}ms threshold"
    )
