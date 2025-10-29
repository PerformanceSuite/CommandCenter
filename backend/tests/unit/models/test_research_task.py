"""Unit tests for ResearchTask model."""
import pytest
from app.models.research_task import ResearchTask, TaskStatus


def test_research_task_state_transitions():
    """ResearchTask state transitions are valid."""
    task = ResearchTask(
        title="Test Task",
        description="Description",
        status=TaskStatus.PENDING,
        project_id=1  # Required field
    )

    # Valid transitions
    task.status = TaskStatus.IN_PROGRESS
    assert task.status == TaskStatus.IN_PROGRESS

    task.status = TaskStatus.COMPLETED
    assert task.status == TaskStatus.COMPLETED

    # Can go back to in_progress (reopening)
    task.status = TaskStatus.IN_PROGRESS
    assert task.status == TaskStatus.IN_PROGRESS
