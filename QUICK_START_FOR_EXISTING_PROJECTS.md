# Quick Start: Using CommandCenter with Existing Projects

**Last Updated**: 2025-10-14 (After N+1 Query Fix)

This guide helps you quickly deploy CommandCenter to track R&D activities across your existing projects.

---

## 🎯 What You'll Achieve

- Track technologies across all your projects
- Monitor GitHub repositories automatically
- Build a searchable knowledge base of your research
- Organize research tasks and findings
- Visualize technology adoption

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Clone & Configure

```bash
# Clone into your project directory for isolation
cd ~/projects/your-project/
git clone https://github.com/PerformanceSuite/CommandCenter.git commandcenter
cd commandcenter

# Create environment file
cp .env.template .env
```

### Step 2: Configure Essential Settings

Edit `.env` with these **required** values:

```bash
# CRITICAL: Unique name per project (prevents data mixing)
COMPOSE_PROJECT_NAME=yourproject-commandcenter

# Generate with: openssl rand -hex 32
SECRET_KEY=<your-32-char-random-string>

# Strong password for PostgreSQL
DB_PASSWORD=<your-strong-password>

# Optional: GitHub token for repo tracking
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxx
```

**⚠️ IMPORTANT**: Each project MUST have a unique `COMPOSE_PROJECT_NAME` to prevent data leakage!

### Step 3: Start Services

```bash
# Check for port conflicts first
./scripts/check-ports.sh

# Start all services
make start

# Or manually:
docker-compose up -d
```

### Step 4: Access CommandCenter

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📋 First Steps After Installation

### 1. Add Your First Repository

**Via Web UI**:
1. Go to Settings → Repository Manager
2. Click "Add Repository"
3. Enter: `owner/repo-name` (e.g., `facebook/react`)
4. Optional: Add GitHub token for private repos

**Via API**:
```bash
curl -X POST http://localhost:8000/api/v1/repositories \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "your-org",
    "name": "your-repo",
    "description": "Your project description",
    "access_token": "ghp_..."
  }'
```

### 2. Add Technologies You're Tracking

**Example Technologies**:
```bash
# Add a technology via API
curl -X POST http://localhost:8000/api/v1/technologies \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "ai-ml",
    "title": "GPT-4",
    "vendor": "OpenAI",
    "status": "adopted",
    "relevance_score": 95,
    "description": "Large language model for code generation"
  }'
```

**Common Domains**:
- `ai-ml` - AI/ML technologies
- `audio-dsp` - Audio processing
- `cloud` - Cloud platforms
- `frontend` - Frontend frameworks
- `backend` - Backend technologies
- `devops` - DevOps tools

### 3. Create Research Tasks

**Via API**:
```bash
curl -X POST http://localhost:8000/api/v1/research \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Evaluate RAG architectures",
    "description": "Compare vector DB options",
    "status": "in_progress",
    "priority": "high",
    "technology_id": 1
  }'
```

### 4. Query Knowledge Base (Optional)

If you've enabled RAG with `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the latest AI music models?"}'
```

---

## 🔧 Configuration for Multiple Projects

### Scenario: Track 3 Different Projects

Each project needs its own CommandCenter instance with **isolated data**.

#### Project A (Music App)
```bash
# ~/projects/music-app/commandcenter/.env
COMPOSE_PROJECT_NAME=musicapp-commandcenter
BACKEND_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432
REDIS_PORT=6379
```

#### Project B (AI Research)
```bash
# ~/projects/ai-research/commandcenter/.env
COMPOSE_PROJECT_NAME=airesearch-commandcenter
BACKEND_PORT=8010
FRONTEND_PORT=3010
POSTGRES_PORT=5433
REDIS_PORT=6380
```

#### Project C (E-commerce)
```bash
# ~/projects/ecommerce/commandcenter/.env
COMPOSE_PROJECT_NAME=ecommerce-commandcenter
BACKEND_PORT=8020
FRONTEND_PORT=3020
POSTGRES_PORT=5434
REDIS_PORT=6381
```

**Access URLs**:
- Music App: http://localhost:3000
- AI Research: http://localhost:3010
- E-commerce: http://localhost:3020

---

## 🚀 Alternative: Use Traefik (Zero Port Conflicts)

If managing ports is annoying, use Traefik for automatic routing:

### One-Time Traefik Setup

```bash
# Create Traefik network (once, shared across all projects)
docker network create traefik-network

