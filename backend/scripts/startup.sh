#!/bin/bash
set -e

echo "=== Command Center Backend Startup ==="
echo "Starting at $(date)"

# Configuration
MAX_RETRIES=30
RETRY_INTERVAL=2

# Function to wait for database
wait_for_db() {
    echo "Waiting for database to be ready..."
    local retries=0

    while [ $retries -lt $MAX_RETRIES ]; do
        if python -c "
import sys
import asyncio
from sqlalchemy import create_engine, text
from app.config import settings

try:
    # For PostgreSQL, use psycopg2 synchronous connection for simple check
    if settings.database_url.startswith('postgresql'):
        db_url = settings.database_url.replace('+asyncpg', '').replace('postgresql://', 'postgresql+psycopg2://')
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('Database is ready!')
        sys.exit(0)
    else:
        # For SQLite, just check if it's accessible
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('Database is ready!')
        sys.exit(0)
except Exception as e:
    print(f'Database not ready: {e}')
    sys.exit(1)
" 2>&1; then
            echo "✓ Database connection successful"
            return 0
        fi

        retries=$((retries + 1))
        echo "Database not ready yet (attempt $retries/$MAX_RETRIES). Retrying in ${RETRY_INTERVAL}s..."
        sleep $RETRY_INTERVAL
    done

    echo "✗ Failed to connect to database after $MAX_RETRIES attempts"
    exit 1
}

# Function to run migrations
run_migrations() {
    echo "Running database migrations..."

    # First, try to merge any multiple heads
    echo "Checking for multiple migration heads..."
    if alembic heads 2>&1 | grep -q "head"; then
        echo "Attempting to upgrade to heads..."
        if alembic upgrade heads 2>&1; then
            echo "✓ Migrations completed successfully"
            return 0
        fi
    fi

    # Try normal upgrade
    if alembic upgrade head 2>&1; then
        echo "✓ Migrations completed successfully"
        return 0
    else
        echo "✗ Migration failed"
        echo "Note: This may be due to migration conflicts. Check alembic logs."
        exit 1
    fi
}

# Function to create default admin user (optional)
create_default_user() {
    echo "Checking for default user..."

    python -c "
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User
from app.auth.jwt import get_password_hash
import os

async def create_user():
    async with AsyncSessionLocal() as session:
        # Check if any user exists
        result = await session.execute(select(User).limit(1))
        existing_user = result.scalars().first()

        if existing_user:
            print('Users already exist. Skipping default user creation.')
            return

        # Create default admin user
        default_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@commandcenter.local')
        default_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'changeme')

        admin_user = User(
            email=default_email,
            username='admin',
            hashed_password=get_password_hash(default_password),
            is_active=True,
            is_superuser=True
        )

        session.add(admin_user)
        await session.commit()
        print(f'✓ Created default admin user: {default_email}')

try:
    asyncio.run(create_user())
except Exception as e:
    print(f'Note: Could not create default user: {e}')
" 2>&1 || echo "Note: Default user creation skipped"
}

# Main startup sequence
echo ""
echo "Step 1: Waiting for database..."
wait_for_db

echo ""
echo "Step 2: Running migrations..."
run_migrations

echo ""
echo "Step 3: Checking for default user..."
create_default_user

echo ""
echo "Step 4: Starting application server..."
echo "Environment: ${ENVIRONMENT:-development}"
echo "Database URL: ${DATABASE_URL}"
echo "Redis URL: ${REDIS_URL}"
echo ""

# Start the application
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info \
    --proxy-headers \
    --forwarded-allow-ips '*'
