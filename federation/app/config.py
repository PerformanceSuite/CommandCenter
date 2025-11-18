# federation/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Federation service configuration."""

    DATABASE_URL: str = "postgresql+asyncpg://commandcenter:password@localhost:5432/commandcenter_fed"
    NATS_URL: str = "nats://localhost:4222"
    LOG_LEVEL: str = "info"
    SERVICE_PORT: int = 8001

    class Config:
        env_file = ".env"


settings = Settings()
