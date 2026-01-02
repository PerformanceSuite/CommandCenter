"""Service for managing user-project relationships."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.user_project import UserProject

logger = logging.getLogger(__name__)


async def assign_user_to_project(
    db: AsyncSession,
    user_id: int,
    project_id: int,
    role: str = "member",
    is_default: bool = False,
) -> UserProject:
    """
    Assign a user to a project.

    Args:
        db: Database session
        user_id: User ID to assign
        project_id: Project ID to assign to
        role: User's role in the project (owner, admin, member, viewer)
        is_default: Whether this should be the user's default project

    Returns:
        Created UserProject association

    Raises:
        IntegrityError: If the user-project association already exists
    """
    user_project = UserProject(
        user_id=user_id, project_id=project_id, role=role, is_default=is_default
    )
    db.add(user_project)
    await db.commit()
    await db.refresh(user_project)
    logger.info(f"Assigned user {user_id} to project {project_id} with role {role}")
    return user_project


async def create_default_project_for_user(
    db: AsyncSession, user_id: int, user_email: str, project_name: str = "Default Project"
) -> int:
    """
    Create a default project and assign user as owner.

    This is typically called during user registration to ensure
    every user has at least one project.

    Args:
        db: Database session
        user_id: User ID to create project for
        user_email: User email for the owner field
        project_name: Name for the new project

    Returns:
        Created project ID
    """
    # Create project
    project = Project(
        name=project_name, owner=user_email, description="Auto-created default project"
    )
    db.add(project)
    await db.flush()

    # Assign user as owner
    await assign_user_to_project(db, user_id, project.id, role="owner", is_default=True)

    logger.info(f"Created default project {project.id} for user {user_id}")
    return project.id


async def get_user_projects(db: AsyncSession, user_id: int) -> list[UserProject]:
    """
    Get all projects a user has access to.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of UserProject associations
    """
    result = await db.execute(
        select(UserProject).where(UserProject.user_id == user_id).order_by(UserProject.created_at)
    )
    return list(result.scalars().all())


async def set_default_project(
    db: AsyncSession, user_id: int, project_id: int
) -> Optional[UserProject]:
    """
    Set a project as the user's default project.

    This will unset any existing default project for the user.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID to set as default

    Returns:
        Updated UserProject association, or None if not found

    Raises:
        ValueError: If user doesn't have access to the project
    """
    # First, verify user has access to the project
    result = await db.execute(
        select(UserProject).where(
            UserProject.user_id == user_id, UserProject.project_id == project_id
        )
    )
    user_project = result.scalar_one_or_none()

    if not user_project:
        raise ValueError(f"User {user_id} does not have access to project {project_id}")

    # Unset all other defaults for this user
    result = await db.execute(
        select(UserProject).where(UserProject.user_id == user_id, UserProject.is_default.is_(True))
    )
    for up in result.scalars().all():
        up.is_default = False

    # Set the new default
    user_project.is_default = True
    await db.commit()
    await db.refresh(user_project)

    logger.info(f"Set project {project_id} as default for user {user_id}")
    return user_project


async def remove_user_from_project(db: AsyncSession, user_id: int, project_id: int) -> bool:
    """
    Remove a user's access to a project.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID

    Returns:
        True if removed, False if association didn't exist
    """
    result = await db.execute(
        select(UserProject).where(
            UserProject.user_id == user_id, UserProject.project_id == project_id
        )
    )
    user_project = result.scalar_one_or_none()

    if not user_project:
        return False

    await db.delete(user_project)
    await db.commit()

    logger.info(f"Removed user {user_id} from project {project_id}")
    return True
