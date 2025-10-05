# Data Isolation & Security

## ⚠️ CRITICAL: One CommandCenter Instance Per Project

**Each project MUST have its own isolated CommandCenter instance.**

CommandCenter stores sensitive research data, GitHub tokens, and proprietary information. **Never share a single instance across multiple projects** to prevent:

- 🚨 Data leakage between projects
- 🚨 Unauthorized access to repositories
- 🚨 Cross-contamination of knowledge bases
- 🚨 Security token exposure
- 🚨 Regulatory compliance violations

---

## Isolation Architecture

### What Gets Isolated Per Instance

Each CommandCenter instance has completely separate:

1. **Database** - PostgreSQL with unique schema
2. **Vector Store** - ChromaDB with isolated embeddings
3. **RAG Storage** - Docling documents and processed research
4. **Redis Cache** - Session and temporary data
5. **Docker Volumes** - Persistent storage
6. **Container Names** - Unique Docker containers
7. **Networks** - Isolated Docker networks

### Docker Volume Naming

Volumes are automatically namespaced by project:

```bash
# Project: performia-commandcenter
performia-commandcenter_postgres_data
performia-commandcenter_rag_storage
performia-commandcenter_redis_data

# Project: clientx-commandcenter
clientx-commandcenter_postgres_data
clientx-commandcenter_rag_storage
clientx-commandcenter_redis_data
```

**No data sharing possible between volumes.**

---

## Setting Up Multiple Instances

### Recommended Directory Structure

```bash
~/projects/
├── performia/
│   └── commandcenter/          # Clone of CommandCenter repo
│       ├── .env                # COMPOSE_PROJECT_NAME=performia-commandcenter
│       └── docker-compose.yml
│
├── client-x/
│   └── commandcenter/          # Separate clone
│       ├── .env                # COMPOSE_PROJECT_NAME=clientx-commandcenter
│       └── docker-compose.yml
│
└── internal-research/
    └── commandcenter/          # Another separate clone
        ├── .env                # COMPOSE_PROJECT_NAME=internal-commandcenter
        └── docker-compose.yml
```

### Setup Process

For each project:

```bash
# 1. Clone CommandCenter to project directory
cd ~/projects/your-project/
git clone https://github.com/PerformanceSuite/CommandCenter.git commandcenter
cd commandcenter

# 2. Configure with unique project name
cp .env.template .env
nano .env

# 3. Set unique COMPOSE_PROJECT_NAME
COMPOSE_PROJECT_NAME=yourproject-commandcenter

# 4. Set unique ports (if running multiple simultaneously)
BACKEND_PORT=8000    # or 8010, 8020, etc.
FRONTEND_PORT=3000   # or 3010, 3020, etc.
POSTGRES_PORT=5432   # or 5433, 5434, etc.
REDIS_PORT=6379      # or 6380, 6381, etc.

# 5. Set unique SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)

# 6. Start instance
docker-compose up -d
```

---

## Configuration Examples

### Example 1: Performia Project

```bash
# ~/projects/performia/commandcenter/.env
COMPOSE_PROJECT_NAME=performia-commandcenter

# Unique ports
BACKEND_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432
REDIS_PORT=6379

# Unique secret
SECRET_KEY=abc123...performia-specific

# Project-specific API keys
GITHUB_TOKEN=ghp_performia_token
ANTHROPIC_API_KEY=sk-ant-performia-key
```

### Example 2: Client X Project

```bash
# ~/projects/client-x/commandcenter/.env
COMPOSE_PROJECT_NAME=clientx-commandcenter

# Different ports (if running simultaneously)
BACKEND_PORT=8010
FRONTEND_PORT=3010
POSTGRES_PORT=5433
REDIS_PORT=6380

# Different secret
SECRET_KEY=xyz789...clientx-specific

# Client-specific API keys
GITHUB_TOKEN=ghp_clientx_token
ANTHROPIC_API_KEY=sk-ant-clientx-key
```

### Example 3: Internal Research

```bash
# ~/projects/internal/commandcenter/.env
COMPOSE_PROJECT_NAME=internal-commandcenter

# Different ports again
BACKEND_PORT=8020
FRONTEND_PORT=3020
POSTGRES_PORT=5434
REDIS_PORT=6381

# Different secret
SECRET_KEY=def456...internal-specific

# Internal API keys
GITHUB_TOKEN=ghp_internal_token
ANTHROPIC_API_KEY=sk-ant-internal-key
```

---

## Running Multiple Instances

### Sequential (One at a Time)

```bash
# Stop current instance
cd ~/projects/performia/commandcenter
docker-compose down

# Start different instance
cd ~/projects/client-x/commandcenter
docker-compose up -d
```

### Concurrent (Multiple Running)

**Requirements:**
- Unique `COMPOSE_PROJECT_NAME` for each
- Unique ports for each
- Sufficient system resources

```bash
# Start Performia instance
cd ~/projects/performia/commandcenter
docker-compose up -d
# Access: http://localhost:3000

# Start Client X instance
cd ~/projects/client-x/commandcenter
docker-compose up -d
# Access: http://localhost:3010

# Start Internal instance
cd ~/projects/internal/commandcenter
docker-compose up -d
# Access: http://localhost:3020
```

### Using Traefik (Recommended for Multiple Instances)

Eliminates port conflicts entirely:

```bash
# Performia: http://performia-cc.localhost
# Client X:  http://clientx-cc.localhost
# Internal:  http://internal-cc.localhost
```

See [TRAEFIK_SETUP.md](./TRAEFIK_SETUP.md) for configuration.

---

## Verification

### Check Isolation

