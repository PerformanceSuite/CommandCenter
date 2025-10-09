#!/bin/bash
# Start CommandCenter with AI Tools UI

set -e

echo "🚀 Starting CommandCenter with AI Tools UI"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if in CommandCenter directory
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Please run this script from the CommandCenter root directory"
    exit 1
fi

echo -e "${BLUE}Starting Backend Server...${NC}"
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null || true

# Set environment variables
export GEMINI_API_KEY=$(grep GEMINI_API_KEY ~/.zshrc | cut -d'=' -f2 | tr -d '"' 2>/dev/null || echo "")

# Start backend in background
python -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"

# Start frontend
cd ../frontend
echo -e "${BLUE}Starting Frontend Server...${NC}"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo -e "${YELLOW}
╔══════════════════════════════════════════════════════════════╗
║                  🎉 CommandCenter is Ready!                   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Frontend:  http://localhost:5173                           ║
║  Backend:   http://localhost:8000                           ║
║  API Docs:  http://localhost:8000/docs                      ║
║                                                              ║
║  AI Tools:  http://localhost:5173/ai-tools                  ║
║                                                              ║
║  Press Ctrl+C to stop all servers                           ║
╚══════════════════════════════════════════════════════════════╝
${NC}"

# Start frontend (this will block)
npm run dev

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null; exit" INT TERM
