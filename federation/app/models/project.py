from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum


class ProjectStatus(str, enum.Enum):
    """Project status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


class Project(Base):
    """Project catalog entry."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    hub_url = Column(String(500), nullable=False)
    mesh_namespace = Column(String(100))
    status = Column(
        SQLEnum(ProjectStatus, name="project_status", create_type=True, values_callable=lambda obj: [e.value for e in obj]),
        default=ProjectStatus.OFFLINE,
        nullable=False,
        index=True
    )
    tags = Column(JSON)
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Project(slug={self.slug}, status={self.status})>"
