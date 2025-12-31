"""Add user_projects association table

Add UserProject model for multi-tenant isolation.
This enables proper project-user relationships to replace
the hardcoded DEFAULT_PROJECT_ID = 1 security issue.

Revision ID: 015_add_user_projects
Revises: e5bd4ea700b0
Create Date: 2025-12-30 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "015_add_user_projects"
down_revision: Union[str, Sequence, None] = "e5bd4ea700b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add user_projects association table."""
    op.create_table(
        "user_projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="member"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_projects_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_user_projects_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_projects")),
        sa.UniqueConstraint("user_id", "project_id", name="uq_user_project"),
    )
    op.create_index(op.f("ix_user_projects_id"), "user_projects", ["id"], unique=False)
    op.create_index(
        op.f("ix_user_projects_user_id"), "user_projects", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_user_projects_project_id"), "user_projects", ["project_id"], unique=False
    )


def downgrade() -> None:
    """Remove user_projects association table."""
    op.drop_index(op.f("ix_user_projects_project_id"), table_name="user_projects")
    op.drop_index(op.f("ix_user_projects_user_id"), table_name="user_projects")
    op.drop_index(op.f("ix_user_projects_id"), table_name="user_projects")
    op.drop_table("user_projects")
