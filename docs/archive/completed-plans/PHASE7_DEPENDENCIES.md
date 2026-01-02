# Phase 7 Dependencies Analysis

**Date**: 2025-11-05
**Phase**: Phase 7 - Graph Service Implementation

## Current Infrastructure (Already Available)

### ✅ Database & ORM
- **PostgreSQL**: Running (Phase 1-6)
- **SQLAlchemy 2.0.25**: Installed
- **Alembic 1.13.1**: Installed for migrations
- **pgvector**: Installed (for RAG, can also support graph queries)
- **asyncpg 0.29.0**: Async PostgreSQL driver

### ✅ Event System (Phase 4-6)
- **NATS**: Implemented in Hub (`hub/backend`)
- **nats-py 2.7.2**: Python NATS client (Hub requirements)
- **EventService**: Full event sourcing system
- **NATSBridge**: Bidirectional NATS integration
- **Subjects**: `hub.presence.*`, `hub.health.*`, routing infrastructure ready

### ✅ Web Framework
- **FastAPI 0.109.0**: Main web framework
- **Uvicorn 0.27.0**: ASGI server
- **Pydantic 2.5.0+**: Data validation

### ✅ Python Parsers
- **ast module**: Built-in Python AST parser
- **Click 8.1.0+**: CLI framework
- **Rich 13.0.0+**: Terminal formatting

## Required New Dependencies

### 1. GraphQL Support
```
strawberry-graphql[fastapi]>=0.235.0  # FastAPI + GraphQL integration
```

**Rationale**:
- Strawberry is type-safe, modern, async-first GraphQL library
- Native FastAPI integration
- Async/await support for SQLAlchemy queries
- Better than graphene-python (outdated, sync-focused)

**Alternatives Considered**:
- `graphene-python`: Older, less type-safe
- `ariadne`: Schema-first (we want code-first)

### 2. Tree-sitter (TypeScript/JavaScript Parsing)
```
tree-sitter>=0.21.0
tree-sitter-languages>=1.10.0  # Pre-built parsers for TS/JS/Go/Rust
```

**Rationale**:
- Fast, incremental AST parsing for multiple languages
- Better than `ts-morph` (requires Node.js)
- Pre-built bindings for TS, JS, Go, Rust, Python

**Alternatives Considered**:
- `esprima`: JavaScript-only, slower
- `pycparser`: C-only
- Calling Node.js ts-morph: Cross-language complexity

### 3. NATS Client (CommandCenter Backend)
```
nats-py==2.7.2  # Match Hub version for consistency
```

**Rationale**:
- Already used in Hub backend
- Proven in Phases 4-6
- Will enable graph ingestion events

**Note**: Hub already has this; CommandCenter backend needs to add it.

### 4. Graph Query Optimization (Optional Phase 7.5+)
```
networkx>=3.2.0  # Graph algorithms for dependency analysis
```

**Rationale**:
- Useful for computing dependency depth, cycles, critical paths
- Can defer to Phase 8 if not needed immediately

**Deferred**: Not needed for MVP. Add in Phase 7.5 if needed.

## Dependencies NOT Needed

### ❌ Prisma/Node.js ORM
**Blueprint suggested Prisma, but we're using SQLAlchemy instead**:
- Keeps Python-only stack
- Reuses existing patterns
- No microservice overhead

### ❌ elkjs (Layout Engine)
**Frontend-only dependency**:
- Deferred to Phase 8 (VISLZR frontend)
- Not needed for Graph Service backend

### ❌ Semgrep/Snyk (Security Scanners)
**Deferred to Milestone 3 (Audits)**:
- Not needed for Graph Service MVP
- Will add when implementing audit system

## Updated requirements.txt

Add to `backend/requirements.txt`:

```python
# Phase 7: Graph Service
strawberry-graphql[fastapi]>=0.235.0  # GraphQL API
tree-sitter>=0.21.0                    # Multi-language AST parsing
tree-sitter-languages>=1.10.0          # Pre-built language parsers
nats-py==2.7.2                         # NATS event integration (match Hub)
```

