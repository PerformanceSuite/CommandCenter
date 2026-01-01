"""
Pydantic schemas for Phase 7 Graph Service

Request/response models for graph API endpoints and service methods.
"""

from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field

from app.models.graph import (
    AuditKind,
    AuditStatus,
    DependencyType,
    HealthStatus,
    LinkType,
    ServiceType,
    SpecItemSource,
    SpecItemStatus,
    SymbolKind,
    TaskKind,
)

# ============================================================================
# Query Filters
# ============================================================================


class GraphFilters(BaseModel):
    """Filters for graph queries"""

    languages: Optional[List[str]] = Field(
        None, description="Filter by programming languages (e.g., ['python', 'typescript'])"
    )
    file_paths: Optional[List[str]] = Field(
        None, description="Filter by file path patterns (glob-like)"
    )
    symbol_kinds: Optional[List[SymbolKind]] = Field(None, description="Filter by symbol types")
    service_types: Optional[List[ServiceType]] = Field(None, description="Filter by service types")


class SpecFilters(BaseModel):
    """Filters for spec item queries"""

    status: Optional[List[SpecItemStatus]] = Field(None, description="Filter by status")
    source: Optional[List[SpecItemSource]] = Field(None, description="Filter by source")


# ============================================================================
# Node Representations
# ============================================================================


class GraphNode(BaseModel):
    """Generic graph node representation"""

    id: str = Field(..., description="Unique node ID (entity_type:entity_id)")
    entity_type: str = Field(
        ...,
        description="Entity type (repo, file, symbol, service, task, spec, persona, workflow, execution)",
    )
    entity_id: int = Field(..., description="Database entity ID")
    label: str = Field(..., description="Display label for the node")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional node properties")

    class Config:
        from_attributes = True


class GraphEdge(BaseModel):
    """Graph edge representation"""

    from_node: str = Field(..., description="Source node ID (entity_type:entity_id)")
    to_node: str = Field(..., description="Target node ID (entity_type:entity_id)")
    type: str = Field(..., description="Edge type (import, call, depends_on, etc.)")
    weight: float = Field(1.0, description="Edge weight/strength")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional edge properties")

    class Config:
        from_attributes = True


# ============================================================================
# Response Models
# ============================================================================


class ProjectGraphResponse(BaseModel):
    """Response for project graph query"""

    nodes: List[GraphNode] = Field(..., description="All nodes in the graph")
    edges: List[GraphEdge] = Field(..., description="All edges in the graph")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Graph metadata (node counts, depth, etc.)",
    )


class DependencyGraph(BaseModel):
    """Response for dependency traversal"""

    root_symbol_id: int = Field(..., description="Starting symbol ID")
    nodes: List[GraphNode] = Field(..., description="Symbols in dependency tree")
    edges: List[GraphEdge] = Field(..., description="Dependency edges")
    depth_reached: int = Field(..., description="Maximum depth traversed")


class GhostNode(BaseModel):
    """Ghost node (spec/task without implementation)"""

    id: int = Field(..., description="SpecItem or Task ID")
    type: Literal["spec", "task"] = Field(..., description="Ghost node type")
    title: str = Field(..., description="Title")
    description: Optional[str] = Field(None, description="Description")
    status: SpecItemStatus = Field(..., description="Status")
    source: Optional[SpecItemSource] = Field(None, description="Source (for specs)")
    ref: Optional[str] = Field(None, description="Reference (file path, URL, etc.)")
    created_at: datetime

    class Config:
        from_attributes = True


class SearchResults(BaseModel):
    """Unified search results"""

    symbols: List[GraphNode] = Field(default_factory=list)
    files: List[GraphNode] = Field(default_factory=list)
    tasks: List[GraphNode] = Field(default_factory=list)
    total: int = Field(..., description="Total results across all types")


# ============================================================================
# Request Models
# ============================================================================


class CreateTaskRequest(BaseModel):
    """Request to create a task"""

    title: str = Field(..., min_length=1, max_length=512)
    kind: TaskKind
    spec_item_id: Optional[int] = None
    description: Optional[str] = None
    labels: Optional[List[str]] = None


class TriggerAuditRequest(BaseModel):
    """Request to trigger an audit"""

    target_entity: str = Field(
        ...,
        description="Target table name (graph_files, graph_symbols, etc.)",
    )
    target_id: int = Field(..., description="Target entity ID")
    kind: AuditKind


class LinkEntitiesRequest(BaseModel):
    """Request to create a link between entities"""

    from_entity: str = Field(..., description="Source table name")
    from_id: int = Field(..., description="Source entity ID")
    to_entity: str = Field(..., description="Target table name")
    to_id: int = Field(..., description="Target entity ID")
    type: LinkType
    weight: float = Field(1.0, ge=0.0, le=100.0)


