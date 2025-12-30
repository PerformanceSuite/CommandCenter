"""add_intelligence_integration_tables

Revision ID: a2d26e62e1f3
Revises: 9ce77bee762b
Create Date: 2025-12-30 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2d26e62e1f3"
down_revision: Union[str, Sequence[str], None] = "9ce77bee762b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create intelligence integration tables: hypotheses, evidence, debates, research_findings."""

    # Create hypotheses table
    op.create_table(
        "hypotheses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("research_task_id", sa.Integer(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "customer",
                "problem",
                "solution",
                "technical",
                "market",
                "regulatory",
                "competitive",
                "gtm",
                name="hypothesiscategory",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "untested",
                "validating",
                "validated",
                "invalidated",
                "needs_more_data",
                name="hypothesisstatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "impact",
            sa.Enum("high", "medium", "low", name="impactlevel"),
            nullable=False,
        ),
        sa.Column(
            "risk",
            sa.Enum("high", "medium", "low", name="risklevel"),
            nullable=False,
        ),
        sa.Column("priority_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("validation_score", sa.Float(), nullable=True),
        sa.Column("knowledge_entry_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["research_task_id"], ["research_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_hypotheses_project_id"), "hypotheses", ["project_id"], unique=False)
    op.create_index(
        op.f("ix_hypotheses_research_task_id"),
        "hypotheses",
        ["research_task_id"],
        unique=False,
    )

    # Create evidence table
    op.create_table(
        "evidence",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hypothesis_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum(
                "research_finding",
                "knowledge_base",
                "manual",
                "external",
                name="evidencesourcetype",
            ),
            nullable=False,
        ),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column(
            "stance",
            sa.Enum("supporting", "contradicting", "neutral", name="evidencestance"),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["hypothesis_id"], ["hypotheses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evidence_hypothesis_id"), "evidence", ["hypothesis_id"], unique=False)

    # Create debates table
    op.create_table(
        "debates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hypothesis_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", name="debatestatus"),
            nullable=False,
        ),
        sa.Column("rounds_requested", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("rounds_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("agents_used", sa.JSON(), nullable=True),
        sa.Column(
            "consensus_level",
            sa.Enum("strong", "moderate", "weak", "deadlock", name="consensuslevel"),
            nullable=True,
        ),
        sa.Column(
            "final_verdict",
            sa.Enum("validated", "invalidated", "needs_more_data", name="debateverdict"),
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
    op.create_index(op.f("ix_debates_hypothesis_id"), "debates", ["hypothesis_id"], unique=False)

    # Create research_findings table
    op.create_table(
        "research_findings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("research_task_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "finding_type",
            sa.Enum("fact", "claim", "insight", "question", "recommendation", name="findingtype"),
            nullable=False,
        ),
        sa.Column("agent_role", sa.String(length=100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("sources", sa.JSON(), nullable=True),
        sa.Column("knowledge_entry_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["research_task_id"], ["research_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_research_findings_research_task_id"),
        "research_findings",
        ["research_task_id"],
        unique=False,
    )

    # Add task_type column to research_tasks
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
    op.drop_column("research_tasks", "task_type")

    # Drop research_findings table
    op.drop_index(op.f("ix_research_findings_research_task_id"), table_name="research_findings")
    op.drop_table("research_findings")

    # Drop debates table
    op.drop_index(op.f("ix_debates_hypothesis_id"), table_name="debates")
    op.drop_table("debates")

    # Drop evidence table
    op.drop_index(op.f("ix_evidence_hypothesis_id"), table_name="evidence")
    op.drop_table("evidence")

    # Drop hypotheses table
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
