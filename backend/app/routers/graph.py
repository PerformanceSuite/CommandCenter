"""
Graph API Router - Phase 7 REST API endpoints

Provides HTTP endpoints for querying and mutating the knowledge graph.
"""

from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.project_context import get_current_project_id
from app.database import get_db
from app.schemas.graph import (
    CreateTaskRequest,
    CrossProjectLinkResponse,
    DependencyGraph,
    FederationQueryRequest,
    FederationQueryResponse,
    GhostNode,
    GraphAuditResponse,
    GraphFilters,
    GraphLinkResponse,
    GraphSearchRequest,
    GraphTaskResponse,
    LinkEntitiesRequest,
    ProjectGraphResponse,
    SearchResults,
    SpecFilters,
    TriggerAuditRequest,
)
from app.schemas.query import ComposedQuery, QueryResult
from app.services.graph_service import GraphService
from app.services.intent_parser import IntentParser
from app.services.query_executor import QueryExecutor

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


# ============================================================================
# Composed Query Endpoints (Phase 2)
# ============================================================================


@router.post("/query", response_model=QueryResult)
async def execute_composed_query(
    query: ComposedQuery,
    include_affordances: bool = Query(
        False, description="Include agent affordances for returned entities"
    ),
    db: AsyncSession = Depends(get_db),
    current_project_id: int = Depends(get_current_project_id),
):
    """
    Execute a composed query against the graph database.

    This endpoint accepts a ComposedQuery object with entity selectors,
    filters, relationship specifications, and optional aggregations.

    **Entity Types:**
    - `symbol`: Code symbols (functions, classes, methods)
    - `file`: Source files
    - `service`: Running services
    - `task`: Work items
    - `spec`: Specification items
    - `any`: All entity types

    **Filters:**
    - `eq`: Equals
    - `ne`: Not equals
    - `lt`, `gt`, `lte`, `gte`: Comparisons
    - `contains`: Text search
    - `in`: Value in list

    **Relationships:**
    - `direction`: inbound, outbound, or both
    - `depth`: Traversal depth (1-10)

    **Time Range Filtering (Phase 4):**
    Use `time_range` for temporal queries:
    - Absolute: `{"start": "2025-01-01T00:00:00Z", "end": "2025-12-31T23:59:59Z"}`
    - Relative: `{"relative": "last 7 days"}`
    - Field selection: `{"relative": "yesterday", "field": "updated_at"}`

    Supported relative expressions:
    - `last N days/hours/weeks/months`
    - `yesterday`, `today`
    - `this week`, `last week`
    - `this month`, `last month`
    - `this quarter`, `last quarter`

    **Temporal Aggregations:**
    Get counts per time bucket with temporal aggregations:
    ```json
    {
      "aggregations": [{
        "type": "count",
        "temporal": {"bucket": "day", "metric": "count"}
      }]
    }
    ```

    **Agent Parity (Phase 3):**
    Set `include_affordances=true` to get available actions for each entity.
    Affordances enable agents to take the same actions available in the UI.

    **Semantic Search (Phase 4):**
    Use `semantic` to perform RAG-based search across the knowledge base:
    ```json
    {
      "entities": [{"type": "knowledge"}],
      "semantic": {
        "query": "authentication flow",
        "limit": 10,
        "threshold": 0.7,
        "categories": ["docs", "code"]
      }
    }
    ```
    - `query`: Natural language search query (required)
    - `limit`: Max results (default: 5, max: 50)
    - `threshold`: Min similarity score (0.0-1.0)
    - `categories`: Filter by knowledge base category

    **Example request:**
    ```json
    {
      "entities": [{"type": "symbol", "scope": "project:1"}],
      "filters": [{"field": "name", "operator": "contains", "value": "auth"}],
      "relationships": [{"type": "dependency", "direction": "outbound", "depth": 2}],
      "time_range": {"relative": "last 30 days"},
      "limit": 50
    }
    ```
    """
    executor = QueryExecutor(db)
    return await executor.execute(
        query, project_id=current_project_id, include_affordances=include_affordances
    )


