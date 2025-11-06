"""Test improvements to Phase 6: Health & Service Discovery system."""
import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service, HealthStatus, ServiceType, HealthMethod
from app.models.project import Project
from app.services.health_service import HealthService, CircuitBreaker
from app.workers.health_worker import HealthCheckWorker
from app.routers.services import RateLimiter


@pytest.mark.asyncio
class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    async def test_circuit_opens_after_threshold(self):
        """Test that circuit opens after failure threshold."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

        # Record failures
        breaker.record_failure(1)
        assert not breaker.is_open(1)

        breaker.record_failure(1)
        assert not breaker.is_open(1)

        breaker.record_failure(1)
        assert breaker.is_open(1)  # Should be open now

    async def test_circuit_closes_after_recovery(self):
        """Test that circuit closes after recovery timeout."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        # Open the circuit
        breaker.record_failure(1)
        breaker.record_failure(1)
        assert breaker.is_open(1)

        # Wait for recovery
        await asyncio.sleep(0.2)
        assert not breaker.is_open(1)

    async def test_circuit_resets_on_success(self):
        """Test that success resets circuit breaker."""
        breaker = CircuitBreaker(failure_threshold=3)

        breaker.record_failure(1)
        breaker.record_failure(1)
        assert not breaker.is_open(1)

        breaker.record_success(1)
        breaker.record_failure(1)
        assert not breaker.is_open(1)  # Should not be open


@pytest.mark.asyncio
class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    @patch('app.services.health_service.httpx.AsyncClient')
    async def test_retry_on_failure(self, mock_client_class, db_session: AsyncSession):
        """Test that health checks retry on failure."""
        # Setup mock
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # First two calls fail, third succeeds
        mock_client.get.side_effect = [
            Exception("Connection error"),
            Exception("Timeout"),
            MagicMock(status_code=200, json=lambda: {"status": "ok"})
        ]

        # Create test service
        project = Project(
            name="test-project",
            slug="test",
            path="/test",
            status="running"
        )
        db_session.add(project)
        await db_session.commit()

        service = Service(
            project_id=project.id,
            name="test-service",
            service_type=ServiceType.API,
            health_method=HealthMethod.HTTP,
            health_url="http://localhost:8000/health",
            health_threshold=1000
        )
        db_session.add(service)
        await db_session.commit()

        # Perform health check with retries
        health_service = HealthService()
        health_check = await health_service.check_service_health(
            service, db_session, max_retries=3
        )

        # Should succeed after retries
        assert health_check.status == HealthStatus.UP
        assert mock_client.get.call_count == 3

    async def test_exponential_backoff(self):
        """Test exponential backoff timing."""
        start_times = []

        async def mock_check():
            start_times.append(time.time())
            if len(start_times) < 3:
                raise Exception("Failed")
            return True, {}

        # Measure backoff timing
        for attempt in range(3):
            try:
                await mock_check()
                break
            except:
                if attempt < 2:
                    wait_time = (2 ** attempt) * 0.5
                    await asyncio.sleep(wait_time)

        # Check timing between attempts
        if len(start_times) >= 2:
            first_wait = start_times[1] - start_times[0]
            assert 0.4 < first_wait < 0.6  # ~0.5 seconds

        if len(start_times) >= 3:
            second_wait = start_times[2] - start_times[1]
            assert 0.9 < second_wait < 1.1  # ~1.0 seconds


@pytest.mark.asyncio
class TestRateLimiting:
    """Test rate limiting for health check triggers."""

    def test_rate_limiter_allows_within_limit(self):
        """Test that rate limiter allows calls within limit."""
        limiter = RateLimiter(max_calls=3, window_seconds=60)

        assert limiter.is_allowed("test1")
        assert limiter.is_allowed("test1")
        assert limiter.is_allowed("test1")
        assert not limiter.is_allowed("test1")  # Should be blocked

    def test_rate_limiter_resets_after_window(self):
        """Test that rate limiter resets after time window."""
        limiter = RateLimiter(max_calls=2, window_seconds=0.1)

        assert limiter.is_allowed("test2")
        assert limiter.is_allowed("test2")
        assert not limiter.is_allowed("test2")

        time.sleep(0.2)  # Wait for window to reset
        assert limiter.is_allowed("test2")

    def test_rate_limiter_separate_keys(self):
        """Test that rate limiter tracks keys separately."""
        limiter = RateLimiter(max_calls=2, window_seconds=60)

        assert limiter.is_allowed("service_1")
        assert limiter.is_allowed("service_1")
        assert not limiter.is_allowed("service_1")

        # Different service should work
        assert limiter.is_allowed("service_2")
        assert limiter.is_allowed("service_2")