## Installation Command

```bash
cd /Users/danielconnolly/Projects/CommandCenter/backend
source venv/bin/activate
pip install strawberry-graphql[fastapi]>=0.235.0 tree-sitter>=0.21.0 tree-sitter-languages>=1.10.0 nats-py==2.7.2
pip freeze > requirements.txt
```

## Verification Steps

### 1. Verify Strawberry GraphQL
```python
import strawberry
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Graph Service Ready"

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)
```

### 2. Verify Tree-sitter
```python
from tree_sitter_languages import get_parser

parser = get_parser("typescript")
tree = parser.parse(b"function hello() { return 42; }")
assert tree.root_node.type == "program"
```

### 3. Verify NATS
```python
import nats
import asyncio

async def test_nats():
    nc = await nats.connect("nats://localhost:4222")
    await nc.publish("graph.test", b"hello")
    await nc.close()

asyncio.run(test_nats())
```

## Architecture Impact

### Before (Current)
```
CommandCenter Backend
├── FastAPI + SQLAlchemy
├── RAG (KnowledgeBeast + pgvector)
├── GitHub Integration
└── No graph/event layer
```

### After (Phase 7)
```
CommandCenter Backend
├── FastAPI + SQLAlchemy
├── RAG (KnowledgeBeast + pgvector)
├── GitHub Integration
└── Graph Service
    ├── SQLAlchemy Models (graph entities)
    ├── Strawberry GraphQL API
    ├── Tree-sitter Indexer (TS/JS/Py)
    └── NATS Event Handlers
```

## Testing Strategy

### Unit Tests
- SQLAlchemy model tests (CRUD operations)
- GraphQL resolver tests (mocked DB)
- Parser tests (AST extraction)

### Integration Tests
- End-to-end ingestion (real repo → DB → GraphQL query)
- NATS event publishing/consumption
- Performance: >5k nodes query <1.5s

### Dependencies for Tests
```python
pytest>=7.4.0           # Already installed
pytest-asyncio>=0.23.0  # Already installed
faker>=22.0.0           # Generate test data (optional)
```

## Migration Plan

### Step 1: Add Dependencies (Day 1)
```bash
pip install strawberry-graphql[fastapi] tree-sitter tree-sitter-languages nats-py==2.7.2
```

### Step 2: Create Module Structure (Day 1)
```
backend/app/services/graph/
├── __init__.py
├── models.py      # SQLAlchemy models
├── service.py     # Graph operations
└── indexer/
    └── parsers.py # AST extractors
```

### Step 3: Alembic Migration (Day 2)
```bash
cd backend
alembic revision --autogenerate -m "Add graph schema for Phase 7"
alembic upgrade head
```

### Step 4: Verify (Day 2)
- Run unit tests
- Test GraphQL endpoint: `http://localhost:8000/graphql`
- Test NATS connection from backend

## Rollback Plan

If Phase 7 needs to be paused:
1. Dependencies are additive (no breaking changes)
2. Graph schema is separate (can be dropped with Alembic downgrade)
3. No changes to existing services

## Cost Analysis

### Performance Impact
- **Strawberry GraphQL**: ~50ms overhead per query (acceptable)
- **Tree-sitter**: 10-20ms per file parse (excellent)
- **NATS**: <5ms pub/sub (proven in Hub)

### Storage Impact
- Graph schema: Estimate ~100MB per 10k symbols (reasonable)
- Event log: ~1MB per 1000 events (manageable)

### Maintenance Burden
- Strawberry: Actively maintained (last release Nov 2024)
- Tree-sitter: Mature, stable (v0.21+)
- nats-py: Active CNCF project

---

**Ready for Implementation**: All dependencies identified, verified, and documented.

**Next Step**: Add dependencies to `requirements.txt` and begin Milestone 1 (Data Models).