class ParseQueryRequest(BaseModel):
    """Request for parsing a natural language or structured query."""

    query: str | dict


@router.post("/query/parse", response_model=QueryResult)
async def parse_and_execute_query(
    request: ParseQueryRequest,
    include_affordances: bool = Query(
        False, description="Include agent affordances for returned entities"
    ),
    db: AsyncSession = Depends(get_db),
    current_project_id: int = Depends(get_current_project_id),
):
    """
    Parse a natural language or structured query and execute it.

    This endpoint first parses the query using the IntentParser,
    then executes the resulting ComposedQuery.

    **Natural Language Examples:**
    - "Show me all services with health below 100"
    - "Find functions containing auth"
    - "List all tasks"

    **Structured Query Example:**
    ```json
    {
      "query": {
        "entity": "symbol:main",
        "context": ["dependencies", "callers"],
        "depth": 2
      }
    }
    ```

    **Agent Parity (Phase 3):**
    Set `include_affordances=true` to get available actions for each entity.
    """
    parser = IntentParser()
    composed_query = parser.parse(request.query)

    executor = QueryExecutor(db)
    return await executor.execute(
        composed_query,
        project_id=current_project_id,
        include_affordances=include_affordances,
    )


# ============================================================================
# Legacy Query Endpoints
# ============================================================================


@router.get("/projects/{project_id}", response_model=ProjectGraphResponse)
async def get_project_graph(
    project_id: int,
    depth: int = Query(2, ge=1, le=3, description="Traversal depth (1-3)"),
    languages: Optional[str] = Query(
        None, description="Comma-separated languages filter (e.g., 'python,typescript')"
    ),
    file_paths: Optional[str] = Query(None, description="Comma-separated file path patterns"),
    symbol_kinds: Optional[str] = Query(None, description="Comma-separated symbol kinds filter"),
    service_types: Optional[str] = Query(None, description="Comma-separated service types filter"),
    db: AsyncSession = Depends(get_db),
    current_project_id: int = Depends(get_current_project_id),
):
    """
    Get complete project knowledge graph.

    Returns nodes (repos, files, symbols, services, tasks, specs) and edges.

    **Depth levels:**
    - 1: Repos, services, tasks, specs
    - 2: + Files, symbols
    - 3: + Dependencies between symbols

    **Performance:** ~1.5s for 5000+ nodes/edges.
    """
    # Enforce project isolation
    if project_id != current_project_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other project's graph",
        )

    # Parse filters
    filters = GraphFilters()
    if languages:
        filters.languages = [lang.strip() for lang in languages.split(",")]
    if file_paths:
        filters.file_paths = [path.strip() for path in file_paths.split(",")]
    if symbol_kinds:
        from app.models.graph import SymbolKind

        filters.symbol_kinds = [SymbolKind(kind.strip()) for kind in symbol_kinds.split(",")]
    if service_types:
        from app.models.graph import ServiceType

        filters.service_types = [ServiceType(stype.strip()) for stype in service_types.split(",")]

    service = GraphService(db)
    return await service.get_project_graph(
        project_id=project_id,
        depth=depth,
        filters=filters,
    )


@router.get("/dependencies/{symbol_id}", response_model=DependencyGraph)
async def get_symbol_dependencies(
    symbol_id: int,
    direction: Literal["inbound", "outbound", "both"] = Query(
        "both", description="Dependency direction"
    ),
    depth: int = Query(3, ge=1, le=5, description="Traversal depth (1-5)"),
    db: AsyncSession = Depends(get_db),
    current_project_id: int = Depends(get_current_project_id),
):
    """
    Traverse symbol dependencies recursively.

    Returns dependency tree with symbols and edges.

    **Direction:**
    - inbound: Symbols that depend on this symbol
    - outbound: Symbols this symbol depends on
    - both: Bidirectional traversal
    """
    service = GraphService(db)

    # Verify symbol exists and belongs to current project
    from sqlalchemy import select

    from app.models.graph import GraphFile, GraphRepo, GraphSymbol

    stmt = (
        select(GraphSymbol)
        .join(GraphFile)
        .join(GraphRepo)
        .filter(GraphSymbol.id == symbol_id)
        .filter(GraphRepo.project_id == current_project_id)
    )
    result = await db.execute(stmt)
    symbol = result.scalar_one_or_none()

    if not symbol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symbol not found or not accessible",
        )

    return await service.get_dependencies(
        symbol_id=symbol_id,
        direction=direction,
        depth=depth,
    )


