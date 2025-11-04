"""CLI test fixtures - isolated from database setup."""
import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()
