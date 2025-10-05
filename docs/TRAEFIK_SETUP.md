# Traefik Setup for Multiple Projects (Advanced)

## What is Traefik?

Traefik is a modern reverse proxy that **eliminates port conflicts** when running multiple Docker projects.

### The Problem It Solves

**Without Traefik:**
```
Project A: http://localhost:8000 ❌
Project B: http://localhost:8001 ❌
Project C: http://localhost:8002 ❌
```
- Hard to remember ports
- Port conflicts common
- Manual port management
- Bookmarks break when ports change

**With Traefik:**
```
Project A: http://projecta.localhost ✅
Project B: http://projectb.localhost ✅
Project C: http://projectc.localhost ✅
```
- Clean, memorable URLs
- Zero port conflicts
- Automatic routing
- Production-like setup

## When to Use Traefik

✅ **Use Traefik if you:**
- Run 3+ Docker projects simultaneously
- Want production-like local environment
- Need SSL/HTTPS locally
- Work on microservices architecture
- Frequently switch between projects

❌ **Stick with ports if you:**
- Only run 1-2 projects
- Prefer simplicity
- Don't need SSL locally
- Are new to Docker

## Installation (One-Time Setup)

### Step 1: Create Traefik Infrastructure

```bash
# Create directory
mkdir -p ~/docker-infrastructure/traefik
cd ~/docker-infrastructure/traefik
```

### Step 2: Create docker-compose.yml

```bash
cat > docker-compose.yml << 'EOF'
name: infrastructure-traefik

services:
  traefik:
    image: traefik:v3.0
    container_name: traefik
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    ports:
      - "80:80"      # HTTP
      - "443:443"    # HTTPS
      - "8080:8080"  # Dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik.yml:/traefik.yml:ro
      - ./certs:/certs  # For SSL certificates
    networks:
      - web
    labels:
      - "traefik.enable=true"
      # Dashboard
      - "traefik.http.routers.dashboard.rule=Host(`traefik.localhost`)"
      - "traefik.http.routers.dashboard.service=api@internal"
      - "traefik.http.routers.dashboard.entrypoints=web"

networks:
  web:
    name: web
    attachable: true
EOF
```

### Step 3: Create traefik.yml Configuration

```bash
cat > traefik.yml << 'EOF'
# API and Dashboard
api:
  dashboard: true
  insecure: true  # Dashboard accessible without auth on localhost

# Docker Provider
providers:
  docker:
    exposedByDefault: false  # Only route containers with traefik.enable=true
    network: web             # Use 'web' network for routing

# Entry Points
entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

# Logging
log:
  level: INFO

# Access Logs (optional)
accessLog:
  filePath: "/var/log/traefik/access.log"
EOF
```

### Step 4: Start Traefik

```bash
docker-compose up -d
```

### Step 5: Verify Installation

1. **Check Traefik is running:**
```bash
docker ps | grep traefik
```

2. **Access dashboard:**
http://traefik.localhost:8080

You should see the Traefik dashboard with no routers yet.

## Configure Performia to Use Traefik

### Option A: Create Traefik-Specific Compose File

Create `docker-compose.traefik.yml` in Performia root:

```yaml
# Performia with Traefik Routing
# Usage: docker-compose -f docker-compose.traefik.yml up -d

name: performia

services:
  postgres:
    image: postgres:16-alpine
    container_name: performia_db
    environment:
      POSTGRES_DB: commandcenter
      POSTGRES_USER: commandcenter
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    # Keep port for direct DB access
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U commandcenter"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - performia

  redis:
    image: redis:7-alpine
    container_name: performia_redis
    # Keep port for direct access
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - performia

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: performia_backend
    environment:
      DATABASE_URL: postgresql://commandcenter:${DB_PASSWORD:-changeme}@postgres:5432/commandcenter
      SECRET_KEY: ${SECRET_KEY}
      RAG_STORAGE_PATH: /app/rag_storage
      CHROMADB_PATH: /app/rag_storage/chromadb
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      GITHUB_TOKEN: ${GITHUB_TOKEN}
      SLACK_TOKEN: ${SLACK_TOKEN:-}
      REDIS_URL: redis://redis:6379
    volumes:
      - rag_storage:/app/rag_storage
      - ./backend/output:/app/output
    # NO port binding - Traefik handles it
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.performia-backend.rule=Host(`api.performia.localhost`)"
      - "traefik.http.services.performia-backend.loadbalancer.server.port=8000"
      - "traefik.docker.network=web"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - performia
      - web

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production
    container_name: performia_frontend
    environment:
      # Frontend now calls backend via Traefik
      VITE_API_URL: http://api.performia.localhost
    # NO port binding - Traefik handles it
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.performia-frontend.rule=Host(`performia.localhost`)"
      - "traefik.http.services.performia-frontend.loadbalancer.server.port=80"
      - "traefik.docker.network=web"
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - performia
      - web

volumes:
  postgres_data:
    driver: local
  rag_storage:
    driver: local
  redis_data:
    driver: local

networks:
  performia:
    driver: bridge
  web:
    external: true  # Created by Traefik
```

