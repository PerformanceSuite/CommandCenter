# AI Provider Routing Architecture

**Version:** 1.0
**Date:** 2025-10-10
**Purpose:** Multi-provider AI routing for research agents, content generation, and analysis

---

## Overview

CommandCenter needs **flexible AI provider routing** to support:
- Multiple AI providers (Anthropic, OpenAI, Google, xAI, Hugging Face, open-source models)
- Per-task model selection (user chooses best model for each research task)
- Cost optimization (route to cheapest suitable model)
- Fallback/redundancy (if primary fails, use backup)
- Local models (via Ollama, LM Studio) for privacy-sensitive tasks

---

## Architecture Decision: MCP vs. Direct Integration

### What Needs MCP vs. What Doesn't

**✅ USE MCP FOR:**
1. **External data sources** (read-only, structured data)
   - Hacker News (MCP exists: `@modelcontextprotocol/server-hackernews`)
   - GitHub API (MCP exists: in this session)
   - arXiv papers (build custom MCP)
   - Competitor websites (web scraping MCP)

   **Why MCP?** These are **resources** that agents need to **query**. MCP provides standardized interface for:
   - Listing resources (`hackernews://trending`)
   - Reading content (`hackernews://item/12345`)
   - Schema validation
   - Caching

2. **Tool integrations** (actions agents can take)
   - File operations (MCP filesystem - already available)
   - Code execution (MCP Python/Node REPL)
   - Web browsing (MCP Puppeteer - already available)

   **Why MCP?** Standard tool calling interface, works across all AI providers

**❌ DON'T USE MCP FOR:**
1. **AI model routing** (LLM inference)
   - Use **OpenRouter** or **LiteLLM** instead
   - MCP is for *tools*, not for *the AI itself*

2. **Database queries** (internal data)
   - Direct SQL/ORM access is faster and simpler
   - No need for abstraction layer

3. **Simple HTTP APIs** (REST endpoints)
   - Just call them directly (axios/fetch)
   - MCP overhead not worth it

---

## Recommended Architecture: **OpenRouter + LiteLLM**

### Option 1: OpenRouter (Recommended for Start)

**What it is:** Unified API for 200+ AI models from all major providers

**Pros:**
- ✅ Single API key for all providers
- ✅ Unified pricing (pay via OpenRouter, no need for 10 different API keys)
- ✅ Automatic fallback (if GPT-4 fails, fallback to Claude)
- ✅ Usage analytics dashboard
- ✅ Rate limiting management
- ✅ Supports: Anthropic, OpenAI, Google, xAI, Mistral, Meta, open models

**Cons:**
- ❌ Small markup on API costs (typically 5-10%)
- ❌ Adds latency (~50-100ms routing overhead)
- ❌ Dependency on third party

**Example:**
```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
  apiKey: process.env.OPENROUTER_API_KEY,
  baseURL: "https://openrouter.ai/api/v1",
});

// Use any model via unified interface
const response = await client.messages.create({
  model: "anthropic/claude-sonnet-4",  // or "openai/gpt-4", "google/gemini-pro"
  messages: [{ role: "user", content: "Research HS-TasNet" }],
  extra_headers: {
    "HTTP-Referer": "https://commandcenter.app",
    "X-Title": "CommandCenter Research Agent"
  }
});
```

**Supported Models (200+):**
- **Anthropic:** Claude Opus 4, Sonnet 4, Haiku 4
- **OpenAI:** GPT-4, GPT-4 Turbo, o1-preview, o1-mini
- **Google:** Gemini Pro 2.0, Gemini Flash 2.0
- **xAI:** Grok 2, Grok 2 Vision
- **Meta:** Llama 3.3 70B, Llama 3.1 405B
- **Mistral:** Large, Medium, Small
- **Open Source:** DeepSeek, Qwen, Mixtral
- **Hugging Face:** Any model via HF Inference API

**Pricing:** https://openrouter.ai/models

### Option 2: LiteLLM (Self-Hosted Alternative)

**What it is:** Open-source proxy server that translates requests to 100+ LLM APIs

**Pros:**
- ✅ Self-hosted (no third-party dependency)
- ✅ No markup on API costs
- ✅ Load balancing across providers
- ✅ Caching layer (reduce costs)
- ✅ Custom routing rules
- ✅ Supports local models (Ollama, vLLM, LM Studio)

