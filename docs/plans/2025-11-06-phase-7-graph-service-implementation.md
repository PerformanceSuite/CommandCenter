# Phase 7: Graph Service Implementation Design

**Date**: 2025-11-06
**Status**: Design Approved
**Milestone**: Phase 7 Milestone 1 - Graph Service MVP
**Architecture**: Service-First (Layered)
**Tech Stack**: Python/FastAPI/SQLAlchemy (consistent with existing backend)

---

## Executive Summary

Phase 7 implements a code knowledge graph that indexes repository structures, tracks dependencies, and enables graph-based queries across projects. This design follows a **Service-First (Layered)** approach, building from GraphService business logic up through REST APIs, code indexing, NATS integration, and audit triggers.

**Key Design Decisions:**
- Python throughout (service, API, CLI) - no TypeScript/Prisma switch
- Multi-tenant via `project_id` filtering on all entities
- Light integration with existing models (no deep foreign keys initially)
- Leverage existing NATS infrastructure from Phases 1-4
- Stub audit agents for Milestone 1, real tools in Milestone 3

**Deliverables:**
1. GraphService with query/mutation methods
2. REST API endpoints for graph access
3. Python CLI indexer for code ingestion
4. NATS event integration
5. Basic audit trigger system

---

## Architecture Overview

### Layer Stack (Service-First Approach)

```
┌─────────────────────────────────────────────────────────┐
│ Layer 5: Audit System                                   │
│  - Trigger audits via NATS (security, code review)     │
│  - Store results in GraphAudit table                    │
│  - Files: backend/scripts/audit_agents.py              │
└─────────────────────────────────────────────────────────┘
                        ↓ depends on
┌─────────────────────────────────────────────────────────┐
│ Layer 4: NATS Integration                               │
│  - graph.ingest.* subjects                             │
│  - audit.requested.* / audit.result.*                  │
│  - Event mirroring to GraphEvent table                 │
│  - Leverage existing NATSBridge from Phase 4           │
└─────────────────────────────────────────────────────────┘
                        ↓ depends on
┌─────────────────────────────────────────────────────────┐
│ Layer 3: Code Indexer CLI                              │
│  - Python CLI tool (backend/scripts/graph_indexer.py)  │
│  - AST parsing (Python, TypeScript/JavaScript)         │
│  - Populates GraphRepo, GraphFile, GraphSymbol         │
│  - Batch inserts, incremental updates                  │
└─────────────────────────────────────────────────────────┘
                        ↓ depends on
┌─────────────────────────────────────────────────────────┐
│ Layer 2: REST API Endpoints                             │
│  - /api/v1/graph/projects/{id} (projectGraph)         │
│  - /api/v1/graph/dependencies/{symbol_id}             │
│  - /api/v1/graph/ghost-nodes/{project_id}             │
│  - /api/v1/graph/search                                │
│  - Files: backend/app/routers/graph.py                │
└─────────────────────────────────────────────────────────┘
                        ↓ depends on
┌─────────────────────────────────────────────────────────┐
│ Layer 1: GraphService (Business Logic)                 │
│  - Query methods (get_project_graph, get_dependencies) │
│  - Mutation methods (create_task, trigger_audit)       │
│  - SQLAlchemy queries on graph models                  │
│  - Files: backend/app/services/graph_service.py       │
└─────────────────────────────────────────────────────────┘
                        ↓ uses
┌─────────────────────────────────────────────────────────┐
│ Foundation: Graph Models (SQLAlchemy) ✅ DONE           │
│  - GraphRepo, GraphFile, GraphSymbol, GraphDependency  │
│  - GraphService, GraphHealthSample                     │
│  - GraphSpecItem, GraphTask, GraphLink, GraphAudit     │
│  - Files: backend/app/models/graph.py (675 lines)     │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 1: GraphService (Business Logic)

**File**: `backend/app/services/graph_service.py`

**Responsibilities:**
- Encapsulate all graph database queries
- Enforce multi-tenant filtering (project_id)
- Provide clean API for routers and CLI tools
- Handle complex graph traversals

### Key Methods

#### Query Operations

```python
class GraphService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_project_graph(
        self,
        project_id: int,
        depth: int = 2,
        filters: Optional[GraphFilters] = None
    ) -> ProjectGraphResponse:
        """
        Return nodes (repos, files, symbols, services, tasks) + edges

        Args:
            project_id: Project for multi-tenant isolation
            depth: How many levels of relationships to traverse
            filters: Optional filters (languages, file paths, symbol kinds)

        Returns:
            ProjectGraphResponse with nodes and edges lists
        """

    async def get_dependencies(
        self,
        symbol_id: int,
        direction: Literal["inbound", "outbound", "both"],
        depth: int = 3
    ) -> DependencyGraph:
        """
        Traverse symbol dependencies recursively

        Args:
            symbol_id: Starting symbol
            direction: Which dependencies to follow
            depth: Maximum traversal depth

        Returns:
            DependencyGraph with symbols and dependency edges
        """

    async def get_ghost_nodes(
        self,
        project_id: int,
        filters: Optional[SpecFilters] = None
    ) -> List[GhostNode]:
        """
        Find SpecItems/Tasks without backing Files/Symbols

        Ghost nodes represent planned work that hasn't been implemented yet.
        Extracted from TODO/FIXME comments or manual spec creation.

        Args:
            project_id: Project scope
            filters: Optional status/source filters

        Returns:
            List of GhostNode (SpecItem/Task without implementation)
        """

    async def search_graph(
        self,
        project_id: int,
        query: str,
        scope: List[str] = ["symbols", "files", "tasks"]
    ) -> SearchResults:
        """
        Unified search across code + specs + tasks

        Uses PostgreSQL full-text search on:
        - Symbol names and signatures
        - File paths
        - Task/SpecItem titles and descriptions

        Args:
            project_id: Project scope
            query: Search string
            scope: Which entity types to search

        Returns:
            SearchResults grouped by entity type
        """
