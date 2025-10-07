# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgentFlow is an autonomous multi-agent orchestration system that runs multiple Claude Code agents in parallel using git worktrees. Each agent works independently in isolated worktrees, creates pull requests, undergoes rigorous review (10/10 threshold), and merges changes through a coordination system.

## Common Commands

### Running the System
```bash
# Launch AgentFlow with default settings
npm start

# Launch with custom configuration
./scripts/agentflow.sh --project my-app --agents 8 --threshold 9

# Run initial setup
npm run setup
```

### Development & Testing
```bash
# Run all tests
npm test

# Run unit tests only
npm run test:unit

# Run integration tests only
npm run test:integration

# Lint code
npm lint

# Format code
npm run format
```

### Monitoring
```bash
# Open web interface
npm run web

# Start monitoring dashboard server
npm run dashboard

# Live CLI monitoring
npm run monitor
# Or: ./scripts/monitor.sh --live
```

## Architecture

### Multi-Agent Orchestration System

**Core Workflow:**
1. **Initialization** - Creates git worktrees for each agent in `.agentflow/worktrees/`
2. **Parallel Execution** - Agents work simultaneously in isolated branches (`agent/{name}`)
3. **Review Phase** - Each PR scored 0-10 across 5 categories (functionality, quality, performance, security, testing)
4. **Coordination** - Dependency-aware merge ordering with conflict detection
5. **Integration** - Automated testing and validation after each merge

**Git Worktree Strategy:**
- Each agent operates in its own worktree under `.agentflow/worktrees/{agent-name}`
- Branches follow pattern: `agent/{agent-name}`
- This enables true parallel work without interference
- Worktrees are cleaned up after successful merges

**Merge Coordination:**
The coordination agent analyzes dependencies and determines merge order:
1. Infrastructure changes (Docker, K8s, CI/CD)
2. Database migrations (schema, indexes)
3. Backend API changes (endpoints, logic)
4. Frontend changes (UI components, state)
5. Documentation updates

### Agent System

**Agent Types:**
- **Core** (backend, frontend, database, testing, infrastructure) - Primary development agents
- **Quality** (ui-ux, security, performance, best-practices, dependencies) - Review and validation
- **Specialized** (documentation, localization, monitoring, devops, data-validation) - Domain-specific tasks

**Agent Configuration:**
Located in `config/agents.json`. Each agent has:
- `name` - Unique identifier
- `type` - Category (core/quality/specialized)
- `responsibilities` - Specific tasks handled
- `technologies` - Tech stack expertise
- `review_focus` - What to evaluate in reviews
- `model` (optional) - Specific Claude model (e.g., UI/UX uses Opus 4.1 for vision)

**Prompt Templates:**
- `prompts/base.md` - Foundation for all agents (development process, review rubric, communication protocol)
- `prompts/review.md` - Code review template with 5-category scoring system
- `prompts/coordinate.md` - Merge coordination logic and conflict resolution

### Configuration System

**Main Config** (`config/default.json`):
- `workflow.maxParallel` - Concurrent agent limit (default: 5)
- `workflow.reviewThreshold` - Minimum passing score (default: 10/10)
- `workflow.mergeStrategy` - "squash", "merge", or "rebase"
- `workflow.minCoverage` - Test coverage requirement (default: 80%)
- `claude.model` - Default model for agents
- `git.branchStrategy` - "gitflow" pattern
- `paths` - All AgentFlow artifacts stored in `.agentflow/`

**Environment Variables:**
```bash
PROJECT_NAME - Project identifier
MAX_PARALLEL - Override concurrent agents
REVIEW_THRESHOLD - Override review threshold
CLAUDE_MODEL - Override default model
```

### Review System

**Scoring Rubric (0-10 total):**
1. **Functionality (2 pts)** - Features work, edge cases handled
2. **Code Quality (2 pts)** - Readable, follows best practices
3. **Performance (2 pts)** - Optimized, no bottlenecks
4. **Security (2 pts)** - No vulnerabilities, proper validation
5. **Testing (2 pts)** - Comprehensive coverage, all passing

