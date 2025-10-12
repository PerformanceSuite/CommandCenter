"""
Test fixtures for project analyzer
"""
import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_package_json(tmp_path):
    """Create sample package.json"""
    package_json = tmp_path / "package.json"
    package_json.write_text(
        json.dumps(
            {
                "name": "test-project",
                "version": "1.0.0",
                "dependencies": {
                    "react": "^18.2.0",
                    "axios": "~1.4.0",
                    "express": "^4.18.0",
                },
                "devDependencies": {"jest": ">=29.0.0", "eslint": "^8.0.0"},
            }
        )
    )
    return tmp_path


@pytest.fixture
def sample_requirements_txt(tmp_path):
    """Create sample requirements.txt"""
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        """
# Core dependencies
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
pydantic>=2.5.0,<3.0.0

# Testing
pytest==7.4.0
"""
    )
    return tmp_path


@pytest.fixture
def sample_go_mod(tmp_path):
    """Create sample go.mod"""
    go_mod = tmp_path / "go.mod"
    go_mod.write_text(
        """
module example.com/myproject

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/stretchr/testify v1.8.4
    golang.org/x/crypto v0.14.0
)
"""
    )
    return tmp_path


@pytest.fixture
def sample_cargo_toml(tmp_path):
    """Create sample Cargo.toml"""
    cargo_toml = tmp_path / "Cargo.toml"
    cargo_toml.write_text(
        """
[package]
name = "myproject"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = "1.32.0"
serde = "1.0"
reqwest = "0.11"

[dev-dependencies]
criterion = "0.5"
"""
    )
    return tmp_path


@pytest.fixture
def sample_docker_compose(tmp_path):
    """Create sample docker-compose.yml"""
    docker_compose = tmp_path / "docker-compose.yml"
    docker_compose.write_text(
        """
version: '3.8'

services:
  postgres:
    image: postgres:15.3
    environment:
      POSTGRES_PASSWORD: password

  redis:
    image: redis:7.0
    ports:
      - "6379:6379"

  app:
    build: .
    depends_on:
      - postgres
      - redis
"""
    )
    return tmp_path


@pytest.fixture
def sample_multi_language_project(tmp_path):
    """Create a multi-language project with multiple config files"""
    # package.json
    package_json = tmp_path / "package.json"
    package_json.write_text(
        json.dumps(
            {
                "name": "full-stack-app",
                "dependencies": {"react": "^18.2.0", "next": "^13.0.0"},
                "devDependencies": {"vite": "^4.0.0"},
            }
        )
    )

    # requirements.txt
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("fastapi==0.109.0\nsqlalchemy==2.0.25")

    # docker-compose.yml
    docker_compose = tmp_path / "docker-compose.yml"
    docker_compose.write_text(
        """
version: '3.8'
services:
  postgres:
    image: postgres:15
"""
    )

    # Create some source files
    backend_dir = tmp_path / "backend"
    backend_dir.mkdir()
    (backend_dir / "main.py").write_text("# Main file\nprint('hello')\n")

    frontend_dir = tmp_path / "frontend"
    frontend_dir.mkdir()
    (frontend_dir / "App.tsx").write_text("// React app\nfunction App() {}\n")

    return tmp_path


@pytest.fixture
def sample_github_actions(tmp_path):
    """Create sample .github/workflows directory"""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)

    (workflows_dir / "ci.yml").write_text(
        """
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
"""
    )

    return tmp_path