```

#### Mutation Operations

```python
    async def create_task(
        self,
        project_id: int,
        title: str,
        kind: TaskKind,
        spec_item_id: Optional[int] = None,
        description: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> GraphTask:
        """
        Create work item, optionally linked to spec

        Args:
            project_id: Project scope
            title: Task title
            kind: TaskKind enum (feature, bug, chore, review, security, etc)
            spec_item_id: Optional link to SpecItem
            description: Optional detailed description
            labels: Optional tags for categorization

        Returns:
            Created GraphTask entity
        """

    async def trigger_audit(
        self,
        target_entity: str,
        target_id: int,
        kind: AuditKind
    ) -> GraphAudit:
        """
        Create audit record + emit NATS event

        Creates pending audit, publishes to NATS for agent pickup.
        Audit agents subscribe to audit.requested.{kind} and respond
        via audit.result.{kind} events.

        Args:
            target_entity: Table name (graph_files, graph_symbols, etc)
            target_id: Entity ID to audit
            kind: AuditKind enum (codeReview, security, license, etc)

        Returns:
            Created GraphAudit entity (status=PENDING)
        """

    async def link_entities(
        self,
        from_entity: str,
        from_id: int,
        to_entity: str,
        to_id: int,
        link_type: LinkType,
        weight: float = 1.0
    ) -> GraphLink:
        """
        Create typed relationship between any two entities

        Generic linking system for flexible relationships:
        - File → SpecItem (file implements spec)
        - Service → Repo (service deployed from repo)
        - Task → Symbol (task modifies symbol)
        - Audit → File (audit targets file)

        Args:
            from_entity: Source table name
            from_id: Source entity ID
            to_entity: Target table name
            to_id: Target entity ID
            link_type: LinkType enum (references, dependsOn, implements, etc)
            weight: Link strength/importance (default 1.0)

        Returns:
            Created GraphLink entity
        """
```

#### Helper Methods

```python
    async def get_graph_stats(self, project_id: int) -> GraphStats:
        """Get counts of all entity types for a project"""

    async def update_audit_result(
        self,
        audit_id: int,
        status: AuditStatus,
        summary: str,
        report_path: Optional[str] = None,
        score: Optional[float] = None
    ) -> GraphAudit:
        """Update audit with results from agent"""
```

### Design Patterns

- **Async/await throughout**: Matches existing FastAPI service patterns
- **Dependency injection**: Session passed to constructor via FastAPI
- **Pydantic schemas**: Request/response validation (GraphFilters, ProjectGraphResponse, etc)
- **SQLAlchemy Core for complex queries**: Better performance than ORM for graph traversal
- **Multi-tenant enforcement**: All queries include `WHERE project_id = ?`

---

## Layer 2: REST API Endpoints

**File**: `backend/app/routers/graph.py`

### Endpoint Design

#### Query Endpoints (GET)

```python
GET  /api/v1/graph/projects/{project_id}
     ?depth=2&include=repos,files,symbols,services,tasks

     Returns: ProjectGraphResponse
     {
       "nodes": [
         {"id": 1, "type": "repo", "name": "CommandCenter", ...},
         {"id": 2, "type": "file", "path": "app/main.py", ...},
         {"id": 3, "type": "symbol", "name": "main", "kind": "function", ...}
       ],
       "edges": [
         {"from": 2, "to": 3, "type": "contains"},
         {"from": 3, "to": 5, "type": "calls"}
       ]
     }

GET  /api/v1/graph/symbols/{symbol_id}/dependencies
     ?direction=both&depth=3

     Returns: DependencyGraph
     {
       "root": {"id": 123, "name": "AuthService", ...},
       "dependencies": [
         {"symbol": {...}, "type": "imports", "depth": 1},
         {"symbol": {...}, "type": "calls", "depth": 2}
       ]
     }

GET  /api/v1/graph/projects/{project_id}/ghost-nodes
     ?status=planned&source=file

     Returns: List[GhostNode]
     [
       {
         "spec_item_id": 45,
         "title": "TODO: Add rate limiting",
         "source": "file",
         "ref": "app/api/routes.py:42",
         "status": "planned"
       }
     ]

GET  /api/v1/graph/projects/{project_id}/search
     ?q=AuthService&scope=symbols,files&limit=20

     Returns: SearchResults
     {
       "symbols": [...],
       "files": [...],
       "tasks": [],
       "total": 15
     }

GET  /api/v1/graph/projects/{project_id}/stats

     Returns: GraphStats
     {
       "repo_count": 3,
       "file_count": 1247,
       "symbol_count": 5832,
       "task_count": 12,
       "audit_count": 8
     }
```

#### Mutation Endpoints (POST)

```python
POST /api/v1/graph/projects/{project_id}/tasks

     Body: {
       "title": "Refactor auth middleware",
       "kind": "refactor",
       "spec_item_id": 45,
       "description": "Extract to separate module",
       "labels": ["backend", "high-priority"]
     }

     Returns: GraphTask

POST /api/v1/graph/audits/trigger

     Body: {
       "target_entity": "graph_files",
       "target_id": 123,
       "kind": "security"
     }

     Returns: GraphAudit (status=pending)

POST /api/v1/graph/links

     Body: {
       "from_entity": "graph_tasks",
       "from_id": 5,
       "to_entity": "graph_symbols",
       "to_id": 234,
       "type": "implements"
     }

     Returns: GraphLink

GET  /api/v1/graph/audits/{audit_id}/report

     Returns: File download or JSON report
```

### Authentication & Authorization

- **Reuse existing auth**: FastAPI dependency injection patterns
- **Project access verification**: Check user permissions for `project_id`
- **Multi-tenant isolation**: Service layer enforces project_id filtering
- **Rate limiting**: Leverage existing RateLimitService

### Response Format

- **Consistent Pydantic schemas**: GraphNode, GraphEdge base types
- **Pagination**: `limit` and `offset` query params for large results
- **Error handling**: Standard FastAPI HTTPException patterns
- **GraphQL**: Deferred to Phase 8 (VISLZR integration)

---

## Layer 3: Code Indexer CLI

**File**: `backend/scripts/graph_indexer.py`

### CLI Interface (Click)

```bash
# Index entire repository
python -m scripts.graph_indexer index \
  --project-id 1 \
  --repo-path /path/to/repo \
  --repo-url github.com/owner/name

# Incremental index (only changed files)
python -m scripts.graph_indexer index \
  --project-id 1 \
  --repo-path /path/to/repo \
  --since last  # or --since <commit-hash>

# Index specific languages
python -m scripts.graph_indexer index \
  --project-id 1 \
  --repo-path /path/to/repo \
  --languages python,typescript

# Extract TODOs/FIXMEs to SpecItems
python -m scripts.graph_indexer extract-specs \
  --project-id 1 \
  --repo-path /path/to/repo

# Full statistics report
python -m scripts.graph_indexer stats \
  --project-id 1
```

### Indexing Pipeline

**1. Scan Phase:**
- Walk directory tree using `os.walk()`
- Filter by language extensions (`.py`, `.ts`, `.js`, `.tsx`, `.jsx`)
- Exclude patterns: `node_modules/`, `.git/`, `__pycache__/`, `venv/`
- Collect file paths with metadata (size, mtime)

**2. Hash Phase:**
- Compute SHA-256 hash of file contents
- Compare with existing GraphFile.hash
- Skip unchanged files (incremental optimization)
- Build "files to process" list

**3. Parse Phase (per language):**

**Python (using `ast` module):**
```python
import ast

tree = ast.parse(file_contents)
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef):
        # Extract class: name, line range, methods
    elif isinstance(node, ast.FunctionDef):
        # Extract function: name, signature, decorators, line range
    elif isinstance(node, ast.Import):
        # Extract import dependencies
