# Next Session: KnowledgeBeast v3.0 Implementation

**Status**: Ready to Execute
**Date**: 2025-10-23
**Session Type**: Implementation (Week 1)

---

## Session Goals

**Primary Goal:** Implement backend abstraction layer for KnowledgeBeast v3.0

**Deliverables:**
- [ ] Create `knowledgebeast/backends/` module structure
- [ ] Implement `VectorBackend` abstract base class
- [ ] Wrap existing ChromaDB code in `ChromaDBBackend`
- [ ] Update `HybridQueryEngine` to use backend abstraction
- [ ] All existing tests passing (no functionality changes)

---

## Key Decisions Made

### Architecture Approved ✅
- Backend abstraction layer + Dagger testing
- Postgres backend with pgvector + ParadeDB
- ChromaDB backend for backward compatibility
- Both backends supported in v3.0.0

### Technical Decisions ✅
1. **Dagger**: Use for testing infrastructure (Week 3+), NOT blocking Week 1
2. **ParadeDB Distribution**: Dagger builds custom Postgres images
3. **Embedding Dimensions**: 384 default, 768 configurable
4. **Multi-Tenancy**: Prefixed tables (`kb_{project}_{collection}_docs`)

### Documents Created ✅
- `docs/KNOWLEDGEBEAST_POSTGRES_UPGRADE.md` - Full architecture & rollout plan
- `docs/UNIVERSAL_DAGGER_PATTERN.md` - Reusable Dagger pattern for all projects
- `~/.config/superpowers/skills/skills/development/using-dagger-for-infrastructure/SKILL.md` - Dagger skill

---

## Week 1 Implementation Plan (Next Session)

### Task 1: Create Backend Abstraction Module

**Location:** `KnowledgeBeast/knowledgebeast/backends/`

**Files to create:**
```
knowledgebeast/
└── backends/
    ├── __init__.py
    ├── base.py           # VectorBackend abstract class
    ├── chromadb.py       # ChromaDBBackend (legacy wrapper)
    └── postgres.py       # PostgresBackend (stub for Week 2)
```

**base.py structure:**
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

class VectorBackend(ABC):
    @abstractmethod
    async def add_documents(...) -> None: ...

    @abstractmethod
    async def query_vector(...) -> List[Tuple[str, float]]: ...

    @abstractmethod
    async def query_keyword(...) -> List[Tuple[str, float]]: ...

    @abstractmethod
    async def delete_documents(...) -> None: ...

    @abstractmethod
    async def get_statistics(...) -> Dict[str, Any]: ...
```

### Task 2: Implement ChromaDBBackend

**Goal:** Wrap existing ChromaDB code without changing functionality

**Pattern:**
```python
# knowledgebeast/backends/chromadb.py
from chromadb import Client, Settings
from .base import VectorBackend

class ChromaDBBackend(VectorBackend):
    """Legacy ChromaDB backend for backward compatibility"""

    def __init__(self, persist_directory: str, collection_name: str = "default"):
        self.client = Client(Settings(persist_directory=persist_directory))
        self.collection = self.client.get_or_create_collection(collection_name)

    async def add_documents(self, ids, embeddings, documents, metadatas):
        # Wrap existing ChromaDB API
        self.collection.add(ids=ids, embeddings=embeddings, ...)
```

### Task 3: Update HybridQueryEngine

**File:** `knowledgebeast/core/query_engine.py`

**Changes:**
```python
# Before (v2.x)
class HybridQueryEngine:
    def __init__(self, repository, model_name="all-MiniLM-L6-v2"):
        self.repository = repository
        # Direct ChromaDB usage

# After (v3.0)
class HybridQueryEngine:
    def __init__(
        self,
        repository,
        backend: VectorBackend = None,  # NEW!
        model_name="all-MiniLM-L6-v2"
    ):
        self.repository = repository
        self.backend = backend or self._get_default_backend()

    def _get_default_backend(self) -> VectorBackend:
        # Default to ChromaDB for backward compatibility
        from knowledgebeast.backends.chromadb import ChromaDBBackend
        return ChromaDBBackend(persist_directory="./chroma_db")
```

### Task 4: Run All Tests

**Goal:** Ensure no functionality changes

```bash
cd /Users/danielconnolly/Projects/KnowledgeBeast
pytest tests/ -v
# Expected: All 278 tests PASS
```

### Task 5: Commit Changes

```bash
git add knowledgebeast/backends/
git commit -m "feat: add backend abstraction layer (v3.0.0-alpha)

- Create VectorBackend abstract base class
- Implement ChromaDBBackend wrapper
- Update HybridQueryEngine to use backends
- Backward compatible (defaults to ChromaDB)
- All tests passing (no functionality changes)

Part of: KnowledgeBeast v3.0 Postgres backend upgrade"
```

---

## Worktree Setup

**Branch:** `feature/postgres-backend`

**Commands:**
```bash
cd /Users/danielconnolly/Projects/KnowledgeBeast
git worktree add .worktrees/postgres-backend -b feature/postgres-backend
cd .worktrees/postgres-backend
```

**Existing worktrees:**
- `.worktrees/advanced-features`
- `.worktrees/mcp-server-core`
- `.worktrees/multi-project-backend`
- etc. (15+ total)

---

## Success Criteria (End of Week 1)

- [ ] Backend abstraction layer implemented
- [ ] ChromaDBBackend wraps existing functionality
- [ ] All 278 tests passing
- [ ] No breaking changes (backward compatible)
- [ ] Clean git history (atomic commits)
- [ ] Ready for Week 2 (PostgresBackend implementation)

---

## Week 2 Preview (Future Session)

**After Week 1 complete:**
- Implement `PostgresBackend` with asyncpg
- Add pgvector integration (connection, queries)
- Stub ParadeDB integration (prepare for Week 3)
- Unit tests for PostgresBackend (mocked database)

---

## Resources & References

**Architecture:**
- `docs/KNOWLEDGEBEAST_POSTGRES_UPGRADE.md` - Complete upgrade plan
- `docs/UNIVERSAL_DAGGER_PATTERN.md` - Dagger patterns (Week 3+)

**Skills:**
- `skills/development/using-dagger-for-infrastructure/SKILL.md` - Dagger usage
- `skills/testing/test-driven-development/SKILL.md` - TDD approach
- `skills/debugging/verification-before-completion/SKILL.md` - Pre-commit checks

**CommandCenter Reference:**
- `.worktrees/feature/dagger-orchestration/` - Dagger implementation example

---

## Notes for Next Session

**Context to load:**
- ✅ All decisions documented in architecture docs
- ✅ Dagger pattern documented and ready for Week 3
- ✅ Worktrees already configured in KnowledgeBeast
- ✅ Test suite baseline: 278 tests passing

**Start with:**
1. Navigate to KnowledgeBeast repository
2. Create worktree: `feature/postgres-backend`
3. Begin Task 1 (create backends module)
4. Use TDD approach (tests first where applicable)
5. Commit atomically after each task

**Don't forget:**
- Use `/superpowers:write-plan` for formal plan
- Use `/superpowers:execute-plan` for batch execution with review gates
- Run tests frequently (after each major change)
- Commit early and often (atomic commits)

---

**Ready to execute!** 🚀
