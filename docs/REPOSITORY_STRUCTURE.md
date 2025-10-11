# Repository Structure Guide

**Last Updated**: 2025-10-11

## Overview

This document explains the CommandCenter repository structure and why files are organized the way they are.

---

## Root Directory Structure

```
CommandCenter/
├── .claude/                    # Claude Code configuration
├── .env                        # Environment config (gitignored) ✅
├── .env.template               # Environment template ✅
├── .env.prod.template          # Production env template ✅
├── .gitignore                  # Git ignore rules
├── backend/                    # FastAPI backend
├── CLAUDE.md                   # Claude Code instructions ✅
├── docker-compose.yml          # Development orchestration ✅
├── docker-compose.prod.yml     # Production orchestration ✅
├── docs/                       # All documentation
├── frontend/                   # React frontend
├── Makefile                    # Build automation ✅
├── monitoring/                 # Prometheus/Grafana
├── README.md                   # Project readme ✅
├── scripts/                    # Operational scripts ✅
├── SECURITY.md                 # Security policy ✅
└── traefik/                    # Reverse proxy config
```

---

## Why `.env` Templates Are in Root

### Rationale:

**1. Docker Compose Convention**
- Docker Compose looks for `.env` in the **same directory** as `docker-compose.yml`
- This is hardcoded behavior - cannot be changed without `-f` flags
- Standard practice across the Docker ecosystem

**2. Makefile Dependency**
```bash
# Makefile references .env.template in root
setup:
    cp .env.template .env
```

