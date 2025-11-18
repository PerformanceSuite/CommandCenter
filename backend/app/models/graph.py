"""
Graph models for Phase 7 - Code knowledge graph entities

These models represent the canonical knowledge graph for code entities,
services, dependencies, specifications, and audit results.

Architecture:
- Project (root container)
- Repo → File → Symbol (code hierarchy)
- Dependency (Symbol→Symbol relationships)
- Service (running services)
- SpecItem (planned features from TODO/FIXME)
- Task (work items)
- Link (generic typed edges)
- HealthSample (service health data)
- Audit (code review/security/compliance results)
- Event (NATS event mirror for queryability)
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SymbolKind(str, Enum):
    """Code symbol types"""

    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    TYPE = "type"
    VARIABLE = "var"
    TEST = "test"
    INTERFACE = "interface"
    ENUM = "enum"
    CONSTANT = "constant"


class DependencyType(str, Enum):
    """Dependency relationship types"""

    IMPORT = "import"
    CALL = "call"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    USES = "uses"
    REFERENCES = "references"


class ServiceType(str, Enum):
    """Service types"""

    API = "api"
    JOB = "job"
    DB = "db"
    QUEUE = "queue"
    MCP = "mcp"
    MESH = "mesh"
    FRONTEND = "frontend"
    BACKEND = "backend"


class SpecItemStatus(str, Enum):
    """Specification item status"""

    PLANNED = "planned"
    IN_PROGRESS = "inProgress"
    DONE = "done"
    BLOCKED = "blocked"


class SpecItemSource(str, Enum):
    """Specification item source"""

    FILE = "file"  # TODO/FIXME comment
    DOC = "doc"  # Documentation
    CANVAS = "canvas"  # Design canvas
    ISSUE = "issue"  # GitHub issue


class TaskKind(str, Enum):
    """Task types"""

    FEATURE = "feature"
    BUG = "bug"
    CHORE = "chore"
    REVIEW = "review"
    SECURITY = "security"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"


class HealthStatus(str, Enum):
    """Service health status"""

    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class AuditKind(str, Enum):
    """Audit types"""

    CODE_REVIEW = "codeReview"
    SECURITY = "security"
    LICENSE = "license"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    TEST_COVERAGE = "testCoverage"
    # Phase 7 audit types
    COMPLETENESS = "completeness"  # TODO/spec coverage, docstrings
    CONSISTENCY = "consistency"  # Naming conventions, code style
    DRIFT = "drift"  # Code vs spec divergence


class AuditStatus(str, Enum):
    """Audit result status"""

    PENDING = "pending"
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"
    ERROR = "error"


class LinkType(str, Enum):
    """Generic link types for flexible relationships"""

    REFERENCES = "references"
    DEPENDS_ON = "dependsOn"
    IMPLEMENTS = "implements"
    TESTS = "tests"
    DOCUMENTS = "documents"
    PRODUCES = "produces"
    CONSUMES = "consumes"
    CONTAINS = "contains"


# ============================================================================
# Core Graph Entities
# ============================================================================


class GraphRepo(Base):
    """
    Git repository in the knowledge graph.

    Note: Different from app.models.Repository (which tracks GitHub sync state).
    GraphRepo is focused on code structure and dependencies.
    """

    __tablename__ = "graph_repos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to project for multi-tenant isolation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Repository identification
    provider: Mapped[str] = mapped_column(String(50), default="github")  # github, gitlab, bitbucket
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)

    # Repository metadata
    default_branch: Mapped[str] = mapped_column(String(255), default="main")
    root_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Local path if available

    # Indexing state
    last_indexed_commit: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    last_indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    # project: Mapped["Project"] = relationship("Project")  # noqa: F821 - Project model TBD
    files: Mapped[list["GraphFile"]] = relationship(
        "GraphFile", back_populates="repo", cascade="all, delete-orphan"
    )
    services: Mapped[list["GraphService"]] = relationship(
        "GraphService", back_populates="repo", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GraphRepo(id={self.id}, full_name='{self.full_name}')>"


class GraphFile(Base):
    """Source file in the knowledge graph"""

    __tablename__ = "graph_files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign keys
    repo_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("graph_repos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # File identification
    path: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    lang: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # python, typescript, javascript, go, rust

    # Content metadata
    hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA-256 of content
    size: Mapped[int] = mapped_column(Integer, default=0)  # File size in bytes
    lines: Mapped[int] = mapped_column(Integer, default=0)  # Line count

    # Indexing state
    last_indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    repo: Mapped["GraphRepo"] = relationship("GraphRepo", back_populates="files")
    symbols: Mapped[list["GraphSymbol"]] = relationship(
        "GraphSymbol", back_populates="file", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GraphFile(id={self.id}, path='{self.path}', lang='{self.lang}')>"


class GraphSymbol(Base):
    """Code symbol (module, class, function, etc.) in the knowledge graph"""

    __tablename__ = "graph_symbols"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign keys
    file_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("graph_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Symbol identification
    kind: Mapped[SymbolKind] = mapped_column(SQLEnum(SymbolKind), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    qualified_name: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Fully qualified name
    signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Function signature

    # Location in file
    range_start: Mapped[int] = mapped_column(Integer, nullable=False)  # Start line
    range_end: Mapped[int] = mapped_column(Integer, nullable=False)  # End line

    # Symbol properties
    exports: Mapped[bool] = mapped_column(Boolean, default=False)  # Is exported/public
    is_async: Mapped[bool] = mapped_column(Boolean, default=False)  # Async function
    is_generator: Mapped[bool] = mapped_column(Boolean, default=False)  # Generator function

    # Additional metadata (JSON for flexibility)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    file: Mapped["GraphFile"] = relationship("GraphFile", back_populates="symbols")
    dependencies_from: Mapped[list["GraphDependency"]] = relationship(
        "GraphDependency",
        foreign_keys="GraphDependency.from_symbol_id",
        back_populates="from_symbol",
        cascade="all, delete-orphan",
    )
    dependencies_to: Mapped[list["GraphDependency"]] = relationship(
        "GraphDependency",
        foreign_keys="GraphDependency.to_symbol_id",
        back_populates="to_symbol",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<GraphSymbol(id={self.id}, kind={self.kind}, name='{self.name}')>"


class GraphDependency(Base):
    """Dependency relationship between symbols"""

    __tablename__ = "graph_dependencies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign keys
    from_symbol_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("graph_symbols.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_symbol_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("graph_symbols.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Dependency metadata
    type: Mapped[DependencyType] = mapped_column(
        SQLEnum(DependencyType), nullable=False, index=True
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0)  # Dependency strength/importance

    # Additional metadata
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    from_symbol: Mapped["GraphSymbol"] = relationship(
        "GraphSymbol",
        foreign_keys=[from_symbol_id],
        back_populates="dependencies_from",
    )
    to_symbol: Mapped["GraphSymbol"] = relationship(
        "GraphSymbol",
        foreign_keys=[to_symbol_id],
        back_populates="dependencies_to",
    )

    def __repr__(self) -> str:
        return f"<GraphDependency(id={self.id}, type={self.type}, from={self.from_symbol_id}, to={self.to_symbol_id})>"


# ============================================================================
# Service & Infrastructure
# ============================================================================


class GraphService(Base):
    """Running service in the system"""

    __tablename__ = "graph_services"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign keys
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    repo_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("graph_repos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Service identification
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[ServiceType] = mapped_column(SQLEnum(ServiceType), nullable=False, index=True)

    # Service metadata
    endpoint: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    health_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Status
    status: Mapped[HealthStatus] = mapped_column(
        SQLEnum(HealthStatus),
        default=HealthStatus.UNKNOWN,
        nullable=False,
    )

    # Additional metadata
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    # project: Mapped["Project"] = relationship("Project")  # noqa: F821 - Project model TBD
    repo: Mapped[Optional["GraphRepo"]] = relationship("GraphRepo", back_populates="services")
    health_samples: Mapped[list["GraphHealthSample"]] = relationship(
        "GraphHealthSample", back_populates="service", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GraphService(id={self.id}, name='{self.name}', type={self.type})>"


class GraphHealthSample(Base):
    """Health check sample for a service"""

    __tablename__ = "graph_health_samples"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign keys
    service_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("graph_services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Health check result
    status: Mapped[HealthStatus] = mapped_column(SQLEnum(HealthStatus), nullable=False, index=True)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Details (JSON for flexibility)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamp
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    service: Mapped["GraphService"] = relationship("GraphService", back_populates="health_samples")

    def __repr__(self) -> str:
        return (
            f"<GraphHealthSample(id={self.id}, service_id={self.service_id}, status={self.status})>"
        )


# ============================================================================
# Specifications & Tasks
# ============================================================================


class GraphSpecItem(Base):
    """Specification item (planned feature, requirement, etc.)"""

    __tablename__ = "graph_spec_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign keys
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Spec item metadata
    source: Mapped[SpecItemSource] = mapped_column(
        SQLEnum(SpecItemSource), nullable=False, index=True
    )
    ref: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )  # File path, doc URL, issue number
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Priority and status
    priority: Mapped[int] = mapped_column(Integer, default=0)  # Higher = more important
    status: Mapped[SpecItemStatus] = mapped_column(
        SQLEnum(SpecItemStatus),
        default=SpecItemStatus.PLANNED,
        nullable=False,
        index=True,
    )

    # Additional metadata
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    # project: Mapped["Project"] = relationship("Project")  # noqa: F821 - Project model TBD
    tasks: Mapped[list["GraphTask"]] = relationship(
        "GraphTask", back_populates="spec_item", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GraphSpecItem(id={self.id}, title='{self.title}', status={self.status})>"


class GraphTask(Base):
    """Work item / task"""

    __tablename__ = "graph_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign keys
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    spec_item_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("graph_spec_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Task metadata
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kind: Mapped[TaskKind] = mapped_column(SQLEnum(TaskKind), nullable=False, index=True)

    # Status and assignment
    status: Mapped[SpecItemStatus] = mapped_column(
        SQLEnum(SpecItemStatus),
        default=SpecItemStatus.PLANNED,
        nullable=False,
        index=True,
    )
    assignee: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Labels (array stored as JSON)
    labels: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)

    # Additional metadata
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    # project: Mapped["Project"] = relationship("Project")  # noqa: F821 - Project model TBD
    spec_item: Mapped[Optional["GraphSpecItem"]] = relationship(
        "GraphSpecItem", back_populates="tasks"
    )

    def __repr__(self) -> str:
        return f"<GraphTask(id={self.id}, title='{self.title}', kind={self.kind})>"


# ============================================================================
# Generic Links
# ============================================================================


class GraphLink(Base):
    """
    Generic typed edge between any two entities in the graph.

    Examples:
    - File → SpecItem (file implements spec)
    - Service → Repo (service deployed from repo)
    - Task → Symbol (task modifies symbol)
    - Audit → File (audit targets file)
    """

    __tablename__ = "graph_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # From entity (polymorphic)
    from_entity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # table name
    from_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # To entity (polymorphic)
    to_entity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # table name
    to_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Link metadata
    type: Mapped[LinkType] = mapped_column(SQLEnum(LinkType), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    # Additional metadata
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<GraphLink(id={self.id}, type={self.type}, {self.from_entity}:{self.from_id} → {self.to_entity}:{self.to_id})>"


# ============================================================================
# Audits & Compliance
# ============================================================================


class GraphAudit(Base):
    """Audit result (code review, security scan, compliance check, etc.)"""

    __tablename__ = "graph_audits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Target entity (polymorphic - can audit any entity)
    target_entity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # table name
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Audit metadata
    kind: Mapped[AuditKind] = mapped_column(SQLEnum(AuditKind), nullable=False, index=True)
    status: Mapped[AuditStatus] = mapped_column(SQLEnum(AuditStatus), nullable=False, index=True)

    # Results
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_path: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True
    )  # Path to detailed report

    # Score/metrics (optional)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0.0-100.0

    # Additional metadata
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<GraphAudit(id={self.id}, kind={self.kind}, status={self.status}, target={self.target_entity}:{self.target_id})>"


# ============================================================================
# Event Mirror
# ============================================================================


class GraphEvent(Base):
    """
    Mirror of select NATS events for queryability.

    Not all NATS events are stored - only those relevant for graph analytics
    and historical queries (e.g., graph.ingest.completed, audit.result.*).
    """

    __tablename__ = "graph_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Event identification
    subject: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Event payload (JSON)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<GraphEvent(id={self.id}, subject='{self.subject}')>"
