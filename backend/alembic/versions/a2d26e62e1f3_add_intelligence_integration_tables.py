"""add_intelligence_integration_tables

Revision ID: a2d26e62e1f3
Revises: 9ce77bee762b
Create Date: 2025-12-30 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a2d26e62e1f3"
down_revision: Union[str, Sequence[str], None] = "9ce77bee762b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def create_enum_if_not_exists(enum_name: str, values: list[str]) -> None:
    """Create PostgreSQL enum type if it doesn't already exist."""
    values_str = ", ".join(f"'{v}'" for v in values)
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}') THEN
                CREATE TYPE {enum_name} AS ENUM ({values_str});
            END IF;
        END$$;
        """
    )


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """Create intelligence integration tables: hypotheses, evidence, debates, research_findings."""

    # Create enum types first (idempotent)
    create_enum_if_not_exists(
        "hypothesiscategory",
        [
            "customer",
            "problem",
            "solution",
            "technical",
            "market",
            "regulatory",
            "competitive",
            "gtm",
        ],
    )
    create_enum_if_not_exists(
        "hypothesisstatus",
        ["untested", "validating", "validated", "invalidated", "needs_more_data"],
    )
    create_enum_if_not_exists("impactlevel", ["high", "medium", "low"])
    create_enum_if_not_exists("risklevel", ["high", "medium", "low"])
    create_enum_if_not_exists(
        "evidencesourcetype",
        ["research_finding", "knowledge_base", "manual", "external"],
    )
    create_enum_if_not_exists("evidencestance", ["supporting", "contradicting", "neutral"])
    create_enum_if_not_exists("debatestatus", ["pending", "running", "completed", "failed"])
    create_enum_if_not_exists("consensuslevel", ["strong", "moderate", "weak", "deadlock"])
    create_enum_if_not_exists("debateverdict", ["validated", "invalidated", "needs_more_data"])
    create_enum_if_not_exists(
        "findingtype", ["fact", "claim", "insight", "question", "recommendation"]
    )

    # Create hypotheses table (check if exists for idempotency)
    if not table_exists("hypotheses"):
        op.create_table(
            "hypotheses",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("research_task_id", sa.Integer(), nullable=False),
            sa.Column("statement", sa.Text(), nullable=False),
            sa.Column(
                "category",
                postgresql.ENUM(
                    "customer",
                    "problem",
                    "solution",
                    "technical",
                    "market",
                    "regulatory",
                    "competitive",
                    "gtm",
                    name="hypothesiscategory",
                    create_type=False,
                ),
                nullable=False,
            ),
            sa.Column(
                "status",
                postgresql.ENUM(
                    "untested",
                    "validating",
                    "validated",
                    "invalidated",
                    "needs_more_data",
                    name="hypothesisstatus",
                    create_type=False,
                ),
                nullable=False,
            ),
            sa.Column(
                "impact",
                postgresql.ENUM("high", "medium", "low", name="impactlevel", create_type=False),
                nullable=False,
            ),
            sa.Column(
                "risk",
                postgresql.ENUM("high", "medium", "low", name="risklevel", create_type=False),
                nullable=False,
            ),
            sa.Column("priority_score", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("validation_score", sa.Float(), nullable=True),
            sa.Column("knowledge_entry_id", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["research_task_id"], ["research_tasks.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_hypotheses_project_id"), "hypotheses", ["project_id"], unique=False
        )
        op.create_index(
            op.f("ix_hypotheses_research_task_id"),
            "hypotheses",
            ["research_task_id"],
            unique=False,
        )

    # Create evidence table
    if not table_exists("evidence"):
        op.create_table(
            "evidence",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("hypothesis_id", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column(
                "source_type",
                postgresql.ENUM(
                    "research_finding",
                    "knowledge_base",
                    "manual",
                    "external",
                    name="evidencesourcetype",
                    create_type=False,
                ),
                nullable=False,
            ),
            sa.Column("source_id", sa.String(length=255), nullable=True),
            sa.Column(
                "stance",
                postgresql.ENUM(
                    "supporting",
                    "contradicting",
                    "neutral",
                    name="evidencestance",
                    create_type=False,
                ),
                nullable=False,
            ),
            sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["hypothesis_id"], ["hypotheses.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_evidence_hypothesis_id"), "evidence", ["hypothesis_id"], unique=False
        )

    # Create debates table
    if not table_exists("debates"):
        op.create_table(
            "debates",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("hypothesis_id", sa.Integer(), nullable=False),
            sa.Column(
                "status",
                postgresql.ENUM(
                    "pending",
                    "running",
                    "completed",
                    "failed",
                    name="debatestatus",
                    create_type=False,
                ),
                nullable=False,
            ),
            sa.Column("rounds_requested", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("rounds_completed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("agents_used", sa.JSON(), nullable=True),
            sa.Column(
                "consensus_level",
                postgresql.ENUM(
                    "strong",
                    "moderate",
                    "weak",
                    "deadlock",
                    name="consensuslevel",
                    create_type=False,
                ),
                nullable=True,
            ),
            sa.Column(
                "final_verdict",
                postgresql.ENUM(
                    "validated",
                    "invalidated",
                    "needs_more_data",
                    name="debateverdict",
                    create_type=False,
                ),
                nullable=True,
            ),
            sa.Column("verdict_reasoning", sa.Text(), nullable=True),
            sa.Column("gap_analysis", sa.JSON(), nullable=True),
            sa.Column("suggested_research", sa.JSON(), nullable=True),
            sa.Column("knowledge_entry_id", sa.String(length=255), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=False),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["hypothesis_id"], ["hypotheses.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_debates_hypothesis_id"), "debates", ["hypothesis_id"], unique=False
        )

    # Create research_findings table
    if not table_exists("research_findings"):
        op.create_table(
            "research_findings",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("research_task_id", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column(
                "finding_type",
                postgresql.ENUM(
                    "fact",
                    "claim",
                    "insight",
                    "question",
                    "recommendation",
                    name="findingtype",
                    create_type=False,
                ),
                nullable=False,
            ),
            sa.Column("agent_role", sa.String(length=100), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
            sa.Column("sources", sa.JSON(), nullable=True),
            sa.Column("knowledge_entry_id", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["research_task_id"], ["research_tasks.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_research_findings_research_task_id"),
            "research_findings",
            ["research_task_id"],
            unique=False,
        )

    # Add task_type column to research_tasks (idempotent)
    if table_exists("research_tasks") and not column_exists("research_tasks", "task_type"):
        op.add_column(
            "research_tasks",
            sa.Column(
                "task_type",
                sa.String(length=50),
                nullable=False,
                server_default="research",
            ),
        )


def downgrade() -> None:
    """Drop intelligence integration tables."""

    # Remove task_type column from research_tasks
    if table_exists("research_tasks") and column_exists("research_tasks", "task_type"):
        op.drop_column("research_tasks", "task_type")

    # Drop research_findings table
    if table_exists("research_findings"):
        op.drop_index(op.f("ix_research_findings_research_task_id"), table_name="research_findings")
        op.drop_table("research_findings")

    # Drop debates table
    if table_exists("debates"):
        op.drop_index(op.f("ix_debates_hypothesis_id"), table_name="debates")
        op.drop_table("debates")

    # Drop evidence table
    if table_exists("evidence"):
        op.drop_index(op.f("ix_evidence_hypothesis_id"), table_name="evidence")
        op.drop_table("evidence")

    # Drop hypotheses table
    if table_exists("hypotheses"):
        op.drop_index(op.f("ix_hypotheses_research_task_id"), table_name="hypotheses")
        op.drop_index(op.f("ix_hypotheses_project_id"), table_name="hypotheses")
        op.drop_table("hypotheses")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS findingtype")
    op.execute("DROP TYPE IF EXISTS debateverdict")
    op.execute("DROP TYPE IF EXISTS consensuslevel")
    op.execute("DROP TYPE IF EXISTS debatestatus")
    op.execute("DROP TYPE IF EXISTS evidencestance")
    op.execute("DROP TYPE IF EXISTS evidencesourcetype")
    op.execute("DROP TYPE IF EXISTS risklevel")
    op.execute("DROP TYPE IF EXISTS impactlevel")
    op.execute("DROP TYPE IF EXISTS hypothesisstatus")
    op.execute("DROP TYPE IF EXISTS hypothesiscategory")
