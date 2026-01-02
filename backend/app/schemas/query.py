"""
Pydantic schemas for Composable Query Language (Task 2.1)

Defines the ComposedQuery model that enables:
- Entity selection with type and scope
- Relationship traversal specifications
- Filter conditions for narrowing results
- Time range filtering
- Presentation hints
- Optional aggregations
"""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


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


class TimeRange(BaseModel):
    """Time range for temporal filtering.

    Both bounds are optional, allowing open-ended ranges.

    Examples:
        TimeRange(start=datetime(2024, 1, 1))
        TimeRange(start=datetime(2024, 1, 1), end=datetime(2024, 12, 31))
    """

    start: Optional[datetime] = Field(
        None,
        description="Start of time range (inclusive)",
    )
    end: Optional[datetime] = Field(
        None,
        description="End of time range (inclusive)",
    )


class Aggregation(BaseModel):
    """Aggregation specification for grouping/summarizing results.

    Examples:
        Aggregation(type="count", group_by=["type"])
        Aggregation(type="sum", field="lines", group_by=["language"])
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

    Contains matched entities, traversed relationships, and optional aggregations.
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
    total: int = Field(
        0,
        description="Total count of matched entities (before limit)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Query execution metadata (timing, depth reached, etc.)",
    )
