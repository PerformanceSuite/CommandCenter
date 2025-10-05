# Port Management & Conflict Resolution

## Overview

Port conflicts are a common issue when running multiple Docker projects. This guide explains how Performia handles port conflicts and provides multiple solutions.

## Quick Fix: Check & Resolve Conflicts

Before starting Docker Compose, run the port checker:

```bash
./scripts/check-ports.sh
```

This script will:
- ✅ Check if all required ports are available
- ❌ Detect conflicts and show which processes are using ports
- 🔧 Offer to automatically kill conflicting processes
- 💡 Suggest alternative port configurations

## How Docker Handles Port Conflicts

When you try to start a container with a port that's already in use, Docker **fails immediately**:

```
Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Docker does NOT:**
- Automatically find an alternative port
- Partially start services
- Queue until ports become available

**The container simply won't start.**

## Solution 1: Environment Variables (Current Setup) ⭐

Performia uses environment variables for flexible port configuration.

### How It Works

1. **Edit your `.env` file** (copy from `.env.template` if needed):

```bash
cp .env.template .env
```

2. **Modify the port variables** if conflicts occur:

```bash
# Default ports
BACKEND_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432
REDIS_PORT=6379

# Example: Changed due to conflicts
BACKEND_PORT=8001
FRONTEND_PORT=3001
POSTGRES_PORT=5433
REDIS_PORT=6380
```

3. **Restart Docker Compose**:

```bash
docker-compose down
docker-compose up -d
```

### Access URLs

After changing ports, access services at:
- Frontend: `http://localhost:${FRONTEND_PORT}` (default: 3000)
- Backend API: `http://localhost:${BACKEND_PORT}` (default: 8000)
- API Docs: `http://localhost:${BACKEND_PORT}/docs`
- PostgreSQL: `localhost:${POSTGRES_PORT}`
- Redis: `localhost:${REDIS_PORT}`

## Solution 2: Traefik Reverse Proxy (Recommended for Multiple Projects) 🚀

If you run many Docker projects, use Traefik to **eliminate port conflicts entirely**.

### Benefits

- ✅ **Zero port conflicts** - only Traefik uses ports 80/443
- ✅ **Clean URLs** - `http://performia.localhost` instead of `http://localhost:8000`
- ✅ **Automatic SSL** (optional)
- ✅ **Works for unlimited projects**

### Setup Traefik (One-Time)

1. **Create Traefik directory**:

```bash
mkdir -p ~/docker-infrastructure/traefik
cd ~/docker-infrastructure/traefik
```

2. **Create `docker-compose.yml`**:

```yaml
name: infrastructure-traefik

services:
  traefik:
    image: traefik:v3.0
    container_name: traefik
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"  # Traefik dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik.yml:/traefik.yml:ro
    networks:
      - web
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.dashboard.rule=Host(`traefik.localhost`)"
      - "traefik.http.routers.dashboard.service=api@internal"

networks:
  web:
    name: web
    attachable: true
```

3. **Create `traefik.yml`**:

```yaml
api:
  dashboard: true
  insecure: true

providers:
  docker:
    exposedByDefault: false
    network: web

entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"
```

4. **Start Traefik**:

```bash
docker-compose up -d
```

5. **Access Traefik Dashboard**: http://traefik.localhost:8080

### Configure Performia to Use Traefik

1. **Create `docker-compose.traefik.yml`** in Performia root:

```yaml
# Use this instead of docker-compose.yml when using Traefik
# Run: docker-compose -f docker-compose.traefik.yml up -d

services:
  postgres:
    # Keep port exposed for direct DB access
    ports:
      - "${POSTGRES_PORT:-5432}:5432"

  redis:
    # Keep port exposed for direct access
    ports:
      - "${REDIS_PORT:-6379}:6379"

  backend:
    # Remove port binding, use Traefik labels
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.performia-backend.rule=Host(`api.performia.localhost`)"
      - "traefik.http.services.performia-backend.loadbalancer.server.port=8000"
      - "traefik.docker.network=web"
    networks:
      - default
      - web

  frontend:
    # Remove port binding, use Traefik labels
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.performia-frontend.rule=Host(`performia.localhost`)"
      - "traefik.http.services.performia-frontend.loadbalancer.server.port=80"
      - "traefik.docker.network=web"
    networks:
      - default
      - web

networks:
  web:
    external: true
  commandcenter:
    driver: bridge
```

2. **Start with Traefik**:

```bash
docker-compose -f docker-compose.traefik.yml up -d
```

3. **Access Services**:
- Frontend: http://performia.localhost
- Backend: http://api.performia.localhost
- API Docs: http://api.performia.localhost/docs
- Traefik Dashboard: http://traefik.localhost:8080

## Solution 3: Manual Port Management

### Find What's Using a Port

**macOS/Linux:**
```bash
lsof -i :8000
```

**Windows:**
```powershell
netstat -ano | findstr :8000
```

### Kill Process on Port

