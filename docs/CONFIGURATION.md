# Configuration Guide

Complete guide to configuring Command Center for your environment.

---

## Environment Variables

All configuration is managed through environment variables in the `.env` file.

### Setup

1. **Copy the template:**
   ```bash
   cp .env.template .env
   ```

2. **Edit values:**
   ```bash
   nano .env  # or vim, code, etc.
   ```

3. **Restart services:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

## Configuration Sections

### Port Configuration

Control which ports services bind to on your host machine.

```bash
# Backend API Port
BACKEND_PORT=8000

# Frontend Port
FRONTEND_PORT=3000

# PostgreSQL Port
POSTGRES_PORT=5432

# Redis Port
REDIS_PORT=6379
```

**When to change:**
- Port conflicts with other services
- Running multiple instances
- Corporate port restrictions

**See also:** [PORT_MANAGEMENT.md](./PORT_MANAGEMENT.md)

---

### Database Configuration

```bash
# PostgreSQL connection string
DATABASE_URL=postgresql://commandcenter:changeme@postgres:5432/commandcenter

# Database password
DB_PASSWORD=changeme
```

**Production recommendations:**
- Generate strong password: `openssl rand -base64 32`
- Use managed database service (AWS RDS, Google Cloud SQL)
- Enable SSL connections
- Regular backups

**Connection string format:**
```
postgresql://[user]:[password]@[host]:[port]/[database]
```

---

### Security

```bash
# Secret key for JWT tokens and encryption
SECRET_KEY=your-secret-key-here

# Whether to encrypt GitHub tokens in database
ENCRYPT_TOKENS=true
```

**Generate secure SECRET_KEY:**
```bash
# Method 1: OpenSSL
openssl rand -hex 32

# Method 2: Python
python -c "import secrets; print(secrets.token_hex(32))"

# Method 3: Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

**⚠️ CRITICAL:**
- **Never** commit `.env` to git
- Use minimum 32-character key
- Rotate keys periodically
- Different keys per environment

**Token Encryption:**
- `ENCRYPT_TOKENS=true` - GitHub tokens encrypted in database (recommended)
- `ENCRYPT_TOKENS=false` - Tokens stored in plaintext (development only)

---

### AI/ML API Keys

```bash
# Anthropic (Claude) API Key
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI (GPT) API Key
OPENAI_API_KEY=sk-...
```

**Where to get keys:**
- Anthropic: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/api-keys

**Usage:**
- Required for RAG knowledge base queries
- Optional for basic functionality
- Can use either Anthropic OR OpenAI (not both required)

**Cost management:**
- Set usage limits in provider dashboard
- Monitor token consumption
- Cache responses when possible

---

### GitHub Integration

```bash
# GitHub Personal Access Token
GITHUB_TOKEN=ghp_...
```

**Creating a token:**

1. Go to GitHub Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes:
   - ✅ `repo` (for private repos)
   - ✅ `read:org` (for organization repos)
4. Generate and copy token
5. Add to `.env`

**Per-repository tokens:**
You can also add tokens when creating individual repositories in the UI. This overrides the global `GITHUB_TOKEN` for that specific repo.

**Token security:**
- Tokens are encrypted in database when `ENCRYPT_TOKENS=true`
- Never log tokens
- Rotate tokens every 90 days
- Use fine-grained tokens when possible

---

### Redis Configuration

```bash
# Redis connection URL
REDIS_URL=redis://redis:6379
```

**Usage:**
- Session management
- Caching
- Background task queue

**Production:**
- Use Redis Cluster for high availability
- Enable persistence (RDB + AOF)
- Set maxmemory policy
- Monitor memory usage

---

### RAG Storage Paths

```bash
# RAG storage root path
RAG_STORAGE_PATH=/app/rag_storage

# ChromaDB vector database path
CHROMADB_PATH=/app/rag_storage/chromadb
```

**Docker volumes:**
These paths are inside containers. Volumes are defined in `docker-compose.yml`:

```yaml
volumes:
  rag_storage:
    driver: local
```

**Backup:**
```bash
# Backup RAG storage
docker run --rm -v commandcenter_rag_storage:/data -v $(pwd):/backup \
  alpine tar czf /backup/rag-backup-$(date +%Y%m%d).tar.gz /data
```

---

### Application Settings

```bash
# Debug mode (development only)
DEBUG=false

# Python unbuffered output (Docker logs)
PYTHONUNBUFFERED=1
```

**Debug mode:**
- `DEBUG=true` - Detailed error messages, auto-reload
- `DEBUG=false` - Production mode, error summaries only

**⚠️ Never use DEBUG=true in production** - exposes sensitive information

---

### Frontend Configuration

```bash
# API base URL (from frontend perspective)
VITE_API_URL=http://localhost:8000
```

**Important:**
- This is the URL the **browser** uses to reach the API
- For Docker: Use `http://localhost:${BACKEND_PORT}`
- For Traefik: Use `http://api.commandcenter.localhost`
- For production: Use your domain `https://api.yourdomain.com`

---

## Environment-Specific Configs

### Development

```bash
# .env.development
BACKEND_PORT=8000
FRONTEND_PORT=3000
DEBUG=true
ENCRYPT_TOKENS=false
DATABASE_URL=postgresql://commandcenter:dev@localhost:5432/commandcenter_dev
```