**Iterative Review:**
- Agents receive feedback when score < threshold
- Agents improve and resubmit automatically
- Process continues until passing score achieved
- Review metadata stored in `.agentflow/reviews/{agent}-pr.json`

### File Structure

**Runtime Artifacts:**
- `.agentflow/worktrees/` - Git worktrees for each agent
- `.agentflow/logs/` - Execution logs per agent with timestamps
- `.agentflow/reviews/` - PR metadata and review scores
- `.agentflow/artifacts/` - Build outputs and generated files
- `.agentflow/cache/` - Cached data for performance

**Configuration:**
- `config/agents.json` - Agent definitions and capabilities
- `config/default.json` - System-wide settings
- `config/workflows.json` - Workflow templates (if exists)

**Scripts:**
- `scripts/agentflow.sh` - Main orchestration script
- `scripts/setup.sh` - Initial setup and dependency checks
- `scripts/monitor.sh` - Real-time monitoring CLI
- `scripts/utils/` - Shell utilities (colors, functions, git helpers)

## Working with AgentFlow

### Adding Custom Agents

1. Add agent definition to `config/agents.json`
2. Create agent-specific instructions in `agents/{name}/instructions.md`
3. Agent will automatically be picked up by orchestration system

### Customizing Workflows

The main script (`scripts/agentflow.sh`) handles the full lifecycle. Key functions:
- `init_project()` - Sets up directories and git
- `load_agents()` - Reads agent configs
- `setup_worktrees()` - Creates isolated work environments
- `launch_agent()` - Spawns agent with prompt template
- `review_agent_work()` - Evaluates PR against rubric
- `coordinate_merges()` - Dependency-aware merge execution

### Understanding Merge Strategies

**Squash** (default):
- Combines all commits into one
- Clean history, easy revert
- Best for feature additions and bug fixes

**Merge**:
- Preserves all commits with merge commit
- Full history maintained
- Use for large multi-commit features

**Rebase**:
- Linear history, no merge commits
- Replays commits on top of main
- Use when linear timeline preferred

### Monitoring Agent Progress

**Web Dashboard** (port 3000):
- Visual status for all agents
- Real-time progress updates
- Review scores and PR metadata

**CLI Monitoring**:
- `./scripts/monitor.sh --live` for terminal-based dashboard
- Shows running/complete status
- Displays review scores as they complete

**Logs**:
- Per-agent logs: `.agentflow/logs/{agent}-{timestamp}.log`
- Review metadata: `.agentflow/reviews/{agent}-pr.json`
- System events tracked with timestamps

## Key Technical Details

**Dependencies Required:**
- Node.js ≥18.0.0
- git (for worktrees and branching)
- jq (for JSON processing in shell scripts)
- Claude Code CLI (for agent execution)

**Commit Message Format:**
Follows conventional commits:
```
type(scope): description

Agent: {agent-name}
Task: {task-description}
Timestamp: {ISO-8601}
Model: {claude-model}
```

**PR Metadata Structure:**
```json
{
  "agent": "backend",
  "branch": "agent/backend",
  "task": "Implement REST API",
  "status": "approved|pending_review|needs_work",
  "score": 10,
  "files_changed": 15,
  "additions": 450,
  "deletions": 23
}
```

## Troubleshooting

**Worktree Conflicts:**
If worktree creation fails, the script automatically cleans up and recreates. Manual cleanup:
```bash
git worktree remove .agentflow/worktrees/{agent} --force
git branch -D agent/{agent}
```

**Review Score Debugging:**
Check review logs and PR metadata in `.agentflow/reviews/` to understand why agents didn't meet threshold.

**Parallel Execution Limits:**
If system resources are constrained, reduce `MAX_PARALLEL` or use `--agents` flag with lower value.
