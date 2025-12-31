"""AgentPersona model for storing custom agent configurations."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgentPersona(Base):
    """
    Agent persona configuration stored in database.

    Personas define the characteristics and behavior of agents:
    - Identity (name, display name, description)
    - System prompt for LLM guidance
    - Model configuration (model, temperature)
    - Execution requirements (sandbox)
    - Metadata (category, tags)
    """

    __tablename__ = "agent_personas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="custom", nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(100), default="claude-sonnet-4-20250514", nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    requires_sandbox: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tags: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<AgentPersona {self.name}: {self.display_name}>"