# Start Traefik (once)
cd ~/traefik-setup
docker-compose up -d
```

### Configure Each Project for Traefik

```bash
# In each project's .env
USE_TRAEFIK=true
TRAEFIK_SUBDOMAIN=musicapp  # or 'airesearch', 'ecommerce'
```

```bash
# Start with Traefik compose file
docker-compose -f docker-compose.traefik.yml up -d
```

**Access URLs**:
- Music App: http://musicapp.localhost
- AI Research: http://airesearch.localhost
- E-commerce: http://ecommerce.localhost

**No port conflicts!** 🎉

See `docs/TRAEFIK_SETUP.md` for complete setup.

---

## 📊 Example Workflow: Tracking React Project

Let's say you're working on a React app and want to track your R&D:

### 1. Add Your Repository

```bash
curl -X POST http://localhost:8000/api/v1/repositories \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "mycompany",
    "name": "react-app",
    "description": "Main React application"
  }'
```

### 2. Add Technologies You Use

```bash
# React
curl -X POST http://localhost:8000/api/v1/technologies \
  -d '{"domain":"frontend","title":"React 18","status":"adopted","relevance_score":100}'

# TypeScript
curl -X POST http://localhost:8000/api/v1/technologies \
  -d '{"domain":"frontend","title":"TypeScript 5","status":"adopted","relevance_score":95}'

# Vite
curl -X POST http://localhost:8000/api/v1/technologies \
  -d '{"domain":"frontend","title":"Vite 5","status":"adopted","relevance_score":90}'
```

### 3. Track Research

```bash
# Research task: Evaluate state management
curl -X POST http://localhost:8000/api/v1/research \
  -d '{
    "title": "Evaluate Zustand vs Redux Toolkit",
    "description": "Compare performance and DX",
    "status": "in_progress",
    "priority": "high",
    "technology_id": 1
  }'
```

### 4. Sync Repository (Auto-detect Technologies)

```bash
# Sync will detect tech from package.json
curl -X POST http://localhost:8000/api/v1/repositories/1/sync
```

---

## 🔍 Key Features for Existing Projects

### 1. **Multi-Repository Tracking**
- Track unlimited GitHub repos
- Auto-sync commits and changes
- Detect technologies from code

### 2. **Technology Radar**
- Visualize tech adoption across domains
- Track maturity: `research` → `trial` → `adopt` → `hold`
- Link technologies to repositories

### 3. **Research Hub**
- Organize research tasks by priority
- Track progress and findings
- Link to specific technologies

### 4. **Knowledge Base (RAG)**
- Upload research documents
- Semantic search across all content
- AI-powered insights

### 5. **Jobs API (Async Operations)**
- **NEW**: Optimized with 70% latency reduction
- Background processing for large operations
- Real-time WebSocket updates
- Batch exports (SARIF, HTML, CSV, Excel, JSON)

---

## 📚 Available Documentation

All documentation is up-to-date (verified 2025-10-14):

### Getting Started
- ✅ **README.md** - Project overview and quick start
- ✅ **CLAUDE.md** - Development commands and architecture
- ✅ **docs/SETUP_GUIDE.md** - Comprehensive setup (43 pages)
- ✅ **docs/USER_GUIDE.md** - End-user documentation

### Development
- ✅ **docs/API.md** - Complete API reference (v2.0.0 with Phase 2 features)
- ✅ **docs/ARCHITECTURE.md** - System design and patterns
- ✅ **docs/CONTRIBUTING.md** - Development guidelines
- ✅ **backend/README.md** - Backend-specific docs
- ✅ **frontend/README.md** - Frontend-specific docs

### Operations
- ✅ **docs/OPERATIONS_GUIDE.md** - Production operations
- ✅ **docs/E2E_TESTING.md** - End-to-end testing (100% pass rate)
- ⚠️ **docs/DATA_ISOLATION.md** - **READ THIS FIRST** for multi-project security

### Recent Updates
- ✅ **PERFORMANCE_ANALYSIS.md** - Performance optimization guide
- ✅ **SECURITY_AUDIT_2025-10-14.md** - Security assessment
- ✅ **COMPREHENSIVE_CODE_REVIEW_2025-10-14.md** - Complete code review
- ✅ **.claude/sessions/session-46-n1-query-fix.md** - Latest performance fix

---

## ⚙️ Configuration Reference

### Minimal Configuration (.env)

```bash
# Required
COMPOSE_PROJECT_NAME=yourproject-commandcenter
SECRET_KEY=<generate-with-openssl-rand-hex-32>
DB_PASSWORD=<strong-password>

