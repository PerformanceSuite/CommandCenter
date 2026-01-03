#!/bin/bash
# monitor-phase1a.sh
# Continuous monitoring script for Phase 1a agents

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ITERATION=0
MAX_ITERATIONS=120  # 10 hours at 5 minute intervals
SLEEP_INTERVAL=300  # 5 minutes

LOG_FILE=".agent-coordination/validation-timeline.log"

log_event() {
    echo "[$(date -u +"%H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

check_agent_status() {
    local agent_num=$1
    local agent_name=$2
    local status_file=".agent-coordination/agent${agent_num}-status.txt"

    if [ -f "$status_file" ]; then
        echo -e "${GREEN}✅${NC} Agent ${agent_num} (${agent_name}) status file exists"
        tail -5 "$status_file" | sed 's/^/     /'
        return 0
    else
        echo -e "${YELLOW}⏳${NC} Agent ${agent_num} (${agent_name}) still working..."
        return 1
    fi
}

check_ci_status() {
    local pr_num=$1
    local pr_name=$2

    # Get all non-SUCCESS checks
    local failures=$(gh pr view "$pr_num" --json statusCheckRollup --jq '.statusCheckRollup[] | select(.conclusion != "SUCCESS" and .conclusion != "SKIPPED") | .name' 2>/dev/null)
    local fail_count=$(echo "$failures" | grep -v '^$' | wc -l | tr -d ' ')

    if [ "$fail_count" -eq 0 ]; then
        echo -e "${GREEN}✅${NC} PR #${pr_num} (${pr_name}) CI passing"
        return 0
    else
        echo -e "${RED}❌${NC} PR #${pr_num} (${pr_name}) has ${fail_count} failing checks:"
        echo "$failures" | sed 's/^/     - /'
        return 1
    fi
}

check_git_status() {
    local dirty=$(git status --porcelain | wc -l | tr -d ' ')

    if [ "$dirty" -eq 0 ]; then
        echo -e "${GREEN}✅${NC} Git working tree clean"
        return 0
    else
        echo -e "${YELLOW}⚠️ ${NC} Git has ${dirty} uncommitted files (may be expected)"
        return 0  # Don't fail on this
    fi
}

# Main monitoring loop
echo "🔍 Starting Phase 1a Monitoring"
echo "================================"
echo ""
log_event "Monitoring started"

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
    ITERATION=$((ITERATION + 1))
    echo ""
    echo -e "${BLUE}=== Iteration ${ITERATION}/${MAX_ITERATIONS} ===${NC}"
    echo "Time: $(date)"
    echo ""

    # Level 1: Check individual agents
    echo "Level 1: Agent Status Checks"
    echo "-----------------------------"

    agent1_ok=false
    agent2_ok=false
    agent3_ok=false

    check_agent_status 1 "CI/CD Fixes" && agent1_ok=true
    check_agent_status 2 "Documentation" && agent2_ok=true
    check_agent_status 3 "Git Coordination" && agent3_ok=true

    echo ""

    # Check CI status even if agents not done
    echo "CI Status Checks"
    echo "----------------"

    ci18_ok=false
    ci19_ok=false

    check_ci_status 18 "VIZTRTR MCP" && ci18_ok=true
    check_ci_status 19 "Security" && ci19_ok=true

    echo ""

    # Check git status
    echo "Git Status Check"
    echo "----------------"
    check_git_status

    echo ""

    # Determine overall status
    if $agent1_ok && $agent2_ok && $agent3_ok && $ci18_ok && $ci19_ok; then
        echo -e "${GREEN}🎉 ALL VALIDATIONS PASSED!${NC}"
        log_event "All validations passed - ready for merge"
        echo ""
        echo "Ready to proceed with auto-merge sequence"
        echo "Run: bash .agent-coordination/auto-merge-phase1a.sh"
        exit 0
    fi

    # Status summary
    echo "Status Summary:"
    echo "---------------"
    $agent1_ok && echo -e "  ${GREEN}✅${NC} Agent 1 (CI/CD)" || echo -e "  ${YELLOW}⏳${NC} Agent 1 (CI/CD)"
    $agent2_ok && echo -e "  ${GREEN}✅${NC} Agent 2 (Docs)" || echo -e "  ${YELLOW}⏳${NC} Agent 2 (Docs)"
    $agent3_ok && echo -e "  ${GREEN}✅${NC} Agent 3 (Git)" || echo -e "  ${YELLOW}⏳${NC} Agent 3 (Git)"
    $ci18_ok && echo -e "  ${GREEN}✅${NC} PR #18 CI" || echo -e "  ${RED}❌${NC} PR #18 CI"
    $ci19_ok && echo -e "  ${GREEN}✅${NC} PR #19 CI" || echo -e "  ${RED}❌${NC} PR #19 CI"

    # Wait before next iteration
    echo ""
    echo "Waiting ${SLEEP_INTERVAL}s before next check..."
    log_event "Iteration ${ITERATION} complete - waiting for next check"
    sleep $SLEEP_INTERVAL
done

# If we get here, we've exceeded max iterations
echo -e "${RED}❌ Maximum iterations exceeded (${MAX_ITERATIONS})${NC}"
log_event "ERROR: Maximum iterations exceeded - manual intervention required"
exit 1
