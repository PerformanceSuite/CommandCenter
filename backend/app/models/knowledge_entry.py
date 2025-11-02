"""
KnowledgeEntry model for RAG knowledge base entries
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class KnowledgeEntry(Base):
    """Knowledge base entries for RAG system"""

    __tablename__ = "knowledge_entries"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to project for isolation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Foreign key to technology
    technology_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("technologies.id", ondelete="CASCADE"), nullable=True
    )

    # Content
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)

    # Source tracking
    source_file: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    source_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # pdf, html, manual, etc.

    # Vector database reference
    vector_db_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Metadata
    page_number: Mapped[Optional[int]] = mapped_column(nullable=True)
    chunk_index: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Quality metrics
    confidence_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    relevance_score: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="knowledge_entries")
    technology: Mapped[Optional["Technology"]] = relationship(
        "Technology", back_populates="knowledge_entries"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeEntry(id={self.id}, title='{self.title}', category='{self.category}')>"
