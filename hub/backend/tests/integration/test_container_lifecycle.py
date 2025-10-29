"""Container lifecycle management tests (8 tests)."""
import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_lifecycle(dagger_client, project_config):
    """Full lifecycle: create → start → stop → restart → remove."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)

    assert not await stack.backend.is_running()

    await stack.start()
    assert await stack.backend.is_running()

    await stack.stop()
    assert not await stack.backend.is_running()

    await stack.restart()
    assert await stack.backend.is_running()

    await stack.remove()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_start_idempotent(dagger_client, project_config):
    """Start on already-running is idempotent."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)

    await stack.start()
    await stack.start()  # Should not error

    assert await stack.backend.is_running()

    await stack.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stop_idempotent(dagger_client, project_config):
    """Stop on already-stopped is idempotent."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)

    await stack.start()
    await stack.stop()
    await stack.stop()  # Should not error


@pytest.mark.integration
@pytest.mark.asyncio
async def test_container_logs(dagger_client, project_config):
    """Container logs accessible."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    await stack.start()

    logs = await stack.backend.logs(tail=50)
    assert len(logs) > 0

    await stack.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_status_updates(dagger_client, project_config):
    """Container status updates correctly."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)

    status = await stack.get_status()
    assert status == "stopped"

    await stack.start()
    status = await stack.get_status()
    assert status == "running"

    await stack.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_restart_preserves_config(dagger_client, project_config):
    """Restart preserves configuration."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    await stack.start()

    ports_before = await stack.get_exposed_ports()
    await stack.restart()
    ports_after = await stack.get_exposed_ports()

    assert ports_before == ports_after

    await stack.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_force_stop(dagger_client, project_config):
    """Force stop with SIGKILL."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    await stack.start()

    await stack.stop(timeout=1, force=True)

    assert not await stack.backend.is_running()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_restart_after_crash(dagger_client, project_config):
    """Restart works after crash."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    await stack.start()

    # Simulate crash
    await stack.backend.kill()
    assert not await stack.backend.is_running()

    # Restart should recover
    await stack.restart()
    assert await stack.backend.is_running()

    await stack.stop()
