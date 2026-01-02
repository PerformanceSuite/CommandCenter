"""
IntentParser - Parse structured or natural language queries into ComposedQuery.

Phase 2, Task 2.2: Intent Parser Service

This service converts user input (structured dictionaries or natural language strings)
into a unified ComposedQuery representation that can be executed by the query engine.
"""

import logging
import re
from typing import Union

from app.schemas.query import ComposedQuery, EntitySelector, Filter, RelationshipSpec

logger = logging.getLogger(__name__)


class IntentParser:
    """Parse structured or natural language queries into ComposedQuery.

    Supports two input modes:
    1. Structured dict: {"entity": "symbol:name", "context": ["dependencies"], "depth": 2}
    2. Natural language: "Show me all services with health below 100%"

    Examples:
        >>> parser = IntentParser()
        >>> result = parser.parse({"entity": "symbol:main", "context": ["callers"]})
        >>> result.entities[0].type
        'symbol'

        >>> result = parser.parse("services with health below 80")
        >>> result.filters[0].field
        'health'
    """

    # Entity type detection patterns for natural language
    # Order matters! More specific patterns (symbol) should come before less specific (service)
    # because "methods in user service" should match "methods" -> symbol, not "service"
    ENTITY_PATTERNS: list[tuple[str, str]] = [
        # Symbol patterns first (function, symbol, method are more specific)
        ("symbol", r"\bfunctions?\b|\bsymbols?\b|\bmethods?\b"),
        # Then other entity types in order of specificity
        ("file", r"\bfiles?\b"),
        ("project", r"\bprojects?\b"),
        ("task", r"\btasks?\b"),
        ("spec", r"\bspecs?\b|\bspecifications?\b"),
        ("workflow", r"\bworkflows?\b"),
        ("execution", r"\bexecutions?\b"),
        # Service last since it's a common word in many contexts
        ("service", r"\bservices?\b"),
    ]

    # Filter patterns: (regex_pattern, field_name, operator)
    # Group 1 is the operator keyword, group 2 is the value
    FILTER_PATTERNS: list[tuple[str, str, str]] = [
        # Health comparisons
        (r"health\s*(?:below|under|<)\s*(\d+)", "health", "lt"),
        (r"health\s*(?:above|over|>)\s*(\d+)", "health", "gt"),
        (r"health\s*(?:=|equals?|==)\s*(\d+)", "health", "eq"),
        # Status comparisons
        (r"status\s*(?:=|equals?|==|is)\s*['\"]?(\w+)['\"]?", "status", "eq"),
        (r"status\s*!=\s*['\"]?(\w+)['\"]?", "status", "ne"),
    ]

    # Context to relationship type mapping
    CONTEXT_MAPPINGS: dict[str, tuple[str, str]] = {
        "dependencies": ("dependency", "outbound"),
        "dependency": ("dependency", "outbound"),
        "callers": ("caller", "inbound"),
        "caller": ("caller", "inbound"),
        "imports": ("import", "outbound"),
        "import": ("import", "outbound"),
        "references": ("reference", "both"),
        "reference": ("reference", "both"),
        "implementations": ("implementation", "outbound"),
        "implementation": ("implementation", "outbound"),
    }

    def parse(self, query: Union[dict, str]) -> ComposedQuery:
        """Parse a query into a ComposedQuery object.

        Args:
            query: Either a structured dict or natural language string

        Returns:
            ComposedQuery object ready for execution
        """
        if isinstance(query, dict):
            return self._parse_structured(query)
        return self._parse_natural_language(query)

    def _parse_structured(self, query: dict) -> ComposedQuery:
        """Parse a structured dictionary query.

        Expected format:
        {
            "entity": "type:id" or "type",
            "context": ["dependencies", "callers", ...],
            "depth": 2
        }
        """
        entities = []
        relationships = []

        # Parse entity reference
        entity_ref = query.get("entity", "")
        if entity_ref:
            if ":" in entity_ref:
                entity_type, entity_id = entity_ref.split(":", 1)
                entities.append(
                    EntitySelector(
                        type=entity_type,
                        id=entity_id if entity_id else None,
                    )
                )
            else:
                entities.append(EntitySelector(type=entity_ref))
        else:
            # No entity specified - use 'any'
            entities.append(EntitySelector(type="any"))

        # Parse context into relationship specifications
        context_list = query.get("context", [])
        depth = query.get("depth", 1)

        for ctx in context_list:
            ctx_lower = ctx.lower()
            if ctx_lower in self.CONTEXT_MAPPINGS:
                rel_type, direction = self.CONTEXT_MAPPINGS[ctx_lower]
                relationships.append(
                    RelationshipSpec(
                        type=rel_type,
                        direction=direction,
                        depth=depth,
                    )
                )
            else:
                # Unknown context - treat as generic relationship
                logger.warning(f"Unknown context type: {ctx}, treating as outbound relationship")
                relationships.append(
                    RelationshipSpec(
                        type=ctx.rstrip("s"),  # Remove trailing 's' if present
                        direction="outbound",
                        depth=depth,
                    )
                )

        return ComposedQuery(
            entities=entities,
            relationships=relationships if relationships else None,
        )

    def _parse_natural_language(self, query: str) -> ComposedQuery:
        """Parse a natural language query string.

        Uses pattern matching to detect:
        - Entity types (service, symbol, file, etc.)
        - Filter conditions (health below X, status = Y)
        """
        entities = []
        filters = []

        # Handle empty or whitespace-only queries
        query_stripped = query.strip()
        if not query_stripped:
            return ComposedQuery(entities=[EntitySelector(type="any")])

        # Detect entity types (first match wins - order matters!)
        entity_type = "any"
        for etype, pattern in self.ENTITY_PATTERNS:
            if re.search(pattern, query_stripped, re.IGNORECASE):
                entity_type = etype
                break

        entities.append(EntitySelector(type=entity_type))

        # Detect filter conditions
        for pattern, field, operator in self.FILTER_PATTERNS:
            match = re.search(pattern, query_stripped, re.IGNORECASE)
            if match:
                value_str = match.group(1)
                # Convert numeric strings to integers
                filter_value: int | str = int(value_str) if value_str.isdigit() else value_str
                filters.append(
                    Filter(
                        field=field,
                        operator=operator,
                        value=filter_value,
                    )
                )

        return ComposedQuery(
            entities=entities,
            filters=filters if filters else None,
        )
