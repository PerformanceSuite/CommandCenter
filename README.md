# Command Center

**Your Personal AI Operating System for Knowledge Work**

Command Center is a production-grade platform that transforms how you work with information. It's not just an R&D tool - it's your personal AI assistant that automates knowledge gathering, connects all your tools, learns your research patterns, and proactively surfaces insights before you even ask.

[![Tests](https://github.com/PerformanceSuite/CommandCenter/workflows/CI/badge.svg)](https://github.com/PerformanceSuite/CommandCenter/actions)
[![codecov](https://codecov.io/gh/PerformanceSuite/CommandCenter/branch/main/graph/badge.svg)](https://codecov.io/gh/PerformanceSuite/CommandCenter)

---

## 🎯 The Big Vision: What CommandCenter Really Is

### Not Just Another Tool - Your Knowledge Operating System

CommandCenter is being built to become the **intelligent layer between you and all your tools** - a unified operating system for knowledge work that:

- **Automates Information Gathering**: While you sleep, it monitors RSS feeds, scrapes documentation, watches repositories, ingests papers
- **Connects Your Entire Ecosystem**: Notion, Slack, GitHub, Obsidian, Zotero, Linear, Jira - all connected through one unified knowledge graph
- **Learns Your Habits**: Understands what you research, when you work, what matters to you
- **Proactively Surfaces Insights**: "This new paper matches your spatial audio research", "You haven't checked JUCE updates in 2 weeks - here's what's new"
- **Becomes Your Second Brain**: But one that's actively working for you, not just storing information

### The Problem: Knowledge Work is Broken

Modern knowledge workers face a **cognitive overload crisis**:

**Information Chaos**:
- Technologies evolve faster than you can track them
- Research scattered across GitHub, Notion, Slack, email, browser tabs, papers
- Important updates lost in notification noise
- Context switching kills 40% of productive time
- Knowledge silos prevent building on past work

**Tool Fragmentation**:
- GitHub for code, Notion for notes, Slack for discussions, Zotero for papers
- No unified search across tools
- Manual context switching between every tool
- Information duplicated in multiple places
- Each tool has different AI features that don't talk to each other

**Manual Everything**:
- You manually check feeds, repos, documentation
- You manually transfer knowledge between tools
- You manually remember what you were researching
- You manually search for that thing you read 3 months ago

### The Solution: Intelligent Automation + Unified Knowledge

CommandCenter creates a **unified intelligence layer** that sits between you and your tools:

```
┌─────────────────────────────────────────────────────────┐
│                         YOU                              │
└────────────────────┬────────────────────────────────────┘
                     │ Natural Language Interface
┌────────────────────▼────────────────────────────────────┐
│              COMMAND CENTER                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Automated Ingestion    │  AI Intelligence        │  │
│  │  • RSS/Feeds            │  • RAG Search           │  │
│  │  • GitHub Webhooks      │  • Pattern Learning     │  │
│  │  • Doc Scrapers         │  • Proactive Insights   │  │
│  │  • File Watchers        │  • Smart Notifications  │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Unified Knowledge Graph                   │  │
│  │  Technologies ↔ Repos ↔ Research ↔ Documents     │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ Bi-Directional Sync
┌────────────────────▼────────────────────────────────────┐
│                YOUR ECOSYSTEM                            │
│  GitHub │ Notion │ Slack │ Obsidian │ Zotero │ Linear  │
│  ArXiv │ YouTube │ Browser │ Jira │ Discord │ Podcasts │
└─────────────────────────────────────────────────────────┘
```

**How It Works**:

1. **Automated Collection**: While you work, CommandCenter continuously ingests information from all configured sources
2. **Intelligent Processing**: RAG embeddings create searchable knowledge, AI identifies patterns and connections
3. **Unified Search**: One natural language query searches across GitHub, Notion, Slack, papers, docs, everything
4. **Proactive Intelligence**: Habit Coach learns your patterns and surfaces relevant insights before you ask
5. **Ecosystem Sync**: Updates in CommandCenter sync to Notion/Slack/etc, updates in those tools sync back

**Result**: You focus on thinking and creating. CommandCenter handles the information management.

---

## 🌟 What Makes CommandCenter Different

### 1. **Your Personal AI That Actually Knows You**

Unlike generic AI tools (ChatGPT, Claude), CommandCenter builds a **persistent memory of YOUR specific context**:
- Your research history and patterns
- Your technology stack and preferences
- Your code repositories and commit patterns
- Your questions and the answers you found useful
- Your work habits and optimal notification times

**Example**: "What authentication library should I use?"
- Generic AI: Gives generic answer about Auth0, Firebase, etc.
- CommandCenter: "Based on your past research on privacy-first design and your preference for self-hosted solutions, and your recent work with Go in the microservices repo, I'd recommend Ory Kratos. Here's the research you did on authentication 3 months ago..."

### 2. **Active Intelligence, Not Passive Storage**

Most "second brain" tools (Notion, Obsidian, Roam) are **passive databases**. CommandCenter is an **active intelligence system**:

**Passive Tools**:
- You manually add information
- You manually search when you need something
- Information just sits there waiting
- No connections made automatically

**CommandCenter**:
- Automatically ingests information while you sleep
- Proactively surfaces relevant insights
- Continuously makes connections across your knowledge
- Learns what matters and filters noise
- Sends notifications when something matches your interests

### 3. **Unified Ecosystem Hub**

Instead of context switching between 10 tools, CommandCenter becomes the **single interface** to your entire ecosystem:

**Old Way**:
- Check GitHub for repo updates → Switch to Notion to take notes → Switch to Slack to discuss → Switch to Zotero to add paper → Switch to Linear to create task

**CommandCenter Way**:
- Ask: "What's new in my spatial audio research?"
- Get: Unified view of GitHub commits, Notion notes, Slack discussions, new papers, with context from all sources
- Act: Create research task, it syncs to Linear. Save finding, it syncs to Notion. All from one place.

### 4. **Privacy-First Personal AI**

Your research is **YOUR proprietary knowledge**. CommandCenter ensures:
- **Data Isolation**: Each project has its own instance (never share data)
- **Local Embeddings**: sentence-transformers runs locally (no data sent to OpenAI)
- **Self-Hosted**: Run on your infrastructure, full control
- **Encrypted Secrets**: All tokens/keys encrypted at rest with AES-256
- **No Vendor Lock-in**: Open source, own your data forever

---

## ✨ Current Capabilities (What Works Today)

### 🧠 AI-Powered Knowledge Base

**Natural Language Search Across Everything**:
```
You: "What are the latest VST3 features?"

CommandCenter searches:
✓ GitHub repos you're tracking
✓ Documentation you've ingested
✓ Research notes you've made
✓ Papers in your file watchers
✓ RSS feeds from JUCE blog

Returns: AI-synthesized answer with citations from all sources
```

**RAG Architecture**:
- KnowledgeBeast v3.0 with PostgreSQL + pgvector
- Hybrid search: Vector similarity + keyword search with Reciprocal Rank Fusion
- HuggingFace sentence-transformers (local, no API costs)
- Docling for PDF, Markdown, HTML, code extraction
- Multi-tenant with collection-based isolation

### 🤖 Automated Knowledge Ingestion (Phase B Complete)

**Set It and Forget It - Information Comes to You**:

**RSS Feed Monitoring**:
- Import OPML files with all your feeds
- Scheduled updates (cron-based: hourly, daily, weekly)
- Automatic deduplication
- Smart prioritization

**Documentation Scrapers**:
- Monitor any documentation site (e.g., LangChain docs, PyTorch docs)
- SSRF protection (won't scrape internal networks)
- URL validation and sanitization
- Scheduled re-scraping to catch updates

**GitHub Webhooks**:
- Real-time notifications on commits, PRs, issues
- Automatic knowledge base updates from README changes
- Works with any GitHub repo (public or private with token)

**File System Watchers**:
- Watch local directories for new papers, notes, code
- Debounced processing (won't re-process on every edit)
- Path validation and file size limits
- Automatic ingestion when files change

**Smart Source Management**:
- Priority levels (critical → high → medium → low)
- Enable/disable sources without deleting
- Full CRUD APIs with pagination
- Error tracking per source

### 📊 Technology Radar & Research Management

**Technology Tracking**:
- Monitor technologies across custom domains (AI/ML, Audio, Cloud, DevOps, etc.)
- Lifecycle tracking: Discovery → Assessment → Trial → Adopt → Hold
- Relevance scoring with justifications
- Link to repos, research, and knowledge entries
- Visual radar inspired by ThoughtWorks

**Research Workflows**:
- Task organization: Planning → In Progress → Completed → Archived
- Priority management with smart sorting
- Rich metadata: tags, links to technologies/repos
- Markdown support for detailed notes

### 📦 Multi-Repository Intelligence

**GitHub Integration**:
- Track unlimited repositories
- Automatic commit syncing
- Per-repo access tokens (AES-256 encrypted)
- Technology detection from codebase
- Activity monitoring and health checks
- Cross-repo insights and pattern analysis

### 🔐 Enterprise-Grade Security

**Data Isolation Architecture**:
- **One instance per project** (never share instances)
- Separate Docker volumes per project
- Unique encryption keys per instance
- Prevents data leakage between projects

**Security Hardening**:
- Token encryption at rest (AES-256 Fernet)
- SSRF protection in scrapers
- SQL injection prevention (SQLAlchemy 2.0)
- XSS protection (CSP headers)
- Input validation (Pydantic schemas)
- Rate limiting on all APIs
- Memory leak prevention
- Timezone-aware datetime handling

### ⚙️ Production Infrastructure

**Celery Task Queue** ✅:
- Robust async processing
- Retry logic and error handling
- Transaction rollback on failures
- Redis broker for reliability

**KnowledgeBeast RAG Engine** ✅:
- Production-grade vector storage
- Local embeddings (no external APIs)
- Hybrid search for optimal results
- Multi-tenant collection management

**Container Orchestration** (Partial):
- Dagger SDK for type-safe infrastructure
- Docker Compose for development
- Hub for multi-instance management
- In progress: Health checks, resource limits, logging (Phase A completion)

---

## 🚀 Getting Started

### ⚠️ CRITICAL: Data Isolation Principle

**Each project MUST have its own CommandCenter instance. Never share instances.**

CommandCenter stores:
- Encrypted GitHub access tokens
- Proprietary research and knowledge
- RAG embeddings of sensitive documents
- Project-specific configurations
- Your work patterns and habits (future)

Sharing instances = security vulnerability + data leakage. See [Data Isolation Guide](./docs/DATA_ISOLATION.md).

### Prerequisites

- **Docker** & **Docker Compose** 20.10+
- **Python** 3.11+ (for local development)
- **Node.js** 18+ (for frontend development)
- **PostgreSQL** 16+ with pgvector (handled by Docker)
- **GitHub Account** (optional, for repository tracking)
- **OpenAI/Anthropic API Key** (optional, for enhanced RAG)

### Quick Start (5 minutes)

1. **Clone into project-specific directory:**
   ```bash
   cd ~/projects/your-project/
   git clone https://github.com/PerformanceSuite/CommandCenter.git commandcenter
   cd commandcenter
   ```

2. **Configure environment:**
   ```bash
   make setup  # Creates .env from template

   # Edit .env
   vim .env
   ```

   **Minimum configuration:**
   ```bash
   COMPOSE_PROJECT_NAME=yourproject-commandcenter  # MUST be unique
   SECRET_KEY=$(openssl rand -hex 32)              # Generate secure key
   DB_PASSWORD=$(openssl rand -hex 16)             # Strong password
   ```

3. **Start services:**
   ```bash
   make start  # Handles port checks automatically
   ```

4. **Verify installation:**
   ```bash
   make health  # Check all services
   ```

5. **Access the application:**
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000/docs

### First Steps: Building Your Knowledge OS

1. **Set up ingestion sources** (Knowledge Base → Sources):
   - Add RSS feeds for blogs you follow
   - Create webhooks for GitHub repos
   - Add file watchers for research directories
   - Configure documentation scrapers

2. **Define your technology landscape** (Dashboard → Technology Radar):
   - Add technologies you use/evaluate
   - Set maturity levels and relevance
   - Link to repositories

3. **Create research tasks** (Research Hub):
   - Current investigations
   - Link to technologies and repos
   - Track status and priority

4. **Ask questions** (Knowledge Base):
   - "What are the latest developments in X?"
   - "What did I research about Y last month?"
   - "How does Z work in my codebase?"

---

## 🏗️ Architecture: How It All Fits Together

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         Frontend (React 18 + TypeScript)                     │
│  Dashboard │ Tech Radar │ Research │ Knowledge │ Sources    │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────────────┐
│         Backend Application Layer (FastAPI)                  │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │  Repos   │  Tech    │ Research │   RAG    │ Ingestion│  │
│  │ Service  │ Service  │ Service  │ Service  │ Service  │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│      Automated Task Processing (Celery + Redis)              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ RSS Scrapers │ Doc Scrapers │ Webhooks │ Watchers  │    │
│  │ ├─ OPML Import                                      │    │
│  │ ├─ Cron Scheduling                                  │    │
│  │ ├─ SSRF Protection                                  │    │
│  │ └─ Debouncing & Deduplication                       │    │
│  └─────────────────────────────────────────────────────┘    │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│            Data & Intelligence Layer                         │
│  ┌──────────────────────────┬──────────┬─────────────┐      │
│  │ PostgreSQL 16            │  Redis 7 │ pgvector    │      │
│  │ • Relational data        │ • Queue  │ • Embeddings│      │
│  │ • Knowledge graph        │ • Cache  │ • Vectors   │      │
│  │ • User data & config     │ • Sessions              │      │
│  └──────────────────────────┴──────────┴─────────────┘      │
└─────────────────────────────────────────────────────────────┘
                     │
                     │ (Future: Phase D)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  External Ecosystem                          │
│  GitHub │ Notion │ Slack │ Obsidian │ Zotero │ Linear       │
│  ArXiv │ YouTube │ Browser Extension │ Jira │ Discord       │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend (Intelligence Engine)**:
- **Framework**: Python 3.11, FastAPI, SQLAlchemy 2.0
- **Task Queue**: Celery with Redis broker
- **Database**: PostgreSQL 16 + pgvector extension
- **RAG Engine**: KnowledgeBeast v3.0 (custom, monorepo)
- **Embeddings**: sentence-transformers (HuggingFace, local)
- **Document Processing**: Docling 2.5.5+
- **Security**: cryptography (Fernet), Pydantic
- **Testing**: pytest (1,676+ tests)

**Frontend (User Interface)**:
- **Framework**: React 18, TypeScript 5
- **Build**: Vite 5
- **Styling**: Tailwind CSS 3
- **State**: TanStack Query (React Query)
- **Charts**: Chart.js
- **Testing**: Vitest, Testing Library, Playwright

**Infrastructure (Orchestration)**:
- **Containers**: Docker Compose, Dagger SDK
- **CI/CD**: GitHub Actions (multi-stage, sharded)
- **Observability** (Phase C): Prometheus, Grafana, OpenTelemetry

**Monorepo Libraries**:
- **KnowledgeBeast**: Custom RAG engine in `libs/knowledgebeast/`

---

## 🗺️ Roadmap: From Knowledge Base to Personal AI

### ✅ Phase A: Dagger Production Hardening (Complete)
**Duration**: 3 weeks | **Status**: Shipped

- Type-safe container orchestration with Dagger SDK
- Hub management for multi-project instances
- Basic health checks and error handling
- Foundation for production deployments

### ✅ Phase B: Automated Knowledge Ingestion (Complete - In Review)
**Duration**: 3 weeks | **Status**: PR #63 Open

**What We Built**:
- RSS feed scraper with OPML import and cron scheduling
- Documentation scraper with SSRF protection
- Webhook receivers (GitHub, generic HTTP)
- File system watchers with debouncing
- Source management CRUD APIs
- 50+ comprehensive tests, security hardening

**Why It Matters**: Transforms CommandCenter from manual to automated. Your knowledge base now grows while you sleep.

**Next**: Awaiting CI/CD → Merge to main

### 🚧 Phase C: Observability Layer (Next - 3 weeks)
**Status**: Planned

**The Missing Piece**: You can't improve what you can't measure.

**What We'll Build**:
- **Prometheus Metrics**: Track ingestion rates, RAG query performance, error rates
- **Grafana Dashboards**: Visualize source health, system metrics, usage patterns
- **Distributed Tracing**: OpenTelemetry for RAG pipeline visibility
- **Alerting System**: Proactive notifications for failed ingestion, anomalies
- **Analytics Dashboard**: Understand your usage patterns, most-queried topics
- **Structured Logging**: Debug issues faster with searchable logs
- **SLO Tracking**: Monitor performance regressions

**Why It Matters**: Production systems need visibility. This enables data-driven optimization and proactive problem detection.

### 🔮 Phase D: Ecosystem Integration (Future - 6-8 weeks)
**Status**: Design phase

**The Game Changer**: CommandCenter becomes the hub connecting all your tools.

**Planned Integrations**:

**Communication & Collaboration**:
- **Slack/Discord**: Real-time research updates, query knowledge base via chatbot, share findings with team
- **Teams/Zoom**: Meeting notes auto-ingestion, action items linked to research

**Note-Taking & PKM**:
- **Notion**: Bi-directional sync of research notes, embed CommandCenter queries in Notion pages
- **Obsidian**: Sync knowledge graph, embed backlinks, unified search
- **Roam Research**: Graph database integration

**Academic & Research**:
- **Zotero/Mendeley**: Academic paper tracking, automatic citation management, PDF ingestion
- **ArXiv/PubMed**: Automated paper discovery based on your research topics
- **Google Scholar**: Citation tracking, related work discovery

**Project Management**:
- **Linear/Jira**: Research tasks sync to project management, status updates flow both ways
- **GitHub Issues**: Auto-create research tasks from issues, link discussions to knowledge

**Content & Media**:
- **YouTube API**: Transcript extraction, video bookmarks, channel monitoring
- **Podcast APIs**: Episode transcripts, show notes ingestion
- **Browser Extension**: One-click capture from any webpage, automatic tagging, save to knowledge base

**Data & Analytics**:
- **Google Drive**: Auto-ingest shared docs, presentations, spreadsheets
- **Dropbox/OneDrive**: File watcher integration for cloud storage

**Architecture Foundations**:
- Plugin system for extensible integrations
- Event-driven architecture with message bus (NATS/RabbitMQ)
- OAuth2 flows for third-party authentication
- Webhook delivery system for bi-directional sync
- GraphQL API for flexible data access
- Rate limiting and backpressure handling

**Why It Matters**: Breaks down tool silos. One search queries everything. Updates in one place sync everywhere.

### 🌟 Phase E: Habit Coach AI Assistant (Future - 8-10 weeks)
**Status**: Concept validation

**The Vision**: Your personal AI that learns your patterns and proactively helps.

**Capabilities - Proactive Intelligence**:

**Pattern Learning**:
- Tracks when you research (mornings, late nights, weekends)
- Learns what topics interest you (audio synthesis, distributed systems, etc.)
- Understands your technology preferences (privacy-first, self-hosted, open source)
- Identifies knowledge gaps in your research
- Recognizes when you're stuck or context switching

**Intelligent Notifications**:
- "This new paper on spatial audio matches your research from last month"
- "JUCE 7.0 released with VST3 improvements - you track this in Technology Radar"
- "You haven't updated your LLM research in 2 weeks, here's what's new: GPT-5, Claude 4, Gemini Ultra"
- "You searched for 'authentication libraries' 3 times this week - want me to create a research task?"

**Research Suggestions**:
- "Based on your work on real-time audio processing, you might want to explore WebTransport"
- "You've been researching vector databases - I found a benchmark comparing Qdrant, Weaviate, and Milvus"
- "Your GitHub activity shows you're building a RAG system, but you haven't ingested any papers on retrieval methods"

**Context Management**:
- "You were researching async Rust 3 weeks ago - here's where you left off"
- "Last time you worked on this project, you were evaluating PortAudio vs JUCE"
- "You asked about embedding models last month - here's the research you gathered"

**Knowledge Gap Detection**:
- "You track 5 AI/ML technologies but have no knowledge base entries - should I start monitoring feeds?"
- "You have 3 repositories using React Query but no documentation ingested"
- "Your research task on 'distributed tracing' has no linked technologies or repos"

**Habit Formation & Optimization**:
- Learns your optimal notification times (don't interrupt deep work)
- Suggests research workflows based on what's worked for you
- Identifies and reduces context switching patterns
- Builds muscle memory: "Every Tuesday you review technology radar - here's what changed"

**Technical Foundation**:
- LLM-powered with vector memory of your research patterns
- Reinforcement learning from your interactions
- Privacy-first: All learning happens locally, never sent to cloud
- Built on Phase B ingestion (data collection)
- Requires Phase C observability (pattern detection)
- Leverages Phase D integrations (delivery channels)

**Why It Matters**: Most AI tools are reactive (you ask, they answer). Habit Coach is proactive - it surfaces insights before you think to ask. It's the difference between a search engine and a research partner.

---

## 🎛️ CommandCenter Hub: Multi-Instance Management

**The Challenge**: If each project needs its own CommandCenter instance (data isolation), managing multiple instances is complex.

**The Solution**: CommandCenter Hub - a meta-application for orchestrating multiple instances.

### Hub Architecture

```
┌──────────────────────────────────────────────────────┐
│         CommandCenter Hub (Port 9000)                 │
│  ┌────────────────────────────────────────────────┐  │
│  │  Performia   │  ClientX  │  OpenSource        │  │
│  │  ●Running    │  ●Running │  ○Stopped          │  │
│  │  8 sources   │  12 sources│  5 sources        │  │
│  │  234 docs    │  567 docs  │  89 docs          │  │
│  └────────────────────────────────────────────────┘  │
│                                                       │
│  Unified Dashboard:                                   │
│  • Health monitoring across all instances             │
│  • Centralized logs and metrics                       │
│  • One-click start/stop/restart                       │
│  • Port conflict resolution                           │
│  • Resource usage tracking                            │
└────────────┬─────────────────────────────────────────┘
             │ Dagger SDK (type-safe orchestration)
     ┌───────▼───────┬───────────┬─────────────┐
     │ Performia     │ ClientX   │ OpenSource  │
     │ Ports: 8001   │ 8002      │ 8003        │
     │ Data: Vol1    │ Vol2      │ Vol3        │
     │ 3 repos       │ 8 repos   │ 2 repos     │
     └───────────────┴───────────┴─────────────┘
```

### Key Benefits

**No Template Cloning**:
- Define CommandCenter stack once
- Instantiate per project on demand
- No copying docker-compose.yml files

**Zero Port Conflicts**:
- Automatic port allocation
- Or use Traefik for domain-based routing
- Hub manages all port assignments

**True Data Isolation**:
- Separate Docker volumes per instance
- Unique encryption keys per instance
- Zero data leakage between projects

**Centralized Monitoring**:
- Health status of all instances
- Aggregated logs across projects
- Unified metrics dashboard

**One-Click Operations**:
- Start/stop instances from UI
- View logs without SSH
- Restart failed instances
- Scale resources per instance

**Architecture Details**:
- Backend: FastAPI + Dagger SDK (Python)
- Frontend: React + TypeScript
- Database: SQLite (metadata only, not project data)
- Orchestration: Dagger replaces docker-compose subprocesses

See [Hub Design Documentation](./docs/HUB_DESIGN.md) for complete architecture.

---

## 🧪 Testing & Quality: Production-Grade Standards

CommandCenter maintains **production-grade quality** with comprehensive test coverage.

### Test Statistics

- **1,700+ Total Tests**
  - Backend: 1,676+ tests (unit, integration, security)
  - Frontend: 47 tests (components, hooks, services)
  - E2E: ~40 tests (critical user paths, 4 browsers)
- **Coverage Requirements** (CI enforced):
  - Backend: 80%+
  - Frontend: 60%+
- **CI Runtime**: <25 minutes (parallelized, sharded)

### Test Pyramid

```
           /\
          /E2E\ 10%  - Critical user journeys
         /----\
        / Int \ 15%  - API & database tests
       /--------\
      /  Unit   \ 75% - Fast, isolated tests
     /------------\
```

### Running Tests

```bash
# All tests
make test

# Backend
cd backend && pytest
pytest -v -k "security"        # Security tests only
pytest --cov --cov-report=html # Coverage report

# Frontend
cd frontend && npm test
npm test -- --watch            # Watch mode
npm test -- Dashboard          # Specific component

# E2E
npx playwright test
npx playwright test --headed   # See browser
npx playwright test --ui       # Interactive mode
```

### CI/CD Pipeline

**Multi-Stage, Parallelized**:
1. **Smoke Tests** (<5 min): Fast feedback
2. **Unit Tests** (parallel): Main test suite
3. **Integration Tests** (sharded): Database/API
4. **E2E Tests** (4-way shard): Chromium, Firefox, WebKit, Mobile
5. **Security Scans**: Trivy, Safety, Bandit
6. **Coverage Enforcement**: Fails if coverage drops

**Quality Gates** (all must pass):
- All tests pass
- Coverage thresholds met
- Security scans pass
- Linters pass (Black, Flake8, ESLint, TypeScript)

---

## ⚙️ Configuration

### Environment Variables

**Minimum Required**:
```bash
COMPOSE_PROJECT_NAME=yourproject-commandcenter  # MUST be unique
SECRET_KEY=$(openssl rand -hex 32)              # Cryptographic key
DB_PASSWORD=$(openssl rand -hex 16)             # Database password
```

**Full Options**:

```bash
# === Ports ===
BACKEND_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432
REDIS_PORT=6379

# === Database ===
DATABASE_URL=postgresql://commandcenter:${DB_PASSWORD}@postgres:5432/commandcenter
DB_PASSWORD=changeme

# === Security ===
SECRET_KEY=your-secret-key-use-openssl-rand-hex-32
ENCRYPT_TOKENS=true
CORS_ORIGINS=http://localhost:3000

# === GitHub (optional) ===
GITHUB_TOKEN=ghp_your_token

# === AI/RAG (optional) ===
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# === Celery ===
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# === RAG ===
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DIMENSION=384
```

**Multi-Instance**: Each instance needs unique `COMPOSE_PROJECT_NAME`, ports, volumes, secrets.

---

## 🛠️ Development

### Local Setup

**Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev  # Port 3000
```

**Database**:
```bash
docker-compose up -d postgres redis
# Or build custom image:
python backend/scripts/build-postgres.py
```

### Database Migrations

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "description"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1

# View
alembic current
alembic history
```

### Make Commands

```bash
make help           # Show all commands
make setup          # Create .env
make start          # Start services
make stop           # Stop services
make restart        # Restart
make logs           # View logs
make health         # Check health
make test           # Run tests
make lint           # Lint code
make format         # Auto-format
make clean          # Remove containers/volumes
```

---

## 📖 Documentation

### User Guides
- [Quick Start](./docs/QUICKSTART.md)
- [API Reference](./docs/API.md)
- [Knowledge Base Guide](./docs/KNOWLEDGE_BASE.md)

### Deployment
- [Deployment Guide](./docs/DEPLOYMENT.md)
- [Data Isolation](./docs/DATA_ISOLATION.md)
- [Port Management](./docs/PORT_MANAGEMENT.md)
- [Traefik Setup](./docs/TRAEFIK_SETUP.md)

### Development
- [Architecture](./docs/ARCHITECTURE.md)
- [Contributing](./docs/CONTRIBUTING.md)
- [Testing Guide](./docs/TESTING_QUICKSTART.md)
- [Hub Design](./docs/HUB_DESIGN.md)
- [Dagger Architecture](./docs/DAGGER_ARCHITECTURE.md)

### Reference
- [PRD](./docs/PRD.md)
- [Roadmap](./docs/ROADMAP.md)
- [Claude Code Guide](./docs/CLAUDE.md)

---

## 📊 Real-World Use Cases

### 1. Solo Developer with Multiple Projects

**Scenario**: You maintain 5 open source projects, consult for 3 clients, and have 2 side projects. Each has different tech stacks, research areas, and documentation.

**CommandCenter Setup**:
- **Hub Instance**: Manage all 10 projects from one dashboard
- **Per-Project Isolation**: Each project's research stays separate
- **Unified Intelligence**: Ask "What authentication patterns have I used across all projects?"
- **Habit Coach**: "You usually update dependencies on Fridays - here are 12 outdated packages across your projects"

**Result**: Context switch between projects in seconds. Never forget what you were researching. Reuse patterns across projects.

### 2. AI/ML Research Lab

**Scenario**: Team of researchers tracking papers, experiments, model benchmarks, datasets. Need to collaborate without duplicating work.

**CommandCenter Setup**:
- **ArXiv/PubMed Integration** (Phase D): Auto-ingest papers matching research areas
- **Shared Knowledge Base**: Team queries across all research
- **Experiment Tracking**: Link experiments to papers, models to research tasks
- **Slack Integration** (Phase D): "New paper on retrieval methods matches your RAG research"

**Result**: No duplicate research. Institutional knowledge persists. New team members search history to get up to speed.

### 3. Music Tech R&D (Performia - Original Use Case)

**Scenario**: Track JUCE updates, spatial audio research, VST development, AI music generation.

**CommandCenter Setup**:
- **RSS**: JUCE blog, VST developer forums
- **GitHub Webhooks**: Audio processing repos, plugin frameworks
- **File Watchers**: Local research papers on binaural rendering
- **Doc Scrapers**: JUCE documentation, PortAudio docs
- **Technologies**: JUCE, PortAudio, VST3, AAX, Spatial Audio

**Result**: Automated tracking of music tech landscape. Query: "What are the latest VST3 features?" Gets answer from JUCE blog + docs + your code comments.

### 4. Privacy-Conscious Consultant

**Scenario**: Work with clients in regulated industries (healthcare, finance). Client data CANNOT leak between projects.

**CommandCenter Setup**:
- **Data Isolation**: Each client gets dedicated instance, separate encryption keys
- **Self-Hosted**: Run on your infrastructure, zero cloud dependencies
- **Local Embeddings**: sentence-transformers runs locally (no data to OpenAI)
- **Audit Trail**: All research tracked for compliance

**Result**: Total data isolation. Meets compliance requirements. Full audit trail. You control all data.

---

## 🤝 Contributing

CommandCenter is built in the open with AI assistance (Claude Code). Contributions welcome!

### How to Contribute

1. Fork repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Add tests and documentation
4. Run test suite: `make test`
5. Ensure linting passes: `make lint`
6. Commit: `feat: add amazing feature` (conventional commits)
7. Push to fork: `git push origin feature/amazing-feature`
8. Open Pull Request

### Guidelines

- **Code Style**: Black (Python), ESLint (TypeScript)
- **Tests Required**: 80%+ backend, 60%+ frontend coverage
- **Documentation**: Update relevant docs
- **Security**: Never commit secrets
- **Commit Messages**: Conventional commits (feat, fix, docs, test, refactor, chore)

See [Contributing Guide](./docs/CONTRIBUTING.md) for details.

---

## 📝 License

[MIT License](./LICENSE) - Free and open source. Use for personal or commercial projects.

---

## 🔗 Links & Resources

- **GitHub**: https://github.com/PerformanceSuite/CommandCenter
- **Issues**: https://github.com/PerformanceSuite/CommandCenter/issues
- **Discussions**: https://github.com/PerformanceSuite/CommandCenter/discussions
- **Performia (Parent)**: https://github.com/PerformanceSuite/Performia

### Community

- 🐛 **Bugs**: [GitHub Issues](https://github.com/PerformanceSuite/CommandCenter/issues/new?template=bug_report.md)
- ✨ **Features**: [GitHub Issues](https://github.com/PerformanceSuite/CommandCenter/issues/new?template=feature_request.md)
- 💬 **Questions**: [GitHub Discussions](https://github.com/PerformanceSuite/CommandCenter/discussions)
- 📖 **Docs**: [docs/](./docs/)

---

## 🙏 Acknowledgments

**Inspiration**:
- [ThoughtWorks Technology Radar](https://www.thoughtworks.com/radar) - Technology tracking
- [Zalando Tech Radar](https://opensource.zalando.com/tech-radar/) - Open source radar
- **Personal Knowledge Management** community (Zettelkasten, PARA, Building a Second Brain)

**Built With**:
- FastAPI, SQLAlchemy, Celery, PostgreSQL (backend)
- React, TypeScript, TanStack Query, Tailwind (frontend)
- Dagger SDK, Docker (infrastructure)
- sentence-transformers, Docling (AI/ML)
- Claude Code (AI pair programming)

---

## 📈 Project Status

**Current Phase**: Phase B Complete (Automated Knowledge Ingestion)
**Active PR**: [#63 - Phase B Implementation](https://github.com/PerformanceSuite/CommandCenter/pull/63)
**Infrastructure**: ~67% complete
**Test Coverage**: Backend 80%+, Frontend 60%+
**Production Readiness**: Approaching production-grade (Phase C needed for observability)

**Last Updated**: 2025-10-31

---

**Built by the Performia Team** | [PerformanceSuite](https://github.com/PerformanceSuite)

*CommandCenter: Your Personal AI Operating System for Knowledge Work* 🚀

Not just a tool. Your intelligent partner that automates the tedious, connects the scattered, and amplifies your best thinking.