**macOS/Linux:**
```bash
# Find and kill in one command
lsof -ti :8000 | xargs kill -9

# Or use our helper script
./scripts/check-ports.sh  # Option 1 auto-kills
```

**Windows:**
```powershell
# Get PID from netstat output, then:
taskkill /PID <PID> /F
```

### Using npm kill-port

```bash
# Install globally
npm install -g kill-port

# Kill single port
npx kill-port 8000

# Kill multiple ports
npx kill-port 8000 3000 5432
```

## Common Port Conflicts

### Port 8000
**Common culprits:**
- Django development server
- Other FastAPI projects
- Python HTTP servers

**Fix:** Change `BACKEND_PORT=8001` in `.env`

### Port 3000
**Common culprits:**
- React development servers
- Next.js projects
- Node.js apps

**Fix:** Change `FRONTEND_PORT=3001` in `.env`

### Port 5432 (PostgreSQL)
**Common culprits:**
- Local PostgreSQL installation
- Other Docker PostgreSQL containers

**Fix:** Change `POSTGRES_PORT=5433` in `.env`

### Port 6379 (Redis)
**Common culprits:**
- Local Redis installation
- Other Docker Redis containers

**Fix:** Change `REDIS_PORT=6380` in `.env`

### Port 80/443
**Common culprits:**
- Apache/Nginx on host
- Other web servers
- Windows IIS

**Fix:** Don't run services on these ports locally, or use Traefik

## Docker-Specific Issues

### Leftover Docker Proxy Processes

Sometimes Docker leaves proxy processes running even after containers stop.

**Symptoms:**
```bash
docker ps  # Shows no containers
lsof -i :8000  # Shows com.docker.backend still using port
```

**Fix:**
```bash
# Restart Docker Desktop (macOS/Windows)
# Or restart Docker daemon (Linux)
sudo systemctl restart docker
```

### Network Conflicts

If containers can't communicate despite being up:

```bash
# Recreate networks
docker-compose down
docker network prune -f
docker-compose up -d
```

## Best Practices

### 1. Always Use .env Files
- ✅ Keep `.env.template` in git with defaults
- ✅ Add `.env` to `.gitignore`
- ✅ Document port ranges in README

### 2. Use Consistent Port Ranges
Assign port ranges per project:
- Performia: 8000-8009
- Command Center: 8010-8019
- Other Project: 8020-8029

### 3. Document Everything
Update your `.env.template` with comments:

```bash
# Backend API Port
# Default: 8000
# If conflict: Try 8001, 8002, etc.
BACKEND_PORT=8000
```

### 4. Check Before Starting
Always run the port checker before `docker-compose up`:

```bash
./scripts/check-ports.sh && docker-compose up -d
```

Or add to `Makefile`:

```makefile
.PHONY: start
start:
	@./scripts/check-ports.sh
	docker-compose up -d
```

Then use: `make start`

## Troubleshooting

### Ports Still Conflicting After Killing Process

**Cause:** OS may have reserved the port

**Fix (macOS/Linux):**
```bash
# Wait a few seconds for OS to release the port
sleep 5
# Try again
./scripts/check-ports.sh
```

**Fix (Windows):**
```powershell
# Check for port exclusions (requires admin)
netsh interface ipv4 show excludedportrange protocol=tcp

# If port is reserved, add explicit exclusion
netsh int ipv4 add excludedportrange protocol=tcp startport=8000 numberofports=1
```

### Docker Says Port Available But It's Not

**Cause:** Port bound to specific IP, not 0.0.0.0

**Fix:**
```bash
# Check all interfaces
netstat -an | grep 8000

# Or use lsof with all IPs
lsof -i -P | grep 8000
```

### Container Starts But Can't Connect

**Cause:** Firewall blocking the port

**macOS:**
```bash
# Check firewall status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Allow if needed (not usually required for localhost)
```

**Linux:**
```bash
# Check firewall
sudo ufw status
sudo iptables -L
```

## Comparison: Three Approaches

| Feature | Env Variables | Traefik | Override Files |
|---------|--------------|---------|----------------|
| Setup Complexity | ⭐ Easy | ⭐⭐⭐ Moderate | ⭐⭐ Easy |
| Port Conflicts | Still possible | Eliminated | Still possible |
| Multi-Project | Manual ports | Automatic | Manual ports |
| Production-like | No | Yes | No |
| Team-friendly | Yes | Yes | Yes |
| Learning Curve | Minimal | Moderate | Minimal |

**Recommendation:**
- **1-2 projects:** Use environment variables (current setup)
- **3+ projects:** Switch to Traefik
- **Learning Docker:** Start with env variables

## References

- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [Docker Port Binding](https://docs.docker.com/config/containers/container-networking/)

## Get Help

If you're still experiencing port conflicts:

1. Run diagnostic: `./scripts/check-ports.sh`
2. Check Docker status: `docker ps -a`
3. Check networks: `docker network ls`
4. See GitHub issues: [Performia Issues](https://github.com/PerformanceSuite/Performia/issues)
