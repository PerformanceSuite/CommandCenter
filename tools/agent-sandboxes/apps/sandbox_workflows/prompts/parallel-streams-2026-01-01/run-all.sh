#!/bin/bash
# Run all parallel streams for January 1, 2026
#
# Usage: ./run-all.sh
#
# This launches 4 parallel E2B sandbox agents, each working on a separate branch.
# Total estimated cost: ~$7-11
# Total estimated time: 2-4 hours

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"

cd "$WORKFLOW_DIR"

# Verify environment
echo "🔍 Checking environment..."
if [ ! -f .env ]; then
    echo "❌ .env file not found. Create it with ANTHROPIC_API_KEY, E2B_API_KEY, GITHUB_TOKEN"
    exit 1
fi

source .env

if [ -z "$ANTHROPIC_API_KEY" ] || [ -z "$E2B_API_KEY" ] || [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Missing required environment variables"
    echo "   Required: ANTHROPIC_API_KEY, E2B_API_KEY, GITHUB_TOKEN"
    exit 1
fi

echo "✅ Environment OK"
echo ""

# Repository URL
REPO_URL="https://github.com/PerformanceSuite/CommandCenter"
BASE_BRANCH="main"

echo "🚀 Launching 4 parallel streams..."
echo ""
echo "Stream A: Multi-tenant Fix"
echo "Stream B: Skills Foundation"
echo "Stream C: AlertManager Deploy"
echo "Stream D: Doc Archival"
echo ""
echo "Estimated cost: ~\$7-11"
echo "Estimated time: 2-4 hours"
echo ""

# Confirm
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "📦 Starting agents..."
echo ""

# Stream A: Multi-tenant Fix
echo "🔧 Stream A: Multi-tenant Fix"
uv run obox "$REPO_URL" \
    -p "$SCRIPT_DIR/01-multi-tenant-fix.md" \
    -b "$BASE_BRANCH" \
    -m sonnet \
    -t 80 \
    --log-prefix "stream-a" &
PID_A=$!
echo "   PID: $PID_A"

# Small delay to avoid rate limits
sleep 5

# Stream B: Skills Foundation
echo "🧠 Stream B: Skills Foundation"
uv run obox "$REPO_URL" \
    -p "$SCRIPT_DIR/02-skills-foundation.md" \
    -b "$BASE_BRANCH" \
    -m sonnet \
    -t 100 \
    --log-prefix "stream-b" &
PID_B=$!
echo "   PID: $PID_B"

sleep 5

# Stream C: AlertManager Deploy
echo "🔔 Stream C: AlertManager Deploy"
uv run obox "$REPO_URL" \
    -p "$SCRIPT_DIR/03-alertmanager-deploy.md" \
    -b "$BASE_BRANCH" \
    -m sonnet \
    -t 60 \
    --log-prefix "stream-c" &
PID_C=$!
echo "   PID: $PID_C"

sleep 5

# Stream D: Doc Archival
echo "📚 Stream D: Doc Archival"
uv run obox "$REPO_URL" \
    -p "$SCRIPT_DIR/04-doc-archival.md" \
    -b "$BASE_BRANCH" \
    -m sonnet \
    -t 60 \
    --log-prefix "stream-d" &
PID_D=$!
echo "   PID: $PID_D"

echo ""
echo "✅ All streams launched!"
echo ""
echo "Monitor progress:"
echo "  tail -f sandbox_agent_working_dir/logs/stream-*.log"
echo ""
echo "Check PRs:"
echo "  gh pr list --repo PerformanceSuite/CommandCenter"
echo ""
echo "Waiting for all streams to complete..."
echo ""

# Wait for all
wait $PID_A
echo "✅ Stream A complete"

wait $PID_B
echo "✅ Stream B complete"

wait $PID_C
echo "✅ Stream C complete"

wait $PID_D
echo "✅ Stream D complete"

echo ""
echo "🎉 All streams complete!"
echo ""
echo "Next steps:"
echo "1. Review PRs: gh pr list --repo PerformanceSuite/CommandCenter"
echo "2. Run tests locally: cd backend && uv run pytest"
echo "3. Merge PRs in order: A → B → C → D"
