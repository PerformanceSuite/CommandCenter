# CommandCenter Hub

Multi-project management interface for CommandCenter instances.

## Features

- **Project Management**: Create, start, stop, delete CommandCenter instances
- **Port Isolation**: Automatic port allocation to avoid conflicts
- **Background Tasks**: Non-blocking project operations with Celery
- **Real-time Progress**: Live progress updates for long-running operations
- **Monitoring Dashboard**: Celery Flower for task/worker monitoring
- **Folder Browser**: Select project directories visually
- **Status Tracking**: Real-time project status (stopped/starting/running/error)

## Quick Start

```bash
# Start Hub
cd hub
docker-compose up -d

# Access Hub
open http://localhost:9000
```

## Architecture

```
Hub (Port 9000/9001)
├── Dashboard - List all projects
├── Add Project - Browse to existing project folder
├── Start/Stop - Control CommandCenter instances
└── Status - Monitor health of all instances

Managed CommandCenter Instances:
├── Performia        (Port 8000, 3000)
├── AI Research      (Port 8010, 3010)
└── E-commerce       (Port 8020, 3020)
```

## Features

- ✅ **Add Existing Projects** - Browse filesystem to select project folder
- ✅ **Auto-Configuration** - Generates `.env` with unique ports
- ✅ **Docker Management** - Start/stop CommandCenter via docker-compose
- ✅ **Health Monitoring** - Real-time status of all instances
- ✅ **Port Management** - Auto-assigns non-conflicting ports
- ✅ **VIZTRTR Design** - Beautiful dark slate UI

## Configuration

### Environment Variables

Hub backend can be configured with the following environment variables:

**PROJECTS_ROOT** (optional)
- Default: `~/Projects` (expands to user's home directory)
- Purpose: Root directory where projects are located
- Example: `PROJECTS_ROOT=/Users/yourname/workspace`
- Used for Docker volume mount path translation

**Database Configuration**
- `DATABASE_URL` - SQLite database path (default: `sqlite:///./hub.db`)

**Port Configuration**
- Backend runs on port `9001` (configurable in `docker-compose.yml`)
- Frontend runs on port `9000` (configurable in `docker-compose.yml`)
- Managed projects auto-assign ports starting from `8000/3000` incrementing by 10

### Docker Compose Services

Hub starts only essential services for managed projects to avoid port conflicts:
- `backend` - FastAPI server
- `frontend` - React app
- `postgres` - Database
- `redis` - Cache/queue

Optional services (excluded by default):
- `flower` - Celery monitoring (port 5555)
- `prometheus` - Metrics collection (port 9090)
- `celery` - Background worker

To include optional services, modify `ESSENTIAL_SERVICES` in `hub/backend/app/services/orchestration_service.py`.

## Development

### Backend (FastAPI)
```bash
cd hub/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 9001
```

### Frontend (React + Vite)
```bash
cd hub/frontend
npm install
npm run dev  # Port 9000
```

## Usage

### 1. Add a Project

1. Click "+ Add Project" on Hub dashboard
2. Browse to your project folder (e.g., `/Users/you/performia/`)
3. Hub creates `commandcenter/` subdirectory
4. Automatically clones CC, configures ports, starts services

### 2. Manage Projects

- **Start** - Spins up CommandCenter instance
- **Stop** - Gracefully stops all services
- **Open** - Opens CommandCenter UI in browser
- **View Logs** - See docker-compose logs

### 3. View Status

Each project card shows:
- Running status (green dot = running)
- Repository count
- Technology count
- Health status

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Docker SDK
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Database**: SQLite (project registry)
- **Orchestration**: Docker Compose

## Design System

Uses VIZTRTR color palette:
- Dark slate backgrounds (#0f172a, #1e293b)
- Blue primary buttons (#3b82f6)
- Status colors (green, yellow, red)
- Glow effects for active states

---

**Built for the PerformanceSuite ecosystem**