**Cons:**
- ❌ Need to manage server infrastructure
- ❌ Need API keys for each provider
- ❌ More complex setup

**Example:**
```yaml
# litellm_config.yaml
model_list:
  - model_name: claude-sonnet-4
    litellm_params:
      model: anthropic/claude-sonnet-4-20250514
      api_key: os.environ/ANTHROPIC_API_KEY

  - model_name: gpt-4
    litellm_params:
      model: gpt-4-turbo-preview
      api_key: os.environ/OPENAI_API_KEY

  - model_name: llama-3-70b
    litellm_params:
      model: ollama/llama3:70b
      api_base: http://localhost:11434

  - model_name: grok-2
    litellm_params:
      model: xai/grok-2-latest
      api_key: os.environ/XAI_API_KEY

router_settings:
  routing_strategy: "usage-based-routing"  # Load balance
  fallbacks:
    - gpt-4: [claude-sonnet-4, grok-2]
```

**Deploy:**
```bash
# Docker
docker run -p 4000:4000 \
  -v $(pwd)/litellm_config.yaml:/app/config.yaml \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  ghcr.io/berriai/litellm:main-latest
```

**Client:**
```typescript
const response = await fetch('http://localhost:4000/chat/completions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'claude-sonnet-4',  // LiteLLM routes to Anthropic
    messages: [{ role: 'user', content: 'Research HS-TasNet' }]
  })
});
```

---

## Recommended Approach: **Hybrid**

**Start with OpenRouter, migrate to LiteLLM later**

### Phase 1: Quick Start (Use OpenRouter)
- Single API key setup
- Get all providers working in days, not weeks
- Focus on building features, not infrastructure
- Cost: ~$0.01/request markup (acceptable for MVP)

### Phase 2: Scale (Add LiteLLM)
- Deploy LiteLLM proxy when costs justify optimization
- Use LiteLLM for high-volume tasks (monitoring, batch processing)
- Keep OpenRouter for low-volume, human-facing tasks
- Gradually migrate providers from OpenRouter → LiteLLM

### Phase 3: Multi-Tier Routing
```typescript
interface ModelRouting {
  // Tier 1: High cost, high quality (use OpenRouter for simplicity)
  premium: ["claude-opus-4", "gpt-4", "grok-2"];

  // Tier 2: Balanced (use LiteLLM for cost optimization)
  standard: ["claude-sonnet-4", "gpt-4-turbo", "gemini-pro"];

  // Tier 3: Low cost, high volume (use LiteLLM + local models)
  economy: ["claude-haiku-4", "llama-3-70b", "mixtral-8x7b"];

  // Tier 4: Local only (privacy-sensitive)
  local: ["ollama/llama3:70b", "lmstudio/deepseek-coder"];
}
```

---

## Model Selection UI

### Research Task Creation

```typescript
interface ResearchAgentConfig {
  // User-selectable per task
  model_provider: "openrouter" | "litellm" | "direct";

  model_tier: "premium" | "standard" | "economy" | "local";

  // Specific model (dropdown populated based on tier)
  model: string;

  // Fallback chain
  fallback_models?: string[];

  // Budget constraints
  max_cost?: number;  // in USD
  max_tokens?: number;

  // Privacy
  require_local?: boolean;  // Force local model (no API calls)
}
```

**UI Mockup:**
```
┌─────────────────────────────────────────────────┐
│ Create Research Task                            │
├─────────────────────────────────────────────────┤
│ Title: Evaluate HS-TasNet for real-time source │
│        separation                                │
│                                                  │
│ AI Model Configuration:                         │
│                                                  │
│ Provider: [OpenRouter ▼]                        │
│           OpenRouter (200+ models, managed)     │
│           LiteLLM (self-hosted, cost-optimized) │
│           Direct (bring your own API keys)      │
│           Local Only (Ollama, LM Studio)        │
│                                                  │
│ Model Tier: [Standard ▼]                        │
│             Premium ($$$) - Best quality        │
│             Standard ($$) - Balanced            │
│             Economy ($) - High volume           │
│             Local (FREE) - Privacy-first        │
│                                                  │
│ Model: [claude-sonnet-4 ▼]                      │
│        claude-sonnet-4 ($3/M tokens) ⭐          │
│        gpt-4-turbo ($10/M tokens)               │
│        gemini-pro-2.0 ($1.25/M tokens)          │
│        grok-2 ($5/M tokens)                     │
│        llama-3.3-70b ($0.50/M tokens)           │
│                                                  │
│ Fallback Models:                                │
│ 1. [gpt-4-turbo ▼]                              │
│ 2. [gemini-pro ▼]                               │
│ 3. [Add fallback]                               │
│                                                  │
│ Budget Limit: [$10 ▼]                           │
│               Estimated: ~3M tokens             │
│                                                  │
│ ☐ Require local model (no API calls)           │
│                                                  │
│ [Cancel]  [Create Research Task]                │
└─────────────────────────────────────────────────┘
```

