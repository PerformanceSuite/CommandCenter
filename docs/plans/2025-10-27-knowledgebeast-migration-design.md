# KnowledgeBeast Migration to CommandCenter Monorepo

**Date:** 2025-10-27
**Status:** Design Approved
**Migration Approach:** Clean Room Migration

## Overview

Migrate KnowledgeBeast from standalone repository (`/Users/danielconnolly/Projects/KnowledgeBeast`) into CommandCenter monorepo as `libs/knowledgebeast/`. This consolidates a core CommandCenter feature into the main codebase while maintaining clean package structure.

## Goals

1. Consolidate KnowledgeBeast into CommandCenter monorepo
2. Maintain all existing functionality without breaking changes
3. Preserve existing imports (no code changes in CommandCenter backend)
4. Clean up non-production files during migration
5. Retire standalone KnowledgeBeast repository

## Non-Goals

- Preserving KnowledgeBeast git history (well-documented final state is sufficient)
- Maintaining standalone KnowledgeBeast repository post-migration
- Keeping KnowledgeBeast-specific test artifacts that don't apply to CommandCenter integration

## Design Decisions

### Directory Structure

**Target Location:** `CommandCenter/libs/knowledgebeast/`

**Rationale:**
- `libs/` is standard monorepo pattern for shared libraries
- Keeps KB organizationally separate from backend application code
- Future-proof: Can be used by frontend, CLI, or other services
- Preserves existing imports: `from knowledgebeast import X` continues to work

**Final Structure:**
```
CommandCenter/
├── libs/
│   └── knowledgebeast/
│       ├── knowledgebeast/          # Core package code
│       │   ├── __init__.py
│       │   ├── backends/
│       │   │   ├── base.py
│       │   │   ├── chroma.py
│       │   │   ├── postgres.py
│       │   │   └── postgres_schema.sql
│       │   ├── document_repository.py
│       │   ├── hybrid_query_engine.py
│       │   └── ...
│       ├── pyproject.toml           # Package configuration
│       ├── setup.py                 # For editable install
│       ├── README.md                # Core documentation
│       └── requirements.txt         # KB-specific dependencies
```

### Migration Approach: Clean Room

**Selected Approach:** Clean Room Migration with opportunistic cleanup

**Rationale:**
- Opportunity to leave behind accumulated cruft from standalone development
- Fresh start in monorepo context
- Only migrate production-essential files
- Cleaner long-term maintenance

**What to Migrate:**
- ✅ All `knowledgebeast/` source code (core package)
- ✅ `pyproject.toml`, `setup.py` (package configuration)
- ✅ `README.md` (documentation)
- ✅ `requirements.txt` (dependencies)
- ✅ Core integration tests validating KB works in CommandCenter

**What to Leave Behind:**
- ❌ `.git/` directory (no history preservation needed)
- ❌ KnowledgeBeast-specific isolation tests (CommandCenter integration tests cover this)
- ❌ `.claude/` session management files
- ❌ Standalone usage docs/examples
- ❌ Build artifacts (`.venv/`, `.coverage`, `.egg-info`)
- ❌ Benchmarks specific to standalone usage

### Path Updates

**Backend requirements.txt** (line 38):
```diff
- -e /Users/danielconnolly/Projects/KnowledgeBeast
+ -e ../libs/knowledgebeast
```

**No import changes needed** - All existing imports continue to work:
```python
from knowledgebeast import HybridQueryEngine, DocumentRepository
from knowledgebeast.backends import PostgresBackend
```

**Environment variables** - No changes needed, all existing KB env vars in `.env` continue to work

### Dependency Management

- KnowledgeBeast maintains its own `requirements.txt`
- Backend `requirements.txt` points to editable install: `-e ../libs/knowledgebeast`
- Must validate no version conflicts between KB and backend dependencies (especially `numpy`, `langchain`)

## Migration Process

### Step 1: Prepare KnowledgeBeast Repository

1. Commit uncommitted postgres backend changes in KnowledgeBeast repo
2. Create final commit documenting migration to CommandCenter
3. Tag as `v3.0-final-standalone` for historical reference

### Step 2: Create Clean Structure in CommandCenter

1. Create `libs/` directory in CommandCenter root
2. Create `libs/knowledgebeast/` structure
3. Copy production-essential files from source list above
4. Ensure proper file permissions preserved

### Step 3: Update CommandCenter References

1. Update `backend/requirements.txt` editable install path
2. Verify no hardcoded paths in config files
3. Update `.gitignore` to ignore `libs/knowledgebeast/.venv`, etc.
4. Check CommandCenter workspace file if needed

### Step 4: Validation Testing

1. Install KB in editable mode: `pip install -e ../libs/knowledgebeast` from backend/
2. Run CommandCenter's existing KB integration tests
3. Verify all imports resolve correctly
4. Test RAG service endpoints
5. Validate postgres backend functionality

### Step 5: Documentation Updates

1. Update CommandCenter `README.md` noting KB is now internal
2. Update architecture docs mentioning external KB dependency
3. Add migration entry to `CHANGELOG.md`
4. Update `PROJECT.md` if KB is mentioned

### Step 6: Cleanup

1. Archive standalone KnowledgeBeast GitHub repository (don't delete)
2. Remove local KnowledgeBeast directory after confirming all tests pass
3. Update any external references to standalone repo

## Rollback Plan

If issues arise during migration:

1. Keep original KB directory at `/Users/danielconnolly/Projects/KnowledgeBeast` until validation complete
2. Editable install can easily revert to old path in requirements.txt
3. Work in git branch for CommandCenter changes - can discard if needed
4. Standalone KB repo remains available during transition

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Dependency version conflicts | Audit dependencies before migration, test thoroughly |
| Missing files in clean room copy | Use comprehensive checklist, validate tests pass |
| Broken imports in CommandCenter | Keep package name identical, test all import paths |
| Lost functionality | Comprehensive integration testing before cleanup |

## Success Criteria

- ✅ All CommandCenter integration tests pass
- ✅ RAG service endpoints function correctly
- ✅ No import errors in CommandCenter backend
- ✅ Editable install works from `libs/knowledgebeast`
- ✅ PostgresBackend functionality verified
- ✅ Documentation updated reflecting new structure
- ✅ Standalone KB directory can be safely removed

## Timeline Estimate

**Total: 2-3 hours**

- Step 1 (Prepare KB): 15 minutes
- Step 2 (Create structure): 30 minutes
- Step 3 (Update references): 15 minutes
- Step 4 (Validation): 45-60 minutes
- Step 5 (Documentation): 30 minutes
- Step 6 (Cleanup): 15 minutes

## Follow-up Tasks

Post-migration tasks (not part of initial migration):

1. Consider consolidating KB-specific env vars into a `KNOWLEDGEBEAST_` prefix for clarity
2. Evaluate moving KB tests into CommandCenter test structure
3. Document KB architecture in CommandCenter docs
4. Create public announcement about KB repository retirement
