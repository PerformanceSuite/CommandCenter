"""Add webhook_deliveries table for delivery tracking

Revision ID: 011_add_webhook_deliveries
Revises: 010_enhance_webhook_config
Create Date: 2025-10-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '011_add_webhook_deliveries'
down_revision: Union[str, Sequence[str], None] = '010_enhance_webhook_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create webhook_deliveries table for tracking individual delivery attempts."""

    op.create_table(
        'webhook_deliveries',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('config_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('target_url', sa.String(512), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('http_status_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('scheduled_for', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('attempted_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['config_id'], ['webhook_configs.id'], ondelete='CASCADE'),
    )

    # Create indexes for common queries
    op.create_index('idx_webhook_deliveries_project', 'webhook_deliveries', ['project_id'])
    op.create_index('idx_webhook_deliveries_config', 'webhook_deliveries', ['config_id'])
    op.create_index('idx_webhook_deliveries_status', 'webhook_deliveries', ['status'])
    op.create_index('idx_webhook_deliveries_scheduled', 'webhook_deliveries', ['scheduled_for'])
    op.create_index('idx_webhook_deliveries_event_type', 'webhook_deliveries', ['event_type'])


def downgrade() -> None:
    """Drop webhook_deliveries table."""

    op.drop_index('idx_webhook_deliveries_event_type', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_deliveries_scheduled', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_deliveries_status', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_deliveries_config', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_deliveries_project', table_name='webhook_deliveries')
    op.drop_table('webhook_deliveries')
