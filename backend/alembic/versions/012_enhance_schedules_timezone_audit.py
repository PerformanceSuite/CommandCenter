"""Enhance schedules with timezone and audit logging

Revision ID: 012_enhance_schedules
Revises: 011_add_webhook_deliveries
Create Date: 2025-10-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '012_enhance_schedules'
down_revision: Union[str, Sequence[str], None] = '011_add_webhook_deliveries'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add timezone and audit logging fields to schedules table."""

    # Add timezone support
    op.add_column('schedules', sa.Column('timezone', sa.String(50), nullable=False, server_default='UTC'))

    # Add audit logging fields
    op.add_column('schedules', sa.Column('last_error', sa.String(1000), nullable=True))
    op.add_column('schedules', sa.Column('last_success_at', sa.DateTime(), nullable=True))
    op.add_column('schedules', sa.Column('last_failure_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove timezone and audit logging fields from schedules table."""

    # Remove audit logging fields
    op.drop_column('schedules', 'last_failure_at')
    op.drop_column('schedules', 'last_success_at')
    op.drop_column('schedules', 'last_error')

    # Remove timezone support
    op.drop_column('schedules', 'timezone')
