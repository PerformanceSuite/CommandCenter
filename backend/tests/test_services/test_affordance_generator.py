"""
Tests for AffordanceGenerator service (Phase 3, Task 3.2)

The AffordanceGenerator produces available actions for entities,
enabling agent parity with the UI.
"""

import pytest

from app.services.affordance_generator import AffordanceGenerator


class TestAffordanceGenerator:
    """Test suite for AffordanceGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a generator instance."""
        return AffordanceGenerator()

    def test_generates_symbol_affordances(self, generator):
        """Test affordance generation for symbol entities."""
        entity = {"id": "123", "type": "symbol", "label": "validateToken"}

        affordances = generator.generate(entity)

        actions = [a.action for a in affordances]
        assert "trigger_audit" in actions
        assert "drill_down" in actions
        assert "open_in_editor" in actions
        assert "create_task" in actions
        assert "view_dependencies" in actions
        assert "view_callers" in actions

    def test_generates_file_affordances(self, generator):
        """Test affordance generation for file entities."""
        entity = {"id": "456", "type": "file", "label": "auth.py"}

        affordances = generator.generate(entity)

        actions = [a.action for a in affordances]
        assert "trigger_audit" in actions
        assert "drill_down" in actions
        assert "open_in_editor" in actions
        # Files don't have callers/dependencies in the same way
        assert "view_dependencies" not in actions

    def test_generates_service_affordances(self, generator):
        """Test affordance generation for service entities."""
        entity = {"id": "789", "type": "service", "label": "API Gateway"}

        affordances = generator.generate(entity)

        actions = [a.action for a in affordances]
        assert "trigger_audit" in actions
        assert "drill_down" in actions
        # Services can't be opened in editor
        assert "open_in_editor" not in actions

    def test_generates_task_affordances(self, generator):
        """Test affordance generation for task entities."""
        entity = {"id": "101", "type": "task", "label": "Implement auth"}

        affordances = generator.generate(entity)

        actions = [a.action for a in affordances]
        assert "drill_down" in actions
        # Can't audit a task
        assert "trigger_audit" not in actions

    def test_generates_repo_affordances(self, generator):
        """Test affordance generation for repo entities."""
        entity = {"id": "202", "type": "repo", "label": "myorg/myrepo"}

        affordances = generator.generate(entity)

        actions = [a.action for a in affordances]
        assert "drill_down" in actions
        assert "run_indexer" in actions
        assert "trigger_audit" in actions

    def test_affordance_target_references_entity(self, generator):
        """Test that affordances correctly reference the target entity."""
        entity = {"id": "123", "type": "symbol", "label": "myFunction"}

        affordances = generator.generate(entity)

        for affordance in affordances:
            assert affordance.target.type == "symbol"
            assert affordance.target.id == "123"

    def test_affordance_descriptions_are_meaningful(self, generator):
        """Test that affordance descriptions include entity info."""
        entity = {"id": "123", "type": "symbol", "label": "myFunction"}

        affordances = generator.generate(entity)

        for affordance in affordances:
            assert len(affordance.description) > 10
            # Description should reference the entity type or label
            assert (
                "symbol" in affordance.description.lower() or "myFunction" in affordance.description
            )

    def test_unknown_entity_type_gets_drill_down(self, generator):
        """Test that unknown entity types at least get drill_down."""
        entity = {"id": "999", "type": "unknown_type", "label": "Something"}

        affordances = generator.generate(entity)

        actions = [a.action for a in affordances]
        assert "drill_down" in actions

    def test_generate_for_entities_list(self, generator):
        """Test generating affordances for multiple entities."""
        entities = [
            {"id": "1", "type": "symbol", "label": "func1"},
            {"id": "2", "type": "file", "label": "main.py"},
            {"id": "3", "type": "service", "label": "API"},
        ]

        all_affordances = generator.generate_for_entities(entities)

        # Should have affordances for all entities
        assert len(all_affordances) > len(entities)

        # Check we have affordances referencing each entity
        entity_ids = {a.target.id for a in all_affordances}
        assert "1" in entity_ids
        assert "2" in entity_ids
        assert "3" in entity_ids

    def test_generate_for_entities_with_limit(self, generator):
        """Test that entity limit is respected."""
        entities = [{"id": str(i), "type": "symbol", "label": f"func{i}"} for i in range(20)]

        all_affordances = generator.generate_for_entities(entities, max_entities=5)

        # Should only have affordances for first 5 entities
        entity_ids = {a.target.id for a in all_affordances}
        assert len(entity_ids) <= 5
