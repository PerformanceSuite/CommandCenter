"""
Redis Cache Service
Provides caching functionality with LRU eviction for RAG queries
"""

from typing import Optional
import json
import os

# Lazy imports - only import when CacheService is instantiated
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class CacheService:
    """Service for Redis-based caching with LRU eviction"""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache service

        Args:
            redis_url: Redis connection URL (uses env var if not provided)

        Raises:
            ImportError: If redis is not installed
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis not installed. "
                "Install with: pip install redis"
            )

        # Get Redis URL from parameter or environment
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')

        # Initialize Redis client (connection is lazy)
        self.redis_client: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        """
        Get or create Redis client

        Returns:
            Redis client instance
        """
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10
            )

        return self.redis_client

    async def get(self, key: str) -> Optional[str]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            client = await self._get_client()
            value = await client.get(key)
            return value
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        """
        Set value in cache with TTL

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 300 = 5 minutes)

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            await client.setex(key, ttl, value)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            await client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern

        Args:
            pattern: Redis key pattern (e.g., "rag_query:*")

        Returns:
            Number of keys deleted
        """
        try:
            client = await self._get_client()

            # Scan for matching keys
            deleted = 0
            async for key in client.scan_iter(match=pattern):
                await client.delete(key)
                deleted += 1

            return deleted
        except Exception as e:
            print(f"Cache clear pattern error: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            client = await self._get_client()
            return await client.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False

    async def get_ttl(self, key: str) -> int:
        """
        Get remaining TTL for a key

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        try:
            client = await self._get_client()
            return await client.ttl(key)
        except Exception as e:
            print(f"Cache get TTL error: {e}")
            return -2

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment
        """
        try:
            client = await self._get_client()
            return await client.incrby(key, amount)
        except Exception as e:
            print(f"Cache increment error: {e}")
            return 0

    async def get_stats(self) -> dict:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        try:
            client = await self._get_client()
            info = await client.info()

            return {
                "used_memory": info.get("used_memory_human", "unknown"),
                "total_keys": await client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "evicted_keys": info.get("evicted_keys", 0),
                "connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {}

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

    async def __aenter__(self):
        """Context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()


# Convenience functions for common caching patterns

async def cache_rag_query(
    query: str,
    collection: str,
    results: list,
    ttl: int = 300
) -> bool:
    """
    Cache RAG query results

    Args:
        query: Search query
        collection: Collection name
        results: Query results
        ttl: Time to live in seconds

    Returns:
        True if successful
    """
    cache = CacheService()
    key = f"rag_query:{collection}:{query}"
    value = json.dumps(results)

    return await cache.set(key, value, ttl)


async def get_cached_rag_query(query: str, collection: str) -> Optional[list]:
    """
    Get cached RAG query results

    Args:
        query: Search query
        collection: Collection name

    Returns:
        Cached results or None
    """
    cache = CacheService()
    key = f"rag_query:{collection}:{query}"
    value = await cache.get(key)

    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    return None


async def invalidate_collection_cache(collection: str) -> int:
    """
    Invalidate all cached queries for a collection

    Args:
        collection: Collection name

    Returns:
        Number of keys deleted
    """
    cache = CacheService()
    pattern = f"rag_query:{collection}:*"
    return await cache.clear_pattern(pattern)
