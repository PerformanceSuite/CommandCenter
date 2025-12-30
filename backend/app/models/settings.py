"""Settings models for LLM provider and agent configuration."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    # Relationship to agent configs
    agent_configs: Mapped[list["AgentConfig"]] = relationship(
        "AgentConfig", back_populates="provider"
    )

    def __repr__(self):
        return f"<Provider {self.alias}: {self.model_id}>"


class AgentConfig(Base):
    """Agent role to provider mapping."""

    __tablename__ = "agent_configs"

    role: Mapped[str] = mapped_column(String(50), primary_key=True)  # analyst, researcher, etc.
    provider_alias: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("providers.alias", onupdate="CASCADE"),
        nullable=False,
    )

    # Relationship to provider
    provider: Mapped["Provider"] = relationship("Provider", back_populates="agent_configs")

    def __repr__(self):
        return f"<AgentConfig {self.role} -> {self.provider_alias}>"
