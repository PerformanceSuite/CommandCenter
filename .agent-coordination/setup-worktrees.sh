#!/bin/bash
# Setup git worktrees for parallel agent development

set -e

WORKTREE_DIR=".agent-worktrees"
BASE_DIR=$(pwd)

echo "🚀 Setting up git worktrees for MCP development..."
echo ""

# Phase 1 agents
AGENTS=(
    "agent/mcp-core-infrastructure:mcp-core"
    "agent/project-analyzer-service:project-analyzer"
    "agent/cli-interface:cli-interface"
)

for agent in "${AGENTS[@]}"; do
    IFS=':' read -r branch worktree <<< "$agent"

    echo "📦 Creating worktree for $branch..."

    # Create branch from main
    git branch "$branch" main 2>/dev/null || echo "  ℹ️  Branch $branch already exists"

    # Create worktree
    if [ -d "$WORKTREE_DIR/$worktree" ]; then
        echo "  ⚠️  Worktree already exists at $WORKTREE_DIR/$worktree"
    else
        git worktree add "$WORKTREE_DIR/$worktree" "$branch"
        echo "  ✅ Worktree created at $WORKTREE_DIR/$worktree"
    fi

    echo ""
done

echo "✨ All Phase 1 worktrees created!"
echo ""
echo "📋 Worktree locations:"
git worktree list
