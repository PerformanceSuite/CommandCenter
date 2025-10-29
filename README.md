# Command Center

**Multi-Project R&D Management & Knowledge Base**

Command Center is a full-stack application for tracking technologies, managing research tasks, and building a searchable knowledge base across multiple GitHub repositories. Built with FastAPI, React, and powered by RAG (Retrieval Augmented Generation) for intelligent research assistance.

---

## 🎯 What is Command Center?

Command Center helps R&D teams:

- 📊 **Track Technologies** - Monitor emerging tech across multiple domains
- 🔍 **Research Hub** - Organize research tasks and findings
- 🧠 **Knowledge Base** - RAG-powered search across all your research
- 📦 **Multi-Repo Tracking** - Sync and analyze any GitHub repository
- 📈 **Technology Radar** - Visualize technology adoption and relevance
- 🔐 **Secure** - Encrypted token storage, enterprise-ready

---

## ✨ Features

### Technology Tracking
- Track technologies across domains (AI, Audio, Cloud, etc.)
- Monitor maturity, relevance, and adoption status
- Link technologies to research entries and repositories
- Technology Radar visualization

### Research Management
- Create and organize research tasks
- Track status: Planning → In Progress → Completed
- Link research to technologies and repositories
- Priority and tag-based organization

### Knowledge Base (RAG)
- Natural language search across all research
- AI-powered insights using your own data
- Document processing with Docling
- Vector search with KnowledgeBeast (PostgreSQL + pgvector)

### GitHub Integration
- Track unlimited repositories
- Automatic commit syncing
- Per-repository access tokens (encrypted)
- Technology detection from code

---

## 🚀 Quick Start

### ⚠️ CRITICAL: Data Isolation

**Each project MUST have its own CommandCenter instance.**

CommandCenter stores sensitive data and must be isolated per project to prevent:
- Data leakage between projects
- Unauthorized repository access
- Cross-contamination of knowledge bases
- Security token exposure

See [Data Isolation Guide](./docs/DATA_ISOLATION.md) for complete details.

### Prerequisites

- Docker & Docker Compose
- GitHub account (optional, for repo tracking)
- OpenAI or Anthropic API key (optional, for RAG features)

### Installation

1. **Clone to project-specific directory:**
   ```bash
   # Clone into your project's directory for isolation
   cd ~/projects/your-project/
   git clone https://github.com/PerformanceSuite/CommandCenter.git commandcenter
   cd commandcenter
   ```

2. **Set up environment:**
   ```bash
   cp .env.template .env
   # Edit .env with your configuration

   # CRITICAL: Set unique project name for data isolation
   COMPOSE_PROJECT_NAME=yourproject-commandcenter
   ```

3. **Start services:**
   ```bash
   # Recommended: Use Makefile (handles port checks automatically)
   make start

   # Or manually with docker-compose
   ./scripts/check-ports.sh  # Check for port conflicts first
   docker-compose up -d
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### First Steps

1. **Add a repository** - Settings → Repository Manager
2. **Create technologies** - Dashboard → Technology Radar
3. **Start research** - Research Hub → New Task
4. **Query knowledge** - Knowledge Base → Ask questions

---

## Testing

CommandCenter has comprehensive test coverage across all layers.

### Quick Start

```bash
# Run all tests
make test

# Backend tests only
cd backend && pytest

# Frontend tests only
cd frontend && npm test

# E2E tests only
npx playwright test

# Docker tests
make test-docker
```

### Test Statistics

- **390+ tests total**
  - Backend: 784+ tests (unit, integration, security, performance)
  - Frontend: 25+ tests (components, hooks, services)
  - E2E: ~40 tests (critical user paths)
- **Coverage:**
  - Backend: 80%+
  - Frontend: 60%+
- **CI Runtime:** <25 minutes

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

### Documentation

- **[Testing Quickstart](docs/TESTING_QUICKSTART.md)** - How to run and write tests
- **[Testing Strategy](docs/TESTING_STRATEGY.md)** - Testing philosophy and best practices
- **[Contributing Guide](docs/CONTRIBUTING.md#testing-requirements)** - PR testing requirements
- **[CI Workflows](docs/CI_WORKFLOWS.md)** - CI/CD pipeline details

### Running Specific Tests

```bash
# Backend - specific test file
pytest backend/tests/unit/models/test_technology.py

# Backend - specific test
pytest backend/tests/unit/models/test_technology.py::test_validation

# Backend - by keyword
pytest -k "security"

# Frontend - specific component
npm test -- Dashboard

# Frontend - watch mode
npm test -- --watch

# E2E - specific test
npx playwright test e2e/tests/smoke.spec.ts

