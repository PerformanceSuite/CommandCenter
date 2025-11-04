"""Configuration management for Hub backend."""
import os
from functools import lru_cache


@lru_cache
def get_nats_url() -> str:
    """Get NATS connection URL from environment."""
    return os.getenv("NATS_URL", "nats://localhost:4222")


@lru_cache
def get_database_url() -> str:
    """Get database connection URL from environment."""
    return os.getenv("DATABASE_URL", "sqlite+aiosqlite:////app/data/hub.db")


@lru_cache
def get_hub_id() -> str:
    """Get unique Hub identifier from environment."""
    return os.getenv("HUB_ID", "local-hub")
