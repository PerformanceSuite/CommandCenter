"""
Tests for IntentParser service.

Phase 2, Task 2.2: Intent Parser Service

This module tests the IntentParser which converts both structured
dictionaries and natural language queries into ComposedQuery objects.
"""

from app.schemas.query import ComposedQuery
from app.services.intent_parser import IntentParser


class TestParseStructuredQuery:
    """Test structured (dict) query parsing."""

    def test_parse_entity_with_type_and_id(self):
        """Parse entity reference with type:id format."""
        parser = IntentParser()
        result = parser.parse(
            {
                "entity": "symbol:graph_service.get_project",
                "context": ["dependencies", "callers"],
                "depth": 2,
            }
        )

        assert isinstance(result, ComposedQuery)
        assert len(result.entities) == 1
        assert result.entities[0].type == "symbol"
        assert result.entities[0].id == "graph_service.get_project"

    def test_parse_context_as_relationships(self):
        """Parse context list into relationship specifications."""
        parser = IntentParser()
        result = parser.parse(
            {
                "entity": "symbol:main",
                "context": ["dependencies", "callers"],
                "depth": 2,
            }
        )

        assert result.relationships is not None
        assert len(result.relationships) == 2

        rel_types = [r.type for r in result.relationships]
        assert "dependency" in rel_types
        assert "caller" in rel_types

    def test_parse_relationship_directions(self):
        """Verify correct direction assignment for context types."""
        parser = IntentParser()
        result = parser.parse(
            {
                "entity": "symbol:test",
                "context": ["dependencies", "callers", "imports"],
            }
        )

        relationships = {r.type: r for r in result.relationships}

        # dependencies go outbound (things this depends on)
        assert relationships["dependency"].direction == "outbound"
        # callers come inbound (things that call this)
        assert relationships["caller"].direction == "inbound"
        # imports go outbound (things this imports)
        assert relationships["import"].direction == "outbound"

    def test_parse_depth_parameter(self):
        """Verify depth is applied to all relationships."""
        parser = IntentParser()
        result = parser.parse(
            {
                "entity": "file:main.py",
                "context": ["dependencies"],
                "depth": 3,
            }
        )

        assert all(r.depth == 3 for r in result.relationships)

    def test_parse_entity_without_id(self):
        """Parse entity reference without specific ID."""
        parser = IntentParser()
        result = parser.parse(
            {
                "entity": "service",
                "context": [],
            }
        )

        assert result.entities[0].type == "service"
        assert result.entities[0].id is None

    def test_parse_empty_context(self):
        """Parse query with empty context list."""
        parser = IntentParser()
        result = parser.parse(
            {
                "entity": "file:test.py",
                "context": [],
            }
        )

        assert result.relationships is None or len(result.relationships) == 0


class TestParseNaturalLanguageQuery:
    """Test natural language query parsing."""

    def test_parse_service_query_with_health_filter(self):
        """Parse NL query for services with health below threshold."""
        parser = IntentParser()
        result = parser.parse("Show me all services with health below 100%")

        assert isinstance(result, ComposedQuery)
        assert result.entities[0].type == "service"
        assert result.filters is not None
        assert any(f.field == "health" for f in result.filters)

    def test_parse_health_below_filter(self):
        """Verify 'below' translates to 'lt' operator."""
        parser = IntentParser()
        result = parser.parse("services with health below 80")

        health_filter = next((f for f in result.filters if f.field == "health"), None)
        assert health_filter is not None
        assert health_filter.operator == "lt"
        assert health_filter.value == 80

    def test_parse_health_above_filter(self):
        """Verify 'above' translates to 'gt' operator."""
        parser = IntentParser()
        result = parser.parse("services with health above 90")

        health_filter = next((f for f in result.filters if f.field == "health"), None)
        assert health_filter is not None
        assert health_filter.operator == "gt"
        assert health_filter.value == 90

    def test_parse_status_equals_filter(self):
        """Parse status equality filter."""
        parser = IntentParser()
        result = parser.parse("services with status = healthy")

        status_filter = next((f for f in result.filters if f.field == "status"), None)
        assert status_filter is not None
        assert status_filter.operator == "eq"
        assert status_filter.value == "healthy"

    def test_detect_symbol_entity_from_function_keyword(self):
        """Detect symbol entity type from 'function' keyword."""
        parser = IntentParser()
        result = parser.parse("find all functions that call auth")

        assert result.entities[0].type == "symbol"

    def test_detect_symbol_entity_from_method_keyword(self):
        """Detect symbol entity type from 'method' keyword."""
        parser = IntentParser()
        result = parser.parse("show methods in user service")

        assert result.entities[0].type == "symbol"

    def test_detect_file_entity(self):
        """Detect file entity type."""
        parser = IntentParser()
        result = parser.parse("list all files in the project")

        assert result.entities[0].type == "file"

    def test_detect_project_entity(self):
        """Detect project entity type."""
        parser = IntentParser()
        result = parser.parse("show all projects")

        assert result.entities[0].type == "project"

    def test_fallback_to_any_entity_type(self):
        """Use 'any' entity type when no specific type detected."""
        parser = IntentParser()
        result = parser.parse("search for authentication")

        assert result.entities[0].type == "any"

    def test_parse_empty_filters_when_no_filter_patterns_match(self):
        """Return None for filters when no filter patterns match."""
        parser = IntentParser()
        result = parser.parse("show all services")

        # No health/status filters in this query
        assert result.filters is None or len(result.filters) == 0


