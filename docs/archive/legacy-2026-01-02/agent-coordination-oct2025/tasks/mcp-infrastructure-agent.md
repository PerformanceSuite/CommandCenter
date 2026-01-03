# MCP Infrastructure Agent - Task Definition

**Mission:** Build base MCP server template and Project Manager MCP server
**Worktree:** worktrees/mcp-infrastructure-agent
**Branch:** feature/mcp-infrastructure
**Estimated Time:** 35 hours
**Dependencies:** None (Phase 1 - Independent)

---

## Tasks Checklist

### Task 1: Create Base MCP Server Template (8 hours)
- [ ] Create `.commandcenter/` directory structure
- [ ] Create base MCP server template in `.commandcenter/mcp-servers/base/`
- [ ] Implement MCP protocol handler (stdio transport)
- [ ] Create tool registry system
- [ ] Add resource provider interface
- [ ] Create prompt template system
- [ ] Write configuration loader (reads .commandcenter/config.json)
- [ ] Add logging and error handling utilities

**Directory Structure:**
```
.commandcenter/
├── config.json
├── mcp-servers/
│   └── base/
│       ├── __init__.py
│       ├── server.py          # Base MCP server class
│       ├── protocol.py        # MCP protocol implementation
│       ├── transport.py       # stdio/SSE transport
│       ├── registry.py        # Tool/resource registry
│       └── utils.py           # Logging, config, etc.
```

**Files to Create:**
- `.commandcenter/config.json` - Main configuration
- `.commandcenter/mcp-servers/base/server.py` - Base MCP server
- `.commandcenter/mcp-servers/base/protocol.py` - Protocol handler
- `.commandcenter/mcp-servers/base/transport.py` - Transport layer
- `.commandcenter/mcp-servers/base/registry.py` - Tool/resource registry
- `.commandcenter/mcp-servers/base/utils.py` - Utilities

**Implementation Guidance:**
- Use Model Context Protocol specification
- Support stdio transport (primary)
- Extensible tool/resource system
- JSON-RPC 2.0 message format
- Proper error handling and logging

---

### Task 2: Build Project Manager MCP Server (12 hours)
- [ ] Create `.commandcenter/mcp-servers/project-manager/` directory
- [ ] Implement main orchestration server
- [ ] Add project state management
- [ ] Create workflow coordination tools
- [ ] Implement agent spawning tools
- [ ] Add git integration tools
- [ ] Create project analysis tools
- [ ] Implement progress tracking
- [ ] Add CLI command generation

**Files to Create:**
```
.commandcenter/mcp-servers/project-manager/
├── __init__.py
├── server.py              # Main MCP server
├── tools/
│   ├── __init__.py
│   ├── workflow.py        # Workflow coordination
│   ├── agent.py           # Agent spawning
│   ├── git.py             # Git operations
│   ├── analysis.py        # Project analysis
│   └── progress.py        # Progress tracking
├── resources/
│   ├── __init__.py
│   ├── project_state.py   # Project state resource
│   └── workflows.py       # Workflow templates
└── config.py              # Server configuration
```

**Tools to Implement:**
1. `analyze_project` - Analyze current project structure
2. `create_workflow` - Create agent workflow from template
3. `spawn_agent` - Launch specialized agent in worktree
4. `track_progress` - Monitor agent progress
5. `merge_results` - Coordinate PR merging
6. `generate_command` - Generate CLI commands

**Resources to Provide:**
1. `project://state` - Current project state
2. `project://workflows` - Available workflow templates
3. `project://agents` - Active agents status

---

### Task 3: Create Configuration System (5 hours)
- [ ] Design `.commandcenter/config.json` schema
- [ ] Add project metadata configuration
- [ ] Configure MCP server settings
- [ ] Add AI provider routing configuration
- [ ] Create per-project isolation settings
- [ ] Implement configuration validation
- [ ] Add default configuration templates
- [ ] Write configuration migration utilities

**Configuration Schema:**
```json
{
  "project": {
    "id": "commandcenter",
    "name": "CommandCenter",
    "type": "fullstack",
    "isolation_id": "cc-main"
  },
  "mcp_servers": {
    "project_manager": {
      "enabled": true,
      "port": null,
      "transport": "stdio"
    },
    "knowledgebeast": {
      "enabled": true,
      "collection_name": "project_commandcenter"
    },
    "agentflow": {
      "enabled": true,
      "max_parallel_agents": 8
    }
  },
  "ai_providers": {
    "primary": "anthropic",
    "fallback": ["openai", "google"],
    "routing": {
      "code_generation": "anthropic",
      "embeddings": "local",
      "analysis": "openai"
    }
  }
}
```

