# Universal Dagger Pattern for All Projects

**Version**: 1.0.0
**Date**: 2025-10-23
**Applies To**: CommandCenter, KnowledgeBeast, Performia, Veria

---

## Overview

This document defines a reusable Dagger pattern for building, testing, and deploying across all projects. Based on CommandCenter's proven implementation.

---

## Core Pattern

### 1. Config Dataclass

**Purpose**: Type-safe configuration for container stack

```python
from dataclasses import dataclass

@dataclass
class {Project}Config:
    """{Project}-specific configuration"""
    # Required fields
    project_name: str

    # Service ports (if multi-container)
    backend_port: int
    postgres_port: int

    # Secrets (generated at runtime, never stored)
    db_password: str
    secret_key: str

    # Project-specific fields
    # ... add as needed
```

**Examples:**
- CommandCenterConfig: project_path, ports for 4 services
- PostgresTestConfig: embedding_dimension, test_data_path
- PerformiaConfig: audio_path, song_library_path

### 2. Stack Class with Async Context Manager

**Purpose**: Define container stack as Python code

```python
import dagger
from typing import Optional

class {Project}Stack:
    """{Project} container stack using Dagger"""

    def __init__(self, config: {Project}Config):
        self.config = config
        self._connection: Optional[dagger.Connection] = None
        self.client = None

    async def __aenter__(self):
        """Initialize Dagger client"""
        self._connection = dagger.Connection(dagger.Config())
        self.client = await self._connection.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup Dagger client"""
        if self._connection:
            await self._connection.__aexit__(exc_type, exc_val, exc_tb)

    async def build_{service}(self) -> dagger.Container:
        """Build {service} container"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        return (
            self.client.container()
            .from_("{base_image}")
            .with_env_variable("KEY", "value")
            .with_exposed_port(port)
        )

    async def start(self) -> dict:
        """Start all containers"""
        # Build containers
        container1 = await self.build_container1()

        # Start as services
        svc1 = container1.as_service()

        return {"success": True, "services": {...}}
```

### 3. Container Builder Methods

**Pattern**: One `async def build_{service}()` method per container

```python
async def build_postgres(self) -> dagger.Container:
    """Build PostgreSQL with custom extensions"""
    return (
        self.client.container()
        .from_("postgres:16")
        # Install extensions
        .with_exec(["apt-get", "update"])
        .with_exec(["apt-get", "install", "-y", "build-essential", "git"])
        # Build pgvector
        .with_exec(["git", "clone", "https://github.com/pgvector/pgvector.git", "/tmp/pgvector"])
        .with_workdir("/tmp/pgvector")
        .with_exec(["make"])
        .with_exec(["make", "install"])
        # Configure
        .with_env_variable("POSTGRES_PASSWORD", self.config.db_password)
        .with_exposed_port(5432)
    )
```

---

## Project-Specific Implementations

### CommandCenter (Multi-Container Orchestration)

**Use Case**: Start/stop complete CommandCenter instances for different projects

**Stack**: postgres + redis + backend + frontend

```python
# hub/backend/app/dagger_modules/commandcenter.py
class CommandCenterStack:
    async def build_postgres(self) -> dagger.Container: ...
    async def build_redis(self) -> dagger.Container: ...
    async def build_backend(self) -> dagger.Container: ...
    async def build_frontend(self) -> dagger.Container: ...
```

**When Used**: Hub orchestration service (start/stop projects)

---

### KnowledgeBeast (Testing Matrix)

**Use Case**: Test PostgresBackend against real Postgres with pgvector + ParadeDB

**Stack**: Single custom Postgres container