---

## Provider Comparison

| Provider | Models | API Key Needed | Cost | Latency | Best For |
|----------|--------|----------------|------|---------|----------|
| **OpenRouter** | 200+ | 1 (OpenRouter) | +10% markup | +50-100ms | Quick start, unified billing |
| **LiteLLM** | 100+ | Multiple | No markup | Minimal | Cost optimization, self-hosted |
| **Anthropic Direct** | Claude only | ANTHROPIC_API_KEY | Standard | Low | Claude-only workflows |
| **OpenAI Direct** | GPT only | OPENAI_API_KEY | Standard | Low | GPT-only workflows |
| **Hugging Face** | 10,000+ | HF_API_KEY | Free tier | High (cold start) | Open-source models, experimentation |
| **Ollama** | 100+ | None (local) | FREE | Low | Privacy, offline, unlimited use |
| **LM Studio** | Any GGUF | None (local) | FREE | Low | GUI for local models |

---

## MCP Servers We Need

### 1. Hacker News (Existing)
```bash
npm install @modelcontextprotocol/server-hackernews

# Config in Claude Code settings
{
  "mcpServers": {
    "hackernews": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-hackernews"]
    }
  }
}
```

**Resources:**
- `hackernews://frontpage` - Top stories
- `hackernews://newest` - Latest submissions
- `hackernews://item/{id}` - Individual story/comment

### 2. arXiv (Build Custom)
```typescript
// backend/mcp-servers/arxiv/
class ArxivMCPServer {
  async listResources() {
    return [
      { uri: "arxiv://search/{query}", name: "Search papers" },
      { uri: "arxiv://paper/{id}", name: "Get paper details" },
      { uri: "arxiv://recent/{category}", name: "Recent papers in category" }
    ];
  }

  async readResource(uri: string) {
    if (uri.startsWith("arxiv://search/")) {
      const query = uri.split("/")[2];
      const papers = await arxiv.search(query);
      return papers.map(p => ({
        id: p.id,
        title: p.title,
        authors: p.authors,
        abstract: p.abstract,
        pdf_url: p.pdf_url,
        published: p.published
      }));
    }
  }
}
```

**Usage by Agent:**
```typescript
// Agent can search papers
const papers = await mcp.read("arxiv://search/real-time source separation");

// Extract relevant findings
const relevant = papers.filter(p =>
  p.abstract.includes("low-latency") || p.abstract.includes("real-time")
);
```

### 3. GitHub Trending (Build Custom)
```typescript
class GitHubTrendingMCP {
  async listResources() {
    return [
      { uri: "github://trending/{language}", name: "Trending repos" },
      { uri: "github://repo/{owner}/{name}", name: "Repo details" },
      { uri: "github://releases/{owner}/{name}", name: "Recent releases" }
    ];
  }

  async readResource(uri: string) {
    if (uri.startsWith("github://trending/")) {
      const language = uri.split("/")[2];
      const trending = await github.trending({ language, since: "weekly" });
      return trending.map(repo => ({
        name: repo.name,
        owner: repo.owner,
        stars: repo.stars,
        description: repo.description,
        language: repo.language,
        url: repo.url,
        weekly_stars: repo.weekly_stars
      }));
    }
  }
}
```

