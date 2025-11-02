"""
GitHub API rate limiting service with tracking and exponential backoff
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from functools import wraps
import hashlib

from github import Github, GithubException, RateLimitExceededException
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GitHubRateLimit

logger = logging.getLogger(__name__)


class RateLimitService:
    """Service for managing GitHub API rate limits"""

    def __init__(self, github_client: Github):
        """
        Initialize rate limit service

        Args:
            github_client: PyGithub client instance
        """
        self.github = github_client

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status from GitHub

        Returns:
            Dictionary with rate limit information for different resources
        """
        try:
            rate_limits = self.github.get_rate_limit()

            return {
                "core": {
                    "limit": rate_limits.core.limit,
                    "remaining": rate_limits.core.remaining,
                    "reset": rate_limits.core.reset,
                    "used": rate_limits.core.limit - rate_limits.core.remaining,
                    "percentage_used": (
                        (rate_limits.core.limit - rate_limits.core.remaining)
                        / rate_limits.core.limit
                        * 100
                        if rate_limits.core.limit > 0
                        else 0
                    ),
                },
                "search": {
                    "limit": rate_limits.search.limit,
                    "remaining": rate_limits.search.remaining,
                    "reset": rate_limits.search.reset,
                    "used": rate_limits.search.limit - rate_limits.search.remaining,
                    "percentage_used": (
                        (rate_limits.search.limit - rate_limits.search.remaining)
                        / rate_limits.search.limit
                        * 100
                        if rate_limits.search.limit > 0
                        else 0
                    ),
                },
                "graphql": {
                    "limit": rate_limits.graphql.limit,
                    "remaining": rate_limits.graphql.remaining,
                    "reset": rate_limits.graphql.reset,
                    "used": rate_limits.graphql.limit - rate_limits.graphql.remaining,
                    "percentage_used": (
                        (rate_limits.graphql.limit - rate_limits.graphql.remaining)
                        / rate_limits.graphql.limit
                        * 100
                        if rate_limits.graphql.limit > 0
                        else 0
                    ),
                },
            }
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            raise

    async def store_rate_limit_status(self, db: AsyncSession, token: Optional[str] = None) -> None:
        """
        Store current rate limit status in database

        Args:
            db: Database session
            token: Optional token to track (will be hashed)
        """
        try:
            status = self.get_rate_limit_status()
            token_hash = None
            if token:
                token_hash = hashlib.sha256(token.encode()).hexdigest()

            # Store each resource type
            for resource_type, data in status.items():
                rate_limit = GitHubRateLimit(
                    resource_type=resource_type,
                    limit=data["limit"],
                    remaining=data["remaining"],
                    reset_at=data["reset"],
                    token_hash=token_hash,
                    checked_at=datetime.utcnow(),
                )
                db.add(rate_limit)

            await db.commit()
            logger.info(
                f"Stored rate limit status: {status['core']['remaining']}/{status['core']['limit']} remaining"
            )

        except Exception as e:
            logger.error(f"Failed to store rate limit status: {e}")
            await db.rollback()

    def check_rate_limit_available(
        self, resource_type: str = "core", min_remaining: int = 10
    ) -> bool:
        """
        Check if rate limit is available

        Args:
            resource_type: Type of resource (core, search, graphql)
            min_remaining: Minimum remaining calls required

        Returns:
            True if rate limit is available
        """
        try:
            status = self.get_rate_limit_status()
            return status[resource_type]["remaining"] >= min_remaining
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return False

    async def wait_for_rate_limit_reset(self, resource_type: str = "core") -> None:
        """
        Wait until rate limit resets

        Args:
            resource_type: Type of resource (core, search, graphql)
        """
        try:
            status = self.get_rate_limit_status()
            reset_time = status[resource_type]["reset"]
            now = datetime.utcnow()

            if reset_time > now:
                wait_seconds = (reset_time - now).total_seconds() + 1  # Add 1 second buffer
                logger.warning(
                    f"Rate limit exceeded for {resource_type}. "
                    f"Waiting {wait_seconds:.0f} seconds until reset."
                )
                await asyncio.sleep(wait_seconds)
        except Exception as e:
            logger.error(f"Failed to wait for rate limit reset: {e}")
            # Wait a default time if we can't get the reset time
            await asyncio.sleep(60)


def with_rate_limit_retry(max_attempts: int = 3, min_wait: int = 1, max_wait: int = 10):
    """
    Decorator to add exponential backoff retry logic for GitHub API calls

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable):
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type((GithubException, RateLimitExceededException)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except RateLimitExceededException as e:
                logger.error(f"Rate limit exceeded in {func.__name__}: {e}")
                raise
            except GithubException as e:
                if e.status == 403 and "rate limit" in str(e).lower():
                    logger.error(f"Rate limit error in {func.__name__}: {e}")
                    raise RateLimitExceededException(e.status, e.data, e.headers)
                raise

        return wrapper

    return decorator


async def get_rate_limit_service(github_client: Github) -> RateLimitService:
    """
    Dependency to get rate limit service

    Args:
        github_client: GitHub client instance

    Returns:
        RateLimitService instance
    """
    return RateLimitService(github_client)
