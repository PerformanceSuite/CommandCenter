"""Integration tests for Celery background tasks with real Redis"""
import pytest
import asyncio
import time
from celery.result import AsyncResult
from app.tasks.orchestration import start_project_task, stop_project_task
from app.database import AsyncSessionLocal


@pytest.mark.integration
class TestBackgroundTaskIntegration:
    """Integration tests for background task execution"""

    def test_task_submission_returns_id(self):
        """Test that submitting a task returns a task ID"""
        # Submit task
        result = start_project_task.delay(project_id=999)

        # Verify we got a task ID
        assert result.id is not None
        assert len(result.id) > 0

        # Task should be pending or started
        assert result.state in ['PENDING', 'STARTED', 'BUILDING']

        # Revoke task to prevent it from running
        result.revoke(terminate=True)

    def test_task_status_polling(self, test_project):
        """Test that we can poll task status"""
        # Submit task
        result = start_project_task.delay(project_id=test_project.id)
        task_id = result.id

        # Poll status
        task_result = AsyncResult(task_id)

        # Should have valid state
        assert task_result.state in [
            'PENDING', 'STARTED', 'BUILDING',
            'RUNNING', 'SUCCESS', 'FAILURE'
        ]

        # Should be able to check if ready
        assert isinstance(task_result.ready(), bool)

        # Revoke task
        result.revoke(terminate=True)

    def test_task_execution_lifecycle(self, test_project):
        """Test full task lifecycle: submit → poll → complete"""
        # Note: This test will fail if Dagger is not available
        # Mark as xfail if running in CI without Dagger
        pytest.skip("Requires Dagger and can take 20+ minutes")

        # Submit task
        result = start_project_task.delay(project_id=test_project.id)
        task_id = result.id

        # Poll until complete (with timeout)
        max_wait = 1800  # 30 minutes
        start_time = time.time()

        while time.time() - start_time < max_wait:
            task_result = AsyncResult(task_id)

            if task_result.ready():
                # Task completed
                if task_result.successful():
                    result_data = task_result.result
                    assert result_data["success"] is True
                    assert result_data["project_id"] == test_project.id
                else:
                    # Task failed
                    pytest.fail(f"Task failed: {task_result.info}")
                break

            # Wait before next poll
            time.sleep(2)
        else:
            pytest.fail("Task did not complete within 30 minutes")

    def test_concurrent_task_execution(self):
        """Test that multiple tasks can run concurrently"""
        # Submit 3 tasks
        results = []
        for i in range(1, 4):
            result = start_project_task.delay(project_id=1000 + i)
            results.append(result)

        # Verify all have task IDs
        task_ids = [r.id for r in results]
        assert len(task_ids) == 3
        assert len(set(task_ids)) == 3  # All unique

        # All should be pending/started
        for result in results:
            assert result.state in ['PENDING', 'STARTED', 'BUILDING']

        # Revoke all tasks
        for result in results:
            result.revoke(terminate=True)

    def test_task_progress_updates(self, test_project):
        """Test that task progress is updated during execution"""
        pytest.skip("Requires mocking Dagger to test progress updates")

        # Submit task
        result = start_project_task.delay(project_id=test_project.id)
        task_id = result.id

        # Wait for task to start
        time.sleep(1)

        # Check for progress updates
        task_result = AsyncResult(task_id)
        if task_result.state == 'BUILDING':
            info = task_result.info
            assert 'step' in info
            assert 'progress' in info
            assert 0 <= info['progress'] <= 100

        # Revoke task
        result.revoke(terminate=True)
