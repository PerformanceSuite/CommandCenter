"""
GraphService - Business logic for Phase 7 Graph Service

Encapsulates all graph database operations with multi-tenant isolation.
"""

import logging
from typing import List, Literal, Optional, Sequence
from uuid import uuid4

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_execution import AgentExecution
from app.models.graph import (
    AuditKind,
    AuditStatus,
    ConceptStatus,
    ConfidenceLevel,
    CrossProjectLink,
    DocumentStatus,
    DocumentType,
    GraphAudit,
    GraphConcept,
    GraphDependency,
    GraphDocument,
    GraphFile,
    GraphLink,
    GraphRepo,
    GraphRequirement,
)
from app.models.graph import GraphService as GraphServiceModel
from app.models.graph import (
    GraphSpecItem,
    GraphSymbol,
    GraphTask,
    LinkType,
    RequirementStatus,
    SpecItemStatus,
    TaskKind,
)
from app.nats_client import get_nats_client
from app.schemas.graph import (
    ApprovalResponse,
    ApproveConceptsRequest,
    ApproveRequirementsRequest,
    ConceptReviewItem,
    CreateConceptRequest,
    CreateDocumentRequest,
    CreateRequirementRequest,
    CreateSimpleConceptRequest,
    CreateSimpleRequirementRequest,
    CrossProjectLinkResponse,
    DependencyGraph,
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentWithEntitiesResponse,
    FederationQueryRequest,
    FederationQueryResponse,
    GhostNode,
    GraphEdge,
    GraphFilters,
    GraphNode,
    IngestDocumentIntelligenceRequest,
    IngestDocumentIntelligenceResponse,
    ProjectGraphResponse,
    RejectionResponse,
    RequirementReviewItem,
    ReviewQueueConceptsResponse,
    ReviewQueueRequirementsResponse,
    SearchResults,
    SpecFilters,
    UpdateConceptRequest,
    UpdateDocumentRequest,
    UpdateRequirementRequest,
)
from app.schemas.graph_events import (
    AuditRequestedEvent,
    AuditResultEvent,
    GraphEdgeEvent,
    GraphInvalidatedEvent,
    GraphNodeEvent,
    GraphTaskCreatedEvent,
)

logger = logging.getLogger(__name__)


