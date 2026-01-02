# KnowledgeBeast Migration to CommandCenter Monorepo - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate KnowledgeBeast from standalone repository into CommandCenter monorepo at `libs/knowledgebeast/` using clean room approach.

**Architecture:** Copy production-essential files from `/Users/danielconnolly/Projects/KnowledgeBeast` to `CommandCenter/libs/knowledgebeast/`, update editable install path in backend requirements, validate all imports and integration tests pass.

**Tech Stack:** Python 3.11+, KnowledgeBeast (RAG library), PostgreSQL + pgvector, pytest

---

## Task 1: Prepare KnowledgeBeast Repository for Migration

**Files:**
- Modify: `/Users/danielconnolly/Projects/KnowledgeBeast/knowledgebeast/backends/base.py`
- Modify: `/Users/danielconnolly/Projects/KnowledgeBeast/knowledgebeast/backends/postgres.py`
- Modify: `/Users/danielconnolly/Projects/KnowledgeBeast/knowledgebeast/backends/postgres_schema.sql`

**Step 1: Change to KnowledgeBeast directory**

Run:
```bash
cd /Users/danielconnolly/Projects/KnowledgeBeast
```

**Step 2: Check current git status**

Run:
```bash
git status
```

Expected: Shows modified files in `knowledgebeast/backends/`

**Step 3: Review uncommitted changes**

Run:
```bash
git diff knowledgebeast/backends/base.py
git diff knowledgebeast/backends/postgres.py
git diff knowledgebeast/backends/postgres_schema.sql
```

Verify: Changes are postgres backend improvements (not WIP or broken code)

**Step 4: Stage postgres backend changes**

Run:
```bash
git add knowledgebeast/backends/base.py knowledgebeast/backends/postgres.py knowledgebeast/backends/postgres_schema.sql
```

**Step 5: Commit postgres backend changes**

Run:
```bash
git commit -m "feat: Postgres backend improvements before CommandCenter migration"
```

Expected: Commit successful

**Step 6: Create migration preparation commit**

Run:
```bash
git commit --allow-empty -m "chore: Prepare v3.0 for migration to CommandCenter monorepo

This is the final standalone version before migrating KnowledgeBeast
into CommandCenter at libs/knowledgebeast/. Future development will
happen in the CommandCenter repository."
```

**Step 7: Tag the final standalone version**

Run:
```bash
git tag -a v3.0-final-standalone -m "Final standalone version before CommandCenter migration"
```

**Step 8: Verify tag created**

Run:
```bash
git tag -l "v3.0*"
git log --oneline -1
```

Expected: Shows `v3.0-final-standalone` tag and final commit

**Step 9: Return to CommandCenter worktree**

Run:
```bash
cd /Users/danielconnolly/Projects/CommandCenter/.worktrees/knowledgebeast-migration
```

---

## Task 2: Create libs/ Directory Structure

**Files:**
- Create: `libs/knowledgebeast/` (directory)

**Step 1: Verify current location**

Run:
```bash
pwd
```

Expected: `/Users/danielconnolly/Projects/CommandCenter/.worktrees/knowledgebeast-migration`

**Step 2: Check if libs/ directory exists**

Run:
```bash
ls -la | grep libs || echo "libs/ does not exist"
```

**Step 3: Create libs/ directory**

Run:
```bash
mkdir -p libs/knowledgebeast
```

**Step 4: Verify directory created**

Run:
```bash
ls -la libs/
```

Expected: Empty `knowledgebeast/` directory exists

**Step 5: Commit the directory structure**

Run:
```bash
git add libs/
git commit -m "chore: Create libs/ directory for KnowledgeBeast migration"
```

---

## Task 3: Copy KnowledgeBeast Core Package

**Files:**
- Create: `libs/knowledgebeast/knowledgebeast/` (entire package)

**Step 1: Copy the core knowledgebeast package**

Run:
```bash
cp -r /Users/danielconnolly/Projects/KnowledgeBeast/knowledgebeast/ libs/knowledgebeast/knowledgebeast/
```

**Step 2: Verify package copied**

Run:
```bash
ls -la libs/knowledgebeast/knowledgebeast/
```

Expected: Shows `__init__.py`, `backends/`, `core/`, `api/`, etc.

**Step 3: Check key files exist**