### 4. Competitor Monitoring (Build Custom)
```typescript
class CompetitorMonitoringMCP {
  async listResources() {
    return [
      { uri: "competitor://{name}/news", name: "Recent news" },
      { uri: "competitor://{name}/pricing", name: "Pricing updates" },
      { uri: "competitor://{name}/features", name: "Feature changelog" }
    ];
  }

  async readResource(uri: string) {
    const [_, name, type] = uri.split("/");

    if (type === "news") {
      // Scrape company blog, press releases
      const news = await scrape(`https://${name}.com/blog`);
      return news;
    }

    if (type === "pricing") {
      // Monitor pricing page changes
      const pricing = await scrape(`https://${name}.com/pricing`);
      return this.extractPricingChanges(pricing);
    }
  }
}
```

---

## Implementation Plan

### Week 1-2: AI Provider Routing
- [ ] Set up OpenRouter account
- [ ] Create model selection UI (dropdown in research task form)
- [ ] Implement routing logic (OpenRouter SDK)
- [ ] Add fallback chain support
- [ ] Test with all major models (Claude, GPT-4, Gemini, Grok, Llama)

### Week 3: MCP Servers (Data Sources)
- [ ] Install Hacker News MCP
- [ ] Build arXiv MCP server
- [ ] Build GitHub Trending MCP server
- [ ] Test MCP resource access from research agents

### Week 4: Agent Orchestration
- [ ] Create ResearchAgent class (uses selected model)
- [ ] Implement worktree isolation for parallel agents
- [ ] Build conversation history persistence
- [ ] Add follow-up question system

### Week 5-6: Tech Radar Monitoring
- [ ] Build scheduled jobs (daily scans)
- [ ] Alert generation + relevance scoring (AI-powered)
- [ ] Alert UI (dashboard view)
- [ ] Email/Slack notifications

---

## Cost Optimization Strategy

### Smart Routing Rules

```typescript
class CostOptimizer {
  selectModel(task: ResearchTask): string {
    // Use cheap models for routine tasks
    if (task.type === "monitoring_scan") {
      return "llama-3-70b";  // $0.50/M tokens
    }

    // Use premium for critical research
    if (task.priority === "high" || task.deliverables.includes("prototype")) {
      return "claude-opus-4";  // $15/M tokens, best quality
    }

    // Balanced for standard research
    return "claude-sonnet-4";  // $3/M tokens
  }

  async routeWithFallback(request, preferredModel, fallbacks) {
    try {
      return await openrouter.complete({ model: preferredModel, ...request });
    } catch (error) {
      if (error.code === "rate_limit" || error.code === "overloaded") {
        const nextModel = fallbacks.shift();
        if (nextModel) {
          console.log(`Falling back to ${nextModel}`);
          return this.routeWithFallback(request, nextModel, fallbacks);
        }
      }
      throw error;
    }
  }
}
```

### Caching Strategy

```typescript
// Cache expensive research results
class ResearchCache {
  async getCached(query: string, model: string): Promise<string | null> {
    const key = `research:${model}:${hash(query)}`;
    const cached = await redis.get(key);

    if (cached) {
      console.log(`Cache hit: Saved ~$${this.estimateCost(query, model)}`);
      return cached;
    }

    return null;
  }

  async setCached(query: string, model: string, result: string, ttl = 7 * 24 * 3600) {
    const key = `research:${model}:${hash(query)}`;
    await redis.set(key, result, 'EX', ttl);
  }
}
```

---

## Recommended Stack

**For CommandCenter Phase 1:**

1. **AI Routing:** OpenRouter (quick start, all models)
2. **MCP Servers:**
   - Hacker News (existing)
   - arXiv (build custom)
   - GitHub (build custom or use existing GitHub MCP)
3. **Local Models:** Ollama (optional, for privacy mode)
4. **Caching:** Redis (already in stack)
5. **Agent Framework:** Custom (based on AgentFlow patterns)

**Total Setup Time:** 2-3 weeks

**Monthly Costs (estimated):**
- OpenRouter: ~$50-200/month (depends on research volume)
- MCP servers: $0 (self-hosted)
- Local models: $0 (if GPU available)

---

## Next Steps

1. ✅ Set up OpenRouter account
2. ✅ Install Hacker News MCP in CommandCenter
3. ✅ Build arXiv MCP server prototype
4. ✅ Design model selection UI
5. ✅ Create research agent orchestration system

**Ready to start implementation?**
