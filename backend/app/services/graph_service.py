"""
GraphService - Business logic for Phase 7 Graph Service

Encapsulates all graph database operations with multi-tenant isolation.
"""

from typing import List, Literal, Optional, Sequence

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
from app.schemas.graph import (
    DependencyGraph,
    GhostNode,
    GraphEdge,
    GraphFilters,
    GraphNode,
    ProjectGraphResponse,
    SearchResults,
    SpecFilters,
)


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
        return results

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

        return task

    async def trigger_audit(
        self,
        target_entity: str,
        target_id: int,
        kind: AuditKind,
    ) -> GraphAudit:
        """
        Trigger an audit for a target entity.

        Creates audit record and publishes NATS event for async processing.

        Args:
            target_entity: Target table name
            target_id: Target entity ID
            kind: Audit type

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

        # TODO: Publish NATS event for async audit processing
        # await self.publish_audit_request(audit)

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
