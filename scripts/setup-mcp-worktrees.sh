#!/bin/bash
# setup-mcp-worktrees.sh - Initialize git worktrees for MCP Phase 1 agents

set -e

echo "🚀 Setting up Git Worktrees for MCP Phase 1 Agents"
echo "=========================================================="

# Define MCP Phase 1 agents and their branches
AGENTS=(
  "mcp-infrastructure-agent:feature/mcp-infrastructure"
  "knowledgebeast-mcp-agent:feature/knowledgebeast-mcp"
  "api-manager-agent:feature/api-manager"
)

# Create worktrees directory
echo ""
echo "📁 Creating worktrees directory..."
mkdir -p worktrees

# Ensure coordination directory exists
echo "📁 Ensuring agent coordination directory exists..."
mkdir -p .agent-coordination/tasks

# Create each worktree
echo ""
echo "🌳 Creating git worktrees..."
for agent in "${AGENTS[@]}"; do
  IFS=':' read -r name branch <<< "$agent"

  # Create branch from main
  echo "  📌 Creating branch: $branch"
  git branch "$branch" main 2>/dev/null || echo "     (branch already exists)"

  # Create worktree
  echo "  🌿 Creating worktree: worktrees/$name"
  git worktree add "worktrees/$name" "$branch" 2>/dev/null || echo "     (worktree already exists)"

  echo "  ✅ $name ready at worktrees/$name"
  echo ""
done

# Update status.json with MCP agents
echo "📋 Updating coordination files..."

cat > .agent-coordination/mcp-status.json <<EOF
{
  "agents": {
    "mcp-infrastructure-agent": {
      "status": "pending",
      "branch": "feature/mcp-infrastructure",
      "worktree": "worktrees/mcp-infrastructure-agent",
      "progress": 0.0,
      "current_task": null,
      "tests_passing": null,
      "review_score": null,
      "blocked_by": [],
      "pr_url": null,
      "estimated_hours": 35
    },
    "knowledgebeast-mcp-agent": {
      "status": "pending",
      "branch": "feature/knowledgebeast-mcp",
      "worktree": "worktrees/knowledgebeast-mcp-agent",
      "progress": 0.0,
      "current_task": null,
      "tests_passing": null,
      "review_score": null,
      "blocked_by": [],
      "pr_url": null,
      "estimated_hours": 25
    },
    "api-manager-agent": {
      "status": "pending",
      "branch": "feature/api-manager",
      "worktree": "worktrees/api-manager-agent",
      "progress": 0.0,
      "current_task": null,
      "tests_passing": null,
      "review_score": null,
      "blocked_by": [],
      "pr_url": null,
      "estimated_hours": 15
    }
  },
  "completed": [],
  "failed": [],
  "blocked": []
}
EOF

echo "✅ mcp-status.json created"

# List all worktrees
echo ""
echo "🌳 Git Worktree List:"
git worktree list

echo ""
echo "=========================================================="
echo "✅ MCP Phase 1 git worktree setup complete!"
echo ""
echo "Next steps:"
echo "  1. Review .agent-coordination/mcp-status.json"
echo "  2. Launch agents via Claude Code Task tool"
echo "  3. Monitor progress in .agent-coordination/mcp-status.json"
echo ""
echo "Total estimated time: 75 hours (parallelized = ~3 days)"
echo ""
