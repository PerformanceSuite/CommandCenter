# 🚀 Dev-Workflow Model Reference Guide

## 🆕 Latest & Greatest Models (December 2024)

### 🌟 Top Tier - Most Capable
```bash
# OpenAI GPT-5 (Latest release)
MODEL=gpt-5 ./bin/ask "Your most complex question"

# Claude Opus 4.1 (Most capable Claude)
MODEL=claude-opus-4.1 ./bin/ask "Advanced reasoning task"

# Gemini 2.5 Pro (Thinking model)
MODEL=gemini-2.5-pro ./bin/ask "Complex problem solving"
```

### ⚡ Speed Demons - Fast & Efficient
```bash
# OpenAI o4-mini (Fast reasoning)
MODEL=o4-mini ./bin/ask "Quick analysis"

# Claude Sonnet 4 (Balance of speed & capability)
MODEL=claude-sonnet-4 ./bin/ask "Code generation"

# Gemini 2.5 Flash (Best price/performance)
MODEL=gemini-2.5-flash ./bin/ask "Everyday tasks"

# Groq Llama 3.1 8B (ULTRA fast)
MODEL=groq-llama3.1-8b ./bin/ask "Need it NOW"
```

### 🧠 Reasoning Specialists
```bash
# OpenAI o3 (Advanced reasoning)
MODEL=o3 ./bin/ask "Step-by-step math problem"

# GPT-5 Pro (Extended thinking)
MODEL=gpt-5-pro ./bin/ask "PhD-level question"
```

### 💻 Coding Champions
```bash
# Claude Opus 4.1 (Best for complex code)
MODEL=claude-opus-4.1 ./bin/ask "Refactor this codebase"

# Gemini 2.0 Pro (Strong coding)
MODEL=gemini-2.0-pro ./bin/ask "Build a full app"

# GPT-4.1 (Excellent for SWE tasks)
MODEL=gpt-4.1 ./bin/ask "Debug this function"
```

### 💰 Budget Friendly
```bash
# Claude 3.5 Haiku (Fast & cheap)
MODEL=claude-3.5-haiku ./bin/ask "Simple task"

# Gemini 2.0 Flash Lite (Ultra budget)
MODEL=gemini-2.0-flash-lite ./bin/ask "Bulk processing"

# Local models (FREE!)
MODEL=ollama-llama3.1-8b ./bin/ask "Private data analysis"
```

## 📊 Model Comparison

| Provider | Latest Flagship | Best Coder | Fastest | Budget |
|----------|----------------|------------|---------|---------|
| OpenAI | GPT-5 | GPT-4.1 | o4-mini | GPT-4.1-nano |
| Anthropic | Opus 4.1 | Opus 4.1 | Sonnet 4 | Haiku 3.5 |
| Google | Gemini 2.5 Pro | Gemini 2.0 Pro | Gemini 2.5 Flash | Flash Lite |
| Groq | - | - | Llama 3.1 8B | Gemma2 9B |
| Local | - | - | Qwen 2.5 7B | Llama 3.1 8B |

## 🎯 When to Use What

### For Maximum Intelligence:
- **GPT-5** - OpenAI's most advanced
- **Claude Opus 4.1** - Anthropic's best
- **Gemini 2.5 Pro** - Google's thinking model

### For Coding:
- **Claude Opus 4.1** - Complex refactoring
- **GPT-4.1** - SWE-bench champion
- **Gemini 2.0 Pro** - Web development

### For Speed:
- **Groq models** - Millisecond responses
- **Claude Sonnet 4** - Fast & capable
- **Gemini 2.5 Flash** - Quick & smart

### For Cost Savings:
- **Local Ollama** - Completely free
- **Claude Haiku** - Cheap API
- **Gemini Flash Lite** - Budget cloud

## 🔧 Quick Commands

```bash
# Compare models on the same prompt
for model in gpt-5 claude-opus-4.1 gemini-2.5-pro; do
  echo "=== $model ==="
  MODEL=$model ./bin/ask "Explain quantum computing in one sentence"
done

# Test all coding models
for model in claude-opus-4.1 gpt-4.1 gemini-2.0-pro; do
  MODEL=$model ./bin/ask "Write a Python fibonacci function"
done

# Speed test
time MODEL=groq-llama3.1-8b ./bin/ask "Hello"
time MODEL=gemini-2.5-flash ./bin/ask "Hello"
time MODEL=claude-sonnet-4 ./bin/ask "Hello"
```

## 📝 Notes

- **GPT-5** is brand new (Dec 2024) - most advanced OpenAI model
- **Claude Opus 4.1** released Aug 2025 - current state-of-the-art
- **Gemini 2.5** models have "thinking" capabilities built-in
- **o3/o4** models are specialized for reasoning tasks
- **Groq** provides the fastest inference (100+ tokens/sec)
- **Local models** work offline and are completely private

## 🚨 Important

Some models may require:
- API access approval (GPT-5, o3)
- Higher rate limits (check your account)
- Specific API endpoints or headers

Always check the latest pricing before high-volume use!