class GraphSearchRequest(BaseModel):
    """Request for graph search"""

    query: str = Field(..., min_length=1)
    scope: List[Literal["symbols", "files", "tasks", "personas", "executions"]] = Field(default=["symbols", "files", "tasks"])


# ============================================================================
# Entity Response Models (for API endpoints)
# ============================================================================


class GraphRepoResponse(BaseModel):
    """Repository response"""

    id: int
    project_id: int
    provider: str
    owner: str
    name: str
    full_name: str
    default_branch: str
    root_path: Optional[str]
    last_indexed_commit: Optional[str]
    last_indexed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GraphFileResponse(BaseModel):
    """File response"""

    id: int
    repo_id: int
    path: str
    lang: Optional[str]
    hash: Optional[str]
    size: int
    lines: int
    last_indexed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GraphSymbolResponse(BaseModel):
    """Symbol response"""

    id: int
    file_id: int
    kind: SymbolKind
    name: str
    qualified_name: Optional[str]
    signature: Optional[str]
    range_start: int
    range_end: int
    exports: bool
    is_async: bool
    is_generator: bool
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GraphDependencyResponse(BaseModel):
    """Dependency response"""

    id: int
    from_symbol_id: int
    to_symbol_id: int
    type: DependencyType
    weight: float
    metadata: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class GraphServiceResponse(BaseModel):
    """Service response"""

    id: int
    project_id: int
    repo_id: Optional[int]
    name: str
    type: ServiceType
    endpoint: Optional[str]
    health_url: Optional[str]
    status: HealthStatus
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GraphHealthSampleResponse(BaseModel):
    """Health sample response"""

    id: int
    service_id: int
    status: HealthStatus
    latency_ms: Optional[float]
    details: Optional[dict]
    observed_at: datetime

    class Config:
        from_attributes = True


class GraphSpecItemResponse(BaseModel):
    """Spec item response"""

    id: int
    project_id: int
    source: SpecItemSource
    ref: Optional[str]
    title: str
    description: Optional[str]
    priority: int
    status: SpecItemStatus
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GraphTaskResponse(BaseModel):
    """Task response"""

    id: int
    project_id: int
    spec_item_id: Optional[int]
    title: str
    description: Optional[str]
    kind: TaskKind
    status: SpecItemStatus
    assignee: Optional[str]
    labels: Optional[List[str]]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GraphLinkResponse(BaseModel):
    """Link response"""

    id: int
    from_entity: str
    from_id: int
    to_entity: str
    to_id: int
    type: LinkType
    weight: float
    metadata: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class GraphAuditResponse(BaseModel):
    """Audit response"""

    id: int
    target_entity: str
    target_id: int
    kind: AuditKind
    status: AuditStatus
    summary: Optional[str]
    report_path: Optional[str]
    score: Optional[float]
    metadata: Optional[dict]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class GraphEventResponse(BaseModel):
    """Event response"""

    id: int
    subject: str
    payload: dict
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Federation Query Models
# ============================================================================


class FederationScope(BaseModel):
    """Scope for federation queries"""

    type: Literal["ecosystem", "projects"] = Field(
        ...,
        description="'ecosystem' for all projects, 'projects' for specific project IDs",
    )
    project_ids: Optional[List[int]] = Field(
        None,
        description="List of project IDs (required when type='projects')",
    )


class CrossProjectLinkResponse(BaseModel):
    """Cross-project link with full context"""

    id: int
    source_project_id: int
    target_project_id: int
    from_entity: str
    from_id: int
    to_entity: str
    to_id: int
    type: LinkType
    weight: float
    metadata: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class FederationQueryRequest(BaseModel):
    """Request for cross-project federation query"""

    scope: FederationScope = Field(
        ...,
        description="Query scope (ecosystem or specific projects)",
    )
    link_types: Optional[List[LinkType]] = Field(
        None,
        description="Filter by link types (None = all types)",
    )
    entity_types: Optional[List[str]] = Field(
        None,
        description="Filter by entity types (e.g., ['graph_repos', 'graph_symbols'])",
    )
    limit: int = Field(
        100,
        ge=1,
        le=1000,
        description="Maximum number of links to return",
    )
    offset: int = Field(
        0,
        ge=0,
        description="Pagination offset",
    )


class FederationQueryResponse(BaseModel):
    """Response for cross-project federation query"""

    links: List[CrossProjectLinkResponse] = Field(
        ...,
        description="Cross-project links matching the query",
    )
    total: int = Field(
        ...,
        description="Total number of matching links (before pagination)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Query metadata (projects involved, etc.)",
    )
