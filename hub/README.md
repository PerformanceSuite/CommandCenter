# CommandCenter Hub

**Multi-project launcher and management interface for CommandCenter**

## What is Hub?

Hub is a lightweight web application that manages multiple CommandCenter instances. Instead of manually running each project's CommandCenter, Hub provides:

- **Dashboard** showing all your projects
- **One-click start/stop** for each CommandCenter instance
- **Project browser** to add existing projects
- **Automatic configuration** and port management
- **Status monitoring** for all instances

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
