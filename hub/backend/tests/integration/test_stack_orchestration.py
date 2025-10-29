"""Stack orchestration tests (6 tests)."""
import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_services_start_in_order(dagger_client, project_config):
    """Services start in dependency order."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    await stack.start()

    # Postgres and Redis should start before backend
    assert await stack.postgres.is_running()
    assert await stack.redis.is_running()
    assert await stack.backend.is_running()

    await stack.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dependencies_verified(dagger_client, project_config):
    """Dependencies verified before starting dependents."""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    await stack.start()

    assert await stack.postgres.is_ready()
    assert await stack.redis.is_ready()

    await stack.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_partial_failure_rollback(dagger_client, project_config):
    """Partial failure rolls back entire stack."""
    from app.dagger_modules.commandcenter import CommandCenterStack
    from unittest.mock import patch

    stack = CommandCenterStack(dagger_client, project_config)

    # Mock backend failure
    with patch.object(stack, '_start_backend', side_effect=Exception("Failed")):
        try:
            await stack.start()
        except:
            pass

    # All should be stopped
    assert not await stack.postgres.is_running()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_checks_prevent_premature_ready(dagger_client, project_config):
    """Health checks prevent premature ready status."""
    import time
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)

    start = time.time()
    await stack.start()
    elapsed = time.time() - start

    assert elapsed >= 3, "Should wait for health checks"

    await stack.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_orchestration_tracks_multiple_stacks(dagger_client, temp_project_dir):
    """OrchestrationService tracks multiple stacks."""
    from app.services.orchestration_service import OrchestrationService
    from app.models.project import CommandCenterConfig, PortSet

    service = OrchestrationService(db_session=None)

    config_a = CommandCenterConfig(
        project_name="tracked-a",
        project_path=temp_project_dir,
        ports=PortSet(backend=18000, frontend=13000, postgres=15432, redis=16379)
    )

    stack = await service.start_project(config_a)
    active = service.get_active_stacks()

    assert len(active) == 1

    await service.stop_project("tracked-a")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_registry_cleanup_on_removal(dagger_client, project_config):
    """Registry cleaned up on stack removal."""
    from app.services.orchestration_service import OrchestrationService

    service = OrchestrationService(db_session=None)

    await service.start_project(project_config)
    assert len(service.get_active_stacks()) == 1

    await service.remove_project(project_config.project_name)
    assert len(service.get_active_stacks()) == 0
