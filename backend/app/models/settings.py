"""Settings models for LLM provider and agent configuration."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Provider(Base):
    """LLM provider configuration."""

    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    alias: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(String(200), nullable=False)  # LiteLLM format
    api_base: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Custom endpoint
    api_key_env: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Env var name
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Encrypted stored key
    cost_input: Mapped[float] = mapped_column(Float, default=0.0)  # Per 1M input tokens
    cost_output: Mapped[float] = mapped_column(Float, default=0.0)  # Per 1M output tokens
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Provider {self.alias}: {self.model_id}>"


class AgentConfig(Base):
    """Agent role to provider/model mapping."""

    __tablename__ = "agent_configs"

    role: Mapped[str] = mapped_column(String(50), primary_key=True)  # analyst, researcher, etc.
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # anthropic, openai, google, zai
    model_id: Mapped[str] = mapped_column(String(200), nullable=False)  # LiteLLM format model ID

    def __repr__(self):
        return f"<AgentConfig {self.role} -> {self.provider}/{self.model_id}>"
