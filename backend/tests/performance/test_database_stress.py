"""Database stress tests."""
import asyncio
import time

import pytest
from sqlalchemy import func, select

from app.models.technology import Technology, TechnologyDomain
from app.schemas.technology import TechnologyCreate


@pytest.mark.asyncio
async def test_bulk_technology_creation(performance_threshold, db_session, user_a):
    """Bulk create 100 technologies within threshold (1500ms)."""
    from app.services.technology_service import TechnologyService

    service = TechnologyService(db_session)

    start = time.time()

    # Create 100 technologies sequentially (concurrent DB writes can cause issues)
    for i in range(100):
        tech_data = TechnologyCreate(
            title=f"Bulk Tech {i}",
            domain=TechnologyDomain.AI_ML,
        )
        await service.create_technology(tech_data, project_id=user_a.project_id)

    await db_session.commit()

    elapsed = (time.time() - start) * 1000

    assert elapsed < performance_threshold["bulk_create"], (
        f"Bulk create 100 technologies took {elapsed:.0f}ms, "
        f"exceeds {performance_threshold['bulk_create']}ms threshold"
    )


@pytest.mark.asyncio
async def test_concurrent_read_queries(
    performance_threshold, large_dataset, client, auth_headers_factory, user_a
):
    """10 concurrent GET requests complete within threshold (1000ms)."""
    headers = auth_headers_factory(user_a)

    start = time.time()

    # Fire 10 concurrent requests (with trailing slash)
    tasks = [client.get("/api/v1/technologies/", headers=headers) for _ in range(10)]

    responses = await asyncio.gather(*tasks)

    elapsed = (time.time() - start) * 1000

    # All should succeed
    assert all(r.status_code == 200 for r in responses)

    # Should complete reasonably fast
    assert elapsed < 1000, f"10 concurrent requests took {elapsed:.0f}ms, exceeds 1000ms threshold"


@pytest.mark.asyncio
async def test_database_connection_pool_stress(db_session, user_a):
    """Database handles 50 rapid queries without errors."""

    async def query_database():
        # Simple query using SQLAlchemy 2.x style
        stmt = (
            select(func.count())
            .select_from(Technology)
            .where(Technology.project_id == user_a.project_id)
        )
        result = await db_session.execute(stmt)
        return result.scalar()

    # Fire 50 concurrent queries
    tasks = [query_database() for _ in range(50)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # None should be exceptions
    exceptions = [r for r in results if isinstance(r, Exception)]
    assert len(exceptions) == 0, f"{len(exceptions)} database queries failed: {exceptions[:3]}"
