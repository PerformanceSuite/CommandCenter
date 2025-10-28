# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Command Center** is a multi-project R&D management and knowledge base system. It tracks technologies, manages research tasks, and provides RAG-powered search across GitHub repositories. Built with FastAPI (Python 3.11) backend and React 18 + TypeScript frontend, deployed via Docker Compose.

**CRITICAL SECURITY REQUIREMENT**: Each project MUST have its own isolated CommandCenter instance. Never share instances across projects due to sensitive data (GitHub tokens, proprietary research, RAG embeddings). See `docs/DATA_ISOLATION.md` for complete isolation architecture.

## Development Commands

### Docker Compose (Recommended)

```bash
# Initial setup
make setup                    # Creates .env from template
make start                    # Start all services with port check
make stop                     # Stop all services
make logs                     # View all logs (follow mode)
make logs-backend             # Backend logs only
make logs-frontend            # Frontend logs only
make health                   # Check service health

# Development
make dev                      # Start in dev mode with live reload
make restart                  # Restart all services
make rebuild                  # Rebuild and restart (no cache)

# Shell access
make shell-backend            # Bash in backend container
make shell-frontend           # Shell in frontend container
make shell-db                 # PostgreSQL shell
```

### Database Operations

```bash
# Migrations (Alembic)
make migrate                  # Apply all pending migrations
make migrate-create MESSAGE="description"  # Create new migration

# Inside backend container:
docker-compose exec backend alembic upgrade head     # Apply migrations
docker-compose exec backend alembic downgrade -1    # Rollback one migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Database backup/restore
make db-backup                # Backup to backups/ directory
make db-restore               # Restore from latest backup
```

### PostgreSQL + pgvector Setup

**Required for RAG/Knowledge Base functionality**

The RAG service uses PostgreSQL with the pgvector extension for vector similarity search. A custom Postgres image is required.

```bash
# Option 1: Build with Dagger (recommended)
cd backend
python scripts/build-postgres.py

# Option 2: Build with Docker Compose (automatic on first run)
docker-compose build postgres

# Option 3: Use docker build directly
docker build -f backend/Dockerfile.postgres -t commandcenter-postgres:latest backend/

# Verify pgvector is installed
docker-compose exec postgres psql -U commandcenter -d commandcenter -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

**Migration**: The pgvector extension is automatically enabled via Alembic migration `e5bd4ea700b0_enable_pgvector_extension.py`

**Image Details**:
- Base: `postgres:16-alpine`
- Extension: `pgvector` (0.7.0 or latest)
- Build context: `backend/` directory
- Dockerfile: `backend/Dockerfile.postgres`
```

### Testing

```bash
# All tests
make test                     # Run backend + frontend tests

# Individual test suites
make test-backend             # pytest in backend container
make test-frontend            # npm test in frontend container

# Local development (outside Docker)
cd backend && pytest          # Backend tests
cd frontend && npm test       # Frontend tests
```

### Linting & Formatting

```bash
# Via Make
make lint                     # Run all linters
make format                   # Auto-format all code

# Backend (Black + Flake8)
docker-compose exec backend black --check app/
docker-compose exec backend black app/           # Format
docker-compose exec backend flake8 app/

# Frontend (ESLint + TypeScript)
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run type-check
```

### Local Development (Without Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev                    # Starts on port 3000

