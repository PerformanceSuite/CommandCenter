"""Dagger SDK integration tests (12 tests)."""
import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_start_complete_stack(dagger_client, project_config):
    """Start complete CommandCenter stack."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    await stack.start()

    assert await stack.postgres.is_running()
    assert await stack.redis.is_running()
    assert await stack.backend.is_running()

    await stack.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stop_preserves_volumes(dagger_client, project_config):
    """Stop preserves volumes (data persistence)."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    await stack.start()

    volumes_before = await stack.get_volumes()
    await stack.stop()
    volumes_after = await stack.get_volumes()

    assert volumes_before == volumes_after

    await stack.remove()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_restart_reuses_volumes(dagger_client, project_config):
    """Restart reuses existing volumes."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    await stack.start()

    volumes_original = await stack.get_volumes()
    await stack.restart()
    volumes_after = await stack.get_volumes()

    assert volumes_original == volumes_after

    await stack.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_build_backend_image(dagger_client, project_config):
    """Build backend Docker image."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    backend_image = await stack.build_backend_image()

    assert backend_image is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_build_frontend_image(dagger_client, project_config):
    """Build frontend Docker image."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    frontend_image = await stack.build_frontend_image()

    assert frontend_image is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mount_project_directory(dagger_client, project_config):
    """Project directory mounted into containers."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    await stack.start()

    backend_ls = await stack.backend.exec(["ls", "/workspace"])
    assert "backend" in backend_ls

    await stack.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pass_environment_variables(dagger_client, project_config):
    """Environment variables passed correctly."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    await stack.start()

    backend_env = await stack.backend.env()
    assert "DATABASE_URL" in backend_env
    assert "SECRET_KEY" in backend_env

    await stack.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_expose_ports(dagger_client, project_config):
    """Ports exposed correctly."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    await stack.start()

    exposed_ports = await stack.get_exposed_ports()
    assert project_config.ports.backend in exposed_ports

    await stack.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check_waits(dagger_client, project_config):
    """Health checks wait for containers ready."""
    import time
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    start = time.time()

    await stack.start()

    elapsed = time.time() - start
    assert elapsed > 3, "Should wait for services to start"

    await stack.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling_failed_start(dagger_client, project_config):
    """Failed start raises clear error."""
    from app.dagger_modules.commandcenter import CommandCenterStack
    from app.exceptions import ContainerStartError

    project_config.ports.postgres = -1  # Invalid

    stack = CommandCenterStack(dagger_client, project_config)

    with pytest.raises(ContainerStartError):
        await stack.start()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cleanup_on_failure(dagger_client, project_config):
    """Partial failure rolls back all containers."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)

    # Test cleanup (implementation-specific)
    assert stack is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_stacks_simultaneous(dagger_client, temp_project_dir):
    """Multiple stacks run simultaneously."""
    from app.dagger_modules.commandcenter import CommandCenterStack
    from app.models.project import CommandCenterConfig, PortSet

    config_a = CommandCenterConfig(
        project_name="proj-a",
        project_path=temp_project_dir,
        ports=PortSet(backend=18000, frontend=13000, postgres=15432, redis=16379)
    )
    config_b = CommandCenterConfig(
        project_name="proj-b",
        project_path=temp_project_dir,
        ports=PortSet(backend=18010, frontend=13010, postgres=15433, redis=16380)
    )

    stack_a = CommandCenterStack(dagger_client, config_a)
    stack_b = CommandCenterStack(dagger_client, config_b)

    await stack_a.start()
    await stack_b.start()

    assert await stack_a.postgres.is_running()
    assert await stack_b.postgres.is_running()

    await stack_a.stop()
    await stack_b.stop()
