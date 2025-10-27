"""enable_pgvector_extension

Enable pgvector extension for vector similarity search.

Required for KnowledgeBeast v3.0 PostgresBackend to store and query
document embeddings using PostgreSQL with pgvector.

Revision ID: e5bd4ea700b0
Revises: 013_merge_heads
Create Date: 2025-10-26 20:36:44.446945

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5bd4ea700b0'
down_revision: Union[str, Sequence[str], None] = '013_merge_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enable pgvector extension for vector similarity search.

    This extension provides:
    - vector data type for storing embeddings
    - vector_cosine_ops for cosine similarity search
    - HNSW and IVFFlat index support

    Note: Requires PostgreSQL 11+ and pgvector extension installed.
    In Docker: Use custom postgres image with pgvector (see dagger_modules/postgres.py)
    """
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create helper function for updating timestamps (if not exists)
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)


def downgrade() -> None:
    """
    Disable pgvector extension.

    WARNING: This will drop all vector columns and indexes!
    Only use in development. In production, this could cause data loss.
    """
    # Drop helper function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE")

    # Disable pgvector extension
    # Note: This will fail if any tables still use vector columns
    op.execute("DROP EXTENSION IF EXISTS vector CASCADE")
