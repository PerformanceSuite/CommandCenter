---
description: Initialize CommandCenter MCP infrastructure in the current project
---

# Initialize CommandCenter

You are tasked with initializing CommandCenter MCP infrastructure in the current project.

## Your Task

1. **Analyze the current project structure**
   - Detect project type (fullstack, backend, frontend, etc.)
   - Identify technologies used
   - Find existing configuration files
   - Check for git repository

2. **Create .commandcenter/ directory structure**
   - Create `.commandcenter/` directory
   - Copy MCP server templates
   - Create initial `config.json` based on project analysis
   - Set up `.agent-coordination/` structure

3. **Generate project-specific configuration**
   - Set unique `project.id` (based on directory name or git repo)
   - Configure `project.type` based on detection
   - Set `isolation_id` for data isolation
   - Configure MCP servers based on project needs

4. **Create initial coordination files**
   - Create `.agent-coordination/mcp-status.json`
   - Create `.agent-coordination/dependencies.json`
   - Create `.agent-coordination/workflows/` directory
   - Add initial workflow templates

5. **Provide setup instructions**
   - Show next steps for configuration
   - Explain how to start using MCP servers
   - Recommend initial workflows based on project type
   - Guide on GitHub app installation (if applicable)

## Expected Output

After initialization, the project should have:

```
.commandcenter/
├── config.json                    # Project-specific configuration
├── config.schema.json             # Configuration schema
├── mcp-servers/                   # MCP server implementations
│   ├── base/                      # Base server template
│   └── project-manager/           # Project manager server
├── .agent-coordination/           # Agent coordination
│   ├── mcp-status.json           # Agent status tracking
│   ├── dependencies.json         # Agent dependencies
│   └── workflows/                # Workflow templates
└── prompts/                       # Prompt templates
    └── commands/                  # Command templates
```

## Configuration Template

Use this template for `config.json`:

```json
{
  "project": {
    "id": "<detected-from-project>",
    "name": "<project-name>",
    "type": "<detected-type>",
    "isolation_id": "<unique-id>"
  },
  "mcp_servers": {
    "project_manager": {
      "enabled": true,
      "transport": "stdio"
    }
  },
  "ai_providers": {
    "primary": "anthropic"
  }
}
```

## Success Criteria

- [ ] .commandcenter/ directory created
- [ ] config.json generated with project-specific values
- [ ] MCP server templates copied
- [ ] Agent coordination structure created
- [ ] Configuration validated successfully
- [ ] Next steps provided to user

Begin the initialization process now.
