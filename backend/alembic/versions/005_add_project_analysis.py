"""add project analysis table

Revision ID: 005
Revises: 004
Create Date: 2025-10-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """Create project_analyses table"""
    op.create_table(
        'project_analyses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_path', sa.String(length=1024), nullable=False),
        sa.Column('detected_technologies', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('dependencies', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('code_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('research_gaps', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('analysis_version', sa.String(length=50), nullable=False, server_default='1.0.0'),
        sa.Column('analysis_duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('analyzed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for common queries
    op.create_index(
        'ix_project_analyses_project_path',
        'project_analyses',
        ['project_path'],
        unique=True
    )
    op.create_index(
        'ix_project_analyses_analyzed_at',
        'project_analyses',
        ['analyzed_at']
    )


def downgrade():
    """Drop project_analyses table"""
    op.drop_index('ix_project_analyses_analyzed_at', table_name='project_analyses')
    op.drop_index('ix_project_analyses_project_path', table_name='project_analyses')
    op.drop_table('project_analyses')