# Database (requires PostgreSQL + Redis running locally)
# Update .env with local DATABASE_URL and REDIS_URL
```

## Architecture & Key Patterns

### Service Layer Architecture

The backend follows a **service-oriented** pattern:

- **Routers** (`app/routers/`): FastAPI endpoints, handle HTTP requests/responses
- **Services** (`app/services/`): Business logic, external API integrations
- **Models** (`app/models/`): SQLAlchemy ORM models (database tables)
- **Schemas** (`app/schemas/`): Pydantic models (request/response validation)

**Pattern**: Routers call Services → Services use Models → Return Schemas

Example flow for repository sync:
1. `repositories.router` receives POST request
2. Calls `GitHubService.sync_repository()`
3. Updates `Repository` model in database
4. Returns `RepositoryResponse` schema

### Key Services

**GitHubService** (`app/services/github_service.py`):
- PyGithub wrapper for GitHub API
- Repository authentication, syncing, commit tracking
- Per-repository access tokens (encrypted via `app/utils/crypto.py`)
- Methods: `sync_repository()`, `list_user_repos()`, `get_repository_info()`

**RAGService** (`app/services/rag_service.py`):
- **KnowledgeBeast** with PostgreSQL + pgvector backend for knowledge base
- **Monorepo Package**: KnowledgeBeast is vendored in `libs/knowledgebeast/` (installed via `-e ../libs/knowledgebeast`)
- HuggingFaceEmbeddings (sentence-transformers, local, no API costs) for vector search
- Hybrid search: Vector similarity + keyword search with Reciprocal Rank Fusion
- Multi-tenant: Collection prefixes (project_{id}) for data isolation
- Document processing via Docling
- Methods: `query()`, `add_document()`, `get_statistics()`
- **Dependencies**: `knowledgebeast`, `sentence-transformers`, `psycopg2-binary`, `asyncpg`, `docling>=2.5.5`
- **Requires**: PostgreSQL with pgvector extension (see setup below)

### Database Models

**Core entities** (all in `app/models/`):
- `Repository`: GitHub repo tracking (owner, name, access_token, last_commit_sha)
- `Technology`: Tech radar entries (domain, title, vendor, status, relevance)
- `ResearchTask`: Research items (title, description, status, priority, linked to repos/tech)
- `KnowledgeEntry`: RAG document metadata (source, category, embedding_id)

**Relationships**:
- Technologies ↔ Repositories (many-to-many)
- ResearchTasks → Technologies (many-to-one)
- ResearchTasks → Repositories (many-to-one)

### Frontend Structure

**Component Organization** (`frontend/src/components/`):
- `Dashboard/`: Main dashboard with repo selector
- `TechnologyRadar/`: Tech radar visualization (Chart.js)
- `ResearchHub/`: Research task management
- `KnowledgeBase/`: RAG query interface
- `Settings/`: Repository manager, configuration
- `common/`: Shared components (Header, Sidebar, LoadingSpinner)

**State Management**:
- React hooks for local state
- Custom hooks: `useRepositories`, `useTechnologies`
- API calls via `services/api.ts` (axios wrapper)

**Routing**: React Router v6 (`App.tsx`)

### Data Isolation (Multi-Instance)

**Critical for security**:
- Each project needs unique `COMPOSE_PROJECT_NAME` in `.env`
- Separate Docker volumes: `{project}_postgres_data`, `{project}_rag_storage`
- Unique secrets: `SECRET_KEY`, `DB_PASSWORD` per instance
- Different ports if running multiple instances simultaneously

**Verification**:
```bash
docker volume ls | grep commandcenter    # Check volume isolation
docker ps --filter name=commandcenter    # Check container names
```

## Configuration

### Environment Variables (.env)

**Required**:
```bash
COMPOSE_PROJECT_NAME=yourproject-commandcenter  # MUST be unique per project
SECRET_KEY=<generate-with-openssl-rand-hex-32>
DB_PASSWORD=<strong-password>
```

**Ports** (customize for multiple instances):
```bash
BACKEND_PORT=8000      # Or 8010, 8020 for additional instances
FRONTEND_PORT=3000     # Or 3010, 3020
POSTGRES_PORT=5432     # Or 5433, 5434
REDIS_PORT=6379        # Or 6380, 6381
```

**GitHub Integration** (optional):
```bash
GITHUB_TOKEN=ghp_...   # Personal access token for repo syncing
```

**AI/RAG** (optional):
```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

**Database**:
```bash
DATABASE_URL=postgresql://commandcenter:${DB_PASSWORD}@postgres:5432/commandcenter
```

### Port Conflicts

If ports are in use:
1. Check conflicts: `./scripts/check-ports.sh`
2. Change ports in `.env`
3. **OR** use Traefik (zero port conflicts): See `docs/TRAEFIK_SETUP.md`

## API Endpoints

**Base URL**: `http://localhost:8000` (or configured `BACKEND_PORT`)

**API Docs**: `http://localhost:8000/docs` (Swagger UI)

**Key Endpoints**:
- `POST /api/v1/repositories` - Add repository
- `GET /api/v1/repositories` - List repositories
- `POST /api/v1/repositories/{id}/sync` - Sync repository
- `GET /api/v1/technologies` - List technologies
- `POST /api/v1/technologies` - Create technology
- `GET /api/v1/research` - List research tasks
- `POST /api/v1/knowledge/query` - Query RAG knowledge base

## Troubleshooting

### Common Issues

**Port conflicts**:
```bash
make check-ports              # Identify conflicts
# Update ports in .env or use Traefik
```

**Database connection errors**:
```bash
docker-compose logs postgres  # Check PostgreSQL logs
make health                   # Verify service health
# Ensure DATABASE_URL in .env matches docker-compose.yml
```

**Migration errors**:
```bash
# Check current migration state
docker-compose exec backend alembic current
# Force to latest
docker-compose exec backend alembic upgrade head
# If corrupted, may need to reset database (LOSES DATA)
make clean  # Removes volumes
make start  # Fresh start
```

**pgvector extension missing**:
```bash
# Rebuild the custom Postgres image with pgvector
docker-compose stop postgres
docker-compose build postgres
docker-compose up -d postgres

# Verify extension is installed
docker-compose exec postgres psql -U commandcenter -d commandcenter -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# If extension exists but not enabled, run migration
docker-compose exec backend alembic upgrade head
```

**RAG dependencies missing**:
```bash
# Dependencies are in requirements.txt (knowledgebeast, sentence-transformers)
# Rebuild backend if needed
docker-compose build backend
docker-compose up -d backend
```

**Frontend build errors**:
```bash
docker-compose logs frontend
# Check for TypeScript errors
docker-compose exec frontend npm run type-check
# Rebuild node_modules
docker-compose exec frontend rm -rf node_modules package-lock.json
docker-compose exec frontend npm install
```

### Logs & Debugging

```bash
make logs                     # All services
make logs-backend             # Backend only (API errors, exceptions)
make logs-frontend            # Frontend only (build errors)
make logs-db                  # PostgreSQL logs

# Filter logs for errors
docker-compose logs backend | grep -i error
```

## Additional Resources

- **Makefile**: Run `make help` to see all available commands
- **Documentation**:
  - `docs/DATA_ISOLATION.md` - Multi-instance security (READ FIRST)
  - `docs/DOCLING_SETUP.md` - RAG document processing
  - `docs/CONFIGURATION.md` - Environment configuration
  - `docs/PORT_MANAGEMENT.md` - Handling port conflicts
  - `docs/TRAEFIK_SETUP.md` - Zero-conflict deployment
- **Backend README**: `backend/README.md`
- **Frontend README**: `frontend/README.md`
