# Sandbox Fork - Parallel Agent Execution

Run parallel Claude Code agents in isolated E2B cloud sandboxes for multi-stream development tasks.

## Key Features

- **Parallel Execution**: Run 1-100 agents in parallel threads with independent sandboxes
- **Model Selection**: Choose between Opus, Sonnet, or Haiku models per task
- **Auto-Branch Generation**: Automatically creates unique branches for each fork
- **Thread-Safe Logging**: Each fork gets its own detailed log file with all agent activity
- **Full Observability**: 6 hook types capture every tool use, prompt, result, and error
- **Path Security**: Hook-based restrictions prevent accidental local filesystem access
- **GitHub Integration**: GitHub token support for automated push/PR operations
- **Cost Tracking**: Per-fork and total cost tracking with detailed token usage
- **VSCode Integration**: Auto-opens all log files for real-time monitoring

## Installation

```bash
cd apps/sandbox_workflows
uv sync
```

## Configuration

Copy `.env.sample` to `.env` and fill in your API keys:
```bash
cp .env.sample .env
```

Edit `.env` and add:
- `ANTHROPIC_API_KEY` - Your Anthropic API key for Claude
- `E2B_API_KEY` - Your E2B API key for sandbox management
- `GITHUB_TOKEN` - GitHub Personal Access Token for git push/PR operations (use classic PAT with 'repo' scope)

## Usage

### ⚠️ IMPORTANT: Correct CLI Syntax

```bash
# ✅ CORRECT - repo URL is the first positional argument
uv run obox <repo_url> --prompt <prompt> [options]

# ❌ WRONG - there is no 'sandbox-fork' subcommand
uv run obox sandbox-fork <repo_url>  # THIS WILL FAIL
```

### Basic Usage

```bash
uv run obox https://github.com/user/repo --prompt "Add unit tests to all functions"
```

### Multiple Parallel Agents

```bash
uv run obox https://github.com/user/repo \
  --prompt "Refactor the codebase to use async/await" \
  --forks 5
```

### Specific Branch

```bash
uv run obox https://github.com/user/repo \
  --branch feature/new-api \
  --prompt "Review and document the new API endpoints"
```

### Prompt from File

```bash
uv run obox https://github.com/user/repo \
  --prompt ./prompts/my-task.md \
  --forks 3
```

### With Different Models

```bash
# Use faster Haiku model
uv run obox https://github.com/user/repo \
  --prompt "Quick code review" \
  --model haiku

# Use powerful Opus model
uv run obox https://github.com/user/repo \
  --prompt "Complex refactoring task" \
  --model opus
```

### With Max Turns Limit

```bash
uv run obox https://github.com/user/repo \
  --prompt "Add comprehensive documentation" \
  --max-turns 50
```

## CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `--prompt` | `-p` | **Required.** Prompt text or path to .md file |
| `--branch` | `-b` | Git branch to checkout/create |
| `--forks` | `-f` | Number of parallel agents (default: 1) |
| `--model` | `-m` | Model: opus, sonnet, haiku (default: sonnet) |
| `--max-turns` | `-t` | Maximum conversation turns |

## How It Works

1. **Validation**: Validates repository URL, branch name, fork count, and model
2. **Branch Generation**: Auto-generates unique branch names if not provided (with num_forks > 1, appends fork number: `branch-1`, `branch-2`, etc.)
3. **Parallel Execution**: Creates N threads, each running an isolated Claude Code agent
4. **Sandbox Initialization**: Each agent initializes its own E2B sandbox with MCP server access
5. **Repository Cloning**: Clones the repository into each sandbox on the fork-specific branch
6. **Agent Execution**: Runs agent with system prompt, user prompt, and full observability hooks
7. **Logging**: Streams all agent activity to dedicated log files (one per fork) with thread-safe logging
8. **Monitoring**: Opens all log files in VSCode for real-time progress tracking
9. **Summary**: Displays execution results table with costs, tokens, status, and log paths

## Git Push Authentication

**CRITICAL**: The sandbox is isolated - no SSH keys, no inherited env vars.

For agents to push to GitHub, your task prompt MUST include:
```bash
git remote set-url origin https://${GITHUB_TOKEN}@github.com/<owner>/<repo>.git
```

The GITHUB_TOKEN environment variable is passed to the sandbox automatically if set in your `.env` file.

## Architecture

### Fork Isolation