```

**TypeScript/JavaScript (using `tree-sitter`):**
```python
from tree_sitter import Language, Parser

parser = Parser()
parser.set_language(Language('build/languages.so', 'javascript'))
tree = parser.parse(file_contents.encode())

# Query for classes, functions, imports
query = language.query("""
  (class_declaration name: (identifier) @class.name)
  (function_declaration name: (identifier) @function.name)
  (import_statement source: (string) @import.source)
""")
```

**4. Extract Phase:**
- Build GraphFile entity (path, lang, hash, size, lines)
- Build GraphSymbol entities (kind, name, qualified_name, range, signature)
- Build GraphDependency entities (from_symbol, to_symbol, type)
- Extract TODO/FIXME comments → GraphSpecItem entities

**5. Upsert Phase:**
- Batch database operations (100 files at a time)
- Use `INSERT ... ON CONFLICT UPDATE` for idempotency
- Transaction per batch for rollback safety
- Progress tracking (tqdm progress bar)

**6. Emit Phase:**
- Publish `graph.ingest.completed` to NATS
- Include stats: files_processed, symbols_extracted, errors
- Update GraphRepo.last_indexed_at timestamp

### Language Support

**Milestone 1:**
- ✅ Python (`ast` module - native, no dependencies)
- ✅ TypeScript/JavaScript (`tree-sitter-javascript`)

**Milestone 2+:**
- 📋 Go (`tree-sitter-go`)
- 📋 Rust (`tree-sitter-rust`)
- 📋 SQL (schema extraction)
- 📋 YAML/JSON (config files)

### Performance Targets

- **Throughput**: ~1000 files/minute (parallel processing)
- **Batch size**: 100 files per database transaction
- **Memory**: Stream large files (don't load all in RAM)
- **Progress**: Real-time tqdm progress bar
- **Incremental**: Only reprocess changed files (hash comparison)

### Error Handling

- **Parse errors**: Log and continue (don't fail entire index)
- **File access errors**: Skip inaccessible files
- **Database errors**: Rollback batch, retry once
- **Final report**: Summary of successes, failures, warnings

---

## Layer 4: NATS Integration

### Leverage Existing Infrastructure

**What we already have (Phases 1-4):**
- ✅ NATS 2.10 server running (localhost:4222)
- ✅ EventService with publish/subscribe/replay
- ✅ NATSBridge for internal ↔ external event routing
- ✅ Health monitoring and correlation IDs

**What we add for Phase 7:**
- New NATS subjects for graph operations
- Event consumers in GraphService
- Event publishers in indexer and API

### New NATS Subjects

```python
# Ingestion Events
"graph.ingest.requested"   # CLI trigger: start indexing job
"graph.ingest.started"     # Indexer begins processing
"graph.ingest.progress"    # Progress updates (every 100 files)
"graph.ingest.completed"   # Indexer finishes (includes stats)

