"""Performance test fixtures."""
import pytest
from sqlalchemy import event
from tests.utils.factories import (
    ProjectFactory,
    RepositoryFactory,
    ResearchTaskFactory,
    TechnologyFactory,
    UserFactory,
)


@pytest.fixture
async def test_project(db_session):
    """Create a test project for performance tests."""
    return await ProjectFactory.create(
        db_session, name="Performance Test Project", owner="perftest"
    )


@pytest.fixture
async def project_a(db_session):
    """Create project A for performance tests."""
    return await ProjectFactory.create(db_session, name="Performance Project A", owner="user_a")


@pytest.fixture
async def user_a(db_session, project_a):
    """Create isolated user A with project for performance tests."""
    user = await UserFactory.create(db_session, email="perf_user_a@test.com")
    # Attach project reference for tests that need it
    user.project = project_a
    user.project_id = project_a.id
    return user


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
            queries.append(
                {"statement": statement, "parameters": parameters, "executemany": executemany}
            )

    # For async engines, use sync_engine to attach event listeners
    sync_engine = db_session.bind.sync_engine

    # Attach listener
    event.listen(sync_engine, "after_cursor_execute", receive_after_cursor_execute)

    yield queries

    # Detach listener
    event.remove(sync_engine, "after_cursor_execute", receive_after_cursor_execute)


@pytest.fixture
async def large_dataset(db_session, test_project):
    """Create dataset large enough to expose N+1 queries.

    Creates 20 technologies, each with 3 repositories and 2 research tasks.
    This generates enough data to make N+1 query problems obvious.
    """
    technologies = []

    for i in range(20):
        tech = await TechnologyFactory.create(
            db_session,
            project_id=test_project.id,
            title=f"Technology {i}",
            vendor=f"Vendor {i}",
        )

        # Add repositories for this technology
        for j in range(3):
            repo = await RepositoryFactory.create(
                db_session,
                project_id=test_project.id,
                owner=f"test-owner-{i}",
                name=f"repo-{i}-{j}",
            )
            tech.repositories.append(repo)

        # Add research tasks for this technology
        for k in range(2):
            await ResearchTaskFactory.create(
                db_session,
                project_id=test_project.id,
                title=f"Research {i}-{k}",
                technology_id=tech.id,
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
        # Generic thresholds used by tests
        "list": 500,  # List endpoints
        "detail": 500,  # Detail endpoints
        "bulk_create": 1500,  # Bulk operations
        "rag_search": 1500,  # RAG query operations
        # Specific endpoint thresholds (legacy)
        "technologies_list": 500,  # GET /api/v1/technologies
        "technologies_create": 300,  # POST /api/v1/technologies
        "research_list": 500,  # GET /api/v1/research
        "research_create": 300,  # POST /api/v1/research
        "knowledge_query": 1500,  # POST /api/v1/knowledge/query
        "repositories_list": 500,  # GET /api/v1/repositories
    }


@pytest.fixture
async def performance_dataset(db_session, test_project):
    """Create large dataset for stress testing (1000 records).

    Used for testing query performance under load.
    """
    technologies = []

    for i in range(1000):
        tech = await TechnologyFactory.create(
            db_session,
            project_id=test_project.id,
            title=f"Performance Tech {i}",
            vendor=f"Vendor {i % 100}",  # Create some duplicates
        )
        technologies.append(tech)

    await db_session.commit()
    return technologies
