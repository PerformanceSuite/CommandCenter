#!/bin/bash

# AgentFlow Setup Script
# Initialize AgentFlow in your project

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log() {
    echo -e "${BLUE}[SETUP]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Banner
echo -e "${BLUE}"
cat << 'EOF'
    ___                    _   _____ _               
   / _ \                  | | |  ___| |              
  / /_\ \ __ _  ___ _ __  | |_| |_  | | _____      __
  |  _  |/ _` |/ _ \ '_ \ | __|  _| | |/ _ \ \ /\ / /
  | | | | (_| |  __/ | | || |_| |   | | (_) \ V  V / 
  \_| |_/\__, |\___|_| |_|\__\_|   |_|\___/ \_/\_/  
          __/ |                                      
         |___/   Autonomous Multi-Agent System                                    
EOF
echo -e "${NC}"

log "Welcome to AgentFlow Setup!"
echo ""

# Check dependencies
log "Checking dependencies..."

missing_deps=()

if ! command -v git &> /dev/null; then
    missing_deps+=("git")
fi

if ! command -v node &> /dev/null; then
    missing_deps+=("node")
fi

if ! command -v npm &> /dev/null; then
    missing_deps+=("npm")
fi

if ! command -v jq &> /dev/null; then
    warning "jq is recommended but not required"
fi

if [ ${#missing_deps[@]} -gt 0 ]; then
    error "Missing required dependencies: ${missing_deps[*]}"
fi

success "All required dependencies are installed"

# Install npm packages
log "Installing npm packages..."
npm install --silent

# Make scripts executable
log "Setting up executable permissions..."
chmod +x scripts/*.sh
chmod +x scripts/utils/*.sh

# Create .agentflow directory structure
log "Creating AgentFlow directories..."
mkdir -p .agentflow/{logs,worktrees,reviews,cache,artifacts}

# Create .gitignore if it doesn't exist
if [ ! -f .gitignore ]; then
    log "Creating .gitignore..."
    cat > .gitignore << 'EOF'
# AgentFlow
.agentflow/
*.log
*.pid
.env.local

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
EOF
fi

# Create sample .env file
if [ ! -f .env ]; then
    log "Creating .env file..."
    cat > .env << 'EOF'
# AgentFlow Configuration
PROJECT_NAME=my-project
MAX_PARALLEL=5
REVIEW_THRESHOLD=10
MERGE_STRATEGY=squash
BRANCH_STRATEGY=gitflow

# Claude Configuration
CLAUDE_MODEL=claude-opus-4-1-20250805
# ANTHROPIC_API_KEY=your-api-key-here

# Optional Features
ENABLE_MONITORING=true
DASHBOARD_PORT=3000
LOG_LEVEL=info
EOF
    warning "Please add your ANTHROPIC_API_KEY to the .env file"
fi

# Initialize git if needed
if [ ! -d .git ]; then
    log "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial AgentFlow setup"
fi

# Success message
echo ""
success "AgentFlow setup completed successfully!"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Add your Anthropic API key to .env file"
echo "2. Open the web interface: npm run web"
echo "3. Or run directly: ./scripts/agentflow.sh --project your-project"
echo ""
echo -e "${BLUE}Available commands:${NC}"
echo "  npm run setup    - Re-run this setup"
echo "  npm run web      - Open setup wizard"
echo "  npm run monitor  - Start monitoring dashboard"
echo "  npm start        - Run AgentFlow"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  README.md        - Full documentation"
echo "  config/          - Configuration files"
echo "  prompts/         - Agent prompt templates"
echo ""
success "Happy coding with AgentFlow! 🚀"