```python
# knowledgebeast/tests/dagger_modules/postgres_test.py
from dataclasses import dataclass
import dagger

@dataclass
class PostgresTestConfig:
    """Config for KnowledgeBeast Postgres testing"""
    embedding_dimension: int = 384
    db_name: str = "kb_test"
    db_password: str = "test_password"

class PostgresTestStack:
    """Postgres container with pgvector + ParadeDB for testing"""

    def __init__(self, config: PostgresTestConfig):
        self.config = config
        self._connection: Optional[dagger.Connection] = None
        self.client = None

    async def __aenter__(self):
        self._connection = dagger.Connection(dagger.Config())
        self.client = await self._connection.__aenter__()

        # Build and start Postgres
        postgres = await self.build_postgres()
        self.postgres_svc = postgres.as_service()

        # Wait for readiness
        await self._wait_for_postgres()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._connection:
            await self._connection.__aexit__(exc_type, exc_val, exc_tb)

    async def build_postgres(self) -> dagger.Container:
        """Build Postgres with pgvector + ParadeDB"""
        return (
            self.client.container()
            .from_("postgres:16")
            # Install build dependencies
            .with_exec(["apt-get", "update"])
            .with_exec(["apt-get", "install", "-y",
                       "build-essential", "postgresql-server-dev-16", "git", "curl"])

            # Install pgvector
            .with_exec(["git", "clone", "--branch", "v0.7.0",
                       "https://github.com/pgvector/pgvector.git", "/tmp/pgvector"])
            .with_workdir("/tmp/pgvector")
            .with_exec(["make"])
            .with_exec(["make", "install"])

            # Install ParadeDB (pg_search extension)
            .with_workdir("/tmp")
            .with_exec(["git", "clone",
                       "https://github.com/paradedb/paradedb.git", "/tmp/paradedb"])
            .with_workdir("/tmp/paradedb")
            .with_exec(["cargo", "build", "--release"])  # Requires Rust
            .with_exec(["make", "install"])

            # Configure Postgres
            .with_env_variable("POSTGRES_DB", self.config.db_name)
            .with_env_variable("POSTGRES_PASSWORD", self.config.db_password)
            .with_exposed_port(5432)
        )

    async def _wait_for_postgres(self):
        """Wait for Postgres to be ready"""
        # Implementation: Poll until connection succeeds
        pass

    @property
    def connection_string(self) -> str:
        """Get connection string for tests"""
        return f"postgresql://postgres:{self.config.db_password}@postgres:5432/{self.config.db_name}"
```

**When Used**: KnowledgeBeast integration tests

```python
# tests/integration/test_postgres_backend.py
import pytest
from knowledgebeast.backends.postgres import PostgresBackend
from tests.dagger_modules.postgres_test import PostgresTestStack, PostgresTestConfig

@pytest.mark.asyncio
async def test_postgres_backend_with_dagger():
    """Test PostgresBackend against real Postgres (pgvector + ParadeDB)"""
    config = PostgresTestConfig(embedding_dimension=384)

    async with PostgresTestStack(config) as stack:
        # Test against real Postgres
        backend = PostgresBackend(
            connection_string=stack.connection_string,
            collection_name="test",
            embedding_dimension=384
        )

        await backend.initialize()

        # Add documents
        await backend.add_documents(
            ids=["doc1"],
            embeddings=[[0.1] * 384],
            documents=["Test document"],
            metadatas=[{"category": "test"}]
        )

        # Query
        results = await backend.query_hybrid(
            query_embedding=[0.1] * 384,
            query_text="test",
            alpha=0.7,
            top_k=5
        )

        assert len(results) > 0
```

---

### Performia (Audio Processing Pipeline)

**Use Case**: Test audio analysis services in isolated containers

**Stack**: Audio processor + Song library database

```python
# performia/tests/dagger_modules/audio_test.py
class AudioTestStack:
    """Audio processing test environment"""

    async def build_audio_processor(self) -> dagger.Container:
        """Build container with JUCE, librosa, whisper"""
        return (
            self.client.container()
            .from_("python:3.12-slim")
            .with_exec(["apt-get", "update"])
            .with_exec(["apt-get", "install", "-y", "ffmpeg", "libsndfile1"])
            .with_exec(["pip", "install", "librosa", "whisper", "juce"])
            .with_mounted_directory("/audio_files", test_audio_path)
        )
```

---

### Veria (Compliance Testing)

**Use Case**: Test compliance API against production-like infrastructure

**Stack**: Postgres + Compliance engine + Policy database

```python
# veria/tests/dagger_modules/compliance_test.py
class ComplianceTestStack:
    """Compliance testing environment"""

    async def build_postgres(self) -> dagger.Container:
        """Postgres with pgvector for policy embeddings"""
        # Similar to KnowledgeBeast, but optimized for legal documents
        pass

    async def build_policy_engine(self) -> dagger.Container:
        """Compliance policy engine with NLP models"""
        pass
```

---

## Testing Matrix Pattern

**Use Case**: Test same code against multiple backends/configurations

```python
# conftest.py (pytest fixture)
import pytest
from tests.dagger_modules.postgres_test import PostgresTestStack, PostgresTestConfig

@pytest.fixture(params=["chromadb", "postgres"])
async def vector_backend(request):
    """Parametrized fixture for testing both backends"""
    if request.param == "chromadb":
        # Use ChromaDB (no Dagger needed)
        from knowledgebeast.backends.chromadb import ChromaDBBackend
        backend = ChromaDBBackend(persist_directory="/tmp/test_chromadb")
        yield backend

    elif request.param == "postgres":
        # Use Dagger to spin up real Postgres
        config = PostgresTestConfig()
        async with PostgresTestStack(config) as stack:
            from knowledgebeast.backends.postgres import PostgresBackend
            backend = PostgresBackend(
                connection_string=stack.connection_string,
                collection_name="test"
            )
            await backend.initialize()
            yield backend

# Tests automatically run against both backends!
@pytest.mark.asyncio
async def test_add_documents(vector_backend):
    """This test runs twice: once with ChromaDB, once with Postgres"""
    await vector_backend.add_documents(...)
    # ... assertions
```

