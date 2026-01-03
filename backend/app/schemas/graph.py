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
    ConceptStatus,
    ConceptType,
    ConfidenceLevel,
    DependencyType,
    DocumentStatus,
    DocumentType,
    HealthStatus,
    LinkType,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
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
    scope: List[Literal["symbols", "files", "tasks", "personas", "executions"]] = Field(
        default=["symbols", "files", "tasks"]
    )


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


# ============================================================================
# Document Intelligence Schemas
# ============================================================================


class GraphDocumentResponse(BaseModel):
    """Document response"""

    id: int
    project_id: int
    path: str
    title: Optional[str]
    doc_type: DocumentType
    subtype: Optional[str]
    status: DocumentStatus
    audience: Optional[str]
    value_assessment: Optional[str]
    word_count: int
    content_hash: Optional[str]
    staleness_score: Optional[int]
    last_meaningful_date: Optional[datetime]
    recommended_action: Optional[str]
    target_location: Optional[str]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime
    last_analyzed_at: Optional[datetime]

    class Config:
        from_attributes = True


class GraphConceptResponse(BaseModel):
    """Concept response"""

    id: int
    project_id: int
    source_document_id: Optional[int]
    name: str
    concept_type: ConceptType
    definition: Optional[str]
    status: ConceptStatus
    domain: Optional[str]
    source_quote: Optional[str]
    confidence: ConfidenceLevel
    related_entities: Optional[List[str]]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GraphRequirementResponse(BaseModel):
    """Requirement response"""

    id: int
    project_id: int
    source_document_id: Optional[int]
    req_id: str
    text: str
    req_type: RequirementType
    priority: RequirementPriority
    status: RequirementStatus
    source_concept: Optional[str]
    source_quote: Optional[str]
    verification: Optional[str]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Document Intelligence Request Models
# ============================================================================


class CreateDocumentRequest(BaseModel):
    """Request to create/upsert a document"""

    path: str = Field(..., min_length=1, max_length=1024)
    title: Optional[str] = Field(None, max_length=512)
    doc_type: DocumentType
    subtype: Optional[str] = Field(None, max_length=100)
    status: DocumentStatus = DocumentStatus.ACTIVE
    audience: Optional[str] = Field(None, max_length=255)
    value_assessment: Optional[Literal["high", "medium", "low", "none"]] = None
    word_count: int = 0
    content_hash: Optional[str] = None
    staleness_score: Optional[int] = Field(None, ge=0, le=100)
    last_meaningful_date: Optional[datetime] = None
    recommended_action: Optional[
        Literal["keep", "update", "archive", "merge", "extract_and_archive", "delete"]
    ] = None
    target_location: Optional[str] = None
    metadata: Optional[dict] = None


class CreateConceptRequest(BaseModel):
    """Request to create a concept"""

    name: str = Field(..., min_length=1, max_length=255)
    concept_type: ConceptType
    source_document_id: Optional[int] = None
    definition: Optional[str] = None
    status: ConceptStatus = ConceptStatus.UNKNOWN
    domain: Optional[str] = Field(None, max_length=100)
    source_quote: Optional[str] = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    related_entities: Optional[List[str]] = None
    metadata: Optional[dict] = None


class CreateRequirementRequest(BaseModel):
    """Request to create a requirement"""

    req_id: str = Field(..., min_length=1, max_length=50, pattern=r"^REQ-[\w-]+$")
    text: str = Field(..., min_length=1)
    req_type: RequirementType
    source_document_id: Optional[int] = None
    priority: RequirementPriority = RequirementPriority.UNKNOWN
    status: RequirementStatus = RequirementStatus.PROPOSED
    source_concept: Optional[str] = Field(None, max_length=255)
    source_quote: Optional[str] = None
    verification: Optional[str] = None
    metadata: Optional[dict] = None


class DocumentFilters(BaseModel):
    """Filters for document queries"""

    doc_types: Optional[List[DocumentType]] = Field(None, description="Filter by document types")
    statuses: Optional[List[DocumentStatus]] = Field(None, description="Filter by status")
    min_staleness: Optional[int] = Field(None, ge=0, le=100, description="Minimum staleness score")
    max_staleness: Optional[int] = Field(None, ge=0, le=100, description="Maximum staleness score")
    recommended_actions: Optional[List[str]] = Field(
        None, description="Filter by recommended action"
    )


class ConceptFilters(BaseModel):
    """Filters for concept queries"""

    concept_types: Optional[List[ConceptType]] = Field(None, description="Filter by concept types")
    statuses: Optional[List[ConceptStatus]] = Field(None, description="Filter by status")
    domains: Optional[List[str]] = Field(None, description="Filter by domain")
    min_confidence: Optional[ConfidenceLevel] = Field(None, description="Minimum confidence level")


