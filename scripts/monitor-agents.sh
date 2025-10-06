#!/bin/bash
# monitor-agents.sh - Real-time monitoring dashboard for agents

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Progress bar function
progress_bar() {
  local progress=$1
  local width=20
  local filled=$(echo "$progress * $width" | bc | awk '{print int($1)}')
  local empty=$((width - filled))

  printf "["
  printf "${GREEN}%0.s█${NC}" $(seq 1 $filled)
  printf "%0.s░" $(seq 1 $empty)
  printf "]"
}

# Clear screen and show header
clear
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     AGENT PARALLEL EXECUTION - LIVE STATUS                     ║"
echo "╔════════════════════════════════════════════════════════════════╗"
echo ""

# Monitor loop
while true; do
  # Move cursor to top
  tput cup 4 0

  # Read status
  STATUS_FILE=".agent-coordination/status.json"

  if [ ! -f "$STATUS_FILE" ]; then
    echo "❌ Status file not found. Run ./scripts/setup-worktrees.sh first"
    exit 1
  fi

  # Agent list
  AGENTS=(
    "security-agent"
    "backend-agent"
    "frontend-agent"
    "rag-agent"
    "devops-agent"
    "github-agent"
    "testing-agent"
    "docs-agent"
  )

  # Display each agent status
  for agent in "${AGENTS[@]}"; do
    status=$(jq -r ".agents[\"$agent\"].status" "$STATUS_FILE")
    progress=$(jq -r ".agents[\"$agent\"].progress" "$STATUS_FILE")
    review_score=$(jq -r ".agents[\"$agent\"].review_score" "$STATUS_FILE")
    current_task=$(jq -r ".agents[\"$agent\"].current_task" "$STATUS_FILE")
    blocked_by=$(jq -r ".agents[\"$agent\"].blocked_by | join(\", \")" "$STATUS_FILE")
    pr_url=$(jq -r ".agents[\"$agent\"].pr_url" "$STATUS_FILE")

    # Format progress as percentage
    progress_pct=$(echo "$progress * 100" | bc | awk '{print int($1)}')

    # Status emoji
    case $status in
      "pending")
        status_emoji="⏸️ "
        status_color=$YELLOW
        ;;
      "in_progress")
        status_emoji="▶️ "
        status_color=$BLUE
        ;;
      "completed")
        status_emoji="✅"
        status_color=$GREEN
        ;;
      "failed")
        status_emoji="❌"
        status_color=$RED
        ;;
      *)
        status_emoji="❓"
        status_color=$NC
        ;;
    esac

    # Review score display
    if [ "$review_score" = "null" ]; then
      review_display="-"
    else
      if [ "$review_score" -eq 10 ]; then
        review_display="${GREEN}$review_score/10 ✅${NC}"
      else
        review_display="$review_score/10"
      fi
    fi

    # Blocked display
    if [ -n "$blocked_by" ] && [ "$blocked_by" != "" ]; then
      blocked_display=" ${RED}[blocked by: $blocked_by]${NC}"
    else
      blocked_display=""
    fi

    # Display agent row
    printf "${status_color}%s %-18s${NC} " "$status_emoji" "$agent"
    progress_bar "$progress"
    printf " %3d%% " "$progress_pct"
    printf " Review: %-15s" "$review_display"
    printf "%s" "$blocked_display"

    # Current task on next line if active
    if [ "$current_task" != "null" ] && [ -n "$current_task" ]; then
      printf "\n   ${CYAN}└─ %s${NC}" "$current_task"
    fi

    # PR URL if exists
    if [ "$pr_url" != "null" ] && [ -n "$pr_url" ]; then
      printf "\n   ${BLUE}└─ PR: %s${NC}" "$pr_url"
    fi

    echo ""
  done

  echo ""
  echo "────────────────────────────────────────────────────────────────"

  # Summary statistics
  completed_count=$(jq -r '.completed | length' "$STATUS_FILE")
  failed_count=$(jq -r '.failed | length' "$STATUS_FILE")

  # Count PRs
  pr_count=$(jq -r '[.agents[] | select(.pr_url != null)] | length' "$STATUS_FILE")
  merged_count=$(jq -r '.merged | length' .agent-coordination/merge-queue.json 2>/dev/null || echo "0")

  echo "📊 Summary:"
  echo "   PRs: ${BLUE}$pr_count open${NC}, ${GREEN}$merged_count merged${NC}, ${RED}$failed_count failed${NC}"
  echo "   Agents: ${GREEN}$completed_count completed${NC}, ${YELLOW}$((8 - completed_count - failed_count)) in progress${NC}"

  # Test status (if available)
  if [ -f ".agent-coordination/test-results.json" ]; then
    tests_pass=$(jq -r '.passing' .agent-coordination/test-results.json)
    tests_fail=$(jq -r '.failing' .agent-coordination/test-results.json)
    coverage=$(jq -r '.coverage' .agent-coordination/test-results.json)

    echo "   Tests: ${GREEN}$tests_pass passing${NC}, ${RED}$tests_fail failing${NC}"
    echo "   Coverage: ${BLUE}$coverage%${NC} (target: 80%)"
  fi

  echo ""
  echo "────────────────────────────────────────────────────────────────"
  echo "Press Ctrl+C to exit | Refreshing every 2 seconds..."
  echo ""

  # Check if all agents are complete
  if [ "$completed_count" -eq 8 ]; then
    echo ""
    echo "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo "${GREEN}║              🎉 ALL AGENTS COMPLETED! 🎉                       ║${NC}"
    echo "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review all PRs"
    echo "  2. Run integration tests"
    echo "  3. Deploy to production"
    echo ""
    break
  fi

  # Wait before refresh
  sleep 2
done
