"""Merge migration heads

Revision ID: 013_merge_heads
Revises: 012_performance_indexes, 012_enhance_schedules
Create Date: 2025-10-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '013_merge_heads'
down_revision: Union[str, Sequence[str], None] = ('012_performance_indexes', '012_enhance_schedules')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge migration heads - no changes needed."""
    pass


def downgrade() -> None:
    """Merge migration heads - no changes needed."""
    pass
