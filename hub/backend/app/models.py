"""
Database models for Hub
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class Project(Base):
    """CommandCenter project instance"""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    path = Column(String, nullable=False)  # Full path to project folder
    cc_path = Column(String, nullable=False)  # Path to commandcenter subdirectory

    # Configuration
    compose_project_name = Column(String, unique=True, nullable=False)
    backend_port = Column(Integer, unique=True, nullable=False)
    frontend_port = Column(Integer, unique=True, nullable=False)
    postgres_port = Column(Integer, unique=True, nullable=False)
    redis_port = Column(Integer, unique=True, nullable=False)

    # Status
    status = Column(String, default="stopped")  # running, stopped, error, starting, stopping
    health = Column(String, default="unknown")  # healthy, unhealthy, unknown
    is_configured = Column(Boolean, default=False)

    # Stats (cached from CC API)
    repo_count = Column(Integer, default=0)
    tech_count = Column(Integer, default=0)
    task_count = Column(Integer, default=0)

    # Timestamps
    last_started = Column(DateTime(timezone=True), nullable=True)
    last_stopped = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