**3. Industry Standard**
Every major Docker project keeps `.env` templates in root:
- [Docker's Official Examples](https://github.com/docker/awesome-compose)
- GitLab, WordPress, Nextcloud, etc.

**4. Simplicity**
```bash
# Works automatically ✅
docker-compose up

# vs. Would require complex setup ❌
docker-compose --env-file config/.env up
```

### Alternative Considered: `config/` folder

**Why NOT used:**
- Would require `--env-file` flag on every docker-compose command
- Breaks standard workflow expectations
- Makefile would need updates to reference `config/.env`
- No significant organizational benefit for 2-3 env files

---

## Why Docker Files Are in Root

### Rationale:

**1. Docker Compose Standard Location**
```bash
# Standard - works everywhere ✅
docker-compose up

# Would require flags everywhere ❌
docker-compose -f docker/docker-compose.yml up
```

**2. Makefile Integration**
Our Makefile has 20+ targets referencing docker-compose:
```makefile
start: check-ports
    docker-compose up -d

stop:
    docker-compose down
```

Moving these would require updating every Makefile target.

**3. CI/CD Compatibility**
Most CI/CD systems (GitHub Actions, GitLab CI) expect:
```yaml
# .github/workflows/deploy.yml
- run: docker-compose up -d
```

Not:
```yaml
- run: docker-compose -f docker/docker-compose.yml up -d
```

**4. Industry Practice**

**Root structure (What we use):**
```
✅ Simple/Medium projects (90% of projects)
├── docker-compose.yml
├── docker-compose.prod.yml
└── {service}/Dockerfile
```

**docker/ folder structure:**
```
❌ Only for complex multi-environment projects
├── docker/
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   ├── docker-compose.staging.yml
│   ├── docker-compose.test.yml
│   └── docker-compose.prod.yml
```

**When to use `docker/` folder:**
- 5+ different docker-compose files
- Complex multi-stage deployments
- Kubernetes + Docker Compose hybrid
- Enterprise projects with dedicated DevOps team

**Our project has:**
- 2 docker-compose files (dev + prod)
- Simple deployment model
- Standard workflow expectations
- **Root structure is appropriate**

---

## Why `scripts/` Is in Root

### Rationale:

**1. Makefile References**
```makefile
check-ports:
    @./scripts/check-ports.sh
```

**2. Documentation References**
```markdown
# README.md
./scripts/check-ports.sh
```

**3. Direct Execution**
```bash
./scripts/backup.sh
./scripts/restore.sh
```

**4. Operational Scripts vs. Source Code**
- `scripts/` = Operations/DevOps utilities
- `backend/` = Application source code
- Clear separation of concerns

### Why NOT in `backend/scripts/`?
- These scripts operate on the entire project (docker, database, etc.)
- Not backend-specific
- Need root-level access to all services

---

## Why These Files Moved

### `start.sh` and `stop.sh` → `scripts/`

**Why moved:**
1. Not infrastructure files (like Makefile, docker-compose.yml)
2. Not referenced in any documentation
3. Redundant (Makefile provides `make start` and `make stop`)
4. Utility scripts belong in `scripts/` directory

**Before:**
```
CommandCenter/
├── start.sh          # ❌ Clutters root
├── stop.sh           # ❌ Clutters root
└── scripts/
    └── backup.sh
```

**After:**
```
CommandCenter/
└── scripts/
    ├── start.sh      # ✅ Organized
    ├── stop.sh       # ✅ Organized
    └── backup.sh
```

### Documentation Files → `docs/`

**65 files organized:**
- 13 review files → `docs/reviews/`
- 12 planning files → `docs/planning/`
- 1 phase report → `docs/phase-reports/`
- 14 old files → `docs/archived/`
- 18 AgentFlow files → `docs/experimental/`

**Why moved:**
- Cluttered root directory (40+ files!)
- Hard to find actual project files
- Professional projects keep docs organized
- Easier to navigate and maintain

---

## What Should Be in Root

### ✅ MUST be in root:
1. **Infrastructure Config**
   - `docker-compose*.yml` - Docker convention
   - `.env.template` - Docker Compose convention
   - `Makefile` - Build tool convention
   - `.gitignore` - Git convention

2. **Essential Documentation**
   - `README.md` - GitHub convention
   - `CLAUDE.md` - Claude Code convention
   - `SECURITY.md` - GitHub security policy convention
   - `LICENSE` - Open source convention

3. **Project Directories**
   - `backend/`, `frontend/` - Service directories
   - `docs/` - Documentation
   - `scripts/` - Operational utilities
   - `monitoring/`, `traefik/` - Infrastructure services

### ❌ Should NOT be in root:
1. **Loose Documentation**
   - Individual markdown files → `docs/`
   - Planning documents → `docs/planning/`
   - Review documents → `docs/reviews/`

2. **Utility Scripts**
   - Shell scripts → `scripts/`
   - Except: Infrastructure scripts referenced by Makefile

3. **Experimental Code**
   - Proof of concepts → `docs/experimental/`
   - AgentFlow → `docs/experimental/`

4. **Demo Files**
   - HTML demos → Remove or `docs/examples/`
   - Test files → Remove or service-specific test directories

---

## File Organization Matrix

| File Type | Root | docs/ | scripts/ | service/ |
|-----------|------|-------|----------|----------|
| docker-compose*.yml | ✅ | ❌ | ❌ | ❌ |
| .env* templates | ✅ | ❌ | ❌ | ❌ |
| Makefile | ✅ | ❌ | ❌ | ❌ |
| README.md | ✅ | ❌ | ❌ | ❌ |
| CLAUDE.md | ✅ | ❌ | ❌ | ❌ |
| SECURITY.md | ✅ | ❌ | ❌ | ❌ |
| Review docs | ❌ | ✅ | ❌ | ❌ |
| Planning docs | ❌ | ✅ | ❌ | ❌ |
| API docs | ❌ | ✅ | ❌ | ❌ |
| start.sh, stop.sh | ❌ | ❌ | ✅ | ❌ |
| backup.sh | ❌ | ❌ | ✅ | ❌ |
| check-ports.sh | ❌ | ❌ | ✅ | ❌ |
| Dockerfile | ❌ | ❌ | ❌ | ✅ |
| requirements.txt | ❌ | ❌ | ❌ | ✅ |
| package.json | ❌ | ❌ | ❌ | ✅ |

---

## Verification Checklist

Run cleanup script to verify structure:
```bash
bash .claude/cleanup.sh
```

Expected output:
```
✅ Cleanup complete!
📁 Repository structure verified:
   Root files: 9
   Root dirs: 9
   Docs organized: 5 folders
```

Manual verification:
```bash
# Should show only infrastructure and docs
ls -1 *.yml *.md Makefile

# Should show organized docs
ls docs/

# Should show utility scripts
ls scripts/
```

---

## References

- [Docker Compose File Reference](https://docs.docker.com/compose/compose-file/)
- [GitHub Repository Best Practices](https://github.com/github/platform-samples)
- [The Twelve-Factor App - Config](https://12factor.net/config)
- [Standard Project Layout](https://github.com/golang-standards/project-layout)

---

**Summary**: Our structure follows industry standards where infrastructure files stay in root for tool compatibility, while documentation and utilities are organized into appropriate directories.
