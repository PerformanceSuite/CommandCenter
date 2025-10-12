#!/bin/bash
# validation-dashboard.sh
# Real-time validation dashboard for Phase 1a

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

clear

echo -e "${BOLD}${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║         Phase 1a Validation & Deployment Dashboard            ║${NC}"
echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Last Updated: $(date)${NC}"
echo ""

# Agent Status Section
echo -e "${BOLD}━━━ Agent Status ━━━${NC}"
echo ""

for i in 1 2 3; do
    status_file=".agent-coordination/agent${i}-status.txt"
    if [ -f "$status_file" ]; then
        agent_name=$(grep "^Agent:" "$status_file" | cut -d: -f2 | xargs)
        status=$(grep "^Status:" "$status_file" | cut -d: -f2 | xargs)
        progress=$(grep "^Progress:" "$status_file" | cut -d: -f2 | xargs)

        if [ "$status" == "COMPLETE" ] || [ "$status" == "SUCCESS" ]; then
            echo -e "  ${GREEN}✅ Agent ${i}:${NC} $agent_name - $status ($progress)"
        else
            echo -e "  ${YELLOW}⏳ Agent ${i}:${NC} $agent_name - $status ($progress)"
        fi
    else
        echo -e "  ${RED}❌ Agent ${i}:${NC} Status file not found (not started)"
    fi
done

echo ""

# PR CI Status Section
echo -e "${BOLD}━━━ Pull Request CI Status ━━━${NC}"
echo ""

# PR #18
pr18_fails=$(gh pr view 18 --json statusCheckRollup --jq '.statusCheckRollup[] | select(.conclusion != "SUCCESS" and .conclusion != "SKIPPED" and .status == "COMPLETED") | .name' 2>/dev/null | wc -l | tr -d ' ')
pr18_running=$(gh pr view 18 --json statusCheckRollup --jq '.statusCheckRollup[] | select(.status == "IN_PROGRESS") | .name' 2>/dev/null | wc -l | tr -d ' ')

if [ "$pr18_fails" -eq 0 ] && [ "$pr18_running" -eq 0 ]; then
    echo -e "  ${GREEN}✅ PR #18 (VIZTRTR):${NC} All checks passing"
elif [ "$pr18_running" -gt 0 ]; then
    echo -e "  ${YELLOW}⏳ PR #18 (VIZTRTR):${NC} $pr18_running checks running, $pr18_fails failed"
else
    echo -e "  ${RED}❌ PR #18 (VIZTRTR):${NC} $pr18_fails checks failing"
fi

# PR #19
pr19_fails=$(gh pr view 19 --json statusCheckRollup --jq '.statusCheckRollup[] | select(.conclusion != "SUCCESS" and .conclusion != "SKIPPED" and .status == "COMPLETED") | .name' 2>/dev/null | wc -l | tr -d ' ')
pr19_running=$(gh pr view 19 --json statusCheckRollup --jq '.statusCheckRollup[] | select(.status == "IN_PROGRESS") | .name' 2>/dev/null | wc -l | tr -d ' ')

if [ "$pr19_fails" -eq 0 ] && [ "$pr19_running" -eq 0 ]; then
    echo -e "  ${GREEN}✅ PR #19 (Security):${NC} All checks passing"
elif [ "$pr19_running" -gt 0 ]; then
    echo -e "  ${YELLOW}⏳ PR #19 (Security):${NC} $pr19_running checks running, $pr19_fails failed"
else
    echo -e "  ${RED}❌ PR #19 (Security):${NC} $pr19_fails checks failing"
fi

echo ""

# Validation Levels Section
echo -e "${BOLD}━━━ Validation Levels ━━━${NC}"
echo ""

# Level 1
agent1_ok=false
agent2_ok=false
agent3_ok=false
[ -f ".agent-coordination/agent1-status.txt" ] && grep -q "COMPLETE\|SUCCESS" ".agent-coordination/agent1-status.txt" && agent1_ok=true
[ -f ".agent-coordination/agent2-status.txt" ] && grep -q "COMPLETE\|SUCCESS" ".agent-coordination/agent2-status.txt" && agent2_ok=true
[ -f ".agent-coordination/agent3-status.txt" ] && grep -q "COMPLETE\|SUCCESS" ".agent-coordination/agent3-status.txt" && agent3_ok=true

if $agent1_ok && $agent2_ok && $agent3_ok; then
    echo -e "  ${GREEN}✅ Level 1:${NC} All agents complete"
else
    echo -e "  ${YELLOW}⏳ Level 1:${NC} Waiting for agents to complete"
fi

# Level 2
if [ -f ".agent-coordination/phase1a-status.json" ] && [ -f ".agent-coordination/phase1a-merge-queue.json" ]; then
    echo -e "  ${GREEN}✅ Level 2:${NC} Integration files present"
else
    echo -e "  ${YELLOW}⏳ Level 2:${NC} Integration validation pending"
fi

# Level 3
ci18_ok=false
ci19_ok=false
[ "$pr18_fails" -eq 0 ] && [ "$pr18_running" -eq 0 ] && ci18_ok=true
[ "$pr19_fails" -eq 0 ] && [ "$pr19_running" -eq 0 ] && ci19_ok=true

if $ci18_ok && $ci19_ok; then
    echo -e "  ${GREEN}✅ Level 3:${NC} Both PRs ready to merge"
else
    echo -e "  ${YELLOW}⏳ Level 3:${NC} Waiting for CI to pass"
fi

echo ""

# Overall Status
echo -e "${BOLD}━━━ Overall Status ━━━${NC}"
echo ""

if $agent1_ok && $agent2_ok && $agent3_ok && $ci18_ok && $ci19_ok; then
    echo -e "  ${GREEN}${BOLD}🎉 ALL VALIDATIONS PASSED - READY FOR MERGE!${NC}"
    echo ""
    echo "  Next step: Run auto-merge sequence"
    echo "  Command: bash .agent-coordination/auto-merge-phase1a.sh"
else
    blockers=()
    ! $agent1_ok && blockers+=("Agent 1 incomplete")
    ! $agent2_ok && blockers+=("Agent 2 incomplete")
    ! $agent3_ok && blockers+=("Agent 3 incomplete")
    ! $ci18_ok && blockers+=("PR #18 CI")
    ! $ci19_ok && blockers+=("PR #19 CI")

    echo -e "  ${YELLOW}⏳ Validation in progress...${NC}"
    echo ""
    echo "  Blockers:"
    for blocker in "${blockers[@]}"; do
        echo "    - $blocker"
    done
fi

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Run this dashboard again: bash .agent-coordination/validation-dashboard.sh"
echo "View detailed logs: cat .agent-coordination/validation-timeline.log"
echo "Monitor continuously: bash .agent-coordination/monitor-phase1a.sh"
echo ""
