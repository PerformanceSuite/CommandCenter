"""Add performance optimization indexes

Revision ID: 012_performance_indexes
Revises: 011_add_webhook_deliveries_table
Create Date: 2025-10-14

Performance optimizations:
- Text search indexes for technologies
- Composite index for jobs filtering
- Descending index for pagination
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "012_performance_indexes"
down_revision: Union[str, Sequence[str], None] = "011_add_webhook_deliveries"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance optimization indexes."""

    # Check if we're using PostgreSQL
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == "postgresql"

    if is_postgresql:
        # Add GIN indexes for text search on technologies
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_technologies_title_gin
            ON technologies
            USING gin(to_tsvector('english', title))
        """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_technologies_description_gin
            ON technologies
            USING gin(to_tsvector('english', COALESCE(description, '')))
        """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_technologies_tags_gin
            ON technologies
            USING gin(to_tsvector('english', COALESCE(tags, '')))
        """
        )

        # Add composite index for full text search
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_technologies_search_gin
            ON technologies
            USING gin(to_tsvector('english',
                COALESCE(title, '') || ' ' ||
                COALESCE(description, '') || ' ' ||
                COALESCE(tags, '')
            ))
        """
        )

    # Add composite index for jobs filtering (works for all databases)
    op.create_index(
        "idx_jobs_project_type_status", "jobs", ["project_id", "job_type", "status"], unique=False
    )

    # Add descending index for pagination optimization
    if is_postgresql:
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_jobs_created_at_desc
            ON jobs(created_at DESC)
        """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_technologies_updated_at_desc
            ON technologies(updated_at DESC)
        """
        )

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_technologies_priority_relevance_desc
            ON technologies(priority DESC, relevance_score DESC)
        """
        )
    else:
        # For SQLite, regular indexes (no DESC support in older versions)
        op.create_index("idx_jobs_created_at_desc", "jobs", ["created_at"], unique=False)

        op.create_index(
            "idx_technologies_updated_at_desc", "technologies", ["updated_at"], unique=False
        )

    # Note: idx_research_tasks_status already exists from migration a1b2c3d4e5f6
    # No need to create it again

    # Add index for knowledge entries
    if op.get_bind().dialect.has_table(op.get_bind(), "knowledge_entries"):
        op.create_index(
            "idx_knowledge_entries_technology_category",
            "knowledge_entries",
            ["technology_id", "category"],
            unique=False,
        )

    # Add partial index for active jobs (PostgreSQL only)
    if is_postgresql:
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_jobs_active
            ON jobs(project_id, job_type)
            WHERE status IN ('pending', 'running')
        """
        )

        # Add index for frequently accessed completed jobs
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_jobs_completed_recent
            ON jobs(project_id, completed_at DESC)
            WHERE status = 'completed'
        """
        )

    # Add covering index for common queries (PostgreSQL)
    if is_postgresql:
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_technologies_list_coverage
            ON technologies(domain, status, priority DESC, relevance_score DESC)
            INCLUDE (title, vendor, description)
        """
        )


def downgrade() -> None:
    """Remove performance optimization indexes."""

    # Check if we're using PostgreSQL
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == "postgresql"

    # Drop PostgreSQL-specific indexes
    if is_postgresql:
        op.execute("DROP INDEX IF EXISTS idx_technologies_title_gin")
        op.execute("DROP INDEX IF EXISTS idx_technologies_description_gin")
        op.execute("DROP INDEX IF EXISTS idx_technologies_tags_gin")
        op.execute("DROP INDEX IF EXISTS idx_technologies_search_gin")
        op.execute("DROP INDEX IF EXISTS idx_jobs_created_at_desc")
        op.execute("DROP INDEX IF EXISTS idx_technologies_updated_at_desc")
        op.execute("DROP INDEX IF EXISTS idx_technologies_priority_relevance_desc")
        op.execute("DROP INDEX IF EXISTS idx_jobs_active")
        op.execute("DROP INDEX IF EXISTS idx_jobs_completed_recent")
        op.execute("DROP INDEX IF EXISTS idx_technologies_list_coverage")
    else:
        # Drop SQLite indexes
        op.drop_index("idx_jobs_created_at_desc", table_name="jobs")
        op.drop_index("idx_technologies_updated_at_desc", table_name="technologies")

    # Drop cross-database indexes
    op.drop_index("idx_jobs_project_type_status", table_name="jobs")
    # Note: idx_research_tasks_status managed by migration a1b2c3d4e5f6

    # Drop knowledge entries index if table exists
    if op.get_bind().dialect.has_table(op.get_bind(), "knowledge_entries"):
        op.drop_index("idx_knowledge_entries_technology_category", table_name="knowledge_entries")
