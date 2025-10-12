#!/bin/bash
# diagnose-ci-failures.sh
# Detailed CI failure analysis for Phase 1a PRs

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔬 CI Failure Diagnostic Report"
echo "================================"
echo "Generated: $(date)"
echo ""

diagnose_pr() {
    local pr_num=$1
    local pr_name=$2

    echo -e "${BLUE}PR #${pr_num}: ${pr_name}${NC}"
    echo "-----------------------------------"

    # Get PR details
    pr_info=$(gh pr view "$pr_num" --json title,url,headRefName,mergeable,mergeStateStatus)
    echo "URL: $(echo "$pr_info" | jq -r '.url')"
    echo "Branch: $(echo "$pr_info" | jq -r '.headRefName')"
    echo "Mergeable: $(echo "$pr_info" | jq -r '.mergeable')"
    echo "Merge State: $(echo "$pr_info" | jq -r '.mergeStateStatus')"
    echo ""

    # Get all status checks
    echo "Status Checks:"
    gh pr view "$pr_num" --json statusCheckRollup --jq '.statusCheckRollup[] | "  [\(.conclusion // "PENDING")] \(.name)"'
    echo ""

    # Get failing checks with details
    local failing=$(gh pr view "$pr_num" --json statusCheckRollup --jq '.statusCheckRollup[] | select(.conclusion != "SUCCESS" and .conclusion != "SKIPPED") | {name: .name, conclusion: .conclusion, description: .description}')

    if [ -n "$failing" ] && [ "$failing" != "" ]; then
        echo -e "${RED}Failing Checks:${NC}"
        echo "$failing" | jq -r '"\n  Check: \(.name)\n  Status: \(.conclusion)\n  Details: \(.description // "N/A")"'
    else
        echo -e "${GREEN}✅ All checks passing!${NC}"
    fi

    # Get recent workflow runs
    echo ""
    echo "Recent Workflow Runs:"
    gh run list --repo PerformanceSuite/CommandCenter --branch "$(echo "$pr_info" | jq -r '.headRefName')" --limit 5 --json databaseId,workflowName,conclusion,createdAt,updatedAt | jq -r '.[] | "  [\(.conclusion // "PENDING")] \(.workflowName) - \(.createdAt)"'

    echo ""
    echo ""
}

# Diagnose both PRs
diagnose_pr 18 "VIZTRTR MCP SDK Fixes"
diagnose_pr 19 "Security Critical Fixes"

# Overall summary
echo "==================================="
echo "Overall Summary"
echo "==================================="

pr18_fails=$(gh pr view 18 --json statusCheckRollup --jq '.statusCheckRollup[] | select(.conclusion != "SUCCESS" and .conclusion != "SKIPPED") | .name' | wc -l | tr -d ' ')
pr19_fails=$(gh pr view 19 --json statusCheckRollup --jq '.statusCheckRollup[] | select(.conclusion != "SUCCESS" and .conclusion != "SKIPPED") | .name' | wc -l | tr -d ' ')

echo "PR #18 failing checks: $pr18_fails"
echo "PR #19 failing checks: $pr19_fails"
echo ""

if [ "$pr18_fails" -eq 0 ] && [ "$pr19_fails" -eq 0 ]; then
    echo -e "${GREEN}✅ Both PRs ready to merge!${NC}"
    echo "Next step: Run ./agent-coordination/validate-phase1a.sh"
else
    echo -e "${YELLOW}⏳ Waiting for CI fixes...${NC}"
    echo "Agent 1 should be working on fixing these issues"
fi
