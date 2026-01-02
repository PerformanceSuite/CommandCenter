"""Add cross_project_links table for federation

Revision ID: c1d2e3f4a5b6
Revises: fd12cd853b12
Create Date: 2025-01-01 12:00:00.000000

This migration creates a dedicated cross_project_links table for explicit
cross-project relationships in the Composable CommandCenter architecture.

This table enables federation queries across multiple projects, such as:
- "Find all services with degraded health across the ecosystem"
- "Show dependencies between project A and project B"

Architecture Decision:
- Separate table from graph_links for cleaner separation of concerns
- Different indexes optimized for ecosystem-wide queries
- Explicit source/target project_id fields for cross-project relationships
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "fd12cd853b12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def is_sqlite() -> bool:
    """Check if we're running on SQLite."""
    conn = op.get_bind()
    return conn.dialect.name == "sqlite"


def table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    """Create cross_project_links table for federation."""
    # Skip if table already exists (idempotent)
    if table_exists("cross_project_links"):
        return

    # Determine JSON type based on dialect
    json_type = sa.JSON() if is_sqlite() else postgresql.JSONB(astext_type=sa.Text())

    # Create the cross_project_links table
    op.create_table(
        "cross_project_links",
        # Primary key
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        # Source project and entity
        sa.Column("source_project_id", sa.Integer(), nullable=False),
        sa.Column("source_entity_type", sa.String(50), nullable=False),
        sa.Column("source_entity_id", sa.Integer(), nullable=False),
        # Target project and entity
        sa.Column("target_project_id", sa.Integer(), nullable=False),
        sa.Column("target_entity_type", sa.String(50), nullable=False),
        sa.Column("target_entity_id", sa.Integer(), nullable=False),
        # Relationship metadata
        sa.Column("relationship_type", sa.String(50), nullable=False),
        sa.Column(
            "metadata",
            json_type,
            nullable=True,
            server_default="{}",
        ),
        # Timestamps
        sa.Column("discovered_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Add foreign keys (skip for SQLite)
    if not is_sqlite():
        op.create_foreign_key(
            "fk_cross_project_links_source_project",
            "cross_project_links",
            "projects",
            ["source_project_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_foreign_key(
            "fk_cross_project_links_target_project",
            "cross_project_links",
            "projects",
            ["target_project_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # Create composite indexes for federation queries
    op.create_index(
        "ix_cross_project_links_source",
        "cross_project_links",
        ["source_project_id", "source_entity_id"],
    )
    op.create_index(
        "ix_cross_project_links_target",
        "cross_project_links",
        ["target_project_id", "target_entity_id"],
    )

    # Additional index for relationship type queries
    op.create_index(
        "ix_cross_project_links_relationship_type",
        "cross_project_links",
        ["relationship_type"],
    )


def downgrade() -> None:
    """Drop cross_project_links table."""
    # Drop indexes
    op.drop_index("ix_cross_project_links_relationship_type", table_name="cross_project_links")
    op.drop_index("ix_cross_project_links_target", table_name="cross_project_links")
    op.drop_index("ix_cross_project_links_source", table_name="cross_project_links")

    # Drop foreign keys (skip for SQLite)
    if not is_sqlite():
        op.drop_constraint(
            "fk_cross_project_links_target_project", "cross_project_links", type_="foreignkey"
        )
        op.drop_constraint(
            "fk_cross_project_links_source_project", "cross_project_links", type_="foreignkey"
        )

    # Drop table
    op.drop_table("cross_project_links")
