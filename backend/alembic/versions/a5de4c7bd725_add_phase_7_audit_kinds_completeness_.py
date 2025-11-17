"""Add Phase 7 audit kinds (completeness, consistency, drift)

Revision ID: a5de4c7bd725
Revises: 18d6609ae6d0
Create Date: 2025-11-17 22:57:32.759694

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a5de4c7bd725"
down_revision: Union[str, Sequence[str], None] = "18d6609ae6d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Phase 7 audit kinds to auditkind enum"""
    # Add new enum values to auditkind type
    # Both lowercase and uppercase versions for compatibility
    op.execute("ALTER TYPE auditkind ADD VALUE IF NOT EXISTS 'completeness'")
    op.execute("ALTER TYPE auditkind ADD VALUE IF NOT EXISTS 'consistency'")
    op.execute("ALTER TYPE auditkind ADD VALUE IF NOT EXISTS 'drift'")
    op.execute("ALTER TYPE auditkind ADD VALUE IF NOT EXISTS 'COMPLETENESS'")
    op.execute("ALTER TYPE auditkind ADD VALUE IF NOT EXISTS 'CONSISTENCY'")
    op.execute("ALTER TYPE auditkind ADD VALUE IF NOT EXISTS 'DRIFT'")


def downgrade() -> None:
    """Remove Phase 7 audit kinds (not supported - enums cannot be removed easily)"""
    # PostgreSQL doesn't support removing enum values directly
    # Would require creating new type and migrating data
    pass
