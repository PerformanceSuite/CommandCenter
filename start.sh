#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     CommandCenter Startup Script          ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo ""

# Function to check if Docker is running
check_docker() {
    echo -e "${YELLOW}→${NC} Checking if Docker is running..."

    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}✗${NC} Docker is not running!"
        echo ""
        echo -e "${YELLOW}Please start Docker Desktop:${NC}"
        echo "  1. Open Docker Desktop application"
        echo "  2. Wait for Docker to fully start"
        echo "  3. Run this script again"
        echo ""

        # Try to open Docker Desktop automatically (macOS)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo -e "${YELLOW}→${NC} Attempting to open Docker Desktop..."
            open -a Docker
            echo ""
            echo -e "${YELLOW}Waiting for Docker to start...${NC}"

            # Wait up to 60 seconds for Docker to start
            COUNTER=0
            while ! docker info > /dev/null 2>&1 && [ $COUNTER -lt 60 ]; do
                sleep 2
                ((COUNTER+=2))
                echo -n "."
            done
            echo ""

            if docker info > /dev/null 2>&1; then
                echo -e "${GREEN}✓${NC} Docker is now running!"
            else
                echo -e "${RED}✗${NC} Docker failed to start. Please start it manually."
                exit 1
            fi
        else
            exit 1
        fi
    else
        echo -e "${GREEN}✓${NC} Docker is running"
    fi
}

# Function to check if .env exists
check_env() {
    echo -e "${YELLOW}→${NC} Checking environment configuration..."

    if [ ! -f .env ]; then
        echo -e "${YELLOW}!${NC} .env file not found. Creating from template..."
        if [ -f .env.template ]; then
            cp .env.template .env
            echo -e "${GREEN}✓${NC} Created .env from template"
            echo -e "${YELLOW}!${NC} Please edit .env and add your configuration (especially SECRET_KEY and DB_PASSWORD)"
            echo ""
            read -p "Press Enter to continue after updating .env, or Ctrl+C to exit..."
        else
            echo -e "${RED}✗${NC} .env.template not found!"
            exit 1
        fi
    else
        echo -e "${GREEN}✓${NC} .env file exists"
    fi
}

# Function to stop any running containers
stop_existing() {
    echo -e "${YELLOW}→${NC} Stopping any existing CommandCenter containers..."
    docker-compose down > /dev/null 2>&1 || true
    echo -e "${GREEN}✓${NC} Stopped existing containers"
}

# Function to start services
start_services() {
    echo -e "${YELLOW}→${NC} Starting CommandCenter services..."
    echo ""

    docker-compose up -d

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓${NC} Services started successfully!"
    else
        echo -e "${RED}✗${NC} Failed to start services"
        exit 1
    fi
}

# Function to wait for services to be healthy
wait_for_services() {
    echo -e "${YELLOW}→${NC} Waiting for services to be ready..."

    # Wait for backend to be healthy
    COUNTER=0
    until curl -s http://localhost:8000/health > /dev/null 2>&1 || [ $COUNTER -eq 30 ]; do
        sleep 2
        ((COUNTER+=2))
        echo -n "."
    done
    echo ""

    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend is ready"
    else
        echo -e "${YELLOW}!${NC} Backend may still be starting up"
    fi
}

# Function to run database migrations
run_migrations() {
    echo -e "${YELLOW}→${NC} Running database migrations..."

    if docker-compose exec -T backend alembic upgrade head > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Database migrations completed"
    else
        echo -e "${YELLOW}!${NC} Migrations may have failed - check logs if needed"
    fi
}

# Function to show status
show_status() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         CommandCenter is Ready!            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Services running:${NC}"
    docker-compose ps
    echo ""
    echo -e "${GREEN}Access your CommandCenter:${NC}"
    echo -e "  Frontend:  ${BLUE}http://localhost:3000${NC}"
    echo -e "  Backend:   ${BLUE}http://localhost:8000${NC}"
    echo -e "  API Docs:  ${BLUE}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${GREEN}Useful commands:${NC}"
    echo -e "  View logs:        ${YELLOW}docker-compose logs -f${NC}"
    echo -e "  Stop services:    ${YELLOW}docker-compose down${NC}"
    echo -e "  Restart services: ${YELLOW}docker-compose restart${NC}"
    echo ""
}

# Main execution
main() {
    check_docker
    check_env
    stop_existing
    start_services
    wait_for_services
    run_migrations
    show_status
}

# Run main function
main
