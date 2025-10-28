"""Multi-instance isolation security tests."""
import os
import pytest


@pytest.mark.asyncio
async def test_project_volumes_are_isolated(
    mock_orchestration_service, project_configs
):
    """Each project uses isolated Docker volumes.

    Critical security requirement: Projects must not share volumes
    as this could leak data between projects.
    """
    # Start two projects
    stack_a = await mock_orchestration_service.start_project(project_configs[0])
    stack_b = await mock_orchestration_service.start_project(project_configs[1])

    # Get volume names for each project
    volumes_a = stack_a.get_volume_names()
    volumes_b = stack_b.get_volume_names()

    # Assert no shared volumes
    shared = set(volumes_a).intersection(set(volumes_b))
    assert len(shared) == 0, (
        f"SECURITY VIOLATION: Found shared volumes between projects: {shared}. "
        f"Projects must have completely isolated storage."
    )

    # Assert volumes include project name for identification
    assert all(project_configs[0].project_name in v for v in volumes_a), (
        "Volume names must include project name for isolation"
    )
    assert all(project_configs[1].project_name in v for v in volumes_b), (
        "Volume names must include project name for isolation"
    )


@pytest.mark.asyncio
async def test_environment_variables_not_leaked(
    mock_orchestration_service, project_configs
):
    """Project A secrets not accessible from Project B.

    Each project must have unique secrets that cannot be accessed
    by other projects.
    """
    # Start both projects
    stack_a = await mock_orchestration_service.start_project(project_configs[0])
    stack_b = await mock_orchestration_service.start_project(project_configs[1])

    # Get environment variables for each
    env_a = stack_a.get_environment_variables()
    env_b = stack_b.get_environment_variables()

    # Assert different secrets
    assert env_a["SECRET_KEY"] != env_b["SECRET_KEY"], (
        "SECURITY VIOLATION: Projects sharing SECRET_KEY. "
        "Each project must have unique secrets."
    )

    assert env_a["DB_PASSWORD"] != env_b["DB_PASSWORD"], (
        "SECURITY VIOLATION: Projects sharing DB_PASSWORD. "
        "Database credentials must be isolated per project."
    )

    # Assert project-specific database URLs
    assert project_configs[0].project_name in env_a["DATABASE_URL"], (
        "Database URL must be project-specific"
    )
    assert project_configs[1].project_name in env_b["DATABASE_URL"], (
        "Database URL must be project-specific"
    )


@pytest.mark.asyncio
async def test_database_files_isolated_per_project(
    mock_orchestration_service, project_configs
):
    """Each project has isolated database storage.

    Database files must be stored in project-specific locations
    to prevent data leakage.
    """
    # Start two projects
    stack_a = await mock_orchestration_service.start_project(project_configs[0])
    stack_b = await mock_orchestration_service.start_project(project_configs[1])

    # Get database file paths
    db_path_a = stack_a.get_database_path()
    db_path_b = stack_b.get_database_path()

    # Assert different paths
    assert db_path_a != db_path_b, (
        "SECURITY VIOLATION: Projects sharing database file path"
    )

    # Assert paths include project identifier
    assert project_configs[0].project_name in db_path_a
    assert project_configs[1].project_name in db_path_b

    # Assert paths are in isolated directories
    parent_a = os.path.dirname(db_path_a)
    parent_b = os.path.dirname(db_path_b)
    assert parent_a != parent_b, (
        "Database files must be in separate directories per project"
    )
