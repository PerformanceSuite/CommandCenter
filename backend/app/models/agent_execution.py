"""AgentExecution model for tracking agent execution runs."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgentExecution(Base):
    """
    Agent execution tracking for the graph system.

    Tracks individual agent runs with their status, results, and metadata.
    Integrates with the graph service to make agent executions queryable
    as graph entities alongside personas and workflows.
    """

    __tablename__ = "agent_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), unique=True, nullable=False, index=True, default=lambda: str(uuid4())
    )
    persona_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Execution status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        default="pending"
    )  # pending, running, completed, failed, cancelled
    
    # Results
    files_changed: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    pr_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    
    # Metrics
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Additional metadata
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    
    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<AgentExecution {self.execution_id}: {self.persona_name} ({self.status})>"
