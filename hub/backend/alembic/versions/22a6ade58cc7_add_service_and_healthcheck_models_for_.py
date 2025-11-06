"""Add Service and HealthCheck models for health monitoring

Revision ID: 22a6ade58cc7
Revises: a1b2c3d4e5f6
Create Date: 2025-11-05 17:23:30.462553

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '22a6ade58cc7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing tables if they exist (from previous incomplete migrations)
    op.execute("DROP TABLE IF EXISTS health_checks")
    op.execute("DROP TABLE IF EXISTS services")

    # Create services table
    op.create_table('services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('service_type', sa.Enum('database', 'cache', 'api', 'web', 'queue', 'worker', name='servicetype'), nullable=False),

        # Health Configuration
        sa.Column('health_url', sa.String(), nullable=True),
        sa.Column('health_method', sa.Enum('http', 'tcp', 'exec', 'redis', 'postgres', name='healthmethod'), nullable=True),
        sa.Column('health_interval', sa.Integer(), nullable=True),
        sa.Column('health_timeout', sa.Integer(), nullable=True),
        sa.Column('health_retries', sa.Integer(), nullable=True),
        sa.Column('health_threshold', sa.Float(), nullable=True),

        # Health Status
        sa.Column('health_status', sa.Enum('up', 'down', 'degraded', 'unknown', name='healthstatus'), nullable=True),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=True),
        sa.Column('consecutive_successes', sa.Integer(), nullable=True),
        sa.Column('health_details', sa.JSON(), nullable=True),

        # Service Info
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('container_id', sa.String(), nullable=True),
        sa.Column('internal_url', sa.String(), nullable=True),
        sa.Column('external_url', sa.String(), nullable=True),

        # Metrics
        sa.Column('total_checks', sa.Integer(), nullable=True),
        sa.Column('failed_checks', sa.Integer(), nullable=True),
        sa.Column('average_latency', sa.Float(), nullable=True),
        sa.Column('uptime_seconds', sa.Integer(), nullable=True),
        sa.Column('last_error', sa.String(), nullable=True),

        # Flags
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.Column('auto_restart', sa.Boolean(), nullable=True),
        sa.Column('alerts_enabled', sa.Boolean(), nullable=True),

        # Timestamps
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_services_id'), 'services', ['id'], unique=False)
    op.create_index(op.f('ix_services_project_id'), 'services', ['project_id'], unique=False)

    # Create health_checks table
    op.create_table('health_checks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('up', 'down', 'degraded', 'unknown', name='healthstatus'), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('checked_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_health_checks_id'), 'health_checks', ['id'], unique=False)
    op.create_index(op.f('ix_health_checks_service_id'), 'health_checks', ['service_id'], unique=False)


def downgrade() -> None:
    # Drop indexes and tables
    op.drop_index(op.f('ix_health_checks_service_id'), table_name='health_checks')
    op.drop_index(op.f('ix_health_checks_id'), table_name='health_checks')
    op.drop_table('health_checks')

    op.drop_index(op.f('ix_services_project_id'), table_name='services')
    op.drop_index(op.f('ix_services_id'), table_name='services')
    op.drop_table('services')
