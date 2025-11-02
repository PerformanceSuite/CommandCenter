"""Add Technology Radar v2 fields

Revision ID: 005_add_technology_radar_v2_fields
Revises: 004_knowledgebeast_integration
Create Date: 2025-10-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_tech_radar_v2"
down_revision: Union[str, Sequence[str], None] = "004_knowledgebeast_integration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add Technology Radar v2 fields to technologies table

    New fields support comprehensive technology evaluation:
    - Performance metrics (latency, throughput)
    - Integration assessment (difficulty, time estimate)
    - Maturity and stability scoring
    - Cost analysis
    - Dependencies and alternatives tracking
    - Automated monitoring metrics (HN mentions, GitHub stats)
    """
    # Create enum types FIRST (PostgreSQL requires this before using them in columns)
    integration_difficulty_enum = postgresql.ENUM(
        "trivial",
        "easy",
        "moderate",
        "complex",
        "very_complex",
        name="integrationdifficulty",
        create_type=False,
    )
    integration_difficulty_enum.create(op.get_bind(), checkfirst=True)

    maturity_level_enum = postgresql.ENUM(
        "alpha", "beta", "stable", "mature", "legacy", name="maturitylevel", create_type=False
    )
    maturity_level_enum.create(op.get_bind(), checkfirst=True)

    cost_tier_enum = postgresql.ENUM(
        "free",
        "freemium",
        "affordable",
        "moderate",
        "expensive",
        "enterprise",
        name="costtier",
        create_type=False,
    )
    cost_tier_enum.create(op.get_bind(), checkfirst=True)

    # Performance characteristics
    op.add_column(
        "technologies",
        sa.Column("latency_ms", sa.Float(), nullable=True, comment="P99 latency in milliseconds"),
    )
    op.add_column(
        "technologies",
        sa.Column(
            "throughput_qps",
            sa.Integer(),
            nullable=True,
            comment="Throughput in queries per second",
        ),
    )

    # Integration assessment
    op.add_column(
        "technologies",
        sa.Column(
            "integration_difficulty",
            sa.Enum(
                "trivial",
                "easy",
                "moderate",
                "complex",
                "very_complex",
                name="integrationdifficulty",
            ),
            nullable=True,
            comment="Estimated integration complexity",
        ),
    )
    op.add_column(
        "technologies",
        sa.Column(
            "integration_time_estimate_days",
            sa.Integer(),
            nullable=True,
            comment="Estimated integration time in days",
        ),
    )

    # Maturity and stability
    op.add_column(
        "technologies",
        sa.Column(
            "maturity_level",
            sa.Enum("alpha", "beta", "stable", "mature", "legacy", name="maturitylevel"),
            nullable=True,
            comment="Technology maturity level",
        ),
    )
    op.add_column(
        "technologies",
        sa.Column(
            "stability_score", sa.Integer(), nullable=True, comment="Stability score (0-100)"
        ),
    )

    # Cost analysis
    op.add_column(
        "technologies",
        sa.Column(
            "cost_tier",
            sa.Enum(
                "free",
                "freemium",
                "affordable",
                "moderate",
                "expensive",
                "enterprise",
                name="costtier",
            ),
            nullable=True,
            comment="Cost tier category",
        ),
    )
    op.add_column(
        "technologies",
        sa.Column(
            "cost_monthly_usd", sa.Float(), nullable=True, comment="Estimated monthly cost in USD"
        ),
    )

    # Dependencies and relationships
    op.add_column(
        "technologies",
        sa.Column(
            "dependencies",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
            comment="Technology dependencies as JSON",
        ),
    )
    op.add_column(
        "technologies",
        sa.Column(
            "alternatives",
            sa.Text(),
            nullable=True,
            comment="Comma-separated list of alternative technology IDs",
        ),
    )

    # Monitoring and alerts
    op.add_column(
        "technologies",
        sa.Column(
            "last_hn_mention",
            sa.DateTime(),
            nullable=True,
            comment="Last HackerNews mention timestamp",
        ),
    )
    op.add_column(
        "technologies",
        sa.Column(
            "hn_score_avg", sa.Integer(), nullable=True, comment="Average HackerNews story score"
        ),
    )
    op.add_column(
        "technologies",
        sa.Column(
            "github_stars", sa.Integer(), nullable=True, comment="GitHub repository star count"
        ),
    )
    op.add_column(
        "technologies",
        sa.Column(
            "github_last_commit",
            sa.DateTime(),
            nullable=True,
            comment="Last GitHub commit timestamp",
        ),
    )


def downgrade() -> None:
    """Remove Technology Radar v2 fields"""
    # Drop monitoring fields
    op.drop_column("technologies", "github_last_commit")
    op.drop_column("technologies", "github_stars")
    op.drop_column("technologies", "hn_score_avg")
    op.drop_column("technologies", "last_hn_mention")

    # Drop dependencies fields
    op.drop_column("technologies", "alternatives")
    op.drop_column("technologies", "dependencies")

    # Drop cost fields
    op.drop_column("technologies", "cost_monthly_usd")
    op.drop_column("technologies", "cost_tier")

    # Drop maturity fields
    op.drop_column("technologies", "stability_score")
    op.drop_column("technologies", "maturity_level")

    # Drop integration fields
    op.drop_column("technologies", "integration_time_estimate_days")
    op.drop_column("technologies", "integration_difficulty")

    # Drop performance fields
    op.drop_column("technologies", "throughput_qps")
    op.drop_column("technologies", "latency_ms")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS integrationdifficulty")
    op.execute("DROP TYPE IF EXISTS maturitylevel")
    op.execute("DROP TYPE IF EXISTS costtier")
