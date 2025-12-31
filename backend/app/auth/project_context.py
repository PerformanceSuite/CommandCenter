"""
Project context helpers for multi-tenant isolation.

Provides project_id resolution from:
1. X-Project-ID header (explicit override)
2. User's default project
3. First available project for user
"""

import logging
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.database import get_async_session
from app.models.user import User
from app.models.user_project import UserProject

logger = logging.getLogger(__name__)


async def get_current_project_id(
    user: User = Depends(get_current_user),
    x_project_id: Optional[int] = Header(None, alias="X-Project-ID"),
    db: AsyncSession = Depends(get_async_session),
) -> int:
    """
    Get the current project ID from authenticated user context.

    Resolution order:
    1. X-Project-ID header (if provided and user has access)
    2. User's default project
    3. User's first available project

    Args:
        user: Current authenticated user (required)
        x_project_id: Optional project ID from header
        db: Database session

    Returns:
        Project ID for the current context

    Raises:
        HTTPException 403: If user has no project access or invalid project requested
    """
    # If explicit project requested via header
    if x_project_id is not None:
        has_access = await _user_has_project_access(db, user.id, x_project_id)
        if not has_access:
            logger.warning(f"User {user.email} denied access to project {x_project_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No access to project {x_project_id}",
            )
        logger.debug(f"Using requested project {x_project_id} for user {user.email}")
        return x_project_id

    # Get user's default or first project
    project_id = await _get_user_default_project(db, user.id)
    if project_id is None:
        logger.warning(f"User {user.email} has no assigned projects")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No project assigned. Contact administrator.",
        )

    logger.debug(f"Using default project {project_id} for user {user.email}")
    return project_id


async def get_optional_project_id(
    user: Optional[User] = Depends(get_optional_user),
    x_project_id: Optional[int] = Header(None, alias="X-Project-ID"),
    db: AsyncSession = Depends(get_async_session),
) -> Optional[int]:
    """
    Get project ID without requiring authentication.

    Used for endpoints transitioning to require auth.
    Returns None if no user or no project.
    """
    if user is None:
        return None

    try:
        return await get_current_project_id(user, x_project_id, db)
    except HTTPException:
        return None


async def _user_has_project_access(db: AsyncSession, user_id: int, project_id: int) -> bool:
    """Check if user has access to a specific project."""
    result = await db.execute(
        select(UserProject).where(
            UserProject.user_id == user_id, UserProject.project_id == project_id
        )
    )
    return result.scalar_one_or_none() is not None


async def _get_user_default_project(db: AsyncSession, user_id: int) -> Optional[int]:
    """Get user's default project ID, or first available."""
    # Try to get default project
    result = await db.execute(
        select(UserProject).where(
            UserProject.user_id == user_id, UserProject.is_default == True  # noqa: E712
        )
    )
    default = result.scalar_one_or_none()
    if default:
        return default.project_id

    # Fall back to first available
    result = await db.execute(
        select(UserProject).where(UserProject.user_id == user_id).order_by(UserProject.created_at)
    )
    first = result.scalar_one_or_none()
    return first.project_id if first else None