class RequirementFilters(BaseModel):
    """Filters for requirement queries"""

    req_types: Optional[List[RequirementType]] = Field(
        None, description="Filter by requirement types"
    )
    priorities: Optional[List[RequirementPriority]] = Field(None, description="Filter by priority")
    statuses: Optional[List[RequirementStatus]] = Field(None, description="Filter by status")
    source_concept: Optional[str] = Field(None, description="Filter by source concept name")


# ============================================================================
# Document Intelligence Batch Operations
# ============================================================================


class BatchIngestConceptsRequest(BaseModel):
    """Request to batch ingest concepts from doc-concept-extractor output"""

    source_document_id: Optional[int] = Field(None, description="Source document ID if known")
    concepts: List[CreateConceptRequest] = Field(..., min_length=1)


class BatchIngestRequirementsRequest(BaseModel):
    """Request to batch ingest requirements from doc-requirement-miner output"""

    source_document_id: Optional[int] = Field(None, description="Source document ID if known")
    requirements: List[CreateRequirementRequest] = Field(..., min_length=1)


class BatchIngestResponse(BaseModel):
    """Response for batch ingest operations"""

    created: int = Field(..., description="Number of entities created")
    updated: int = Field(..., description="Number of entities updated")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")


class IngestDocumentIntelligenceRequest(BaseModel):
    """Request to ingest Document Intelligence pipeline output.

    Accepts the combined output from all Document Intelligence personas:
    - Documents from doc-classifier
    - Concepts from doc-concept-extractor
    - Requirements from doc-requirement-miner

    Documents are processed first to establish IDs, then concepts and
    requirements are linked to their source documents by path.
    """

    documents: List[CreateDocumentRequest] = Field(
        default_factory=list,
        description="Classified documents from doc-classifier",
    )
    concepts: List[CreateConceptRequest] = Field(
        default_factory=list,
        description="Extracted concepts from doc-concept-extractor",
    )
    requirements: List[CreateRequirementRequest] = Field(
        default_factory=list,
        description="Mined requirements from doc-requirement-miner",
    )


class IngestDocumentIntelligenceResponse(BaseModel):
    """Response for Document Intelligence ingestion."""

    documents_created: int = Field(0, description="Documents created")
    documents_updated: int = Field(0, description="Documents updated (by path)")
    concepts_created: int = Field(0, description="Concepts created")
    concepts_updated: int = Field(0, description="Concepts updated (by name)")
    requirements_created: int = Field(0, description="Requirements created")
    requirements_updated: int = Field(0, description="Requirements updated (by req_id)")
    links_created: int = Field(0, description="Links created between entities")
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (processing time, etc.)",
    )


# ============================================================================
# Review Queue & Approval Workflow
# ============================================================================


class ConceptReviewItem(BaseModel):
    """Concept with source document path for review UI."""

    id: int
    project_id: int
    source_document_id: Optional[int]
    source_document_path: Optional[str] = Field(
        None, description="Path of source document (joined from graph_documents)"
    )
    name: str
    concept_type: ConceptType
    definition: Optional[str]
    status: ConceptStatus
    domain: Optional[str]
    source_quote: Optional[str]
    confidence: ConfidenceLevel
    related_entities: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


class RequirementReviewItem(BaseModel):
    """Requirement with source document path for review UI."""

    id: int
    project_id: int
    source_document_id: Optional[int]
    source_document_path: Optional[str] = Field(
        None, description="Path of source document (joined from graph_documents)"
    )
    req_id: str
    text: str
    req_type: RequirementType
    priority: RequirementPriority
    status: RequirementStatus
    source_concept: Optional[str]
    source_quote: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewQueueConceptsResponse(BaseModel):
    """Response for concepts review queue."""

    items: List[ConceptReviewItem]
    total_pending: int = Field(..., description="Total items pending review")
    has_more: bool = Field(..., description="Whether there are more items beyond limit")


class ReviewQueueRequirementsResponse(BaseModel):
    """Response for requirements review queue."""

    items: List[RequirementReviewItem]
    total_pending: int = Field(..., description="Total items pending review")
    has_more: bool = Field(..., description="Whether there are more items beyond limit")


class ApproveConceptsRequest(BaseModel):
    """Request to approve concepts and optionally index to KnowledgeBeast."""

    ids: List[int] = Field(..., min_length=1, description="Concept IDs to approve")
    status: ConceptStatus = Field(
        ConceptStatus.ACTIVE,
        description="Status to set (active, implemented, deprecated)",
    )
    index_to_kb: bool = Field(
        True, description="Whether to index approved concepts to KnowledgeBeast"
    )


