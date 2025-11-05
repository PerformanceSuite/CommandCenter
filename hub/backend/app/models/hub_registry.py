"""Hub Registry model for tracking discovered Hubs in federation."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Integer
from app.database import Base


class HubRegistry(Base):
    """Model for tracking discovered CommandCenter Hubs.

    Attributes:
        id: Unique Hub identifier (format: hub-<12-char-hash>)
        name: Human-readable Hub name
        version: Hub software version
        hostname: Machine hostname where Hub is running
        project_path: Absolute path to project directory
        projects: JSON list of project IDs managed by this Hub
        services: JSON list of service names running in this Hub
        project_count: Number of active projects (for quick queries)
        service_count: Number of active services (for quick queries)
        uptime_seconds: Hub uptime in seconds
        first_seen: Timestamp when Hub was first discovered
        last_seen: Timestamp of last presence heartbeat
        extra_data: Extensible JSON field for future metadata
    """

    __tablename__ = "hub_registry"

    # Identity
    id = Column(String, primary_key=True)  # hub-abc123def456
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)

    # Discovery metadata
    hostname = Column(String, nullable=True)
    project_path = Column(String, nullable=True)

    # Hub state
    projects = Column(JSON, default=lambda: [])  # List of project IDs
    services = Column(JSON, default=lambda: [])  # List of service names

    # Metrics (minimal for Phase 5)
    project_count = Column(Integer, default=0)
    service_count = Column(Integer, default=0)
    uptime_seconds = Column(Integer, default=0)

    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Extension point for additional metadata
    extra_data = Column(JSON, default=lambda: {})

    def __repr__(self):
        return (
            f"<HubRegistry(id='{self.id}', name='{self.name}', "
            f"projects={self.project_count}, services={self.service_count})>"
        )
