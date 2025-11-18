# Docker-First Development Workflow

**Last Updated**: 2025-11-06
**Status**: Production-Ready ✅

## Philosophy

> **Development Environment = Production Environment**

All development happens inside Docker containers to ensure:
- ✅ Zero environment mismatches (venv versions, Python versions, etc.)
- ✅ Identical behavior in development and production
- ✅ Works on any machine (Mac, Linux, Windows)
- ✅ Team members get consistent environment
- ✅ No local dependency conflicts

## Quick Start

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Run tests
docker-compose exec backend pytest

# Access shell
docker-compose exec backend bash
```

## Common Operations

### Database Migrations

```bash
# Create a new migration (auto-generate from models)
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Check current migration version
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history

# Rollback one migration
docker-compose exec backend alembic downgrade -1
```

**Copy migration to host:**
```bash
# After creating migration in container
docker cp commandcenter_backend:/app/alembic/versions/MIGRATION_ID.py backend/alembic/versions/
```

### Running Tests

```bash
# All tests
docker-compose exec backend pytest

# Specific test file
docker-compose exec backend pytest tests/test_models.py

# With coverage
docker-compose exec backend pytest --cov=app

# Verbose output
docker-compose exec backend pytest -v
```

### Code Quality

```bash
# Format code with Black
docker-compose exec backend black app/

# Check with Black
docker-compose exec backend black --check app/

# Lint with flake8
docker-compose exec backend flake8 app/

# Type check with mypy
docker-compose exec backend mypy app/
```

### Python Shell / REPL

```bash
# IPython shell with app context
docker-compose exec backend python

# Example session:
>>> from app.models import GraphRepo
>>> from app.database import SessionLocal
>>> session = SessionLocal()
>>> repos = session.query(GraphRepo).all()
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 50 lines
docker-compose logs --tail=50 backend

# Postgres logs
docker-compose logs postgres
```

### Database Access

```bash
# PostgreSQL shell
docker-compose exec postgres psql -U commandcenter -d commandcenter

# Run SQL query
docker-compose exec postgres psql -U commandcenter -d commandcenter -c "SELECT COUNT(*) FROM graph_repos;"

# List tables
docker-compose exec postgres psql -U commandcenter -d commandcenter -c "\dt"
```

### Rebuilding After Dependency Changes

```bash
# When requirements.txt changes
docker-compose build backend

# Rebuild without cache (clean build)
docker-compose build --no-cache backend

# Rebuild and restart
docker-compose up -d --build backend
```

## Advantages vs Local Venv

| Aspect | Local Venv | Docker-First |
|--------|------------|--------------|
| Setup Time | Manual venv creation | Single `docker-compose up` |
| Python Version | Can mismatch | Always consistent |
| Dependencies | Can drift | Locked in Dockerfile |
| Team Onboarding | Install Python, create venv, install deps | Clone + `docker-compose up` |
| Production Parity | Different from prod | Identical to prod |
| Cleanup | venv artifacts everywhere | Single `docker-compose down` |

## When to Use Local Venv (Optional)

You can *optionally* maintain a local venv for:
- IDE type hints and autocomplete
- Local debugging with breakpoints

**Setup:**
```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**But**: All actual development should still happen via Docker.

## Troubleshooting

### Services Won't Start

```bash
# Check service status
docker-compose ps

# View logs for errors
docker-compose logs backend

# Restart services
docker-compose restart

# Nuclear option: full rebuild
docker-compose down
docker-compose up -d --build
```

### Database Connection Errors

```bash
# Check postgres is healthy
docker-compose ps postgres

# Verify connection from backend
docker-compose exec backend python -c "from app.database import engine; engine.connect()"
```

### Port Conflicts

If ports are already in use:
1. Edit `.env` to change ports
2. Or use Traefik (see `docs/TRAEFIK_SETUP.md`)

### Permission Issues

If you get permission errors when copying files:
```bash
# Fix ownership
sudo chown -R $(whoami):$(whoami) backend/alembic/versions/
```

## Phase 7 Migration Example

This workflow was used to successfully create the Phase 7 graph schema migration:

```bash
# 1. Start services
docker-compose up -d postgres backend

# 2. Create migration (auto-detected 11 new graph tables)
docker-compose exec backend alembic revision --autogenerate -m "Add Phase 7 graph schema"

# 3. Copy migration to host
docker cp commandcenter_backend:/app/alembic/versions/18d6609ae6d0_add_phase_7_graph_schema.py \
  backend/alembic/versions/

# 4. Apply migration
docker-compose exec backend alembic upgrade head

# 5. Verify tables created
docker-compose exec postgres psql -U commandcenter -d commandcenter -c "\dt graph_*"
```

Result: 11 Phase 7 graph tables created successfully ✅

## Best Practices

1. **Always use Docker for migrations** - Ensures consistent database schema
2. **Copy migration files to host** - Keep them in version control
3. **Test before committing** - Run `alembic upgrade head` to verify migration works
4. **Use docker-compose exec -T** for scripts - The `-T` flag disables TTY allocation for piping
5. **Check logs frequently** - `docker-compose logs -f backend` during development

## Next Steps

See related documentation:
- `docs/CLAUDE.md` - Full development guide
- `docs/TRAEFIK_SETUP.md` - Zero-conflict deployment
- `docs/DATA_ISOLATION.md` - Multi-instance security
