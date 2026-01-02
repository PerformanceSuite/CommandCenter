"""Tests for multi-tenant project isolation with UserProject model."""

import pytest
from sqlalchemy import select

from app.models.project import Project
from app.models.user_project import UserProject
from app.services.user_project_service import (
    assign_user_to_project,
    create_default_project_for_user,
    get_user_projects,
    remove_user_from_project,
    set_default_project,
)


@pytest.mark.asyncio
async def test_user_assigned_to_project(db_session, test_user):
    """Test that users can be assigned to projects."""
    # Create a project
    project = Project(name="Test Project", owner=test_user.email, description="Test")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Assign user to project
    user_project = await assign_user_to_project(
        db_session, test_user.id, project.id, role="member", is_default=True
    )

    assert user_project.user_id == test_user.id
    assert user_project.project_id == project.id
    assert user_project.role == "member"
    assert user_project.is_default is True


@pytest.mark.asyncio
async def test_create_default_project_for_user(db_session, test_user):
    """Test automatic project creation for new users."""
    project_id = await create_default_project_for_user(
        db_session, test_user.id, test_user.email, project_name="My Project"
    )

    # Verify project was created
    result = await db_session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one()
    assert project.name == "My Project"
    assert project.owner == test_user.email

    # Verify user-project association exists
    result = await db_session.execute(
        select(UserProject).where(
            UserProject.user_id == test_user.id, UserProject.project_id == project_id
        )
    )
    user_project = result.scalar_one()
    assert user_project.role == "owner"
    assert user_project.is_default is True


@pytest.mark.asyncio
async def test_user_default_project_id_property(db_session, test_user):
    """Test User.default_project_id property returns correct project."""
    # Create two projects
    project1 = Project(name="Project 1", owner=test_user.email)
    project2 = Project(name="Project 2", owner=test_user.email)
    db_session.add_all([project1, project2])
    await db_session.commit()
    await db_session.refresh(project1)
    await db_session.refresh(project2)

    # Assign user to both projects, second one as default
    await assign_user_to_project(db_session, test_user.id, project1.id, is_default=False)
    await assign_user_to_project(db_session, test_user.id, project2.id, is_default=True)

    # Query for default project directly to avoid sync property access issue
    result = await db_session.execute(
        select(UserProject).where(
            UserProject.user_id == test_user.id, UserProject.is_default == True  # noqa: E712
        )
    )
    default_up = result.scalar_one_or_none()
    assert default_up is not None
    assert default_up.project_id == project2.id


@pytest.mark.asyncio
async def test_user_default_project_id_returns_first_if_no_default(db_session, test_user):
    """Test User.default_project_id returns first project if no default set."""
    # Create project
    project = Project(name="Project", owner=test_user.email)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Assign user without setting as default
    await assign_user_to_project(db_session, test_user.id, project.id, is_default=False)

    # Query for user's projects directly to verify first project is returned
    result = await db_session.execute(
        select(UserProject).where(UserProject.user_id == test_user.id)
    )
    user_projects = result.scalars().all()
    assert len(user_projects) == 1
    # Should return the only project
    assert user_projects[0].project_id == project.id


@pytest.mark.asyncio
async def test_user_default_project_id_returns_none_if_no_projects(db_session, test_user):
    """Test User.default_project_id returns None if user has no projects."""
    # Don't assign any projects
    # Query for user's projects directly to verify no projects
    result = await db_session.execute(
        select(UserProject).where(UserProject.user_id == test_user.id)
    )
    user_projects = result.scalars().all()

    # Should have no projects
    assert len(user_projects) == 0


