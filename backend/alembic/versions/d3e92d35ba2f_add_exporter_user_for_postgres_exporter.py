"""add exporter user for postgres_exporter

Revision ID: d3e92d35ba2f
Revises: d4dff12b63d6
Create Date: 2025-11-02 09:00:07.653730

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3e92d35ba2f"
down_revision: Union[str, Sequence[str], None] = "d4dff12b63d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create exporter_user role for postgres_exporter monitoring.

    The exporter_user has minimal read-only privileges:
    - CONNECT to database
    - pg_monitor role (grants access to monitoring views)

    Password should be set via environment variable EXPORTER_PASSWORD.
    """
    # Note: Password will be set from environment in docker-compose
    op.execute(
        """
        DO $$
        BEGIN
            -- Create user if not exists
            IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'exporter_user') THEN
                CREATE USER exporter_user WITH PASSWORD 'changeme';
            END IF;
        END
        $$;
    """
    )

    # Grant connection privilege
    op.execute("GRANT CONNECT ON DATABASE commandcenter TO exporter_user;")

    # Grant pg_monitor role for access to monitoring views
    op.execute("GRANT pg_monitor TO exporter_user;")


def downgrade() -> None:
    """Remove exporter_user role."""
    # Revoke privileges
    op.execute("REVOKE pg_monitor FROM exporter_user;")
    op.execute("REVOKE CONNECT ON DATABASE commandcenter FROM exporter_user;")

    # Drop user
    op.execute("DROP USER IF EXISTS exporter_user;")
