"""Add schedules table for recurring task execution

Revision ID: 008_add_schedules_table
Revises: 007_add_jobs_table
Create Date: 2025-10-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "008_add_schedules_table"
down_revision: Union[str, Sequence[str], None] = "007_add_jobs_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create schedules table for Celery Beat scheduling."""

    # Create schedules table
    op.create_table(
        "schedules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(512), nullable=True),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("task_parameters", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("frequency", sa.String(20), nullable=False, server_default="daily"),
        sa.Column("cron_expression", sa.String(100), nullable=True),
        sa.Column("interval_seconds", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("next_run_at", sa.DateTime(), nullable=True),
        sa.Column("run_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("celery_task_name", sa.String(255), nullable=True),
        sa.Column("celery_beat_key", sa.String(255), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "tags", postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default="{}"
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("celery_beat_key"),
    )

    # Create indexes
    op.create_index("ix_schedules_project_id", "schedules", ["project_id"])
    op.create_index("ix_schedules_task_type", "schedules", ["task_type"])
    op.create_index("ix_schedules_enabled", "schedules", ["enabled"])
    op.create_index("ix_schedules_next_run_at", "schedules", ["next_run_at"])
    op.create_index("idx_schedules_project_enabled", "schedules", ["project_id", "enabled"])
    op.create_index("idx_schedules_task_type", "schedules", ["task_type"])
    op.create_index("idx_schedules_next_run", "schedules", ["next_run_at"])


def downgrade() -> None:
    """Drop schedules table."""
    op.drop_index("idx_schedules_next_run", table_name="schedules")
    op.drop_index("idx_schedules_task_type", table_name="schedules")
    op.drop_index("idx_schedules_project_enabled", table_name="schedules")
    op.drop_index("ix_schedules_next_run_at", table_name="schedules")
    op.drop_index("ix_schedules_enabled", table_name="schedules")
    op.drop_index("ix_schedules_task_type", table_name="schedules")
    op.drop_index("ix_schedules_project_id", table_name="schedules")
    op.drop_table("schedules")