class TestParseEdgeCases:
    """Test edge cases and error handling."""

    def test_parse_empty_string_query(self):
        """Handle empty string query gracefully."""
        parser = IntentParser()
        result = parser.parse("")

        assert isinstance(result, ComposedQuery)
        assert result.entities[0].type == "any"

    def test_parse_whitespace_only_query(self):
        """Handle whitespace-only query."""
        parser = IntentParser()
        result = parser.parse("   \n\t  ")

        assert isinstance(result, ComposedQuery)
        assert result.entities[0].type == "any"

    def test_parse_dict_without_entity(self):
        """Handle dict query without entity key."""
        parser = IntentParser()
        result = parser.parse({"context": ["dependencies"]})

        assert isinstance(result, ComposedQuery)
        assert result.entities[0].type == "any"

    def test_parse_case_insensitive_entity_detection(self):
        """Entity detection should be case insensitive."""
        parser = IntentParser()

        result1 = parser.parse("Show SERVICES")
        result2 = parser.parse("show services")
        result3 = parser.parse("Show Services")

        assert result1.entities[0].type == "service"
        assert result2.entities[0].type == "service"
        assert result3.entities[0].type == "service"

    def test_parse_case_insensitive_filter_detection(self):
        """Filter detection should be case insensitive."""
        parser = IntentParser()

        result1 = parser.parse("services with HEALTH below 50")
        result2 = parser.parse("services with Health Below 50")

        assert result1.filters is not None
        assert result2.filters is not None
        assert result1.filters[0].field == "health"
        assert result2.filters[0].field == "health"


class TestParseMultipleFilters:
    """Test queries with multiple filter conditions."""

    def test_parse_multiple_health_filters(self):
        """Parse query with multiple health conditions."""
        parser = IntentParser()
        # This tests both operators in one query
        result = parser.parse("services with health above 50 and health below 100")

        # Should detect at least one health filter
        assert result.filters is not None
        health_filters = [f for f in result.filters if f.field == "health"]
        assert len(health_filters) >= 1


class TestIntentParserIntegration:
    """Integration tests for common use cases."""

    def test_full_structured_query_workflow(self):
        """Test a complete structured query parsing workflow."""
        parser = IntentParser()
        result = parser.parse(
            {
                "entity": "symbol:app.services.graph_service.GraphService",
                "context": ["dependencies", "callers"],
                "depth": 2,
            }
        )

        # Verify complete result
        assert result.entities[0].type == "symbol"
        assert result.entities[0].id == "app.services.graph_service.GraphService"
        assert len(result.relationships) == 2
        assert all(r.depth == 2 for r in result.relationships)

    def test_full_nl_query_workflow(self):
        """Test a complete natural language query parsing workflow."""
        parser = IntentParser()
        result = parser.parse("Show me services with health below 80%")

        # Verify complete result
        assert result.entities[0].type == "service"
        assert result.filters is not None
        health_filter = next(f for f in result.filters if f.field == "health")
        assert health_filter.operator == "lt"
        assert health_filter.value == 80
