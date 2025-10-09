# 🎯 LLM Command - Quick Reference

## ✨ Your New Smart LLM Command!

You now have a single `llm` command with slash commands for model selection!

## 🚀 Basic Usage

```bash
# Just ask a question (uses default model)
llm "What is the meaning of life?"

# Use slash commands to pick a model
llm /gpt5 "Your most complex question"
llm /opus "Write production-ready code"
llm /fast "Quick question"
llm /free "Private local query"
```

## ⚡ Quick Slash Commands

### Top Models
- `/gpt5` - OpenAI GPT-5 (smartest)
- `/opus` - Claude Opus 4.1 (best coder)
- `/gemini` - Gemini 2.5 Pro (thinking)

### Fast Options
- `/sonnet` - Claude Sonnet 4
- `/flash` - Gemini Flash
- `/groq` - Ultra-fast Groq

### Special Purpose
- `/o3` - Advanced reasoning
- `/code` - Best for coding
- `/think` - Deep thinking
- `/local` - Free, private

### Smart Selects
- `/smart` - Picks smartest model
- `/fast` - Picks fastest model  
- `/free` - Uses local model
- `/cheap` - Cheapest cloud option

## 📋 Utility Commands

```bash
# Show all options
llm /help
llm /models

# Compare models
llm /compare "What is consciousness?"

# Check costs
llm /cost

# System status
llm /status
```

## 💡 Pro Tips

### Set Default Model
```bash
# In your .zshrc
export LLM_MODEL="claude-sonnet-4"  # Your favorite

# Or temporarily
LLM_MODEL=gpt-5 llm "Use GPT-5 by default for this session"
```

### Quick Aliases
Add to your `.zshrc`:
```bash
alias ask='llm'
alias smart='llm /smart'
alias fast='llm /fast'
alias code='llm /code'
```

### Piping
```bash
# Still works with pipes!
cat file.txt | xargs llm /opus
echo "text" | xargs llm /gemini "Analyze this:"
```

## 🎨 Examples

```bash
# Quick check
llm /status

# Smart coding
llm /code "Write a Python REST API with FastAPI"

# Fast response
llm /fast "What's 2+2?"

# Free and private
llm /local "Analyze this sensitive data"

# Compare approaches
llm /compare "How do I learn machine learning?"

# Check spending
llm /cost
```

## 🔄 Model Switching Flow

```bash
# Start with fast
llm /fast "Draft an email about..."

# Refine with smart
llm /smart "Improve this email: [paste]"

# Final check with balanced
llm /sonnet "Is this email professional?"
```

## 🆘 Troubleshooting

```bash
# If not working
source ~/.zshrc

# Make sure Docker is running
cd ~/Projects/Dev-workflow && docker compose up -d

# Check what's available
llm /help

# Test specific model
llm /gpt5 "test"
```

## 📝 Complete Model List

| Slash | Model | Description |
|-------|-------|-------------|
| `/gpt5` | GPT-5 | OpenAI's latest |
| `/gpt4` | GPT-4o | GPT-4 Optimized |
| `/gpt4.1` | GPT-4.1 | Better GPT-4 |
| `/opus` | Claude Opus 4.1 | Most capable |
| `/sonnet` | Claude Sonnet 4 | Balanced |
| `/claude` | Claude 3.5 Sonnet | Standard Claude |
| `/haiku` | Claude 3.5 Haiku | Fast & cheap |
| `/gemini` | Gemini 2.5 Pro | Thinking model |
| `/flash` | Gemini 2.5 Flash | Fast Gemini |
| `/o3` | OpenAI o3 | Reasoning |
| `/o4` | OpenAI o4-mini | Fast reasoning |
| `/groq` | Groq Llama 8B | Ultra-fast |
| `/groq70` | Groq Llama 70B | Fast & capable |
| `/local` | Ollama Llama | Free & private |

---

**That's it!** Just `llm` for default, or `llm /model` to choose. Simple! 🎉