class GraphService:
    """Graph service for querying and mutating the knowledge graph"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # Event Publishing Helpers (Sprint 4)
    # ========================================================================

    async def _publish_node_event(
        self,
        event_type: str,
        project_id: int,
        node_type: str,
        node_id: int,
        label: Optional[str] = None,
        changes: Optional[dict] = None,
    ) -> None:
        """Publish a graph node event to NATS.

        Args:
            event_type: 'created', 'updated', or 'deleted'
            project_id: Project ID for filtering
            node_type: Entity type (task, spec, service, etc.)
            node_id: Entity database ID
            label: Optional display label
            changes: Optional dict of changed fields (for updates)
        """
        nats_client = await get_nats_client()
        if not nats_client:
            return

        try:
            event = GraphNodeEvent(
                event_type=event_type,
                project_id=project_id,
                node_type=node_type,
                node_id=f"{node_type}:{node_id}",
                label=label,
                changes=changes,
            )
            subject = f"graph.node.{event_type}"
            await nats_client.publish(subject, event.model_dump(mode="json"))
            logger.debug(f"Published {subject}: {node_type}:{node_id}")
        except Exception as e:
            logger.error(f"Failed to publish node event: {e}")

    async def _publish_edge_event(
        self,
        event_type: str,
        project_id: int,
        from_entity: str,
        from_id: int,
        to_entity: str,
        to_id: int,
        edge_type: str,
        weight: Optional[float] = None,
    ) -> None:
        """Publish a graph edge event to NATS.

        Args:
            event_type: 'created' or 'deleted'
            project_id: Project ID for filtering
            from_entity: Source entity type
            from_id: Source entity ID
            to_entity: Target entity type
            to_id: Target entity ID
            edge_type: Link type (contains, imports, implements, etc.)
            weight: Optional edge weight
        """
        nats_client = await get_nats_client()
        if not nats_client:
            return

        try:
            # Normalize entity names (remove 'graph_' prefix if present)
            from_type = from_entity.replace("graph_", "").rstrip("s")
            to_type = to_entity.replace("graph_", "").rstrip("s")

            event = GraphEdgeEvent(
                event_type=event_type,
                project_id=project_id,
                from_node=f"{from_type}:{from_id}",
                to_node=f"{to_type}:{to_id}",
                edge_type=edge_type,
                weight=weight,
            )
            subject = f"graph.edge.{event_type}"
            await nats_client.publish(subject, event.model_dump(mode="json"))
            logger.debug(f"Published {subject}: {from_type}:{from_id} -> {to_type}:{to_id}")
        except Exception as e:
            logger.error(f"Failed to publish edge event: {e}")

    async def _publish_invalidated_event(
        self,
        project_id: int,
        reason: str,
        affected_types: Optional[List[str]] = None,
    ) -> None:
        """Publish a graph invalidation event to NATS.

        Args:
            project_id: Project ID for filtering
            reason: Reason for invalidation
            affected_types: Optional list of affected entity types
        """
        nats_client = await get_nats_client()
        if not nats_client:
            return

        try:
            event = GraphInvalidatedEvent(
                project_id=project_id,
                reason=reason,
                affected_types=affected_types,
            )
            await nats_client.publish("graph.invalidated", event.model_dump(mode="json"))
            logger.info(f"Published graph.invalidated for project {project_id}: {reason}")
        except Exception as e:
            logger.error(f"Failed to publish invalidation event: {e}")

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

            persona_stmt = (
                select(AgentPersona)
                .filter(
                    or_(
                        AgentPersona.name.ilike(search_pattern),
                        AgentPersona.display_name.ilike(search_pattern),
                        AgentPersona.description.ilike(search_pattern),
                    )
                )
                .limit(50)
            )
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
            execution_stmt = (
                select(AgentExecution)
                .filter(
                    or_(
                        AgentExecution.persona_name.ilike(search_pattern),
                        AgentExecution.execution_id.ilike(search_pattern),
                    )
                )
                .limit(50)
            )
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
                    "link_types": (
                        [lt.value for lt in request.link_types] if request.link_types else None
                    ),
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

        # Sprint 4: Publish edge events to both projects for real-time UI updates
        await self._publish_edge_event(
            event_type="created",
            project_id=source_project_id,
            from_entity=from_entity,
            from_id=from_id,
            to_entity=to_entity,
            to_id=to_id,
            edge_type=link_type.value,
            weight=weight,
        )
        # Also notify target project
        if target_project_id != source_project_id:
            await self._publish_edge_event(
                event_type="created",
                project_id=target_project_id,
                from_entity=from_entity,
                from_id=from_id,
                to_entity=to_entity,
                to_id=to_id,
                edge_type=link_type.value,
                weight=weight,
            )

        return link

    async def query_ecosystem_links(
        self,
        entity_types: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None,
        source_project_ids: Optional[List[int]] = None,
        target_project_ids: Optional[List[int]] = None,
        limit: int = 1000,
    ) -> List[CrossProjectLink]:
        """Query cross-project links across the ecosystem.

        This method queries the CrossProjectLink table for ecosystem-wide
        federation queries, enabling discovery of relationships between
        projects such as shared dependencies, API consumers, and service
        integrations.

        Args:
            entity_types: Filter by source or target entity type
                (e.g., ["symbol", "service", "file"])
            relationship_types: Filter by relationship type
                (e.g., ["calls", "imports", "depends_on"])
            source_project_ids: Filter by source project IDs
            target_project_ids: Filter by target project IDs
            limit: Maximum number of results (default: 1000)

        Returns:
            List of CrossProjectLink objects matching the filters

        Example:
            # Find all symbol-to-symbol calls/imports across projects
            links = await graph_service.query_ecosystem_links(
                entity_types=["symbol"],
                relationship_types=["calls", "imports"]
            )

            # Find all outgoing links from project 1
            links = await graph_service.query_ecosystem_links(
                source_project_ids=[1]
            )
        """
        query = select(CrossProjectLink)

        # Filter by entity types (match source OR target)
        if entity_types:
            query = query.filter(
                or_(
                    CrossProjectLink.source_entity_type.in_(entity_types),
                    CrossProjectLink.target_entity_type.in_(entity_types),
                )
            )

        # Filter by relationship types
        if relationship_types:
            query = query.filter(CrossProjectLink.relationship_type.in_(relationship_types))

        # Filter by source project IDs
        if source_project_ids:
            query = query.filter(CrossProjectLink.source_project_id.in_(source_project_ids))

        # Filter by target project IDs
        if target_project_ids:
            query = query.filter(CrossProjectLink.target_project_id.in_(target_project_ids))

        # Apply limit
        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

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

        # Publish task creation events (legacy + Sprint 4 format)
        nats_client = await get_nats_client()
        if nats_client:
            try:
                # Legacy event format
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

        # Sprint 4: Publish node event for real-time UI updates
        await self._publish_node_event(
            event_type="created",
            project_id=project_id,
            node_type="task",
            node_id=task.id,
            label=title,
        )

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
        project_id: Optional[int] = None,
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
            project_id: Optional project ID for event filtering

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

        # Sprint 4: Publish edge event for real-time UI updates
        if project_id is not None:
            await self._publish_edge_event(
                event_type="created",
                project_id=project_id,
                from_entity=from_entity,
                from_id=from_id,
                to_entity=to_entity,
                to_id=to_id,
                edge_type=link_type.value,
                weight=weight,
            )

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

    async def start_audit_result_consumer(self) -> None:
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

    # ========================================================================
    # Document Intelligence Operations (Sprint 6)
    # ========================================================================

    async def ingest_document_intelligence(
        self,
        project_id: int,
        request: IngestDocumentIntelligenceRequest,
    ) -> IngestDocumentIntelligenceResponse:
        """
        Ingest Document Intelligence pipeline output into the graph.

        Processes documents, concepts, and requirements from Document Intelligence
        personas (doc-classifier, doc-concept-extractor, doc-requirement-miner).

        Documents are upserted first (by path), establishing IDs that concepts
        and requirements can reference. Concepts and requirements are then
        upserted (by name/req_id) and linked to their source documents.

        Args:
            project_id: Project ID for multi-tenant isolation
            request: Combined output from Document Intelligence pipeline

        Returns:
            IngestDocumentIntelligenceResponse with counts and any errors
        """
        import time

        start_time = time.time()
        response = IngestDocumentIntelligenceResponse()
        path_to_doc_id: dict[str, int] = {}

        # Phase 1: Upsert documents (by path)
        for doc_req in request.documents:
            try:
                doc, created = await self._upsert_document(project_id, doc_req)
                path_to_doc_id[doc.path] = doc.id

                if created:
                    response.documents_created += 1
                    await self._publish_node_event(
                        event_type="created",
                        project_id=project_id,
                        node_type="document",
                        node_id=doc.id,
                        label=doc.title or doc.path,
                    )
                else:
                    response.documents_updated += 1
                    await self._publish_node_event(
                        event_type="updated",
                        project_id=project_id,
                        node_type="document",
                        node_id=doc.id,
                        label=doc.title or doc.path,
                    )
            except Exception as e:
                response.errors.append(f"Document '{doc_req.path}': {str(e)}")
                logger.error(f"Error upserting document {doc_req.path}: {e}")

        # Phase 2: Upsert concepts (by name) and link to source documents
        for concept_req in request.concepts:
            try:
                concept, created = await self._upsert_concept(project_id, concept_req)

                if created:
                    response.concepts_created += 1
                    await self._publish_node_event(
                        event_type="created",
                        project_id=project_id,
                        node_type="concept",
                        node_id=concept.id,
                        label=concept.name,
                    )
                else:
                    response.concepts_updated += 1
                    await self._publish_node_event(
                        event_type="updated",
                        project_id=project_id,
                        node_type="concept",
                        node_id=concept.id,
                        label=concept.name,
                    )

                # Create link from source document if we have it
                if concept.source_document_id:
                    link = await self._ensure_link(
                        from_entity="graph_documents",
                        from_id=concept.source_document_id,
                        to_entity="graph_concepts",
                        to_id=concept.id,
                        link_type=LinkType.EXTRACTS_FROM,
                        project_id=project_id,
                    )
                    if link:
                        response.links_created += 1
            except Exception as e:
                response.errors.append(f"Concept '{concept_req.name}': {str(e)}")
                logger.error(f"Error upserting concept {concept_req.name}: {e}")

        # Phase 3: Upsert requirements (by req_id) and link to source documents
        for req_req in request.requirements:
            try:
                requirement, created = await self._upsert_requirement(project_id, req_req)

                if created:
                    response.requirements_created += 1
                    await self._publish_node_event(
                        event_type="created",
                        project_id=project_id,
                        node_type="requirement",
                        node_id=requirement.id,
                        label=requirement.req_id,
                    )
                else:
                    response.requirements_updated += 1
                    await self._publish_node_event(
                        event_type="updated",
                        project_id=project_id,
                        node_type="requirement",
                        node_id=requirement.id,
                        label=requirement.req_id,
                    )

                # Create link from source document if we have it
                if requirement.source_document_id:
                    link = await self._ensure_link(
                        from_entity="graph_documents",
                        from_id=requirement.source_document_id,
                        to_entity="graph_requirements",
                        to_id=requirement.id,
                        link_type=LinkType.EXTRACTS_FROM,
                        project_id=project_id,
                    )
                    if link:
                        response.links_created += 1
            except Exception as e:
                response.errors.append(f"Requirement '{req_req.req_id}': {str(e)}")
                logger.error(f"Error upserting requirement {req_req.req_id}: {e}")

        # Finalize
        elapsed_ms = (time.time() - start_time) * 1000
        response.metadata = {
            "processing_time_ms": round(elapsed_ms, 2),
            "documents_processed": len(request.documents),
            "concepts_processed": len(request.concepts),
            "requirements_processed": len(request.requirements),
        }

        logger.info(
            f"Document Intelligence ingestion complete for project {project_id}: "
            f"docs={response.documents_created}/{response.documents_updated}, "
            f"concepts={response.concepts_created}/{response.concepts_updated}, "
            f"reqs={response.requirements_created}/{response.requirements_updated}, "
            f"links={response.links_created}, errors={len(response.errors)}"
        )

        return response

    async def _upsert_document(
        self,
        project_id: int,
        req: CreateDocumentRequest,
    ) -> tuple[GraphDocument, bool]:
        """
        Upsert a document by path within a project.

        Returns:
            Tuple of (document, created) where created is True if new
        """
        # Try to find existing document by path
        stmt = select(GraphDocument).filter(
            and_(
                GraphDocument.project_id == project_id,
                GraphDocument.path == req.path,
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing document
            existing.title = req.title
            existing.doc_type = req.doc_type
            existing.subtype = req.subtype
            existing.status = req.status
            existing.audience = req.audience
            existing.value_assessment = req.value_assessment
            existing.word_count = req.word_count
            existing.content_hash = req.content_hash
            existing.staleness_score = req.staleness_score
            existing.last_meaningful_date = req.last_meaningful_date
            existing.recommended_action = req.recommended_action
            existing.target_location = req.target_location
            existing.metadata_ = req.metadata
            from datetime import datetime

            existing.last_analyzed_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing, False
        else:
            # Create new document
            doc = GraphDocument(
                project_id=project_id,
                path=req.path,
                title=req.title,
                doc_type=req.doc_type,
                subtype=req.subtype,
                status=req.status,
                audience=req.audience,
                value_assessment=req.value_assessment,
                word_count=req.word_count,
                content_hash=req.content_hash,
                staleness_score=req.staleness_score,
                last_meaningful_date=req.last_meaningful_date,
                recommended_action=req.recommended_action,
                target_location=req.target_location,
                metadata_=req.metadata,
            )
            self.db.add(doc)
            await self.db.commit()
            await self.db.refresh(doc)
            return doc, True

    async def _upsert_concept(
        self,
        project_id: int,
        req: CreateConceptRequest,
    ) -> tuple[GraphConcept, bool]:
        """
        Upsert a concept by name within a project.

        Returns:
            Tuple of (concept, created) where created is True if new
        """
        # Try to find existing concept by name
        stmt = select(GraphConcept).filter(
            and_(
                GraphConcept.project_id == project_id,
                GraphConcept.name == req.name,
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing concept
            existing.concept_type = req.concept_type
            existing.source_document_id = req.source_document_id
            existing.definition = req.definition
            existing.status = req.status
            existing.domain = req.domain
            existing.source_quote = req.source_quote
            existing.confidence = req.confidence
            existing.related_entities = req.related_entities
            existing.metadata_ = req.metadata
            await self.db.commit()
            await self.db.refresh(existing)
            return existing, False
        else:
            # Create new concept
            concept = GraphConcept(
                project_id=project_id,
                name=req.name,
                concept_type=req.concept_type,
                source_document_id=req.source_document_id,
                definition=req.definition,
                status=req.status,
                domain=req.domain,
                source_quote=req.source_quote,
                confidence=req.confidence,
                related_entities=req.related_entities,
                metadata_=req.metadata,
            )
            self.db.add(concept)
            await self.db.commit()
            await self.db.refresh(concept)
            return concept, True

    async def _upsert_requirement(
        self,
        project_id: int,
        req: CreateRequirementRequest,
    ) -> tuple[GraphRequirement, bool]:
        """
        Upsert a requirement by req_id within a project.

        Returns:
            Tuple of (requirement, created) where created is True if new
        """
        # Try to find existing requirement by req_id
        stmt = select(GraphRequirement).filter(
            and_(
                GraphRequirement.project_id == project_id,
                GraphRequirement.req_id == req.req_id,
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing requirement
            existing.text = req.text
            existing.req_type = req.req_type
            existing.source_document_id = req.source_document_id
            existing.priority = req.priority
            existing.status = req.status
            existing.source_concept = req.source_concept
            existing.source_quote = req.source_quote
            existing.verification = req.verification
            existing.metadata_ = req.metadata
            await self.db.commit()
            await self.db.refresh(existing)
            return existing, False
        else:
            # Create new requirement
            requirement = GraphRequirement(
                project_id=project_id,
                req_id=req.req_id,
                text=req.text,
                req_type=req.req_type,
                source_document_id=req.source_document_id,
                priority=req.priority,
                status=req.status,
                source_concept=req.source_concept,
                source_quote=req.source_quote,
                verification=req.verification,
                metadata_=req.metadata,
            )
            self.db.add(requirement)
            await self.db.commit()
            await self.db.refresh(requirement)
            return requirement, True

    async def _ensure_link(
        self,
        from_entity: str,
        from_id: int,
        to_entity: str,
        to_id: int,
        link_type: LinkType,
        project_id: int,
        weight: float = 1.0,
    ) -> Optional[GraphLink]:
        """
        Create a link if it doesn't already exist.

        Returns:
            Created GraphLink or None if it already exists
        """
        # Check for existing link
        stmt = select(GraphLink).filter(
            and_(
                GraphLink.from_entity == from_entity,
                GraphLink.from_id == from_id,
                GraphLink.to_entity == to_entity,
                GraphLink.to_id == to_id,
                GraphLink.type == link_type,
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return None  # Link already exists

        # Create new link
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

        # Publish edge event
        await self._publish_edge_event(
            event_type="created",
            project_id=project_id,
            from_entity=from_entity,
            from_id=from_id,
            to_entity=to_entity,
            to_id=to_id,
            edge_type=link_type.value,
            weight=weight,
        )

        return link

    # ========================================================================
    # Review Queue & Approval Workflow
    # ========================================================================

    async def list_concepts_for_review(
        self,
        project_id: int,
        statuses: Optional[List[ConceptStatus]] = None,
        limit: int = 50,
    ) -> ReviewQueueConceptsResponse:
        """
        List concepts pending review with source document paths.

        Args:
            project_id: Project ID for multi-tenant isolation
            statuses: Statuses to filter (default: [UNKNOWN])
            limit: Maximum items to return

        Returns:
            ReviewQueueConceptsResponse with items, total count, and has_more flag
        """
        if statuses is None:
            statuses = [ConceptStatus.UNKNOWN]

        # Build query with optional join to get document path
        stmt = (
            select(GraphConcept, GraphDocument.path)
            .outerjoin(
                GraphDocument,
                GraphConcept.source_document_id == GraphDocument.id,
            )
            .filter(
                and_(
                    GraphConcept.project_id == project_id,
                    GraphConcept.status.in_(statuses),
                )
            )
            .order_by(GraphConcept.created_at.desc())
            .limit(limit + 1)  # Fetch one extra to check has_more
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        # Count total pending
        count_stmt = select(GraphConcept).filter(
            and_(
                GraphConcept.project_id == project_id,
                GraphConcept.status.in_(statuses),
            )
        )
        count_result = await self.db.execute(count_stmt)
        total_pending = len(count_result.all())

        # Build response items
        items = []
        for i, (concept, doc_path) in enumerate(rows):
            if i >= limit:
                break
            items.append(
                ConceptReviewItem(
                    id=concept.id,
                    project_id=concept.project_id,
                    source_document_id=concept.source_document_id,
                    source_document_path=doc_path,
                    name=concept.name,
                    concept_type=concept.concept_type,
                    definition=concept.definition,
                    status=concept.status,
                    domain=concept.domain,
                    source_quote=concept.source_quote,
                    confidence=concept.confidence,
                    related_entities=concept.related_entities,
                    created_at=concept.created_at,
                )
            )

        return ReviewQueueConceptsResponse(
            items=items,
            total_pending=total_pending,
            has_more=len(rows) > limit,
        )

    async def list_requirements_for_review(
        self,
        project_id: int,
        statuses: Optional[List[RequirementStatus]] = None,
        limit: int = 50,
    ) -> ReviewQueueRequirementsResponse:
        """
        List requirements pending review with source document paths.

        Args:
            project_id: Project ID for multi-tenant isolation
            statuses: Statuses to filter (default: [PROPOSED])
            limit: Maximum items to return

        Returns:
            ReviewQueueRequirementsResponse with items, total count, and has_more flag
        """
        if statuses is None:
            statuses = [RequirementStatus.PROPOSED]

        # Build query with optional join to get document path
        stmt = (
            select(GraphRequirement, GraphDocument.path)
            .outerjoin(
                GraphDocument,
                GraphRequirement.source_document_id == GraphDocument.id,
            )
            .filter(
                and_(
                    GraphRequirement.project_id == project_id,
                    GraphRequirement.status.in_(statuses),
                )
            )
            .order_by(GraphRequirement.created_at.desc())
            .limit(limit + 1)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        # Count total pending
        count_stmt = select(GraphRequirement).filter(
            and_(
                GraphRequirement.project_id == project_id,
                GraphRequirement.status.in_(statuses),
            )
        )
        count_result = await self.db.execute(count_stmt)
        total_pending = len(count_result.all())

        # Build response items
        items = []
        for i, (requirement, doc_path) in enumerate(rows):
            if i >= limit:
                break
            items.append(
                RequirementReviewItem(
                    id=requirement.id,
                    project_id=requirement.project_id,
                    source_document_id=requirement.source_document_id,
                    source_document_path=doc_path,
                    req_id=requirement.req_id,
                    text=requirement.text,
                    req_type=requirement.req_type,
                    priority=requirement.priority,
                    status=requirement.status,
                    source_concept=requirement.source_concept,
                    source_quote=requirement.source_quote,
                    created_at=requirement.created_at,
                )
            )

        return ReviewQueueRequirementsResponse(
            items=items,
            total_pending=total_pending,
            has_more=len(rows) > limit,
        )

    async def approve_concepts(
        self,
        project_id: int,
        request: ApproveConceptsRequest,
    ) -> ApprovalResponse:
        """
        Approve concepts by updating their status and optionally indexing to KB.

        Args:
            project_id: Project ID for multi-tenant isolation
            request: Approval request with IDs, status, and index_to_kb flag

        Returns:
            ApprovalResponse with counts
        """
        # Fetch concepts to approve (filtered by project for security)
        stmt = select(GraphConcept).filter(
            and_(
                GraphConcept.project_id == project_id,
                GraphConcept.id.in_(request.ids),
            )
        )
        result = await self.db.execute(stmt)
        concepts = list(result.scalars().all())

        if not concepts:
            return ApprovalResponse(approved=0, indexed_to_kb=0)

        # Update status
        for concept in concepts:
            concept.status = request.status
        await self.db.commit()

        # Index to KnowledgeBeast if requested
        indexed_count = 0
        if request.index_to_kb:
            indexed_count = await self._index_concepts_to_kb(project_id, concepts)

        logger.info(
            f"Approved {len(concepts)} concepts (project={project_id}, "
            f"status={request.status.value}, indexed={indexed_count})"
        )

        return ApprovalResponse(approved=len(concepts), indexed_to_kb=indexed_count)

    async def approve_requirements(
        self,
        project_id: int,
        request: ApproveRequirementsRequest,
    ) -> ApprovalResponse:
        """
        Approve requirements by updating their status and optionally indexing to KB.

        Args:
            project_id: Project ID for multi-tenant isolation
            request: Approval request with IDs, status, and index_to_kb flag

        Returns:
            ApprovalResponse with counts
        """
        # Fetch requirements to approve (filtered by project for security)
        stmt = select(GraphRequirement).filter(
            and_(
                GraphRequirement.project_id == project_id,
                GraphRequirement.id.in_(request.ids),
            )
        )
        result = await self.db.execute(stmt)
        requirements = list(result.scalars().all())

        if not requirements:
            return ApprovalResponse(approved=0, indexed_to_kb=0)

        # Update status
        for requirement in requirements:
            requirement.status = request.status
        await self.db.commit()

        # Index to KnowledgeBeast if requested
        indexed_count = 0
        if request.index_to_kb:
            indexed_count = await self._index_requirements_to_kb(project_id, requirements)

        logger.info(
            f"Approved {len(requirements)} requirements (project={project_id}, "
            f"status={request.status.value}, indexed={indexed_count})"
        )

        return ApprovalResponse(approved=len(requirements), indexed_to_kb=indexed_count)

    async def reject_concepts(
        self,
        project_id: int,
        ids: List[int],
    ) -> RejectionResponse:
        """
        Reject (delete) concepts from the graph.

        Args:
            project_id: Project ID for multi-tenant isolation
            ids: Concept IDs to delete

        Returns:
            RejectionResponse with count
        """
        # Delete concepts (filtered by project for security)
        stmt = select(GraphConcept).filter(
            and_(
                GraphConcept.project_id == project_id,
                GraphConcept.id.in_(ids),
            )
        )
        result = await self.db.execute(stmt)
        concepts = list(result.scalars().all())

        for concept in concepts:
            await self.db.delete(concept)
        await self.db.commit()

        logger.info(f"Rejected (deleted) {len(concepts)} concepts (project={project_id})")

        return RejectionResponse(deleted=len(concepts))

    async def reject_requirements(
        self,
        project_id: int,
        ids: List[int],
    ) -> RejectionResponse:
        """
        Reject (delete) requirements from the graph.

        Args:
            project_id: Project ID for multi-tenant isolation
            ids: Requirement IDs to delete

        Returns:
            RejectionResponse with count
        """
        # Delete requirements (filtered by project for security)
        stmt = select(GraphRequirement).filter(
            and_(
                GraphRequirement.project_id == project_id,
                GraphRequirement.id.in_(ids),
            )
        )
        result = await self.db.execute(stmt)
        requirements = list(result.scalars().all())

        for requirement in requirements:
            await self.db.delete(requirement)
        await self.db.commit()

        logger.info(f"Rejected (deleted) {len(requirements)} requirements (project={project_id})")

        return RejectionResponse(deleted=len(requirements))

    async def _index_concepts_to_kb(
        self,
        project_id: int,
        concepts: List[GraphConcept],
    ) -> int:
        """
        Index approved concepts to KnowledgeBeast.

        Uses category='document_intelligence' metadata for filtering.
        Future enhancement: Add dedicated collection for doc intel queries.

        Args:
            project_id: Project ID for collection naming
            concepts: List of concepts to index

        Returns:
            Number of concepts indexed
        """
        # Import here to avoid circular imports
        from app.services.rag_service import RAGService

        try:
            # Use project_id as repository_id for collection naming
            rag_service = RAGService(repository_id=project_id)
            await rag_service.initialize()
            indexed = 0

            for concept in concepts:
                content = f"""Concept: {concept.name}
