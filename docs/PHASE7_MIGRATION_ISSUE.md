# Phase 7 Migration Issue & Resolution

**Date**: 2025-11-05
**Status**: BLOCKED - Venv Python version mismatch

## Problem

When attempting to create the Alembic migration for Phase 7 graph schema, encountered error:

```
sqlalchemy.exc.InvalidRequestError: The asyncio extension requires an async driver to be used. The loaded 'psycopg2' is not async.
```

## Root Cause

**Python version mismatch in venv**:
- Venv was created with Python 3.12
- Currently running with Python 3.13.8
- Packages installed in `venv/lib/python3.12/site-packages/`
- Python looking in `venv/lib/python3.13/site-packages/`
- Result: `asyncpg` installed but not importable

## Investigation Steps

1. ✅ Installed Phase 7 dependencies successfully
   - strawberry-graphql[fastapi]>=0.235.0
   - tree-sitter>=0.21.0
   - tree-sitter-languages>=1.10.0
   - nats-py==2.7.2

2. ✅ Updated `requirements.txt` with Phase 7 deps

3. ✅ Created graph models (`backend/app/models/graph.py`)

4. ✅ Updated `alembic/env.py` to import graph models

5. ✅ Fixed DATABASE_URL to use async driver:
   - Changed from: `postgresql://...`
   - Changed to: `postgresql+asyncpg://...`

6. ❌ **BLOCKED**: Venv Python mismatch prevents asyncpg import

## Resolution Options

### Option 1: Recreate venv with Python 3.12 (Recommended)

```bash
cd /Users/danielconnolly/Projects/CommandCenter/backend

# Deactivate current venv
deactivate

# Remove old venv
rm -rf venv

# Create new venv with Python 3.12 explicitly
python3.12 -m venv venv

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Option 2: Upgrade venv to Python 3.13

```bash
cd /Users/danielconnolly/Projects/CommandCenter/backend

# Deactivate current venv
deactivate

# Remove old venv
rm -rf venv

# Create new venv with Python 3.13
python3.13 -m venv venv

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: Python 3.13 is very new (released Oct 2024). Stick with 3.12 for stability.

### Option 3: Use system Python (Not Recommended)

Run Alembic without venv (uses system Python). Not recommended due to dependency isolation issues.

## After venv Fix

Once venv is recreated, run:

```bash
cd /Users/danielconnolly/Projects/CommandCenter/backend
source venv/bin/activate

# Verify asyncpg is importable
python -c "import asyncpg; print(asyncpg.__version__)"

# Create migration
alembic revision --autogenerate -m "Add Phase 7 graph schema"

# Apply migration
alembic upgrade head
```

## Verification Commands

```bash
# Check Python version
python --version

# Check venv location
which python

# Check sys.path
python -c "import sys; print('\\n'.join(sys.path))"

# Verify asyncpg
python -c "import asyncpg; print(asyncpg.__version__)"

# Verify SQLAlchemy async support
python -c "from sqlalchemy.ext.asyncio import create_async_engine; print('OK')"
```

## Files Modified So Far

- ✅ `backend/app/models/graph.py` - 845 lines, 11 models, 10 enums
- ✅ `backend/app/models/__init__.py` - Added graph model exports
- ✅ `backend/requirements.txt` - Added Phase 7 dependencies
- ✅ `backend/alembic/env.py` - Import graph models
- ✅ `.env` - Changed DATABASE_URL to `postgresql+asyncpg://...`

## Next Steps

1. **Fix venv** (use Option 1 - Python 3.12)
2. Create Alembic migration
3. Apply migration to database
4. Continue with Milestone 1 completion:
   - Set up graph service module structure
   - Begin Milestone 2 (Indexer implementation)

---

**Note for User**: The venv recreation is a one-time fix. All Phase 7 code is ready; we just need a working Python environment to run the migration.
