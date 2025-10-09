# CommandCenter Quick Start Guide

## 🚀 One-Command Startup

```bash
./start.sh
```

This script will:
1. ✅ Check if Docker is running (and start it if needed on macOS)
2. ✅ Verify `.env` configuration exists
3. ✅ Stop any existing containers
4. ✅ Start all services (frontend, backend, database, redis)
5. ✅ Wait for services to be healthy
6. ✅ Run database migrations
7. ✅ Show you the URLs to access

## 🛑 Stop CommandCenter

```bash
./stop.sh
```

## 📝 First Time Setup

1. **Clone and navigate to the project:**
   ```bash
   cd /path/to/CommandCenter
   ```

2. **Run the startup script:**
   ```bash
   ./start.sh
   ```

3. **On first run**, the script will:
   - Create `.env` from `.env.template`
   - Ask you to configure `SECRET_KEY` and `DB_PASSWORD`
   - Wait for you to press Enter after editing

4. **Edit `.env`** and set at minimum:
   ```bash
   SECRET_KEY=your-secret-key-here
   DB_PASSWORD=your-strong-password
   ```

5. **Run again:**
   ```bash
   ./start.sh
   ```

## 🌐 Accessing CommandCenter

Once started, access:

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🎯 Using Multi-Project Features

1. **Navigate to Projects page** (sidebar menu)
2. **Click "New Project"**
3. **Fill in project details:**
   - Name: "My AI Research"
   - Owner: your-username
   - Description: (optional)
4. **Click Create**
5. **Use the project selector dropdown** in the header to switch between projects

## 🔧 Troubleshooting

### Docker not starting automatically?

**macOS:**
```bash
open -a Docker
# Wait for Docker to start, then run ./start.sh again
```

**Linux:**
```bash
sudo systemctl start docker
```

**Windows:**
- Open Docker Desktop manually

### Services not responding?

```bash
# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
```

### Database issues?

```bash
# Re-run migrations
docker-compose exec backend alembic upgrade head

# Reset database (WARNING: destroys all data)
docker-compose down -v
./start.sh
```

### Port conflicts?

Check what's using the ports:
```bash
# macOS/Linux
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
```

Change ports in `.env` if needed:
```bash
FRONTEND_PORT=3001
BACKEND_PORT=8001
POSTGRES_PORT=5433
REDIS_PORT=6380
```

## 📚 Additional Documentation

- **Full Setup Guide**: `CLAUDE.md`
- **Multi-Project Architecture**: `PHASE1B_STATUS_REPORT.md`
- **API Documentation**: http://localhost:8000/docs (when running)

## 🆘 Need Help?

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Ensure Docker is running: `docker info`
3. Verify `.env` is configured: `cat .env`
4. Try a clean restart: `./stop.sh && ./start.sh`

---

**Quick Commands Reference:**

```bash
# Start everything
./start.sh

# Stop everything
./stop.sh

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart backend

# Run migrations
docker-compose exec backend alembic upgrade head

# Access database shell
docker-compose exec postgres psql -U commandcenter

# Access backend shell
docker-compose exec backend bash
```