Each fork runs in complete isolation:
- **Separate Thread**: Independent Python thread with its own async event loop
- **Separate E2B Sandbox**: Isolated cloud sandbox with full filesystem and process isolation
- **Independent Branch**: Auto-generated branch name (e.g., `main-1`, `main-2`, `main-3`)
- **Own Claude Code Agent**: Dedicated ClaudeSDKClient instance with full configuration
- **Dedicated Log File**: Thread-safe logger writing to `{branch}-fork-{num}-{timestamp}.log`

### Agent Configuration

Each agent is configured with:
- **System Prompt**: Dynamically formatted with repo URL, branch, fork number, GitHub token, allowed directories
- **MCP Server Access**: Full access to E2B sandbox tools via MCP protocol
- **Allowed Tools**: Whitelisted set of 25+ tools (sandbox + local + utility)
- **Permission Mode**: Set to `acceptEdits` for autonomous operation
- **Max Turns**: Configurable (default: 100 turns)
- **Model**: Configurable (opus, sonnet, haiku)
- **Working Directory**: Set to `apps/sandbox_agent_working_dir/`
- **Environment**: GitHub token passed to agent environment if available

### Hybrid Tool Access with Hook-Based Security

Agents operate in a **hybrid environment**:

**MCP Sandbox Tools** (Primary - for repository operations):
- ✅ `mcp__e2b-sandbox__execute_command` - Run git, npm, python, etc. in sandbox
- ✅ `mcp__e2b-sandbox__write_file` - Write files to sandbox
- ✅ `mcp__e2b-sandbox__read_file` - Read files from sandbox
- ✅ `mcp__e2b-sandbox__list_files` - List sandbox directory contents
- ✅ `mcp__e2b-sandbox__make_directory` - Create directories in sandbox
- ✅ `mcp__e2b-sandbox__get_host` - Get public URL for exposed ports (webservers)

**Local Tools** (Secondary - restricted to allowed directories):
- ✅ `Read`, `Write`, `Edit` - Local file operations (ONLY in allowed directories)
- ✅ `Bash` - Local commands (logged for observability)
- ✅ `WebFetch`, `WebSearch`, `Task`, `Skill`, `SlashCommand`, `TodoWrite`, `Glob`, `Grep` - Utility tools

## Logs

Log files are stored in `../sandbox_agent_working_dir/logs/`:
- Format: `{branch}-fork-{fork_num}-{timestamp}.log`
- Contains: All agent messages, tool usage, errors, and results
- Opens automatically in VSCode when command completes

## Examples

### Example 1: Single Agent Task

```bash
uv run obox https://github.com/myorg/myrepo \
  --branch feature/auth-tests \
  --prompt "Add comprehensive unit tests for all auth functions" \
  --model sonnet
```

### Example 2: Parallel Development Streams

```bash
uv run obox https://github.com/myorg/myrepo \
  --prompt "Refactor the authentication module to use modern async/await patterns" \
  --branch feature/async-refactor \
  --forks 3
```

### Example 3: Code Review and Documentation

```bash
uv run obox https://github.com/myorg/myrepo \
  --branch feature/new-api \
  --prompt "Review the new API implementation, add JSDoc comments, and create usage examples"
```

## Project Structure

```
apps/sandbox_workflows/
├── src/
│   ├── main.py                 # CLI entry point
│   ├── commands/
│   │   ├── __init__.py
│   │   └── sandbox_fork.py     # Main command implementation
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── constants.py        # Configuration constants
│   │   ├── logs.py             # Thread-safe logging
│   │   ├── hooks.py            # Hook implementations
│   │   ├── git_utils.py        # Git utilities
│   │   ├── forks.py            # Fork execution management
│   │   └── agents.py           # Agent management
│   └── prompts/
│       └── sandbox_fork_agent_system_prompt.md
├── pyproject.toml              # Project configuration
├── .env.sample                 # Environment variables template
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## Troubleshooting

### "Got unexpected extra argument"

**Wrong**: `uv run obox sandbox-fork https://github.com/...`
**Right**: `uv run obox https://github.com/... --prompt ...`

There is no `sandbox-fork` subcommand. The repo URL is the first positional argument.

### "VSCode not found"

If VSCode doesn't open automatically, manually open log files from:
```
../sandbox_agent_working_dir/logs/
```

### "Invalid API key"

Make sure you've created a `.env` file with valid API keys:
```bash
cp .env.sample .env
# Edit .env with your keys
```

### "Push failed" / "could not read Username"

1. Verify GITHUB_TOKEN is in your `.env` file
2. Verify it's a classic PAT (`ghp_...`), NOT an OAuth token (`gho_...`)
3. Verify your task prompt includes git auth instructions

### "E2B API error"

Check your E2B API key and quota at https://e2b.dev/dashboard

## License

MIT
