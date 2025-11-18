import os
import pytest
import asyncio
import subprocess
import time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.models import Project


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    """Create test database."""
    # Allow configurable test database URL for different environments
    test_db_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://commandcenter:changeme@localhost:5432/commandcenter_fed_test"
    )
    engine = create_async_engine(
        test_db_url,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(test_db):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_db, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="session")
def nats_server():
    """
    Start embedded NATS server for integration tests.

    Assumes nats-server is installed on the system:
    - macOS: brew install nats-server
    - Linux: Download from https://github.com/nats-io/nats-server/releases

    Falls back to using existing NATS server at NATS_URL if nats-server not found.
    """
    nats_process = None

    try:
        # Try to start nats-server on port 4222
        nats_process = subprocess.Popen(
            ["nats-server", "--port", "4222"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for NATS to be ready
        time.sleep(1)

        # Check if process started successfully
        if nats_process.poll() is not None:
            raise Exception("NATS server failed to start")

        yield nats_process

    except FileNotFoundError:
        # nats-server not found - assume external NATS server is running
        print("\nWARNING: nats-server not found. Using NATS_URL from environment.")
        print("Install with: brew install nats-server (macOS)")
        yield None

    except Exception as e:
        print(f"\nWARNING: Failed to start NATS server: {e}")
        print("Using NATS_URL from environment instead.")
        yield None

    finally:
        if nats_process:
            nats_process.terminate()
            try:
                nats_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                nats_process.kill()
