# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Command Center** is a multi-project R&D management and knowledge base system. It tracks technologies, manages research tasks, and provides RAG-powered search across GitHub repositories. Built with FastAPI (Python 3.11) backend and React 18 + TypeScript frontend, deployed via Docker Compose.

**Command Center Hub** is a companion application for managing multiple CommandCenter instances across different projects. Built with FastAPI backend and React frontend, it uses **Dagger SDK** for type-safe container orchestration instead of docker-compose subprocess calls.

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
- ChromaDB + LangChain for knowledge base
- HuggingFaceEmbeddings (local, no API costs) for vector search
- Document processing via Docling
- Methods: `query()`, `add_document()`, `get_statistics()`
- **Optional dependencies**: Install with `pip install langchain langchain-community langchain-chroma chromadb sentence-transformers`

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

**RAG dependencies missing**:
```bash
# Install optional dependencies
docker-compose exec backend pip install langchain langchain-community langchain-chroma chromadb sentence-transformers
# Or rebuild container with updated requirements.txt
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

## CommandCenter Hub (Multi-Project Management)

### Architecture

The Hub uses **Dagger SDK** for container orchestration, eliminating the need to clone CommandCenter into each project folder. Key benefits:

- **No template cloning**: Projects stay clean, CommandCenter stack defined once
- **Type-safe orchestration**: Python SDK with full type hints and IDE support
- **Better error handling**: SDK exceptions instead of subprocess stderr parsing
- **Programmatic control**: Async/await API for container lifecycle management
- **Intelligent caching**: Dagger automatically caches builds and dependencies

### Hub Structure

```
hub/
├── backend/
│   ├── app/
│   │   ├── dagger_modules/
│   │   │   └── commandcenter.py    # Dagger stack definition
│   │   ├── services/
│   │   │   └── orchestration_service.py  # Dagger orchestration logic
│   │   └── models/
│   │       └── project.py          # Project model (path, ports, status)
│   └── requirements.txt            # Includes dagger-io SDK
└── frontend/
    └── src/
        └── components/
            └── ProjectCard.tsx     # Start/stop projects
```

### Key Concepts

**CommandCenterStack** (`hub/backend/app/dagger_modules/commandcenter.py`):
- Defines complete CommandCenter infrastructure as Python code
- Builds postgres, redis, backend, frontend containers
- Mounts project folder as `/workspace` in containers
- No docker-compose.yml files needed

**CommandCenterConfig**:
- Configuration dataclass: project_name, project_path, ports, secrets
- Passed to CommandCenterStack for per-project instantiation
- Secrets auto-generated at runtime (not stored in database)

**OrchestrationService** (`hub/backend/app/services/orchestration_service.py`):
- Bridges Hub database with Dagger stack management
- Maintains `_active_stacks` registry (project_id → CommandCenterStack)
- Handles port conflict detection, lifecycle management

### Dagger vs docker-compose

| Aspect | docker-compose | Dagger SDK |
|--------|----------------|------------|
| Configuration | YAML files | Python code |
| Type Safety | None | Full type hints |
| Error Handling | Parse stderr | Python exceptions |
| Template Mgmt | Clone files | No templates needed |
| IDE Support | YAML linting | Full autocomplete |

### Hub Commands

```bash
# Start Hub backend
cd hub/backend
pip install -r requirements.txt
export DATABASE_URL="sqlite+aiosqlite:///./data/hub.db"
uvicorn app.main:app --reload --port 9001

# Start Hub frontend
cd hub/frontend
npm install
npm run dev  # Port 9000

# Run Hub tests
cd hub/backend
pytest tests/ -v
```

## Additional Resources

- **Makefile**: Run `make help` to see all available commands
- **Documentation**:
  - `docs/DATA_ISOLATION.md` - Multi-instance security (READ FIRST)
  - `docs/DAGGER_ARCHITECTURE.md` - How Dagger orchestration works (Hub-specific)
  - `docs/DOCLING_SETUP.md` - RAG document processing
  - `docs/CONFIGURATION.md` - Environment configuration
  - `docs/PORT_MANAGEMENT.md` - Handling port conflicts
  - `docs/TRAEFIK_SETUP.md` - Zero-conflict deployment
  - `HUB_DESIGN.md` - Hub architecture and design
- **Backend README**: `backend/README.md`
- **Frontend README**: `frontend/README.md`
