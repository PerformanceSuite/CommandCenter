"""add_agent_executions_table

Revision ID: fd12cd853b12
Revises: dfec56a5f500
Create Date: 2025-12-31 19:14:06.100556

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fd12cd853b12"
down_revision: Union[str, Sequence[str], None] = "dfec56a5f500"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create agent_executions table
    op.create_table(
        "agent_executions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("execution_id", sa.String(36), nullable=False),
        sa.Column("persona_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("files_changed", sa.JSON(), nullable=False),
        sa.Column("pr_url", sa.String(length=512), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agent_executions_execution_id"), "agent_executions", ["execution_id"], unique=True
    )
    op.create_index(
        op.f("ix_agent_executions_persona_name"), "agent_executions", ["persona_name"], unique=False
    )
    op.create_index(
        op.f("ix_agent_executions_status"), "agent_executions", ["status"], unique=False
    )

    # Create agent_personas table (if not exists check for SQLite compatibility)
    op.create_table(
        "agent_personas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("requires_sandbox", sa.Boolean(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_personas_name"), "agent_personas", ["name"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_agent_personas_name"), table_name="agent_personas")
    op.drop_table("agent_personas")
    op.drop_index(op.f("ix_agent_executions_status"), table_name="agent_executions")
    op.drop_index(op.f("ix_agent_executions_persona_name"), table_name="agent_executions")
    op.drop_index(op.f("ix_agent_executions_execution_id"), table_name="agent_executions")
    op.drop_table("agent_executions")
