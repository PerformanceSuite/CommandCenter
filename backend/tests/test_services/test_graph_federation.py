"""
Tests for GraphService federation query methods.

Phase 1, Task 1.3: Federation Query Service Methods
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.graph import CrossProjectLink
from app.models.project import Project
from app.services.graph_service import GraphService


@pytest.fixture
async def sample_projects(db_session: AsyncSession) -> tuple[Project, Project, Project]:
    """Create sample projects for cross-project link testing."""
    project1 = Project(name="Project Alpha", owner="org1", description="First project")
    project2 = Project(name="Project Beta", owner="org1", description="Second project")
    project3 = Project(name="Project Gamma", owner="org2", description="Third project")

    db_session.add_all([project1, project2, project3])
    await db_session.commit()
    await db_session.refresh(project1)
    await db_session.refresh(project2)
    await db_session.refresh(project3)

    return project1, project2, project3


@pytest.fixture
async def sample_cross_project_links(
    db_session: AsyncSession, sample_projects: tuple[Project, Project, Project]
) -> list[CrossProjectLink]:
    """Create sample cross-project links for testing."""
    project1, project2, project3 = sample_projects

    links = [
        # Project 1 -> Project 2 (symbol calls)
        CrossProjectLink(
            source_project_id=project1.id,
            source_entity_type="symbol",
            source_entity_id=100,
            target_project_id=project2.id,
            target_entity_type="symbol",
            target_entity_id=200,
            relationship_type="calls",
            metadata_={"caller": "main.py", "callee": "utils.py"},
        ),
        # Project 1 -> Project 2 (symbol imports)
        CrossProjectLink(
            source_project_id=project1.id,
            source_entity_type="symbol",
            source_entity_id=101,
            target_project_id=project2.id,
            target_entity_type="symbol",
            target_entity_id=201,
            relationship_type="imports",
            metadata_={"module": "shared_lib"},
        ),
        # Project 2 -> Project 3 (service depends_on)
        CrossProjectLink(
            source_project_id=project2.id,
            source_entity_type="service",
            source_entity_id=300,
            target_project_id=project3.id,
            target_entity_type="service",
            target_entity_id=400,
            relationship_type="depends_on",
            metadata_={"api_version": "v2"},
        ),
        # Project 1 -> Project 3 (file references)
        CrossProjectLink(
            source_project_id=project1.id,
            source_entity_type="file",
            source_entity_id=500,
            target_project_id=project3.id,
            target_entity_type="file",
            target_entity_id=600,
            relationship_type="references",
            metadata_=None,
        ),
    ]

    db_session.add_all(links)
    await db_session.commit()

    for link in links:
        await db_session.refresh(link)

    return links


@pytest.fixture
def graph_service(db_session: AsyncSession) -> GraphService:
    """Create GraphService instance for testing."""
    return GraphService(db_session)


class TestQueryEcosystemLinks:
    """Test suite for query_ecosystem_links method."""

    async def test_query_ecosystem_links_no_filters(
        self, graph_service: GraphService, sample_cross_project_links: list[CrossProjectLink]
    ):
        """Query all cross-project links in ecosystem without filters."""
        result = await graph_service.query_ecosystem_links()

        assert len(result) == 4
        # Verify all links are cross-project (source != target)
        assert all(link.source_project_id != link.target_project_id for link in result)

    async def test_query_ecosystem_links_by_entity_types(
        self, graph_service: GraphService, sample_cross_project_links: list[CrossProjectLink]
    ):
        """Query cross-project links filtered by entity types."""
        result = await graph_service.query_ecosystem_links(entity_types=["symbol"])

        assert len(result) >= 2
        # All results should have symbol as source or target entity type
        for link in result:
            assert link.source_entity_type == "symbol" or link.target_entity_type == "symbol"

    async def test_query_ecosystem_links_by_relationship_types(
        self, graph_service: GraphService, sample_cross_project_links: list[CrossProjectLink]
    ):
        """Query cross-project links filtered by relationship types."""
        result = await graph_service.query_ecosystem_links(relationship_types=["calls", "imports"])

        assert len(result) == 2
        assert all(link.relationship_type in ["calls", "imports"] for link in result)

    async def test_query_ecosystem_links_by_source_project(
        self,
        graph_service: GraphService,
        sample_cross_project_links: list[CrossProjectLink],
        sample_projects: tuple[Project, Project, Project],
    ):
        """Filter by source project IDs."""
        project1, _, _ = sample_projects

        result = await graph_service.query_ecosystem_links(source_project_ids=[project1.id])

        assert len(result) == 3  # Project 1 has 3 outgoing links
        assert all(link.source_project_id == project1.id for link in result)

    async def test_query_ecosystem_links_by_target_project(
        self,
        graph_service: GraphService,
        sample_cross_project_links: list[CrossProjectLink],
        sample_projects: tuple[Project, Project, Project],
    ):
        """Filter by target project IDs."""
        _, project2, _ = sample_projects

        result = await graph_service.query_ecosystem_links(target_project_ids=[project2.id])

        assert len(result) == 2  # Project 2 has 2 incoming links
        assert all(link.target_project_id == project2.id for link in result)

    async def test_query_ecosystem_links_combined_filters(
        self,
        graph_service: GraphService,
        sample_cross_project_links: list[CrossProjectLink],
        sample_projects: tuple[Project, Project, Project],
    ):
        """Query with multiple filters combined."""
        project1, project2, _ = sample_projects

        result = await graph_service.query_ecosystem_links(
            entity_types=["symbol"],
            relationship_types=["calls"],
            source_project_ids=[project1.id],
            target_project_ids=[project2.id],
        )

        assert len(result) == 1
        link = result[0]
        assert link.source_project_id == project1.id
        assert link.target_project_id == project2.id
        assert link.relationship_type == "calls"
        assert link.source_entity_type == "symbol"

    async def test_query_ecosystem_links_with_limit(
        self, graph_service: GraphService, sample_cross_project_links: list[CrossProjectLink]
    ):
        """Query with limit parameter."""
        result = await graph_service.query_ecosystem_links(limit=2)

        assert len(result) == 2

    async def test_query_ecosystem_links_empty_result(
        self, graph_service: GraphService, sample_cross_project_links: list[CrossProjectLink]
    ):
        """Query with filters that return no results."""
        result = await graph_service.query_ecosystem_links(relationship_types=["nonexistent_type"])

        assert len(result) == 0

    async def test_query_ecosystem_links_service_entity_type(
        self, graph_service: GraphService, sample_cross_project_links: list[CrossProjectLink]
    ):
        """Query cross-project links for service entities."""
        result = await graph_service.query_ecosystem_links(entity_types=["service"])

        assert len(result) == 1
        link = result[0]
        assert link.source_entity_type == "service" or link.target_entity_type == "service"
        assert link.relationship_type == "depends_on"
