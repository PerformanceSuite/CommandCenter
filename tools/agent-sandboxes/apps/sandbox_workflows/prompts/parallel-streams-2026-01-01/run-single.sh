#!/bin/bash
# Run a single parallel stream
#
# Usage: ./run-single.sh <stream>
#
# Streams:
#   a, multi-tenant  - Multi-tenant isolation fix
#   b, skills        - Skills foundation
#   c, alertmanager  - AlertManager deployment
#   d, docs          - Doc archival

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"

cd "$WORKFLOW_DIR"

# Parse argument
STREAM="${1:-}"

case "$STREAM" in
    a|multi-tenant)
        PROMPT_FILE="01-multi-tenant-fix.md"
        STREAM_NAME="Multi-tenant Fix"
        TURNS=80
        ;;
    b|skills)
        PROMPT_FILE="02-skills-foundation.md"
        STREAM_NAME="Skills Foundation"
        TURNS=100
        ;;
    c|alertmanager)
        PROMPT_FILE="03-alertmanager-deploy.md"
        STREAM_NAME="AlertManager Deploy"
        TURNS=60
        ;;
    d|docs)
        PROMPT_FILE="04-doc-archival.md"
        STREAM_NAME="Doc Archival"
        TURNS=60
        ;;
    *)
        echo "Usage: $0 <stream>"
        echo ""
        echo "Streams:"
        echo "  a, multi-tenant  - Multi-tenant isolation fix (~\$2-3)"
        echo "  b, skills        - Skills foundation (~\$3-4)"
        echo "  c, alertmanager  - AlertManager deployment (~\$1-2)"
        echo "  d, docs          - Doc archival (~\$1-2)"
        exit 1
        ;;
esac

# Verify environment
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    exit 1
fi

source .env

if [ -z "$ANTHROPIC_API_KEY" ] || [ -z "$E2B_API_KEY" ] || [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Missing required environment variables"
    exit 1
fi

REPO_URL="https://github.com/PerformanceSuite/CommandCenter"
BASE_BRANCH="main"

echo "🚀 Running Stream: $STREAM_NAME"
echo "   Prompt: $PROMPT_FILE"
echo "   Max turns: $TURNS"
echo ""

uv run obox "$REPO_URL" \
    -p "$SCRIPT_DIR/$PROMPT_FILE" \
    -b "$BASE_BRANCH" \
    -m sonnet \
    -t "$TURNS"

echo ""
echo "✅ Stream complete!"
echo "   Check PR: gh pr list --repo PerformanceSuite/CommandCenter"
