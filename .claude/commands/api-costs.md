---
description: Estimate costs and manage budget limits for API usage
tags: [api, costs, budget, estimation]
---

# API Cost Estimation & Budget Management

Estimate API costs, track spending, and manage budget limits across all providers.

## Cost Estimation

### 1. Estimate Request Cost
Estimate the cost before making an API call:

Use `estimate_cost` tool with:
- **provider**: Provider name
- **input_tokens**: Estimated input tokens
- **output_tokens**: Estimated output tokens
- **model**: (optional) Specific model

**Example:**
```json
{
  "provider": "anthropic",
  "input_tokens": 5000,
  "output_tokens": 2000,
  "model": "claude-3-5-sonnet-20241022"
}
```

### 2. Compare Provider Costs
Estimate costs across different providers to find the most economical option:

Run `estimate_cost` for each provider with same token counts to compare

### 3. Get Cost-Optimized Routing
Find the cheapest provider for a task:

Use routing recommendations to see cost-effective options

## Budget Management

### 1. Check Budget Status
View current budget status and limits:

Use `check_budget` tool to see:
- Daily spending vs. limit
- Monthly spending vs. limit
- Remaining budget
- Alert status
- Budget exceeded warnings

**Example Response:**
```json
{
  "budget_enabled": true,
  "daily": {
    "spent": 2.50,
    "limit": 10.00,
    "remaining": 7.50,
    "percentage": 25,
    "alert": false,
    "exceeded": false
  },
  "monthly": {
    "spent": 45.00,
    "limit": 100.00,
    "remaining": 55.00,
    "percentage": 45,
    "alert": false,
    "exceeded": false
  }
}
```

### 2. Budget Alerts
Monitor for budget alerts:

The `check_budget` tool shows alerts when spending reaches 80% (configurable) of limits

### 3. Budget Configuration
Budget limits are configured in routing_config.json:

```json
{
  "budget": {
    "enabled": true,
    "daily_limit": 10.0,
    "monthly_limit": 100.0,
    "alert_threshold": 0.8
  }
}
```

## Cost Breakdown by Provider

### Current Pricing (per 1,000 tokens)

**Anthropic (Claude):**
- Input: $0.003/1k tokens
- Output: $0.015/1k tokens

**OpenAI (GPT):**
- Input: $0.01/1k tokens
- Output: $0.03/1k tokens

**Google (Gemini):**
- Input: $0.0005/1k tokens
- Output: $0.0015/1k tokens

**Local (Ollama):**
- Free (no API costs)

## Cost Optimization Tips

1. **Use local models for embeddings**: Free, no API costs
2. **Choose appropriate models**: Don't use expensive models for simple tasks
3. **Monitor token usage**: Optimize prompts to reduce token count
4. **Set budget limits**: Prevent unexpected costs
5. **Use routing optimization**: Let the system choose cost-effective providers

## Examples

1. **Estimate cost for a request:**
   - Tool: `estimate_cost`
   - Args: `{"provider": "anthropic", "input_tokens": 1000, "output_tokens": 500}`

2. **Check current budget status:**
   - Tool: `check_budget`
   - Args: `{}`

3. **Compare providers:**
   Run `estimate_cost` for each provider with same tokens:
   ```
   anthropic: ~$0.01
   openai: ~$0.025
   google: ~$0.001
   local: $0.00
   ```

4. **Get cost-optimized routing:**
   - Tool: `get_routing_recommendations`
   - Check for cost optimization suggestions

## Budget Warnings

- **Daily alert**: Triggers at 80% of daily limit (configurable)
- **Monthly alert**: Triggers at 80% of monthly limit (configurable)
- **Exceeded**: When spending exceeds the limit

Use `check_budget` regularly to stay within limits.

## Tracking Actual Costs

Costs are automatically tracked when you use `track_request` after API calls:

```json
{
  "provider": "anthropic",
  "input_tokens": 1000,
  "output_tokens": 500,
  "model": "claude-3-5-sonnet-20241022",
  "success": true
}
```

This updates usage statistics and cost totals in real-time.
