#!/bin/bash

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
echo -e "${BLUE}║     CommandCenter Stop Script              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}→${NC} Stopping CommandCenter services..."
docker-compose down

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓${NC} CommandCenter stopped successfully!"
else
    echo -e "${RED}✗${NC} Failed to stop services"
    exit 1
fi
