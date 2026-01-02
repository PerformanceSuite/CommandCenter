"""Pytest configuration for router unit tests - isolated from parent conftest."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.project_context import get_current_project_id
from app.database import Base, get_db
from app.main import app

# Create in-memory SQLite database for unit tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency with test database."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_project_id():
    """Override auth dependency to return a test project ID."""
    return 1


@pytest.fixture
def client():
    """Create test client for FastAPI app with overridden dependencies."""
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_project_id] = override_get_current_project_id

    yield TestClient(app)

    # Clean up
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
