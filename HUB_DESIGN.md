# CommandCenter Hub - Design Document

**Created**: 2025-10-14
**Purpose**: Multi-project launcher and management interface for CommandCenter

---

## 🎯 Vision

A lightweight web application that:
1. **Lists all CommandCenter projects** (Performia, AI Research, etc.)
2. **Shows status** of each project (running/stopped, health, stats)
3. **Starts/stops** individual CommandCenter instances
4. **Creates new projects** with wizard-guided setup
5. **Manages ports/resources** automatically (no conflicts)

---

## 🏗️ Architecture

### Simple 3-Tier Design

```
┌─────────────────────────────────────────┐
│     Hub Frontend (React)                │
│     Port: 9000                          │
│  - Project list dashboard               │
│  - Start/Stop buttons                   │
│  - "Create New Project" wizard          │
│  - Direct links to each CC instance     │
└──────────────┬──────────────────────────┘
               │ REST API
┌──────────────▼──────────────────────────┐
│     Hub Backend (FastAPI)               │
│     Port: 9001                          │
│  - Project CRUD operations              │
│  - Dagger SDK orchestration             │
│  - Health checks for CC instances       │
│  - Port allocation management           │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Project Registry (SQLite)           │
│  - project_name                         │
│  - path                                 │
│  - ports (backend, frontend, db)        │
│  - status (running/stopped)             │
│  - last_started, created_at             │
└─────────────────────────────────────────┘
```

### CommandCenter Instances (Managed via Dagger)

```
Hub manages multiple CC instances (no cloning required):

├── ~/performia/                        (Port 8000, 3000)
├── ~/ai-research/                      (Port 8010, 3010)
├── ~/ecommerce/                        (Port 8020, 3020)
└── ~/new-project/                      (Port 8030, 3030)

CommandCenter stack defined once in hub/backend/app/dagger_modules/commandcenter.py
Projects mount their folders into containers - no template cloning needed
```

---

## 📋 Features

### Phase 1: MVP (Launch & Manage)
- [ ] List all registered projects
- [ ] Show project status (running/stopped)
- [ ] Start/stop individual projects
- [ ] View basic stats (repos, techs, tasks count)
- [ ] Direct links to each CommandCenter UI

### Phase 2: Project Creation
- [ ] "Create New Project" wizard
  - Project name input
  - Project directory selection
  - Auto-generate unique ports
  - No cloning needed (Dagger mounts project folder)
  - Configuration stored in Hub database
- [ ] Start project immediately after creation

### Phase 3: Advanced Management
- [ ] Edit project settings (rename, change ports)
- [ ] Delete projects (with confirmation)
- [ ] View logs from each project
- [ ] Resource usage monitoring (CPU, memory, disk)
- [ ] Bulk operations (start all, stop all)

### Phase 4: Nice-to-Have
- [ ] Import existing CommandCenter instances
- [ ] Export project configurations
- [ ] Health checks with alerts
- [ ] Auto-restart on failure
- [ ] Traefik integration (zero port conflicts)

---

## 🗄️ Data Model

### Project Registry

```python
class Project(BaseModel):
    id: int
    name: str                    # "Performia", "AI Research"
    slug: str                    # "performia", "ai-research"
    path: str                    # "/Users/you/performia" (project folder, not CC path)

    # Ports
    backend_port: int            # 8000, 8010, 8020...
    frontend_port: int           # 3000, 3010, 3020...
    postgres_port: int           # 5432, 5433, 5434...
    redis_port: int              # 6379, 6380, 6381...

    # Status
    status: str                  # "running", "stopped", "error"
    health: str                  # "healthy", "unhealthy", "unknown"
    last_started: datetime
    last_stopped: datetime

    # Stats (cached from CC API)
    repo_count: int
    tech_count: int
    task_count: int

    created_at: datetime
    updated_at: datetime
```

---

## 🔧 Implementation

### Hub Backend (FastAPI)

**File Structure:**
```
hub/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── routers/
│   │   │   ├── projects.py      # CRUD for projects
│   │   │   └── orchestration.py # Start/stop operations
│   │   ├── services/
│   │   │   ├── orchestration_service.py # Dagger orchestration
│   │   │   ├── port_service.py   # Port allocation
│   │   │   └── health_service.py # Health checks
│   │   └── dagger_modules/
│   │       └── commandcenter.py  # Dagger stack definition
│   ├── database.py
│   ├── requirements.txt
│   └── Dockerfile
```

