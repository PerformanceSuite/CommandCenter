"""
Tests for Affordance schema (Phase 3, Task 3.1)

Affordances represent actions that can be taken on entities,
enabling agent parity with the UI.
"""


def test_affordance_schema():
    """Test basic affordance creation."""
    from app.schemas.query import Affordance, EntityRef

    affordance = Affordance(
        action="trigger_audit",
        target=EntityRef(type="symbol", id="123"),
        description="Run security audit on this function",
        parameters={"audit_type": "security"},
    )
    assert affordance.action == "trigger_audit"
    assert affordance.target.type == "symbol"
    assert affordance.target.id == "123"
    assert affordance.parameters == {"audit_type": "security"}


def test_entity_ref_schema():
    """Test EntityRef creation."""
    from app.schemas.query import EntityRef

    ref = EntityRef(type="file", id="456")
    assert ref.type == "file"
    assert ref.id == "456"


def test_affordance_without_parameters():
    """Test affordance creation without optional parameters."""
    from app.schemas.query import Affordance, EntityRef

    affordance = Affordance(
        action="drill_down",
        target=EntityRef(type="service", id="789"),
        description="Explore this service in detail",
    )
    assert affordance.action == "drill_down"
    assert affordance.parameters is None


def test_affordance_valid_actions():
    """Test all valid affordance actions."""
    from app.schemas.query import Affordance, EntityRef

    valid_actions = [
        "trigger_audit",
        "create_task",
        "open_in_editor",
        "drill_down",
        "run_indexer",
        "view_dependencies",
        "view_callers",
    ]

    for action in valid_actions:
        affordance = Affordance(
            action=action,
            target=EntityRef(type="symbol", id="1"),
            description=f"Test {action}",
        )
        assert affordance.action == action


def test_query_result_with_affordances():
    """Test that QueryResult can include affordances."""
    from app.schemas.query import Affordance, EntityRef, QueryResult

    affordances = [
        Affordance(
            action="trigger_audit",
            target=EntityRef(type="symbol", id="123"),
            description="Run audit",
        ),
        Affordance(
            action="drill_down",
            target=EntityRef(type="symbol", id="123"),
            description="View details",
        ),
    ]

    result = QueryResult(
        entities=[{"id": 123, "type": "symbol", "label": "myFunction"}],
        relationships=[],
        affordances=affordances,
        total=1,
    )

    assert result.affordances is not None
    assert len(result.affordances) == 2
    assert result.affordances[0].action == "trigger_audit"
    assert result.affordances[1].action == "drill_down"


def test_query_result_without_affordances():
    """Test QueryResult without affordances (backward compatibility)."""
    from app.schemas.query import QueryResult

    result = QueryResult(
        entities=[{"id": 1, "type": "file", "label": "main.py"}],
        relationships=[],
        total=1,
    )

    assert result.affordances is None
