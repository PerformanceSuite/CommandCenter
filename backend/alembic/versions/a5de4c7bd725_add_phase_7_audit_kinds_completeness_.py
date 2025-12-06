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
    # First, check if the auditkind enum exists. If not, create it with all values.
    # This handles both fresh databases and existing databases.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'auditkind') THEN
                CREATE TYPE auditkind AS ENUM (
                    'codeReview', 'security', 'license', 'compliance',
                    'performance', 'testCoverage', 'completeness', 'consistency', 'drift'
                );
            ELSE
                -- Add new enum values if they don't exist
                BEGIN
                    ALTER TYPE auditkind ADD VALUE IF NOT EXISTS 'completeness';
                EXCEPTION WHEN duplicate_object THEN NULL;
                END;
                BEGIN
                    ALTER TYPE auditkind ADD VALUE IF NOT EXISTS 'consistency';
                EXCEPTION WHEN duplicate_object THEN NULL;
                END;
                BEGIN
                    ALTER TYPE auditkind ADD VALUE IF NOT EXISTS 'drift';
                EXCEPTION WHEN duplicate_object THEN NULL;
                END;
            END IF;
        END
        $$;
    """
    )


def downgrade() -> None:
    """Remove Phase 7 audit kinds (not supported - enums cannot be removed easily)"""
    # PostgreSQL doesn't support removing enum values directly
    # Would require creating new type and migrating data
    pass