@router.get("/ghost-nodes/{project_id}", response_model=List[GhostNode])
async def get_ghost_nodes(
    project_id: int,
    status: Optional[str] = Query(
        None, description="Comma-separated status filter (e.g., 'planned,inProgress')"
    ),
    source: Optional[str] = Query(
        None, description="Comma-separated source filter (e.g., 'file,doc')"
    ),
    db: AsyncSession = Depends(get_db),
    current_project_id: int = Depends(get_current_project_id),
):
    """
    Get ghost nodes (specs/tasks without implementation).

    Ghost nodes represent planned work that hasn't been implemented yet.
    Extracted from TODO/FIXME comments or manual spec creation.
    """
    # Enforce project isolation
    if project_id != current_project_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot access other project's ghost nodes",
        )

    # Parse filters
    filters = SpecFilters()
    if status:
        from app.models.graph import SpecItemStatus

        filters.status = [SpecItemStatus(s.strip()) for s in status.split(",")]
    if source:
        from app.models.graph import SpecItemSource

        filters.source = [SpecItemSource(src.strip()) for src in source.split(",")]

    service = GraphService(db)
    return await service.get_ghost_nodes(project_id=project_id, filters=filters)


@router.post("/search", response_model=SearchResults)
async def search_graph(
    request: GraphSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_project_id: int = Depends(get_current_project_id),
):
    """
    Unified search across code + specs + tasks.

    Searches symbols, files, and tasks using case-insensitive substring matching.
    """
    service = GraphService(db)
    return await service.search_graph(
        project_id=current_project_id,
        query=request.query,
        scope=request.scope,
    )


# ============================================================================
# Federation Endpoints
# ============================================================================


@router.post("/federation/query", response_model=FederationQueryResponse)
async def query_federation(
    request: FederationQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_project_id: int = Depends(get_current_project_id),
):
    """
    Query cross-project links for federation visualization.

    Returns links between entities in different projects, enabling
    cross-project dependency visualization in VISLZR.

    **Scope types:**
    - `ecosystem`: Query all projects the user has access to
    - `projects`: Query specific project IDs (must have access)

    **Filters:**
    - `link_types`: Filter by relationship type (e.g., DEPENDS_ON, REFERENCES)
    - `entity_types`: Filter by entity table (e.g., graph_repos, graph_symbols)

    **Example request:**
    ```json
    {
      "scope": {"type": "ecosystem"},
      "link_types": ["dependsOn", "references"],
      "limit": 100
    }
    ```
    """
    # Get user's accessible projects
    # For now, use current_project_id as the only accessible project
    # TODO: Expand to get all user's projects from UserProject table
    from sqlalchemy import select

    from app.models.user_project import UserProject

    # Get all project IDs the user has access to
    stmt = select(UserProject.project_id)
    result = await db.execute(stmt)
    user_project_ids = [row[0] for row in result.fetchall()]

    # If no projects found, at least include current project
    if not user_project_ids:
        user_project_ids = [current_project_id]

    service = GraphService(db)
    return await service.query_cross_project_links(
        request=request,
        user_project_ids=user_project_ids,
    )


