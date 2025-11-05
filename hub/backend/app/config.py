"""Configuration management for Hub backend."""
import hashlib
import os
import socket
from functools import lru_cache
from pathlib import Path


@lru_cache
def get_nats_url() -> str:
    """Get NATS connection URL from environment."""
    return os.getenv("NATS_URL", "nats://localhost:4222")


@lru_cache
def get_database_url() -> str:
    """Get database connection URL from environment.

    Default path uses /app/data/hub.db which is the Docker container path.
    The path uses four slashes: sqlite+aiosqlite:// + //app/data/hub.db
    (protocol with two slashes + absolute path with two slashes)
    """
    return os.getenv("DATABASE_URL", "sqlite+aiosqlite:////app/data/hub.db")


def generate_hub_id() -> str:
    """
    Generate collision-resistant Hub ID from machine + project path.
    Format: hub-<short-hash>

    To prevent collisions when projects move:
    - Include hostname (machine identity)
    - Include absolute project path
    - Include a namespace identifier ('commandcenter')
    - Use SHA256 for cryptographic collision resistance

    Returns:
        str: Hub ID in format "hub-<12-char-hash>" (68 bits of entropy)
    """
    hostname = socket.gethostname()
    project_path = str(Path.cwd().resolve())
    namespace = "commandcenter"

    # Combine all identifiers
    identity_string = f"{namespace}:{hostname}:{project_path}"

    # SHA256 hash (first 12 chars provides ~68 bits of entropy)
    hash_digest = hashlib.sha256(identity_string.encode()).hexdigest()[:12]

    return f"hub-{hash_digest}"


@lru_cache
def get_hub_id() -> str:
    """Get unique Hub identifier.

    First tries environment variable, then generates from machine + project path.
    The generated ID is stable across restarts but changes if machine or path changes.
    """
    return os.getenv("HUB_ID", generate_hub_id())


@lru_cache
def get_hub_name() -> str:
    """Get Hub name from environment."""
    return os.getenv("HUB_NAME", "CommandCenter Hub")


@lru_cache
def get_hub_version() -> str:
    """Get Hub version from environment."""
    return os.getenv("HUB_VERSION", "1.0.0")
