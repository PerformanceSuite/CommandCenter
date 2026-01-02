"""Add cross-project link columns to graph_links table

Revision ID: b1c2d3e4f5a6
Revises: a2d26e62e1f3
Create Date: 2025-01-01 14:00:00.000000

This migration adds source_project_id and target_project_id columns to
the graph_links table to enable cross-project federation queries.

These columns are nullable for backward compatibility with existing
intra-project links. Cross-project links are identified when both
columns are set and source_project_id != target_project_id.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a2d26e62e1f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def is_sqlite() -> bool:
    """Check if we're running on SQLite."""
    conn = op.get_bind()
    return conn.dialect.name == "sqlite"


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    if not table_exists(table_name):
        return False
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    # Skip if graph_links table doesn't exist yet (will be created by later migration)
    if not table_exists("graph_links"):
        print("graph_links table does not exist yet, skipping column additions")
        return

    # Add source_project_id column with FK to projects table (idempotent)
    if not column_exists("graph_links", "source_project_id"):
        op.add_column(
            "graph_links",
            sa.Column("source_project_id", sa.Integer(), nullable=True),
        )
    # SQLite doesn't support ALTER TABLE ADD CONSTRAINT for foreign keys
    if not is_sqlite():
        op.create_foreign_key(
            "fk_graph_links_source_project_id",
            "graph_links",
            "projects",
            ["source_project_id"],
            ["id"],
            ondelete="CASCADE",
        )
    if not index_exists("graph_links", "ix_graph_links_source_project_id"):
        op.create_index(
            "ix_graph_links_source_project_id",
            "graph_links",
            ["source_project_id"],
        )

    # Add target_project_id column with FK to projects table (idempotent)
    if not column_exists("graph_links", "target_project_id"):
        op.add_column(
            "graph_links",
            sa.Column("target_project_id", sa.Integer(), nullable=True),
        )
    if not is_sqlite():
        op.create_foreign_key(
            "fk_graph_links_target_project_id",
            "graph_links",
            "projects",
            ["target_project_id"],
            ["id"],
            ondelete="CASCADE",
        )
    if not index_exists("graph_links", "ix_graph_links_target_project_id"):
        op.create_index(
            "ix_graph_links_target_project_id",
            "graph_links",
            ["target_project_id"],
        )

    # Add composite index for cross-project federation queries (idempotent)
    # This optimizes queries like: "find all links between project A and project B"
    if not index_exists("graph_links", "ix_graph_links_cross_project"):
        op.create_index(
            "ix_graph_links_cross_project",
            "graph_links",
            ["source_project_id", "target_project_id"],
        )


def downgrade() -> None:
    # Drop composite index
    op.drop_index("ix_graph_links_cross_project", table_name="graph_links")

    # Drop target_project_id
    op.drop_index("ix_graph_links_target_project_id", table_name="graph_links")
    if not is_sqlite():
        op.drop_constraint("fk_graph_links_target_project_id", "graph_links", type_="foreignkey")
    op.drop_column("graph_links", "target_project_id")

    # Drop source_project_id
    op.drop_index("ix_graph_links_source_project_id", table_name="graph_links")
    if not is_sqlite():
        op.drop_constraint("fk_graph_links_source_project_id", "graph_links", type_="foreignkey")
    op.drop_column("graph_links", "source_project_id")