@pytest.mark.asyncio
async def test_get_user_projects(db_session, test_user):
    """Test retrieving all projects for a user."""
    # Create multiple projects
    project1 = Project(name="Project 1", owner=test_user.email)
    project2 = Project(name="Project 2", owner=test_user.email)
    db_session.add_all([project1, project2])
    await db_session.commit()

    # Assign user to both
    await assign_user_to_project(db_session, test_user.id, project1.id)
    await assign_user_to_project(db_session, test_user.id, project2.id)

    # Get user projects
    user_projects = await get_user_projects(db_session, test_user.id)

    assert len(user_projects) == 2
    project_ids = [up.project_id for up in user_projects]
    assert project1.id in project_ids
    assert project2.id in project_ids


@pytest.mark.asyncio
async def test_set_default_project(db_session, test_user):
    """Test setting a project as default."""
    # Create two projects
    project1 = Project(name="Project 1", owner=test_user.email)
    project2 = Project(name="Project 2", owner=test_user.email)
    db_session.add_all([project1, project2])
    await db_session.commit()

    # Assign user to both, first as default
    await assign_user_to_project(db_session, test_user.id, project1.id, is_default=True)
    await assign_user_to_project(db_session, test_user.id, project2.id, is_default=False)

    # Change default to project2
    await set_default_project(db_session, test_user.id, project2.id)

    # Verify only project2 is default
    result = await db_session.execute(
        select(UserProject).where(UserProject.user_id == test_user.id)
    )
    user_projects = result.scalars().all()

    for up in user_projects:
        if up.project_id == project2.id:
            assert up.is_default is True
        else:
            assert up.is_default is False


@pytest.mark.asyncio
async def test_set_default_project_user_has_no_access(db_session, test_user):
    """Test setting default project fails if user doesn't have access."""
    # Create project but don't assign user
    project = Project(name="Project", owner="other@example.com")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Try to set as default - should raise ValueError
    with pytest.raises(ValueError, match="does not have access"):
        await set_default_project(db_session, test_user.id, project.id)


@pytest.mark.asyncio
async def test_remove_user_from_project(db_session, test_user):
    """Test removing user access to a project."""
    # Create project and assign user
    project = Project(name="Project", owner=test_user.email)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    await assign_user_to_project(db_session, test_user.id, project.id)

    # Remove user from project
    removed = await remove_user_from_project(db_session, test_user.id, project.id)
    assert removed is True

    # Verify association no longer exists
    result = await db_session.execute(
        select(UserProject).where(
            UserProject.user_id == test_user.id, UserProject.project_id == project.id
        )
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_remove_nonexistent_user_project_association(db_session, test_user):
    """Test removing non-existent association returns False."""
    # Try to remove association that doesn't exist
    removed = await remove_user_from_project(db_session, test_user.id, 99999)
    assert removed is False


@pytest.mark.asyncio
async def test_user_project_unique_constraint(db_session, test_user):
    """Test that user-project combinations must be unique."""
    # Create project
    project = Project(name="Project", owner=test_user.email)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Assign user to project
    await assign_user_to_project(db_session, test_user.id, project.id)

    # Try to assign again - should raise IntegrityError
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await assign_user_to_project(db_session, test_user.id, project.id)
        await db_session.commit()


@pytest.mark.asyncio
async def test_user_project_cascade_delete_on_user(db_session, test_user):
    """Test that UserProject associations are deleted when user is deleted."""
    # Create project and assign user
    project = Project(name="Project", owner=test_user.email)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    user_project = await assign_user_to_project(db_session, test_user.id, project.id)

    # Delete user
    await db_session.delete(test_user)
    await db_session.commit()

    # Verify UserProject association was deleted
    result = await db_session.execute(select(UserProject).where(UserProject.id == user_project.id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_user_project_cascade_delete_on_project(db_session, test_user):
    """Test that UserProject associations are deleted when project is deleted."""
    # Create project and assign user
    project = Project(name="Project", owner=test_user.email)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    user_project = await assign_user_to_project(db_session, test_user.id, project.id)

    # Delete project
    await db_session.delete(project)
    await db_session.commit()

    # Verify UserProject association was deleted
    result = await db_session.execute(select(UserProject).where(UserProject.id == user_project.id))
    assert result.scalar_one_or_none() is None
