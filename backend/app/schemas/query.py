"""
Pydantic schemas for Composable Query Language (Tasks 2.1, 3.1)

Defines the ComposedQuery model that enables:
- Entity selection with type and scope
- Relationship traversal specifications
- Filter conditions for narrowing results
- Time range filtering
- Presentation hints
- Optional aggregations
- Affordances for agent parity (Phase 3)
"""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

# =============================================================================
# Affordance Schemas (Phase 3, Task 3.1)
# =============================================================================


class EntityRef(BaseModel):
    """Reference to a specific entity.

    Used in affordances to identify the target of an action.

    Examples:
        EntityRef(type="symbol", id="123")
        EntityRef(type="file", id="456")
    """

    type: str = Field(..., description="Entity type (symbol, file, service, etc.)")
    id: str = Field(..., description="Entity ID")


class Affordance(BaseModel):
    """An action that can be taken on an entity.

    Affordances enable agent parity - any action a user can take
    in the UI, an agent can also take via the API.

    Examples:
        Affordance(
            action="trigger_audit",
            target=EntityRef(type="symbol", id="123"),
            description="Run security audit on this function",
            parameters={"audit_type": "security"}
        )
    """

    action: Literal[
        "trigger_audit",
        "create_task",
        "open_in_editor",
        "drill_down",
        "run_indexer",
        "view_dependencies",
        "view_callers",
    ] = Field(..., description="Action type")
    target: EntityRef = Field(..., description="Target entity for the action")
    description: str = Field(..., description="Human-readable description of the action")
    parameters: Optional[dict[str, Any]] = Field(
        None, description="Optional action-specific parameters"
    )


# =============================================================================
# Query Schemas (Phase 2)
# =============================================================================


class EntitySelector(BaseModel):
    """Selects entities by type and optional scope.

    Examples:
        EntitySelector(type="symbol", scope="file:main.py")
        EntitySelector(type="service", scope="project:123")
        EntitySelector(type="file", constraints={"lang": "python"})
    """

    type: str = Field(
        ...,
        description="Entity type: symbol, file, service, task, spec, persona, workflow, execution, or 'any'",
    )
    scope: Optional[str] = Field(
        None,
        description="Optional scope in format 'scope_type:scope_id' (e.g., 'file:main.py', 'project:123')",
    )
    id: Optional[str] = Field(
        None,
        description="Optional specific entity ID to select",
    )
    constraints: Optional[dict] = Field(
        None,
        description="Additional constraints (e.g., {'lang': 'python', 'path_prefix': '/src'})",
    )


class RelationshipSpec(BaseModel):
    """Specifies relationship traversal from selected entities.

    Examples:
        RelationshipSpec(type="dependency", direction="outbound", depth=2)
        RelationshipSpec(type="caller", direction="inbound", depth=1)
    """

    type: str = Field(
        ...,
        description="Relationship type: calls, imports, depends_on, implements, etc.",
    )
    direction: Literal["inbound", "outbound", "both"] = Field(
        "both",
        description="Direction of traversal from the entity",
    )
    depth: int = Field(
        1,
        ge=1,
        le=10,
        description="Maximum traversal depth",
    )
    filters: Optional[dict[str, Any]] = Field(
        None,
        description="Additional filters to apply during traversal",
    )


class Filter(BaseModel):
    """Filter condition for narrowing query results.

    Examples:
        Filter(field="health", operator="lt", value=100)
        Filter(field="status", operator="eq", value="active")
    """

    field: str = Field(..., description="Field name to filter on")
    operator: Literal["eq", "ne", "lt", "gt", "lte", "gte", "in", "contains"] = Field(
        ...,
        description="Comparison operator",
    )
    value: Any = Field(..., description="Value to compare against")


class RelativeTimeRange(BaseModel):
    """Relative time expression that resolves to absolute datetime range.

    Supports natural language time expressions:
    - "last N days/hours/weeks/months"
    - "yesterday", "today", "tomorrow"
    - "this week", "last week", "this month", "last month"
    - "this quarter", "last quarter"

    Examples:
        RelativeTimeRange(expression="last 7 days")
        RelativeTimeRange(expression="yesterday")
        RelativeTimeRange(expression="this month")
    """

    expression: str = Field(
        ...,
        description="Relative time expression (e.g., 'last 7 days', 'this week')",
    )


class TemporalAggregation(BaseModel):
    """Temporal bucketing for time-based aggregations.

    Groups results into time buckets for trend analysis.

    Examples:
        TemporalAggregation(bucket="day", metric="count")
        TemporalAggregation(bucket="week", metric="sum", field="lines")
    """

    bucket: Literal["hour", "day", "week", "month", "quarter", "year"] = Field(
        ...,
        description="Time bucket granularity",
    )
    metric: Literal["count", "sum", "avg", "min", "max"] = Field(
        "count",
        description="Aggregation metric",
    )
    field: Optional[str] = Field(
        None,
        description="Field to aggregate (required for sum, avg, min, max)",
    )


class TimeRange(BaseModel):
    """Time range for temporal filtering.

    Supports both absolute datetime ranges and relative expressions.
    Can optionally specify which timestamp field to filter on.

    Examples:
        TimeRange(start=datetime(2024, 1, 1))
        TimeRange(start=datetime(2024, 1, 1), end=datetime(2024, 12, 31))
        TimeRange(relative="last 7 days")
        TimeRange(relative="yesterday", field="updated_at")
    """

    start: Optional[datetime] = Field(
        None,
        description="Start of time range (inclusive)",
    )
    end: Optional[datetime] = Field(
        None,
        description="End of time range (inclusive)",
    )
    relative: Optional[str] = Field(
        None,
        description="Relative time expression (e.g., 'last 7 days', 'yesterday')",
    )
    field: Optional[Literal["created_at", "updated_at", "last_indexed_at"]] = Field(
        None,
        description="Timestamp field to filter on (auto-detected if not specified)",
    )


