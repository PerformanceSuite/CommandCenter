"""add_document_intelligence_entities

Revision ID: doc1nt3ll001
Revises: sk1lls00001a, fd12cd853b12
Create Date: 2026-01-02 11:30:00.000000

Adds Document Intelligence entity types for Sprint 6:
- graph_documents: Document metadata and classification
- graph_concepts: Extracted concepts from documents
- graph_requirements: Mined requirements from documents
- Extended LinkType enum with document relationship types
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "doc1nt3ll001"
down_revision: Union[str, Sequence[str], None] = ("sk1lls00001a", "fd12cd853b12")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get dialect to handle PostgreSQL vs SQLite differences
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # Create new enum types for PostgreSQL
        op.execute(
            """
            CREATE TYPE documenttype AS ENUM (
                'plan', 'concept', 'guide', 'reference', 'report', 'session', 'archive'
            )
        """
        )
        op.execute(
            """
            CREATE TYPE documentstatus AS ENUM (
                'active', 'completed', 'superseded', 'abandoned', 'stale'
            )
        """
        )
        op.execute(
            """
            CREATE TYPE concepttype AS ENUM (
                'product', 'feature', 'module', 'process', 'technology', 'framework', 'methodology', 'other'
            )
        """
        )
        op.execute(
            """
            CREATE TYPE conceptstatus AS ENUM (
                'proposed', 'active', 'implemented', 'deprecated', 'unknown'
            )
        """
        )
        op.execute(
            """
            CREATE TYPE requirementtype AS ENUM (
                'functional', 'nonFunctional', 'constraint', 'dependency', 'outcome'
            )
        """
        )
        op.execute(
            """
            CREATE TYPE requirementpriority AS ENUM (
                'critical', 'high', 'medium', 'low', 'unknown'
            )
        """
        )
        op.execute(
            """
            CREATE TYPE requirementstatus AS ENUM (
                'proposed', 'accepted', 'implemented', 'verified', 'unknown'
            )
        """
        )
        op.execute(
            """
            CREATE TYPE confidencelevel AS ENUM (
                'high', 'medium', 'low'
            )
        """
        )

        # Add new values to linktype enum (each must be separate for asyncpg)
        op.execute("ALTER TYPE linktype ADD VALUE IF NOT EXISTS 'integratesWith'")
        op.execute("ALTER TYPE linktype ADD VALUE IF NOT EXISTS 'providesTo'")
        op.execute("ALTER TYPE linktype ADD VALUE IF NOT EXISTS 'replaces'")
        op.execute("ALTER TYPE linktype ADD VALUE IF NOT EXISTS 'similarTo'")
        op.execute("ALTER TYPE linktype ADD VALUE IF NOT EXISTS 'supersedes'")
        op.execute("ALTER TYPE linktype ADD VALUE IF NOT EXISTS 'extractsFrom'")

    # Create graph_documents table
    # Use String for enum columns to support both SQLite and PostgreSQL
    op.create_table(
        "graph_documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("doc_type", sa.String(length=50), nullable=False),
        sa.Column("subtype", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("audience", sa.String(length=255), nullable=True),
        sa.Column("value_assessment", sa.String(length=20), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("staleness_score", sa.Integer(), nullable=True),
        sa.Column("last_meaningful_date", sa.DateTime(), nullable=True),
        sa.Column("recommended_action", sa.String(length=50), nullable=True),
        sa.Column("target_location", sa.String(length=512), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_analyzed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_graph_documents_project_id", "graph_documents", ["project_id"])
    op.create_index("ix_graph_documents_path", "graph_documents", ["path"])
    op.create_index("ix_graph_documents_doc_type", "graph_documents", ["doc_type"])
    op.create_index("ix_graph_documents_status", "graph_documents", ["status"])

    # Create graph_concepts table
    op.create_table(
        "graph_concepts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("concept_type", sa.String(length=50), nullable=False),
        sa.Column("definition", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("domain", sa.String(length=100), nullable=True),
        sa.Column("source_quote", sa.Text(), nullable=True),
        sa.Column("confidence", sa.String(length=20), nullable=False),
        sa.Column("related_entities", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_document_id"], ["graph_documents.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_graph_concepts_project_id", "graph_concepts", ["project_id"])
    op.create_index(
        "ix_graph_concepts_source_document_id", "graph_concepts", ["source_document_id"]
    )
    op.create_index("ix_graph_concepts_name", "graph_concepts", ["name"])
    op.create_index("ix_graph_concepts_concept_type", "graph_concepts", ["concept_type"])
    op.create_index("ix_graph_concepts_status", "graph_concepts", ["status"])

    # Create graph_requirements table
    op.create_table(
        "graph_requirements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("req_id", sa.String(length=50), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("req_type", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("source_concept", sa.String(length=255), nullable=True),
        sa.Column("source_quote", sa.Text(), nullable=True),
        sa.Column("verification", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_document_id"], ["graph_documents.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_graph_requirements_project_id", "graph_requirements", ["project_id"])
    op.create_index(
        "ix_graph_requirements_source_document_id", "graph_requirements", ["source_document_id"]
    )
    op.create_index("ix_graph_requirements_req_id", "graph_requirements", ["req_id"])
    op.create_index("ix_graph_requirements_req_type", "graph_requirements", ["req_type"])
    op.create_index("ix_graph_requirements_priority", "graph_requirements", ["priority"])
    op.create_index("ix_graph_requirements_status", "graph_requirements", ["status"])


def downgrade() -> None:
    # Drop tables
    op.drop_table("graph_requirements")
    op.drop_table("graph_concepts")
    op.drop_table("graph_documents")

    # Drop enum types (PostgreSQL only)
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("DROP TYPE IF EXISTS confidencelevel")
        op.execute("DROP TYPE IF EXISTS requirementstatus")
        op.execute("DROP TYPE IF EXISTS requirementpriority")
        op.execute("DROP TYPE IF EXISTS requirementtype")
        op.execute("DROP TYPE IF EXISTS conceptstatus")
        op.execute("DROP TYPE IF EXISTS concepttype")
        op.execute("DROP TYPE IF EXISTS documentstatus")
        op.execute("DROP TYPE IF EXISTS documenttype")

    # Note: LinkType enum values cannot be easily removed in PostgreSQL
    # They will remain but won't affect functionality
