#!/bin/bash
# launch-agents.sh - Launch parallel agents for development

set -e

echo "🤖 Launching Agent Parallel Development System"
echo "=============================================="

# Check if worktrees are set up
if [ ! -d "worktrees" ]; then
  echo "❌ Worktrees not found. Run ./scripts/setup-worktrees.sh first"
  exit 1
fi

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
  echo "❌ GitHub CLI (gh) not found. Install with: brew install gh"
  exit 1
fi

# Check if authenticated with GitHub
if ! gh auth status &> /dev/null; then
  echo "❌ Not authenticated with GitHub. Run: gh auth login"
  exit 1
fi

echo ""
echo "📋 Phase 1: Independent Agents (No Dependencies)"
echo "================================================="

# Phase 1 agents can run in parallel
PHASE1_AGENTS=(
  "security-agent"
  "backend-agent"
  "frontend-agent"
  "rag-agent"
  "devops-agent"
)

echo ""
echo "🚀 Launching ${#PHASE1_AGENTS[@]} agents in parallel..."
echo ""

for agent in "${PHASE1_AGENTS[@]}"; do
  echo "  ▶️  Launching $agent..."

  # Launch agent in background
  ./scripts/run-agent.sh "$agent" &

  # Store PID for monitoring
  echo $! > ".agent-coordination/${agent}.pid"

  echo "     PID: $(cat .agent-coordination/${agent}.pid)"
  echo ""
done

echo "✅ Phase 1 agents launched!"
echo ""
echo "Monitor progress with: ./scripts/monitor-agents.sh"
echo "Or check individual agent logs: tail -f .agent-coordination/logs/<agent>.log"
echo ""
echo "Phase 2 agents will launch automatically when dependencies are satisfied."
echo ""
