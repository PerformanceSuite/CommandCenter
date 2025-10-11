# AI Models Reference & Update Strategy

**Last Updated**: 2025-10-11
**Review Frequency**: Monthly (check for model updates)

This document tracks the latest AI models across all supported providers and provides a strategy for staying current with new releases.

---

## 🚀 Latest Models (October 2025)

### Anthropic Claude

**Current Recommended**: `claude-sonnet-4-5` (Released Sep 29, 2025)

| Model ID | Released | Context | Cost (Input/Output per 1M tokens) | Best For |
|----------|----------|---------|-----------------------------------|----------|
| `claude-sonnet-4-5-20250929` | Sep 2025 | 200K (1M with beta) | $3/$15 | **Best coding model**, complex agents, computer use |
| `claude-opus-4-1-20250805` | Aug 2025 | 200K (1M with beta) | $15/$75 | Most capable reasoning, advanced coding |
| `claude-sonnet-4-20250522` | May 2025 | 200K (1M with beta) | $3/$15 | High-performance reasoning |

**API Reference**: https://docs.anthropic.com/en/docs/about-claude/models

**Key Features** (API):
- Extended context: Use `context-1m-2025-08-07` beta header for 1M tokens
- Code execution tool (beta)
- MCP connector support
- Files API
- Prompt caching (up to 1 hour)

---

### OpenAI GPT

**Current Recommended**: `gpt-5` (Released Aug 2025)

| Model ID | Released | Context | Cost | Best For |
|----------|----------|---------|------|----------|
| `gpt-5` | Aug 2025 | 1M tokens | TBD | State-of-the-art coding (74.9% SWE-bench), math, reasoning |
| `gpt-5-mini` | Aug 2025 | 1M tokens | Lower cost | Balanced performance/cost |
| `gpt-5-nano` | Aug 2025 | TBD | Lowest cost | High-throughput, low-latency |
| `gpt-4-1` | 2025 | 1M tokens | TBD | Previous generation flagship |
| `gpt-4-1-mini` | 2025 | 1M tokens | Lower | Improved over gpt-4o-mini |

**API Reference**: https://platform.openai.com/docs/models

**Key Features**:
- Extended context windows (1M tokens)
- Improved long-context comprehension
- Major gains in coding and instruction following
- Voice models: `gpt-realtime`, `gpt-realtime-mini`
- Image generation: `gpt-image-1`

---

### Google Gemini

**Current Recommended**: `gemini-2.5-pro` (2025)

| Model ID | Released | Context | Cost | Best For |
|----------|----------|---------|------|----------|
| `gemini-2.5-pro` | 2025 | 1M (2M soon) | TBD | State-of-the-art reasoning with adaptive thinking |
| `gemini-2.5-flash` | Sep 2025 | 1M | Lower | Best price-performance, agentic use cases (54% SWE-Bench) |
| `gemini-2.5-flash-lite` | Sep 2025 | 1M | Lowest | Fastest, high-throughput (50% token reduction) |
| `gemini-2.5-computer-use` | 2025 | TBD | TBD | Browser/mobile UI automation |
| `gemini-2.0-flash` | 2025 | 1M | Lower | Next-gen speed, native tool use |

**API Reference**: https://ai.google.dev/gemini-api/docs/models

**Key Features**:
- Multimodal: text, images, video, audio
- Adaptive thinking (Pro model)
- Native audio output (24+ languages, 30+ voices)
- Computer Use capabilities (beta)
- Improved agentic tool use

---

## 🔄 Model Update Strategy

### 1. Monthly Review Schedule

**Action**: Review this document monthly to check for new models.

**Sources to Monitor**:
- Anthropic: https://www.anthropic.com/news + https://docs.anthropic.com/en/docs/about-claude/models
- OpenAI: https://openai.com/index + https://platform.openai.com/docs/models
- Google: https://developers.googleblog.com/ + https://ai.google.dev/gemini-api/docs/changelog

**Calendar Reminder**: Set recurring reminder on 1st of each month to review.

### 2. Notification System (Future Enhancement)

**Phase 1**: Manual monthly checks (current)

**Phase 2**: Automated webhook monitoring (future)
- Subscribe to provider status pages/RSS feeds
- GitHub Actions workflow to check model APIs weekly
- Auto-create GitHub issue when new model detected

**Phase 3**: In-app notification system (future)
- Backend service to poll provider APIs for model list changes
- Admin dashboard notification when new models available
- One-click config update

### 3. Update Process

When a new model is released:

1. **Update this document** (`docs/AI_MODELS.md`)
   - Add new model to table
   - Update "Last Updated" date
   - Note any breaking changes

2. **Update `.env.example`** (`backend/.env.example`)
   - Update `DEFAULT_MODEL` if new recommended model
   - Add comments with new model options
   - Document any new required env vars

