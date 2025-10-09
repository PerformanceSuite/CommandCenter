"""merge migration heads

Revision ID: a7ecf93fa46a
Revises: 001_add_security, a1b2c3d4e5f6, webhook_rate_limit_001
Create Date: 2025-10-09 22:29:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7ecf93fa46a'
down_revision: Union[str, tuple, None] = ('001_add_security', 'a1b2c3d4e5f6', 'webhook_rate_limit_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
