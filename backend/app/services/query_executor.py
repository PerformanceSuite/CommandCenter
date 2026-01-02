"""
QueryExecutor - Execute ComposedQuery against the graph database.

Phase 2, Task 2.3: Query Execution Service
Phase 4, Task 4.1: Enhanced with Temporal Query Support

This service takes a ComposedQuery (from IntentParser or direct construction)
and executes it against the graph database, returning entities, relationships,
and optional aggregations. Supports relative time expressions and temporal
aggregations.
"""

import logging
import time
from typing import Any, Optional, Type

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.models.graph import (
    DependencyType,
    GraphDependency,
    GraphFile,
    GraphRepo,
    GraphService,
    GraphSpecItem,
    GraphSymbol,
    GraphTask,
)
from app.schemas.query import (
    Affordance,
    ComposedQuery,
    EntitySelector,
    Filter,
    QueryResult,
    RelationshipSpec,
    TemporalAggregation,
    TimeRange,
)
from app.services.affordance_generator import AffordanceGenerator
from app.services.temporal_resolver import TemporalResolver

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Execute ComposedQuery against the graph database.

    Maps entity type strings to SQLAlchemy models and builds/executes
    queries based on the ComposedQuery specification.

    Examples:
        >>> executor = QueryExecutor(db_session)
        >>> query = ComposedQuery(entities=[EntitySelector(type="symbol")])
        >>> result = await executor.execute(query, project_id=1)
        >>> print(result.entities)
    """

    # Map entity type strings to model classes
    ENTITY_MODEL_MAP: dict[str, Type[DeclarativeBase]] = {
        "symbol": GraphSymbol,
        "file": GraphFile,
        "service": GraphService,
        "task": GraphTask,
        "spec": GraphSpecItem,
        "repo": GraphRepo,
    }

    # Columns that support text search (contains filter)
    TEXT_COLUMNS = {"name", "path", "title", "description", "qualified_name", "signature"}

    # Timestamp columns for time range filtering
    TIME_COLUMNS = {"created_at", "updated_at", "last_indexed_at"}

    def __init__(self, db: AsyncSession):
        """Initialize QueryExecutor with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db
        self.affordance_generator = AffordanceGenerator()
        self.temporal_resolver = TemporalResolver()

    async def execute(
        self,
        query: ComposedQuery,
        project_id: int,
        include_affordances: bool = False,
    ) -> QueryResult:
        """Execute a ComposedQuery and return results.

        Args:
            query: The composed query to execute
            project_id: Current project ID for scoping
            include_affordances: Whether to include affordances for agent parity

        Returns:
            QueryResult with entities, relationships, optional affordances, and metadata
        """
        start_time = time.time()

        entities: list[dict[str, Any]] = []
        relationships: list[dict[str, Any]] = []
        total = 0

        # Resolve relative time range if needed (Phase 4, Task 4.1)
        resolved_time_range: Optional[TimeRange] = None
        time_range_resolved: Optional[dict[str, str]] = None
        time_field_used: Optional[str] = None

        if query.time_range:
            resolved_time_range, time_range_resolved, time_field_used = self._resolve_time_range(
                query.time_range
            )

        # Process each entity selector
        for selector in query.entities:
            selector_entities, selector_total = await self._execute_entity_selector(
                selector=selector,
                filters=query.filters,
                time_range=resolved_time_range,
                project_id=project_id,
                limit=query.limit,
                offset=query.offset,
            )
            entities.extend(selector_entities)
            total += selector_total

        # Fetch relationships if requested
        if query.relationships and entities:
            entity_ids = [e["id"] for e in entities if e.get("type") == "symbol"]
            for rel_spec in query.relationships:
                rels = await self._fetch_relationships(entity_ids, rel_spec)
                relationships.extend(rels)

        # Compute aggregations if requested
        aggregations = None
        if query.aggregations:
            aggregations = await self._compute_aggregations(
                query=query,
                project_id=project_id,
                resolved_time_range=resolved_time_range,
            )

        # Generate affordances if requested (Phase 3, Task 3.3)
        affordances: list[Affordance] | None = None
        if include_affordances and entities:
            affordances = self.affordance_generator.generate_for_entities(entities, max_entities=10)

        elapsed_ms = (time.time() - start_time) * 1000

        # Build metadata with temporal information
        metadata: dict[str, Any] = {
            "execution_time_ms": round(elapsed_ms, 2),
            "entity_types_queried": [s.type for s in query.entities],
            "filters_applied": len(query.filters) if query.filters else 0,
            "relationships_traversed": len(query.relationships) if query.relationships else 0,
            "affordances_generated": len(affordances) if affordances else 0,
        }

        # Add temporal metadata if time range was used
        if time_range_resolved:
            metadata["time_range_resolved"] = time_range_resolved
        if time_field_used:
            metadata["time_field_used"] = time_field_used

        return QueryResult(
            entities=entities,
            relationships=relationships,
            aggregations=aggregations,
            affordances=affordances,
            total=total,
            metadata=metadata,
        )

    def _resolve_time_range(
        self,
        time_range: TimeRange,
    ) -> tuple[TimeRange, Optional[dict[str, str]], Optional[str]]:
        """Resolve relative time expressions to absolute datetime range.

        Returns:
            Tuple of (resolved_time_range, resolved_info, field_used)
        """
        resolved_info: Optional[dict[str, str]] = None
        field_used = time_range.field

        # If relative expression provided, resolve it
        if time_range.relative:
            try:
                start, end = self.temporal_resolver.resolve(time_range.relative)
                resolved_info = {
                    "expression": time_range.relative,
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                }
                # Create new TimeRange with resolved values
                return (
                    TimeRange(start=start, end=end, field=time_range.field),
                    resolved_info,
                    field_used,
                )
            except ValueError as e:
                logger.warning(f"Failed to resolve temporal expression: {e}")

        return time_range, resolved_info, field_used

    async def _execute_entity_selector(
        self,
        selector: EntitySelector,
        filters: Optional[list[Filter]],
        time_range: Optional[TimeRange],
        project_id: int,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Execute a single entity selector.

        Returns:
            Tuple of (entities list, total count before limit)
        """
        if selector.type == "any":
            # Query all entity types - collect results from each
            all_entities: list[dict[str, Any]] = []
            total_count = 0
            for entity_type, model in self.ENTITY_MODEL_MAP.items():
                type_entities, type_count = await self._query_model(
                    model=model,
                    entity_type=entity_type,
                    selector=selector,
                    filters=filters,
                    time_range=time_range,
                    project_id=project_id,
                    limit=limit,
                    offset=offset,
                )
                all_entities.extend(type_entities)
                total_count += type_count
            return all_entities[:limit], total_count

        model = self.ENTITY_MODEL_MAP.get(selector.type)
        if not model:
            logger.warning(f"Unknown entity type: {selector.type}")
            return [], 0

        return await self._query_model(
            model=model,
            entity_type=selector.type,
            selector=selector,
            filters=filters,
            time_range=time_range,
            project_id=project_id,
            limit=limit,
            offset=offset,
        )

    async def _query_model(
        self,
        model: Type[DeclarativeBase],
        entity_type: str,
        selector: EntitySelector,
        filters: Optional[list[Filter]],
        time_range: Optional[TimeRange],
        project_id: int,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Query a specific model with filters.

        Returns:
            Tuple of (entities list, total count)
        """
        # Build base query
        stmt = select(model)

        # Apply project scope based on model type
        stmt = self._apply_project_scope(stmt, model, project_id, selector)

        # Apply specific entity ID if provided
        if selector.id:
            stmt = stmt.filter(model.id == int(selector.id))

        # Apply filters
        if filters:
            stmt = self._apply_filters(stmt, model, filters)

        # Apply time range
        if time_range:
            stmt = self._apply_time_range(stmt, model, time_range)

        # Get total count before limit
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply limit and offset
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await self.db.execute(stmt)
        rows = result.scalars().all()

        # Serialize entities
        entities = [self._serialize_entity(entity, entity_type) for entity in rows]

        return entities, total

    def _apply_project_scope(
        self,
        stmt,
        model: Type[DeclarativeBase],
        project_id: int,
        selector: EntitySelector,
    ):
        """Apply project scoping to query based on model type."""
        # Models with direct project_id
        if hasattr(model, "project_id"):
            return stmt.filter(model.project_id == project_id)

        # GraphFile and GraphSymbol need to join through repo
        if model == GraphSymbol:
            # Symbol -> File -> Repo -> project_id
            stmt = stmt.join(GraphFile).join(GraphRepo)
            return stmt.filter(GraphRepo.project_id == project_id)

        if model == GraphFile:
            # File -> Repo -> project_id
            stmt = stmt.join(GraphRepo)
            return stmt.filter(GraphRepo.project_id == project_id)

        if model == GraphRepo:
            return stmt.filter(model.project_id == project_id)

        return stmt

    def _apply_filters(
        self,
        stmt,
        model: Type[DeclarativeBase],
        filters: list[Filter],
    ):
        """Apply filter conditions to query."""
        for f in filters:
            if not hasattr(model, f.field):
                logger.warning(f"Filter field '{f.field}' not found on model {model.__name__}")
                continue

            col = getattr(model, f.field)

            if f.operator == "eq":
                stmt = stmt.filter(col == f.value)
            elif f.operator == "ne":
                stmt = stmt.filter(col != f.value)
            elif f.operator == "lt":
                stmt = stmt.filter(col < f.value)
            elif f.operator == "gt":
                stmt = stmt.filter(col > f.value)
            elif f.operator == "lte":
                stmt = stmt.filter(col <= f.value)
            elif f.operator == "gte":
                stmt = stmt.filter(col >= f.value)
            elif f.operator == "in":
                if isinstance(f.value, list):
                    stmt = stmt.filter(col.in_(f.value))
            elif f.operator == "contains":
                if f.field in self.TEXT_COLUMNS:
                    stmt = stmt.filter(col.ilike(f"%{f.value}%"))

        return stmt

    def _apply_time_range(
        self,
        stmt,
        model: Type[DeclarativeBase],
        time_range: TimeRange,
    ):
        """Apply time range filtering.

        Supports specific field selection via time_range.field or
        auto-detects the first available timestamp column.
        """
        # Use specified field or auto-detect
        time_col = None

        if time_range.field and hasattr(model, time_range.field):
            time_col = getattr(model, time_range.field)
        else:
            # Auto-detect time column
            for col_name in self.TIME_COLUMNS:
                if hasattr(model, col_name):
                    time_col = getattr(model, col_name)
                    break

        if not time_col:
            return stmt

        if time_range.start:
            stmt = stmt.filter(time_col >= time_range.start)
        if time_range.end:
            stmt = stmt.filter(time_col <= time_range.end)

        return stmt

    async def _fetch_relationships(
        self,
        entity_ids: list[int | str],
        rel_spec: RelationshipSpec,
    ) -> list[dict[str, Any]]:
        """Fetch relationships for given entity IDs.

        Currently supports symbol dependencies. Can be extended
        for other relationship types.
        """
        relationships: list[dict[str, Any]] = []

        if not entity_ids:
            return relationships

        # Convert to integers
        int_ids = [int(eid) for eid in entity_ids if str(eid).isdigit()]
        if not int_ids:
            return relationships

        # Build query based on direction
        if rel_spec.direction == "outbound":
            stmt = select(GraphDependency).filter(GraphDependency.from_symbol_id.in_(int_ids))
        elif rel_spec.direction == "inbound":
            stmt = select(GraphDependency).filter(GraphDependency.to_symbol_id.in_(int_ids))
        else:  # both
            stmt = select(GraphDependency).filter(
                or_(
                    GraphDependency.from_symbol_id.in_(int_ids),
                    GraphDependency.to_symbol_id.in_(int_ids),
                )
            )

        # Filter by relationship type if it maps to DependencyType
        type_mapping = {
            "dependency": [DependencyType.IMPORT, DependencyType.USES],
            "import": [DependencyType.IMPORT],
            "call": [DependencyType.CALL],
            "caller": [DependencyType.CALL],  # callers are inbound calls
            "reference": [DependencyType.REFERENCES],
        }

        if rel_spec.type in type_mapping:
            stmt = stmt.filter(GraphDependency.type.in_(type_mapping[rel_spec.type]))

        stmt = stmt.limit(100)  # Limit relationships to avoid explosion

        result = await self.db.execute(stmt)
        deps = result.scalars().all()

        for dep in deps:
            relationships.append(
                {
                    "id": dep.id,
                    "source": dep.from_symbol_id,
                    "target": dep.to_symbol_id,
                    "type": dep.type.value if hasattr(dep.type, "value") else str(dep.type),
                    "weight": dep.weight,
                }
            )

        return relationships

    async def _compute_aggregations(
        self,
        query: ComposedQuery,
        project_id: int,
        resolved_time_range: Optional[TimeRange] = None,
    ) -> dict[str, Any]:
        """Compute aggregations for the query.

        Args:
            query: The composed query
            project_id: Current project ID for scoping
            resolved_time_range: Optional resolved time range for temporal aggregations
        """
        aggregations: dict[str, Any] = {}

        if not query.aggregations:
            return aggregations

        for agg in query.aggregations:
            for selector in query.entities:
                model = self.ENTITY_MODEL_MAP.get(selector.type)
                if not model:
                    continue

                if agg.type == "count":
                    # Check for temporal aggregation (Phase 4, Task 4.1)
                    if agg.temporal:
                        result = await self._compute_temporal_aggregation(
                            model=model,
                            project_id=project_id,
                            selector=selector,
                            filters=query.filters,
                            time_range=resolved_time_range,
                            temporal=agg.temporal,
                        )
                        aggregations["temporal"] = result
                    elif agg.group_by:
                        # Group by aggregation
                        result = await self._count_grouped(
                            model, project_id, selector, query.filters, agg.group_by
                        )
                        aggregations[f"count_by_{agg.group_by[0]}"] = result
                    else:
                        # Simple count
                        count = await self._count_entities(
                            model, project_id, selector, query.filters
                        )
                        aggregations["count"] = count

        return aggregations

    async def _compute_temporal_aggregation(
        self,
        model: Type[DeclarativeBase],
        project_id: int,
        selector: EntitySelector,
        filters: Optional[list[Filter]],
        time_range: Optional[TimeRange],
        temporal: TemporalAggregation,
    ) -> dict[str, Any]:
        """Compute temporal aggregation (counts per time bucket).

        Returns:
            Dictionary with buckets and their counts/values
        """
        # Find appropriate time column
        time_col = None
        time_col_name: Optional[str] = time_range.field if time_range and time_range.field else None

        if time_col_name and hasattr(model, time_col_name):
            time_col = getattr(model, time_col_name)
        else:
            # Auto-detect time column
            for col_name in self.TIME_COLUMNS:
                if hasattr(model, col_name):
                    time_col = getattr(model, col_name)
                    time_col_name = col_name
                    break

        if not time_col:
            return {"error": "No timestamp column available", "buckets": []}

        # Build bucket expression based on granularity
        if temporal.bucket == "hour":
            bucket_expr = func.date_trunc("hour", time_col)
        elif temporal.bucket == "day":
            bucket_expr = func.date_trunc("day", time_col)
        elif temporal.bucket == "week":
            bucket_expr = func.date_trunc("week", time_col)
        elif temporal.bucket == "month":
            bucket_expr = func.date_trunc("month", time_col)
        elif temporal.bucket == "quarter":
            bucket_expr = func.date_trunc("quarter", time_col)
        elif temporal.bucket == "year":
            bucket_expr = func.date_trunc("year", time_col)
        else:
            bucket_expr = func.date_trunc("day", time_col)

        # Build aggregation expression
        if temporal.metric == "count":
            agg_expr = func.count()
        elif temporal.metric == "sum" and temporal.field and hasattr(model, temporal.field):
            agg_expr = func.sum(getattr(model, temporal.field))
        elif temporal.metric == "avg" and temporal.field and hasattr(model, temporal.field):
            agg_expr = func.avg(getattr(model, temporal.field))
        elif temporal.metric == "min" and temporal.field and hasattr(model, temporal.field):
            agg_expr = func.min(getattr(model, temporal.field))
        elif temporal.metric == "max" and temporal.field and hasattr(model, temporal.field):
            agg_expr = func.max(getattr(model, temporal.field))
        else:
            agg_expr = func.count()

        # Build query
        stmt = select(bucket_expr.label("bucket"), agg_expr.label("value")).group_by(bucket_expr)

        # Apply project scope
        if hasattr(model, "project_id"):
            stmt = stmt.filter(model.project_id == project_id)

        # Apply time range filter
        if time_range:
            if time_range.start:
                stmt = stmt.filter(time_col >= time_range.start)
            if time_range.end:
                stmt = stmt.filter(time_col <= time_range.end)

        # Apply additional filters
        if filters:
            stmt = self._apply_filters(stmt, model, filters)

        # Order by bucket
        stmt = stmt.order_by(bucket_expr)

        # Execute query
        result = await self.db.execute(stmt)
        rows = result.all()

        # Format results
        buckets = []
        for row in rows:
            bucket_value = row.bucket
            if bucket_value:
                buckets.append(
                    {
                        "bucket": bucket_value.isoformat()
                        if hasattr(bucket_value, "isoformat")
                        else str(bucket_value),
                        "value": row.value,
                    }
                )

        return {
            "bucket_size": temporal.bucket,
            "metric": temporal.metric,
            "field": temporal.field or "count",
            "time_column": time_col_name,
            "buckets": buckets,
        }

    async def _count_entities(
        self,
        model: Type[DeclarativeBase],
        project_id: int,
        selector: EntitySelector,
        filters: Optional[list[Filter]],
    ) -> int:
        """Count entities matching the query."""
        stmt = select(func.count()).select_from(model)
        stmt = self._apply_project_scope(stmt, model, project_id, selector)

        if filters:
            stmt = self._apply_filters(stmt, model, filters)

        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _count_grouped(
        self,
        model: Type[DeclarativeBase],
        project_id: int,
        selector: EntitySelector,
        filters: Optional[list[Filter]],
        group_by: list[str],
    ) -> dict[str, int]:
        """Count entities grouped by specified fields."""
        if not group_by or not hasattr(model, group_by[0]):
            return {}

        group_col = getattr(model, group_by[0])
        stmt = select(group_col, func.count()).group_by(group_col)

        # Apply project scope
        if hasattr(model, "project_id"):
            stmt = stmt.filter(model.project_id == project_id)

        if filters:
            stmt = self._apply_filters(stmt, model, filters)

        result = await self.db.execute(stmt)
        rows = result.all()

        return {str(row[0].value if hasattr(row[0], "value") else row[0]): row[1] for row in rows}

    def _serialize_entity(self, entity: Any, entity_type: str) -> dict[str, Any]:
        """Serialize a model instance to a dictionary.

        Creates a consistent representation with id, type, label, and metadata.
        """
        # Get primary identifier
        entity_id = entity.id

        # Determine label based on entity type
        if entity_type == "symbol":
            label = entity.name
        elif entity_type == "file":
            label = entity.path
        elif entity_type == "service":
            label = entity.name
        elif entity_type == "task":
            label = entity.title
        elif entity_type == "spec":
            label = entity.title
        elif entity_type == "repo":
            label = entity.full_name
        else:
            label = str(entity_id)

        # Build base serialized entity
        serialized: dict[str, Any] = {
            "id": entity_id,
            "type": entity_type,
            "label": label,
        }

        # Add type-specific fields
        if entity_type == "symbol":
            serialized.update(
                {
                    "kind": entity.kind.value
                    if hasattr(entity.kind, "value")
                    else str(entity.kind),
                    "file_id": entity.file_id,
                    "range_start": entity.range_start,
                    "range_end": entity.range_end,
                    "exports": entity.exports,
                }
            )
        elif entity_type == "file":
            serialized.update(
                {
                    "path": entity.path,
                    "lang": entity.lang,
                    "lines": entity.lines,
                    "repo_id": entity.repo_id,
                }
            )
        elif entity_type == "service":
            serialized.update(
                {
                    "service_type": entity.type.value
                    if hasattr(entity.type, "value")
                    else str(entity.type),
                    "status": entity.status.value
                    if hasattr(entity.status, "value")
                    else str(entity.status),
                    "endpoint": entity.endpoint,
                }
            )
        elif entity_type == "task":
            serialized.update(
                {
                    "title": entity.title,
                    "kind": entity.kind.value
                    if hasattr(entity.kind, "value")
                    else str(entity.kind),
                    "status": entity.status.value
                    if hasattr(entity.status, "value")
                    else str(entity.status),
                }
            )
        elif entity_type == "spec":
            serialized.update(
                {
                    "title": entity.title,
                    "source": entity.source.value
                    if hasattr(entity.source, "value")
                    else str(entity.source),
                    "status": entity.status.value
                    if hasattr(entity.status, "value")
                    else str(entity.status),
                    "priority": entity.priority,
                }
            )

        # Include any metadata
        if hasattr(entity, "metadata_") and entity.metadata_:
            serialized["metadata"] = entity.metadata_

        return serialized
