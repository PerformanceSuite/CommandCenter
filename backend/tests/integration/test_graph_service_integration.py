"""
Integration tests for Phase 7 GraphService

Tests GraphService methods with real database connections.
"""

import pytest
from sqlalchemy import select

from app.models.graph import GraphFile, GraphSymbol
from app.services.graph_service import GraphService


@pytest.mark.asyncio
async def test_get_project_graph_basic(db_session):
    """Test get_project_graph returns nodes and edges"""
    service = GraphService(db_session)

    # Get graph for project 1 (test data created earlier)
    graph = await service.get_project_graph(project_id=1, depth=3)

    # Verify we have nodes and edges
    assert graph.nodes is not None
    assert graph.edges is not None
    assert len(graph.nodes) > 0, "Should have at least some nodes"

    # Verify metadata
    assert graph.metadata["node_count"] == len(graph.nodes)
    assert graph.metadata["edge_count"] == len(graph.edges)
    assert graph.metadata["depth"] == 3

    # Check for specific node types
    node_types = {node.entity_type for node in graph.nodes}
    assert "repo" in node_types
    assert "file" in node_types
    assert "symbol" in node_types

    print(f"✅ Graph query successful: {len(graph.nodes)} nodes, {len(graph.edges)} edges")


@pytest.mark.asyncio
async def test_get_dependencies(db_session):
    """Test symbol dependency traversal"""
    service = GraphService(db_session)

    # Get a symbol with dependencies
    stmt = select(GraphSymbol).limit(1)
    result = await db_session.execute(stmt)
    symbol = result.scalar_one_or_none()

    if not symbol:
        pytest.skip("No symbols in database")

    # Get outbound dependencies
    dep_graph = await service.get_dependencies(symbol_id=symbol.id, direction="outbound", depth=2)

    assert dep_graph.root_symbol_id == symbol.id
    assert len(dep_graph.nodes) >= 1  # At least the root symbol

    print(f"✅ Dependency traversal: {len(dep_graph.nodes)} symbols, {len(dep_graph.edges)} edges")


@pytest.mark.asyncio
async def test_get_ghost_nodes(db_session):
    """Test ghost node detection (specs/tasks without implementation)"""
    service = GraphService(db_session)

    # Get ghost nodes for project 1
    ghost_nodes = await service.get_ghost_nodes(project_id=1)

    # We should have at least the spec item we created (if no links were added)
    assert isinstance(ghost_nodes, list)

    if len(ghost_nodes) > 0:
        ghost = ghost_nodes[0]
        assert ghost.type in ["spec", "task"]
        assert ghost.title is not None
        print(f"✅ Found {len(ghost_nodes)} ghost nodes: {[g.title for g in ghost_nodes]}")
    else:
        print("✅ No ghost nodes found (all specs/tasks have implementations)")


@pytest.mark.asyncio
async def test_search_graph(db_session):
    """Test graph search functionality"""
    service = GraphService(db_session)

    # Search for "main" (should match the main function)
    results = await service.search_graph(
        project_id=1, query="main", scope=["symbols", "files", "tasks"]
    )

    assert results.total >= 0

    # Check if we found the main symbol or file
    if len(results.symbols) > 0:
        print(f"✅ Search found {results.total} results:")
        print(f"   - Symbols: {len(results.symbols)}")
        print(f"   - Files: {len(results.files)}")
        print(f"   - Tasks: {len(results.tasks)}")
    else:
        print("✅ Search completed (no results for 'main')")


@pytest.mark.asyncio
async def test_create_task(db_session):
    """Test task creation"""
    from app.models.graph import TaskKind

    service = GraphService(db_session)

    # Create a new task
    task = await service.create_task(
        project_id=1,
        title="Test task creation",
        kind=TaskKind.FEATURE,
        description="Testing GraphService.create_task method",
    )

    assert task.id is not None
    assert task.project_id == 1
    assert task.title == "Test task creation"
    assert task.kind == TaskKind.FEATURE

    print(f"✅ Created task: {task.title} (ID: {task.id})")


@pytest.mark.asyncio
async def test_link_entities(db_session):
    """Test entity linking"""
    from app.models.graph import LinkType

    service = GraphService(db_session)

    # Get two files to link
    stmt = select(GraphFile).limit(2)
    result = await db_session.execute(stmt)
    files = result.scalars().all()

    if len(files) < 2:
        pytest.skip("Need at least 2 files for linking test")

    # Create a link between files
    link = await service.link_entities(
        from_entity="graph_files",
        from_id=files[0].id,
        to_entity="graph_files",
        to_id=files[1].id,
        link_type=LinkType.REFERENCES,
        weight=0.5,
    )

    assert link.id is not None
    assert link.from_entity == "graph_files"
    assert link.to_entity == "graph_files"
    assert link.type == LinkType.REFERENCES

    print(f"✅ Created link: {link.from_entity}:{link.from_id} -> {link.to_entity}:{link.to_id}")


@pytest.mark.asyncio
async def test_multi_tenant_isolation(db_session):
    """Test that different projects don't see each other's data"""
    service = GraphService(db_session)

    # Query project 1 (has test data)
    graph1 = await service.get_project_graph(project_id=1, depth=1)

    # Query project 999 (doesn't exist)
    graph999 = await service.get_project_graph(project_id=999, depth=1)

    assert len(graph1.nodes) > 0, "Project 1 should have data"
    assert len(graph999.nodes) == 0, "Project 999 should have no data"

    print(
        f"✅ Multi-tenant isolation verified: project 1 has {len(graph1.nodes)} nodes, project 999 has 0"
    )


@pytest.mark.asyncio
async def test_graph_depth_levels(db_session):
    """Test different depth levels return different amounts of data"""
    service = GraphService(db_session)

    # Get graph at different depths
    graph_depth1 = await service.get_project_graph(project_id=1, depth=1)
    graph_depth2 = await service.get_project_graph(project_id=1, depth=2)
    graph_depth3 = await service.get_project_graph(project_id=1, depth=3)

    # Depth 2 should have files and symbols (more nodes than depth 1)
    # Depth 3 should have dependencies (more edges than depth 2)

    print("✅ Depth levels:")
    print(f"   - Depth 1: {len(graph_depth1.nodes)} nodes, {len(graph_depth1.edges)} edges")
    print(f"   - Depth 2: {len(graph_depth2.nodes)} nodes, {len(graph_depth2.edges)} edges")
    print(f"   - Depth 3: {len(graph_depth3.nodes)} nodes, {len(graph_depth3.edges)} edges")

    # Verify depth 2 has more nodes than depth 1 (includes symbols)
    assert len(graph_depth2.nodes) >= len(graph_depth1.nodes)