**Key APIs:**
```python
# Projects
GET    /api/projects              # List all projects
POST   /api/projects              # Create new project
GET    /api/projects/{id}         # Get project details
PATCH  /api/projects/{id}         # Update project
DELETE /api/projects/{id}         # Delete project

# Orchestration
POST   /api/projects/{id}/start   # Start CommandCenter
POST   /api/projects/{id}/stop    # Stop CommandCenter
POST   /api/projects/{id}/restart # Restart CommandCenter
GET    /api/projects/{id}/health  # Health check
GET    /api/projects/{id}/logs    # Get logs

# System
GET    /api/ports/available       # Get next available port set
POST   /api/setup/detect          # Auto-detect existing CC instances
```

### Hub Frontend (React)

**Components:**
```
hub/
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── ProjectCard.tsx       # Project status card
    │   │   ├── ProjectList.tsx       # Grid of project cards
    │   │   ├── CreateProjectModal.tsx # New project wizard
    │   │   ├── ProjectDetailsModal.tsx
    │   │   └── Header.tsx
    │   ├── pages/
    │   │   └── Dashboard.tsx         # Main hub page
    │   ├── services/
    │   │   └── api.ts                # API client
    │   └── App.tsx
    ├── package.json
    └── vite.config.ts
```

**UI Mockup:**

```
┌─────────────────────────────────────────────────────────────┐
│  CommandCenter Hub                          [+ New Project]  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 🎵 Performia │  │ 🤖 AI Rsrch  │  │ 🛒 Ecommerce │      │
│  │              │  │              │  │              │      │
│  │ ● Running    │  │ ○ Stopped    │  │ ● Running    │      │
│  │ 5 repos      │  │ 12 repos     │  │ 3 repos      │      │
│  │ 15 techs     │  │ 25 techs     │  │ 8 techs      │      │
│  │              │  │              │  │              │      │
│  │ [Stop] [Open]│  │ [Start] [Open│  │ [Stop] [Open]│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start Commands

### For Users

```bash
# Install Hub (one-time)
npm install -g commandcenter-hub

# Start Hub
cc-hub start

# Access Hub
open http://localhost:9000

# Create new project (via UI wizard or CLI)
cc-hub create performia --path ~/performia

# Start project
cc-hub start performia

# Open project
cc-hub open performia  # Opens browser to http://localhost:3000
```

### Development

```bash
# Clone Hub repo
git clone https://github.com/PerformanceSuite/CommandCenterHub
cd CommandCenterHub

# Start Hub backend
cd hub/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 9001

# Start Hub frontend
cd hub/frontend
npm install
npm run dev  # Port 9000
```

---

## 🔐 Security Considerations

1. **Isolation**: Each CC instance has its own database/volumes
2. **Secrets**: Hub never stores CC secrets (only paths/ports)
3. **Docker Access**: Hub needs Docker socket access (`/var/run/docker.sock`)
4. **Port Conflicts**: Hub checks ports before allocation
5. **Path Validation**: Sanitize project paths to prevent traversal attacks

---

## 📦 Deployment

### Docker Compose (Recommended)

```yaml
# hub/docker-compose.yml
version: '3.8'

services:
  hub-backend:
    build: ./backend
    ports:
      - "9001:9001"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Docker control
      - ./data:/app/data                           # Project registry
      - ~/Projects:/projects:ro                    # Access to CC instances
    environment:
      - DATABASE_URL=sqlite:///data/hub.db

  hub-frontend:
    build: ./frontend
    ports:
      - "9000:80"
    depends_on:
      - hub-backend
```

**Start Hub:**
```bash
cd hub
docker-compose up -d
```

---

## 🎯 Success Metrics

Hub is successful when:
- ✅ Creating a new project takes < 2 minutes
- ✅ No manual `.env` editing required
- ✅ Zero port conflicts
- ✅ All projects visible from one dashboard
- ✅ Start/stop works reliably
- ✅ Health status is accurate

---

## 📝 Next Steps

1. **Create Hub skeleton** (FastAPI + React scaffolding)
2. **Implement Dagger SDK orchestration** (start/stop logic)
3. **Build project registry** (SQLite database)
4. **Create wizard UI** (new project creation)
5. **Add health checks** (poll CC instances)
6. **Polish & document** (README, screenshots)

---

## 🤔 Open Questions

1. **Where should Hub live?**
   - Option A: Separate repo (`CommandCenterHub`)
   - Option B: Subdirectory in CommandCenter (`hub/`)
   - **Recommendation**: Separate repo for clarity

2. **CLI vs Web-only?**
   - Option A: Web UI only
   - Option B: Add CLI tool (`cc-hub`)
   - **Recommendation**: Both (Web is MVP, CLI later)

3. **Auto-discovery?**
   - Should Hub auto-detect existing CC instances?
   - **Recommendation**: Yes, via "Import Existing" feature

---

**Ready to build!** 🚀

Let me know if you want to adjust anything before we start implementing.
