"""Add integrations table for third-party service connections

Revision ID: 009_add_integrations_table
Revises: 008_add_schedules_table
Create Date: 2025-10-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '009_add_integrations_table'
down_revision: Union[str, Sequence[str], None] = '008_add_schedules_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create integrations table."""

    # Create integrations table
    op.create_table(
        'integrations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('integration_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('auth_type', sa.String(50), nullable=False),
        sa.Column('credentials', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('access_token_encrypted', sa.Text(), nullable=True),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('token_refreshed_at', sa.DateTime(), nullable=True),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('webhook_url', sa.String(512), nullable=True),
        sa.Column('scopes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_error_at', sa.DateTime(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rate_limit_remaining', sa.Integer(), nullable=True),
        sa.Column('rate_limit_reset_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_integrations_project_id', 'integrations', ['project_id'])
    op.create_index('ix_integrations_integration_type', 'integrations', ['integration_type'])
    op.create_index('ix_integrations_status', 'integrations', ['status'])
    op.create_index('ix_integrations_enabled', 'integrations', ['enabled'])
    op.create_index('idx_integrations_project_type', 'integrations', ['project_id', 'integration_type'])


def downgrade() -> None:
    """Drop integrations table."""
    op.drop_index('idx_integrations_project_type', table_name='integrations')
    op.drop_index('ix_integrations_enabled', table_name='integrations')
    op.drop_index('ix_integrations_status', table_name='integrations')
    op.drop_index('ix_integrations_integration_type', table_name='integrations')
    op.drop_index('ix_integrations_project_id', table_name='integrations')
    op.drop_table('integrations')