3. **Update configuration** (`backend/app/config.py`)
   - Update `default_model` Field description with latest options
   - No code changes needed (env-driven)

4. **Test new model**
   - Run E2E test with new model: `python scripts/test_research_e2e.py`
   - Verify API compatibility
   - Check for breaking changes

5. **Update project `.env`**
   - Update production/staging `.env` files with new model
   - Restart services to pick up changes

6. **Notify team**
   - Create GitHub issue with model update summary
   - Update project README/CHANGELOG
   - Slack/email notification to team

### 4. Version Pinning Strategy

**SDK Version Ranges** (in `requirements.txt`):
```python
# Latest SDK versions (October 2025)
openai>=2.3.0,<3.0.0  # Latest: 2.3.0 (Oct 10, 2025)
anthropic>=0.69.0,<0.70.0  # Latest: 0.69.0 (Sep 29, 2025)
google-genai>=1.0.0,<2.0.0  # NEW SDK (replaces google-generativeai, GA May 2025)
litellm>=1.30.0,<1.50.0  # Multi-provider proxy
```

**⚠️ BREAKING CHANGE**: Google SDK Migration
- **Old**: `google-generativeai` (deprecated, support ends Aug 31, 2025)
- **New**: `google-genai` (General Availability, production-ready)
- **Migration Required**: Update imports from `import google.generativeai` to `from google import genai`
- See: https://cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview

**Model Version Pinning** (in `.env`):
- **Development**: Use dated model IDs (e.g., `claude-sonnet-4-5-20250929`) for reproducibility
- **Production**: Consider using undated aliases (e.g., `claude-sonnet-4-5`) for auto-updates
- **Critical Systems**: Always use dated IDs to prevent breaking changes

---

## 📊 Model Selection Guidelines

### For Research Agents (CommandCenter Default)

**Primary**: `claude-sonnet-4-5` (Anthropic)
- Best coding performance
- Strong agentic capabilities
- Good context handling (1M tokens)
- Moderate cost

**Alternative**: `gemini-2.5-flash` (Google)
- Best price-performance
- Good agentic tool use (54% SWE-Bench)
- Fast, high-throughput
- Lower cost

**Fallback**: `gpt-5-mini` (OpenAI)
- Balanced performance/cost
- Strong coding (GPT-5 family)
- 1M token context
- Reliable availability

### Cost-Optimization Strategy

1. **Development/Testing**: Use `-mini` or `-flash` variants
2. **Production (High-Stakes)**: Use flagship models (`claude-sonnet-4-5`, `gpt-5`, `gemini-2.5-pro`)
3. **High-Volume Tasks**: Use `-lite` or `-nano` variants
4. **Reasoning-Heavy**: Use thinking models (`gemini-2.5-pro`, `claude-opus-4-1`)

---

## 🛠️ Configuration Examples

### Anthropic (Recommended Default)
```bash
DEFAULT_AI_PROVIDER=anthropic
DEFAULT_MODEL=claude-sonnet-4-5-20250929
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### OpenAI
```bash
DEFAULT_AI_PROVIDER=openai
DEFAULT_MODEL=gpt-5
OPENAI_API_KEY=sk-proj-...
```

### Google Gemini
```bash
DEFAULT_AI_PROVIDER=google
DEFAULT_MODEL=gemini-2.5-pro
GOOGLE_API_KEY=AIzaSy...
```

### Multi-Provider (OpenRouter)
```bash
DEFAULT_AI_PROVIDER=openrouter
DEFAULT_MODEL=anthropic/claude-sonnet-4-5  # Note: namespace required
OPENROUTER_API_KEY=sk-or-v1-...
```

---

## 🔍 Verification Commands

Check currently configured model:
```bash
docker-compose exec backend python -c "from app.config import settings; print(f'Provider: {settings.default_ai_provider}\nModel: {settings.default_model}')"
```

Test model API access:
```bash
cd backend
python scripts/test_research_e2e.py
```

List available models via API:
```bash
# Anthropic
curl https://api.anthropic.com/v1/models -H "x-api-key: $ANTHROPIC_API_KEY"

# OpenAI
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"

# Google (requires OAuth, see docs)
```

---

## 📝 Changelog

### 2025-10-11
- Initial documentation created
- Added latest models: Claude Sonnet 4.5, GPT-5, Gemini 2.5 Pro
- Established monthly review schedule
- Defined update process and notification strategy

---

## 🔗 Additional Resources

- [Provider API Comparison](https://artificialanalysis.ai/models)
- [Model Benchmarks (SWE-Bench)](https://www.swebench.com/)
- [Cost Calculator](https://docsbot.ai/tools/gpt-openai-api-pricing-calculator)
- [Anthropic Model Deprecation Policy](https://docs.anthropic.com/en/docs/about-claude/model-deprecation)
- [OpenAI Model Lifecycle](https://platform.openai.com/docs/deprecations)
