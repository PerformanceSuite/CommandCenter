"""Merge migration heads

Revision ID: 006_merge_heads
Revises: 005_add_project_analysis, 005_tech_radar_v2
Create Date: 2025-10-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_merge_heads"
down_revision: Union[str, Sequence[str], None] = ("005_add_project_analysis", "005_tech_radar_v2")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge heads - no changes needed"""
    pass


def downgrade() -> None:
    """Merge heads - no changes needed"""
    pass
