"""
Project context helpers for multi-tenant isolation

IMPORTANT: This module provides project_id resolution for the current request.
Currently defaults to project_id=1 for development. This will be replaced with
proper multi-tenant isolation once User-Project relationships are implemented.

Roadmap for Multi-Tenant Support:
1. Create UserProject association table (many-to-many)
2. Add default_project_id to User model
3. Update get_current_project_id() to use authenticated user's default project
4. Add project_id parameter to protected routes
5. Validate user has access to requested project_id
6. Remove DEFAULT_PROJECT_ID constant

See docs/DATA_ISOLATION.md for complete architecture.
"""

import logging
from typing import Optional

from fastapi import Depends

from app.auth.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

# TEMPORARY: Default project ID for single-tenant development mode
# TODO: Remove this once User-Project relationships are implemented
DEFAULT_PROJECT_ID = 1


async def get_current_project_id(
    user: Optional[User] = Depends(get_current_user),
) -> int:
    """
    Get the current project ID from authenticated user context.

    TEMPORARY IMPLEMENTATION:
    Currently returns DEFAULT_PROJECT_ID (1) for all users.
    This bypasses multi-project isolation and is a known security limitation.

    Future Implementation (when User-Project relationships exist):
    1. Get user from JWT token (already working)
    2. Fetch user's default_project_id from database
    3. Return user's default project
    4. Validate user has access to the project

    Args:
        user: Current authenticated user (optional during transition)

    Returns:
        Project ID for the current context (currently always 1)

    Security Warning:
        This implementation does NOT provide multi-tenant isolation.
        All users share project_id=1. This is acceptable for development
        but MUST be fixed before multi-project production use.
    """
    if user:
        logger.debug(
            f"Project context for user {user.email}: Using DEFAULT_PROJECT_ID={DEFAULT_PROJECT_ID}"
        )
    else:
        logger.debug(f"No authenticated user - Using DEFAULT_PROJECT_ID={DEFAULT_PROJECT_ID}")

    # TODO: When User model has project relationships:
    # if user.default_project_id:
    #     return user.default_project_id
    # raise HTTPException(
    #     status_code=status.HTTP_403_FORBIDDEN,
    #     detail="User has no assigned project"
    # )

    return DEFAULT_PROJECT_ID


async def get_optional_project_id() -> int:
    """
    Get project ID without requiring authentication.

    Used for endpoints that are transitioning to require auth but
    need to maintain backward compatibility.

    Returns:
        Project ID (currently always DEFAULT_PROJECT_ID)
    """
    return DEFAULT_PROJECT_ID
