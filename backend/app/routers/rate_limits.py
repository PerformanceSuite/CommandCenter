"""
GitHub rate limit tracking and monitoring endpoints
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from github import Github
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services.rate_limit_service import RateLimitService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rate-limits", tags=["rate-limits"])


def get_github_client() -> Github:
    """Get GitHub client"""
    return Github(settings.github_token) if settings.github_token else Github()


@router.get("/status", response_model=Dict[str, Any])
async def get_rate_limit_status(
    github: Github = Depends(get_github_client),
) -> Dict[str, Any]:
    """
    Get current GitHub API rate limit status

    Returns:
        Rate limit status for all resource types
    """
    try:
        rate_limit_service = RateLimitService(github)
        status_dict = rate_limit_service.get_rate_limit_status()

        return {"status": "success", "rate_limits": status_dict}

    except Exception as e:
        logger.error(f"Failed to get rate limit status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit status: {str(e)}",
        )


@router.post("/track", status_code=status.HTTP_201_CREATED)
async def track_rate_limit(
    db: AsyncSession = Depends(get_db),
    github: Github = Depends(get_github_client),
) -> Dict[str, str]:
    """
    Store current rate limit status in database for tracking

    Args:
        db: Database session
        github: GitHub client

    Returns:
        Success message
    """
    try:
        rate_limit_service = RateLimitService(github)
        await rate_limit_service.store_rate_limit_status(db, token=settings.github_token)

        return {
            "status": "success",
            "message": "Rate limit status tracked successfully",
        }

    except Exception as e:
        logger.error(f"Failed to track rate limit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track rate limit: {str(e)}",
        )


@router.get("/health")
async def check_rate_limit_health(
    github: Github = Depends(get_github_client),
) -> Dict[str, Any]:
    """
    Check if GitHub API rate limit is healthy (enough remaining calls)

    Returns:
        Health status
    """
    try:
        rate_limit_service = RateLimitService(github)
        status_dict = rate_limit_service.get_rate_limit_status()

        core_status = status_dict["core"]
        is_healthy = core_status["remaining"] > 100  # Arbitrary threshold

        return {
            "healthy": is_healthy,
            "core_remaining": core_status["remaining"],
            "core_limit": core_status["limit"],
            "percentage_available": 100 - core_status["percentage_used"],
            "reset_at": core_status["reset"].isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to check rate limit health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check rate limit health: {str(e)}",
        )
