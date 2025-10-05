#!/bin/bash
set -e

# Port Conflict Checker for Command Center
# Checks if required ports are available before starting Docker Compose

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load .env if exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Define ports to check
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
DB_PORT=${POSTGRES_PORT:-5432}

PORTS_TO_CHECK=($BACKEND_PORT $FRONTEND_PORT $DB_PORT)
PORT_NAMES=("Backend API" "Frontend" "PostgreSQL")

echo "🔍 Checking port availability..."
echo ""

all_clear=true
conflicts=()

# Check each port
for i in "${!PORTS_TO_CHECK[@]}"; do
    port="${PORTS_TO_CHECK[$i]}"
    name="${PORT_NAMES[$i]}"

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        PID=$(lsof -ti :$port)
        PROCESS=$(ps -p $PID -o comm= 2>/dev/null || echo "unknown")
        echo -e "${RED}❌ Port $port ($name) is in use${NC}"
        echo -e "   Process: $PROCESS (PID: $PID)"
        echo ""
        all_clear=false
        conflicts+=("$port:$PID:$name")
    else
        echo -e "${GREEN}✅ Port $port ($name) is available${NC}"
    fi
done

echo ""

if [ "$all_clear" = false ]; then
    echo -e "${YELLOW}⚠️  Port conflicts detected!${NC}"
    echo ""
    echo "Choose an option:"
    echo ""
    echo "1. Kill conflicting processes automatically"
    echo "2. Modify ports in .env file"
    echo "3. Use Traefik reverse proxy (recommended for multiple projects)"
    echo "4. Exit and handle manually"
    echo ""
    read -p "Enter choice (1-4): " choice

    case $choice in
        1)
            echo ""
            echo "Killing conflicting processes..."
            for conflict in "${conflicts[@]}"; do
                IFS=':' read -r port pid name <<< "$conflict"
                echo "Killing PID $pid on port $port ($name)..."
                kill -9 $pid 2>/dev/null || echo "Failed to kill $pid"
            done
            echo -e "${GREEN}✅ Processes killed. Run this script again to verify.${NC}"
            exit 0
            ;;
        2)
            echo ""
            echo "Edit .env file and change these variables:"
            for conflict in "${conflicts[@]}"; do
                IFS=':' read -r port pid name <<< "$conflict"
                suggested=$((port + 1))
                case $name in
                    "Backend API")
                        echo "  BACKEND_PORT=$suggested  # Currently: $port"
                        ;;
                    "Frontend")
                        echo "  FRONTEND_PORT=$suggested  # Currently: $port"
                        ;;
                    "PostgreSQL")
                        echo "  POSTGRES_PORT=$suggested  # Currently: $port"
                        ;;
                esac
            done
            echo ""
            echo "Then run: docker-compose up -d"
            exit 1
            ;;
        3)
            echo ""
            echo "Traefik setup guide: See docs/TRAEFIK_SETUP.md"
            echo "This eliminates port conflicts entirely!"
            exit 1
            ;;
        4)
            echo "Exiting..."
            exit 1
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
else
    echo -e "${GREEN}✅ All ports clear! Safe to start Docker Compose.${NC}"
    exit 0
fi
