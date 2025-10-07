---
description: Show or edit MCP server configuration
---

# MCP Configuration

You are tasked with displaying or editing the CommandCenter MCP configuration.

## Command Format

```
/mcp-config [action] [key] [value]
```

## Actions

- `show` (default): Display current configuration
- `edit <key> <value>`: Update configuration value
- `validate`: Validate configuration against schema
- `reset`: Reset to default configuration

## Your Task

### For `show` action:

1. **Load configuration**
   - Read `.commandcenter/config.json`
   - Pretty-print JSON with syntax highlighting
   - Show all sections

2. **Display MCP server status**
   - Show which servers are enabled
   - Display transport type for each
   - Show AI provider routing

3. **Show configuration validation**
   - Validate against schema
   - Display any warnings or errors
   - Show schema version

### For `edit` action:

1. **Parse edit request**
   - Validate key path (e.g., "project.id")
   - Validate value type
   - Check if key exists in schema

2. **Update configuration**
   - Load current config
   - Update specified key
   - Validate updated config
   - Save back to file

3. **Show updated value**
   - Display old value
   - Display new value
   - Confirm successful update

### For `validate` action:

1. **Load schema**
   - Read `.commandcenter/config.schema.json`
   - Parse schema rules

2. **Validate configuration**
   - Check required fields
   - Validate field types
   - Check enum values
   - Validate constraints

3. **Report results**
   - Show validation status (✓ or ✗)
   - List any errors
   - Suggest fixes

### For `reset` action:

1. **Confirm reset**
   - Warn about data loss
   - Ask for confirmation

2. **Reset configuration**
   - Backup current config
   - Generate default config
   - Customize for current project
   - Save new config

3. **Show changes**
   - Display what was reset
   - Show new configuration

## Configuration Display Format

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
      "transport": "stdio"
    },
    "knowledgebeast": {
      "enabled": true,
      "collection_name": "project_commandcenter"
    }
  },
  "ai_providers": {
    "primary": "anthropic",
    "routing": {
      "code_generation": "anthropic",
      "embeddings": "local"
    }
  }
}
```

## Configuration Sections

Explain each section:

- **project**: Project metadata and identification
- **mcp_servers**: MCP server configurations (enable/disable, transport)
- **ai_providers**: AI provider routing and model selection
- **workflows**: Workflow templates and settings
- **git**: Git configuration for worktrees
- **security**: Security settings
- **logging**: Logging configuration

## Example Usage

```bash
# Show current configuration
/mcp-config

# Edit project name
/mcp-config edit project.name "My Project"

# Enable VIZTRTR server
/mcp-config edit mcp_servers.viztrtr.enabled true

# Validate configuration
/mcp-config validate

# Reset to defaults
/mcp-config reset
```

## Success Criteria

- [ ] Configuration loaded successfully
- [ ] JSON displayed with proper formatting
- [ ] All sections explained
- [ ] Validation status shown
- [ ] For edits: Changes saved successfully
- [ ] For edits: Configuration still valid after update
- [ ] Clear error messages if validation fails

Execute the requested MCP configuration action now.
