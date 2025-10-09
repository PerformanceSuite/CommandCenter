"""
Redis caching service for API responses
"""

import json
import logging
from typing import Optional, Any
import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Service for Redis caching operations"""

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

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/error
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: 300 = 5 minutes)

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            serialized = json.dumps(value)
            if ttl:
                await self.redis_client.setex(key, ttl, serialized)
            else:
                # Default TTL of 5 minutes
                await self.redis_client.setex(key, 300, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern

        Args:
            pattern: Redis key pattern (e.g., "github:repo:*")

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0

        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis DELETE_PATTERN error for pattern {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False

    def make_cache_key(self, *parts: str) -> str:
        """
        Create a cache key from parts

        Args:
            *parts: Key parts

        Returns:
            Cache key string
        """
        return ":".join(str(p) for p in parts)


# Global Redis service instance
redis_service = RedisService()


async def get_redis() -> RedisService:
    """Dependency to get Redis service"""
    return redis_service