# Audit Events
"audit.requested.codeReview"  # Trigger code review audit
"audit.requested.security"    # Trigger security scan
"audit.requested.license"     # Trigger license check
"audit.result.codeReview"     # Audit agent completion
"audit.result.security"       # Security scan results
"audit.result.license"        # License check results

# Graph Updates (for real-time UI)
"graph.updated.{project_id}"  # Any graph data change
"graph.symbol.added"          # New symbol indexed
"graph.task.created"          # New task created
```

### Event Schemas (Pydantic)

```python
class GraphIngestCompletedEvent(BaseModel):
    project_id: int
    repo_id: int
    files_processed: int
    symbols_extracted: int
    dependencies_found: int
    errors: int
    duration_seconds: float
    timestamp: datetime

class AuditRequestedEvent(BaseModel):
    audit_id: int
    target_entity: str
    target_id: int
    kind: AuditKind
    requested_by: str
    timestamp: datetime

class AuditResultEvent(BaseModel):
    audit_id: int
    status: AuditStatus
    summary: str
    report_path: Optional[str]
    score: Optional[float]
    metadata: dict
    timestamp: datetime
```

### Event Consumers

**In GraphService:**
```python
class GraphService:
    async def start_audit_result_consumer(self):
        """Subscribe to audit.result.* subjects"""
        async def handle_audit_result(msg):
            event = AuditResultEvent.parse_raw(msg.data)
            await self.update_audit_result(
                audit_id=event.audit_id,
                status=event.status,
                summary=event.summary,
                report_path=event.report_path,
                score=event.score
            )

        await nats_client.subscribe(
            subject="audit.result.*",
            cb=handle_audit_result
        )
