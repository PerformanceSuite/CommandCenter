# federation/app/config.py
from pydantic_settings import BaseSettings
from pathlib import Path
import logging


class Settings(BaseSettings):
    """Federation service configuration."""

    DATABASE_URL: str = "postgresql+asyncpg://commandcenter:password@127.0.0.1:5432/commandcenter_fed"
    NATS_URL: str = "nats://127.0.0.1:4222"
    LOG_LEVEL: str = "info"
    SERVICE_PORT: int = 8001

    # Heartbeat monitoring configuration
    HEARTBEAT_STALE_THRESHOLD_SECONDS: int = 90
    HEARTBEAT_STALE_CHECK_INTERVAL_SECONDS: int = 60

    class Config:
        # Look for .env in the federation directory (parent of app/)
        env_file = str(Path(__file__).parent.parent / ".env")


settings = Settings()
