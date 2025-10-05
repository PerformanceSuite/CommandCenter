# Port Conflict Quick Start Guide

## The Problem

When you run `docker-compose up` and see:
```
Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**This means:** Another process is already using that port, and Docker **cannot start** your containers.

## The Foolproof Solution (3 Options)

### 🚀 Option 1: Automated Port Checker (Recommended)

Run this script **before** starting Docker Compose:

```bash
./scripts/check-ports.sh
```

The script will:
1. ✅ Check all required ports (8000, 3000, 5432, 6379)
2. ❌ Show which processes are blocking ports
3. 🔧 **Automatically fix conflicts** (choose option 1)

**Example:**
```
🔍 Checking port availability...

✅ Port 8000 (Backend API) is available
❌ Port 3000 (Frontend) is in use
   Process: node (PID: 12345)

Choose an option:
1. Kill conflicting processes automatically  ← Choose this
2. Modify ports in .env file
3. Use Traefik reverse proxy
4. Exit and handle manually
```

### 🔧 Option 2: Change Ports Manually

1. **Copy the template:**
   ```bash
   cp .env.template .env
   ```

2. **Edit `.env` to use different ports:**
   ```bash
   # Change from:
   BACKEND_PORT=8000
   FRONTEND_PORT=3000

   # To (if conflicts):
   BACKEND_PORT=8001
   FRONTEND_PORT=3001
   ```

3. **Restart Docker:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Access at new ports:**
   - Frontend: http://localhost:3001
   - Backend: http://localhost:8001

### 🎯 Option 3: Traefik (Zero Conflicts Forever)

**Best for:** Running multiple Docker projects simultaneously

**Setup once, never worry about ports again:**

See full guide: [docs/TRAEFIK_SETUP.md](docs/TRAEFIK_SETUP.md)

**Quick version:**
1. Set up Traefik (one-time, 10 minutes)
2. Access ALL projects via clean URLs:
   - http://performia.localhost (instead of localhost:3000)
   - http://api.performia.localhost (instead of localhost:8000)
3. Run unlimited projects with **zero port conflicts**

## Common Port Issues

### Port 8000 Already in Use

**Likely culprit:** Another API server (Django, FastAPI, etc.)

**Quick fix:**
```bash
# Find and kill process
lsof -ti :8000 | xargs kill -9

# Or change port in .env
BACKEND_PORT=8001
```

### Port 3000 Already in Use

**Likely culprit:** React/Next.js development server

**Quick fix:**
```bash
# Find and kill
lsof -ti :3000 | xargs kill -9

# Or change port
FRONTEND_PORT=3001
```

### Port 5432 Already in Use

**Likely culprit:** Local PostgreSQL installation

**Quick fix:**
```bash
# Change port (recommended for DB)
POSTGRES_PORT=5433

# Now connect to DB at localhost:5433
```

### Port 6379 Already in Use

**Likely culprit:** Local Redis installation

**Quick fix:**
```bash
REDIS_PORT=6380
```

## Finding What's Using a Port

### macOS/Linux:
```bash
lsof -i :8000
```

### Windows:
```powershell
netstat -ano | findstr :8000
```

### Kill Process on Port:
```bash
# macOS/Linux
lsof -ti :8000 | xargs kill -9

# Or use our script
./scripts/check-ports.sh  # Choose option 1

# Or use npm package
npx kill-port 8000
```

## How Docker Handles Ports

**What Docker Does:**
- Maps container port to host port: `8000:8000`
  - Left side (8000): Port on YOUR computer
  - Right side (8000): Port INSIDE container

**What Docker Does NOT Do:**
- ❌ Automatically find available ports
- ❌ Queue until port is free
- ❌ Warn before overwriting

**Result:** If port is in use → **Container fails to start**

## Environment Variable Port Mapping

This is how Performia handles configurable ports:

**In docker-compose.yml:**
```yaml
services:
  backend:
    ports:
      - "${BACKEND_PORT:-8000}:8000"
      #     ^                ^
      #     |                |
      #  From .env       Container port
      #  (default: 8000)  (fixed)
