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
