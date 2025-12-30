# CommandCenter - Agent Instructions

> AI assistant instructions for working with this codebase.

## Project Overview

**CommandCenter** is a multi-project R&D management platform with AI-powered hypothesis validation. It combines:

- **Knowledge Management**: RAG-powered search across GitHub repos using KnowledgeBeast + pgvector
- **AI Arena**: Multi-model debate system for hypothesis validation (Claude, GPT-4, Gemini)
- **Project Orchestration**: Hub for managing multiple CommandCenter instances via Dagger SDK
- **Event-Driven Architecture**: NATS JetStream for real-time event streaming

**Status**: Active Development | **Tests**: 1,700+ passing

## Architecture

```
├── backend/                 # FastAPI + SQLAlchemy (port 8000)
│   ├── app/
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── models/         # SQLAlchemy ORM
│   │   └── schemas/        # Pydantic validation
│   └── libs/
│       ├── ai_arena/       # Multi-agent debate library
│       ├── llm_gateway/    # Multi-provider LLM abstraction
│       └── knowledgebeast/ # RAG engine
├── frontend/               # React + TypeScript + Vite (port 3000)
│   └── src/components/
│       ├── AIArena/        # Hypothesis validation UI
│       ├── Dashboard/      # Main dashboard
│       ├── KnowledgeBase/  # RAG search interface
│       └── TechnologyRadar/# Tech radar visualization
└── hub/                    # Multi-project orchestration (port 9000)
    ├── backend/            # FastAPI + SQLite + Dagger SDK
    └── frontend/           # React + TypeScript
```

## Key Features

### AI Arena (Hypothesis Validation)
- **Location**: `frontend/src/components/AIArena/`, `backend/app/routers/hypotheses.py`
- **Route**: `/arena` in main frontend
- Multi-model debates with Analyst, Researcher, Strategist, Critic agents
- Chairman synthesis for consensus building
- Evidence exploration and validation tracking

### Settings & Provider Management
- **Location**: `backend/app/routers/settings.py`, `backend/app/services/settings_service.py`
- Dynamic provider configuration (Anthropic, OpenAI, Google, Z.AI)
- Model selection with live pricing from LiteLLM registry
- Encrypted API key storage

### LLM Gateway
- **Location**: `backend/libs/llm_gateway/`
- Multi-provider support: Claude, GPT-4, Gemini, Grok, local models
- Dynamic provider registry with database backend
- Cost tracking with per-request metrics
- Prometheus metrics export

### Knowledge Base (RAG)
- **Location**: `backend/libs/knowledgebeast/`, `backend/app/services/rag_service.py`
- PostgreSQL + pgvector for vector search
- HuggingFace embeddings (local, no API costs)
- Hybrid search: vector similarity + keyword search

## Commands

```bash
# Development
make dev                    # Start with live reload
make start                  # Start all services
make stop                   # Stop services
make logs                   # View logs

# Testing
make test                   # All tests
make test-backend           # Backend only (pytest)
make test-frontend          # Frontend only

# Database
make migrate                # Apply migrations
make shell-db               # PostgreSQL shell

# Hub (Multi-Project)
cd hub && docker-compose up # Start Hub services
```

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Main React app |
| Backend API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Hub | http://localhost:9000 | Project orchestration |
| Hub API | http://localhost:9002 | Hub backend |

## Code Patterns

### Service Layer
```
Router (HTTP) → Service (Logic) → Model (ORM) → Schema (Validation)
```

### Key Services
- `GitHubService`: Repository sync, commit tracking
- `SettingsService`: Provider/model configuration
- `HypothesisService`: AI Arena validation orchestration
- `KnowledgeBeastService`: RAG queries

### API Conventions
- All endpoints under `/api/v1/`
- Pagination: `skip` and `limit` parameters
- Errors return `{"detail": "message"}`

## Recent Changes (Dec 2025)

1. **AI Arena moved to main frontend** - `/arena` route with full validation UI
2. **Dynamic provider registry** - Database-backed LLM configuration
3. **Settings dashboard** - Provider/model selection with two-dropdown UI
4. **Hypothesis quick input** - Simplified hypothesis creation
5. **Cost statistics** - Aggregated LLM usage tracking

## Important Files

| File | Purpose |
|------|---------|
| `docs/CAPABILITIES.md` | Feature audit and status |
| `docs/CLAUDE.md` | Extended Claude Code instructions |
| `backend/app/routers/` | All API endpoints |
| `backend/libs/` | Core libraries (AI Arena, LLM Gateway, RAG) |
| `frontend/src/App.tsx` | Frontend routing |

## Notes for AI Assistants

- Check `docs/CAPABILITIES.md` for current feature status
- The Hub and main app are separate deployments
- AI Arena uses the main backend API, not the Hub
- Settings/providers are configured in main backend, not Hub
- Commit with meaningful messages, ask before large refactors
- Prefer simple solutions over clever ones