# Ports (change if conflicts)
BACKEND_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432
REDIS_PORT=6379
```

### Full Configuration (Optional Features)

```bash
# GitHub Integration
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxx

# AI APIs (for RAG features)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx

# Database
DATABASE_URL=postgresql://commandcenter:${DB_PASSWORD}@postgres:5432/commandcenter

# Redis & Celery
REDIS_URL=redis://redis:6379
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Security
ENCRYPT_TOKENS=true
CORS_ORIGINS=["http://localhost:3000"]

# RAG/Knowledge Base
KNOWLEDGE_BASE_PATH=./rag_storage
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## 🛠️ Common Commands

### Docker Management
```bash
make start          # Start all services
make stop           # Stop all services
make restart        # Restart all services
make logs           # View all logs
make logs-backend   # Backend logs only
make health         # Check service health
make clean          # Remove all data (⚠️ DESTRUCTIVE)
```

### Database Operations
```bash
make migrate        # Apply migrations
make db-backup      # Backup database
make db-restore     # Restore from backup
make shell-db       # PostgreSQL shell
```

### Development
```bash
make shell-backend   # Backend container shell
make test            # Run all tests
make lint            # Run linters
make format          # Auto-format code
```

---

## 🐛 Troubleshooting

### Port Conflicts
```bash
# Check which ports are in use
./scripts/check-ports.sh

# Solution 1: Change ports in .env
BACKEND_PORT=8010
FRONTEND_PORT=3010

# Solution 2: Use Traefik (zero conflicts)
# See docs/TRAEFIK_SETUP.md
```

### Database Connection Errors
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify database is running
docker-compose ps

# Reset database (⚠️ LOSES DATA)
make clean
make start
```

### Migration Errors
```bash
# Check current migration state
docker-compose exec backend alembic current

# Force to latest
docker-compose exec backend alembic upgrade head

# Create new migration
make migrate-create MESSAGE="your description"
```

### Frontend Build Errors
```bash
# Check logs
docker-compose logs frontend

# Rebuild node_modules
docker-compose exec frontend rm -rf node_modules
docker-compose exec frontend npm install

# Type check
docker-compose exec frontend npm run type-check
```

---

## 📞 Getting Help

- 📖 **Docs**: `docs/` directory
- 🐛 **Issues**: https://github.com/PerformanceSuite/CommandCenter/issues
- 💬 **Discussions**: https://github.com/PerformanceSuite/CommandCenter/discussions
- 📧 **API Docs**: http://localhost:8000/docs (when running)

---

## ✅ Pre-Deployment Checklist

Before using CommandCenter with your project:

- [ ] Unique `COMPOSE_PROJECT_NAME` set
- [ ] Strong `SECRET_KEY` generated
- [ ] Strong `DB_PASSWORD` set
- [ ] Ports checked for conflicts
- [ ] `.env` file reviewed
- [ ] Docker & Docker Compose installed
- [ ] Read `docs/DATA_ISOLATION.md` (for multi-project setups)

---

## 🎯 Next Steps

1. **Start using**: Add your first repository
2. **Explore features**: Try the Technology Radar and Research Hub
3. **Customize**: Adjust domains and statuses to match your workflow
4. **Scale up**: Add more repositories and technologies
5. **Advanced features**: Enable RAG for knowledge base search

**Ready to track your R&D like a pro!** 🚀

---

**Version**: 2.0 (Phase 2 Complete)
**Last Updated**: 2025-10-14
**Performance**: ✅ Optimized (70% latency reduction)
**Tests**: ✅ 100% E2E pass rate across 6 browsers