```

### Integration Pattern

```python
# Example: GraphService.trigger_audit()
async def trigger_audit(self, target_entity, target_id, kind):
    # 1. Create pending audit record
    audit = GraphAudit(
        target_entity=target_entity,
        target_id=target_id,
        kind=kind,
        status=AuditStatus.PENDING,
        created_at=datetime.utcnow()
    )
    self.db.add(audit)
    await self.db.commit()

    # 2. Publish NATS event for audit agents
    event = AuditRequestedEvent(
        audit_id=audit.id,
        target_entity=target_entity,
        target_id=target_id,
        kind=kind,
        requested_by="api",  # or user ID
        timestamp=datetime.utcnow()
    )

    await nats_client.publish(
        subject=f"audit.requested.{kind.value}",
        data=event.json().encode()
    )

    return audit
```

### Event Mirroring to GraphEvent

**Optional**: Store important events in database for queryable history

```python
async def mirror_event_to_db(subject: str, payload: dict):
    """Store NATS event in GraphEvent table for analytics"""
    event = GraphEvent(
        subject=subject,
        payload=payload,
        created_at=datetime.utcnow()
    )
    db.add(event)
    await db.commit()
```

---

## Layer 5: Basic Audit System

### Audit Flow

```
User/VISLZR → API: POST /audits/trigger
              ↓
         GraphService.trigger_audit()
              ↓
    1. Create GraphAudit (status=PENDING)
    2. Emit NATS: audit.requested.{kind}
              ↓
         NATS Message Bus
              ↓
    Audit Agent Subscriber (separate process)
              ↓
    3. Process audit (stub for Milestone 1)
    4. Emit NATS: audit.result.{kind}
              ↓
         GraphService Consumer
              ↓
    5. Update GraphAudit (status=OK/WARN/FAIL)
    6. Store report_path (if artifact generated)
```

### Audit Agents (Milestone 1 - Stubs)

**File**: `backend/scripts/audit_agents.py`

```python
import asyncio
from typing import Dict
from nats.aio.client import Client as NATS

