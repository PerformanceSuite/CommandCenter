"""add_database_indexes

Revision ID: a1b2c3d4e5f6
Revises: 62ebb9783d8e
Create Date: 2025-10-05 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "62ebb9783d8e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes to tables."""
    # Add index on Repository(owner, name) for faster lookups by owner/name
    op.create_index("idx_repositories_owner_name", "repositories", ["owner", "name"], unique=False)

    # Add index on Repository(owner) for filtering by owner
    op.create_index("idx_repositories_owner", "repositories", ["owner"], unique=False)

    # Add index on Repository(language) for filtering by language
    op.create_index("idx_repositories_language", "repositories", ["language"], unique=False)

    # Add index on Repository(last_synced_at) for sorting recently synced
    op.create_index(
        "idx_repositories_last_synced_at", "repositories", ["last_synced_at"], unique=False
    )

    # Add index on Technology(domain, status) for filtering
    op.create_index(
        "idx_technologies_domain_status", "technologies", ["domain", "status"], unique=False
    )

    # Add index on Technology(status) for filtering by status
    op.create_index("idx_technologies_status", "technologies", ["status"], unique=False)

    # Add index on Technology(domain) for filtering by domain
    op.create_index("idx_technologies_domain", "technologies", ["domain"], unique=False)

    # Add index on Technology(priority, relevance_score) for sorting
    op.create_index(
        "idx_technologies_priority_relevance",
        "technologies",
        ["priority", "relevance_score"],
        unique=False,
    )

    # Add index on ResearchTask(technology_id) for foreign key lookups
    op.create_index(
        "idx_research_tasks_technology_id", "research_tasks", ["technology_id"], unique=False
    )

    # Add index on ResearchTask(repository_id) for foreign key lookups
    op.create_index(
        "idx_research_tasks_repository_id", "research_tasks", ["repository_id"], unique=False
    )

    # Add index on ResearchTask(status) for filtering by status
    op.create_index("idx_research_tasks_status", "research_tasks", ["status"], unique=False)

    # Add index on ResearchTask(assigned_to) for filtering by assignee
    op.create_index(
        "idx_research_tasks_assigned_to", "research_tasks", ["assigned_to"], unique=False
    )

    # Add index on ResearchTask(due_date) for sorting and filtering by due date
    op.create_index("idx_research_tasks_due_date", "research_tasks", ["due_date"], unique=False)

    # Add index on KnowledgeEntry(technology_id) for foreign key lookups
    op.create_index(
        "idx_knowledge_entries_technology_id", "knowledge_entries", ["technology_id"], unique=False
    )

    # Add index on KnowledgeEntry(category) for filtering by category
    op.create_index(
        "idx_knowledge_entries_category", "knowledge_entries", ["category"], unique=False
    )

    # Add index on KnowledgeEntry(vector_db_id) for vector DB integration
    op.create_index(
        "idx_knowledge_entries_vector_db_id", "knowledge_entries", ["vector_db_id"], unique=False
    )


def downgrade() -> None:
    """Remove performance indexes from tables."""
    # Drop indexes in reverse order
    op.drop_index("idx_knowledge_entries_vector_db_id", table_name="knowledge_entries")
    op.drop_index("idx_knowledge_entries_category", table_name="knowledge_entries")
    op.drop_index("idx_knowledge_entries_technology_id", table_name="knowledge_entries")
    op.drop_index("idx_research_tasks_due_date", table_name="research_tasks")
    op.drop_index("idx_research_tasks_assigned_to", table_name="research_tasks")
    op.drop_index("idx_research_tasks_status", table_name="research_tasks")
    op.drop_index("idx_research_tasks_repository_id", table_name="research_tasks")
    op.drop_index("idx_research_tasks_technology_id", table_name="research_tasks")
    op.drop_index("idx_technologies_priority_relevance", table_name="technologies")
    op.drop_index("idx_technologies_domain", table_name="technologies")
    op.drop_index("idx_technologies_status", table_name="technologies")
    op.drop_index("idx_technologies_domain_status", table_name="technologies")
    op.drop_index("idx_repositories_last_synced_at", table_name="repositories")
    op.drop_index("idx_repositories_language", table_name="repositories")
    op.drop_index("idx_repositories_owner", table_name="repositories")
    op.drop_index("idx_repositories_owner_name", table_name="repositories")
