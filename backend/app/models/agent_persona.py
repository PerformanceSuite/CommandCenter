"""
Agent Persona model for storing agent/persona configurations
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgentPersona(Base):
    """Agent Persona configuration storage"""

    __tablename__ = "agent_personas"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Persona identification
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Categorization
    category: Mapped[str] = mapped_column(String(100), default="custom", nullable=False)

    # Core configuration
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(
        String(255), default="claude-sonnet-4-20250514", nullable=False
    )
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)

    # Execution hints
    requires_sandbox: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Additional metadata
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<AgentPersona(id={self.id}, name='{self.name}', category='{self.category}')>"