**Files to Create:**
- `.commandcenter/config.json` - Main configuration
- `.commandcenter/config.schema.json` - JSON schema
- `.commandcenter/mcp-servers/base/config_validator.py` - Validator

---

### Task 4: Implement Slash Command Integration (5 hours)
- [ ] Create `.claude/commands/init-commandcenter.md` command
- [ ] Create `.claude/commands/start-workflow.md` command
- [ ] Create `.claude/commands/agent-status.md` command
- [ ] Create `.claude/commands/mcp-config.md` command
- [ ] Add command templates in `.commandcenter/prompts/commands/`
- [ ] Implement command → MCP tool mapping
- [ ] Add command documentation

**Slash Commands to Create:**
1. `/init-commandcenter` - Initialize .commandcenter/ in project
2. `/start-workflow <type>` - Start agent workflow
3. `/agent-status` - Show active agents status
4. `/mcp-config` - Show/edit MCP configuration

**Files to Create:**
- `.claude/commands/init-commandcenter.md`
- `.claude/commands/start-workflow.md`
- `.claude/commands/agent-status.md`
- `.claude/commands/mcp-config.md`
- `.commandcenter/prompts/commands/` (templates)

---

### Task 5: Create Agent Coordination System (5 hours)
- [ ] Port AgentFlow coordination logic to MCP
- [ ] Create `.commandcenter/.agent-coordination/` structure
- [ ] Implement agent status tracking
- [ ] Add dependency management system
- [ ] Create merge queue coordination
- [ ] Implement review score tracking
- [ ] Add conflict resolution workflows

**Files to Create:**
```
.commandcenter/.agent-coordination/
├── status.json            # Agent status tracking
├── dependencies.json      # Agent dependencies
├── merge-queue.json       # PR merge queue
├── tasks/                 # Agent task definitions
└── workflows/             # Workflow templates
```

**Implementation:**
- Reuse existing `.agent-coordination/` patterns
- Add MCP tool integration
- Real-time status updates via resources
- Automated conflict detection

---

## Testing Requirements

### Unit Tests to Write
- [ ] `tests/mcp/test_base_server.py` - Base MCP server
- [ ] `tests/mcp/test_protocol.py` - Protocol handling
- [ ] `tests/mcp/test_project_manager.py` - Project Manager tools
- [ ] `tests/mcp/test_config.py` - Configuration validation

### Integration Tests
- [ ] Test MCP server stdio communication
- [ ] Test tool invocation flow
- [ ] Test resource access
- [ ] Test multi-server coordination

---

## Review Checklist

Before creating PR, ensure:
- [ ] All tests pass: `pytest tests/mcp/`
- [ ] MCP protocol compliance verified
- [ ] Slash commands working in Claude Code
- [ ] Configuration validation working
- [ ] Documentation complete
- [ ] Run `/review` until score is 10/10

---

## PR Details

**Title:** "MCP: Base infrastructure and Project Manager server"

**Description:**
```markdown
## MCP Infrastructure Complete ✅

This PR implements the base MCP server infrastructure and Project Manager orchestration server.

### Changes
- ✅ Base MCP server template (stdio transport)
- ✅ Project Manager MCP server with 6 core tools
- ✅ Configuration system (.commandcenter/config.json)
- ✅ Slash command integration (4 commands)
- ✅ Agent coordination system

### MCP Servers Implemented
1. **Base MCP Template** - Reusable MCP server foundation
2. **Project Manager** - Main orchestration and workflow coordination

### Slash Commands Added
- `/init-commandcenter` - Initialize CommandCenter in project
- `/start-workflow` - Launch agent workflows
- `/agent-status` - Monitor agent progress
- `/mcp-config` - Manage configuration

### Architecture
- Model Context Protocol compliant
- Stdio transport (cross-IDE compatible)
- Tool registry system
- Resource provider interface
- Multi-server coordination ready

### Review Score: 10/10 ✅
```

---

## Success Criteria

- [ ] Base MCP server template complete
- [ ] Project Manager MCP server operational
- [ ] Configuration system working
- [ ] Slash commands functional
- [ ] Agent coordination system ready
- [ ] All tests passing (>90% coverage)
- [ ] Review score 10/10
- [ ] No merge conflicts
- [ ] PR approved and merged

---

**Reference Documents:**
- `.claude/memory.md` (Session 2 - MCP architecture planning)
- `AgentFlow/README.md` (Multi-agent coordination patterns)
- MCP Protocol Specification
