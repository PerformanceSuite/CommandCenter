# CommandCenter CLI Guide

Professional command-line interface for CommandCenter R&D management and knowledge base.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Commands](#commands)
  - [Analyze](#analyze-commands)
  - [Agents](#agent-orchestration)
  - [Search](#search-commands)
  - [Config](#configuration-management)
- [Shell Completion](#shell-completion)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Installation

### From Source

```bash
cd backend
pip install -e .
```

### With Development Dependencies

```bash
cd backend
pip install -e ".[dev]"
```

### Verify Installation

```bash
commandcenter --version
commandcenter --help
```

## Configuration

The CLI uses a YAML configuration file located at `~/.commandcenter/config.yaml`.

### Initialize Configuration

```bash
commandcenter config init
```

### Configuration Structure

```yaml
# API Configuration
api:
  url: http://localhost:8000
  timeout: 30
  verify_ssl: true

# Authentication
auth:
  token: null  # Set via: commandcenter config set auth.token <token>

# Output Preferences
output:
  format: table  # table, json, yaml
  color: auto    # auto, always, never
  verbose: false

# Analysis Defaults
analysis:
  cache: true
  create_tasks: false
  export_path: ./analysis-results

# Agent Orchestration
agents:
  max_concurrent: 3
  retry_failed: true
  log_level: info
```

### Configuration Commands

```bash
# Initialize config
commandcenter config init

# Get configuration value
commandcenter config get api.url

# Set configuration value
commandcenter config set api.url http://localhost:8000
commandcenter config set auth.token my-token

# List all configuration
commandcenter config list

# Show config file path
commandcenter config path
```

## Commands

### Analyze Commands

Analyze projects to detect technologies, dependencies, and research gaps.

#### Analyze Local Project

```bash
# Analyze current directory
commandcenter analyze project .

# Analyze specific path
commandcenter analyze project /path/to/project

# Analyze with options
commandcenter analyze project . --no-cache
commandcenter analyze project . --export json
commandcenter analyze project . --create-tasks
```

#### Analyze GitHub Repository

```bash
# Analyze GitHub repository
commandcenter analyze project --github facebook/react
commandcenter analyze project --github vercel/next.js

# With export
commandcenter analyze project --github microsoft/vscode --export yaml
```

#### Watch Mode

```bash
# Watch project for changes and re-analyze automatically
commandcenter analyze project . --watch

# Watch with export
commandcenter analyze project . --watch --export json --output results.json

# Press Enter to manually trigger analysis
# Press Ctrl+C to exit watch mode
```

**Watch Mode Features:**
- Auto-detects file changes with 1-second debounce
- Ignores `.git`, `__pycache__`, `node_modules`, `.venv`, `venv`
- Manual trigger with Enter key
- Clean exit with Ctrl+C

#### Export with Custom Output Path

```bash
# Export to default path
commandcenter analyze project . --export json

# Export to custom path
commandcenter analyze project . --export json --output ./reports/analysis.json
commandcenter analyze project . --export yaml -o results/scan.yaml
```

#### Analysis Statistics

```bash
# Show analysis statistics
commandcenter analyze stats
```

### Agent Orchestration

Manage and monitor agent workflows.

#### Launch Agents

```bash
# Launch full workflow
commandcenter agents launch

# Launch specific workflow
commandcenter agents launch --workflow analyze-only
commandcenter agents launch --workflow custom

# Launch without watching
commandcenter agents launch --no-watch

# Custom concurrency
commandcenter agents launch --max-concurrent 5
```

#### Check Agent Status

```bash
# List all orchestrations
commandcenter agents status

# Check specific orchestration
commandcenter agents status orch-123

# Watch orchestration in real-time
commandcenter agents status orch-123 --watch
```

#### View Agent Logs

```bash
# View agent logs
commandcenter agents logs agent-123

# Follow logs in real-time
commandcenter agents logs agent-123 --follow
```

#### Stop Orchestration

```bash
# Stop running orchestration
commandcenter agents stop orch-123
```

#### Retry Failed Agent

```bash
# Retry a failed agent
commandcenter agents retry agent-123
```

### Search Commands

RAG-powered knowledge base search.

#### Basic Search

```bash
# Search knowledge base
commandcenter search "FastAPI authentication"
commandcenter search "RAG implementation best practices"
```

#### Filtered Search

```bash
# Filter by technology
commandcenter search "Python frameworks" --filter technology

# Filter by research
commandcenter search "API design" --filter research

# Limit results
commandcenter search "Docker" --limit 5
```

#### Interactive Search

```bash
# Interactive search mode
commandcenter search --interactive

# In interactive mode:
Search> FastAPI authentication
# Results displayed...
Search> RAG implementation
# More results...
Search> exit
```

### Configuration Management

See [Configuration](#configuration) section above.

## Shell Completion

Enable tab completion for your shell using the `completion` command.

### Bash

```bash
# Temporary (current session only)
eval "$(commandcenter completion bash)"

# Permanent (add to ~/.bashrc)
echo 'eval "$(commandcenter completion bash)"' >> ~/.bashrc
source ~/.bashrc
```

### Zsh

```bash
# Temporary (current session only)
eval "$(commandcenter completion zsh)"

# Permanent (add to ~/.zshrc)
echo 'eval "$(commandcenter completion zsh)"' >> ~/.zshrc
source ~/.zshrc
```

### Fish

```bash
# Temporary (current session only)
commandcenter completion fish | source

# Permanent (add to config)
commandcenter completion fish > ~/.config/fish/completions/commandcenter.fish
```

**Shell completion enables:**
- Command name completion
- Subcommand completion
- Option completion
- Path completion for file arguments

## Examples

### Complete Analysis Workflow

```bash
# 1. Initialize configuration
commandcenter config init

# 2. Set API URL (if not using default)
commandcenter config set api.url http://my-server:8000

# 3. Analyze project
commandcenter analyze project /path/to/project --create-tasks --export json

# 4. Launch agents to process research
commandcenter agents launch --workflow full

# 5. Monitor progress
commandcenter agents status --watch

# 6. Search knowledge base
commandcenter search "technologies used in project"
```

### CI/CD Integration

```bash
#!/bin/bash
# analyze-project.sh

# Configure CLI
commandcenter config set api.url $COMMANDCENTER_API_URL
commandcenter config set auth.token $COMMANDCENTER_TOKEN

# Analyze and export
commandcenter analyze project . --no-cache --export json

# Check for research gaps
if grep -q "research_gaps" analysis-*.json; then
    echo "Research gaps found!"
    exit 1
fi
```

### Batch Analysis

```bash
#!/bin/bash
# batch-analyze.sh

REPOS=(
    "facebook/react"
    "vercel/next.js"
    "microsoft/vscode"
)

for repo in "${REPOS[@]}"; do
    echo "Analyzing $repo..."
    commandcenter analyze project --github $repo --export json
done

commandcenter analyze stats
```

## Output Formats

### Table (Default)

Beautiful terminal tables with color coding and formatting.

```bash
commandcenter analyze project .
```

### JSON

Machine-readable JSON output for scripting.

```bash
commandcenter analyze project . --format json
commandcenter --format json analyze stats
```

### YAML

Human-readable YAML output.

```bash
commandcenter --format yaml analyze project .
```

## Environment Variables

- `NO_COLOR`: Disable colored output
- `COMMANDCENTER_API_URL`: Override API URL
- `COMMANDCENTER_CONFIG`: Custom config file path

```bash
# Disable colors
NO_COLOR=1 commandcenter analyze project .

# Custom API URL
COMMANDCENTER_API_URL=http://localhost:9000 commandcenter analyze stats

# Custom config
COMMANDCENTER_CONFIG=/path/to/config.yaml commandcenter config list
```

## Troubleshooting

### Configuration Issues

**Problem**: "Configuration not found"

```bash
# Solution: Initialize configuration
commandcenter config init
```

**Problem**: "Invalid configuration key"

```bash
# Solution: Check valid keys
commandcenter config list

# Valid key format: section.key
commandcenter config get api.url
```

### API Connection Issues

**Problem**: "Connection refused"

```bash
# Check API URL
commandcenter config get api.url

# Verify backend is running
curl http://localhost:8000/health

# Update URL if needed
commandcenter config set api.url http://localhost:8000
```

**Problem**: "Authentication failed"

```bash
# Set authentication token
commandcenter config set auth.token your-token-here
```

### Analysis Issues

**Problem**: "Analysis failed: Project not found"

```bash
# Verify path exists
ls /path/to/project

# Use absolute path
commandcenter analyze project /absolute/path/to/project
```

**Problem**: "Analysis is slow"

```bash
# Enable caching
commandcenter config set analysis.cache true

# Or use --no-cache to force fresh analysis
commandcenter analyze project . --no-cache
```

### Agent Issues

**Problem**: "Orchestration failed"

```bash
# Check agent logs
commandcenter agents logs agent-123

# Retry failed agent
commandcenter agents retry agent-123

# View orchestration status
commandcenter agents status orch-123
```

## Advanced Usage

### Verbose Output

```bash
# Enable verbose output globally
commandcenter config set output.verbose true

# Or per-command
commandcenter -v analyze project .
```

### Custom Timeouts

```bash
# Increase timeout for large projects
commandcenter config set api.timeout 120
```

### Batch Operations

```bash
# Export all configurations
commandcenter config list --format yaml > my-config.yaml

# Run multiple analyses
for dir in project-*; do
    commandcenter analyze project $dir --export json
done
```

## Getting Help

```bash
# General help
commandcenter --help

# Command-specific help
commandcenter analyze --help
commandcenter agents --help
commandcenter search --help
commandcenter config --help

# Subcommand help
commandcenter analyze project --help
commandcenter agents launch --help
```

## Version Information

```bash
# Check CLI version
commandcenter --version
```

## License

MIT License - See LICENSE file for details.
