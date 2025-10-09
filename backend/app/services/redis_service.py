"""
Redis caching service for API responses
"""

import json
import logging
from typing import Optional, Any
from datetime import timedelta
import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Service for Redis caching operations with project-level namespacing"""

    def __init__(self):
        """Initialize Redis service"""
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = False

    async def connect(self):
        """Connect to Redis"""
        try:
            # Check if Redis URL is configured
            redis_url = getattr(settings, "redis_url", None)
            if not redis_url:
                logger.warning("Redis URL not configured, caching disabled")
                return

            self.redis_client = redis.from_url(
                redis_url, encoding="utf-8", decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            self.enabled = True
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            self.enabled = False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    def _make_key(self, project_id: int, key_type: str, identifier: str) -> str:
        """
        Generate project-namespaced key.

        Pattern: project:{project_id}:{key_type}:{identifier}

        Examples:
            project:123:repo:owner/name
            project:123:rate_limit:github_api
            project:456:pr:18

        Args:
            project_id: Project/repository ID
            key_type: Type of cached data (repo, pr, issue, rate_limit, etc.)
            identifier: Unique identifier for the cached item

        Returns:
            Namespaced cache key
        """
        return f"project:{project_id}:{key_type}:{identifier}"

    async def get(
        self, project_id: int, key_type: str, identifier: str
    ) -> Optional[Any]:
        """
        Get value from project-namespaced cache

        Args:
            project_id: Project/repository ID
            key_type: Type of cached data
            identifier: Unique identifier for the cached item

        Returns:
            Cached value or None if not found/error
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            key = self._make_key(project_id, key_type, identifier)
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(
                f"Redis GET error for project {project_id}, key_type {key_type}, identifier {identifier}: {e}"
            )
            return None

    async def set(
        self,
        project_id: int,
        key_type: str,
        identifier: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in project-namespaced cache with TTL

        Args:
            project_id: Project/repository ID
            key_type: Type of cached data
            identifier: Unique identifier for the cached item
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: 3600 = 1 hour)

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            key = self._make_key(project_id, key_type, identifier)
            serialized = json.dumps(value)
            ttl_seconds = ttl if ttl is not None else 3600
            await self.redis_client.setex(key, ttl_seconds, serialized)
            logger.debug(
                f"Cached data for project {project_id}, key_type {key_type}, identifier {identifier} with TTL {ttl_seconds}s"
            )
            return True
        except Exception as e:
            logger.error(
                f"Redis SET error for project {project_id}, key_type {key_type}, identifier {identifier}: {e}"
            )
            return False

    async def delete(self, project_id: int, key_type: str, identifier: str) -> bool:
        """
        Delete specific key from project's cache

        Args:
            project_id: Project/repository ID
            key_type: Type of cached data
            identifier: Unique identifier for the cached item

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            key = self._make_key(project_id, key_type, identifier)
            await self.redis_client.delete(key)
            logger.debug(
                f"Deleted cache for project {project_id}, key_type {key_type}, identifier {identifier}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Redis DELETE error for project {project_id}, key_type {key_type}, identifier {identifier}: {e}"
            )
            return False

    async def delete_pattern(self, project_id: int, pattern: str) -> int:
        """
        Delete all keys matching project-namespaced pattern.

        Example:
            delete_pattern(123, "repo:*")
            -> Deletes all project:123:repo:* keys

        Args:
            project_id: Project/repository ID
            pattern: Pattern to match within project namespace (e.g., "repo:*")

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0

        try:
            full_pattern = f"project:{project_id}:{pattern}"
            keys = []
            async for key in self.redis_client.scan_iter(match=full_pattern):
                keys.append(key)

            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(
                    f"Deleted {deleted} cache entries for project {project_id} matching pattern {pattern}"
                )
                return deleted
            return 0
        except Exception as e:
            logger.error(
                f"Redis DELETE_PATTERN error for project {project_id}, pattern {pattern}: {e}"
            )
            return 0

    async def exists(self, project_id: int, key_type: str, identifier: str) -> bool:
        """
        Check if key exists in project's cache

        Args:
            project_id: Project/repository ID
            key_type: Type of cached data
            identifier: Unique identifier for the cached item

        Returns:
            True if key exists
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            key = self._make_key(project_id, key_type, identifier)
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(
                f"Redis EXISTS error for project {project_id}, key_type {key_type}, identifier {identifier}: {e}"
            )
            return False

    def make_cache_key(self, *parts: str) -> str:
        """
        Create a cache key from parts (DEPRECATED - use _make_key with project_id)

        This method is kept for backward compatibility but should not be used for new code.

        Args:
            *parts: Key parts

        Returns:
            Cache key string
        """
        logger.warning(
            "make_cache_key is deprecated, use _make_key with project_id instead"
        )
        return ":".join(str(p) for p in parts)


# Global Redis service instance
redis_service = RedisService()


async def get_redis() -> RedisService:
    """Dependency to get Redis service"""
    return redis_service
