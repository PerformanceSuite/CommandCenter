"""
AffordanceGenerator - Generate available actions for entities.

Phase 3, Task 3.2: Affordance Generator

This service generates the list of actions (affordances) that can be taken
on graph entities, enabling agent parity with the UI. Any action a user
can take in the interface, an agent can also invoke via the API.
"""

from typing import Any

from app.schemas.query import Affordance, EntityRef


class AffordanceGenerator:
    """Generate available actions for entities.

    Affordances are actions that can be taken on entities. This generator
    maps entity types to their applicable actions, creating fully-specified
    Affordance objects that agents can execute via the action API.

    Examples:
        >>> generator = AffordanceGenerator()
        >>> entity = {"id": "123", "type": "symbol", "label": "myFunction"}
        >>> affordances = generator.generate(entity)
        >>> print([a.action for a in affordances])
        ['trigger_audit', 'drill_down', 'open_in_editor', ...]
    """

    # Map entity types to their available actions
    ENTITY_AFFORDANCES: dict[str, list[str]] = {
        "symbol": [
            "trigger_audit",
            "drill_down",
            "open_in_editor",
            "create_task",
            "view_dependencies",
            "view_callers",
        ],
        "file": [
            "trigger_audit",
            "drill_down",
            "open_in_editor",
            "create_task",
        ],
        "service": [
            "trigger_audit",
            "drill_down",
        ],
        "task": [
            "drill_down",
        ],
        "spec": [
            "drill_down",
            "create_task",
        ],
        "repo": [
            "drill_down",
            "run_indexer",
            "trigger_audit",
        ],
    }

    # Human-readable descriptions for each action
    ACTION_DESCRIPTIONS: dict[str, str] = {
        "trigger_audit": "Run code analysis on this {type}",
        "drill_down": "Explore {label} in detail",
        "open_in_editor": "Open {label} in your editor",
        "create_task": "Create a task related to {label}",
        "run_indexer": "Re-index this {type}",
        "view_dependencies": "View dependencies of {label}",
        "view_callers": "View callers of {label}",
    }

    def generate(self, entity: dict[str, Any]) -> list[Affordance]:
        """Generate affordances for a single entity.

        Args:
            entity: Entity dict with at least 'id', 'type', and 'label' keys

        Returns:
            List of Affordance objects for the entity
        """
        entity_type = entity.get("type", "unknown")
        entity_id = str(entity.get("id", ""))
        entity_label = entity.get("label", entity_id)

        # Get actions for this entity type, defaulting to just drill_down
        actions = self.ENTITY_AFFORDANCES.get(entity_type, ["drill_down"])

        affordances = []
        for action in actions:
            description = self.ACTION_DESCRIPTIONS.get(
                action,
                f"Perform {action} on {entity_label}",
            ).format(type=entity_type, label=entity_label)

            affordances.append(
                Affordance(
                    action=action,
                    target=EntityRef(type=entity_type, id=entity_id),
                    description=description,
                )
            )

        return affordances

    def generate_for_entities(
        self,
        entities: list[dict[str, Any]],
        max_entities: int = 10,
    ) -> list[Affordance]:
        """Generate affordances for multiple entities.

        To avoid response bloat, only generates affordances for
        the first max_entities entities.

        Args:
            entities: List of entity dicts
            max_entities: Maximum number of entities to generate affordances for

        Returns:
            Combined list of affordances for all entities (up to limit)
        """
        all_affordances = []
        for entity in entities[:max_entities]:
            all_affordances.extend(self.generate(entity))
        return all_affordances