### Option B: Use Docker Compose Override

1. **Keep `docker-compose.yml` as-is** (with ports for non-Traefik use)

2. **Create `docker-compose.override.yml`** (gitignored):

```yaml
# This file is automatically merged with docker-compose.yml
# Add it to .gitignore so each developer can customize

services:
  backend:
    ports: []  # Remove port binding
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.performia-backend.rule=Host(`api.performia.localhost`)"
      - "traefik.http.services.performia-backend.loadbalancer.server.port=8000"
      - "traefik.docker.network=web"
    networks:
      - commandcenter
      - web

  frontend:
    ports: []  # Remove port binding
    environment:
      VITE_API_URL: http://api.performia.localhost
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.performia-frontend.rule=Host(`performia.localhost`)"
      - "traefik.http.services.performia-frontend.loadbalancer.server.port=80"
      - "traefik.docker.network=web"
    networks:
      - commandcenter
      - web

networks:
  web:
    external: true
```

## Usage

### Starting Services

**With separate Traefik file:**
```bash
docker-compose -f docker-compose.traefik.yml up -d
```

**With override file:**
```bash
# Docker automatically merges docker-compose.yml + docker-compose.override.yml
docker-compose up -d
```

### Accessing Services

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://performia.localhost | Main application |
| Backend API | http://api.performia.localhost | API endpoints |
| API Docs | http://api.performia.localhost/docs | Swagger/OpenAPI |
| Traefik Dashboard | http://traefik.localhost:8080 | Router status |
| PostgreSQL | localhost:5432 | Direct DB access |
| Redis | localhost:6379 | Direct cache access |

### Stopping Services

```bash
docker-compose down
```

## Adding More Projects

For each new project, just add labels:

```yaml
# ~/projects/another-project/docker-compose.yml
services:
  web:
    image: nginx
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myproject.rule=Host(`myproject.localhost`)"
      - "traefik.http.services.myproject.loadbalancer.server.port=80"
    networks:
      - default
      - web

networks:
  web:
    external: true
```

Access at: http://myproject.localhost

**No port conflicts, ever!**

## Advanced Features

### HTTPS with Self-Signed Certificates

1. **Generate certificate:**
```bash
cd ~/docker-infrastructure/traefik
mkdir -p certs

# Generate self-signed cert
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/localhost.key \
  -out certs/localhost.crt \
  -subj "/CN=*.localhost"
```

2. **Update traefik.yml:**
```yaml
entryPoints:
  websecure:
    address: ":443"
    http:
      tls:
        certificates:
          - certFile: /certs/localhost.crt
            keyFile: /certs/localhost.key
```

3. **Update labels to use HTTPS:**
```yaml
labels:
  - "traefik.http.routers.performia.entrypoints=websecure"
  - "traefik.http.routers.performia.tls=true"
```

Access at: https://performia.localhost

### Authentication for Services

Add basic auth to protect services:

```yaml
labels:
  - "traefik.http.routers.performia.middlewares=auth"
  - "traefik.http.middlewares.auth.basicauth.users=admin:$$apr1$$hash$$here"
```

Generate password hash:
```bash
htpasswd -nb admin password
```

### Custom Domains (No .localhost)

Use wildcard DNS services:

**Option 1: traefik.me**
```yaml
- "traefik.http.routers.performia.rule=Host(`performia.traefik.me`)"
```
Access at: http://performia.traefik.me

**Option 2: nip.io**
```yaml
- "traefik.http.routers.performia.rule=Host(`performia.127.0.0.1.nip.io`)"
```
Access at: http://performia.127.0.0.1.nip.io

**Option 3: /etc/hosts**
```bash
sudo nano /etc/hosts

# Add:
127.0.0.1 performia.local
127.0.0.1 api.performia.local
```

