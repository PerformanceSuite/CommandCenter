"""Service model for health tracking and service discovery."""
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean,
    ForeignKey, JSON, Enum as SQLEnum, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class HealthStatus(str, enum.Enum):
    """Service health status."""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class HealthMethod(str, enum.Enum):
    """Health check method."""
    HTTP = "http"
    TCP = "tcp"
    EXEC = "exec"
    REDIS = "redis"
    POSTGRES = "postgres"


class ServiceType(str, enum.Enum):
    """Service type classification."""
    DATABASE = "database"
    CACHE = "cache"
    API = "api"
    WEB = "web"
    QUEUE = "queue"
    WORKER = "worker"


class Service(Base):
    """Service registration and health tracking."""

    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)  # postgres, redis, backend, frontend, nats
    service_type = Column(SQLEnum(ServiceType), nullable=False)

    # Health Configuration
    health_url = Column(String)  # HTTP health endpoint or connection string
    health_method = Column(SQLEnum(HealthMethod), default=HealthMethod.HTTP)
    health_interval = Column(Integer, default=30)  # seconds between checks
    health_timeout = Column(Integer, default=5)  # timeout for each check
    health_retries = Column(Integer, default=3)  # retries before marking down
    health_threshold = Column(Float, default=1000.0)  # ms threshold for degraded

    # Health Status
    health_status = Column(SQLEnum(HealthStatus), default=HealthStatus.UNKNOWN)
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    consecutive_failures = Column(Integer, default=0)
    consecutive_successes = Column(Integer, default=0)
    health_details = Column(JSON, default=dict)  # latency, errors, version, etc.

    # Service Info
    version = Column(String)
    port = Column(Integer)
    container_id = Column(String)
    internal_url = Column(String)  # Internal Docker/network URL
    external_url = Column(String)  # External accessible URL

    # Metrics
    total_checks = Column(Integer, default=0)
    failed_checks = Column(Integer, default=0)
    average_latency = Column(Float)  # milliseconds
    uptime_seconds = Column(Integer, default=0)
    last_error = Column(String)

    # Flags
    is_required = Column(Boolean, default=True)  # Required for project to be healthy
    auto_restart = Column(Boolean, default=False)  # Auto-restart on failure
    alerts_enabled = Column(Boolean, default=True)  # Send alerts on status change

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="services")
    health_checks = relationship("HealthCheck", back_populates="service", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Service {self.name} ({self.health_status})>"

    @property
    def is_healthy(self) -> bool:
        """Check if service is healthy (up or degraded)."""
        return self.health_status in [HealthStatus.UP, HealthStatus.DEGRADED]

    @property
    def uptime_percentage(self) -> float:
        """Calculate uptime percentage."""
        if self.total_checks == 0:
            return 0.0
        return ((self.total_checks - self.failed_checks) / self.total_checks) * 100


class HealthCheck(Base):
    """Health check history for services."""

    __tablename__ = "health_checks"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)

    # Check details
    status = Column(SQLEnum(HealthStatus), nullable=False)
    latency_ms = Column(Float)  # Response time in milliseconds
    error_message = Column(String)
    details = Column(JSON, default=dict)  # Additional check details

    # Timestamp
    checked_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    service = relationship("Service", back_populates="health_checks")

    def __repr__(self):
        return f"<HealthCheck {self.service_id} {self.status} at {self.checked_at}>"
