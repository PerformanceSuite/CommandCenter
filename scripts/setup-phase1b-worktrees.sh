#!/bin/bash
# setup-phase1b-worktrees.sh
# Creates isolated worktrees for Phase 1b: CommandCenter Database Isolation

set -e

echo "🚀 Setting up Phase 1b Agent Worktrees"
echo "======================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create worktrees directory if needed
mkdir -p worktrees
mkdir -p .agent-coordination/tasks

# Define Phase 1b agents
declare -A AGENTS
AGENTS=(
    ["database-isolation-agent"]="feature/database-isolation"
    ["redis-namespacing-agent"]="feature/redis-namespacing"
    ["chromadb-collections-agent"]="feature/chromadb-collections"
    ["project-context-agent"]="feature/project-context"
)

echo ""

# Create worktrees
for agent in "${!AGENTS[@]}"; do
    branch="${AGENTS[$agent]}"
    worktree_path="worktrees/$agent"

    echo -e "${GREEN}Creating worktree:${NC} $agent"
    echo "  Branch: $branch"
    echo "  Path: $worktree_path"

    if [ -d "$worktree_path" ]; then
        echo -e "${YELLOW}  ⚠️  Worktree exists, removing...${NC}"
        git worktree remove "$worktree_path" --force 2>/dev/null || true
    fi

    if git show-ref --verify --quiet "refs/heads/$branch"; then
        echo "  ℹ️  Branch exists, will reuse"
        git worktree add "$worktree_path" "$branch"
    else
        echo "  ✨ Creating new branch from main"
        git worktree add -b "$branch" "$worktree_path" main
    fi

    echo -e "${GREEN}  ✅ Worktree created${NC}"
    echo ""
done

# Create Phase 1b coordination files
echo "📝 Creating Phase 1b coordination files"

cat > .agent-coordination/phase1b-status.json <<EOF
{
  "phase": "1b",
  "goal": "CommandCenter Database Isolation & Multi-Project Support",
  "start_time": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "agents": {
    "database-isolation-agent": {
      "status": "initialized",
      "worktree": "worktrees/database-isolation-agent",
      "branch": "feature/database-isolation",
      "progress": 0.0,
      "current_task": "Ready to start",
      "priority": "critical",
      "estimated_hours": 12,
      "description": "Add project_id to all tables, implement complete database isolation"
    },
    "redis-namespacing-agent": {
      "status": "initialized",
      "worktree": "worktrees/redis-namespacing-agent",
      "branch": "feature/redis-namespacing",
      "progress": 0.0,
      "current_task": "Ready to start",
      "priority": "critical",
      "estimated_hours": 3,
      "description": "Namespace all Redis cache keys by project_id"
    },
    "chromadb-collections-agent": {
      "status": "initialized",
      "worktree": "worktrees/chromadb-collections-agent",
      "branch": "feature/chromadb-collections",
      "progress": 0.0,
      "current_task": "Ready to start",
      "priority": "critical",
      "estimated_hours": 4,
      "description": "Create per-project ChromaDB collections for knowledge base"
    },
    "project-context-agent": {
      "status": "initialized",
      "worktree": "worktrees/project-context-agent",
      "branch": "feature/project-context",
      "progress": 0.0,
      "current_task": "Ready to start",
      "priority": "high",
      "estimated_hours": 2,
      "description": "Add ProjectContextMiddleware and access control"
    }
  },
  "dependencies": {
    "database-isolation-agent": [],
    "redis-namespacing-agent": [],
    "chromadb-collections-agent": [],
    "project-context-agent": []
  },
  "merge_order": [
    "project-context-agent",
    "redis-namespacing-agent",
    "chromadb-collections-agent",
    "database-isolation-agent"
  ],
  "completed": [],
  "failed": [],
  "blocked": []
}
