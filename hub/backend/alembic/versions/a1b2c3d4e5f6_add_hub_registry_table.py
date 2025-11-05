"""add hub_registry table for federation

Revision ID: a1b2c3d4e5f6
Revises: 7db4424ec6b7
Create Date: 2025-01-05 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '7db4424ec6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create hub_registry table for tracking discovered Hubs."""
    op.create_table(
        'hub_registry',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('hostname', sa.String(), nullable=True),
        sa.Column('project_path', sa.String(), nullable=True),
        sa.Column('projects', sa.JSON(), nullable=True),
        sa.Column('services', sa.JSON(), nullable=True),
        sa.Column('project_count', sa.Integer(), nullable=True),
        sa.Column('service_count', sa.Integer(), nullable=True),
        sa.Column('uptime_seconds', sa.Integer(), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on last_seen for fast pruning queries
    op.create_index(
        'ix_hub_registry_last_seen',
        'hub_registry',
        ['last_seen'],
        unique=False
    )


def downgrade() -> None:
    """Drop hub_registry table."""
    op.drop_index('ix_hub_registry_last_seen', table_name='hub_registry')
    op.drop_table('hub_registry')
