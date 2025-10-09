"""
Application configuration using Pydantic Settings
Loads configuration from environment variables and .env file
"""

import json
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "Command Center API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./commandcenter.db",
        description="Database connection URL",
    )

    # PostgreSQL settings (for production)
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_host: Optional[str] = None
    postgres_port: int = 5432
    postgres_db: Optional[str] = None

    # GitHub Integration
    github_token: Optional[str] = None
    github_default_org: Optional[str] = None

    # Redis Configuration
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL (e.g., redis://localhost:6379/0)",
    )

    # RAG/Knowledge Base
    knowledge_base_path: str = Field(
        default="./docs/knowledge-base/chromadb",
        description="Path to ChromaDB vector store",
    )
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Security
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT tokens and encryption",
    )
    ENCRYPTION_SALT: str = Field(
        default="dev-encryption-salt-change-in-production",
        description="Salt for PBKDF2 key derivation (must be consistent for decryption)",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPT_TOKENS: bool = Field(
        default=True, description="Whether to encrypt GitHub tokens in database"
    )

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins (comma-separated in env: CORS_ORIGINS)",
    )
    cors_allow_credentials: bool = Field(
        default=True, description="Allow credentials in CORS requests"
    )
    cors_max_age: int = Field(
        default=600, description="Maximum age (seconds) for CORS preflight cache"
    )

    # API Settings
    api_v1_prefix: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from JSON string if provided as string"""
        if isinstance(v, str):
            try:
                # Try to parse as JSON array
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                # If it's a single string, wrap in list
                return [parsed]
            except json.JSONDecodeError:
                # Fallback: treat as comma-separated list
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    def get_postgres_url(self) -> str:
        """Construct PostgreSQL URL from components"""
        if all(
            [
                self.postgres_user,
                self.postgres_password,
                self.postgres_host,
                self.postgres_db,
            ]
        ):
            return (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return self.database_url

    def get_async_database_url(self) -> str:
        """
        Get database URL with async driver
        Converts postgresql:// to postgresql+asyncpg:// for async SQLAlchemy
        """
        url = self.get_postgres_url()

        # If using PostgreSQL without explicit driver, add asyncpg
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        return url


# Global settings instance
settings = Settings()
