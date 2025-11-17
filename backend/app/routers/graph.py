"""
Graph API Router - Phase 7 REST API endpoints

Provides HTTP endpoints for querying and mutating the knowledge graph.
"""

from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.project_context import get_current_project_id
from app.database import get_db
from app.schemas.graph import (
    CreateTaskRequest,
    DependencyGraph,
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
from app.services.graph_service import GraphService

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


# ============================================================================
# Query Endpoints
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