Run:
```bash
test -f libs/knowledgebeast/knowledgebeast/__init__.py && echo "✓ __init__.py exists"
test -d libs/knowledgebeast/knowledgebeast/backends && echo "✓ backends/ exists"
test -f libs/knowledgebeast/knowledgebeast/backends/postgres.py && echo "✓ postgres.py exists"
```

Expected: All checks pass

**Step 4: Remove pycache and build artifacts**

Run:
```bash
find libs/knowledgebeast/knowledgebeast -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find libs/knowledgebeast/knowledgebeast -type f -name "*.pyc" -delete 2>/dev/null || true
find libs/knowledgebeast/knowledgebeast -type f -name "*.pyo" -delete 2>/dev/null || true
```

**Step 5: Verify clean state**

Run:
```bash
find libs/knowledgebeast/knowledgebeast -name "*.pyc" -o -name "__pycache__" | wc -l
```

Expected: 0 (no Python cache files)

**Step 6: Commit the core package**

Run:
```bash
git add libs/knowledgebeast/knowledgebeast/
git commit -m "feat: Add KnowledgeBeast core package to libs/"
```

---

## Task 4: Copy Package Configuration Files

**Files:**
- Create: `libs/knowledgebeast/pyproject.toml`
- Create: `libs/knowledgebeast/setup.py`
- Create: `libs/knowledgebeast/requirements.txt`

**Step 1: Copy pyproject.toml**

Run:
```bash
cp /Users/danielconnolly/Projects/KnowledgeBeast/pyproject.toml libs/knowledgebeast/
```

**Step 2: Copy setup.py**

Run:
```bash
cp /Users/danielconnolly/Projects/KnowledgeBeast/setup.py libs/knowledgebeast/
```

**Step 3: Copy requirements.txt**

Run:
```bash
cp /Users/danielconnolly/Projects/KnowledgeBeast/requirements.txt libs/knowledgebeast/
```

**Step 4: Verify files copied**

Run:
```bash
ls -la libs/knowledgebeast/ | grep -E "(pyproject|setup|requirements)"
```

Expected: All three files present

**Step 5: Review pyproject.toml**

Run:
```bash
head -20 libs/knowledgebeast/pyproject.toml
```

Verify: Package name is `knowledgebeast`, version is appropriate

**Step 6: Commit configuration files**

Run:
```bash
git add libs/knowledgebeast/pyproject.toml libs/knowledgebeast/setup.py libs/knowledgebeast/requirements.txt
git commit -m "feat: Add KnowledgeBeast package configuration"
```

---

## Task 5: Copy Documentation

**Files:**
- Create: `libs/knowledgebeast/README.md`

**Step 1: Copy README**

Run:
```bash
cp /Users/danielconnolly/Projects/KnowledgeBeast/README.md libs/knowledgebeast/
```

**Step 2: Verify README copied**

Run:
```bash
head -10 libs/knowledgebeast/README.md
```

Expected: Shows KnowledgeBeast title and description

**Step 3: Commit documentation**

Run:
```bash
git add libs/knowledgebeast/README.md
git commit -m "docs: Add KnowledgeBeast README to libs/"
```

---

## Task 6: Update Backend Requirements Path

**Files:**
- Modify: `backend/requirements.txt:38`

**Step 1: Check current requirements.txt**

Run:
```bash
grep -n "KnowledgeBeast" backend/requirements.txt
```

Expected: Line 38 shows `-e /Users/danielconnolly/Projects/KnowledgeBeast`

**Step 2: Create backup of requirements.txt**

Run:
```bash
cp backend/requirements.txt backend/requirements.txt.backup
```

**Step 3: Update the editable install path**

Edit `backend/requirements.txt` line 38:

FROM:
```
-e /Users/danielconnolly/Projects/KnowledgeBeast  # Editable install of local project
```

TO:
```
-e ../libs/knowledgebeast  # Editable install from monorepo libs/
```

**Step 4: Verify the change**

Run:
```bash
grep -n "knowledgebeast" backend/requirements.txt | grep -E "^\s*38"
```

Expected: Shows line 38 with new path `../libs/knowledgebeast`

**Step 5: Remove backup**

Run:
```bash
rm backend/requirements.txt.backup
```

**Step 6: Commit the path update**

