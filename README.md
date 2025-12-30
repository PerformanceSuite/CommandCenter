# CommandCenter

**Your Personal AI Operating System for Knowledge Work**

An intelligent layer between you and all your tools—active intelligence that learns YOUR patterns and unifies your ecosystem (GitHub, Notion, Slack, Obsidian, Zotero, Linear, ArXiv, YouTube, Browser) with privacy-first architecture.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)

---

## 🚀 Quick Start

```bash
# Setup
make setup                    # Creates .env from template
make start                    # Start all services

# Development
make dev                      # Start in dev mode with live reload
make logs                     # View all logs
make test                     # Run all tests

# Database
make migrate                  # Apply migrations
make shell-db                 # PostgreSQL shell
```

**Access Points:**
- Frontend: http://localhost:3000
- AI Arena: http://localhost:3000/arena
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Hub (Multi-Project): http://localhost:9000

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Development Roadmap](#development-roadmap)
- [Current Status](#current-status)
- [Getting Started](#getting-started)
- [Documentation](#documentation)
- [Contributing](#contributing)

---

## 🎯 Overview

CommandCenter is a multi-project R&D management and knowledge base system that:

- **Tracks Technologies**: Tech radar with domain/vendor/status tracking
- **Manages Research**: Task management linked to repositories and technologies
- **RAG-Powered Search**: Vector search across GitHub repositories using KnowledgeBeast v3.0
- **Multi-Project Orchestration**: CommandCenter Hub for managing isolated instances via Dagger SDK
- **Event-Driven Architecture**: NATS-based event streaming with correlation tracking
- **Observability**: Comprehensive monitoring with Prometheus, Grafana, and custom dashboards

### Key Features

✅ **AI Arena**: Multi-model hypothesis validation with AI debates (Claude, GPT-4, Gemini)
✅ **GitHub Integration**: Sync repositories, track commits, manage access tokens
✅ **Knowledge Base**: Hybrid vector + keyword search with PostgreSQL + pgvector
✅ **LLM Gateway**: Multi-provider abstraction with dynamic configuration and cost tracking
✅ **Privacy-First**: Data isolation, local embeddings, self-hosted infrastructure
✅ **Production-Ready**: Full observability, health checks, automated testing
✅ **Type-Safe Orchestration**: Dagger SDK for container management (no docker-compose)
✅ **Event Streaming**: Real-time event correlation and query capabilities

---

## 🏗️ Architecture

### Core Stack

- **Backend**: Python 3.11 + FastAPI + SQLAlchemy
- **Frontend**: React 18 + TypeScript + Vite
- **Database**: PostgreSQL 16 + pgvector
- **Cache**: Redis
- **Message Bus**: NATS with JetStream
- **Orchestration**: Dagger SDK (Python)
- **Monitoring**: Prometheus + Grafana
- **Task Queue**: Celery

### Service Layer

```
app/
├── routers/      # FastAPI endpoints (HTTP interface)
├── services/     # Business logic (GitHubService, RAGService, EventService)
├── models/       # SQLAlchemy ORM (database tables)
└── schemas/      # Pydantic models (request/response validation)
```

**Pattern**: Routers → Services → Models → Schemas

### Data Isolation

**Critical**: Each project requires its own isolated CommandCenter instance.

- Unique `COMPOSE_PROJECT_NAME` in `.env`
- Separate Docker volumes per project
- Independent secrets and ports
- See [CLAUDE.md](docs/CLAUDE.md#data-isolation-multi-instance) for details

---

## 🗺️ Development Roadmap

### Comprehensive Phases 1-12 (32 Weeks)

**Vision**: Transform CommandCenter into a self-healing, AI-driven mesh with federated instances, real-time visualization, agent orchestration, and predictive intelligence.

📖 **[Full Roadmap Document](docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md)** (2,880 lines)

#### Foundation & Events (Weeks 1-8)
- **[Phase 1](docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md#phase-1-event-system-bootstrap-week-1)**: Event System Bootstrap ✅ **COMPLETE**
- **[Phase 2-3](docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md#phase-2-3-event-streaming--correlation-weeks-2-3)**: Event Streaming & Correlation ✅ **COMPLETE**
- **[Phase 4](docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md#phase-4-nats-bridge-week-4)**: NATS Bridge (Week 4)
- **[Phase 5](docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md#phase-5-federation-prep-week-5)**: Federation Prep (Week 5)
- **[Phase 6](docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md#phase-6-health--service-discovery-weeks-6-8)**: Health & Service Discovery (Weeks 6-8)

#### Graph & Visualization (Weeks 9-16)
- **[Phase 7](docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md#phase-7-graph-service-implementation-weeks-9-12)**: Graph-Service Implementation ([Blueprint](hub-prototype/phase_7_8_graph_service_vislzr_integration_plan_command_center.md))
- **[Phase 8](docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md#phase-8-vislzr-frontend-weeks-13-16)**: VISLZR Frontend ([Blueprint](hub-prototype/phase_7_8_graph_service_vislzr_integration_plan_command_center.md))

#### Intelligence & Automation (Weeks 17-27)
- **[Phase 9](docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md#phase-9-federation--cross-project-intelligence-weeks-17-20)**: Federation & Ecosystem Mode ([Blueprint](hub-prototype/phase_9_federation_ecosystem_mode_implementation_blueprint.md))
- **[Phase 10](docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md#phase-10-agent-orchestration--workflow-automation-weeks-21-24)**: Agent Orchestration & Workflows ([Blueprint](hub-prototype/phase_10_agent_orchestration_workflow_automation_blueprint.md))
- **[Phase 11](docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md#phase-11-compliance-security--partner-interfaces-weeks-25-27)**: Compliance & Security ([Blueprint](hub-prototype/phase_11_compliance_security_partner_interfaces_blueprint.md))

#### Autonomous Systems (Weeks 28-32)
- **[Phase 12](docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md#phase-12-autonomous-mesh--predictive-intelligence-weeks-28-32)**: Autonomous Mesh & Predictive Intelligence ([Blueprint](hub-prototype/phase_12_autonomous_mesh_predictive_intelligence_blueprint.md))

**Architecture**: Hybrid Modular Monolith with NATS event bus
**Timeline**: 8 months from foundation to full autonomy

---

## 📊 Current Status

**Phase**: Active Development - AI Arena & Settings Complete ✅
**Infrastructure**: 95% Complete
**Testing**: 1,700+ tests passing

### Recent Releases (December 2025)

✅ **AI Arena** - Multi-model hypothesis validation
- Hypothesis CRUD with quick input
- Multi-agent debate system (Analyst, Researcher, Strategist, Critic)
- Chairman synthesis for consensus
- Evidence exploration and cost tracking
- Moved to main frontend at `/arena` route

✅ **Settings & Provider Management**
- Dynamic provider configuration (Anthropic, OpenAI, Google, Z.AI)
- Model selection with LiteLLM registry (live pricing)
- Encrypted API key storage
- Two-dropdown provider/model UI

✅ **LLM Gateway Enhancements**
- Dynamic provider registry with DB support
- Cost statistics and aggregated metrics
- Per-instance caching for performance

### Completed Phases

✅ **Phase A**: Dagger Production Hardening (PR #74) - PRODUCTION-READY
✅ **Phase B**: Automated Knowledge Ingestion (PR #63) - MERGED
✅ **Phase C**: Observability Layer (PR #73) - PRODUCTION
✅ **Phase 1**: Event System Bootstrap - COMPLETE
✅ **Phase 2-3**: Event Streaming & Correlation - COMPLETE

### Active Components

- **AI Arena**: Hypothesis validation ✅
- **LLM Gateway**: Multi-provider with cost tracking ✅
- **Settings Service**: Provider/model configuration ✅
- **Celery Task System**: Production-ready ✅
- **RAG Backend**: KnowledgeBeast v3.0 ✅
- **Knowledge Ingestion**: Complete ✅
- **Observability Layer**: Production ✅
- **Dagger Orchestration**: Production-ready ✅
- **Event System**: Complete ✅

### Quality Metrics

- **ESLint**: 0 errors ✅
- **Frontend Tests**: Passing ✅
- **Backend Tests**: 1,700+ tests passing ✅
- **Pre-commit Hooks**: All passing (black, isort, flake8, mypy) ✅

---

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)
- Make

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/CommandCenter.git
   cd CommandCenter
   ```

2. **Initial setup**
   ```bash
   make setup                    # Creates .env from template
   # Edit .env and set required values:
   # - COMPOSE_PROJECT_NAME (must be unique)
   # - SECRET_KEY (generate with: openssl rand -hex 32)
   # - DB_PASSWORD (strong password)
   # - GITHUB_TOKEN (optional, for repo syncing)
   ```

3. **Start services**
   ```bash
   make start                    # Start all services
   make logs                     # View logs to verify startup
   make health                   # Check service health
   ```

4. **Apply database migrations**
   ```bash
   make migrate
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Grafana: http://localhost:3001

### Development Workflow

```bash
# Start development environment
make dev                      # Live reload enabled

# Run tests
make test                     # All tests
make test-backend             # Backend only
make test-frontend            # Frontend only

# Code quality
make lint                     # Run linters
make format                   # Auto-format code

# Database operations
make shell-db                 # PostgreSQL shell
make migrate                  # Apply migrations
make migrate-create MESSAGE="description"  # Create migration

# Shell access
make shell-backend            # Backend container bash
make shell-frontend           # Frontend container shell

# Cleanup
make stop                     # Stop services
make clean                    # Remove volumes (CAUTION: deletes data)
```

### CommandCenter Hub (Multi-Project)

The Hub manages multiple CommandCenter instances using Dagger SDK:

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
```

**Hub Features**:
- Type-safe container orchestration with Dagger
- No template cloning needed
- Programmatic project lifecycle management
- Port conflict detection
- Health monitoring

See [HUB_DESIGN.md](docs/HUB_DESIGN.md) for architecture details.

---

## 📚 Documentation

### Core Documentation

- **[CLAUDE.md](docs/CLAUDE.md)** - Complete development guide (commands, architecture, patterns)
- **[PROJECT.md](docs/PROJECT.md)** - Project status and tracking
- **[DAGGER_ARCHITECTURE.md](docs/DAGGER_ARCHITECTURE.md)** - Hub orchestration architecture
- **[HUB_DESIGN.md](docs/HUB_DESIGN.md)** - Hub architecture and Dagger integration

### Phase Documentation

- **[Comprehensive Roadmap](docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md)** - Full 32-week plan (2,880 lines)
- **[EVENT_SYSTEM.md](hub/docs/EVENT_SYSTEM.md)** - Event infrastructure documentation (Phase 1-3)
- **[Phase A Status](docs/PHASE_A_STATUS.md)** - Dagger production hardening
- **[Phase C Readiness](docs/phase-c-readiness.md)** - Observability layer details

### Phase Blueprints

- **[Phase 7-8 Blueprint](hub-prototype/phase_7_8_graph_service_vislzr_integration_plan_command_center.md)** - Graph Service & VISLZR
- **[Phase 9 Blueprint](hub-prototype/phase_9_federation_ecosystem_mode_implementation_blueprint.md)** - Federation & Ecosystem Mode
- **[Phase 10 Blueprint](hub-prototype/phase_10_agent_orchestration_workflow_automation_blueprint.md)** - Agent Orchestration
- **[Phase 11 Blueprint](hub-prototype/phase_11_compliance_security_partner_interfaces_blueprint.md)** - Compliance & Security
- **[Phase 12 Blueprint](hub-prototype/phase_12_autonomous_mesh_predictive_intelligence_blueprint.md)** - Autonomous Mesh

### Feature Documentation

- **[CONFIGURATION.md](docs/CONFIGURATION.md)** - Environment configuration
- **[PORT_MANAGEMENT.md](docs/PORT_MANAGEMENT.md)** - Handling port conflicts
- **[TRAEFIK_SETUP.md](docs/TRAEFIK_SETUP.md)** - Zero-conflict deployment
- **[DOCLING_SETUP.md](docs/DOCLING_SETUP.md)** - RAG document processing

### Component READMEs

- [Backend README](backend/README.md) - Backend architecture and API
- [Frontend README](frontend/README.md) - Frontend components and structure
- [Hub Design](docs/HUB_DESIGN.md) - Hub architecture and Dagger integration

---

## 🔧 Configuration

### Environment Variables

**Required**:
```bash
COMPOSE_PROJECT_NAME=yourproject-commandcenter  # MUST be unique
SECRET_KEY=<generate-with-openssl-rand-hex-32>
DB_PASSWORD=<strong-password>
```

**Optional**:
```bash
# GitHub Integration
GITHUB_TOKEN=ghp_...          # Personal access token

# AI APIs
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Ports (customize for multiple instances)
BACKEND_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432
REDIS_PORT=6379
```

### Database Setup

The RAG service requires PostgreSQL with pgvector extension:

```bash
# Build custom Postgres image (automatic on first run)
docker-compose build postgres

# Or use Dagger
cd backend
python scripts/build-postgres.py

# Verify pgvector
docker-compose exec postgres psql -U commandcenter -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

---

## 🧪 Testing

```bash
# All tests
make test

# Individual suites
make test-backend             # pytest (1,676 tests)
make test-frontend            # npm test (12 tests)

# Coverage
cd backend && pytest --cov=app --cov-report=html

# Run specific test file
docker-compose exec backend pytest tests/test_events.py -v
```

### Test Structure

```
backend/tests/
├── unit/                     # Unit tests (services, utilities)
├── integration/              # Integration tests (database, APIs)
└── fixtures/                 # Shared test fixtures

frontend/src/
└── **/*.test.tsx             # Component tests
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`make test && make lint`)
5. Commit with pre-commit hooks (`git commit -m 'Add amazing feature'`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Standards

- **Code Style**: Black (Python), ESLint + Prettier (TypeScript)
- **Type Hints**: Required for all Python functions
- **Tests**: Required for new features
- **Documentation**: Update relevant docs for changes
- **Pre-commit Hooks**: Must pass before commit

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- **KnowledgeBeast**: RAG backend engine (vendored in `libs/knowledgebeast/`)
- **Dagger**: Type-safe container orchestration SDK
- **FastAPI**: High-performance Python web framework
- **React**: UI component framework
- **PostgreSQL + pgvector**: Vector database for semantic search
- **NATS**: Cloud-native messaging system

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/CommandCenter/issues)
- **Documentation**: [docs/](docs/)
- **API Docs**: http://localhost:8000/docs (when running)

---

**Built with ❤️ for knowledge workers who demand privacy, power, and control.**
