"""
Tests for projects.yaml Pydantic validation

Validates that the config schema correctly enforces:
- Required fields
- Field format (slug, mesh_namespace, hub_url)
- Unique slugs across projects
- Tag and allow_fanout list validation
"""
import pytest
from pydantic import ValidationError
from app.schemas.config import ProjectConfig, ProjectsConfig


def test_project_config_valid():
    """Test valid project configuration."""
    config = ProjectConfig(
        slug="commandcenter",
        name="CommandCenter",
        hub_url="http://localhost:8000",
        mesh_namespace="hub.commandcenter",
        tags=["python", "fastapi"],
        allow_fanout=[]
    )

    assert config.slug == "commandcenter"
    assert config.name == "CommandCenter"
    assert config.hub_url == "http://localhost:8000"
    assert config.mesh_namespace == "hub.commandcenter"
    assert config.tags == ["python", "fastapi"]


def test_project_config_missing_required_field():
    """Test that missing required fields raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectConfig(
            slug="commandcenter",
            name="CommandCenter",
            # Missing hub_url
            mesh_namespace="hub.commandcenter"
        )

    assert "hub_url" in str(exc_info.value)


def test_project_config_invalid_slug():
    """Test that invalid slug format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectConfig(
            slug="invalid slug!",  # Contains space and special char
            name="Invalid",
            hub_url="http://localhost:8000",
            mesh_namespace="hub.invalid-slug"
        )

    assert "alphanumeric" in str(exc_info.value).lower()


def test_project_config_slug_normalized_to_lowercase():
    """Test that slug is normalized to lowercase."""
    config = ProjectConfig(
        slug="CommandCenter",
        name="CommandCenter",
        hub_url="http://localhost:8000",
        mesh_namespace="hub.commandcenter"
    )

    assert config.slug == "commandcenter"


def test_project_config_invalid_hub_url():
    """Test that invalid hub_url format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectConfig(
            slug="commandcenter",
            name="CommandCenter",
            hub_url="not-a-url",  # Missing http:// or https://
            mesh_namespace="hub.commandcenter"
        )

    assert "hub_url" in str(exc_info.value)


def test_project_config_mesh_namespace_mismatch():
    """Test that mesh_namespace must match slug."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectConfig(
            slug="commandcenter",
            name="CommandCenter",
            hub_url="http://localhost:8000",
            mesh_namespace="hub.different-project"  # Mismatch!
        )

    assert "mesh_namespace must be 'hub.commandcenter'" in str(exc_info.value)


def test_project_config_invalid_mesh_namespace_format():
    """Test that mesh_namespace must follow hub.<slug> pattern."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectConfig(
            slug="commandcenter",
            name="CommandCenter",
            hub_url="http://localhost:8000",
            mesh_namespace="invalid.namespace"  # Must start with "hub."
        )

    assert "pattern" in str(exc_info.value).lower()


def test_project_config_empty_tag_rejected():
    """Test that empty tags are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectConfig(
            slug="commandcenter",
            name="CommandCenter",
            hub_url="http://localhost:8000",
            mesh_namespace="hub.commandcenter",
            tags=["python", ""]  # Empty tag
        )

    assert "non-empty" in str(exc_info.value)


def test_project_config_invalid_allow_fanout_slug():
    """Test that allow_fanout slugs must be valid."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectConfig(
            slug="commandcenter",
            name="CommandCenter",
            hub_url="http://localhost:8000",
            mesh_namespace="hub.commandcenter",
            allow_fanout=["invalid slug!"]  # Invalid slug
        )

    assert "allow_fanout" in str(exc_info.value)


def test_projects_config_valid():
    """Test valid projects configuration."""
    config = ProjectsConfig(
        projects=[
            {
                "slug": "project1",
                "name": "Project 1",
                "hub_url": "http://localhost:8001",
                "mesh_namespace": "hub.project1",
                "tags": ["tag1"],
                "allow_fanout": []
            },
            {
                "slug": "project2",
                "name": "Project 2",
                "hub_url": "http://localhost:8002",
                "mesh_namespace": "hub.project2",
                "tags": ["tag2"],
                "allow_fanout": []
            }
        ]
    )

    assert len(config.projects) == 2
    assert config.projects[0].slug == "project1"
    assert config.projects[1].slug == "project2"


def test_projects_config_empty_list_allowed():
    """Test that empty projects list is allowed."""
    config = ProjectsConfig(projects=[])
    assert len(config.projects) == 0


def test_projects_config_duplicate_slugs_rejected():
    """Test that duplicate slugs are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectsConfig(
            projects=[
                {
                    "slug": "commandcenter",
                    "name": "Project 1",
                    "hub_url": "http://localhost:8001",
                    "mesh_namespace": "hub.commandcenter",
                },
                {
                    "slug": "commandcenter",  # Duplicate!
                    "name": "Project 2",
                    "hub_url": "http://localhost:8002",
                    "mesh_namespace": "hub.commandcenter",
                }
            ]
        )

    assert "duplicate" in str(exc_info.value).lower()
    assert "commandcenter" in str(exc_info.value)


def test_projects_config_invalid_nested_project():
    """Test that validation propagates to nested projects."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectsConfig(
            projects=[
                {
                    "slug": "valid-project",
                    "name": "Valid",
                    "hub_url": "http://localhost:8001",
                    "mesh_namespace": "hub.valid-project",
                },
                {
                    "slug": "invalid project!",  # Invalid slug in nested project
                    "name": "Invalid",
                    "hub_url": "http://localhost:8002",
                    "mesh_namespace": "hub.invalid-project",
                }
            ]
        )

    assert "alphanumeric" in str(exc_info.value).lower()


def test_projects_config_defaults():
    """Test that optional fields have correct defaults."""
    config = ProjectsConfig(
        projects=[
            {
                "slug": "minimal",
                "name": "Minimal Project",
                "hub_url": "http://localhost:8000",
                "mesh_namespace": "hub.minimal"
                # tags and allow_fanout not provided
            }
        ]
    )

    assert config.projects[0].tags == []
    assert config.projects[0].allow_fanout == []