Then use:
```yaml
- "traefik.http.routers.performia.rule=Host(`performia.local`)"
```

## Troubleshooting

### 404 Not Found

**Cause:** Traefik can't find the container

**Fix:**
1. Check container is on `web` network:
```bash
docker network inspect web
```

2. Check Traefik dashboard for routers: http://traefik.localhost:8080

3. Verify labels are correct:
```bash
docker inspect performia_backend | grep -A 10 Labels
```

### Gateway Timeout

**Cause:** Container not responding

**Fix:**
1. Check container health:
```bash
docker ps
docker logs performia_backend
```

2. Verify internal port in labels matches container port:
```yaml
- "traefik.http.services.performia.loadbalancer.server.port=8000"
# Must match the port the app listens on INSIDE the container
```

### Traefik Can't Connect to Docker

**Error:** `Cannot create service: error while dialing`

**Fix:**
```bash
# Linux: Add user to docker group
sudo usermod -aG docker $USER

# macOS/Windows: Restart Docker Desktop
```

### Browser Doesn't Resolve .localhost

**Cause:** Some browsers don't support .localhost TLD

**Fix:**
1. Use Chrome/Firefox (both support .localhost natively)
2. Or use traefik.me / nip.io instead
3. Or add to /etc/hosts

## Performance Considerations

### Overhead

Traefik adds ~1-5ms latency for routing. Negligible for local development.

### Resource Usage

- **CPU:** ~0.5% idle, ~2% under load
- **Memory:** ~100MB
- **Disk:** <1GB

## Maintenance

### Update Traefik

```bash
cd ~/docker-infrastructure/traefik
docker-compose pull
docker-compose up -d
```

### View Logs

```bash
docker logs traefik -f
```

### Backup Configuration

```bash
cd ~/docker-infrastructure/traefik
tar -czf traefik-backup-$(date +%Y%m%d).tar.gz .
```

## Comparison: Ports vs Traefik

| Aspect | Port-Based | Traefik-Based |
|--------|-----------|---------------|
| Setup Time | 5 min | 30 min |
| Port Conflicts | Frequent | Never |
| URLs | localhost:8000 | performia.localhost |
| Multi-Project | Manual ports | Automatic |
| SSL/HTTPS | Complex | Easy |
| Production Parity | Low | High |
| Learning Curve | Easy | Moderate |
| Ongoing Maintenance | High | Low |

## Migration Checklist

Migrating from port-based to Traefik:

- [ ] Install Traefik globally
- [ ] Test Traefik dashboard accessible
- [ ] Create `docker-compose.traefik.yml` for each project
- [ ] Add `web` network to all services
- [ ] Add Traefik labels to services
- [ ] Remove or comment out port bindings
- [ ] Update frontend to use new API URL
- [ ] Test each project individually
- [ ] Update documentation/bookmarks
- [ ] Add to team setup guide

## Team Adoption

### For Teams

1. **Document the setup** in your README
2. **Create setup script:**

```bash
#!/bin/bash
# setup-traefik.sh

echo "Setting up Traefik..."

# Create infrastructure directory
mkdir -p ~/docker-infrastructure/traefik
cd ~/docker-infrastructure/traefik

# Copy files from repository
cp scripts/traefik/* .

# Start Traefik
docker-compose up -d

echo "✅ Traefik running at http://traefik.localhost:8080"
```

3. **Make it optional:**
   - Keep `docker-compose.yml` working with ports
   - Provide `docker-compose.traefik.yml` as opt-in
   - Document both approaches

### Onboarding Docs

```markdown
## Local Development

### Option 1: Port-Based (Simpler)
```bash
docker-compose up -d
# Access at http://localhost:3000
```

### Option 2: Traefik (Advanced)
```bash
# One-time setup
./scripts/setup-traefik.sh

# Start project
docker-compose -f docker-compose.traefik.yml up -d
# Access at http://performia.localhost
```
```

## References

- [Official Traefik Docs](https://doc.traefik.io/traefik/)
- [Traefik Docker Provider](https://doc.traefik.io/traefik/providers/docker/)
- [Traefik Routing Docs](https://doc.traefik.io/traefik/routing/routers/)

## Get Help

- Traefik Community: https://community.traefik.io/
- Performia Issues: https://github.com/PerformanceSuite/Performia/issues

---

**Next Steps:** After setting up Traefik, see [PORT_MANAGEMENT.md](./PORT_MANAGEMENT.md) for comprehensive port handling strategies.