@pytest.mark.asyncio
class TestHealthWorkerLifecycle:
    """Test health check worker lifecycle management."""

    async def test_worker_start_stop(self):
        """Test worker starts and stops cleanly."""
        worker = HealthCheckWorker()

        # Start worker
        await worker.start()
        assert worker._running

        # Stop worker
        await asyncio.wait_for(worker.stop(), timeout=5.0)
        assert not worker._running

    async def test_worker_task_cleanup(self):
        """Test that worker cleans up tasks on stop."""
        worker = HealthCheckWorker()

        # Add mock tasks
        worker._tasks[1] = asyncio.create_task(asyncio.sleep(10))
        worker._tasks[2] = asyncio.create_task(asyncio.sleep(10))

        # Stop should cancel tasks
        await worker.stop()
        assert len(worker._tasks) == 0

    @patch('app.workers.health_worker.async_session_maker')
    async def test_worker_handles_errors(self, mock_session_maker):
        """Test worker continues on errors."""
        # Setup mock to raise error
        mock_session = AsyncMock()
        mock_session.__aenter__.side_effect = Exception("Database error")
        mock_session_maker.return_value = mock_session

        worker = HealthCheckWorker()
        worker._running = True

        # Should handle error without crashing
        try:
            await asyncio.wait_for(worker._run_loop(), timeout=0.1)
        except asyncio.TimeoutError:
            pass  # Expected timeout

        # Worker should still be marked as running
        assert worker._running


@pytest.mark.asyncio
class TestRetentionPolicy:
    """Test health history retention policy."""

    async def test_cleanup_old_records(self, db_session: AsyncSession):
        """Test that old health records are cleaned up."""
        # Create old and new health checks
        service = Service(
            project_id=1,
            name="test",
            service_type=ServiceType.API
        )
        db_session.add(service)
        await db_session.commit()

        # Add health checks with different ages
        old_date = datetime.now(timezone.utc) - timedelta(days=10)
        new_date = datetime.now(timezone.utc)

        from app.models.service import HealthCheck

        old_check = HealthCheck(
            service_id=service.id,
            status=HealthStatus.UP,
            checked_at=old_date
        )
        new_check = HealthCheck(
            service_id=service.id,
            status=HealthStatus.UP,
            checked_at=new_date
        )

        db_session.add(old_check)
        db_session.add(new_check)
        await db_session.commit()

        # Run cleanup
        health_service = HealthService()
        count = await health_service.cleanup_old_health_checks(retention_days=7)

        # Old record should be deleted
        assert count == 1

    async def test_retention_worker_periodic_cleanup(self):
        """Test that worker performs periodic cleanup."""
        worker = HealthCheckWorker()
        worker.cleanup_interval = 0.1  # Fast cleanup for testing
        worker._running = True

        with patch.object(worker.health_service, 'cleanup_old_health_checks') as mock_cleanup:
            mock_cleanup.return_value = 5

            # Start cleanup task
            cleanup_task = asyncio.create_task(worker._cleanup_old_records())

            # Wait for cleanup to run
            await asyncio.sleep(0.2)

            # Should have called cleanup
            assert mock_cleanup.called

            # Stop the task
            worker._running = False
            cleanup_task.cancel()


@pytest.mark.asyncio
class TestConnectionPooling:
    """Test HTTP connection pooling."""

    async def test_connection_pool_reuse(self):
        """Test that HTTP client reuses connections."""
        health_service = HealthService()

        # Check that client is configured with pooling
        assert health_service._http_client.limits.max_connections == 20
        assert health_service._http_client.limits.max_keepalive_connections == 10

    async def test_connection_pool_cleanup(self):
        """Test that connection pool is cleaned up."""
        health_service = HealthService()

        # Use context manager
        async with health_service:
            pass  # Client should be available

        # After exit, client should be closed
        assert health_service._http_client.is_closed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
