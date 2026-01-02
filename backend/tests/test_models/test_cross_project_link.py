# backend/tests/test_models/test_cross_project_link.py
"""Tests for CrossProjectLink model."""
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.graph import CrossProjectLink
from app.models.project import Project


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_projects(db_session):
    """Create two test projects for cross-project linking."""
    project1 = Project(name="Project Alpha", owner="testowner")
    project2 = Project(name="Project Beta", owner="testowner")
    db_session.add(project1)
    db_session.add(project2)
    db_session.commit()
    return project1, project2


def test_cross_project_link_creation(db_session, test_projects):
    """Test CrossProjectLink can be created with all required fields."""
    project1, project2 = test_projects

    link = CrossProjectLink(
        source_project_id=project1.id,
        source_entity_type="symbol",
        source_entity_id=100,
        target_project_id=project2.id,
        target_entity_type="symbol",
        target_entity_id=200,
        relationship_type="calls",
    )
    db_session.add(link)
    db_session.commit()

    assert link.id is not None
    assert link.source_project_id == project1.id
    assert link.target_project_id == project2.id
    assert link.source_entity_type == "symbol"
    assert link.source_entity_id == 100
    assert link.target_entity_type == "symbol"
    assert link.target_entity_id == 200
    assert link.relationship_type == "calls"
    assert link.discovered_at is not None
    assert link.updated_at is not None


def test_cross_project_link_with_metadata(db_session, test_projects):
    """Test CrossProjectLink can store optional metadata."""
    project1, project2 = test_projects

    metadata = {
        "version": "1.0",
        "confidence": 0.95,
        "discovered_by": "static_analysis",
    }

    link = CrossProjectLink(
        source_project_id=project1.id,
        source_entity_type="service",
        source_entity_id=10,
        target_project_id=project2.id,
        target_entity_type="service",
        target_entity_id=20,
        relationship_type="consumes_api",
        metadata_=metadata,
    )
    db_session.add(link)
    db_session.commit()

    result = db_session.query(CrossProjectLink).filter_by(id=link.id).first()
    assert result.metadata_ == metadata
    assert result.metadata_["confidence"] == 0.95


def test_cross_project_link_repr():
    """Test CrossProjectLink has informative repr."""
    link = CrossProjectLink(
        id=42,
        source_project_id=1,
        source_entity_type="service",
        source_entity_id=10,
        target_project_id=2,
        target_entity_type="service",
        target_entity_id=20,
        relationship_type="depends_on",
    )
    repr_str = repr(link)

    assert "CrossProjectLink" in repr_str
    assert "depends_on" in repr_str
    assert "service:10@1" in repr_str
    assert "service:20@2" in repr_str


def test_cross_project_link_timestamps_default(db_session, test_projects):
    """Test that timestamps are set automatically."""
    project1, project2 = test_projects
    before = datetime.utcnow()

    link = CrossProjectLink(
        source_project_id=project1.id,
        source_entity_type="file",
        source_entity_id=1,
        target_project_id=project2.id,
        target_entity_type="file",
        target_entity_id=2,
        relationship_type="imports",
    )
    db_session.add(link)
    db_session.commit()

    after = datetime.utcnow()

    assert link.discovered_at >= before
    assert link.discovered_at <= after
    assert link.updated_at >= before
    assert link.updated_at <= after


def test_cross_project_link_multiple_relationship_types(db_session, test_projects):
    """Test various relationship types can be stored."""
    project1, project2 = test_projects

    relationship_types = [
        "depends_on",
        "imports",
        "calls",
        "extends",
        "implements",
        "shares_library",
        "consumes_api",
        "produces_event",
    ]

    for i, rel_type in enumerate(relationship_types):
        link = CrossProjectLink(
            source_project_id=project1.id,
            source_entity_type="symbol",
            source_entity_id=i,
            target_project_id=project2.id,
            target_entity_type="symbol",
            target_entity_id=i + 100,
            relationship_type=rel_type,
        )
        db_session.add(link)

    db_session.commit()

    all_links = db_session.query(CrossProjectLink).all()
    assert len(all_links) == len(relationship_types)

    stored_types = {link.relationship_type for link in all_links}
    assert stored_types == set(relationship_types)
