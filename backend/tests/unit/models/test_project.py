"""
Unit tests for Project model
"""

from datetime import datetime

import pytest
from tests.utils import create_test_project

from app.models.project import Project


@pytest.mark.unit
@pytest.mark.db
class TestProjectModel:
    """Test Project database model"""

    async def test_create_project(self, db_session):
        """Test creating a project"""
        project = await create_test_project(db_session)

        assert project.id is not None
        assert project.name == "Test Project"
        assert project.owner == "testowner"
        assert project.description == "A test project for unit testing"
        assert isinstance(project.created_at, datetime)

    async def test_project_empty_name_validation(self, db_session):
        """Empty project name should raise error"""
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            project = Project(name="", owner="testowner", description="Test")
            db_session.add(project)
            await db_session.commit()

    async def test_project_whitespace_name_validation(self, db_session):
        """Whitespace-only project name should raise error"""
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            project = Project(name="   ", owner="testowner", description="Test")
            db_session.add(project)
            await db_session.commit()

    async def test_project_long_name_validation(self, db_session):
        """Project name exceeding max length should raise error"""
        long_name = "a" * 300

        with pytest.raises(ValueError, match="Project name cannot exceed 255 characters"):
            project = Project(name=long_name, owner="testowner", description="Test")
            db_session.add(project)
            await db_session.commit()

    async def test_project_max_length_name(self, db_session):
        """Project name at max length should be accepted"""
        max_length_name = "a" * 255
        project = await create_test_project(db_session, name=max_length_name)

        assert len(project.name) == 255
        assert project.name == max_length_name

    async def test_project_unique_owner_name_constraint(self, db_session):
        """Test that owner + name combination must be unique"""
        await create_test_project(db_session, name="UniqueProject", owner="owner1")

        # Same name with different owner should work
        project2 = await create_test_project(db_session, name="UniqueProject", owner="owner2")
        assert project2.id is not None

        # Same owner + name should fail
        with pytest.raises(Exception):
            await create_test_project(db_session, name="UniqueProject", owner="owner1")

    async def test_project_relationships_initialization(self, db_session):
        """Project should initialize with empty relationships"""
        from sqlalchemy.orm import selectinload

        project = await create_test_project(db_session)

        # Re-query with eager loading to avoid lazy-load in async context
        from sqlalchemy import select

        from app.models.project import Project

        stmt = (
            select(Project)
            .where(Project.id == project.id)
            .options(
                selectinload(Project.technologies),
                selectinload(Project.repositories),
                selectinload(Project.research_tasks),
                selectinload(Project.knowledge_entries),
                selectinload(Project.webhook_configs),
                selectinload(Project.webhook_events),
                selectinload(Project.webhook_deliveries),
            )
        )
        result = await db_session.execute(stmt)
        loaded_project = result.scalar_one()

        assert loaded_project.technologies == []
        assert loaded_project.repositories == []
        assert loaded_project.research_tasks == []
        assert loaded_project.knowledge_entries == []
        assert loaded_project.webhook_configs == []
        assert loaded_project.webhook_events == []
        assert loaded_project.webhook_deliveries == []

    async def test_project_with_full_details(self, db_session):
        """Test project with all fields populated"""
        project = await create_test_project(
            db_session,
            name="Comprehensive Project",
            owner="john_doe",
            description="A detailed project description with all information",
        )

        assert project.name == "Comprehensive Project"
        assert project.owner == "john_doe"
        assert project.description == "A detailed project description with all information"

    async def test_project_update_timestamp(self, db_session):
        """Test that updated_at timestamp changes on update"""
        project = await create_test_project(db_session)
        original_updated_at = project.updated_at

        # Update the project
        project.description = "Updated description"
        await db_session.commit()
        await db_session.refresh(project)

        assert project.updated_at > original_updated_at
        assert project.description == "Updated description"

    async def test_project_without_description(self, db_session):
        """Test project can be created without description"""
        project = Project(name="Minimal Project", owner="testowner")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert project.description is None
        assert project.name == "Minimal Project"

    async def test_project_repr(self, db_session):
        """Test project string representation"""
        project = await create_test_project(db_session)
        repr_str = repr(project)

        assert "Project" in repr_str
        assert str(project.id) in repr_str
        assert project.name in repr_str
        assert project.owner in repr_str
