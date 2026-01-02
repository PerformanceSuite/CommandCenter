"""
Computed Properties Service (Phase 4, Task 4.3)

Provides computation of derived properties on entities at query time:
- symbolCount: Count of symbols in a file
- allDependencies: Transitive closure of symbol dependencies
- projectHealth: Aggregate health score for a project
- dependencyCount: Number of dependencies for a symbol
- callerCount: Number of callers for a symbol
"""

import logging
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.graph import GraphDependency, GraphFile, GraphService, GraphSymbol, GraphTask
from app.schemas.query import ComputedPropertySpec

logger = logging.getLogger(__name__)


class ComputedPropertiesService:
    """Service for computing derived properties on entities.

    Computes properties like symbol counts, dependency traversals,
    and health scores at query time.

    Examples:
        >>> service = ComputedPropertiesService(db_session)
        >>> count = await service.compute_symbol_count(file_id=123)
        >>> deps = await service.compute_all_dependencies(symbol_id=456, max_depth=3)
        >>> health = await service.compute_project_health(project_id=1)
    """

    def __init__(self, db: AsyncSession):
        """Initialize ComputedPropertiesService.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db

    async def compute_for_entity(
        self,
        entity: dict[str, Any],
        spec: ComputedPropertySpec,
    ) -> Any:
        """Compute a property for a specific entity.

        Dispatches to the appropriate computation method based on
        the property name.

        Args:
            entity: Entity dictionary with at least 'id' and 'type'
            spec: Computed property specification

        Returns:
            Computed property value, or None if unknown property
        """
        entity_id = entity.get("id")
        entity_type = entity.get("type")

        if spec.property == "symbolCount" and entity_type == "file":
            return await self.compute_symbol_count(file_id=entity_id)

        elif spec.property == "allDependencies" and entity_type == "symbol":
            max_depth = spec.options.get("depth", 3) if spec.options else 3
            return await self.compute_all_dependencies(
                symbol_id=entity_id,
                max_depth=max_depth,
            )

        elif spec.property == "projectHealth":
            # Project ID might be passed directly or derived from entity
            project_id = (
                entity_id
                if entity_type == "project"
                else spec.options.get("project_id")
                if spec.options
                else None
            )
            if project_id:
                return await self.compute_project_health(project_id=project_id)

        elif spec.property == "dependencyCount" and entity_type == "symbol":
            return await self.compute_dependency_count(symbol_id=entity_id)

        elif spec.property == "callerCount" and entity_type == "symbol":
            return await self.compute_caller_count(symbol_id=entity_id)

        logger.warning(
            f"Unknown or incompatible computed property: "
            f"{spec.property} for entity type {entity_type}"
        )
        return None

    async def compute_symbol_count(self, file_id: int) -> int:
        """Count symbols in a file.

        Args:
            file_id: File ID

        Returns:
            Number of symbols in the file
        """
        stmt = select(func.count()).select_from(GraphSymbol).filter(GraphSymbol.file_id == file_id)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def compute_all_dependencies(
        self,
        symbol_id: int,
        max_depth: int = 3,
    ) -> dict[str, Any]:
        """Compute transitive closure of dependencies.

        Traverses the dependency graph up to max_depth levels,
        collecting both direct and indirect dependencies.

        Args:
            symbol_id: Starting symbol ID
            max_depth: Maximum traversal depth

        Returns:
            Dictionary with direct, indirect, and total counts
        """
        direct_deps: set[int] = set()
        indirect_deps: set[int] = set()
        current_level = {symbol_id}
        depth = 0

        while current_level and depth < max_depth:
            # Query dependencies for current level
            stmt = select(GraphDependency).filter(GraphDependency.from_symbol_id.in_(current_level))
            result = await self.db.execute(stmt)
            deps = result.scalars().all()

            next_level: set[int] = set()
            for dep in deps:
                target_id = dep.to_symbol_id
                if (
                    target_id not in direct_deps
                    and target_id not in indirect_deps
                    and target_id != symbol_id
                ):
                    if depth == 0:
                        direct_deps.add(target_id)
                    else:
                        indirect_deps.add(target_id)
                    next_level.add(target_id)

            current_level = next_level
            depth += 1

        return {
            "direct": list(direct_deps),
            "indirect": list(indirect_deps),
            "direct_count": len(direct_deps),
            "indirect_count": len(indirect_deps),
            "total_count": len(direct_deps) + len(indirect_deps),
            "max_depth_reached": depth,
        }

    async def compute_project_health(self, project_id: int) -> dict[str, Any]:
        """Compute aggregate health score for a project.

        Health is computed based on:
        - Symbol coverage (symbols without issues)
        - File health (files without issues)
        - Task completion rate
        - Service status

        Args:
            project_id: Project ID

        Returns:
            Dictionary with score (0-100) and component breakdowns
        """
        components: dict[str, float] = {}

        # Symbol health (40% weight)
        total_symbols = await self._count_project_symbols(project_id)
        if total_symbols > 0:
            symbols_with_issues = await self._count_symbols_with_issues(project_id)
            components["symbol_health"] = (
                (total_symbols - symbols_with_issues) / total_symbols * 100
            )
        else:
            components["symbol_health"] = 100.0

        # File health (20% weight)
        total_files = await self._count_project_files(project_id)
        if total_files > 0:
            files_with_issues = await self._count_files_with_issues(project_id)
            components["file_health"] = (total_files - files_with_issues) / total_files * 100
        else:
            components["file_health"] = 100.0

        # Task completion (20% weight)
        total_tasks = await self._count_project_tasks(project_id)
        if total_tasks > 0:
            completed_tasks = await self._count_completed_tasks(project_id)
            components["task_completion"] = completed_tasks / total_tasks * 100
        else:
            components["task_completion"] = 100.0

        # Service availability (20% weight)
        total_services = await self._count_project_services(project_id)
        if total_services > 0:
            healthy_services = await self._count_healthy_services(project_id)
            components["service_health"] = healthy_services / total_services * 100
        else:
            components["service_health"] = 100.0

        # Weighted average
        weights = {
            "symbol_health": 0.4,
            "file_health": 0.2,
            "task_completion": 0.2,
            "service_health": 0.2,
        }

        score = sum(components[k] * weights[k] for k in components)

        return {
            "score": round(score, 2),
            "components": {k: round(v, 2) for k, v in components.items()},
            "total_symbols": total_symbols,
            "total_files": total_files,
            "total_tasks": total_tasks,
            "total_services": total_services,
        }

    async def compute_dependency_count(self, symbol_id: int) -> int:
        """Count outbound dependencies for a symbol.

        Args:
            symbol_id: Symbol ID

        Returns:
            Number of dependencies
        """
        stmt = (
            select(func.count())
            .select_from(GraphDependency)
            .filter(GraphDependency.from_symbol_id == symbol_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def compute_caller_count(self, symbol_id: int) -> int:
        """Count inbound callers for a symbol.

        Args:
            symbol_id: Symbol ID

        Returns:
            Number of callers
        """
        stmt = (
            select(func.count())
            .select_from(GraphDependency)
            .filter(GraphDependency.to_symbol_id == symbol_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def batch_compute(
        self,
        entities: list[dict[str, Any]],
        property: str,
        options: Optional[dict[str, Any]] = None,
    ) -> dict[int, Any]:
        """Compute a property for multiple entities.

        Args:
            entities: List of entity dictionaries
            property: Property name to compute
            options: Property-specific options

        Returns:
            Dictionary mapping entity IDs to computed values
        """
        results: dict[int, Any] = {}
        spec = ComputedPropertySpec(
            property=property,  # type: ignore
            entity_type=entities[0]["type"] if entities else "unknown",
            options=options,
        )

        for entity in entities:
            entity_id = entity.get("id")
            if entity_id is not None:
                value = await self.compute_for_entity(entity, spec)
                results[entity_id] = value

        return results

    # ==========================================================================
    # Private helper methods for health computation
    # ==========================================================================

    async def _count_project_symbols(self, project_id: int) -> int:
        """Count total symbols in a project."""
        from app.models.graph import GraphRepo

        stmt = (
            select(func.count())
            .select_from(GraphSymbol)
            .join(GraphFile)
            .join(GraphRepo)
            .filter(GraphRepo.project_id == project_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _count_symbols_with_issues(self, project_id: int) -> int:
        """Count symbols with issues (placeholder for actual logic)."""
        # In a real implementation, this would check for symbols
        # with failing tests, lint errors, or quality issues
        return 0

    async def _count_project_files(self, project_id: int) -> int:
        """Count total files in a project."""
        from app.models.graph import GraphRepo

        stmt = (
            select(func.count())
            .select_from(GraphFile)
            .join(GraphRepo)
            .filter(GraphRepo.project_id == project_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _count_files_with_issues(self, project_id: int) -> int:
        """Count files with issues (placeholder for actual logic)."""
        return 0

    async def _count_project_tasks(self, project_id: int) -> int:
        """Count total tasks in a project."""
        stmt = (
            select(func.count()).select_from(GraphTask).filter(GraphTask.project_id == project_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _count_completed_tasks(self, project_id: int) -> int:
        """Count completed tasks in a project."""
        from app.models.graph import TaskStatus

        stmt = (
            select(func.count())
            .select_from(GraphTask)
            .filter(
                GraphTask.project_id == project_id,
                GraphTask.status == TaskStatus.DONE,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _count_project_services(self, project_id: int) -> int:
        """Count total services in a project."""
        stmt = (
            select(func.count())
            .select_from(GraphService)
            .filter(GraphService.project_id == project_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _count_healthy_services(self, project_id: int) -> int:
        """Count healthy services in a project."""
        from app.models.graph import ServiceStatus

        stmt = (
            select(func.count())
            .select_from(GraphService)
            .filter(
                GraphService.project_id == project_id,
                GraphService.status == ServiceStatus.HEALTHY,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
