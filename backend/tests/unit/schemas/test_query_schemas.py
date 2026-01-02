"""
Unit tests for ComposedQuery Pydantic schemas

TDD: Write failing tests first, then implement the schema.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.query import ComposedQuery, EntitySelector, Filter, RelationshipSpec, TimeRange


@pytest.mark.unit
class TestEntitySelector:
    """Test EntitySelector schema validation"""

    def test_entity_selector_basic(self):
        """Test EntitySelector with basic fields"""
        selector = EntitySelector(type="symbol", scope="project:abc")
        assert selector.type == "symbol"
        assert selector.scope == "project:abc"
        assert selector.constraints is None

    def test_entity_selector_with_constraints(self):
        """Test EntitySelector with constraints"""
        selector = EntitySelector(
            type="file",
            scope="ecosystem",
            constraints={"lang": "python", "path_prefix": "/src"},
        )
        assert selector.type == "file"
        assert selector.scope == "ecosystem"
        assert selector.constraints == {"lang": "python", "path_prefix": "/src"}

    def test_entity_selector_minimal(self):
        """Test EntitySelector with only required type field"""
        selector = EntitySelector(type="service")
        assert selector.type == "service"
        assert selector.scope is None
        assert selector.constraints is None

    def test_entity_selector_requires_type(self):
        """Test that EntitySelector requires type field"""
        with pytest.raises(ValidationError) as exc_info:
            EntitySelector()
        assert "type" in str(exc_info.value)


@pytest.mark.unit
class TestFilter:
    """Test Filter schema validation"""

    def test_filter_basic(self):
        """Test Filter with basic comparison"""
        f = Filter(field="health", operator="lt", value=100)
        assert f.field == "health"
        assert f.operator == "lt"
        assert f.value == 100

    def test_filter_string_value(self):
        """Test Filter with string value"""
        f = Filter(field="status", operator="eq", value="active")
        assert f.field == "status"
        assert f.operator == "eq"
        assert f.value == "active"

    def test_filter_list_value_for_in_operator(self):
        """Test Filter with list value for 'in' operator"""
        f = Filter(field="lang", operator="in", value=["python", "typescript"])
        assert f.operator == "in"
        assert f.value == ["python", "typescript"]

    def test_filter_all_operators(self):
        """Test all valid filter operators"""
        operators = ["eq", "ne", "lt", "gt", "lte", "gte", "in", "contains"]
        for op in operators:
            f = Filter(field="test", operator=op, value="val")
            assert f.operator == op

    def test_filter_invalid_operator(self):
        """Test Filter rejects invalid operator"""
        with pytest.raises(ValidationError) as exc_info:
            Filter(field="test", operator="invalid", value=1)
        assert "operator" in str(exc_info.value)

    def test_filter_requires_all_fields(self):
        """Test Filter requires field, operator, and value"""
        with pytest.raises(ValidationError):
            Filter(field="test", operator="eq")  # missing value
        with pytest.raises(ValidationError):
            Filter(field="test", value=1)  # missing operator
        with pytest.raises(ValidationError):
            Filter(operator="eq", value=1)  # missing field


@pytest.mark.unit
class TestRelationshipSpec:
    """Test RelationshipSpec schema validation"""

    def test_relationship_spec_basic(self):
        """Test RelationshipSpec with minimal fields"""
        rel = RelationshipSpec(type="calls")
        assert rel.type == "calls"
        assert rel.direction == "both"  # default
        assert rel.depth == 1  # default

    def test_relationship_spec_full(self):
        """Test RelationshipSpec with all fields"""
        rel = RelationshipSpec(type="imports", direction="inbound", depth=3)
        assert rel.type == "imports"
        assert rel.direction == "inbound"
        assert rel.depth == 3

    def test_relationship_spec_direction_options(self):
        """Test all valid direction options"""
        for direction in ["inbound", "outbound", "both"]:
            rel = RelationshipSpec(type="depends_on", direction=direction)
            assert rel.direction == direction

    def test_relationship_spec_invalid_direction(self):
        """Test RelationshipSpec rejects invalid direction"""
        with pytest.raises(ValidationError) as exc_info:
            RelationshipSpec(type="calls", direction="sideways")
        assert "direction" in str(exc_info.value)


@pytest.mark.unit
class TestTimeRange:
    """Test TimeRange schema validation"""

    def test_time_range_both_bounds(self):
        """Test TimeRange with both start and end"""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 12, 31, tzinfo=timezone.utc)
        tr = TimeRange(start=start, end=end)
        assert tr.start == start
        assert tr.end == end

    def test_time_range_start_only(self):
        """Test TimeRange with only start"""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        tr = TimeRange(start=start)
        assert tr.start == start
        assert tr.end is None

    def test_time_range_end_only(self):
        """Test TimeRange with only end"""
        end = datetime(2024, 12, 31, tzinfo=timezone.utc)
        tr = TimeRange(end=end)
        assert tr.start is None
        assert tr.end == end

    def test_time_range_empty(self):
        """Test TimeRange with no bounds (open range)"""
        tr = TimeRange()
        assert tr.start is None
        assert tr.end is None


@pytest.mark.unit
class TestComposedQuery:
    """Test ComposedQuery schema validation"""

    def test_composed_query_from_structured(self):
        """Test ComposedQuery creation from structured data"""
        query = ComposedQuery(
            entities=[EntitySelector(type="symbol", scope="project:abc")],
            filters=[Filter(field="health", operator="lt", value=100)],
            presentation={"layout": "graph", "depth": 2},
        )
        assert len(query.entities) == 1
        assert query.entities[0].type == "symbol"
        assert query.filters is not None
        assert len(query.filters) == 1
        assert query.presentation == {"layout": "graph", "depth": 2}

    def test_composed_query_multiple_entities(self):
        """Test ComposedQuery with multiple entity selectors"""
        query = ComposedQuery(
            entities=[
                EntitySelector(type="symbol", scope="project:abc"),
                EntitySelector(type="file", constraints={"lang": "python"}),
                EntitySelector(type="service"),
            ]
        )
        assert len(query.entities) == 3
        assert query.entities[0].type == "symbol"
        assert query.entities[1].type == "file"
        assert query.entities[2].type == "service"

    def test_composed_query_with_relationships(self):
        """Test ComposedQuery with relationship specifications"""
        query = ComposedQuery(
            entities=[EntitySelector(type="symbol")],
            relationships=[
                RelationshipSpec(type="calls", direction="outbound", depth=2),
                RelationshipSpec(type="imports"),
            ],
        )
        assert query.relationships is not None
        assert len(query.relationships) == 2
        assert query.relationships[0].type == "calls"
        assert query.relationships[0].depth == 2

    def test_composed_query_with_time_range(self):
        """Test ComposedQuery with time range"""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        query = ComposedQuery(
            entities=[EntitySelector(type="symbol")],
            time_range=TimeRange(start=start),
        )
        assert query.time_range is not None
        assert query.time_range.start == start

    def test_composed_query_full(self):
        """Test ComposedQuery with all fields populated"""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 12, 31, tzinfo=timezone.utc)

        query = ComposedQuery(
            entities=[
                EntitySelector(type="symbol", scope="project:xyz"),
                EntitySelector(type="file"),
            ],
            filters=[
                Filter(field="health", operator="gte", value=80),
                Filter(field="lang", operator="in", value=["python", "go"]),
            ],
            relationships=[
                RelationshipSpec(type="depends_on", direction="both", depth=3),
            ],
            presentation={"layout": "force", "show_labels": True},
            time_range=TimeRange(start=start, end=end),
        )

        assert len(query.entities) == 2
        assert len(query.filters) == 2
        assert len(query.relationships) == 1
        assert query.presentation["layout"] == "force"
        assert query.time_range.start == start
        assert query.time_range.end == end

    def test_composed_query_minimal(self):
        """Test ComposedQuery with only required fields"""
        query = ComposedQuery(entities=[EntitySelector(type="project")])
        assert len(query.entities) == 1
        assert query.filters is None
        assert query.relationships is None
        assert query.presentation is None
        assert query.time_range is None

    def test_composed_query_requires_entities(self):
        """Test that ComposedQuery requires at least one entity"""
        with pytest.raises(ValidationError):
            ComposedQuery(entities=[])

    def test_composed_query_requires_entities_field(self):
        """Test that ComposedQuery requires entities field"""
        with pytest.raises(ValidationError) as exc_info:
            ComposedQuery()
        assert "entities" in str(exc_info.value)
