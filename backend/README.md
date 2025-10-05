# Command Center Backend

Production-ready FastAPI backend for Performia Command Center - Research and Development management system.

## Architecture

### Tech Stack
- **Framework**: FastAPI 0.109.0 (async Python web framework)
- **Database**: SQLAlchemy 2.0.25 (async ORM) + Alembic 1.13.1 (migrations)
- **Validation**: Pydantic 2.5.3 (schemas and settings)
- **GitHub**: PyGithub 2.1.1 (API integration)
- **RAG**: LangChain + ChromaDB (optional, for knowledge base)

### Database Models

1. **Repository** - GitHub repository tracking
   - Metadata: owner, name, description, access token
   - Sync data: last commit SHA, message, author, date
   - Stats: stars, forks, language

2. **Technology** - R&D technology tracking
   - Classification: domain, status, priority, relevance score
   - Documentation: description, notes, use cases, URLs
   - Tags: comma-separated for filtering

3. **ResearchTask** - Task management
   - Links: technology_id, repository_id (optional)
   - Progress: status, percentage, hours (estimated/actual)
   - Artifacts: uploaded documents, user notes, findings

4. **KnowledgeEntry** - RAG knowledge base
   - Content: title, content, category
   - Source: file, URL, type (pdf/html/manual)
   - Vector DB: reference to ChromaDB entry

### API Endpoints

#### Core Resources
- `GET /health` - Health check
- `GET /` - API information

#### Repositories (`/api/v1/repositories`)
- `GET /` - List all repositories (paginated)
- `POST /` - Create repository
- `GET /{id}` - Get repository details
- `PATCH /{id}` - Update repository
- `DELETE /{id}` - Delete repository
- `POST /{id}/sync` - Sync with GitHub

#### Technologies (`/api/v1/technologies`)
- `GET /` - List technologies (filterable by domain/status, searchable, paginated)
- `POST /` - Create technology
- `GET /{id}` - Get technology details
- `PATCH /{id}` - Update technology
- `DELETE /{id}` - Delete technology

#### Dashboard (`/api/v1/dashboard`)
- `GET /stats` - Aggregate statistics (repos, techs, tasks, knowledge base)
- `GET /recent-activity` - Recent updates across all resources

## Setup

### Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production (Docker)

```bash
# Build image
docker build -t command-center-backend .

# Run container
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@host/db" \
  -e GITHUB_TOKEN="your_token" \
  --name command-center \
  command-center-backend
```

## Configuration

Configuration via environment variables (or `.env` file):

```bash
# Application
APP_NAME="Command Center API"
DEBUG=false

# Database
DATABASE_URL="sqlite+aiosqlite:///./commandcenter.db"  # Dev
# DATABASE_URL="postgresql+asyncpg://user:pass@host/db"  # Prod

# PostgreSQL (alternative to DATABASE_URL)
POSTGRES_USER=ccuser
POSTGRES_PASSWORD=secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=commandcenter

# GitHub Integration
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
GITHUB_DEFAULT_ORG=performia

# Knowledge Base (RAG)
KNOWLEDGE_BASE_PATH=./docs/knowledge-base/chromadb
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Security
SECRET_KEY=change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

## Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# View history
alembic history
```

## Testing

```bash
# Run API tests
python test_api.py

# Expected output: All 10 endpoint tests pass
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Services

### GitHubService
Async GitHub API integration:
- `authenticate_repo()` - Test repository access
- `list_user_repos()` - List user's repositories
- `sync_repository()` - Sync repo metadata and detect changes
- `search_repositories()` - Search GitHub

### RAGService (Optional)
Knowledge base operations:
- `query()` - Semantic search
- `add_document()` - Add document chunks
- `get_statistics()` - KB stats
- `process_directory()` - Batch process docs

**Note**: RAG dependencies are optional. Install with:
```bash
pip install langchain langchain-community langchain-chroma chromadb sentence-transformers
```

## Project Structure

```
commandcenter/backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── database.py          # SQLAlchemy setup
│   ├── models/              # Database models
│   │   ├── repository.py
│   │   ├── technology.py
│   │   ├── research_task.py
│   │   └── knowledge_entry.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── repository.py
│   │   ├── technology.py
│   │   └── research.py
│   ├── routers/             # API endpoints
│   │   ├── repositories.py
│   │   ├── technologies.py
│   │   └── dashboard.py
│   └── services/            # Business logic
│       ├── github_service.py
│       └── rag_service.py
├── alembic/                 # Database migrations
│   ├── env.py
│   └── versions/
├── Dockerfile
├── requirements.txt
└── test_api.py
```

## Production Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Use PostgreSQL for production database
- [ ] Set `DEBUG=false`
- [ ] Configure proper CORS origins
- [ ] Add GitHub token for repository sync
- [ ] Set up knowledge base path
- [ ] Configure monitoring/logging
- [ ] Enable HTTPS
- [ ] Set up database backups
- [ ] Review security settings

## License

Part of Performia project - see main repository LICENSE file.