class AuditAgentStubs:
    """Stub audit agents for Milestone 1 - just acknowledge requests"""

    def __init__(self, nats_client: NATS):
        self.nats = nats_client

    async def start(self):
        """Start all stub agents"""
        await self.nats.subscribe("audit.requested.codeReview",
                                  cb=self.handle_code_review)
        await self.nats.subscribe("audit.requested.security",
                                  cb=self.handle_security)
        print("Audit agent stubs started")

    async def handle_code_review(self, msg):
        """Stub code review audit"""
        event = json.loads(msg.data)
        audit_id = event["audit_id"]

        # Simulate processing
        await asyncio.sleep(2)

        # Publish result
        result = {
            "audit_id": audit_id,
            "status": "ok",
            "summary": f"Code review stub: {event['target_entity']}:{event['target_id']} passes basic checks",
            "score": 85.0,
            "metadata": {
                "stub": True,
                "checks_run": ["naming", "complexity", "docs"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.nats.publish(
            "audit.result.codeReview",
            json.dumps(result).encode()
        )

    async def handle_security(self, msg):
        """Stub security audit"""
        event = json.loads(msg.data)
        audit_id = event["audit_id"]

        await asyncio.sleep(2)

        # Simulate finding a warning
        result = {
            "audit_id": audit_id,
            "status": "warn",
            "summary": "Security stub: 1 medium severity issue found",
            "score": 75.0,
            "metadata": {
                "stub": True,
                "findings": [
                    {
                        "severity": "medium",
                        "rule": "stub-sql-injection",
                        "message": "Potential SQL injection (stub finding)"
                    }
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.nats.publish(
            "audit.result.security",
            json.dumps(result).encode()
        )

# Run as separate process
if __name__ == "__main__":
    async def main():
        nats = NATS()
        await nats.connect("nats://localhost:4222")

        agents = AuditAgentStubs(nats)
        await agents.start()

        # Keep running
        while True:
            await asyncio.sleep(1)

    asyncio.run(main())
```

### Artifact Storage

**Path format**: `snapshots/audits/{project_id}/{audit_id}/report.json`

**Storage logic**:
```python
async def store_audit_report(audit_id: int, project_id: int, report: dict):
    """Store audit report artifact"""
    report_dir = f"snapshots/audits/{project_id}/{audit_id}"
    os.makedirs(report_dir, exist_ok=True)

    report_path = f"{report_dir}/report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Update audit record
    audit = await db.get(GraphAudit, audit_id)
    audit.report_path = report_path
    await db.commit()

    return report_path
```

**API endpoint for retrieval**:
```python
@router.get("/audits/{audit_id}/report")
async def get_audit_report(audit_id: int):
    """Download audit report artifact"""
    audit = await db.get(GraphAudit, audit_id)
    if not audit or not audit.report_path:
        raise HTTPException(404, "Report not found")

    return FileResponse(audit.report_path)
```

### Milestone 3 Upgrade Path

**Replace stubs with real tools:**

**Code Review Agent:**
- LLM-based review (Claude, GPT-4)
- Static analysis (pylint, mypy, eslint)
- Code complexity metrics (radon, sonarqube)
- Documentation coverage

**Security Agent:**
- SAST tools: `bandit` (Python), `semgrep` (multi-language)
- Dependency scanning: `safety`, `snyk`
- Secret detection: `trufflehog`, `git-secrets`
- OWASP Top 10 checks

**License Agent:**
- Dependency license scanning
- License compatibility checks
- SPDX identifier validation

**All agents:**
- Proper severity scoring
- Actionable recommendations
- HTML + JSON reports
- Integration with issue trackers

---

## Integration with Existing Models

### Multi-Tenant Architecture

**Existing Pattern** (already in place):
- All models have `project_id` foreign key
- All queries filtered by project_id
- Complete data isolation between projects

**Graph Models** (already implemented):
- GraphRepo, GraphService, GraphSpecItem, GraphTask all have `project_id`
- Consistent with existing architecture ✅

### Light Integration Strategy

**Phase 7 Milestone 1** (Now):
- Graph models are **standalone tables**
- Store `repository_id` reference in `GraphRepo.metadata` JSON:
  ```json
  {
    "repository_id": 5,  // Link to existing Repository model
    "last_sync_commit": "abc123"
  }
  ```
- No foreign key constraints (avoid refactoring existing models)

**Phase 7 Milestone 2+** (Later):
- Add GraphLink entries: `Repository → GraphRepo`
- Link `ResearchTask → GraphSymbol` (tasks point to code)
- Enhance RAG with graph relationships

### Why Light Integration?

**Benefits:**
1. ✅ **Fast delivery**: No refactoring existing stable systems
2. ✅ **Low risk**: Graph models don't affect Repository/ResearchTask
3. ✅ **Prove value first**: Let graph system validate before deep integration
4. ✅ **Clear upgrade path**: GraphLink table designed for this evolution

**Avoid Anti-pattern:**
- Don't merge Repository and GraphRepo into one model
- They serve different purposes:
  - `Repository`: GitHub sync, webhooks, access tokens
  - `GraphRepo`: Code structure, symbols, dependencies

---

## Testing Strategy

### Unit Tests

**GraphService Tests** (`tests/services/test_graph_service.py`):
```python
@pytest.mark.asyncio
async def test_get_project_graph(db_session):
    service = GraphService(db_session)

    # Setup: Create test graph data
    repo = GraphRepo(project_id=1, full_name="test/repo")
    file = GraphFile(repo=repo, path="main.py", lang="python")
    symbol = GraphSymbol(file=file, kind=SymbolKind.FUNCTION, name="main")

    db_session.add_all([repo, file, symbol])
    await db_session.commit()

    # Test
    graph = await service.get_project_graph(project_id=1, depth=2)

    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2
    assert graph.nodes[0]["type"] == "repo"

@pytest.mark.asyncio
async def test_trigger_audit(db_session, mock_nats):
    service = GraphService(db_session)

    audit = await service.trigger_audit(
        target_entity="graph_files",
        target_id=123,
        kind=AuditKind.SECURITY
    )

    assert audit.status == AuditStatus.PENDING
    assert mock_nats.published_subjects == ["audit.requested.security"]
```

**API Tests** (`tests/routers/test_graph.py`):
```python
def test_get_project_graph(client, test_project):
    response = client.get(f"/api/v1/graph/projects/{test_project.id}")

    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data

def test_trigger_audit_endpoint(client, test_file):
    response = client.post("/api/v1/graph/audits/trigger", json={
        "target_entity": "graph_files",
        "target_id": test_file.id,
        "kind": "security"
    })

    assert response.status_code == 201
    audit = response.json()
    assert audit["status"] == "pending"
```

**Indexer Tests** (`tests/scripts/test_graph_indexer.py`):
```python
def test_parse_python_file():
    code = """
    class MyClass:
        def method(self):
            pass

    def my_function():
        return 42
    """

    parser = PythonParser()
    symbols = parser.parse(code, "test.py")

    assert len(symbols) == 3  # class, method, function
    assert symbols[0].kind == SymbolKind.CLASS
    assert symbols[0].name == "MyClass"

def test_incremental_indexing(tmpdir):
    # Create test repo
    repo_path = tmpdir / "test_repo"
    repo_path.mkdir()
    (repo_path / "file1.py").write_text("def foo(): pass")

    # First index
    indexer = GraphIndexer(project_id=1, repo_path=str(repo_path))
    stats1 = indexer.index()
    assert stats1["files_processed"] == 1

    # Second index (no changes)
    stats2 = indexer.index()
    assert stats2["files_processed"] == 0  # Skipped via hash

    # Modify file
    (repo_path / "file1.py").write_text("def bar(): pass")
    stats3 = indexer.index()
    assert stats3["files_processed"] == 1  # Re-indexed
```

### Integration Tests

**Full Pipeline Test**:
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_graph_pipeline(db_session, nats_client, tmpdir):
    """Test: Index repo → Query graph → Trigger audit → Get results"""

    # 1. Create test repo
    repo_path = create_test_repo(tmpdir, files=[
        ("src/main.py", "def main(): pass"),
        ("src/utils.py", "def helper(): pass"),
    ])

    # 2. Index repository
    indexer = GraphIndexer(
        project_id=1,
        repo_path=str(repo_path),
        db=db_session
    )
    stats = await indexer.index()

    assert stats["files_processed"] == 2
    assert stats["symbols_extracted"] == 2

    # 3. Query graph via API
    service = GraphService(db_session)
    graph = await service.get_project_graph(project_id=1)

    assert len(graph.nodes) >= 4  # repo + 2 files + 2 symbols

    # 4. Trigger audit
    file = await db_session.execute(
        select(GraphFile).filter_by(path="src/main.py")
    )
    file = file.scalar_one()

    audit = await service.trigger_audit(
        target_entity="graph_files",
        target_id=file.id,
        kind=AuditKind.SECURITY
    )

    # 5. Wait for audit result (stub agent)
    await asyncio.sleep(3)
    await db_session.refresh(audit)

    assert audit.status in [AuditStatus.OK, AuditStatus.WARN]
    assert audit.summary is not None
```

### Acceptance Criteria (Milestone 1)

**Must Pass:**

1. ✅ **Performance**: Index CommandCenter backend (1000+ Python files) in < 2 minutes
   ```bash
   time python -m scripts.graph_indexer index \
     --project-id 1 \
     --repo-path /path/to/CommandCenter/backend
   # Should complete in < 120 seconds
   ```

2. ✅ **Query Speed**: `projectGraph` returns >5000 nodes + edges in < 1.5 seconds
   ```bash
   curl -w "@curl-format.txt" \
     http://localhost:8000/api/v1/graph/projects/1?depth=2
   # time_total should be < 1.5s
   ```

3. ✅ **Ghost Nodes**: TODO/FIXME comments extracted as SpecItems
   ```python
   # After indexing repo with TODOs
   ghost_nodes = await service.get_ghost_nodes(project_id=1)
   assert len(ghost_nodes) > 0
   assert any("TODO" in node.title for node in ghost_nodes)
   ```

4. ✅ **Audit Flow**: Trigger audit → NATS event → stub responds in < 3 seconds
   ```python
   start = time.time()
   audit = await service.trigger_audit(...)
   await wait_for_audit_completion(audit.id, timeout=3)
   elapsed = time.time() - start
   assert elapsed < 3.0
   ```

5. ✅ **Multi-tenant Isolation**: Projects can't access each other's graph data
   ```python
   # Create data for project 1
   await service.get_project_graph(project_id=1)  # Returns data

   # Try to access from project 2
   graph = await service.get_project_graph(project_id=2)
   assert len(graph.nodes) == 0  # No cross-project access
   ```

---

## Implementation Sequence (Layered)

### Week 1: Foundation & Service Layer
1. Create `backend/app/services/graph_service.py`
2. Implement query methods (get_project_graph, get_dependencies, etc)
3. Implement mutation methods (create_task, trigger_audit, link_entities)
4. Write unit tests for GraphService
5. Create Pydantic schemas for requests/responses

### Week 2: API Layer
1. Create `backend/app/routers/graph.py`
2. Implement all REST endpoints
3. Add authentication and project access checks
4. Write API integration tests
5. Update FastAPI main.py to include graph router

### Week 3: Indexer CLI
1. Create `backend/scripts/graph_indexer.py`
2. Implement Python AST parser
3. Implement TypeScript/JavaScript tree-sitter parser
4. Add TODO/FIXME extraction to SpecItems
5. Implement incremental indexing (hash comparison)
6. Add progress tracking and error handling
7. Write indexer unit tests
8. Run integration test on CommandCenter backend

### Week 4: NATS Integration & Audits
1. Define NATS subjects and Pydantic event schemas
2. Add NATS publishers to GraphService and indexer
3. Add NATS consumers to GraphService (audit results)
4. Create `backend/scripts/audit_agents.py` (stubs)
5. Implement artifact storage (report files)
6. Add audit report API endpoint
7. Write end-to-end integration test
8. Performance testing and optimization

---

## File Structure

```
backend/
├── app/
│   ├── models/
│   │   └── graph.py                    # ✅ DONE (675 lines)
│   ├── services/
│   │   └── graph_service.py            # Week 1 - NEW
│   ├── routers/
│   │   └── graph.py                    # Week 2 - NEW
│   └── schemas/
│       └── graph.py                    # Week 1 - NEW
├── scripts/
│   ├── graph_indexer.py                # Week 3 - NEW
│   └── audit_agents.py                 # Week 4 - NEW
└── alembic/
    └── versions/
        └── 18d6609ae6d0_add_phase_7_graph_schema.py  # ✅ DONE

tests/
├── services/
│   └── test_graph_service.py           # Week 1 - NEW
├── routers/
│   └── test_graph.py                   # Week 2 - NEW
├── scripts/
│   └── test_graph_indexer.py           # Week 3 - NEW
└── integration/
    └── test_graph_pipeline.py          # Week 4 - NEW

snapshots/
└── audits/                             # Week 4 - NEW
    └── {project_id}/
        └── {audit_id}/
            └── report.json
```

---

## Configuration

### Environment Variables

Add to `.env`:
```bash
# Phase 7: Graph Service
GRAPH_INDEXER_BATCH_SIZE=100           # Files per DB transaction
GRAPH_INDEXER_PARALLEL_WORKERS=4       # Parallel file processing
GRAPH_QUERY_DEFAULT_DEPTH=2            # Default graph traversal depth
GRAPH_AUDIT_TIMEOUT=300                # Audit timeout in seconds

# Already configured (from Phases 1-4)
NATS_URL=nats://localhost:4222
DATABASE_URL=postgresql+asyncpg://...
```

### Dependencies

Add to `backend/requirements.txt`:
```
# Existing dependencies
fastapi
sqlalchemy[asyncio]
asyncpg
nats-py

# Phase 7 additions
tree-sitter==0.20.4                    # AST parsing
tree-sitter-javascript==0.20.3         # JS/TS support
click==8.1.7                           # CLI framework
tqdm==4.66.1                           # Progress bars
```

---

## Future Enhancements (Post-Milestone 1)

### Milestone 2: TaskGraph & Deep Integration
- GraphLink entries connecting Repository → GraphRepo
- ResearchTask → GraphSymbol links
- Enhanced ghost node visualization

### Milestone 3: Real Audit Tools
- Replace stubs with bandit, semgrep, LLM review
- Proper severity scoring and recommendations
- HTML report generation
- Integration with GitHub Issues

### Phase 8: VISLZR Frontend
- GraphQL API (Apollo Server)
- Interactive graph visualization (React Flow, D3.js)
- Real-time updates via WebSocket
- Time-travel debugging (historical graph states)

### Phase 9: Federation
- Cross-project dependency tracking
- Ecosystem-wide security sweeps
- Global search across all projects

---

## Summary

Phase 7 delivers a **production-ready code knowledge graph** using a layered architecture:

1. **GraphService**: Business logic for queries and mutations
2. **REST API**: FastAPI endpoints for graph access
3. **Indexer CLI**: Python tool for code ingestion with AST parsing
4. **NATS Integration**: Event-driven architecture for real-time updates
5. **Audit System**: Trigger and track security/quality checks

**Key Strengths:**
- Consistent with existing Python/FastAPI architecture
- Multi-tenant by design
- Leverages existing NATS infrastructure
- Light integration (low risk, fast delivery)
- Clear upgrade path for future enhancements

**Acceptance Criteria:**
- Index 1000+ files in < 2 minutes
- Query 5000+ nodes in < 1.5 seconds
- Complete audit flow in < 3 seconds
- Multi-tenant isolation enforced

**Ready for implementation!** 🚀
