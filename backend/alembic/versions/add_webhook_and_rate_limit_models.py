"""Add webhook and rate limit models

Revision ID: webhook_rate_limit_001
Revises: 62ebb9783d8e
Create Date: 2025-10-05 19:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "webhook_rate_limit_001"
down_revision: Union[str, None] = "62ebb9783d8e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create webhook_configs table
    op.create_table(
        "webhook_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("webhook_id", sa.Integer(), nullable=True),
        sa.Column("webhook_url", sa.String(length=512), nullable=False),
        sa.Column("secret", sa.String(length=512), nullable=False),
        sa.Column("events", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("last_delivery_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create webhook_events table
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("config_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("delivery_id", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("repository_full_name", sa.String(length=512), nullable=True),
        sa.Column("processed", sa.Boolean(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["config_id"], ["webhook_configs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("delivery_id"),
    )

    # Create github_rate_limits table
    op.create_table(
        "github_rate_limits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("limit", sa.Integer(), nullable=False),
        sa.Column("remaining", sa.Integer(), nullable=False),
        sa.Column("reset_at", sa.DateTime(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=True),
        sa.Column("checked_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_webhook_events_event_type", "webhook_events", ["event_type"])
    op.create_index("idx_webhook_events_repository", "webhook_events", ["repository_full_name"])
    op.create_index("idx_webhook_events_processed", "webhook_events", ["processed"])
    op.create_index("idx_rate_limits_resource_type", "github_rate_limits", ["resource_type"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_rate_limits_resource_type", table_name="github_rate_limits")
    op.drop_index("idx_webhook_events_processed", table_name="webhook_events")
    op.drop_index("idx_webhook_events_repository", table_name="webhook_events")
    op.drop_index("idx_webhook_events_event_type", table_name="webhook_events")

    # Drop tables
    op.drop_table("github_rate_limits")
    op.drop_table("webhook_events")
    op.drop_table("webhook_configs")
