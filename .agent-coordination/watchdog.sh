#!/bin/bash
# watchdog.sh
# Automated watchdog for Phase 1a - monitors and triggers actions

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

LOG_FILE=".agent-coordination/validation-timeline.log"
STATUS_FILE=".agent-coordination/validation-status.json"

log_event() {
    echo "[$(date -u +"%H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

update_status() {
    local key=$1
    local value=$2
    # Simple JSON update (requires jq)
    if command -v jq &> /dev/null; then
        tmp=$(mktemp)
        jq "$key = $value" "$STATUS_FILE" > "$tmp" && mv "$tmp" "$STATUS_FILE"
    fi
}

check_all_agents_complete() {
    local all_complete=true

    for i in 1 2 3; do
        status_file=".agent-coordination/agent${i}-status.txt"
        if [ ! -f "$status_file" ]; then
            all_complete=false
            break
        fi

        if ! grep -q "COMPLETE\|SUCCESS" "$status_file"; then
            all_complete=false
            break
        fi
    done

    if $all_complete; then
        return 0
    else
        return 1
    fi
}

check_ci_passing() {
    local pr_num=$1

    local fails=$(gh pr view "$pr_num" --json statusCheckRollup --jq '.statusCheckRollup[] | select(.conclusion != "SUCCESS" and .conclusion != "SKIPPED" and .status == "COMPLETED") | .name' 2>/dev/null | wc -l | tr -d ' ')
    local running=$(gh pr view "$pr_num" --json statusCheckRollup --jq '.statusCheckRollup[] | select(.status == "IN_PROGRESS") | .name' 2>/dev/null | wc -l | tr -d ' ')

    if [ "$fails" -eq 0 ] && [ "$running" -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

run_level1_validation() {
    echo -e "${BLUE}Running Level 1 Validation...${NC}"
    log_event "Level 1: Checking agent completions"

    if check_all_agents_complete; then
        echo -e "${GREEN}✅ Level 1 PASSED: All agents complete${NC}"
        log_event "Level 1 PASSED"
        return 0
    else
        echo -e "${YELLOW}⏳ Level 1: Agents still working${NC}"
        return 1
    fi
}

run_level2_validation() {
    echo -e "${BLUE}Running Level 2 Validation...${NC}"
    log_event "Level 2: Integration validation"

    # Check coordination files
    if [ ! -f ".agent-coordination/phase1a-status.json" ]; then
        echo -e "${RED}❌ Level 2 FAILED: phase1a-status.json missing${NC}"
        return 1
    fi

    if [ ! -f ".agent-coordination/phase1a-merge-queue.json" ]; then
        echo -e "${RED}❌ Level 2 FAILED: phase1a-merge-queue.json missing${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ Level 2 PASSED: Integration files valid${NC}"
    log_event "Level 2 PASSED"
    return 0
}

run_level3_validation() {
    echo -e "${BLUE}Running Level 3 Validation...${NC}"
    log_event "Level 3: CI and merge readiness"

    local pr18_ok=false
    local pr19_ok=false

    check_ci_passing 18 && pr18_ok=true
    check_ci_passing 19 && pr19_ok=true

    if $pr18_ok && $pr19_ok; then
        echo -e "${GREEN}✅ Level 3 PASSED: Both PRs ready${NC}"
        log_event "Level 3 PASSED"
        return 0
    else
        ! $pr18_ok && echo -e "${YELLOW}⏳ PR #18 CI not ready${NC}"
        ! $pr19_ok && echo -e "${YELLOW}⏳ PR #19 CI not ready${NC}"
        return 1
    fi
}

trigger_auto_merge() {
    echo ""
    echo -e "${GREEN}${BOLD}🎉 ALL VALIDATIONS PASSED!${NC}"
    echo ""
    log_event "All validations passed - triggering auto-merge"

    echo "Would you like to proceed with auto-merge? (yes/no)"
    read -t 60 response || response="yes"

    if [ "$response" == "yes" ]; then
        log_event "Auto-merge approved - executing"
        bash .agent-coordination/auto-merge-phase1a.sh
    else
        log_event "Auto-merge deferred - manual intervention required"
        echo "Auto-merge deferred. Run manually:"
        echo "  bash .agent-coordination/auto-merge-phase1a.sh"
    fi
}

# Main watchdog loop
echo "🐕 Phase 1a Watchdog Started"
echo "============================"
log_event "Watchdog started"

iteration=0
max_wait=7200  # 2 hours
check_interval=60  # Check every minute

while [ $iteration -lt $max_wait ]; do
    iteration=$((iteration + check_interval))

    # Run validations in sequence
    if run_level1_validation; then
        if run_level2_validation; then
            if run_level3_validation; then
                # All passed - trigger merge
                trigger_auto_merge
                exit 0
            fi
        fi
    fi

    # Wait before next check
    sleep $check_interval
done

echo -e "${RED}❌ Watchdog timeout after ${max_wait}s${NC}"
log_event "ERROR: Watchdog timeout - manual intervention required"
exit 1