---

## CI/CD Integration

### GitHub Actions with Dagger

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test-matrix:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
        backend: ['chromadb', 'postgres']

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests with Dagger
        run: |
          # Dagger handles container orchestration
          pytest tests/ -v -m ${{ matrix.backend }}
```

---

## Directory Structure

### Recommended Layout for All Projects

```
project/
├── src/
│   └── {project}/
│       ├── backends/          # Backend abstraction (if applicable)
│       │   ├── base.py        # Abstract base class
│       │   ├── chromadb.py    # ChromaDB implementation
│       │   └── postgres.py    # Postgres implementation
│       └── ...
├── tests/
│   ├── dagger_modules/        # Dagger stack definitions
│   │   ├── __init__.py
│   │   ├── postgres_test.py   # PostgresTestStack
│   │   └── ...
│   ├── integration/           # Integration tests using Dagger
│   │   └── test_postgres_backend.py
│   └── unit/                  # Unit tests (no Dagger)
│       └── test_embeddings.py
└── dagger/                     # Optional: Dagger CI/CD pipelines
    └── main.py                # Dagger Functions (if using Dagger Cloud)
```

---

## Best Practices

### 1. Separation of Concerns

- **Production code**: Backend abstraction for runtime flexibility
- **Test infrastructure**: Dagger for reproducible environments
- **CI/CD**: Dagger for build/test/deploy pipelines

### 2. Cache Optimization

```python
# Dagger automatically caches layers
# Order from least-changing to most-changing:
return (
    self.client.container()
    .from_("postgres:16")                 # Cached forever
    .with_exec(["apt-get", "update"])     # Cached per Dockerfile
    .with_exec(["apt-get", "install", ...])  # Cached if deps unchanged
    .with_exec(["git", "clone", ...])     # Cached if version unchanged
    .with_env_variable("VAR", "value")    # Cached if value unchanged
)
```

### 3. Service Dependencies

```python
# Start services in dependency order
postgres = await self.build_postgres()
postgres_svc = postgres.as_service()  # Start first

# Backend depends on postgres
backend = await self.build_backend("postgres")  # Use service hostname
backend_svc = backend.as_service()
```

### 4. Health Checks

```python
async def _wait_for_postgres(self):
    """Wait for Postgres to be ready"""
    import asyncpg
    max_retries = 30
    for i in range(max_retries):
        try:
            conn = await asyncpg.connect(self.connection_string)
            await conn.close()
            return  # Success!
        except:
            if i == max_retries - 1:
                raise
            await asyncio.sleep(1)
```

---

## When to Use Dagger

### ✅ Good Use Cases

1. **Testing against real infrastructure**
   - KnowledgeBeast: Test Postgres backend with real pgvector + ParadeDB
   - Veria: Test compliance engine with production-like setup

2. **Building custom Docker images**
   - Postgres with extensions (pgvector, ParadeDB)
   - Audio processing containers (JUCE, librosa)

3. **CI/CD pipelines**
   - Multi-backend testing matrix
   - Build/test/deploy automation
   - Reproducible builds across environments

4. **Development environments**
   - CommandCenter Hub: Start/stop project instances
   - Consistent local development setup

### ❌ When NOT to Use Dagger

1. **Simple unit tests** - Just use mocks
2. **Production runtime** - Use backend abstraction instead
3. **Trivial containers** - Docker Compose might be simpler

---

## Migration Guide (Existing Projects)

### Step 1: Identify Container Needs

- Does your project need custom Docker images? → Dagger for building
- Does your project need testing against real infrastructure? → Dagger for testing
- Does your project orchestrate multiple containers? → Dagger for orchestration

### Step 2: Create Dagger Modules

1. Create `tests/dagger_modules/` directory
2. Copy pattern from this document
3. Adapt Config dataclass to your needs
4. Implement Stack class with your containers

### Step 3: Update Tests

1. Create pytest fixtures using Dagger stacks
2. Update integration tests to use fixtures
3. Add parametrized fixtures for testing matrix

### Step 4: Update CI/CD

1. Add Dagger to CI workflow
2. Use testing matrix for multi-backend/multi-version testing
3. Leverage Dagger caching for faster CI

---

## Summary

**Dagger Pattern = Config + Stack + Container Builders**

- ✅ Reproducible across all projects (CommandCenter, KnowledgeBeast, Performia, Veria)
- ✅ Type-safe infrastructure as code
- ✅ Automatic caching and optimization
- ✅ Perfect for testing, CI/CD, and development environments
- ✅ Complements (not replaces) backend abstraction layers

**Next Steps:**
1. Apply this pattern to KnowledgeBeast (Postgres testing)
2. Document as reusable skill
3. Use across all projects going forward
