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

    # Knowledge base settings (KnowledgeBeast v0.1.0)
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    KNOWLEDGE_COLLECTION_PREFIX: str = "commandcenter"

    # Connection pool settings for KnowledgeBeast PostgresBackend
    KB_POOL_MIN_SIZE: int = 2
    KB_POOL_MAX_SIZE: int = 10
    KB_POOL_TIMEOUT: int = 30

    # GitHub Integration
    github_token: Optional[str] = None
    github_default_org: Optional[str] = None

    # Redis Configuration
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL (e.g., redis://localhost:6379/0)",
    )

    # RAG/Knowledge Base (Legacy)
    knowledge_base_path: str = Field(
        default="./docs/knowledge-base/chromadb",
        description="Path to ChromaDB vector store (legacy RAG)",
    )
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # KnowledgeBeast Integration (v2.3.2+)
    use_knowledgebeast: bool = Field(
        default=False,
        description="Use KnowledgeBeast for RAG (gradual rollout flag)",
    )
    knowledgebeast_db_path: str = Field(
        default="./kb_chroma_db",
        description="Path to KnowledgeBeast ChromaDB storage",
    )
    knowledgebeast_embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="KnowledgeBeast embedding model (all-MiniLM-L6-v2, all-mpnet-base-v2)",
    )

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
    cors_origins: str | list[str] = Field(
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

    # Multi-Provider AI Routing
    openrouter_api_key: Optional[str] = Field(
        default=None,
        description="OpenRouter API key for multi-provider AI access",
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key (direct access)",
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key (direct access)",
    )
    google_api_key: Optional[str] = Field(
        default=None,
        description="Google AI API key (direct access)",
    )
    default_ai_provider: str = Field(
        default="anthropic",
        description="Default AI provider (openrouter, anthropic, openai, google, litellm)",
    )
    default_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Default AI model to use for research agents. Latest models (Oct 2025): "
        "Anthropic: claude-sonnet-4-5-20250929, claude-opus-4-1-20250805 | "
        "OpenAI: gpt-5, gpt-5-mini, gpt-4-1 | "
        "Google: gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite | "
        "See docs/AI_MODELS.md for full reference and update strategy",
    )

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

    def get_postgres_url(self, for_asyncpg: bool = False) -> str:
        """
        Construct PostgreSQL URL from components

        Args:
            for_asyncpg: If True, return asyncpg format (postgresql://),
                        otherwise return SQLAlchemy format (postgresql+asyncpg://)
        """
        if all(
            [
                self.postgres_user,
                self.postgres_password,
                self.postgres_host,
                self.postgres_db,
            ]
        ):
            scheme = "postgresql" if for_asyncpg else "postgresql+asyncpg"
            return (
                f"{scheme}://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        # Strip +asyncpg if for_asyncpg and database_url contains it
        url = self.database_url
        if for_asyncpg and "+asyncpg" in url:
            url = url.replace("postgresql+asyncpg://", "postgresql://")
        return url


# Global settings instance
settings = Settings()
