from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add app directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# We need to avoid importing app.database because it creates async engine
# Instead, we'll get Base from the declarative_base used in database.py
# and import models which will register themselves with Base.metadata
from sqlalchemy.orm import declarative_base

# Create a temporary Base for migration purposes
# This must match the Base in app.database
Base = declarative_base()

# Now we need to recreate the model definition here for migrations
# Since we can't import from app.models due to async engine creation
#
# TECHNICAL DEBT: Model definitions duplicated from app/models.py
# This duplication exists because:
# 1. app.database creates an async engine which conflicts with Alembic's sync engine
# 2. Alembic needs access to model metadata for autogenerate to work
# 3. Importing app.models triggers app.database import, causing async/sync conflict
#
# The duplicated models are:
# - GUID (custom TypeDecorator for UUID handling)
# - Project (from app/models/project.py)
# - Event (from app/models/event.py)
#
# IMPORTANT: When modifying models in app/models/, these definitions must be
# updated manually to match. Future improvements could use a shared base or
# refactor database.py to avoid async engine creation on import.
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Index, TypeDecorator, CHAR
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid import UUID, uuid4
from typing import Any, Optional


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as
    stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value) if isinstance(value, UUID) else value
        else:
            if isinstance(value, UUID):
                return str(value)
            else:
                return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if isinstance(value, UUID):
                return value
            else:
                return UUID(value) if value else None


class Project(Base):
    """CommandCenter project instance"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    path = Column(String, nullable=False)

    # Configuration (Dagger handles orchestration, no compose_project_name needed)
    backend_port = Column(Integer, unique=True, nullable=False)
    frontend_port = Column(Integer, unique=True, nullable=False)
    postgres_port = Column(Integer, unique=True, nullable=False)
    redis_port = Column(Integer, unique=True, nullable=False)

    # Status
    status = Column(String, default="stopped")
    health = Column(String, default="unknown")
    is_configured = Column(Boolean, default=False)

    # Stats
    repo_count = Column(Integer, default=0)
    tech_count = Column(Integer, default=0)
    task_count = Column(Integer, default=0)

    # Timestamps
    last_started = Column(DateTime(timezone=True), nullable=True)
    last_stopped = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Event(Base):
    """Event model for NATS-based event sourcing.

    Events are the source of truth for all state changes in the Hub.
    They are published to NATS subjects and persisted to database.

    Attributes:
        id: Unique event identifier (UUID)
        subject: NATS subject (e.g., 'hub.local-hub.project.created')
        origin: Source metadata (hub_id, service, user)
        correlation_id: Request correlation UUID for tracing
        payload: Event data as JSON
        timestamp: Event creation time (UTC)
    """

    __tablename__ = "events"

    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid4)

    # Event metadata
    subject = Column(String, nullable=False, index=True)
    origin = Column(JSON, nullable=False)
    correlation_id = Column(GUID(), nullable=False, index=True)

    # Event content
    payload = Column(JSON, nullable=False)

    # Temporal
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        index=True
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_events_subject_timestamp", "subject", "timestamp"),
        Index("ix_events_correlation_timestamp", "correlation_id", "timestamp"),
    )

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get database URL from environment or use default
database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:////app/data/hub.db")
# Convert async URL to sync for Alembic
database_url = database_url.replace("+aiosqlite", "")
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
