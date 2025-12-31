"""Agent Persona model for storing agent configurations."""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgentPersona(Base):
    """
    Agent Persona configuration for the unified agent framework.

    Stores agent definitions that can be loaded at runtime to configure
    agent behavior, model selection, and execution environment.
    """

    __tablename__ = "agent_personas"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Persona identification
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="custom", nullable=False)

    # Agent behavior
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # Model configuration
    model: Mapped[str] = mapped_column(String(200), default="claude-sonnet-4-20250514", nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)

    # Execution configuration
    requires_sandbox: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tags: Mapped[Optional[dict]] = mapped_column(
        JSON, default=list, nullable=True
    )  # Changed from list to dict for JSON compatibility

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<AgentPersona(id={self.id}, name='{self.name}', category='{self.category}')>"
