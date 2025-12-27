"""
Unit tests for Technology model
"""

from datetime import datetime

import pytest
from tests.utils import create_test_project, create_test_technology

from app.models.technology import Technology, TechnologyDomain, TechnologyStatus


@pytest.mark.unit
@pytest.mark.db
class TestTechnologyModel:
    """Test Technology database model"""

    async def test_create_technology(self, db_session):
        """Test creating a technology"""
        tech = await create_test_technology(db_session)

        assert tech.id is not None
        assert tech.title == "Python"
        assert tech.domain is not None  # Technology uses domain, not category
        assert tech.status is not None  # Technology uses status, not ring
        assert isinstance(tech.created_at, datetime)

    async def test_technology_with_domain(self, db_session):
        """Test technology with specific domain"""
        project = await create_test_project(db_session)
        tech = Technology(
            title="TensorFlow",
            domain=TechnologyDomain.AI_ML,
            status=TechnologyStatus.RESEARCH,
            project_id=project.id,
        )
        db_session.add(tech)
        await db_session.commit()
        await db_session.refresh(tech)

        assert tech.domain == TechnologyDomain.AI_ML
        assert tech.status == TechnologyStatus.RESEARCH

    async def test_technology_default_values(self, db_session):
        """Test technology default values"""
        project = await create_test_project(db_session)
        tech = Technology(title="NewTech", project_id=project.id)
        db_session.add(tech)
        await db_session.commit()
        await db_session.refresh(tech)

        assert tech.domain == TechnologyDomain.OTHER
        assert tech.status == TechnologyStatus.DISCOVERY
        assert tech.relevance_score == 50
        assert tech.priority == 3
        assert tech.created_at is not None

    async def test_technology_unique_title(self, db_session):
        """Test that technology title must be unique"""
        await create_test_technology(db_session, title="UniqueTitle")

        # Attempting to create another tech with same title should fail
        with pytest.raises(Exception):
            await create_test_technology(db_session, title="UniqueTitle")

    async def test_technology_with_urls(self, db_session):
        """Test technology with external URLs"""
        tech = await create_test_technology(
            db_session,
            title="FastAPI",
            documentation_url="https://fastapi.tiangolo.com",
            repository_url="https://github.com/tiangolo/fastapi",
            website_url="https://fastapi.tiangolo.com",
        )

        assert tech.documentation_url == "https://fastapi.tiangolo.com"
        assert tech.repository_url == "https://github.com/tiangolo/fastapi"
        assert tech.website_url == "https://fastapi.tiangolo.com"

    async def test_technology_with_tags(self, db_session):
        """Test technology with tags"""
        tech = await create_test_technology(
            db_session, title="React", tags="frontend,javascript,ui,library"
        )

        assert tech.tags == "frontend,javascript,ui,library"
        tag_list = tech.tags.split(",")
        assert len(tag_list) == 4
        assert "frontend" in tag_list

    async def test_technology_status_transitions(self, db_session):
        """Test technology status updates"""
        tech = await create_test_technology(db_session)
        assert tech.status == TechnologyStatus.DISCOVERY

        # Update status
        tech.status = TechnologyStatus.RESEARCH
        await db_session.commit()
        await db_session.refresh(tech)
        assert tech.status == TechnologyStatus.RESEARCH

        tech.status = TechnologyStatus.IMPLEMENTATION
        await db_session.commit()
        await db_session.refresh(tech)
        assert tech.status == TechnologyStatus.IMPLEMENTATION

    async def test_technology_relevance_and_priority(self, db_session):
        """Test technology relevance score and priority"""
        tech = await create_test_technology(
            db_session, title="HighPriority", relevance_score=95, priority=5
        )

        assert tech.relevance_score == 95
        assert tech.priority == 5

    async def test_technology_with_full_details(self, db_session):
        """Test technology with all fields populated"""
        project = await create_test_project(db_session)
        tech = Technology(
            title="Comprehensive Tech",
            vendor="Tech Corp",
            domain=TechnologyDomain.AI_ML,
            status=TechnologyStatus.EVALUATION,
            relevance_score=80,
            priority=4,
            description="A comprehensive technology",
            notes="Some implementation notes",
            use_cases="Use case 1, Use case 2",
            documentation_url="https://docs.example.com",
            repository_url="https://github.com/example/repo",
            website_url="https://example.com",
            tags="ai,ml,production",
            project_id=project.id,
        )
        db_session.add(tech)
        await db_session.commit()
        await db_session.refresh(tech)

        assert tech.vendor == "Tech Corp"
        assert tech.description == "A comprehensive technology"
        assert tech.notes == "Some implementation notes"
        assert tech.use_cases == "Use case 1, Use case 2"

    async def test_technology_repr(self, db_session):
        """Test technology string representation"""
        tech = await create_test_technology(db_session)
        repr_str = repr(tech)

        assert "Technology" in repr_str
        assert str(tech.id) in repr_str
        assert tech.title in repr_str
