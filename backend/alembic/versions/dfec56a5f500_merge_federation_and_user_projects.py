"""merge_federation_and_user_projects

Revision ID: dfec56a5f500
Revises: 015_add_user_projects, b1c2d3e4f5a6
Create Date: 2025-12-31 14:04:43.058556

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "dfec56a5f500"
down_revision: Union[str, Sequence[str], None] = ("015_add_user_projects", "b1c2d3e4f5a6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
