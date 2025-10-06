"""Add security features: User model and token encryption

Revision ID: 001_add_security
Revises: 62ebb9783d8e
Create Date: 2025-10-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_security'
down_revision = '62ebb9783d8e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Alter repositories table to increase access_token column size for encryption
    # Encrypted tokens are larger than plain tokens
    op.alter_column(
        'repositories',
        'access_token',
        existing_type=sa.String(length=512),
        type_=sa.String(length=1024),
        existing_nullable=True
    )


def downgrade() -> None:
    # Drop users table
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    # Revert repositories.access_token column size
    op.alter_column(
        'repositories',
        'access_token',
        existing_type=sa.String(length=1024),
        type_=sa.String(length=512),
        existing_nullable=True
    )
