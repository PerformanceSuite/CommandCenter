"""
GraphService - Business logic for Phase 7 Graph Service

Encapsulates all graph database operations with multi-tenant isolation.
"""

import logging
from typing import List, Literal, Optional, Sequence
from uuid import uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.graph import (
    AuditKind,
    AuditStatus,
    GraphAudit,
    GraphDependency,
    GraphFile,
    GraphLink,
    GraphRepo,
)
from app.models.graph import GraphService as GraphServiceModel
from app.models.graph import (
    GraphSpecItem,
    GraphSymbol,
    GraphTask,
    LinkType,
    SpecItemStatus,
    TaskKind,
)
from app.nats_client import get_nats_client
from app.models.agent_execution import AgentExecution
from app.schemas.graph import (
    CrossProjectLinkResponse,
    DependencyGraph,
    FederationQueryRequest,
    FederationQueryResponse,
    GhostNode,
    GraphEdge,
    GraphFilters,
    GraphNode,
    ProjectGraphResponse,
    SearchResults,
    SpecFilters,
)
from app.schemas.graph_events import AuditRequestedEvent, AuditResultEvent, GraphTaskCreatedEvent

logger = logging.getLogger(__name__)


class GraphService:
    """Graph service for querying and mutating the knowledge graph"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # Query Operations
    # ========================================================================

    async def get_project_graph(
        self,
        project_id: int,
        depth: int = 2,
        filters: Optional[GraphFilters] = None,
    ) -> ProjectGraphResponse:
        """
        Return complete project graph with nodes and edges.

        Args:
            project_id: Project for multi-tenant isolation
            depth: How many levels of relationships to traverse (1-3)
            filters: Optional filters for languages, file paths, etc.

        Returns:
            ProjectGraphResponse with nodes and edges lists
        """
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        filters = filters or GraphFilters()

        # Query repos
        stmt = select(GraphRepo).filter(GraphRepo.project_id == project_id)
        result = await self.db.execute(stmt)
        repos = result.scalars().all()

        for repo in repos:
            nodes.append(
                GraphNode(
                    id=f"repo:{repo.id}",
                    entity_type="repo",
                    entity_id=repo.id,
                    label=repo.full_name,
                    metadata={
                        "provider": repo.provider,
                        "default_branch": repo.default_branch,
                        "last_indexed_at": (
                            repo.last_indexed_at.isoformat() if repo.last_indexed_at else None
                        ),
                    },
                )
            )

        # Query files with optional filters
        file_stmt = select(GraphFile).join(GraphRepo).filter(GraphRepo.project_id == project_id)

        if filters.languages:
            file_stmt = file_stmt.filter(GraphFile.lang.in_(filters.languages))

        if filters.file_paths:
            # Simple path matching (can be enhanced with glob patterns)
            path_conditions = [GraphFile.path.contains(pattern) for pattern in filters.file_paths]
            file_stmt = file_stmt.filter(or_(*path_conditions))

        result = await self.db.execute(file_stmt)
        files = result.scalars().all()

        for file in files:
            nodes.append(
                GraphNode(
                    id=f"file:{file.id}",
                    entity_type="file",
                    entity_id=file.id,
                    label=file.path,
                    metadata={
                        "lang": file.lang,
                        "lines": file.lines,
                        "size": file.size,
                    },
                )
            )
            # Add repo -> file edge
            edges.append(
                GraphEdge(
                    from_node=f"repo:{file.repo_id}",
                    to_node=f"file:{file.id}",
                    type="contains",
                )
            )

        # Query symbols (if depth >= 2)
        if depth >= 2:
            symbol_stmt = (
                select(GraphSymbol)
                .join(GraphFile)
                .join(GraphRepo)
                .filter(GraphRepo.project_id == project_id)
            )

            if filters.symbol_kinds:
                symbol_stmt = symbol_stmt.filter(GraphSymbol.kind.in_(filters.symbol_kinds))

            result = await self.db.execute(symbol_stmt)
            symbols = result.scalars().all()

            for symbol in symbols:
                nodes.append(
                    GraphNode(
                        id=f"symbol:{symbol.id}",
                        entity_type="symbol",
                        entity_id=symbol.id,
                        label=symbol.name,
                        metadata={
                            "kind": symbol.kind.value,
                            "qualified_name": symbol.qualified_name,
                            "signature": symbol.signature,
                            "exports": symbol.exports,
                        },
                    )
                )
                # Add file -> symbol edge
                edges.append(
                    GraphEdge(
                        from_node=f"file:{symbol.file_id}",
                        to_node=f"symbol:{symbol.id}",
                        type="contains",
                    )
                )

            # Query dependencies (if depth >= 3)
            if depth >= 3:
                # Get symbol IDs for this project
                symbol_ids = [s.id for s in symbols]

                dep_stmt = select(GraphDependency).filter(
                    or_(
                        GraphDependency.from_symbol_id.in_(symbol_ids),
                        GraphDependency.to_symbol_id.in_(symbol_ids),
                    )
                )
                result = await self.db.execute(dep_stmt)
                dependencies = result.scalars().all()

                for dep in dependencies:
                    edges.append(
                        GraphEdge(
                            from_node=f"symbol:{dep.from_symbol_id}",
                            to_node=f"symbol:{dep.to_symbol_id}",
                            type=dep.type.value,
                            weight=dep.weight,
                        )
                    )

        # Query services
        service_stmt = select(GraphServiceModel).filter(GraphServiceModel.project_id == project_id)

        if filters.service_types:
            service_stmt = service_stmt.filter(GraphServiceModel.type.in_(filters.service_types))

        result = await self.db.execute(service_stmt)
        services = result.scalars().all()

        for service in services:
            nodes.append(
                GraphNode(
                    id=f"service:{service.id}",
                    entity_type="service",
                    entity_id=service.id,
                    label=service.name,
                    metadata={
                        "type": service.type.value,
                        "status": service.status.value,
                        "endpoint": service.endpoint,
                    },
                )
            )
            # Add repo -> service edge if linked
            if service.repo_id:
                edges.append(
                    GraphEdge(
                        from_node=f"repo:{service.repo_id}",
                        to_node=f"service:{service.id}",
                        type="produces",
                    )
                )

        # Query tasks
        task_stmt = select(GraphTask).filter(GraphTask.project_id == project_id)
        result = await self.db.execute(task_stmt)
        tasks = result.scalars().all()

        for task in tasks:
            nodes.append(
                GraphNode(
                    id=f"task:{task.id}",
                    entity_type="task",
                    entity_id=task.id,
                    label=task.title,
                    metadata={
                        "kind": task.kind.value,
                        "status": task.status.value,
                        "assignee": task.assignee,
                    },
                )
            )
            # Add spec -> task edge if linked
            if task.spec_item_id:
                edges.append(
                    GraphEdge(
                        from_node=f"spec:{task.spec_item_id}",
                        to_node=f"task:{task.id}",
                        type="implements",
                    )
                )

        # Query spec items
        spec_stmt = select(GraphSpecItem).filter(GraphSpecItem.project_id == project_id)
        result = await self.db.execute(spec_stmt)
        specs = result.scalars().all()

        for spec in specs:
            nodes.append(
                GraphNode(
                    id=f"spec:{spec.id}",
                    entity_type="spec",
                    entity_id=spec.id,
                    label=spec.title,
                    metadata={
                        "source": spec.source.value,
                        "status": spec.status.value,
                        "priority": spec.priority,
                    },
                )
            )

        # Query generic links
        link_stmt = select(GraphLink).filter(
            or_(
                and_(
                    GraphLink.from_entity == "graph_repos",
                    GraphLink.from_id.in_([r.id for r in repos]),
                ),
                and_(
                    GraphLink.to_entity == "graph_repos",
                    GraphLink.to_id.in_([r.id for r in repos]),
                ),
            )
        )
        result = await self.db.execute(link_stmt)
        links = result.scalars().all()

        for link in links:
            edges.append(
                GraphEdge(
                    from_node=f"{link.from_entity.replace('graph_', '')}:{link.from_id}",
                    to_node=f"{link.to_entity.replace('graph_', '')}:{link.to_id}",
                    type=link.type.value,
                    weight=link.weight,
                )
            )

        return ProjectGraphResponse(
            nodes=nodes,
            edges=edges,
            metadata={
                "node_count": len(nodes),
                "edge_count": len(edges),
                "depth": depth,
                "repos": len(repos),
                "files": len(files),
                "symbols": len(symbols) if depth >= 2 else 0,
                "services": len(services),
                "tasks": len(tasks),
                "specs": len(specs),
            },
        )

    async def get_dependencies(
        self,
        symbol_id: int,
        direction: Literal["inbound", "outbound", "both"] = "both",
        depth: int = 3,
    ) -> DependencyGraph:
        """
        Traverse symbol dependencies recursively.

        Args:
            symbol_id: Starting symbol ID
            direction: Which dependencies to follow
            depth: Maximum traversal depth

        Returns:
            DependencyGraph with symbols and dependency edges
        """
        visited_ids = set()
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        current_level = [symbol_id]
        current_depth = 0

        while current_level and current_depth < depth:
            next_level = []

            for sid in current_level:
                if sid in visited_ids:
                    continue

                visited_ids.add(sid)

                # Get symbol details
                stmt = select(GraphSymbol).filter(GraphSymbol.id == sid)
                result = await self.db.execute(stmt)
                symbol = result.scalar_one_or_none()

                if not symbol:
                    continue

                nodes.append(
                    GraphNode(
                        id=f"symbol:{symbol.id}",
                        entity_type="symbol",
                        entity_id=symbol.id,
                        label=symbol.name,
                        metadata={
                            "kind": symbol.kind.value,
                            "qualified_name": symbol.qualified_name,
                        },
                    )
                )

                # Get dependencies
                if direction in ["outbound", "both"]:
                    stmt = select(GraphDependency).filter(GraphDependency.from_symbol_id == sid)
                    result = await self.db.execute(stmt)
                    outbound_deps = result.scalars().all()

                    for dep in outbound_deps:
                        edges.append(
                            GraphEdge(
                                from_node=f"symbol:{dep.from_symbol_id}",
                                to_node=f"symbol:{dep.to_symbol_id}",
                                type=dep.type.value,
                                weight=dep.weight,
                            )
                        )
                        if dep.to_symbol_id not in visited_ids:
                            next_level.append(dep.to_symbol_id)

                if direction in ["inbound", "both"]:
                    stmt = select(GraphDependency).filter(GraphDependency.to_symbol_id == sid)
                    result = await self.db.execute(stmt)
                    inbound_deps = result.scalars().all()

                    for dep in inbound_deps:
                        edges.append(
                            GraphEdge(
                                from_node=f"symbol:{dep.from_symbol_id}",
                                to_node=f"symbol:{dep.to_symbol_id}",
                                type=dep.type.value,
                                weight=dep.weight,
                            )
                        )
                        if dep.from_symbol_id not in visited_ids:
                            next_level.append(dep.from_symbol_id)

            current_level = next_level
            current_depth += 1

        return DependencyGraph(
            root_symbol_id=symbol_id,
            nodes=nodes,
            edges=edges,
            depth_reached=current_depth,
        )

    async def get_ghost_nodes(
        self,
        project_id: int,
        filters: Optional[SpecFilters] = None,
    ) -> List[GhostNode]:
        """
        Find SpecItems/Tasks without backing Files/Symbols.

        Ghost nodes represent planned work that hasn't been implemented yet.

        Args:
            project_id: Project scope
            filters: Optional status/source filters

        Returns:
            List of GhostNode (SpecItem/Task without implementation)
        """
        ghost_nodes: List[GhostNode] = []
        filters = filters or SpecFilters()

        # Query spec items
        spec_stmt = select(GraphSpecItem).filter(GraphSpecItem.project_id == project_id)

        if filters.status:
            spec_stmt = spec_stmt.filter(GraphSpecItem.status.in_(filters.status))

        if filters.source:
            spec_stmt = spec_stmt.filter(GraphSpecItem.source.in_(filters.source))

        result = await self.db.execute(spec_stmt)
        specs = result.scalars().all()

        for spec in specs:
            # Check if spec has implementation (via links)
            link_stmt = select(GraphLink).filter(
                and_(
                    GraphLink.from_entity == "graph_spec_items",
                    GraphLink.from_id == spec.id,
                    GraphLink.type == LinkType.IMPLEMENTS,
                )
            )
            result = await self.db.execute(link_stmt)
            links = result.scalars().all()

            # If no implementation links, it's a ghost node
            if not links:
                ghost_nodes.append(
                    GhostNode(
                        id=spec.id,
                        type="spec",
                        title=spec.title,
                        description=spec.description,
                        status=spec.status,
                        source=spec.source,
                        ref=spec.ref,
                        created_at=spec.created_at,
                    )
                )

        # Query tasks without linked symbols/files
        task_stmt = select(GraphTask).filter(GraphTask.project_id == project_id)

        if filters.status:
            task_stmt = task_stmt.filter(GraphTask.status.in_(filters.status))

        result = await self.db.execute(task_stmt)
        tasks = result.scalars().all()

        for task in tasks:
            # Check if task has implementation (via links)
            link_stmt = select(GraphLink).filter(
                and_(
                    GraphLink.from_entity == "graph_tasks",
                    GraphLink.from_id == task.id,
                )
            )
            result = await self.db.execute(link_stmt)
            links = result.scalars().all()

            # If no implementation links, it's a ghost node
            if not links:
                ghost_nodes.append(
                    GhostNode(
                        id=task.id,
                        type="task",
                        title=task.title,
                        description=task.description,
                        status=task.status,
                        source=None,
                        ref=None,
                        created_at=task.created_at,
                    )
                )

        return ghost_nodes

    async def search_graph(
        self,
        project_id: int,
        query: str,
        scope: Sequence[str],
    ) -> SearchResults:
        """
        Unified search across code + specs + tasks.

        Uses PostgreSQL ILIKE for case-insensitive substring matching.
        Can be enhanced with full-text search indexes later.

        Args:
            project_id: Project scope
            query: Search string
            scope: Which entity types to search

        Returns:
            SearchResults grouped by entity type
        """
        results = SearchResults(total=0)
        search_pattern = f"%{query}%"

        # Search symbols
        if "symbols" in scope:
            symbol_stmt = (
                select(GraphSymbol)
                .join(GraphFile)
                .join(GraphRepo)
                .filter(
                    and_(
                        GraphRepo.project_id == project_id,
                        or_(
                            GraphSymbol.name.ilike(search_pattern),
                            GraphSymbol.qualified_name.ilike(search_pattern),
                            GraphSymbol.signature.ilike(search_pattern),
                        ),
                    )
                )
                .limit(50)
            )
            result = await self.db.execute(symbol_stmt)
            symbols = result.scalars().all()

            for symbol in symbols:
                results.symbols.append(
                    GraphNode(
                        id=f"symbol:{symbol.id}",
                        entity_type="symbol",
                        entity_id=symbol.id,
                        label=symbol.name,
                        metadata={
                            "kind": symbol.kind.value,
                            "qualified_name": symbol.qualified_name,
                        },
                    )
                )

        # Search files
        if "files" in scope:
            file_stmt = (
                select(GraphFile)
                .join(GraphRepo)
                .filter(
                    and_(
                        GraphRepo.project_id == project_id,
                        GraphFile.path.ilike(search_pattern),
                    )
                )
                .limit(50)
            )
            result = await self.db.execute(file_stmt)
            files = result.scalars().all()

            for file in files:
                results.files.append(
                    GraphNode(
                        id=f"file:{file.id}",
                        entity_type="file",
                        entity_id=file.id,
                        label=file.path,
                        metadata={"lang": file.lang},
                    )
                )

        # Search tasks
        if "tasks" in scope:
            task_stmt = select(GraphTask).filter(
                and_(
                    GraphTask.project_id == project_id,
                    or_(
                        GraphTask.title.ilike(search_pattern),
                        GraphTask.description.ilike(search_pattern),
                    ),
                )
            )
            result = await self.db.execute(task_stmt)
            tasks = result.scalars().all()

            for task in tasks:
                results.tasks.append(
                    GraphNode(
                        id=f"task:{task.id}",
                        entity_type="task",
                        entity_id=task.id,
                        label=task.title,
                        metadata={"kind": task.kind.value, "status": task.status.value},
                    )
                )

        results.total = len(results.symbols) + len(results.files) + len(results.tasks)

        # Search personas (Sprint 3 Task 7)
        if "personas" in scope:
            from app.models.agent_persona import AgentPersona
            
            persona_stmt = select(AgentPersona).filter(
                or_(
                    AgentPersona.name.ilike(search_pattern),
                    AgentPersona.display_name.ilike(search_pattern),
                    AgentPersona.description.ilike(search_pattern),
                )
            ).limit(50)
            result = await self.db.execute(persona_stmt)
            personas = result.scalars().all()

            for persona in personas:
                results.symbols.append(  # Reuse symbols list or add personas list to SearchResults
                    GraphNode(
                        id=f"persona:{persona.id}",
                        entity_type="persona",
                        entity_id=persona.id,
                        label=persona.display_name,
                        metadata={
                            "name": persona.name,
                            "category": persona.category,
                            "model": persona.model,
                        },
                    )
                )

        # Search executions (Sprint 3 Task 7)
        if "executions" in scope:
            execution_stmt = select(AgentExecution).filter(
                or_(
                    AgentExecution.persona_name.ilike(search_pattern),
                    AgentExecution.execution_id.ilike(search_pattern),
                )
            ).limit(50)
            result = await self.db.execute(execution_stmt)
            executions = result.scalars().all()

            for execution in executions:
                results.symbols.append(  # Reuse symbols list or add executions list to SearchResults
                    GraphNode(
                        id=f"execution:{execution.id}",
                        entity_type="execution",
                        entity_id=execution.id,
                        label=f"{execution.persona_name} - {execution.execution_id[:8]}",
                        metadata={
                            "status": execution.status,
                            "execution_id": execution.execution_id,
                            "persona_name": execution.persona_name,
                            "created_at": execution.created_at.isoformat(),
                        },
                    )
                )

        return results

    # ========================================================================
    # Federation Operations
    # ========================================================================

    async def query_cross_project_links(
        self,
        request: FederationQueryRequest,
        user_project_ids: List[int],
    ) -> FederationQueryResponse:
        """
        Query cross-project links for federation.

        Returns links where source_project_id != target_project_id,
        filtered by scope and user's accessible projects.

        Args:
            request: Federation query request with scope and filters
            user_project_ids: Project IDs the user has access to (for authorization)

        Returns:
            FederationQueryResponse with matching cross-project links
        """
        from sqlalchemy import func

        # Build base query for cross-project links
        # Cross-project = both project IDs set AND they're different
        base_conditions = [
            GraphLink.source_project_id.isnot(None),
            GraphLink.target_project_id.isnot(None),
            GraphLink.source_project_id != GraphLink.target_project_id,
        ]

        # Apply scope filter
        if request.scope.type == "projects":
            # Specific projects requested - intersect with user's access
            if not request.scope.project_ids:
                return FederationQueryResponse(
                    links=[],
                    total=0,
                    metadata={"error": "project_ids required when scope.type='projects'"},
                )

            allowed_ids = set(request.scope.project_ids) & set(user_project_ids)
            if not allowed_ids:
                return FederationQueryResponse(
                    links=[],
                    total=0,
                    metadata={"error": "No accessible projects in scope"},
                )

            # Links where both source AND target are in allowed projects
            base_conditions.append(GraphLink.source_project_id.in_(allowed_ids))
            base_conditions.append(GraphLink.target_project_id.in_(allowed_ids))
        else:
            # Ecosystem scope - use all user's accessible projects
            base_conditions.append(GraphLink.source_project_id.in_(user_project_ids))
            base_conditions.append(GraphLink.target_project_id.in_(user_project_ids))

        # Apply link type filter
        if request.link_types:
            base_conditions.append(GraphLink.type.in_(request.link_types))

        # Apply entity type filter
        if request.entity_types:
            base_conditions.append(
                or_(
                    GraphLink.from_entity.in_(request.entity_types),
                    GraphLink.to_entity.in_(request.entity_types),
                )
            )

        # Get total count
        count_stmt = select(func.count(GraphLink.id)).filter(and_(*base_conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Get paginated results
        query_stmt = (
            select(GraphLink)
            .filter(and_(*base_conditions))
            .order_by(GraphLink.created_at.desc())
            .offset(request.offset)
            .limit(request.limit)
        )
        result = await self.db.execute(query_stmt)
        links = result.scalars().all()

        # Build response
        link_responses = []
        project_ids_involved = set()

        for link in links:
            project_ids_involved.add(link.source_project_id)
            project_ids_involved.add(link.target_project_id)

            link_responses.append(
                CrossProjectLinkResponse(
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
            )

        return FederationQueryResponse(
            links=link_responses,
            total=total,
            metadata={
                "projects_involved": list(project_ids_involved),
                "scope_type": request.scope.type,
                "filters_applied": {
                    "link_types": [lt.value for lt in request.link_types]
                    if request.link_types
                    else None,
                    "entity_types": request.entity_types,
                },
            },
        )

    async def create_cross_project_link(
        self,
        source_project_id: int,
        target_project_id: int,
        from_entity: str,
        from_id: int,
        to_entity: str,
        to_id: int,
        link_type: LinkType,
        weight: float = 1.0,
        metadata: Optional[dict] = None,
    ) -> GraphLink:
        """
        Create a cross-project link between entities in different projects.

        Args:
            source_project_id: Project ID of the source entity
            target_project_id: Project ID of the target entity
            from_entity: Source table name
            from_id: Source entity ID
            to_entity: Target table name
            to_id: Target entity ID
            link_type: Link type
            weight: Link weight/strength
            metadata: Optional metadata

        Returns:
            Created GraphLink instance
        """
        link = GraphLink(
            source_project_id=source_project_id,
            target_project_id=target_project_id,
            from_entity=from_entity,
            from_id=from_id,
            to_entity=to_entity,
            to_id=to_id,
            type=link_type,
            weight=weight,
            metadata_=metadata,
        )

        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)

        logger.info(
            f"Created cross-project link: {from_entity}:{from_id} -> {to_entity}:{to_id} "
            f"(projects {source_project_id} -> {target_project_id})"
        )

        return link

    # ========================================================================
    # Mutation Operations
    # ========================================================================

    async def create_task(
        self,
        project_id: int,
        title: str,
        kind: TaskKind,
        spec_item_id: Optional[int] = None,
        description: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> GraphTask:
        """
        Create work item, optionally linked to spec.

        Args:
            project_id: Project ID for multi-tenant isolation
            title: Task title
            kind: Task type (feature, bug, etc.)
            spec_item_id: Optional link to spec item
            description: Optional task description
            labels: Optional labels

        Returns:
            Created GraphTask instance
        """
        task = GraphTask(
            project_id=project_id,
            title=title,
            kind=kind,
            spec_item_id=spec_item_id,
            description=description,
            labels=labels,
            status=SpecItemStatus.PLANNED,
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        # Publish task creation event
        nats_client = await get_nats_client()
        if nats_client:
            try:
                event = GraphTaskCreatedEvent(
                    task_id=task.id,
                    project_id=project_id,
                    title=title,
                    kind=kind.value,
                    spec_item_id=spec_item_id,
                )
                await nats_client.publish("graph.task.created", event.model_dump(mode="json"))
                logger.debug(f"Published task created event: task_id={task.id}")
            except Exception as e:
                logger.error(f"Failed to publish task created event: {e}")

        return task

    async def trigger_audit(
        self,
        target_entity: str,
        target_id: int,
        kind: AuditKind,
        project_id: int,
    ) -> GraphAudit:
        """
        Trigger an audit for a target entity.

        Creates audit record and publishes NATS event for async processing.

        Args:
            target_entity: Target table name
            target_id: Target entity ID
            kind: Audit type
            project_id: Project ID for multi-tenant isolation

        Returns:
            Created GraphAudit instance (status=PENDING)
        """
        audit = GraphAudit(
            target_entity=target_entity,
            target_id=target_id,
            kind=kind,
            status=AuditStatus.PENDING,
        )

        self.db.add(audit)
        await self.db.commit()
        await self.db.refresh(audit)

        # Publish NATS event for async audit processing
        nats_client = await get_nats_client()
        if nats_client:
            try:
                correlation_id = uuid4()
                event = AuditRequestedEvent(
                    audit_id=audit.id,
                    project_id=project_id,
                    target_entity=target_entity,
                    target_id=target_id,
                    kind=kind,
                    correlation_id=correlation_id,
                )

                subject = f"audit.requested.{kind.value}"
                # Use model_dump with mode='json' to handle UUID serialization
                event_dict = event.model_dump(mode="json")
                await nats_client.publish(subject, event_dict, correlation_id)
                logger.info(
                    f"Published audit request: {subject} (audit_id={audit.id}, "
                    f"correlation={correlation_id})"
                )
            except Exception as e:
                logger.error(f"Failed to publish audit request to NATS: {e}")
                # Don't fail the audit creation if NATS publish fails
        else:
            logger.warning("NATS client not available, audit request not published")

        return audit

    async def link_entities(
        self,
        from_entity: str,
        from_id: int,
        to_entity: str,
        to_id: int,
        link_type: LinkType,
        weight: float = 1.0,
    ) -> GraphLink:
        """
        Create a typed link between two entities.

        Args:
            from_entity: Source table name
            from_id: Source entity ID
            to_entity: Target table name
            to_id: Target entity ID
            link_type: Link type
            weight: Link weight/strength

        Returns:
            Created GraphLink instance
        """
        link = GraphLink(
            from_entity=from_entity,
            from_id=from_id,
            to_entity=to_entity,
            to_id=to_id,
            type=link_type,
            weight=weight,
        )

        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)

        return link

    async def update_audit_result(
        self,
        audit_id: int,
        status: AuditStatus,
        summary: str,
        report_path: Optional[str] = None,
        score: Optional[float] = None,
    ) -> GraphAudit:
        """
        Update audit with results from agent.

        Called when audit.result.* event is received from audit agents.

        Args:
            audit_id: Audit ID
            status: Audit result status (completed, failed)
            summary: Human-readable summary
            report_path: Optional path to detailed report
            score: Optional quality score (0-10)

        Returns:
            Updated GraphAudit instance
        """
        stmt = select(GraphAudit).filter(GraphAudit.id == audit_id)
        result = await self.db.execute(stmt)
        audit = result.scalar_one_or_none()

        if not audit:
            raise ValueError(f"Audit {audit_id} not found")

        # Update audit record
        audit.status = status
        audit.summary = summary
        audit.report_path = report_path
        audit.score = score

        await self.db.commit()
        await self.db.refresh(audit)

        logger.info(f"Updated audit {audit_id} with status={status}, score={score}")
        return audit

    async def start_audit_result_consumer(self) -> None:
    # ========================================================================
    # Agent Execution Operations (Sprint 3 Task 6)
    # ========================================================================

    async def create_agent_execution(
        self,
        persona_name: str,
        execution_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> AgentExecution:
        """
        Create a new agent execution record and emit NATS event.

        Args:
            persona_name: Name of the agent persona being executed
            execution_id: Optional execution ID (auto-generated if not provided)
            metadata: Optional metadata dict

        Returns:
            Created AgentExecution instance
        """
        from datetime import datetime

        execution = AgentExecution(
            persona_name=persona_name,
            status="pending",
            metadata_=metadata,
        )

        if execution_id:
            execution.execution_id = execution_id

        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)

        # Publish NATS event for agent execution created
        nats_client = await get_nats_client()
        if nats_client:
            try:
                event_data = {
                    "execution_id": execution.execution_id,
                    "persona_name": persona_name,
                    "status": "pending",
                    "created_at": execution.created_at.isoformat(),
                }
                await nats_client.publish("agent.execution.created", event_data)
                logger.info(
                    f"Published agent execution created event: execution_id={execution.execution_id}"
                )
            except Exception as e:
                logger.error(f"Failed to publish agent execution created event: {e}")

        return execution

    async def update_agent_execution(
        self,
        execution_id: str,
        status: Optional[str] = None,
        files_changed: Optional[list] = None,
        pr_url: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        cost_usd: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> AgentExecution:
        """
        Update agent execution status and emit NATS event.

        Args:
            execution_id: Execution ID to update
            status: New status (pending, running, completed, failed, cancelled)
            files_changed: List of files changed during execution
            pr_url: Pull request URL if created
            duration_seconds: Execution duration in seconds
            cost_usd: Execution cost in USD
            error_message: Error message if failed

        Returns:
            Updated AgentExecution instance
        """
        from datetime import datetime

        stmt = select(AgentExecution).filter(AgentExecution.execution_id == execution_id)
        result = await self.db.execute(stmt)
        execution = result.scalar_one_or_none()

        if not execution:
            raise ValueError(f"Agent execution {execution_id} not found")

        # Update fields
        if status:
            execution.status = status
            if status == "running" and not execution.started_at:
                execution.started_at = datetime.utcnow()
            elif status in ["completed", "failed", "cancelled"] and not execution.completed_at:
                execution.completed_at = datetime.utcnow()

        if files_changed is not None:
            execution.files_changed = files_changed
        if pr_url is not None:
            execution.pr_url = pr_url
        if duration_seconds is not None:
            execution.duration_seconds = duration_seconds
        if cost_usd is not None:
            execution.cost_usd = cost_usd
        if error_message is not None:
            execution.error_message = error_message

        await self.db.commit()
        await self.db.refresh(execution)

        # Publish NATS event for agent execution updated
        nats_client = await get_nats_client()
        if nats_client:
            try:
                event_data = {
                    "execution_id": execution.execution_id,
                    "persona_name": execution.persona_name,
                    "status": execution.status,
                    "files_changed": execution.files_changed,
                    "pr_url": execution.pr_url,
                    "duration_seconds": execution.duration_seconds,
                    "cost_usd": execution.cost_usd,
                    "updated_at": execution.updated_at.isoformat(),
                }
                await nats_client.publish(f"agent.execution.{status}", event_data)
                logger.info(
                    f"Published agent execution event: execution_id={execution.execution_id}, status={status}"
                )
            except Exception as e:
                logger.error(f"Failed to publish agent execution event: {e}")

        return execution

        """
        Start consuming audit.result.* events from NATS.

        Should be called on application startup to begin listening for
        audit results from agents.
        """
        nats_client = await get_nats_client()
        if not nats_client:
            logger.warning("NATS client not available, audit result consumer not started")
            return

        async def handle_audit_result(subject: str, data: dict):
            """Handle audit.result.* events"""
            try:
                event = AuditResultEvent(**data)
                await self.update_audit_result(
                    audit_id=event.audit_id,
                    status=event.status,
                    summary=event.summary,
                    report_path=event.report_path,
                    score=event.score,
                )
                logger.info(
                    f"Processed audit result: audit_id={event.audit_id}, status={event.status}"
                )
            except Exception as e:
                logger.error(f"Error processing audit result event from {subject}: {e}")

        await nats_client.subscribe("audit.result.*", handle_audit_result)
        logger.info("Started audit result consumer (subscribed to audit.result.*)")
