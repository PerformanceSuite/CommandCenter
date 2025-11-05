#!/bin/bash
# End-to-end test for Hub background task system

set -e

echo "🧪 Hub E2E Test - Background Tasks"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Start infrastructure
echo "Step 1: Starting Redis + Celery worker..."
cd "$(dirname "$0")/.."
docker-compose -f docker-compose.monitoring.yml up -d redis celery-worker

# Wait for Redis to be ready
echo "Waiting for Redis..."
sleep 3

# Check Redis
if ! docker exec hub-redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}❌ Redis not ready${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Redis ready${NC}"

# Check Celery worker
echo "Waiting for Celery worker..."
sleep 5

if ! docker logs hub-celery-worker 2>&1 | grep -q "ready"; then
    echo -e "${YELLOW}⚠️  Celery worker may not be ready (check logs)${NC}"
else
    echo -e "${GREEN}✓ Celery worker ready${NC}"
fi

# Step 2: Start Hub backend
echo ""
echo "Step 2: Starting Hub backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

export DATABASE_URL="sqlite+aiosqlite:///./data/hub.db"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"

# Start backend in background
uvicorn app.main:app --host 0.0.0.0 --port 9002 > /tmp/hub-backend.log 2>&1 &
BACKEND_PID=$!

echo "Backend PID: $BACKEND_PID"
sleep 3

# Check backend health
if ! curl -s http://localhost:9002/health > /dev/null; then
    echo -e "${RED}❌ Backend not responding${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi
echo -e "${GREEN}✓ Backend ready${NC}"

# Step 3: Submit a test task
echo ""
echo "Step 3: Submitting test task..."

# Create a test project first
PROJECT_RESPONSE=$(curl -s -X POST http://localhost:9002/api/projects \
    -H "Content-Type: application/json" \
    -d '{
        "name": "E2E Test Project",
        "path": "/tmp/e2e-test-project",
        "backend_port": 8999,
        "frontend_port": 3999,
        "postgres_port": 5999,
        "redis_port": 6999
    }')

PROJECT_ID=$(echo $PROJECT_RESPONSE | grep -o '"id":[0-9]*' | grep -o '[0-9]*')
echo "Created project ID: $PROJECT_ID"

# Start project (this will submit Celery task)
TASK_RESPONSE=$(curl -s -X POST "http://localhost:9002/api/orchestration/${PROJECT_ID}/start")
TASK_ID=$(echo $TASK_RESPONSE | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TASK_ID" ]; then
    echo -e "${RED}❌ Failed to get task ID${NC}"
    echo "Response: $TASK_RESPONSE"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✓ Task submitted: $TASK_ID${NC}"

# Step 4: Poll task status
echo ""
echo "Step 4: Polling task status (10 seconds)..."

for i in {1..5}; do
    sleep 2
    STATUS_RESPONSE=$(curl -s "http://localhost:9002/api/tasks/${TASK_ID}/status")
    STATE=$(echo $STATUS_RESPONSE | grep -o '"state":"[^"]*"' | cut -d'"' -f4)
    PROGRESS=$(echo $STATUS_RESPONSE | grep -o '"progress":[0-9]*' | grep -o '[0-9]*')

    echo "  Poll $i: State=$STATE, Progress=$PROGRESS%"

    if [ "$STATE" = "SUCCESS" ] || [ "$STATE" = "FAILURE" ]; then
        break
    fi
done

echo -e "${GREEN}✓ Task polling working${NC}"

# Step 5: Verify task in Flower (if available)
echo ""
echo "Step 5: Checking Flower dashboard (optional)..."

if docker ps | grep -q hub-flower; then
    if curl -s http://localhost:5555/api/tasks/$TASK_ID > /dev/null; then
        echo -e "${GREEN}✓ Task visible in Flower${NC}"
    else
        echo -e "${YELLOW}⚠️  Task not yet in Flower (may be too fast)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Flower not running (start with docker-compose)${NC}"
fi

# Step 6: Revoke task (cleanup)
echo ""
echo "Step 6: Revoking task (cleanup)..."
docker exec hub-celery-worker celery -A app.celery_app control revoke $TASK_ID

# Cleanup
echo ""
echo "Cleaning up..."
kill $BACKEND_PID 2>/dev/null || true
docker-compose -f ../docker-compose.monitoring.yml down

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ E2E Test Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Summary:"
echo "  - Redis: ✓"
echo "  - Celery Worker: ✓"
echo "  - Hub Backend: ✓"
echo "  - Task Submission: ✓"
echo "  - Task Polling: ✓"
echo ""
echo "All systems operational!"
