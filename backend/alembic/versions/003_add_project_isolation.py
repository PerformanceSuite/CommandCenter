"""Add project_id to all tables for multi-project isolation

Revision ID: add_project_isolation
Revises: add_webhook_and_rate_limit_models
Create Date: 2025-10-09 03:00:00.000000

This migration implements complete database isolation by:
1. Creating the projects table
2. Adding a default project for existing data
3. Adding project_id foreign key to all tables
4. Migrating existing data to the default project
5. Making project_id non-nullable with cascade delete

CRITICAL: This migration ensures complete data isolation between projects.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003_add_project_isolation"
down_revision: Union[str, None] = "a7ecf93fa46a"  # merge_migration_heads
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add project isolation to all tables"""

    # 1. Create projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner", "name", name="uq_project_owner_name"),
    )
    op.create_index("ix_projects_id", "projects", ["id"], unique=False)

    # 2. Insert default project for existing data
    op.execute(
        """
        INSERT INTO projects (name, owner, description, created_at)
        VALUES (
            'Default Project',
            'system',
            'Auto-created default project for existing data migration',
            NOW()
        )
    """
    )

    # 3. Add project_id to repositories table
    op.add_column("repositories", sa.Column("project_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE repositories SET project_id = (SELECT id FROM projects WHERE name = 'Default Project')"
    )
    op.alter_column("repositories", "project_id", nullable=False)
    op.create_foreign_key(
        "fk_repositories_project",
        "repositories",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_repositories_project_id", "repositories", ["project_id"], unique=False)

    # 4. Add project_id to technologies table
    op.add_column("technologies", sa.Column("project_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE technologies SET project_id = (SELECT id FROM projects WHERE name = 'Default Project')"
    )
    op.alter_column("technologies", "project_id", nullable=False)
    op.create_foreign_key(
        "fk_technologies_project",
        "technologies",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_technologies_project_id", "technologies", ["project_id"], unique=False)

    # 5. Add project_id to research_tasks table
    op.add_column("research_tasks", sa.Column("project_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE research_tasks SET project_id = (SELECT id FROM projects WHERE name = 'Default Project')"
    )
    op.alter_column("research_tasks", "project_id", nullable=False)
    op.create_foreign_key(
        "fk_research_tasks_project",
        "research_tasks",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_research_tasks_project_id", "research_tasks", ["project_id"], unique=False)

    # 6. Add project_id to knowledge_entries table
    op.add_column("knowledge_entries", sa.Column("project_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE knowledge_entries SET project_id = (SELECT id FROM projects WHERE name = 'Default Project')"
    )
    op.alter_column("knowledge_entries", "project_id", nullable=False)
    op.create_foreign_key(
        "fk_knowledge_entries_project",
        "knowledge_entries",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_knowledge_entries_project_id", "knowledge_entries", ["project_id"], unique=False
    )

    # 7. Add project_id to webhook_configs table
    op.add_column("webhook_configs", sa.Column("project_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE webhook_configs SET project_id = (SELECT id FROM projects WHERE name = 'Default Project')"
    )
    op.alter_column("webhook_configs", "project_id", nullable=False)
    op.create_foreign_key(
        "fk_webhook_configs_project",
        "webhook_configs",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_webhook_configs_project_id", "webhook_configs", ["project_id"], unique=False
    )

    # 8. Add project_id to webhook_events table
    op.add_column("webhook_events", sa.Column("project_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE webhook_events SET project_id = (SELECT id FROM projects WHERE name = 'Default Project')"
    )
    op.alter_column("webhook_events", "project_id", nullable=False)
    op.create_foreign_key(
        "fk_webhook_events_project",
        "webhook_events",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_webhook_events_project_id", "webhook_events", ["project_id"], unique=False)

    # 9. Add project_id to github_rate_limits table
    op.add_column("github_rate_limits", sa.Column("project_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE github_rate_limits SET project_id = (SELECT id FROM projects WHERE name = 'Default Project')"
    )
    op.alter_column("github_rate_limits", "project_id", nullable=False)
    op.create_foreign_key(
        "fk_github_rate_limits_project",
        "github_rate_limits",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_github_rate_limits_project_id", "github_rate_limits", ["project_id"], unique=False
    )


def downgrade() -> None:
    """Remove project isolation from all tables"""

    # Drop indexes and foreign keys in reverse order
    op.drop_index("ix_github_rate_limits_project_id", table_name="github_rate_limits")
    op.drop_constraint("fk_github_rate_limits_project", "github_rate_limits", type_="foreignkey")
    op.drop_column("github_rate_limits", "project_id")

    op.drop_index("ix_webhook_events_project_id", table_name="webhook_events")
    op.drop_constraint("fk_webhook_events_project", "webhook_events", type_="foreignkey")
    op.drop_column("webhook_events", "project_id")

    op.drop_index("ix_webhook_configs_project_id", table_name="webhook_configs")
    op.drop_constraint("fk_webhook_configs_project", "webhook_configs", type_="foreignkey")
    op.drop_column("webhook_configs", "project_id")

    op.drop_index("ix_knowledge_entries_project_id", table_name="knowledge_entries")
    op.drop_constraint("fk_knowledge_entries_project", "knowledge_entries", type_="foreignkey")
    op.drop_column("knowledge_entries", "project_id")

    op.drop_index("ix_research_tasks_project_id", table_name="research_tasks")
    op.drop_constraint("fk_research_tasks_project", "research_tasks", type_="foreignkey")
    op.drop_column("research_tasks", "project_id")

    op.drop_index("ix_technologies_project_id", table_name="technologies")
    op.drop_constraint("fk_technologies_project", "technologies", type_="foreignkey")
    op.drop_column("technologies", "project_id")

    op.drop_index("ix_repositories_project_id", table_name="repositories")
    op.drop_constraint("fk_repositories_project", "repositories", type_="foreignkey")
    op.drop_column("repositories", "project_id")

    # Drop projects table
    op.drop_index("ix_projects_id", table_name="projects")
    op.drop_table("projects")
