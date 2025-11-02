"""merge migration heads

Revision ID: d4dff12b63d6
Revises: 014_add_ingestion_sources, e5bd4ea700b0
Create Date: 2025-11-02 09:00:03.150452

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4dff12b63d6"
down_revision: Union[str, Sequence[str], None] = ("014_add_ingestion_sources", "e5bd4ea700b0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