Type: {concept.concept_type.value}
Definition: {concept.definition or 'No definition provided'}
Domain: {concept.domain or 'Unknown'}
Status: {concept.status.value}
Related Entities: {', '.join(concept.related_entities) if concept.related_entities else 'None'}
"""

                metadata = {
                    "source": f"graph_concept_{concept.id}",
                    "category": "document_intelligence",
                    "entity_type": "concept",
                    "entity_id": concept.id,
                    "concept_type": concept.concept_type.value,
                    "domain": concept.domain,
                    "project_id": project_id,
                }

                await rag_service.add_document(content=content, metadata=metadata)
                indexed += 1

            await rag_service.close()
            logger.info(f"Indexed {indexed} concepts to KnowledgeBeast (project={project_id})")
            return indexed

        except Exception as e:
            logger.error(f"Failed to index concepts to KnowledgeBeast: {e}")
            return 0

    async def _index_requirements_to_kb(
        self,
        project_id: int,
        requirements: List[GraphRequirement],
    ) -> int:
        """
        Index approved requirements to KnowledgeBeast.

        Uses category='document_intelligence' metadata for filtering.
        Future enhancement: Add dedicated collection for doc intel queries.

        Args:
            project_id: Project ID for collection naming
            requirements: List of requirements to index

        Returns:
            Number of requirements indexed
        """
        # Import here to avoid circular imports
        from app.services.rag_service import RAGService

        try:
            # Use project_id as repository_id for collection naming
            rag_service = RAGService(repository_id=project_id)
            await rag_service.initialize()
            indexed = 0

            for req in requirements:
                content = f"""Requirement: {req.req_id}