```bash
# List all CommandCenter volumes
docker volume ls | grep commandcenter

# Should see separate volumes per project:
# performia-commandcenter_postgres_data
# performia-commandcenter_rag_storage
# clientx-commandcenter_postgres_data
# clientx-commandcenter_rag_storage
```

### Verify Container Names

```bash
# List running containers
docker ps --filter name=commandcenter

# Should see unique names:
# performia-commandcenter_backend
# performia-commandcenter_frontend
# clientx-commandcenter_backend
# clientx-commandcenter_frontend
```

### Verify Network Isolation

```bash
# Inspect networks
docker network ls | grep commandcenter

# Each project has its own network:
# performia-commandcenter_commandcenter
# clientx-commandcenter_commandcenter
```

---

## Security Best Practices

### 1. Never Share Credentials

Each instance must have:
- ✅ Unique `SECRET_KEY`
- ✅ Unique `DB_PASSWORD`
- ✅ Project-specific `GITHUB_TOKEN`
- ✅ Project-specific API keys

### 2. Never Share Volumes

```bash
# ❌ WRONG - Sharing volumes
volumes:
  - /shared/postgres:/var/lib/postgresql/data

# ✅ CORRECT - Named Docker volumes (auto-isolated)
volumes:
  - postgres_data:/var/lib/postgresql/data
```

### 3. Never Share Databases

```bash
# ❌ WRONG - Multiple projects using same database
DATABASE_URL=postgresql://user:pass@shared-db:5432/shared_db

# ✅ CORRECT - Each project has its own database container
# Defined per-project in docker-compose.yml
```

### 4. Audit Access

```bash
# Check which repositories each instance tracks
cd ~/projects/performia/commandcenter
docker-compose exec backend python -c "
from app.database import SessionLocal
from app.models import Repository
db = SessionLocal()
repos = db.query(Repository).all()
for r in repos:
    print(f'{r.owner}/{r.name}')
"
```

---

## Data Migration & Backup

### Backing Up Instance Data

```bash
# Backup specific instance
cd ~/projects/performia/commandcenter

# Database backup
docker-compose exec -T postgres pg_dump -U commandcenter commandcenter > backup-db.sql

# RAG storage backup
docker run --rm -v performia-commandcenter_rag_storage:/data -v $(pwd):/backup \
  alpine tar czf /backup/rag-storage.tar.gz /data

# Full backup
make db-backup  # If using Makefile
```

### Migrating Between Instances

**Never directly copy data between instances.** If you need to move repositories:

1. Export from source instance via API
2. Import to target instance via API
3. Re-sync repositories to rebuild RAG

```bash
# Export repositories from source
curl http://localhost:8000/api/v1/repositories > repos.json

# Import to target (after editing project-specific fields)
curl -X POST http://localhost:8010/api/v1/repositories -d @repos.json
```

---

## Compliance Considerations

### Multi-Tenant Scenarios

If running CommandCenter for multiple clients:

- ✅ Each client MUST have separate instance
- ✅ Use different servers/VMs for high-sensitivity clients
- ✅ Implement network segmentation
- ✅ Regular security audits
- ✅ Encrypted backups with separate keys

### Regulatory Requirements

Depending on your industry:

**Healthcare (HIPAA):**
- Encrypt all volumes
- Audit logging enabled
- Access controls per instance

**Finance (SOC 2):**
- Separate instances per customer
- Encrypted at-rest and in-transit
- Regular penetration testing

**Government:**
- Air-gapped instances
- No cloud API keys
- Physical security controls

---

## Troubleshooting Isolation Issues

### Problem: Data Appearing in Wrong Instance

**Cause:** Shared `COMPOSE_PROJECT_NAME`

**Fix:**
```bash
# Check current project name
docker-compose config | grep name

# Change to unique name in .env
COMPOSE_PROJECT_NAME=unique-project-name

# Recreate containers
docker-compose down
docker-compose up -d
```

### Problem: Container Name Conflicts

**Cause:** Multiple instances with same project name

**Fix:**
```bash
# Stop all instances
docker stop $(docker ps -q --filter name=commandcenter)

# Fix .env in each instance
# Ensure each has unique COMPOSE_PROJECT_NAME

# Restart one by one
```

### Problem: Port Conflicts

**Cause:** Multiple instances using same ports

**Fix:**
Use unique ports in each `.env`:
```bash
# Instance 1
BACKEND_PORT=8000

# Instance 2
BACKEND_PORT=8010

# Instance 3
BACKEND_PORT=8020
```

Or use Traefik (see [TRAEFIK_SETUP.md](./TRAEFIK_SETUP.md))

---

## Summary Checklist

Before deploying a new CommandCenter instance:

- [ ] Clone to project-specific directory
- [ ] Set unique `COMPOSE_PROJECT_NAME` in `.env`
- [ ] Generate new `SECRET_KEY`
- [ ] Set unique `DB_PASSWORD`
- [ ] Use project-specific `GITHUB_TOKEN`
- [ ] Configure unique ports (if running multiple)
- [ ] Verify no volume name collisions
- [ ] Test data isolation
- [ ] Document which repos this instance tracks
- [ ] Set up backup procedures

---

## Getting Help

- Security Concerns: [Open a private security issue](https://github.com/PerformanceSuite/CommandCenter/security/advisories/new)
- General Questions: [GitHub Discussions](https://github.com/PerformanceSuite/CommandCenter/discussions)
- Bug Reports: [GitHub Issues](https://github.com/PerformanceSuite/CommandCenter/issues)

---

**Remember:** One CommandCenter instance = One project's data. Never share instances across projects with different security requirements.
