"""
Unit tests for ResearchTask model
"""

import pytest
from datetime import datetime
from sqlalchemy import select

from app.models.research_task import ResearchTask, TaskStatus
from tests.utils import create_test_research_task, create_test_project


@pytest.mark.unit
@pytest.mark.db
class TestResearchTaskModel:
    """Test ResearchTask database model"""

    async def test_create_research_task(self, db_session):
        """Test creating a research task"""
        project = await create_test_project(db_session)
        task = await create_test_research_task(db_session, project_id=project.id)

        assert task.id is not None
        assert task.title == "Test Research Task"
        assert task.description == "A test research task"
        assert task.status == TaskStatus.PENDING
        assert task.project_id == project.id
        assert isinstance(task.created_at, datetime)

    async def test_research_task_state_transitions(self, db_session):
        """ResearchTask state transitions are valid"""
        project = await create_test_project(db_session)
        task = await create_test_research_task(
            db_session,
            project_id=project.id,
            status=TaskStatus.PENDING
        )

        # Valid transitions
        task.status = TaskStatus.IN_PROGRESS
        await db_session.commit()
        await db_session.refresh(task)
        assert task.status == TaskStatus.IN_PROGRESS

        task.status = TaskStatus.COMPLETED
        await db_session.commit()
        await db_session.refresh(task)
        assert task.status == TaskStatus.COMPLETED

        # Can go back to in_progress (reopening)
        task.status = TaskStatus.IN_PROGRESS
        await db_session.commit()
        await db_session.refresh(task)
        assert task.status == TaskStatus.IN_PROGRESS

    async def test_research_task_all_statuses(self, db_session):
        """Test all task status values"""
        project = await create_test_project(db_session)

        for status in TaskStatus:
            task = await create_test_research_task(
                db_session,
                project_id=project.id,
                title=f"Task {status.value}",
                status=status
            )
            assert task.status == status

    async def test_research_task_default_values(self, db_session):
        """Test research task default values"""
        project = await create_test_project(db_session)

        task = ResearchTask(
            title="Minimal Task",
            project_id=project.id
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.status == TaskStatus.PENDING
        assert task.progress_percentage == 0
        assert task.description is None
        assert task.assigned_to is None
        assert task.due_date is None
        assert task.completed_at is None
        assert task.estimated_hours is None
        assert task.actual_hours is None

    async def test_research_task_with_full_details(self, db_session):
        """Test research task with all fields populated"""
        project = await create_test_project(db_session)
        due_date = datetime.utcnow()

        task = ResearchTask(
            title="Comprehensive Task",
            description="Detailed task description",
            status=TaskStatus.IN_PROGRESS,
            project_id=project.id,
            assigned_to="John Doe",
            due_date=due_date,
            progress_percentage=50,
            estimated_hours=10,
            actual_hours=5,
            user_notes="Some user notes",
            findings="Research findings",
            uploaded_documents=["doc1.pdf", "doc2.pdf"],
            metadata_={"key": "value"}
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.title == "Comprehensive Task"
        assert task.description == "Detailed task description"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.assigned_to == "John Doe"
        assert task.progress_percentage == 50
        assert task.estimated_hours == 10
        assert task.actual_hours == 5
        assert task.user_notes == "Some user notes"
        assert task.findings == "Research findings"
        assert task.uploaded_documents == ["doc1.pdf", "doc2.pdf"]
        assert task.metadata_ == {"key": "value"}

    async def test_research_task_progress_tracking(self, db_session):
        """Test research task progress updates"""
        project = await create_test_project(db_session)
        task = await create_test_research_task(db_session, project_id=project.id)

        assert task.progress_percentage == 0

        # Update progress
        task.progress_percentage = 25
        await db_session.commit()
        await db_session.refresh(task)
        assert task.progress_percentage == 25

        task.progress_percentage = 100
        await db_session.commit()
        await db_session.refresh(task)
        assert task.progress_percentage == 100

    async def test_research_task_completion(self, db_session):
        """Test marking research task as completed"""
        project = await create_test_project(db_session)
        task = await create_test_research_task(db_session, project_id=project.id)

        # Complete the task
        completed_time = datetime.utcnow()
        task.status = TaskStatus.COMPLETED
        task.completed_at = completed_time
        task.progress_percentage = 100
        await db_session.commit()
        await db_session.refresh(task)

        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
        assert abs((task.completed_at - completed_time).total_seconds()) < 1

    async def test_research_task_blocking(self, db_session):
        """Test blocking a research task"""
        project = await create_test_project(db_session)
        task = await create_test_research_task(
            db_session,
            project_id=project.id,
            status=TaskStatus.IN_PROGRESS
        )

        # Block the task
        task.status = TaskStatus.BLOCKED
        task.user_notes = "Blocked by external dependency"
        await db_session.commit()
        await db_session.refresh(task)

        assert task.status == TaskStatus.BLOCKED
        assert "Blocked by" in task.user_notes

    async def test_research_task_cancellation(self, db_session):
        """Test cancelling a research task"""
        project = await create_test_project(db_session)
        task = await create_test_research_task(
            db_session,
            project_id=project.id,
            status=TaskStatus.PENDING
        )

        # Cancel the task
        task.status = TaskStatus.CANCELLED
        await db_session.commit()
        await db_session.refresh(task)

        assert task.status == TaskStatus.CANCELLED

    async def test_research_task_project_relationship(self, db_session):
        """Test research task relationship with project"""
        project = await create_test_project(db_session)
        task = await create_test_research_task(db_session, project_id=project.id)

        assert task.project_id == project.id
        assert task.project is not None
        assert task.project.id == project.id

    async def test_research_task_update_timestamp(self, db_session):
        """Test that updated_at timestamp changes on update"""
        project = await create_test_project(db_session)
        task = await create_test_research_task(db_session, project_id=project.id)
        original_updated_at = task.updated_at

        # Update the task
        task.description = "Updated description"
        await db_session.commit()
        await db_session.refresh(task)

        assert task.updated_at > original_updated_at

    async def test_research_task_repr(self, db_session):
        """Test research task string representation"""
        project = await create_test_project(db_session)
        task = await create_test_research_task(db_session, project_id=project.id)
        repr_str = repr(task)

        assert "ResearchTask" in repr_str
        assert str(task.id) in repr_str
        assert task.title in repr_str
        assert task.status.value in repr_str
