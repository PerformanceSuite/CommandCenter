"""Add KnowledgeBeast integration support

Revision ID: 004
Revises: 003
Create Date: 2025-10-09

Changes:
- Add kb_collection_name to knowledge_entries table
- Add kb_document_ids to track KnowledgeBeast document IDs
- Add search_mode to track which search mode was used
- Add kb_chunk_count for tracking chunk statistics
- Populate kb_collection_name based on project_id
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_knowledgebeast_integration'
down_revision = '003_add_project_isolation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add KnowledgeBeast integration columns to knowledge_entries table"""

    # Add new columns for KnowledgeBeast integration
    op.add_column(
        'knowledge_entries',
        sa.Column('kb_collection_name', sa.String(255), nullable=True)
    )
    op.add_column(
        'knowledge_entries',
        sa.Column('kb_document_ids', sa.JSON, nullable=True,
                  comment='List of KnowledgeBeast document IDs for this entry')
    )
    op.add_column(
        'knowledge_entries',
        sa.Column('search_mode', sa.String(50), nullable=True,
                  comment='Search mode used: vector, keyword, or hybrid')
    )
    op.add_column(
        'knowledge_entries',
        sa.Column('kb_chunk_count', sa.Integer, nullable=True,
                  comment='Number of chunks created in KnowledgeBeast')
    )

    # Populate kb_collection_name based on project_id for existing entries
    # Collection naming: project_{project_id}
    op.execute("""
        UPDATE knowledge_entries
        SET kb_collection_name = 'project_' || project_id::text
        WHERE kb_collection_name IS NULL
    """)


def downgrade() -> None:
    """Remove KnowledgeBeast integration columns"""

    op.drop_column('knowledge_entries', 'kb_chunk_count')
    op.drop_column('knowledge_entries', 'search_mode')
    op.drop_column('knowledge_entries', 'kb_document_ids')
    op.drop_column('knowledge_entries', 'kb_collection_name')