class ApproveRequirementsRequest(BaseModel):
    """Request to approve requirements and optionally index to KnowledgeBeast."""

    ids: List[int] = Field(..., min_length=1, description="Requirement IDs to approve")
    status: RequirementStatus = Field(
        RequirementStatus.ACCEPTED,
        description="Status to set (accepted, implemented, verified)",
    )
    index_to_kb: bool = Field(
        True, description="Whether to index approved requirements to KnowledgeBeast"
    )


class RejectEntitiesRequest(BaseModel):
    """Request to reject (delete) entities."""

    ids: List[int] = Field(..., min_length=1, description="Entity IDs to delete")


class ApprovalResponse(BaseModel):
    """Response for approval operations."""

    approved: int = Field(..., description="Number of items approved")
    indexed_to_kb: int = Field(0, description="Number of items indexed to KnowledgeBeast")


class RejectionResponse(BaseModel):
    """Response for rejection (deletion) operations."""

    deleted: int = Field(..., description="Number of items deleted")


# ============================================================================
# Document CRUD Schemas
# ============================================================================


class DocumentListResponse(BaseModel):
    """Paginated document list response."""

    items: List[GraphDocumentResponse]
    total: int = Field(..., description="Total number of documents matching filters")
    has_more: bool = Field(..., description="Whether there are more items beyond limit")


class DocumentWithEntitiesResponse(BaseModel):
    """Document with its extracted concepts and requirements."""

    document: GraphDocumentResponse
    concepts: List[GraphConceptResponse] = Field(default_factory=list)
    requirements: List[GraphRequirementResponse] = Field(default_factory=list)
    pending_concept_count: int = Field(0, description="Count of concepts pending review")
    pending_requirement_count: int = Field(0, description="Count of requirements pending review")


class UpdateDocumentRequest(BaseModel):
    """Request to update document fields (all optional for partial update)."""

    title: Optional[str] = Field(None, max_length=512)
    doc_type: Optional[DocumentType] = None
    subtype: Optional[str] = Field(None, max_length=100)
    status: Optional[DocumentStatus] = None
    audience: Optional[str] = Field(None, max_length=255)
    value_assessment: Optional[str] = None
    recommended_action: Optional[str] = None
    target_location: Optional[str] = Field(None, max_length=1024)
    metadata: Optional[dict] = None


class DocumentDeleteResponse(BaseModel):
    """Response for document deletion."""

    deleted: bool = Field(..., description="Whether document was deleted")
    cascaded_concepts: int = Field(0, description="Number of concepts deleted (if cascade)")
    cascaded_requirements: int = Field(0, description="Number of requirements deleted (if cascade)")


# ============================================================================
# Simple Entity Creation Schemas
# ============================================================================


class CreateSimpleConceptRequest(BaseModel):
    """Simplified request for manual concept creation."""

    name: str = Field(..., min_length=1, max_length=255, description="Concept name")
    concept_type: ConceptType = Field(..., description="Type of concept")
    definition: Optional[str] = Field(None, description="Optional definition")
    source_document_id: Optional[int] = Field(None, description="Optional source document")


class CreateSimpleRequirementRequest(BaseModel):
    """Simplified request for manual requirement creation."""

    text: str = Field(..., min_length=1, description="Requirement text")
    req_type: RequirementType = Field(..., description="Type of requirement")
    priority: RequirementPriority = Field(RequirementPriority.MEDIUM, description="Priority level")
    source_document_id: Optional[int] = Field(None, description="Optional source document")


class UpdateConceptRequest(BaseModel):
    """Request to update concept fields (all optional for partial update)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    concept_type: Optional[ConceptType] = None
    definition: Optional[str] = None
    status: Optional[ConceptStatus] = None
    domain: Optional[str] = Field(None, max_length=100)
    source_quote: Optional[str] = None
    confidence: Optional[ConfidenceLevel] = None
    related_entities: Optional[List[str]] = None
    metadata: Optional[dict] = None


class UpdateRequirementRequest(BaseModel):
    """Request to update requirement fields (all optional for partial update)."""

    text: Optional[str] = Field(None, min_length=1)
    req_type: Optional[RequirementType] = None
    priority: Optional[RequirementPriority] = None
    status: Optional[RequirementStatus] = None
    source_concept: Optional[str] = Field(None, max_length=255)
    source_quote: Optional[str] = None
    verification: Optional[str] = None
    metadata: Optional[dict] = None
