"""Unit tests for Project model."""
import pytest
from app.models.project import Project


def test_project_model_edge_cases():
    """Project model handles edge cases."""
    # Empty name should raise error
    with pytest.raises(ValueError):
        Project(name="", owner="testowner", description="Test")

    # Very long name should be truncated or raise error
    long_name = "a" * 300
    project = Project(name=long_name, owner="testowner", description="Test")
    assert len(project.name) <= 255  # Assuming max length


def test_project_relationship_validation():
    """Project relationships are properly validated."""
    project = Project(name="Test Project", owner="testowner", description="Description")

    # Project should initialize with empty relationships
    assert project.technologies == []
    assert project.repositories == []
    assert project.research_tasks == []
