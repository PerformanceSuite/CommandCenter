"""Add ingestion sources table for automated knowledge ingestion

Revision ID: 014_add_ingestion_sources
Revises: 013_merge_heads
Create Date: 2025-10-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "014_add_ingestion_sources"
down_revision: Union[str, Sequence[str], None] = "013_merge_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ingestion_sources table."""

    # Create ingestion_sources table
    op.create_table(
        "ingestion_sources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(1024), nullable=True),
        sa.Column("path", sa.String(1024), nullable=True),
        sa.Column("schedule", sa.String(100), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("config", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("last_run", sa.DateTime(), nullable=True),
        sa.Column("last_success", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("documents_ingested", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("ix_ingestion_sources_project_id", "ingestion_sources", ["project_id"])
    op.create_index("ix_ingestion_sources_type", "ingestion_sources", ["type"])


def downgrade() -> None:
    """Drop ingestion_sources table."""
    op.drop_index("ix_ingestion_sources_type", table_name="ingestion_sources")
    op.drop_index("ix_ingestion_sources_project_id", table_name="ingestion_sources")
    op.drop_table("ingestion_sources")