# E2E - headed mode (see browser)
npx playwright test --headed
```

### CI/CD

Tests run automatically on:
- Every pull request
- Every push to main
- Manual workflow dispatch

**CI Pipeline:**
1. Smoke tests (<5 min) - Fast feedback
2. Unit tests (parallel) - Bulk of tests
3. Integration tests (sharded) - Database tests
4. E2E tests (4-way shard) - Browser tests
5. Performance check - Regression detection

**Coverage Enforcement:**
- Backend must maintain 80%+ coverage
- Frontend must maintain 60%+ coverage
- CI fails if coverage drops

### Badges

[![Tests](https://github.com/PerformanceSuite/CommandCenter/workflows/CI/badge.svg)](https://github.com/PerformanceSuite/CommandCenter/actions)
[![codecov](https://codecov.io/gh/PerformanceSuite/CommandCenter/branch/main/graph/badge.svg)](https://codecov.io/gh/PerformanceSuite/CommandCenter)

---

## 📖 Documentation

### Deployment & Operations
- [Deployment Guide](./docs/DEPLOYMENT.md) - Complete deployment guide
- [Data Isolation](./docs/DATA_ISOLATION.md) - Multi-project security
- [Port Management](./docs/PORT_MANAGEMENT.md) - Handling port conflicts
- [Traefik Setup](./docs/TRAEFIK_SETUP.md) - Zero-conflict deployment

### Development
- [API Documentation](./docs/API.md) - Complete API reference
- [Architecture](./docs/ARCHITECTURE.md) - System design and patterns
- [Contributing Guide](./docs/CONTRIBUTING.md) - Development guidelines
- [Docling Setup](./docs/DOCLING_SETUP.md) - RAG document processing

### Reference
- [PRD](./docs/PRD.md) - Original product specification

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                  │
│  Dashboard │ Tech Radar │ Research │ Knowledge Base │
└────────────────────┬────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────┐
│              Backend (FastAPI)                       │
│  ┌──────────┬──────────┬──────────┬──────────┐     │
│  │  Repos   │  Tech    │ Research │   RAG    │     │
│  │ Service  │ Service  │ Service  │ Service  │     │
│  └──────────┴──────────┴──────────┴──────────┘     │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                  Data Layer                          │
│  ┌──────────────────────────┬──────────┐           │
│  │PostgreSQL (+ pgvector)   │  Redis   │           │
│  └──────────────────────────┴──────────┘           │
└─────────────────────────────────────────────────────┘
```

**Tech Stack:**
- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic
- **Frontend:** React 18, TypeScript 5, Vite 5, Tailwind CSS 3
- **Database:** PostgreSQL 16 (+ pgvector), Redis 7
- **AI/ML:** KnowledgeBeast, Docling, sentence-transformers, OpenAI/Anthropic APIs
- **Infrastructure:** Docker, Docker Compose
- **Monorepo:** KnowledgeBeast library in `libs/knowledgebeast/`

---

## ⚙️ Configuration

### Environment Variables

Key settings in `.env`:

```bash
# Port Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432
REDIS_PORT=6379

# Database
DATABASE_URL=postgresql://commandcenter:changeme@postgres:5432/commandcenter
DB_PASSWORD=changeme

# Security
SECRET_KEY=your-secret-key-here
ENCRYPT_TOKENS=true

# AI APIs (optional)
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key

# GitHub Integration (optional)
GITHUB_TOKEN=your-personal-access-token
```

See [.env.template](./.env.template) for full configuration options.

---

## 🛠️ Development

### Local Development

```bash
# Backend (Python)
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (React)
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Database Migrations

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 🐳 Docker Deployment

### Production

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Using Traefik (Recommended for Multiple Projects)

For zero port conflicts across multiple projects:

```bash
# See detailed setup guide
cat docs/TRAEFIK_SETUP.md

# Quick version
docker-compose -f docker-compose.traefik.yml up -d
# Access at: http://commandcenter.localhost
```

---

## 📊 Use Cases

### 1. Music Tech R&D (Performia)
Track JUCE updates, AI music models, audio processing libraries, spatial audio research.

### 2. AI/ML Research Lab
Monitor LLM releases, track papers, organize experiments, build knowledge base from findings.

### 3. Multi-Project Consultancy
Track client technologies, maintain research across projects, share knowledge across teams.

### 4. Open Source Maintainer
Monitor dependencies, track feature requests, organize roadmap research.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./docs/CONTRIBUTING.md) for:

- Development setup and prerequisites
- Coding standards and style guide
- Testing guidelines
- Pull request process
- Commit message conventions
- Issue templates and guidelines

### Quick Start for Contributors

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/CommandCenter.git
cd CommandCenter

# Set up backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up frontend
cd ../frontend
npm install

# Start development environment
docker compose up -d postgres redis
```

See the full [Contributing Guide](./docs/CONTRIBUTING.md) for detailed instructions.

---

## 📝 License

[MIT License](./LICENSE)

---

## 🔗 Links

- **GitHub:** https://github.com/PerformanceSuite/CommandCenter
- **Issues:** https://github.com/PerformanceSuite/CommandCenter/issues
- **Performia (Parent Project):** https://github.com/PerformanceSuite/Performia

---

## 💡 Examples

### Track a Repository

```bash
curl -X POST http://localhost:8000/api/v1/repositories \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "performancesuite",
    "name": "performia",
    "description": "Music performance system",
    "access_token": "ghp_..."
  }'
```

### Create a Technology

```bash
curl -X POST http://localhost:8000/api/v1/technologies \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "audio",
    "title": "JUCE Framework",
    "vendor": "JUCE",
    "status": "adopted",
    "relevance": "high"
  }'
```

### Query Knowledge Base

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the latest AI music generation models?"}'
```

---

## 🙏 Acknowledgments

Built with inspiration from:
- [ThoughtWorks Technology Radar](https://www.thoughtworks.com/radar)
- [Zalando Tech Radar](https://opensource.zalando.com/tech-radar/)
- Modern R&D management practices

---

## 📧 Support

- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/PerformanceSuite/CommandCenter/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/PerformanceSuite/CommandCenter/discussions)
- 📖 **Documentation:** [docs/](./docs/)

---

**Built by the Performia Team** | [PerformanceSuite](https://github.com/PerformanceSuite)