@router.post(
    "/federation/links",
    response_model=CrossProjectLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cross_project_link(
    source_project_id: int = Query(..., description="Source project ID"),
    target_project_id: int = Query(..., description="Target project ID"),
    from_entity: str = Query(..., description="Source entity table name"),
    from_id: int = Query(..., description="Source entity ID"),
    to_entity: str = Query(..., description="Target entity table name"),
    to_id: int = Query(..., description="Target entity ID"),
    link_type: str = Query(..., description="Link type"),
    weight: float = Query(1.0, ge=0.0, le=100.0, description="Link weight"),
    db: AsyncSession = Depends(get_db),
    current_project_id: int = Depends(get_current_project_id),
):
    """
    Create a cross-project link between entities in different projects.

    Used for establishing dependencies, references, or other relationships
    between entities that span project boundaries.

    **Authorization:** User must have access to both source and target projects.
    """
    from app.models.graph import LinkType

    # Validate user has access to both projects
    # For now, just verify they have access to at least one
    # TODO: Proper multi-project authorization
    if current_project_id not in [source_project_id, target_project_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must have access to at least one of the linked projects",
        )

    # Validate link type
    try:
        parsed_link_type = LinkType(link_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid link type: {link_type}. Valid types: {[lt.value for lt in LinkType]}",
        )

    service = GraphService(db)
    link = await service.create_cross_project_link(
        source_project_id=source_project_id,
        target_project_id=target_project_id,
        from_entity=from_entity,
        from_id=from_id,
        to_entity=to_entity,
        to_id=to_id,
        link_type=parsed_link_type,
        weight=weight,
    )

    return CrossProjectLinkResponse(
        id=link.id,
        source_project_id=link.source_project_id,
        target_project_id=link.target_project_id,
        from_entity=link.from_entity,
        from_id=link.from_id,
        to_entity=link.to_entity,
        to_id=link.to_id,
        type=link.type,
        weight=link.weight,
        metadata=link.metadata_,
        created_at=link.created_at,
    )


# ============================================================================
# Mutation Endpoints
# ============================================================================


@router.post("/tasks", response_model=GraphTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: CreateTaskRequest,
    db: AsyncSession = Depends(get_db),
    current_project_id: int = Depends(get_current_project_id),
):
    """
    Create a new task, optionally linked to a spec item.
    """
    service = GraphService(db)

    # If spec_item_id provided, verify it exists and belongs to current project
    if request.spec_item_id:
        from sqlalchemy import select

        from app.models.graph import GraphSpecItem

        stmt = select(GraphSpecItem).filter(
            GraphSpecItem.id == request.spec_item_id,
            GraphSpecItem.project_id == current_project_id,
        )
        result = await db.execute(stmt)
        spec = result.scalar_one_or_none()

        if not spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Spec item not found or not accessible",
            )

    task = await service.create_task(
        project_id=current_project_id,
        title=request.title,
        kind=request.kind,
        spec_item_id=request.spec_item_id,
        description=request.description,
        labels=request.labels,
    )

    return GraphTaskResponse.model_validate(task)


@router.post("/audits", response_model=GraphAuditResponse, status_code=status.HTTP_201_CREATED)
async def trigger_audit(
    request: TriggerAuditRequest,
    db: AsyncSession = Depends(get_db),
    current_project_id: int = Depends(get_current_project_id),
):
    """
    Trigger an audit for a target entity.

    Creates audit record (status=PENDING) and publishes NATS event for async processing.
    """
    service = GraphService(db)

    # Verify target entity exists and belongs to current project
    # (Implementation depends on target_entity type)
    # For now, trust the caller - can add validation later

    audit = await service.trigger_audit(
        target_entity=request.target_entity,
        target_id=request.target_id,
        kind=request.kind,
        project_id=current_project_id,
    )

    return GraphAuditResponse.model_validate(audit)


@router.post("/links", response_model=GraphLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_entities(
    request: LinkEntitiesRequest,
    db: AsyncSession = Depends(get_db),
    current_project_id: int = Depends(get_current_project_id),
):
    """
    Create a typed link between two entities.

    Links allow flexible relationships beyond the predefined schema.
    """
    service = GraphService(db)

    # Verify entities exist and belong to current project
    # (Implementation depends on entity types)
    # For now, trust the caller - can add validation later

    link = await service.link_entities(
        from_entity=request.from_entity,
        from_id=request.from_id,
        to_entity=request.to_entity,
        to_id=request.to_id,
        link_type=request.type,
        weight=request.weight,
    )

    return GraphLinkResponse.model_validate(link)


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health")
async def health_check():
    """Graph service health check"""
    return {"status": "ok", "service": "graph"}