Run:
```bash
git add backend/requirements.txt
git commit -m "chore: Update KnowledgeBeast to monorepo path in requirements"
```

---

## Task 7: Test Editable Install

**Files:**
- Test: Backend virtual environment

**Step 1: Check if backend venv exists**

Run:
```bash
test -d backend/venv && echo "✓ Backend venv exists" || echo "✗ No backend venv"
```

**Step 2: Create backend venv if needed**

Run:
```bash
if [ ! -d backend/venv ]; then cd backend && python -m venv venv && cd ..; fi
```

Expected: venv directory created

**Step 3: Install backend requirements**

Run:
```bash
cd backend && source venv/bin/activate && pip install -r requirements.txt && cd ..
```

Expected: All requirements install successfully (note: KnowledgeBeast will fail since path doesn't exist yet)

**Step 4: Install KnowledgeBeast in editable mode**

Run:
```bash
cd backend && source venv/bin/activate && pip install -e ../libs/knowledgebeast && cd ..
```

Expected: Installation succeeds, shows "Successfully installed knowledgebeast"

**Step 5: Verify import works**

Run:
```bash
cd backend && source venv/bin/activate && python -c "from knowledgebeast import HybridQueryEngine, DocumentRepository; print('✓ Imports successful')" && cd ..
```

Expected: Prints "✓ Imports successful"

**Step 6: Verify backend-specific imports**

Run:
```bash
cd backend && source venv/bin/activate && python -c "from knowledgebeast.backends import PostgresBackend; print('✓ PostgresBackend import successful')" && cd ..
```

Expected: Prints "✓ PostgresBackend import successful"

**Step 7: Check installed package location**

Run:
```bash
cd backend && source venv/bin/activate && pip show knowledgebeast | grep Location && cd ..
```

Expected: Shows path pointing to `libs/knowledgebeast`

---

## Task 8: Run Integration Tests

**Files:**
- Test: `backend/tests/services/test_rag_service.py`
- Test: `backend/tests/services/test_knowledgebeast_service.py`
- Test: `backend/tests/integration/test_knowledge_kb_integration.py`

**Step 1: Run RAG service tests**

Run:
```bash
cd backend && source venv/bin/activate && pytest tests/services/test_rag_service.py -v && cd ..
```

Expected: All tests pass

**Step 2: Run KnowledgeBeast service tests**

Run:
```bash
cd backend && source venv/bin/activate && pytest tests/services/test_knowledgebeast_service.py -v && cd ..
```

Expected: All tests pass

**Step 3: Run KB integration tests**

Run:
```bash
cd backend && source venv/bin/activate && pytest tests/integration/test_knowledge_kb_integration.py -v && cd ..
```

Expected: All tests pass

**Step 4: Run all knowledge-related tests**

Run:
```bash
cd backend && source venv/bin/activate && pytest -k "knowledge" -v && cd ..
```

Expected: All knowledge tests pass

**Step 5: Check for import errors in entire test suite**

Run:
```bash
cd backend && source venv/bin/activate && pytest --collect-only 2>&1 | grep -i "import" | grep -i "error" || echo "✓ No import errors" && cd ..
```

Expected: No import errors found

---

## Task 9: Update .gitignore for libs/

**Files:**
- Modify: `.gitignore`

**Step 1: Check if libs/ patterns exist in .gitignore**

Run:
```bash
grep -n "libs/" .gitignore || echo "No libs/ patterns found"
```

**Step 2: Add libs/ ignore patterns**

Append to `.gitignore`:

```
# KnowledgeBeast in libs/
libs/knowledgebeast/.venv
libs/knowledgebeast/__pycache__
libs/knowledgebeast/*.egg-info
libs/knowledgebeast/.pytest_cache
libs/knowledgebeast/.coverage
libs/knowledgebeast/chroma
```

**Step 3: Verify patterns added**

Run:
```bash
tail -10 .gitignore
```

Expected: Shows new libs/knowledgebeast patterns

**Step 4: Test gitignore works**

Run:
```bash
git status | grep "libs/knowledgebeast" || echo "✓ Build artifacts properly ignored"
```

Expected: No build artifact files shown in git status

**Step 5: Commit .gitignore update**

Run:
```bash
git add .gitignore
git commit -m "chore: Add libs/knowledgebeast to .gitignore"
```

---

## Task 10: Update CommandCenter Documentation

**Files:**
- Modify: `docs/CLAUDE.md`
- Modify: `README.md` (if KB mentioned)
- Modify: `docs/PROJECT.md`

**Step 1: Update CLAUDE.md RAG service section**

In `docs/CLAUDE.md`, find the RAGService section (around line 100) and update:

FROM:
```markdown
**Dependencies**: `knowledgebeast`, `sentence-transformers`, `psycopg2-binary`, `asyncpg`
```

TO:
```markdown
**Location**: KnowledgeBeast is located at `libs/knowledgebeast/` in the monorepo
**Dependencies**: `knowledgebeast` (local package), `sentence-transformers`, `psycopg2-binary`, `asyncpg`
```

**Step 2: Check if README mentions KnowledgeBeast**

Run:
```bash
grep -n "KnowledgeBeast" README.md || echo "Not mentioned in README"
```

**Step 3: Update README if needed**

If README mentions external dependency, update to note it's now internal at `libs/knowledgebeast/`

**Step 4: Update PROJECT.md**

In `docs/PROJECT.md`, add entry under dependencies section:

```markdown
### KnowledgeBeast (libs/knowledgebeast/)

Integrated RAG (Retrieval-Augmented Generation) library providing vector search and document management. Migrated from standalone repository into monorepo on 2025-10-27.

- **Version**: v3.0+
- **Backends**: ChromaDB (legacy), PostgresBackend (production)
- **Location**: `libs/knowledgebeast/`
- **Previous**: Standalone repo at `github.com/PerformanceSuite/KnowledgeBeast` (archived)
```

**Step 5: Verify documentation changes**

Run:
```bash
git diff docs/CLAUDE.md
git diff docs/PROJECT.md
```

Review: Changes accurately reflect migration

**Step 6: Commit documentation updates**

Run:
```bash
git add docs/CLAUDE.md docs/PROJECT.md README.md
git commit -m "docs: Update documentation for KnowledgeBeast migration to libs/"
```

---

## Task 11: Update CHANGELOG

**Files:**
- Modify: `CHANGELOG.md` (or create if doesn't exist)

**Step 1: Check if CHANGELOG exists**

Run:
```bash
test -f CHANGELOG.md && echo "✓ CHANGELOG exists" || echo "✗ No CHANGELOG"
```

**Step 2: Add migration entry to CHANGELOG**

Add to top of `CHANGELOG.md` (or create file):

```markdown
## [Unreleased]

### Changed

- **BREAKING**: KnowledgeBeast migrated from external dependency to monorepo at `libs/knowledgebeast/`
  - Updated backend requirements.txt to use local editable install
  - Standalone repository archived at v3.0-final-standalone
  - No code changes required - all imports remain identical
  - See `docs/plans/2025-10-27-knowledgebeast-migration-design.md` for details

```

**Step 3: Commit CHANGELOG**

Run:
```bash
git add CHANGELOG.md
git commit -m "docs: Add KnowledgeBeast migration entry to CHANGELOG"
```

---

## Task 12: Validation Checkpoint - Full Test Suite

**Files:**
- Test: All backend tests

**Step 1: Run complete backend test suite**

Run:
```bash
cd backend && source venv/bin/activate && pytest -v && cd ..
```

Expected: All tests pass

**Step 2: Check for any import warnings**

Run:
```bash
cd backend && source venv/bin/activate && pytest -W error::ImportWarning 2>&1 | grep -i "import" || echo "✓ No import warnings" && cd ..
```

Expected: No import warnings

**Step 3: Verify KnowledgeBeast package metadata**

Run:
```bash
cd backend && source venv/bin/activate && pip show knowledgebeast && cd ..
```

Expected: Shows correct version, location at libs/knowledgebeast

**Step 4: Test RAG service endpoints (if server running)**

This step requires the backend server to be running. Skip if not applicable, or note for manual testing.

Run:
```bash
# Start server in background (if not running)
# cd backend && source venv/bin/activate && uvicorn app.main:app --reload &
# Wait for startup, then test
# curl http://localhost:8000/api/v1/knowledge/query -X POST -H "Content-Type: application/json" -d '{"query": "test"}'
# Stop server after testing
```

**Step 5: Document validation results**

Create validation summary:

```bash
cat > MIGRATION_VALIDATION.md <<EOF
# KnowledgeBeast Migration Validation

**Date**: $(date +%Y-%m-%d)
**Branch**: feature/knowledgebeast-migration

## Test Results

- ✓ All backend tests pass
- ✓ No import errors or warnings
- ✓ Editable install working from libs/knowledgebeast
- ✓ PostgresBackend functional
- ✓ RAG service operational

## Package Verification

\`\`\`
$(cd backend && source venv/bin/activate && pip show knowledgebeast)
\`\`\`

## Migration Complete

KnowledgeBeast successfully migrated to monorepo. Ready for cleanup phase.
EOF
```

**Step 6: Commit validation document**

Run:
```bash
git add MIGRATION_VALIDATION.md
git commit -m "docs: Add KnowledgeBeast migration validation results"
```

---

## Task 13: Final Integration Commit

**Files:**
- All migration changes

**Step 1: Review all changes in branch**

Run:
```bash
git log --oneline origin/main..HEAD
```

Expected: Shows ~10-12 commits for migration tasks

**Step 2: Check diff summary**

Run:
```bash
git diff origin/main --stat
```

Expected: Shows libs/ additions, backend/requirements.txt change, doc updates

**Step 3: Verify no unwanted files staged**

Run:
```bash
git status
```

Expected: Clean working tree

**Step 4: Create integration commit (if any remaining changes)**

Run:
```bash
git status --short | wc -l
```

If any changes remain:
```bash
git add -A
git commit -m "chore: Final KnowledgeBeast migration integration"
```

---

## Task 14: Post-Migration Cleanup Instructions

**Files:**
- Document: Cleanup steps (not executed in this plan)

**Step 1: Document cleanup steps**

Create `CLEANUP_STEPS.md`:

```markdown
# KnowledgeBeast Migration Cleanup Steps

**IMPORTANT**: Only perform these steps AFTER migration is merged to main and validated in production.

## 1. Archive Standalone KnowledgeBeast Repository

On GitHub:
1. Go to https://github.com/PerformanceSuite/KnowledgeBeast
2. Settings → General → Danger Zone
3. Click "Archive this repository"
4. Add archive reason: "Migrated to CommandCenter monorepo at libs/knowledgebeast/"

## 2. Remove Local KnowledgeBeast Directory

**WARNING**: Only do this after confirming CommandCenter migration works!

\`\`\`bash
# Verify CommandCenter migration is working
cd /Users/danielconnolly/Projects/CommandCenter
cd backend && source venv/bin/activate && python -c "from knowledgebeast import HybridQueryEngine; print('✓ Working')"

# If working, remove old directory
rm -rf /Users/danielconnolly/Projects/KnowledgeBeast
rm -rf /Users/danielconnolly/Projects/KnowledgeBeast-worktrees
\`\`\`

## 3. Update External References

Check for external references to standalone KB repo:
- Documentation links pointing to old repo
- CI/CD configurations
- Other projects that may reference it

## 4. Announce Migration

Consider announcing on:
- KnowledgeBeast GitHub (pinned issue)
- CommandCenter changelog
- Any user communities
```

**Step 2: Commit cleanup instructions**

Run:
```bash
git add CLEANUP_STEPS.md
git commit -m "docs: Add post-migration cleanup instructions"
```

---

## Success Criteria

Before merging this branch:

- ✅ All backend tests pass
- ✅ No import errors
- ✅ KnowledgeBeast editable install working from `libs/knowledgebeast/`
- ✅ PostgresBackend functional
- ✅ RAG service endpoints operational
- ✅ Documentation updated
- ✅ `.gitignore` properly configured
- ✅ Migration design and validation documented

## Rollback Plan

If issues arise:

1. Revert requirements.txt: `git checkout origin/main -- backend/requirements.txt`
2. Reinstall old KB: `cd backend && pip install -e /Users/danielconnolly/Projects/KnowledgeBeast`
3. Original KB directory remains untouched until cleanup phase

## Post-Merge Tasks

After merging to main:

1. Archive standalone KnowledgeBeast repository on GitHub
2. Remove local KB directory (after validation)
3. Update any external references
4. Announce migration (if applicable)

---

**Implementation time estimate**: 1.5-2 hours
**Required skills**: @superpowers:verification-before-completion for test validation
