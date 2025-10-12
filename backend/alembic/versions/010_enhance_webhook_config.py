"""Enhance webhook_configs with delivery settings and statistics

Revision ID: 010_enhance_webhook_config
Revises: 009_add_integrations_table
Create Date: 2025-10-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '010_enhance_webhook_config'
down_revision: Union[str, Sequence[str], None] = '009_add_integrations_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add delivery configuration and statistics to webhook_configs."""

    # Add delivery configuration columns
    op.add_column('webhook_configs', sa.Column('delivery_mode', sa.String(20), nullable=False, server_default='async'))
    op.add_column('webhook_configs', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='3'))
    op.add_column('webhook_configs', sa.Column('retry_delay_seconds', sa.Integer(), nullable=False, server_default='300'))
    op.add_column('webhook_configs', sa.Column('max_delivery_time_seconds', sa.Integer(), nullable=False, server_default='3600'))

    # Add statistics columns
    op.add_column('webhook_configs', sa.Column('total_deliveries', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('webhook_configs', sa.Column('successful_deliveries', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('webhook_configs', sa.Column('failed_deliveries', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Remove delivery configuration and statistics from webhook_configs."""

    # Remove statistics columns
    op.drop_column('webhook_configs', 'failed_deliveries')
    op.drop_column('webhook_configs', 'successful_deliveries')
    op.drop_column('webhook_configs', 'total_deliveries')

    # Remove delivery configuration columns
    op.drop_column('webhook_configs', 'max_delivery_time_seconds')
    op.drop_column('webhook_configs', 'retry_delay_seconds')
    op.drop_column('webhook_configs', 'retry_count')
    op.drop_column('webhook_configs', 'delivery_mode')