class Aggregation(BaseModel):
    """Aggregation specification for grouping/summarizing results.

    Examples:
        Aggregation(type="count", group_by=["type"])
        Aggregation(type="sum", field="lines", group_by=["language"])
        Aggregation(type="count", temporal=TemporalAggregation(bucket="day"))
    """

    type: Literal["count", "sum", "avg", "min", "max", "group"] = Field(
        ...,
        description="Aggregation type",
    )
    field: Optional[str] = Field(
        None,
        description="Field to aggregate (required for sum, avg, min, max)",
    )
    group_by: Optional[list[str]] = Field(
        None,
        description="Fields to group by",
    )
    temporal: Optional[TemporalAggregation] = Field(
        None,
        description="Temporal bucketing for time-based aggregations",
    )


# =============================================================================
# Semantic Search Schema (Phase 4, Task 4.2)
# =============================================================================


class SemanticSearchSpec(BaseModel):
    """Specification for semantic/RAG-based search.

    Integrates with KnowledgeBeast/RAG service to perform vector
    similarity and hybrid (vector + keyword) search across the
    knowledge base.

    Examples:
        SemanticSearchSpec(query="authentication flow")
        SemanticSearchSpec(query="security best practices", threshold=0.7)
        SemanticSearchSpec(query="database schema", categories=["docs", "code"])
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural language search query",
    )
    limit: int = Field(
        5,
        ge=1,
        le=50,
        description="Maximum number of semantic results to return",
    )
    threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold (0.0-1.0)",
    )
    categories: Optional[list[str]] = Field(
        None,
        description="Filter by knowledge base categories (e.g., 'docs', 'code')",
    )
    include_content: bool = Field(
        True,
        description="Include full content in results (vs. just metadata)",
    )


# =============================================================================
# Computed Properties Schema (Phase 4, Task 4.3)
# =============================================================================


class ComputedPropertySpec(BaseModel):
    """Specification for a computed property on entities.

    Computed properties are derived values calculated at query time,
    such as counts, aggregations, or traversal results.

    Supported properties:
    - symbolCount: Count of symbols in a file
    - allDependencies: Transitive closure of symbol dependencies
    - projectHealth: Aggregate health score for a project

    Examples:
        ComputedPropertySpec(property="symbolCount", entity_type="file")
        ComputedPropertySpec(
            property="allDependencies",
            entity_type="symbol",
            options={"depth": 3}
        )
    """

    property: Literal[
        "symbolCount",
        "allDependencies",
        "projectHealth",
        "dependencyCount",
        "callerCount",
    ] = Field(
        ...,
        description="Name of the computed property",
    )
    entity_type: str = Field(
        ...,
        description="Entity type this property applies to",
    )
    options: Optional[dict[str, Any]] = Field(
        None,
        description="Property-specific options (e.g., depth for traversals)",
    )


class ComposedQuery(BaseModel):
    """A composable query that can express complex graph traversals.

    This is the core query model for the Composable CommandCenter,
    enabling natural language and structured queries to be converted
    to a unified representation for graph traversal.

    Examples:
        # Simple entity query
        ComposedQuery(entities=[EntitySelector(type="service")])

        # Entity with relationships
        ComposedQuery(
            entities=[EntitySelector(type="symbol", id="graph_service.get_project")],
            relationships=[RelationshipSpec(type="dependency", direction="outbound", depth=2)]
        )

        # Filtered query
        ComposedQuery(
            entities=[EntitySelector(type="service")],
            filters=[Filter(field="health", operator="lt", value=100)]
        )
    """

    entities: list[EntitySelector] = Field(
        ...,
        min_length=1,
        description="Entity selectors - at least one required",
    )
    filters: Optional[list[Filter]] = Field(
        None,
        description="Filter conditions to apply",
    )
    relationships: Optional[list[RelationshipSpec]] = Field(
        None,
        description="Relationship traversal specifications",
    )
    presentation: Optional[dict] = Field(
        None,
        description="Presentation hints (e.g., {'layout': 'graph', 'depth': 2})",
    )
    time_range: Optional[TimeRange] = Field(
        None,
        description="Temporal filter for time-based queries",
    )
    aggregations: Optional[list[Aggregation]] = Field(
        None,
        description="Aggregations to compute on results",
    )
    semantic: Optional[SemanticSearchSpec] = Field(
        None,
        description="Semantic/RAG search specification (Phase 4, Task 4.2)",
    )
    computed: Optional[list[ComputedPropertySpec]] = Field(
        None,
        description="Computed properties to calculate for entities (Phase 4, Task 4.3)",
    )
    limit: int = Field(
        100,
        ge=1,
        le=1000,
        description="Maximum number of results",
    )
    offset: int = Field(
        0,
        ge=0,
        description="Offset for pagination",
    )


class QueryResult(BaseModel):
    """Result of executing a ComposedQuery.

    Contains matched entities, traversed relationships, optional aggregations,
    and affordances for agent parity.
    """

    entities: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Matched entities with their properties",
    )
    relationships: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Traversed relationships",
    )
    aggregations: Optional[dict[str, Any]] = Field(
        None,
        description="Computed aggregation results",
    )
    affordances: Optional[list[Affordance]] = Field(
        None,
        description="Available actions for the returned entities (Phase 3)",
    )
    total: int = Field(
        0,
        description="Total count of matched entities (before limit)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Query execution metadata (timing, depth reached, etc.)",
    )