```

**In .env:**
```bash
BACKEND_PORT=8001  # Now maps 8001 → 8000
```

**Result:** Access backend at http://localhost:8001 (maps to container's port 8000)

## Recommended Workflow

### First Time Setup

1. **Copy environment template:**
   ```bash
   cp .env.template .env
   ```

2. **Check ports before starting:**
   ```bash
   ./scripts/check-ports.sh
   ```

3. **Start services:**
   ```bash
   docker-compose up -d
   ```

### Daily Usage

```bash
# Quick start (with port check)
./scripts/check-ports.sh && docker-compose up -d

# Or create alias
alias dc-start='./scripts/check-ports.sh && docker-compose up -d'
```

### When Conflicts Occur

```bash
# Option A: Let script fix it
./scripts/check-ports.sh  # Choose option 1 to auto-kill

# Option B: Change ports
vim .env  # Modify BACKEND_PORT, FRONTEND_PORT, etc.
docker-compose down && docker-compose up -d

# Option C: Manual kill
lsof -ti :8000 | xargs kill -9
docker-compose up -d
```

## Preventing Conflicts

### 1. Use Port Ranges Per Project

Assign dedicated port ranges:
- **Performia:** 8000-8009
- **Command Center:** 8010-8019
- **Other Project:** 8020-8029

Update `.env`:
```bash
# Performia uses 8000-8009
BACKEND_PORT=8000
FRONTEND_PORT=8001
POSTGRES_PORT=8002
REDIS_PORT=8003
```

### 2. Document Your Ports

Add to your project README:
```markdown
## Port Usage
- 8000: Backend API
- 3000: Frontend
- 5432: PostgreSQL
- 6379: Redis

If ports conflict, edit `.env` file.
```

### 3. Stop Services When Not Using

```bash
# Stop but keep data
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Full cleanup (removes data too)
docker-compose down -v
```

## Advanced: No Port Conflicts Ever

Use Traefik reverse proxy:

```bash
# Setup once
mkdir -p ~/docker-infrastructure/traefik
# ... (see docs/TRAEFIK_SETUP.md for full guide)

# Use clean URLs
http://performia.localhost
http://api.performia.localhost

# Run unlimited projects - zero conflicts!
```

## Debugging Port Issues

### Check Docker Port Mappings

```bash
# See all containers and their ports
docker ps --format "table {{.Names}}\t{{.Ports}}"

# See ports for specific project
docker-compose ps
```

### Check All Listening Ports

```bash
# macOS/Linux
lsof -i -P | grep LISTEN

# Linux (alternative)
netstat -tulpn | grep LISTEN
ss -tulpn

# Windows
netstat -ano | findstr LISTENING
```

### Docker-Specific Issues

**Leftover Docker processes:**
```bash
# Sometimes Docker proxy processes remain
docker system prune -f

# Restart Docker Desktop (macOS/Windows)
# Or restart daemon (Linux)
sudo systemctl restart docker
```

**Network conflicts:**
```bash
docker-compose down
docker network prune -f
docker-compose up -d
```

## Get Help

1. **Check logs:**
   ```bash
   docker-compose logs backend
   ```

2. **Run diagnostics:**
   ```bash
   ./scripts/check-ports.sh
   docker ps -a
   docker network ls
   ```

3. **Read detailed docs:**
   - [docs/PORT_MANAGEMENT.md](docs/PORT_MANAGEMENT.md) - Comprehensive guide
   - [docs/TRAEFIK_SETUP.md](docs/TRAEFIK_SETUP.md) - Zero-conflict solution

4. **GitHub Issues:**
   - [Performia Issues](https://github.com/PerformanceSuite/Performia/issues)

## Summary

| Method | Difficulty | When to Use |
|--------|-----------|-------------|
| **Port Checker Script** | ⭐ Easy | First choice, handles most cases |
| **Edit .env File** | ⭐⭐ Easy | When you want specific ports |
| **Traefik** | ⭐⭐⭐ Moderate | 3+ projects, want zero conflicts |

**Most people should:** Start with the port checker script, and switch to Traefik if you run many projects.

---

**Quick Commands Cheat Sheet:**

```bash
# Check ports before starting
./scripts/check-ports.sh

# Start services
docker-compose up -d

# Stop services
docker-compose down

# Change ports
vim .env  # Edit BACKEND_PORT, FRONTEND_PORT, etc.

# Kill process on port
lsof -ti :8000 | xargs kill -9

# See what's using ports
lsof -i -P | grep LISTEN

# Access services (default ports)
http://localhost:3000  # Frontend
http://localhost:8000  # Backend API
```
