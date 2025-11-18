"""Initial schema - projects table

Revision ID: 001_projects_table
Revises:
Create Date: 2025-11-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_projects_table'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type
    op.execute("CREATE TYPE project_status AS ENUM ('online', 'offline', 'degraded')")

    # Create projects table
    op.create_table('projects',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('hub_url', sa.String(length=500), nullable=False),
    sa.Column('mesh_namespace', sa.String(length=100), nullable=True),
    sa.Column('status', postgresql.ENUM('online', 'offline', 'degraded', name='project_status', create_type=False), nullable=False),
    sa.Column('tags', sa.JSON(), nullable=True),
    sa.Column('last_heartbeat_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_slug'), 'projects', ['slug'], unique=True)
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_projects_status'), table_name='projects')
    op.drop_index(op.f('ix_projects_slug'), table_name='projects')
    op.drop_table('projects')
    op.execute("DROP TYPE project_status")
