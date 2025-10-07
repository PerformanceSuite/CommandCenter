# API Key Manager MCP Server

Secure API key management and multi-provider AI routing for Command Center.

## Features

- **Secure Key Storage**: API keys encrypted at rest using backend crypto utilities
- **Multi-Provider Support**: Anthropic, OpenAI, Google, and Local (Ollama)
- **Intelligent Routing**: Task-based routing to optimal providers
- **Usage Tracking**: Track requests, tokens, and costs per provider
- **Cost Estimation**: Estimate costs before making API calls
- **Budget Management**: Set daily and monthly limits with alerts
- **Audit Trail**: Complete access logging for security compliance
- **Fallback Support**: Automatic failover to backup providers
- **Health Monitoring**: Track provider availability and status

## Supported Providers

### Anthropic (Claude)
- **Models**: claude-3-5-sonnet, claude-3-opus, claude-3-sonnet, claude-3-haiku
- **Best for**: Code generation, code review, chat
- **Pricing**: $0.003/1k input, $0.015/1k output

### OpenAI (GPT)
- **Models**: gpt-4-turbo, gpt-4, gpt-3.5-turbo
- **Best for**: Analysis, data extraction
- **Pricing**: $0.01/1k input, $0.03/1k output

### Google (Gemini)
- **Models**: gemini-pro, gemini-pro-vision
- **Best for**: Fallback, cost optimization
- **Pricing**: $0.0005/1k input, $0.0015/1k output

### Local (Ollama)
- **Models**: codellama, mistral, llama2
- **Best for**: Embeddings, offline work
- **Pricing**: Free

## MCP Tools

### Key Management
- `add_api_key` - Add/update API keys
- `remove_api_key` - Remove API keys
- `rotate_key` - Rotate API keys
- `list_api_keys` - List configured keys
- `validate_key` - Validate API key
- `validate_all_keys` - Validate all keys

### Routing
- `route_request` - Route request to best provider
- `get_routing_recommendations` - Get routing advice
- `get_provider_stats` - Provider statistics

### Usage & Costs
- `get_usage` - Get usage statistics
- `estimate_cost` - Estimate request cost
- `check_budget` - Check budget status
- `track_request` - Track API request

## MCP Resources

- `api://providers` - Provider configuration and status
- `api://usage` - Usage statistics dashboard
- `api://routing` - Routing recommendations

## Slash Commands

- `/api-config` - Configure API providers
- `/api-usage` - View usage statistics
- `/api-costs` - Check costs and budget

## Quick Start

### 1. Add API Keys

```bash
# Add Anthropic key from environment
add_api_key(provider="anthropic", env_var="ANTHROPIC_API_KEY")

# Add OpenAI key directly
add_api_key(provider="openai", api_key="sk-...")
```

### 2. Validate Keys

```bash
# Validate all configured keys
validate_all_keys()

# Validate specific provider
validate_key(provider="anthropic")
```

### 3. Route Requests

```bash
# Get best provider for code generation
route_request(task_type="code_generation")

# Route with preferred provider and fallback
route_request(
    task_type="analysis",
    preferred_provider="openai",
    enable_fallback=True
)
```

### 4. Track Usage

```bash
# Track a request
track_request(
    provider="anthropic",
    input_tokens=1000,
    output_tokens=500,
    model="claude-3-5-sonnet-20241022",
    success=True
)

# Get usage stats
get_usage(provider="anthropic", days=30)
```

### 5. Estimate Costs

```bash
# Estimate cost before making request
estimate_cost(
    provider="anthropic",
    input_tokens=5000,
    output_tokens=2000
)

# Check budget
check_budget()
```

## Configuration

### Routing Configuration

Edit `.commandcenter/mcp-servers/api-keys/routing_config.json`:

```json
{
  "providers": {
    "anthropic": {
      "enabled": true,
      "models": ["claude-3-5-sonnet-20241022"],
      "rate_limit": 100
    }
  },
  "routing": {
    "code_generation": "anthropic",
    "embeddings": "local",
    "analysis": "openai"
  },
  "fallback_order": ["anthropic", "openai", "google", "local"],
  "budget": {
    "enabled": true,
    "daily_limit": 10.0,
    "monthly_limit": 100.0,
    "alert_threshold": 0.8
  }
}
```

### Security Configuration

- Keys encrypted using backend crypto utilities
- Encryption key derived from `SECRET_KEY`
- Restricted file permissions (600)
- No plaintext logging

## File Structure

```
.commandcenter/mcp-servers/api-keys/
├── __init__.py
├── server.py              # MCP server
├── config.py              # Configuration
├── tools/
│   ├── __init__.py
│   ├── manage.py          # Key management
│   ├── validate.py        # Key validation
│   ├── storage.py         # Secure storage
│   ├── usage.py           # Usage tracking
│   └── routing.py         # Provider routing
├── resources/
│   ├── __init__.py
│   ├── providers.py       # Provider resource
│   └── usage_stats.py     # Usage resource
├── tests/
│   ├── __init__.py
│   ├── test_storage.py
│   ├── test_manage.py
│   ├── test_routing.py
│   └── test_usage.py
├── .keys.enc              # Encrypted keys (auto-generated)
├── usage.json             # Usage stats (auto-generated)
└── routing_config.json    # Routing config (auto-generated)
```

## Testing

```bash
# Run all tests
cd .commandcenter/mcp-servers/api-keys
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Coverage goal: >90%
```

## Security Best Practices

1. **Use Environment Variables**: Store keys in env vars when possible
2. **Rotate Keys Regularly**: Use `rotate_key()` for periodic rotation
3. **Monitor Audit Logs**: Review access logs regularly
4. **Set Budget Limits**: Prevent unexpected costs
5. **Validate Keys**: Test keys after adding
6. **Restrict Permissions**: Ensure `.keys.enc` is read-only
7. **Backup Keys**: Backup encrypted key file securely

## Routing Strategies

### Task-Based Routing

The system automatically routes requests based on task type:

- **Code Generation/Review**: Anthropic (Claude) - Best code understanding
- **Embeddings**: Local (Ollama) - Free, offline
- **Analysis**: OpenAI (GPT) - Strong analytical capabilities
- **Chat**: Anthropic (Claude) - Natural conversation
- **Summarization**: Anthropic (Claude) - Excellent summarization

### Fallback Routing

If primary provider fails:
1. Check fallback order: `["anthropic", "openai", "google", "local"]`
2. Try next available provider
3. Return error if all providers fail

### Cost Optimization

For cost-sensitive workloads:
1. Use `get_best_provider_for_cost()` to find cheapest option
2. Prefer local models when possible
3. Set budget limits to control spending

## Troubleshooting

### Key Not Found Error
```bash
# List configured keys
list_api_keys()

# Add missing key
add_api_key(provider="anthropic", env_var="ANTHROPIC_API_KEY")
```

### Provider Unavailable
```bash
# Check provider status
get_provider_stats()

# Enable provider
update_provider_config(provider="anthropic", enabled=True)
```

### Budget Exceeded
```bash
# Check budget status
check_budget()

# Adjust limits in routing_config.json
```

### Validation Failed
```bash
# Validate key format
validate_key(provider="anthropic")

# Check key format:
# - Anthropic: starts with "sk-ant-"
# - OpenAI: starts with "sk-"
# - Google: at least 20 characters
```

## Integration with Command Center

The API Key Manager integrates with Command Center's:
- **Backend Crypto**: Uses `app/utils/crypto.py` for encryption
- **Environment Config**: Reads from `.env` files
- **MCP Protocol**: Standard MCP server interface

## Version

Current version: 1.0.0

## License

Same as Command Center project.
