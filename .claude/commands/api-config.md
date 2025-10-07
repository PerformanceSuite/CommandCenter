---
description: Configure and manage API providers for multi-provider AI routing
tags: [api, configuration, providers]
---

# API Configuration Manager

Manage API keys and provider configuration for the API Key Manager MCP server.

## Available Operations

### 1. Add/Update API Key
Add or update an API key for a provider:

**Providers:** anthropic, openai, google, local

**Example:**
- Add Anthropic key: Use `add_api_key` tool with provider="anthropic" and api_key or env_var
- Add OpenAI key: Use `add_api_key` tool with provider="openai" and api_key or env_var

### 2. List API Keys
View all configured API keys (without revealing actual keys):

Use `list_api_keys` tool to see:
- Which providers have keys configured
- Key metadata (creation date, expiration, etc.)
- Provider enabled/disabled status

### 3. Rotate API Key
Rotate an existing API key for security:

Use `rotate_key` tool with provider and new_api_key or env_var

### 4. Remove API Key
Remove an API key for a provider:

Use `remove_api_key` tool with provider name

### 5. Update Provider Configuration
Enable/disable providers or update settings:

Use `update_provider_config` from the management tools

### 6. View Provider Status
Check which providers are available:

Use `get_provider_stats` tool to see:
- Enabled/disabled status
- Available models
- Rate limits
- Pricing information
- Health status

## Quick Actions

**List all providers:**
Use the `api://providers` resource to view complete provider configuration

**Check what's configured:**
Use `list_api_keys` tool

**Add a new API key:**
Use `add_api_key` tool with the appropriate provider and key

**Validate all keys:**
Use `validate_all_keys` tool to test all configured keys

## Security Notes

- All API keys are encrypted at rest
- Keys are never logged in plaintext
- Use environment variables when possible for additional security
- Audit logs track all key access

## Examples

1. **Add Anthropic API key from environment:**
   - Tool: `add_api_key`
   - Args: `{"provider": "anthropic", "env_var": "ANTHROPIC_API_KEY"}`

2. **List all configured providers:**
   - Tool: `list_api_keys`
   - Args: `{"include_metadata": true}`

3. **Validate OpenAI key:**
   - Tool: `validate_key`
   - Args: `{"provider": "openai"}`
