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
    # Document Intelligence link types
    INTEGRATES_WITH = "integratesWith"
    PROVIDES_TO = "providesTo"
    REPLACES = "replaces"
    SIMILAR_TO = "similarTo"
    SUPERSEDES = "supersedes"
    EXTRACTS_FROM = "extractsFrom"


class DocumentType(str, Enum):
    """Document classification types"""

    PLAN = "plan"
    CONCEPT = "concept"
    GUIDE = "guide"
    REFERENCE = "reference"
    REPORT = "report"
    SESSION = "session"
    ARCHIVE = "archive"


class DocumentStatus(str, Enum):
    """Document lifecycle status"""

    ACTIVE = "active"
    COMPLETED = "completed"
    SUPERSEDED = "superseded"
    ABANDONED = "abandoned"
    STALE = "stale"


class ConceptType(str, Enum):
    """Concept classification types"""

    PRODUCT = "product"
    FEATURE = "feature"
    MODULE = "module"
    PROCESS = "process"
    TECHNOLOGY = "technology"
    FRAMEWORK = "framework"
    METHODOLOGY = "methodology"
    OTHER = "other"


class ConceptStatus(str, Enum):
    """Concept lifecycle status"""

    PROPOSED = "proposed"
    ACTIVE = "active"
    IMPLEMENTED = "implemented"
    DEPRECATED = "deprecated"
    UNKNOWN = "unknown"


class RequirementType(str, Enum):
    """Requirement classification types"""

    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "nonFunctional"
    CONSTRAINT = "constraint"
    DEPENDENCY = "dependency"
    OUTCOME = "outcome"


class RequirementPriority(str, Enum):
    """Requirement priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class RequirementStatus(str, Enum):
    """Requirement status"""

    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    """AI extraction confidence level"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


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

    Cross-Project Federation:
    - source_project_id and target_project_id enable cross-project queries
    - When both are set and different, this is a cross-project link
    - Nullable for backward compatibility with existing intra-project links
    """

    __tablename__ = "graph_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Project context for federation queries (nullable for backward compatibility)
    source_project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    target_project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

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

    @property
    def is_cross_project(self) -> bool:
        """Returns True if this link spans across different projects."""
        return (
            self.source_project_id is not None
            and self.target_project_id is not None
            and self.source_project_id != self.target_project_id
        )

    def __repr__(self) -> str:
        cross = " [cross-project]" if self.is_cross_project else ""
        return f"<GraphLink(id={self.id}, type={self.type}, {self.from_entity}:{self.from_id} → {self.to_entity}:{self.to_id}{cross})>"


# ============================================================================
# Cross-Project Federation
# ============================================================================


class CrossProjectLink(Base):
    """
    Explicit cross-project relationship for federation queries.

    This table enables ecosystem-wide queries across multiple projects:
    - "Find all services with degraded health across the ecosystem"
    - "Show dependencies between project A and project B"
    - "List all shared libraries used across projects"

    Architecture Decision:
    - Dedicated table separate from GraphLink for cleaner separation
    - Different indexes optimized for ecosystem-wide queries
    - Explicit source/target project_id fields (not nullable)

    Entity Types:
    - "graph_repos", "graph_files", "graph_symbols", "graph_services",
      "graph_spec_items", "graph_tasks", etc.

    Relationship Types:
    - "depends_on", "imports", "calls", "extends", "implements",
      "shares_library", "consumes_api", "produces_event", etc.
    """

    __tablename__ = "cross_project_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Source project and entity
    source_project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_entity_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Target project and entity
    target_project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_entity_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationship metadata
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Timestamps
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<CrossProjectLink(id={self.id}, "
            f"{self.source_entity_type}:{self.source_entity_id}@{self.source_project_id} "
            f"--[{self.relationship_type}]--> "
            f"{self.target_entity_type}:{self.target_entity_id}@{self.target_project_id})>"
        )


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


# ============================================================================
# Document Intelligence Entities
# ============================================================================


class GraphDocument(Base):
    """
    Document in the knowledge graph with classification metadata.

    Stores document metadata and classification results from the
    doc-classifier persona. Enables document lifecycle management
    and querying across the documentation corpus.
    """

    __tablename__ = "graph_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to project for multi-tenant isolation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Document identification
    path: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Classification (from doc-classifier)
    doc_type: Mapped[DocumentType] = mapped_column(
        SQLEnum(DocumentType), nullable=False, index=True
    )
    subtype: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    audience: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    value_assessment: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # high, medium, low, none

    # Content metadata
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Staleness tracking (from doc-staleness-detector)
    staleness_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100
    last_meaningful_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Recommendation (from doc-classifier)
    recommended_action: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # keep, update, archive, merge, delete
    target_location: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Additional metadata (JSON for flexibility)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    concepts: Mapped[list["GraphConcept"]] = relationship(
        "GraphConcept", back_populates="source_document", cascade="all, delete-orphan"
    )
    requirements: Mapped[list["GraphRequirement"]] = relationship(
        "GraphRequirement", back_populates="source_document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GraphDocument(id={self.id}, path='{self.path}', type={self.doc_type})>"


class GraphConcept(Base):
    """
    Named concept extracted from documents.

    Stores concepts extracted by the doc-concept-extractor persona.
    Concepts are named ideas, products, features, or business entities
    that have a distinct identity in the knowledge graph.
    """

    __tablename__ = "graph_concepts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign keys
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_document_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("graph_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Concept identification
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    concept_type: Mapped[ConceptType] = mapped_column(
        SQLEnum(ConceptType), nullable=False, index=True
    )
    definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status and domain
    status: Mapped[ConceptStatus] = mapped_column(
        SQLEnum(ConceptStatus),
        default=ConceptStatus.UNKNOWN,
        nullable=False,
        index=True,
    )
    domain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Extraction metadata
    source_quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[ConfidenceLevel] = mapped_column(
        SQLEnum(ConfidenceLevel),
        default=ConfidenceLevel.MEDIUM,
        nullable=False,
    )

    # Related entities (JSON array of names for flexibility)
    related_entities: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)

    # Additional metadata
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    source_document: Mapped[Optional["GraphDocument"]] = relationship(
        "GraphDocument", back_populates="concepts"
    )

    def __repr__(self) -> str:
        return f"<GraphConcept(id={self.id}, name='{self.name}', type={self.concept_type})>"


class GraphRequirement(Base):
    """
    Requirement mined from documents.

    Stores requirements extracted by the doc-requirement-miner persona.
    Requirements are explicit or implicit statements about what a
    system MUST, SHOULD, or COULD do.
    """

    __tablename__ = "graph_requirements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign keys
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_document_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("graph_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Requirement identification
    req_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # REQ-XXX format
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Classification
    req_type: Mapped[RequirementType] = mapped_column(
        SQLEnum(RequirementType), nullable=False, index=True
    )
    priority: Mapped[RequirementPriority] = mapped_column(
        SQLEnum(RequirementPriority),
        default=RequirementPriority.UNKNOWN,
        nullable=False,
        index=True,
    )
    status: Mapped[RequirementStatus] = mapped_column(
        SQLEnum(RequirementStatus),
        default=RequirementStatus.PROPOSED,
        nullable=False,
        index=True,
    )

    # Traceability
    source_concept: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Which concept this relates to
    source_quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verification: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # How to verify this is met

    # Additional metadata
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    source_document: Mapped[Optional["GraphDocument"]] = relationship(
        "GraphDocument", back_populates="requirements"
    )

    def __repr__(self) -> str:
        return f"<GraphRequirement(id={self.id}, req_id='{self.req_id}', type={self.req_type})>"