Text: {req.text}
Type: {req.req_type.value}
Priority: {req.priority.value}
Status: {req.status.value}
Source Concept: {req.source_concept or 'None'}
Verification: {req.verification or 'Not specified'}
"""

                metadata = {
                    "source": f"graph_requirement_{req.id}",
                    "category": "document_intelligence",
                    "entity_type": "requirement",
                    "entity_id": req.id,
                    "req_type": req.req_type.value,
                    "priority": req.priority.value,
                    "project_id": project_id,
                }

                await rag_service.add_document(content=content, metadata=metadata)
                indexed += 1

            await rag_service.close()
            logger.info(f"Indexed {indexed} requirements to KnowledgeBeast (project={project_id})")
            return indexed

        except Exception as e:
            logger.error(f"Failed to index requirements to KnowledgeBeast: {e}")
            return 0

    # ========================================================================
    # Document CRUD Operations
    # ========================================================================

    async def list_documents(
        self,
        project_id: int,
        limit: int = 50,
        offset: int = 0,
        doc_types: Optional[List[DocumentType]] = None,
        statuses: Optional[List[DocumentStatus]] = None,
        search: Optional[str] = None,
    ) -> "DocumentListResponse":
        """
        List documents with optional filters.

        Args:
            project_id: Project ID for multi-tenant isolation
            limit: Maximum items to return
            offset: Number of items to skip
            doc_types: Filter by document types
            statuses: Filter by document statuses
            search: Search term for path/title

        Returns:
            DocumentListResponse with items, total count, and has_more flag
        """
        from app.schemas.graph import DocumentListResponse, GraphDocumentResponse

        # Build base query
        query = select(GraphDocument).filter(GraphDocument.project_id == project_id)

        # Apply filters
        if doc_types:
            query = query.filter(GraphDocument.doc_type.in_(doc_types))
        if statuses:
            query = query.filter(GraphDocument.status.in_(statuses))
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    GraphDocument.path.ilike(search_pattern),
                    GraphDocument.title.ilike(search_pattern),
                )
            )

        # Get total count
        count_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar() or 0

        # Apply pagination and ordering
        query = (
            query.order_by(GraphDocument.updated_at.desc())
            .offset(offset)
            .limit(limit + 1)  # Fetch one extra to check has_more
        )

        result = await self.db.execute(query)
        documents = list(result.scalars().all())

        # Check has_more
        has_more = len(documents) > limit
        if has_more:
            documents = documents[:limit]

        return DocumentListResponse(
            items=[GraphDocumentResponse.model_validate(doc) for doc in documents],
            total=total,
            has_more=has_more,
        )

    async def get_document_with_entities(
        self,
        project_id: int,
        document_id: int,
    ) -> Optional["DocumentWithEntitiesResponse"]:
        """
        Get a document with its extracted concepts and requirements.

        Args:
            project_id: Project ID for multi-tenant isolation
            document_id: Document ID

        Returns:
            DocumentWithEntitiesResponse or None if not found
        """
        from app.schemas.graph import (
            DocumentWithEntitiesResponse,
            GraphConceptResponse,
            GraphDocumentResponse,
            GraphRequirementResponse,
        )

        # Get document
        doc_result = await self.db.execute(
            select(GraphDocument).filter(
                and_(
                    GraphDocument.project_id == project_id,
                    GraphDocument.id == document_id,
                )
            )
        )
        document = doc_result.scalar_one_or_none()
        if not document:
            return None

        # Get concepts for this document
        concepts_result = await self.db.execute(
            select(GraphConcept)
            .filter(
                and_(
                    GraphConcept.project_id == project_id,
                    GraphConcept.source_document_id == document_id,
                )
            )
            .order_by(GraphConcept.created_at.desc())
        )
        concepts = list(concepts_result.scalars().all())

        # Get requirements for this document
        requirements_result = await self.db.execute(
            select(GraphRequirement)
            .filter(
                and_(
                    GraphRequirement.project_id == project_id,
                    GraphRequirement.source_document_id == document_id,
                )
            )
            .order_by(GraphRequirement.created_at.desc())
        )
        requirements = list(requirements_result.scalars().all())

        # Count pending items
        pending_concepts = sum(1 for c in concepts if c.status == ConceptStatus.UNKNOWN)
        pending_requirements = sum(
            1 for r in requirements if r.status == RequirementStatus.PROPOSED
        )

        return DocumentWithEntitiesResponse(
            document=GraphDocumentResponse.model_validate(document),
            concepts=[GraphConceptResponse.model_validate(c) for c in concepts],
            requirements=[GraphRequirementResponse.model_validate(r) for r in requirements],
            pending_concept_count=pending_concepts,
            pending_requirement_count=pending_requirements,
        )

    async def create_single_document(
        self,
        project_id: int,
        request: "CreateDocumentRequest",
    ) -> GraphDocument:
        """
        Create a single document.

        Args:
            project_id: Project ID for multi-tenant isolation
            request: Document creation request

        Returns:
            Created document
        """
        document = GraphDocument(
            project_id=project_id,
            path=request.path,
            title=request.title,
            doc_type=request.doc_type,
            subtype=request.subtype,
            status=request.status or DocumentStatus.ACTIVE,
            audience=request.audience,
            value_assessment=request.value_assessment,
            word_count=request.word_count or 0,
            staleness_score=request.staleness_score,
            last_meaningful_date=request.last_meaningful_date,
            recommended_action=request.recommended_action,
            target_location=request.target_location,
            metadata=request.metadata,
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)

        logger.info(f"Created document {document.id} (project={project_id}, path={request.path})")
        return document

    async def update_document(
        self,
        project_id: int,
        document_id: int,
        request: "UpdateDocumentRequest",
    ) -> Optional[GraphDocument]:
        """
        Update a document.

        Args:
            project_id: Project ID for multi-tenant isolation
            document_id: Document ID
            request: Update request with partial fields

        Returns:
            Updated document or None if not found
        """
        result = await self.db.execute(
            select(GraphDocument).filter(
                and_(
                    GraphDocument.project_id == project_id,
                    GraphDocument.id == document_id,
                )
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            return None

        # Update only provided fields
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(document, field, value)

        await self.db.commit()
        await self.db.refresh(document)

        logger.info(f"Updated document {document_id} (project={project_id})")
        return document

    async def delete_document(
        self,
        project_id: int,
        document_id: int,
        cascade: bool = False,
    ) -> "DocumentDeleteResponse":
        """
        Delete a document and optionally cascade to concepts/requirements.

        Args:
            project_id: Project ID for multi-tenant isolation
            document_id: Document ID
            cascade: Whether to delete linked concepts/requirements

        Returns:
            DocumentDeleteResponse with deletion counts
        """
        from app.schemas.graph import DocumentDeleteResponse

        result = await self.db.execute(
            select(GraphDocument).filter(
                and_(
                    GraphDocument.project_id == project_id,
                    GraphDocument.id == document_id,
                )
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            return DocumentDeleteResponse(deleted=False)

        cascaded_concepts = 0
        cascaded_requirements = 0

        if cascade:
            # Delete linked concepts
            concepts_result = await self.db.execute(
                select(GraphConcept).filter(
                    and_(
                        GraphConcept.project_id == project_id,
                        GraphConcept.source_document_id == document_id,
                    )
                )
            )
            concepts = list(concepts_result.scalars().all())
            for concept in concepts:
                await self.db.delete(concept)
            cascaded_concepts = len(concepts)

            # Delete linked requirements
            requirements_result = await self.db.execute(
                select(GraphRequirement).filter(
                    and_(
                        GraphRequirement.project_id == project_id,
                        GraphRequirement.source_document_id == document_id,
                    )
                )
            )
            requirements = list(requirements_result.scalars().all())
            for req in requirements:
                await self.db.delete(req)
            cascaded_requirements = len(requirements)

        await self.db.delete(document)
        await self.db.commit()

        logger.info(
            f"Deleted document {document_id} (project={project_id}, "
            f"cascade={cascade}, concepts={cascaded_concepts}, requirements={cascaded_requirements})"
        )

        return DocumentDeleteResponse(
            deleted=True,
            cascaded_concepts=cascaded_concepts,
            cascaded_requirements=cascaded_requirements,
        )

    # ========================================================================
    # Simple Entity Creation
    # ========================================================================

    async def create_simple_concept(
        self,
        project_id: int,
        request: "CreateSimpleConceptRequest",
    ) -> GraphConcept:
        """
        Create a concept with minimal fields.

        Args:
            project_id: Project ID for multi-tenant isolation
            request: Simple concept creation request

        Returns:
            Created concept
        """
        concept = GraphConcept(
            project_id=project_id,
            source_document_id=request.source_document_id,
            name=request.name,
            concept_type=request.concept_type,
            definition=request.definition,
            status=ConceptStatus.ACTIVE,  # Manual creation = active
            confidence=ConfidenceLevel.HIGH,  # Manual = high confidence
        )
        self.db.add(concept)
        await self.db.commit()
        await self.db.refresh(concept)

        logger.info(f"Created concept {concept.id} (project={project_id}, name={request.name})")
        return concept

    async def update_concept(
        self,
        project_id: int,
        concept_id: int,
        request: "UpdateConceptRequest",
    ) -> Optional[GraphConcept]:
        """
        Update a concept.

        Args:
            project_id: Project ID for multi-tenant isolation
            concept_id: Concept ID
            request: Update request with partial fields

        Returns:
            Updated concept or None if not found
        """
        result = await self.db.execute(
            select(GraphConcept).filter(
                and_(
                    GraphConcept.project_id == project_id,
                    GraphConcept.id == concept_id,
                )
            )
        )
        concept = result.scalar_one_or_none()
        if not concept:
            return None

        # Update only provided fields
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(concept, field, value)

        await self.db.commit()
        await self.db.refresh(concept)

        logger.info(f"Updated concept {concept_id} (project={project_id})")
        return concept

    async def create_simple_requirement(
        self,
        project_id: int,
        request: "CreateSimpleRequirementRequest",
    ) -> GraphRequirement:
        """
        Create a requirement with minimal fields.

        Args:
            project_id: Project ID for multi-tenant isolation
            request: Simple requirement creation request

        Returns:
            Created requirement
        """
        # Generate unique req_id
        req_id = f"REQ-{uuid4().hex[:8].upper()}"

        requirement = GraphRequirement(
            project_id=project_id,
            source_document_id=request.source_document_id,
            req_id=req_id,
            text=request.text,
            req_type=request.req_type,
            priority=request.priority,
            status=RequirementStatus.ACCEPTED,  # Manual creation = accepted
        )
        self.db.add(requirement)
        await self.db.commit()
        await self.db.refresh(requirement)

        logger.info(f"Created requirement {requirement.id} (project={project_id}, req_id={req_id})")
        return requirement

    async def update_requirement(
        self,
        project_id: int,
        requirement_id: int,
        request: "UpdateRequirementRequest",
    ) -> Optional[GraphRequirement]:
        """
        Update a requirement.

        Args:
            project_id: Project ID for multi-tenant isolation
            requirement_id: Requirement ID
            request: Update request with partial fields

        Returns:
            Updated requirement or None if not found
        """
        result = await self.db.execute(
            select(GraphRequirement).filter(
                and_(
                    GraphRequirement.project_id == project_id,
                    GraphRequirement.id == requirement_id,
                )
            )
        )
        requirement = result.scalar_one_or_none()
        if not requirement:
            return None

        # Update only provided fields
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(requirement, field, value)

        await self.db.commit()
        await self.db.refresh(requirement)

        logger.info(f"Updated requirement {requirement_id} (project={project_id})")
        return requirement
