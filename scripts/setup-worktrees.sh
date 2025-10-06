#!/bin/bash
# setup-worktrees.sh - Initialize git worktrees for parallel agent development

set -e

echo "🚀 Setting up Git Worktrees for Agent Parallel Execution"
echo "=========================================================="

# Define agents and their branches
AGENTS=(
  "security-agent:feature/security-hardening"
  "backend-agent:feature/backend-architecture"
  "frontend-agent:feature/frontend-improvements"
  "rag-agent:feature/rag-completion"
  "devops-agent:feature/devops-infrastructure"
  "testing-agent:feature/testing-coverage"
  "docs-agent:feature/documentation-updates"
  "github-agent:feature/github-optimization"
)

# Create worktrees directory
echo ""
echo "📁 Creating worktrees directory..."
mkdir -p worktrees

# Create coordination directory
echo "📁 Creating agent coordination directory..."
mkdir -p .agent-coordination

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

# Initialize coordination files
echo "📋 Initializing coordination files..."

# Create status.json
cat > .agent-coordination/status.json <<EOF
{
  "agents": {
    "security-agent": {
      "status": "pending",
      "branch": "feature/security-hardening",
      "worktree": "worktrees/security-agent",
      "progress": 0.0,
      "current_task": null,
      "tests_passing": null,
      "review_score": null,
      "blocked_by": [],
      "pr_url": null
    },
    "backend-agent": {
      "status": "pending",
      "branch": "feature/backend-architecture",
      "worktree": "worktrees/backend-agent",
      "progress": 0.0,
      "current_task": null,
      "tests_passing": null,
      "review_score": null,
      "blocked_by": [],
      "pr_url": null
    },
    "frontend-agent": {
      "status": "pending",
      "branch": "feature/frontend-improvements",
      "worktree": "worktrees/frontend-agent",
      "progress": 0.0,
      "current_task": null,
      "tests_passing": null,
      "review_score": null,
      "blocked_by": [],
      "pr_url": null
    },
    "rag-agent": {
      "status": "pending",
      "branch": "feature/rag-completion",
      "worktree": "worktrees/rag-agent",
      "progress": 0.0,
      "current_task": null,
      "tests_passing": null,
      "review_score": null,
      "blocked_by": [],
      "pr_url": null
    },
    "devops-agent": {
      "status": "pending",
      "branch": "feature/devops-infrastructure",
      "worktree": "worktrees/devops-agent",
      "progress": 0.0,
      "current_task": null,
      "tests_passing": null,
      "review_score": null,
      "blocked_by": [],
      "pr_url": null
    },
    "testing-agent": {
      "status": "pending",
      "branch": "feature/testing-coverage",
      "worktree": "worktrees/testing-agent",
      "progress": 0.0,
      "current_task": null,
      "tests_passing": null,
      "review_score": null,
      "blocked_by": ["backend-agent", "frontend-agent"],
      "pr_url": null
    },
    "docs-agent": {
      "status": "pending",
      "branch": "feature/documentation-updates",
      "worktree": "worktrees/docs-agent",
      "progress": 0.0,
      "current_task": null,
      "tests_passing": null,
      "review_score": null,
      "blocked_by": ["security-agent", "backend-agent", "rag-agent"],
      "pr_url": null
    },
    "github-agent": {
      "status": "pending",
      "branch": "feature/github-optimization",
      "worktree": "worktrees/github-agent",
      "progress": 0.0,
      "current_task": null,
      "tests_passing": null,
      "review_score": null,
      "blocked_by": ["backend-agent"],
      "pr_url": null
    }
  },
  "completed": [],
  "failed": [],
  "blocked": []
}
EOF

# Create dependencies.json
cat > .agent-coordination/dependencies.json <<EOF
{
  "dependencies": {
    "testing-agent": ["backend-agent", "frontend-agent"],
    "docs-agent": ["security-agent", "backend-agent", "rag-agent"],
    "github-agent": ["backend-agent"]
  },
  "merge_order": [
    ["security-agent", "backend-agent", "frontend-agent", "rag-agent", "devops-agent"],
    ["github-agent"],
    ["testing-agent"],
    ["docs-agent"]
  ],
  "phase1_independent": [
    "security-agent",
    "backend-agent",
    "frontend-agent",
    "rag-agent",
    "devops-agent"
  ],
  "phase2_dependent": [
    "github-agent",
    "testing-agent",
    "docs-agent"
  ]
}
EOF

# Create merge-queue.json
cat > .agent-coordination/merge-queue.json <<EOF
{
  "queue": [],
  "merged": [],
  "conflicts": []
}
EOF

echo "✅ status.json created"
echo "✅ dependencies.json created"
echo "✅ merge-queue.json created"

# Create .gitignore for coordination files
echo ""
echo "📝 Configuring .gitignore..."
if ! grep -q ".agent-coordination" .gitignore 2>/dev/null; then
  echo "# Agent coordination (temporary)" >> .gitignore
  echo ".agent-coordination/" >> .gitignore
  echo "worktrees/" >> .gitignore
fi

# List all worktrees
echo ""
echo "🌳 Git Worktree List:"
git worktree list

echo ""
echo "=========================================================="
echo "✅ Git worktree setup complete!"
echo ""
echo "Next steps:"
echo "  1. Review .agent-coordination/status.json"
echo "  2. Run: ./scripts/launch-agents.sh"
echo "  3. Monitor: ./scripts/monitor-agents.sh"
echo ""
