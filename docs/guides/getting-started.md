# Getting Started

## Prerequisites

- Docker and Docker Compose
- Node.js 18+
- Python 3.11+
- PostgreSQL with pgvector (or use Docker)

## Quick Start

```bash
# Clone
git clone https://github.com/PerformanceSuite/CommandCenter.git
cd CommandCenter

# Environment
cp .env.example .env
# Edit .env with your API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)

# Start everything
make start

# Or manually:
docker-compose up -d          # Infrastructure (postgres, redis, nats)
cd backend && make run        # Backend API on :8000
cd frontend && npm run dev    # Main frontend on :3000
cd hub/frontend && npm run dev # Hub frontend on :9000
```

## Verify Installation

```bash
# Health check
curl http://localhost:8000/api/v1/health

# API docs
open http://localhost:8000/docs

# Main UI
open http://localhost:3000

# Hub UI
open http://localhost:9000
```

## First Steps

1. **Configure Providers**: Go to Hub → Settings → Add your API keys
2. **Create a Hypothesis**: Go to AI Arena → Create hypothesis → Run validation
3. **Search Knowledge**: Go to Knowledge Base → Search for something

## Project Structure

```
CommandCenter/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── routers/  # API endpoints
│   │   ├── services/ # Business logic
│   │   ├── models/   # SQLAlchemy models
│   │   └── libs/     # AI Arena, LLM Gateway
│   └── tests/
├── frontend/          # Main React frontend
├── hub/
│   ├── backend/      # Hub orchestration
│   └── frontend/     # Hub React frontend
├── docs/             # This documentation
└── tools/            # CLI tools, agent sandboxes
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection |
| `REDIS_URL` | Yes | Redis connection |
| `ANTHROPIC_API_KEY` | Yes | Claude API |
| `OPENAI_API_KEY` | No | GPT-4 API |
| `GOOGLE_API_KEY` | No | Gemini API |
| `NATS_URL` | No | NATS server (default: localhost:4222) |

## Common Commands

```bash
# Development
make start              # Start all services
make stop               # Stop all services
make logs               # View logs
make test               # Run tests

# Database
make migrate            # Run migrations
make shell-db           # Database shell

# Backend
cd backend
make run                # Run with reload
make test               # Run backend tests

# Frontend
cd frontend
npm run dev             # Dev server
npm run build           # Production build
npm run test            # Run tests
```

## Next Steps

- Read the [Architecture](../architecture.md) to understand how pieces connect
- Explore [Modules](../modules/) to see what's available
- Check the [Roadmap](../roadmap.md) for what's coming
