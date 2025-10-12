#!/bin/bash
# auto-merge-phase1a.sh
# Automated merge sequence for Phase 1a PRs

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🤖 Phase 1a Auto-Merge Sequence"
echo "================================"
echo ""

# Function to wait for CI
wait_for_ci() {
    local pr_number=$1
    local max_wait=3600  # 1 hour
    local elapsed=0

    while [ $elapsed -lt $max_wait ]; do
        failing=$(gh pr view "$pr_number" --json statusCheckRollup --jq '.statusCheckRollup[] | select(.conclusion != "SUCCESS") | .name')

        if [ -z "$failing" ]; then
            echo -e "${GREEN}✅ PR #$pr_number CI passed${NC}"
            return 0
        fi

        echo -e "${YELLOW}⏳ Waiting for PR #$pr_number CI... (${elapsed}s elapsed)${NC}"
        echo "   Failing: $failing"
        sleep 60
        elapsed=$((elapsed + 60))
    done

    echo -e "${RED}❌ PR #$pr_number CI timeout${NC}"
    return 1
}

# Step 1: Merge PR #19 (Security)
echo "Step 1: Merging PR #19 (Security Critical Fixes)"
echo "------------------------------------------------"

if wait_for_ci 19; then
    gh pr merge 19 \
        --squash \
        --auto \
        --subject "Phase 1a: Security Critical Fixes 🔒" \
        --body "Automated merge: CWE-306 and CWE-78 fixes ready for production"

    echo -e "${GREEN}✅ PR #19 merge initiated${NC}"
else
    echo -e "${RED}❌ PR #19 CI failed, aborting${NC}"
    exit 1
fi

# Wait for merge to complete
echo "Waiting for PR #19 merge to complete..."
sleep 120

# Step 2: Merge PR #18 (VIZTRTR)
echo ""
echo "Step 2: Merging PR #18 (VIZTRTR MCP SDK Fixes)"
echo "-----------------------------------------------"

if wait_for_ci 18; then
    gh pr merge 18 \
        --squash \
        --auto \
        --subject "Phase 1a: VIZTRTR MCP SDK Fixes - Production Ready" \
        --body "Automated merge: First production MCP server ready to deploy"

    echo -e "${GREEN}✅ PR #18 merge initiated${NC}"
else
    echo -e "${RED}❌ PR #18 CI failed, aborting${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Phase 1a Complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Verify deployments"
echo "  2. Run integration tests"
echo "  3. Launch Phase 1b agents"
