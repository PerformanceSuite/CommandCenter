# KnowledgeBeast Migration Guide

**Status**: ✅ Complete
**Branch**: `feature/knowledgebeast-migration`
**Version**: KnowledgeBeast v3.0-final-standalone → Monorepo package

---

## Migration Summary

CommandCenter has migrated from using KnowledgeBeast as an external PyPI dependency to a vendored monorepo package. This provides better control over the codebase, easier debugging, and tighter integration.

### What Changed

**Before**: External dependency via PyPI
```bash
# In requirements.txt
knowledgebeast==0.1.0
```

**After**: Monorepo vendored package
```bash
# In requirements.txt
-e ../libs/knowledgebeast
```

### Key Changes

1. **Package Location**: `libs/knowledgebeast/` (79 files, 24k+ lines of code)
2. **Installation**: Editable install from local path
3. **Dependencies Upgraded**:
   - `docling`: `>=1.0.0,<2.0.0` → `>=2.5.5`
   - `openpyxl`: `==3.1.2` → `>=3.1.5,<4.0.0`
4. **Backend**: PostgreSQL + pgvector (unchanged)
5. **API**: Fully backward compatible (no breaking changes)

---

## Post-Migration Cleanup Instructions

### 1. Merge the Migration Branch

```bash
# Switch to main branch
git checkout main

# Merge the migration branch
git merge feature/knowledgebeast-migration

# Push to remote
git push origin main
```

### 2. Update Development Environments

**All developers need to:**

```bash
# Pull latest changes
git pull origin main

# Recreate backend virtual environment
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies (including monorepo KnowledgeBeast)
pip install -r requirements.txt

# Verify imports
python -c "from knowledgebeast import KnowledgeBase; print('✅ KnowledgeBeast imported successfully')"
```

### 3. Update Docker Environments

**The backend Dockerfile may need updating to handle editable installs:**

Check `backend/Dockerfile` and ensure it properly handles the `../libs/knowledgebeast` path:

```dockerfile
# Copy libs directory first
COPY ../libs /app/libs

# Install requirements (including editable knowledgebeast)
RUN pip install --no-cache-dir -r requirements.txt
```

**Rebuild containers:**

```bash
# Stop existing containers
docker-compose down

# Rebuild with no cache
docker-compose build --no-cache backend

# Start fresh
docker-compose up -d
```

### 4. Clean Up Old Worktrees (Optional)

After merging, the worktree is no longer needed:

```bash
# Remove the worktree
rm -rf .worktrees/knowledgebeast-migration

# Clean up git worktree references
git worktree prune
```

### 5. Verify Production Deployment

**Before deploying to production:**

1. Run full test suite:
   ```bash
   make test
   # or
   cd backend && pytest
   ```

2. Verify RAG service functionality:
   ```bash
   # Start services
   make start

   # Test knowledge query endpoint
   curl -X POST http://localhost:8000/api/v1/knowledge/query \
     -H "Content-Type: application/json" \
     -d '{"query": "test query"}'
   ```

3. Check logs for any import errors:
   ```bash
   docker-compose logs backend | grep -i error
   ```

### 6. Update CI/CD Pipelines

If you have CI/CD pipelines, ensure they:

1. **Clone/checkout includes `libs/` directory**
2. **Install dependencies properly handles editable installs**
3. **Build process copies `libs/` to Docker context**

Example GitHub Actions workflow update:

```yaml
- name: Install dependencies
  run: |
    cd backend
    pip install -r requirements.txt  # Now includes -e ../libs/knowledgebeast
```

---

## Rollback Instructions (If Needed)

If issues arise after merging:

### Option 1: Revert the Merge

```bash
# Find the merge commit
git log --oneline -5

# Revert the merge commit
git revert -m 1 <merge-commit-sha>

# Push the revert
git push origin main
```

### Option 2: Use Previous Requirements

Temporarily switch back to PyPI package:

```bash
# Edit backend/requirements.txt
# Replace: -e ../libs/knowledgebeast
# With: knowledgebeast==0.1.0

# Reinstall
pip install -r requirements.txt
```

---

## Verification Checklist

After completing migration cleanup, verify:

- [ ] All developers can import `knowledgebeast` successfully
- [ ] Docker containers build without errors
- [ ] RAG queries return results
- [ ] No import errors in backend logs
- [ ] Tests pass (or pre-existing failures only)
- [ ] Documentation reflects monorepo structure
- [ ] CI/CD pipelines work with new structure

---

## Migration Timeline

- **2025-10-27 20:00-20:12**: Initial migration (9/14 tasks)
- **2025-10-27 20:44**: Documentation & validation complete (14/14 tasks)
- **Next**: Merge to main and deploy

---

## Support

If you encounter issues during cleanup:

1. Check `libs/knowledgebeast/README.md` for package documentation
2. Review `CHANGELOG.md` for detailed changes
3. Verify venv includes `knowledgebeast` package: `pip list | grep knowledgebeast`
4. Check Docker build logs: `docker-compose build backend 2>&1 | grep -i error`

---

## Architecture Notes

### Import Structure

```python
# Core imports (unchanged)
from knowledgebeast import KnowledgeBase, KnowledgeBeastConfig

# Backend imports (path updated)
from knowledgebeast.backends.postgres import PostgresBackend
```

### Package Structure

```
CommandCenter/
├── libs/
│   └── knowledgebeast/          # Monorepo package
│       ├── knowledgebeast/      # Package code
│       ├── pyproject.toml       # Package config
│       ├── setup.py             # Install config
│       └── requirements.txt     # Package dependencies
└── backend/
    ├── requirements.txt         # Includes: -e ../libs/knowledgebeast
    └── app/
        └── services/
            └── rag_service.py   # Uses KnowledgeBase
```

---

**Migration completed successfully** ✅

For questions or issues, refer to the [main documentation](./CLAUDE.md) or open an issue.