### Staging

```bash
# .env.staging
BACKEND_PORT=8010
FRONTEND_PORT=3010
DEBUG=false
ENCRYPT_TOKENS=true
DATABASE_URL=postgresql://commandcenter:staging@db.staging:5432/commandcenter_staging
VITE_API_URL=https://api-staging.commandcenter.com
```

### Production

```bash
# .env.production
BACKEND_PORT=80
FRONTEND_PORT=443
DEBUG=false
ENCRYPT_TOKENS=true
DATABASE_URL=postgresql://commandcenter:prod@db.prod.rds.amazonaws.com:5432/commandcenter
SECRET_KEY=<64-char-hex-key>
VITE_API_URL=https://api.commandcenter.com

# Production-only
SENTRY_DSN=https://...
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE=10485760
RATE_LIMIT_PER_MINUTE=60
```

---

## Docker Compose Configuration

### Override Files

Create `docker-compose.override.yml` for local customization (not committed to git):

```yaml
# docker-compose.override.yml
services:
  backend:
    ports:
      - "8001:8000"  # Different port
    environment:
      - DEBUG=true
    volumes:
      - ./backend:/app  # Live code reload
```

### Production Compose

For production, create `docker-compose.prod.yml`:

```yaml
# docker-compose.prod.yml
services:
  backend:
    restart: always
    environment:
      - DEBUG=false
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  postgres:
    restart: always
    environment:
      - POSTGRES_MAX_CONNECTIONS=200
    volumes:
      - /mnt/data/postgres:/var/lib/postgresql/data
```

Run with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Configuration Validation

### Startup Checks

Backend validates configuration on startup:

```python
# app/config.py checks for:
- SECRET_KEY length >= 32 characters
- Valid DATABASE_URL format
- Required API keys if RAG enabled
- Port availability
```

### Manual Validation

```bash
# Check configuration
docker-compose config

# Validate environment variables
docker-compose run --rm backend python -c "from app.config import settings; print(settings)"
```

---

## Security Best Practices

### 1. Environment Files

```bash
# .gitignore (already configured)
.env
.env.local
.env.*.local
```

### 2. Secrets Management

**Development:**
- Use `.env` files
- Share `.env.template` only

**Production:**
- Use Docker secrets:
  ```yaml
  secrets:
    db_password:
      external: true
  ```
- Or use environment variable injection from orchestrator
- Or use AWS Secrets Manager / Google Secret Manager

### 3. Principle of Least Privilege

- GitHub tokens: Minimum required scopes
- Database user: Only needed permissions
- API keys: Project-specific when possible

### 4. Regular Rotation

```bash
# Rotate every 90 days:
- SECRET_KEY
- DB_PASSWORD
- GITHUB_TOKEN
- API_KEY credentials
```

---

## Troubleshooting

### Configuration Not Loading

**Problem:** Changes to `.env` not reflected

**Solution:**
```bash
# Recreate containers (reloads .env)
docker-compose down
docker-compose up -d

# Or force recreation
docker-compose up -d --force-recreate
```

### Environment Variable Syntax Errors

**Problem:** `export: not valid in this context`

**Solution:**
- Don't use `export` in `.env` files
- Use `KEY=value` format only
- No spaces around `=`
- Quote values with spaces: `KEY="value with spaces"`

```bash
# ❌ Wrong
export SECRET_KEY=abc123
SECRET_KEY = abc123

# ✅ Correct
SECRET_KEY=abc123
SECRET_KEY="abc 123"
```

### Database Connection Fails

**Problem:** `could not connect to server`

**Check:**
1. PostgreSQL container running: `docker ps | grep postgres`
2. Port accessible: `nc -zv localhost 5432`
3. Credentials correct in `.env`
4. Database created: `docker-compose logs postgres | grep "database system is ready"`

### Frontend Can't Reach Backend

**Problem:** API calls fail from browser

**Solution:**
- Check `VITE_API_URL` matches where backend is accessible
- For Docker: Use `http://localhost:${BACKEND_PORT}`
- Check CORS settings in backend
- Verify backend health: `curl http://localhost:8000/health`

---

## Advanced Configuration

### Custom Docker Network

```yaml
# docker-compose.override.yml
networks:
  commandcenter:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

### Resource Limits

```yaml
# docker-compose.override.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Health Checks

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## Configuration Reference

### Complete .env Template

See [.env.template](../.env.template) for the complete, commented configuration template.

### Required vs Optional

**Required (minimum):**
- `SECRET_KEY`
- `DB_PASSWORD`
- Port configuration (if defaults conflict)

**Optional (enhances functionality):**
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` (for RAG)
- `GITHUB_TOKEN` (for auto-syncing repos)
- `SLACK_TOKEN` (for notifications)

---

## Getting Help

- Check logs: `docker-compose logs -f`
- Validate config: `docker-compose config`
- Test connection: `docker-compose exec backend python -c "from app.database import engine; print(engine.url)"`
- See [GitHub Issues](https://github.com/PerformanceSuite/CommandCenter/issues)

---

**Next Steps:**
- [Quick Start Guide](../QUICK_START_PORTS.md)
- [Port Management](./PORT_MANAGEMENT.md)
- [API Documentation](./API.md)
