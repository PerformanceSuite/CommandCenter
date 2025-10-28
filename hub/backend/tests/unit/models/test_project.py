"""
Unit tests for Project model

Tests project model validation, constraints, and business logic.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Project
from tests.utils.factories import ProjectFactory


@pytest.mark.asyncio
async def test_project_creation(db_session):
    """Test basic project creation"""
    project = ProjectFactory.create_project(
        name="TestProject",
        slug="test-project",
        path="/tmp/test-project",
    )

    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    assert project.id is not None
    assert project.name == "TestProject"
    assert project.slug == "test-project"
    assert project.path == "/tmp/test-project"
    assert project.status == "stopped"
    assert project.is_configured is True


@pytest.mark.asyncio
async def test_project_name_must_be_unique(db_session):
    """Test that project names must be unique"""
    project1 = ProjectFactory.create_project(name="UniqueProject", slug="unique-1")
    project2 = ProjectFactory.create_project(name="UniqueProject", slug="unique-2")

    db_session.add(project1)
    await db_session.commit()

    db_session.add(project2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_project_slug_must_be_unique(db_session):
    """Test that project slugs must be unique"""
    project1 = ProjectFactory.create_project(name="Project1", slug="unique-slug")
    project2 = ProjectFactory.create_project(name="Project2", slug="unique-slug")

    db_session.add(project1)
    await db_session.commit()

    db_session.add(project2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_project_ports_must_be_unique(db_session):
    """Test that port numbers must be unique across projects"""
    project1 = ProjectFactory.create_project(
        name="Project1", slug="project-1", backend_port=8010
    )
    project2 = ProjectFactory.create_project(
        name="Project2", slug="project-2", backend_port=8010  # Same port
    )

    db_session.add(project1)
    await db_session.commit()

    db_session.add(project2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_project_status_transitions(db_session):
    """Test project status can transition between valid states"""
    project = ProjectFactory.create_project(status="stopped")

    db_session.add(project)
    await db_session.commit()
    assert project.status == "stopped"

    # Transition to starting
    project.status = "starting"
    await db_session.commit()
    await db_session.refresh(project)
    assert project.status == "starting"

    # Transition to running
    project.status = "running"
    await db_session.commit()
    await db_session.refresh(project)
    assert project.status == "running"

    # Transition to stopping
    project.status = "stopping"
    await db_session.commit()
    await db_session.refresh(project)
    assert project.status == "stopping"

    # Back to stopped
    project.status = "stopped"
    await db_session.commit()
    await db_session.refresh(project)
    assert project.status == "stopped"


@pytest.mark.asyncio
async def test_project_default_values(db_session):
    """Test project default values are set correctly"""
    project = Project(
        name="DefaultProject",
        slug="default-project",
        path="/tmp/default",
        backend_port=8010,
        frontend_port=3010,
        postgres_port=5442,
        redis_port=6389,
    )

    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Check defaults
    assert project.status == "stopped"
    assert project.health == "unknown"
    assert project.is_configured is False
    assert project.repo_count == 0
    assert project.tech_count == 0
    assert project.task_count == 0
    assert project.last_started is None
    assert project.last_stopped is None
    assert project.created_at is not None


@pytest.mark.asyncio
async def test_project_timestamps(db_session):
    """Test project timestamps are managed correctly"""
    project = ProjectFactory.create_project()

    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    created_at = project.created_at
    assert created_at is not None

    # Update project
    project.name = "UpdatedName"
    await db_session.commit()
    await db_session.refresh(project)

    # created_at should not change
    assert project.created_at == created_at
    # updated_at should be set
    assert project.updated_at is not None


@pytest.mark.asyncio
async def test_project_query_by_status(db_session, multiple_projects):
    """Test querying projects by status"""
    # Query running projects
    result = await db_session.execute(
        select(Project).where(Project.status == "running")
    )
    running = list(result.scalars().all())
    assert len(running) == 1
    assert running[0].name == "Project2"

    # Query stopped projects
    result = await db_session.execute(
        select(Project).where(Project.status == "stopped")
    )
    stopped = list(result.scalars().all())
    assert len(stopped) == 1
    assert stopped[0].name == "Project1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
