"""Add projects last_heartbeat_at status index

Revision ID: 002_heartbeat_idx
Revises: 001_projects_table
Create Date: 2025-11-18 00:00:00

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '002_heartbeat_idx'
down_revision: Union[str, None] = '001_projects_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite index on (status, last_heartbeat_at) for stale checker performance."""
    # This index optimizes the stale checker query:
    # WHERE status = 'ONLINE' AND last_heartbeat_at < threshold
    op.create_index(
        'idx_projects_status_last_heartbeat',
        'projects',
        ['status', 'last_heartbeat_at'],
        unique=False
    )


def downgrade() -> None:
    """Remove the composite index."""
    op.drop_index('idx_projects_status_last_heartbeat', table_name='projects')
