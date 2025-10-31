# Command Center

**Next-Generation R&D Management & AI-Powered Knowledge Base**

Command Center is a production-grade platform for managing research and development workflows, tracking emerging technologies, and building intelligent knowledge bases. It combines automated knowledge ingestion, RAG-powered search, and multi-repository tracking to give R&D teams superhuman research capabilities.

[![Tests](https://github.com/PerformanceSuite/CommandCenter/workflows/CI/badge.svg)](https://github.com/PerformanceSuite/CommandCenter/actions)
[![codecov](https://codecov.io/gh/PerformanceSuite/CommandCenter/branch/main/graph/badge.svg)](https://codecov.io/gh/PerformanceSuite/CommandCenter)

---

## 🎯 Vision: What CommandCenter Intends to Be

CommandCenter is being built to become the **operating system for R&D teams** - a unified platform that automates the tedious parts of research while amplifying human insight with AI.

### The Problem We're Solving

Modern R&D teams face an **information overload crisis**:
- Technologies evolve faster than humans can track them
- Research is scattered across repos, docs, papers, and conversations
- Knowledge silos prevent teams from building on past work
- Manual research processes don't scale
- Context switching between tools kills productivity

### Our Solution: Automated Research Intelligence

CommandCenter automates the entire research workflow:

```
Automated Ingestion → Intelligent Processing → AI-Powered Insights
      ↓                      ↓                        ↓
  RSS/Webhooks/Files    RAG Embeddings          Natural Language Query
  GitHub/Docs/Papers    Vector Search           Context-Aware Answers
  Scheduled Scrapers    Knowledge Graph         Research Assistance
```

**Phase 1 (Complete)**: Foundation - Technology tracking, research management, manual knowledge entry
**Phase 2 (Current)**: Automation - Automated ingestion from multiple sources, scheduled updates, real-time webhooks
**Phase 3 (Next)**: Intelligence - Observability, analytics, predictive insights, proactive recommendations
**Phase 4 (Future)**: Ecosystem - Multi-tool integration, Habit Coach AI, collaborative workflows

---

## ✨ Current Capabilities

### 🧠 AI-Powered Knowledge Base
- **Natural Language Search**: Ask questions in plain English, get AI-powered answers from your research
- **RAG Architecture**: Retrieval Augmented Generation using KnowledgeBeast v3.0 with PostgreSQL + pgvector
- **Hybrid Search**: Combines vector similarity with keyword search for optimal results
- **Automated Ingestion** (Phase B - Complete):
  - RSS feed monitoring with scheduled updates
  - Webhook receivers for real-time documentation changes
  - File system watchers for local document changes
  - Documentation scrapers with SSRF protection
  - Source prioritization and deduplication
- **Document Processing**: Uses Docling for PDF, Markdown, HTML, and code extraction
- **Multi-Tenant**: Isolated knowledge bases per project with collection prefixes

### 📊 Technology Radar
- **Domain Tracking**: Monitor technologies across AI/ML, Audio, Cloud, DevOps, and custom domains
- **Maturity Lifecycle**: Track technologies from Discovery → Assessment → Trial → Adopt → Hold
- **Relevance Scoring**: High/Medium/Low relevance ratings with justifications
- **Relationship Mapping**: Link technologies to repositories, research tasks, and knowledge entries
- **Visual Radar**: Interactive visualization inspired by ThoughtWorks Technology Radar
- **Change Tracking**: Audit trail of all technology updates and transitions

### 🔬 Research Management
- **Task Organization**: Create, track, and manage research tasks with rich metadata
- **Status Workflows**: Planning → In Progress → Completed → Archived
- **Priority Management**: Critical → High → Medium → Low with smart sorting
- **Technology Linking**: Associate research with specific technologies and repos
- **Tag System**: Flexible categorization and filtering
- **Notes & Documentation**: Rich text descriptions with Markdown support

### 📦 Multi-Repository Tracking
- **Unlimited Repos**: Track any number of GitHub repositories
- **Automatic Syncing**: Scheduled commit tracking and metadata updates
- **Secure Access**: Per-repository access tokens with AES-256 encryption
- **Technology Detection**: Automatic identification of technologies in codebases
- **Activity Monitoring**: Track commits, contributors, and repository health
- **Cross-Project Insights**: Analyze patterns across all tracked repositories

### 🔐 Enterprise-Grade Security
- **Data Isolation**: Each project requires its own CommandCenter instance (never share instances)
- **Token Encryption**: All GitHub tokens encrypted at rest with AES-256
- **SSRF Protection**: Comprehensive protection against Server-Side Request Forgery in scrapers
- **Input Validation**: Pydantic schemas with strict validation on all API endpoints
- **Rate Limiting**: Prevent abuse with configurable request limits
- **SQL Injection Prevention**: SQLAlchemy 2.0 with parameterized queries
- **XSS Protection**: Content Security Policy and output sanitization

### ⚙️ Production Infrastructure (Phase B Complete)

#### Automated Knowledge Ingestion System ✅
- **Celery Task Queue**: Robust async task processing with retry logic and error handling
- **Multiple Ingestion Sources**:
  - RSS feed scraper with OPML import support
  - Documentation scraper with URL validation and SSRF protection
  - Webhook receivers (GitHub, generic HTTP)
  - File system watchers with debouncing and path validation
- **Scheduled Updates**: Cron-based scheduling with `croniter` validation
- **Source Management**: CRUD APIs for managing ingestion sources
- **Error Handling**: Comprehensive error tracking, transaction rollback, and retry mechanisms
- **Security Hardening**:
  - Memory leak prevention in file watchers
  - Timezone-aware datetime handling
  - Cron expression validation
  - File size limits and path sanitization

#### KnowledgeBeast RAG Engine ✅
- **PostgreSQL Backend**: Production-grade vector storage with pgvector extension
- **HuggingFace Embeddings**: Local sentence-transformers (no API costs)
- **Hybrid Search**: Vector similarity + keyword search with Reciprocal Rank Fusion
- **Collection Management**: Multi-tenant with project-based isolation
- **Monorepo Architecture**: Vendored in `libs/knowledgebeast/` for tight integration

#### Container Orchestration (Partial - Phase A) 🟡
- **Dagger SDK**: Type-safe Python-based container orchestration
- **Docker Compose**: Development and single-instance deployments
- **Hub Management**: Multi-project instance management via CommandCenter Hub
- **In Progress**: Production hardening (health checks, resource limits, logging)

---

## 🚀 Getting Started

### ⚠️ CRITICAL: Data Isolation Principle

**Each project MUST have its own CommandCenter instance. Never share instances.**

CommandCenter stores:
- Encrypted GitHub access tokens
- Proprietary research and knowledge
- RAG embeddings of sensitive documents
- Project-specific configurations

Sharing instances creates security vulnerabilities and data leakage risks. See [Data Isolation Guide](./docs/DATA_ISOLATION.md) for architecture details.

### Prerequisites

- **Docker** & **Docker Compose** 20.10+
- **Python** 3.11+ (for local development)
- **Node.js** 18+ (for frontend development)
- **PostgreSQL** 16+ with pgvector extension (handled by Docker)
- **GitHub Account** (optional, for repository tracking)
- **OpenAI or Anthropic API Key** (optional, for enhanced RAG features)

### Quick Start (5 minutes)

1. **Clone into project-specific directory:**
   ```bash
   # Clone into your project's directory for isolation
   cd ~/projects/your-project/
   git clone https://github.com/PerformanceSuite/CommandCenter.git commandcenter
   cd commandcenter
   ```

2. **Configure environment:**
   ```bash
   make setup  # Creates .env from template

   # Edit .env with your settings
   # CRITICAL: Set unique project name for data isolation
   vim .env
   ```

   **Minimum required configuration:**
   ```bash
   COMPOSE_PROJECT_NAME=yourproject-commandcenter  # MUST be unique
   SECRET_KEY=$(openssl rand -hex 32)              # Generate secure key
   DB_PASSWORD=$(openssl rand -hex 16)             # Strong password
   ```

3. **Start services:**
   ```bash
   make start  # Handles port checks automatically

   # Or manually:
   ./scripts/check-ports.sh  # Check for conflicts
   docker-compose up -d
   ```

4. **Verify installation:**
   ```bash
   make health  # Check all services
   ```

5. **Access the application:**
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs
   - **Grafana** (future): http://localhost:3001

### First Steps

1. **Add a repository**: Settings → Repository Manager → Add Repository
2. **Create technologies**: Dashboard → Technology Radar → Add Technology
3. **Set up ingestion sources**: Knowledge Base → Sources → Add Source (RSS, Webhook, File Watcher)
4. **Start research**: Research Hub → New Task
5. **Query knowledge**: Knowledge Base → Ask questions in natural language

---

## 🏗️ Architecture & Tech Stack

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React 18 + TypeScript)          │
│  Dashboard │ Tech Radar │ Research │ Knowledge Base │ Sources│
└────────────────────┬────────────────────────────────────────┘
                     │ REST API (FastAPI)
┌────────────────────▼────────────────────────────────────────┐
│              Backend Application Layer                        │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │  Repos   │  Tech    │ Research │   RAG    │ Ingestion│  │
│  │ Service  │ Service  │ Service  │ Service  │ Service  │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Task Processing Layer (Celery)                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ RSS Scrapers │ Doc Scrapers │ Webhooks │ Watchers  │    │
│  └─────────────────────────────────────────────────────┘    │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Data & Storage Layer                         │
│  ┌──────────────────────────┬──────────┬─────────────┐      │
│  │ PostgreSQL 16            │  Redis 7 │ pgvector    │      │
│  │ (Relational + Vectors)   │ (Queue)  │ (Embeddings)│      │
│  └──────────────────────────┴──────────┴─────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- **Framework**: Python 3.11, FastAPI, SQLAlchemy 2.0
- **Task Queue**: Celery with Redis broker
- **Database**: PostgreSQL 16 + pgvector extension
- **RAG Engine**: KnowledgeBeast v3.0 (custom, vendored)
- **Embeddings**: sentence-transformers (HuggingFace, local)
- **Document Processing**: Docling 2.5.5+
- **Migrations**: Alembic
- **Security**: cryptography (Fernet), Pydantic validation
- **Testing**: pytest (1,676+ tests), pytest-asyncio, pytest-cov

**Frontend:**
- **Framework**: React 18, TypeScript 5
- **Build Tool**: Vite 5
- **Styling**: Tailwind CSS 3
- **State Management**: TanStack Query (React Query)
- **Charts**: Chart.js, react-chartjs-2
- **HTTP Client**: Axios
- **Testing**: Vitest, Testing Library, Playwright (E2E)

**Infrastructure:**
- **Orchestration**: Docker Compose, Dagger SDK (Python)
- **Container Registry**: Docker Hub
- **CI/CD**: GitHub Actions (multi-stage, sharded)
- **Observability** (planned): Prometheus, Grafana, OpenTelemetry

**Monorepo Libraries:**
- **KnowledgeBeast**: Custom RAG engine in `libs/knowledgebeast/`

---

## 📋 Roadmap: From Foundation to Ecosystem

### ✅ Phase A: Dagger Production Hardening (Complete)
**Duration**: 3 weeks | **Status**: Shipped

- Container orchestration with Dagger SDK
- Type-safe Python API for infrastructure
- Basic health checks and error handling
- Hub management for multi-project instances

### ✅ Phase B: Automated Knowledge Ingestion (Complete - In Review)
**Duration**: 3 weeks | **Status**: PR #63 Open

**Delivered**:
- RSS feed scraper with OPML import and scheduled updates
- Documentation scraper with SSRF protection and URL validation
- Webhook receivers (GitHub, generic HTTP endpoints)
- File system watchers with debouncing and path sanitization
- Source management CRUD APIs with pagination
- 50+ comprehensive tests (100% passing)
- Security hardening (9 critical issues fixed)
- Production-grade error handling and transaction management

**Next**: Awaiting CI/CD validation → Merge to main

### 🚧 Phase C: Observability Layer (Next - 3 weeks)
**Status**: Planned

**Goals**:
- Prometheus metrics for ingestion tasks and RAG queries
- Grafana dashboards for source monitoring and system health
- Distributed tracing with OpenTelemetry for RAG pipeline
- Alerting for failed ingestion tasks and anomalies
- Analytics dashboard for ingestion metrics and usage patterns
- Log aggregation and structured logging
- Performance monitoring and SLO tracking

**Success Criteria**:
- Real-time visibility into all ingestion pipelines
- Proactive alerting before user-facing failures
- Performance regression detection
- Production-ready monitoring stack

### 🔮 Phase D: Ecosystem Integration (Future - 6-8 weeks)
**Status**: Design phase

**Vision**: CommandCenter becomes the hub for your entire research ecosystem

**Planned Integrations**:
- **Slack/Discord**: Real-time research updates, knowledge queries via chatbot
- **Notion/Obsidian**: Bi-directional sync of research notes and knowledge
- **Zotero/Mendeley**: Academic paper tracking and citation management
- **Linear/Jira**: Research task integration with project management
- **ArXiv/PubMed**: Automated paper discovery and ingestion
- **YouTube/Podcast APIs**: Transcript extraction and knowledge base ingestion
- **Browser Extension**: One-click research capture from any webpage

**Architecture**:
- Plugin system for extensible integrations
- Event-driven architecture with message bus
- OAuth2 flows for third-party authentication
- Webhook delivery system for real-time updates

### 🌟 Phase E: Habit Coach AI Assistant (Future - 8-10 weeks)
**Status**: Concept validation

**Vision**: AI-powered research assistant that learns your habits and proactively helps

**Capabilities**:
- **Intelligent Notifications**: "This new AI paper matches your research on audio synthesis"
- **Research Suggestions**: "Based on your work last week, you might want to explore X"
- **Context Switching**: "You haven't updated Technology Radar in 2 weeks - here's what changed"
- **Knowledge Gaps**: "You've tracked these technologies but have no knowledge base entries"
- **Habit Formation**: Learn patterns in your research workflow and optimize them
- **Personalization**: Adapts to your research style, priorities, and communication preferences

**Technical Foundation**:
- Built on Phase B ingestion (data collection)
- Requires Phase C observability (pattern detection)
- Leverages Phase D integrations (delivery channels)
- LLM-powered with vector memory of your research patterns

---

## 🎛️ CommandCenter Hub (Multi-Instance Management)

**Problem**: Running multiple CommandCenter instances (one per project) is complex

**Solution**: CommandCenter Hub - a meta-application for managing multiple instances

### Hub Capabilities

```
┌──────────────────────────────────────────────────────┐
│               CommandCenter Hub (Port 9000)           │
│  ┌────────────────────────────────────────────────┐  │
│  │  Project 1  │  Project 2  │  Project 3         │  │
│  │  ●Running   │  ●Running   │  ○Stopped          │  │
│  └────────────────────────────────────────────────┘  │
└────────────┬─────────────────────────────────────────┘
             │ Dagger SDK (type-safe orchestration)
     ┌───────▼───────┬───────────┬─────────────┐
     │   Instance 1  │ Instance 2│ Instance 3  │
     │  Ports: 8001  │ Ports:8002│ Ports: 8003 │
     │  Data: Vol1   │ Data: Vol2│ Data: Vol3  │
     └───────────────┴───────────┴─────────────┘
```

**Key Features**:
- **No Template Cloning**: Define stack once, instantiate per project
- **Port Management**: Automatic port allocation, zero conflicts
- **Volume Isolation**: Separate Docker volumes per project
- **Health Monitoring**: Real-time status of all instances
- **Logs & Metrics**: Centralized observability across instances
- **One-Click Operations**: Start/stop/restart instances from UI

**Architecture**:
- **Backend**: FastAPI + Dagger SDK (Python)
- **Frontend**: React + TypeScript
- **Database**: SQLite (instance metadata only, not project data)
- **Orchestration**: Dagger SDK replaces docker-compose subprocesses

See [Hub Design Documentation](./docs/HUB_DESIGN.md) for complete architecture.

---

## 🧪 Testing & Quality

CommandCenter maintains **production-grade quality** with comprehensive test coverage.

### Test Statistics

- **1,700+ Total Tests**
  - Backend: 1,676+ tests (unit, integration, security, performance)
  - Frontend: 47 tests (components, hooks, services)
  - E2E: ~40 tests (critical user paths across browsers)
- **Coverage Requirements**:
  - Backend: 80%+ (enforced by CI)
  - Frontend: 60%+ (enforced by CI)
- **CI Runtime**: <25 minutes (parallelized, sharded)

### Test Pyramid

```
           /\
          /E2E\ 10%  - Critical user journeys (Playwright)
         /----\
        / Int \ 15%  - API & database integration tests
       /--------\
      /  Unit   \ 75% - Fast, isolated unit tests
     /------------\
```

### Running Tests

```bash
# All tests (backend + frontend + E2E)
make test

# Backend only
cd backend && pytest
pytest -v                          # Verbose
pytest -k "security"               # By keyword
pytest tests/unit/models/          # Specific directory

# Frontend only
cd frontend && npm test
npm test -- --watch                # Watch mode
npm test -- Dashboard              # Specific component

# E2E only
npx playwright test
npx playwright test --headed       # See browser
npx playwright test --ui           # Interactive UI mode
```

### CI/CD Pipeline

**Multi-Stage, Parallelized Pipeline**:
1. **Smoke Tests** (<5 min): Fast feedback, fail fast
2. **Unit Tests** (parallel): Bulk of test suite
3. **Integration Tests** (sharded): Database and API tests
4. **E2E Tests** (4-way shard): Browser tests across Chromium, Firefox, WebKit, Mobile
5. **Security Scans**: Trivy, Safety, Bandit
6. **Coverage Enforcement**: Fails if coverage drops below thresholds

**Quality Gates**:
- All tests must pass
- Coverage must meet thresholds
- Security scans must pass
- Linters must pass (Black, Flake8, ESLint, TypeScript)

See [Testing Documentation](./docs/TESTING_QUICKSTART.md) for complete guide.

---

## ⚙️ Configuration

### Environment Variables

**Minimum Required Configuration:**
```bash
# .env file
COMPOSE_PROJECT_NAME=yourproject-commandcenter  # MUST be unique per project
SECRET_KEY=$(openssl rand -hex 32)              # Cryptographic operations
DB_PASSWORD=$(openssl rand -hex 16)             # Database password
```

**Full Configuration Options:**

```bash
# === Service Ports ===
BACKEND_PORT=8000       # FastAPI backend
FRONTEND_PORT=3000      # React frontend
POSTGRES_PORT=5432      # PostgreSQL
REDIS_PORT=6379         # Redis (Celery broker)

# === Database ===
DATABASE_URL=postgresql://commandcenter:${DB_PASSWORD}@postgres:5432/commandcenter
DB_PASSWORD=changeme

# === Security ===
SECRET_KEY=your-secret-key-here-use-openssl-rand-hex-32
ENCRYPT_TOKENS=true                    # Encrypt GitHub tokens at rest
CORS_ORIGINS=http://localhost:3000     # CORS allowed origins

# === GitHub Integration (Optional) ===
GITHUB_TOKEN=ghp_your_personal_access_token

# === AI/RAG APIs (Optional) ===
ANTHROPIC_API_KEY=sk-ant-...           # For Claude models
OPENAI_API_KEY=sk-...                  # For GPT models

# === Celery (Task Queue) ===
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# === KnowledgeBeast/RAG ===
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  # Local embeddings
VECTOR_DIMENSION=384                    # Embedding vector size
```

**Multi-Instance Configuration**:

When running multiple CommandCenter instances, each must have:
- Unique `COMPOSE_PROJECT_NAME`
- Different port numbers (or use Traefik)
- Separate Docker volumes
- Unique `SECRET_KEY` and `DB_PASSWORD`

See [Configuration Guide](./docs/CONFIGURATION.md) for advanced options.

---

## 🛠️ Development

### Local Development Setup

**Backend (Python):**
```bash
cd backend
python -m venv venv
source venv/bin/activate              # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend (React):**
```bash
cd frontend
npm install
npm run dev                           # Starts on port 3000
```

**Database (PostgreSQL + pgvector):**
```bash
# Use Docker for development
docker-compose up -d postgres redis

# Or build custom image with pgvector
python backend/scripts/build-postgres.py
```

### Database Migrations

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "description of change"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current version
alembic current

# View migration history
alembic history
```

### Make Commands

```bash
make help           # Show all available commands

# Setup
make setup          # Create .env from template
make start          # Start all services with port check
make stop           # Stop all services
make restart        # Restart all services
make rebuild        # Rebuild and restart (no cache)

# Development
make dev            # Start in dev mode with live reload
make logs           # View all logs (follow mode)
make logs-backend   # Backend logs only
make logs-frontend  # Frontend logs only
make health         # Check service health

# Testing
make test           # Run all tests
make test-backend   # Backend tests only
make test-frontend  # Frontend tests only
make test-docker    # Full Docker-based test suite

# Database
make migrate        # Apply all pending migrations
make db-backup      # Backup to backups/ directory
make db-restore     # Restore from latest backup
make shell-db       # PostgreSQL shell

# Code Quality
make lint           # Run all linters
make format         # Auto-format all code

# Cleanup
make clean          # Remove containers, volumes, images
```

---

## 📖 Documentation

### User Guides
- **[Quick Start Guide](./docs/QUICKSTART.md)** - Get up and running in 5 minutes
- **[API Documentation](./docs/API.md)** - Complete REST API reference
- **[Knowledge Base Guide](./docs/KNOWLEDGE_BASE.md)** - Using RAG features effectively

### Deployment & Operations
- **[Deployment Guide](./docs/DEPLOYMENT.md)** - Production deployment strategies
- **[Data Isolation](./docs/DATA_ISOLATION.md)** - Multi-project security architecture
- **[Port Management](./docs/PORT_MANAGEMENT.md)** - Handling port conflicts
- **[Traefik Setup](./docs/TRAEFIK_SETUP.md)** - Zero-conflict deployment with reverse proxy

### Development
- **[Architecture](./docs/ARCHITECTURE.md)** - System design and patterns
- **[Contributing Guide](./docs/CONTRIBUTING.md)** - Development guidelines and PR process
- **[Testing Guide](./docs/TESTING_QUICKSTART.md)** - Writing and running tests
- **[Docling Setup](./docs/DOCLING_SETUP.md)** - RAG document processing configuration
- **[Hub Design](./docs/HUB_DESIGN.md)** - Multi-instance management architecture
- **[Dagger Architecture](./docs/DAGGER_ARCHITECTURE.md)** - Container orchestration details

### Reference
- **[PRD](./docs/PRD.md)** - Original product specification
- **[Roadmap](./docs/ROADMAP.md)** - Development timeline and milestones
- **[Claude Code Guide](./docs/CLAUDE.md)** - AI assistant integration guide

---

## 📊 Use Cases & Examples

### 1. Music Tech R&D (Performia - Original Use Case)
**Scenario**: Track JUCE framework updates, AI music generation models, spatial audio research, audio processing libraries

**Workflow**:
- Add RSS feed for JUCE blog
- Set up GitHub webhooks for audio processing repos
- Create technologies: JUCE, PortAudio, Spatial Audio
- Research tasks: "Evaluate binaural rendering libraries", "Benchmark real-time audio ML"
- Knowledge base: Ingest research papers on spatial audio via file watcher

**Result**: Automated tracking of music tech landscape, AI-powered answers to "What are the latest VST3 features?"

### 2. AI/ML Research Lab
**Scenario**: Monitor LLM releases, track AI papers, organize experiments, build knowledge from findings

**Workflow**:
- RSS feeds: OpenAI blog, Anthropic releases, HuggingFace updates
- Documentation scrapers: LangChain docs, PyTorch docs
- File watchers: Local experiment notebooks and results
- Technologies: GPT-4, Claude, LLaMA, Stable Diffusion
- Research: "Evaluate retrieval methods for RAG", "Benchmark embedding models"

**Result**: Never miss important AI releases, query knowledge base with "What embedding model should I use for code search?"

### 3. Multi-Project Software Consultancy
**Scenario**: Manage R&D across 10+ client projects, each with different tech stacks

**Workflow**:
- Deploy CommandCenter Hub
- Create instance per client project (data isolation)
- Track client repos, technologies, research per project
- Centralized monitoring via Hub dashboard
- Query knowledge: "What authentication libraries did we evaluate for Project X?"

**Result**: Organized research across all projects, no data leakage, reusable insights

### 4. Open Source Maintainer
**Scenario**: Maintain multiple OSS projects, track dependencies, organize roadmap research

**Workflow**:
- Track all owned repos + key dependencies
- RSS feeds for dependency release notes
- GitHub webhooks for issue/PR activity
- Technologies: Track all major dependencies and their updates
- Research: "Security audit findings", "Performance optimization ideas"

**Result**: Proactive dependency management, searchable history of architectural decisions

---

## 🤝 Contributing

We welcome contributions! CommandCenter is built in the open with AI assistance (primarily Claude Code).

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with tests and documentation
4. **Run the full test suite**: `make test`
5. **Ensure linting passes**: `make lint`
6. **Commit with conventional commits**: `feat: add amazing feature`
7. **Push to your fork**: `git push origin feature/amazing-feature`
8. **Open a Pull Request** with a clear description

### Contribution Guidelines

- **Code Style**: Follow existing patterns, use Black (Python) and ESLint (TypeScript)
- **Tests Required**: All new features must have tests (maintain 80%+ backend, 60%+ frontend coverage)
- **Documentation**: Update relevant docs in `docs/` directory
- **Security**: Never commit secrets, tokens, or sensitive data
- **Commit Messages**: Use conventional commits (feat, fix, docs, test, refactor, chore)

See [Contributing Guide](./docs/CONTRIBUTING.md) for detailed requirements.

### Development Workflow

```bash
# Set up development environment
git clone https://github.com/YOUR_USERNAME/CommandCenter.git
cd CommandCenter
make setup
make start

# Create feature branch
git checkout -b feature/my-feature

# Make changes, add tests
cd backend && pytest                  # Verify backend tests pass
cd ../frontend && npm test            # Verify frontend tests pass

# Lint and format
make lint
make format

# Commit and push
git add .
git commit -m "feat: add my feature"
git push origin feature/my-feature
```

---

## 📝 License

[MIT License](./LICENSE)

CommandCenter is free and open source software. You can use it for personal or commercial projects.

---

## 🔗 Links & Resources

- **GitHub Repository**: https://github.com/PerformanceSuite/CommandCenter
- **Issue Tracker**: https://github.com/PerformanceSuite/CommandCenter/issues
- **Discussions**: https://github.com/PerformanceSuite/CommandCenter/discussions
- **Performia (Parent Project)**: https://github.com/PerformanceSuite/Performia
- **KnowledgeBeast Documentation**: [libs/knowledgebeast/README.md](./libs/knowledgebeast/README.md)

### Community & Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/PerformanceSuite/CommandCenter/issues/new?template=bug_report.md)
- ✨ **Feature Requests**: [GitHub Issues](https://github.com/PerformanceSuite/CommandCenter/issues/new?template=feature_request.md)
- 💬 **Questions**: [GitHub Discussions](https://github.com/PerformanceSuite/CommandCenter/discussions)
- 📖 **Documentation**: [docs/](./docs/)

---

## 🙏 Acknowledgments

CommandCenter is built with inspiration from:
- **[ThoughtWorks Technology Radar](https://www.thoughtworks.com/radar)** - Technology tracking visualization
- **[Zalando Tech Radar](https://opensource.zalando.com/tech-radar/)** - Open source radar implementation
- **Modern R&D management practices** from leading software organizations

**Built with:**
- FastAPI, SQLAlchemy, Celery, PostgreSQL (backend)
- React, TypeScript, TanStack Query, Tailwind (frontend)
- Dagger SDK, Docker (infrastructure)
- sentence-transformers, Docling (AI/ML)
- Claude Code (AI pair programming)

---

## 📈 Project Status

**Current Phase**: Phase B Complete (Automated Knowledge Ingestion)
**Active PR**: [#63 - Phase B: Automated Knowledge Ingestion System](https://github.com/PerformanceSuite/CommandCenter/pull/63)
**Infrastructure Completeness**: ~67%
**Test Coverage**: Backend 80%+, Frontend 60%+
**Production Readiness**: Approaching production-grade (Phase C required for full observability)

**Last Updated**: 2025-10-31

---

**Built by the Performia Team** | [PerformanceSuite](https://github.com/PerformanceSuite)

*CommandCenter: Your R&D Operating System* 🚀
