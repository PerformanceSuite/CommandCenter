# 🎯 Interactive LLM - Quick Reference

## Starting the Interactive CLI

```bash
llm
```

That's it! Everything auto-starts.

## 🎮 Interactive Commands

Once inside the LLM environment:

### Model Switching
- `/models` - Show all available models
- `/1` to `/15` - Switch by number
- `/gpt4` - Switch to GPT-4o
- `/opus` - Switch to Claude Opus
- `/sonnet` - Switch to Claude Sonnet
- `/gemini` - Switch to Gemini Pro
- `/fast` - Switch to Groq (ultra-fast)
- `/local` - Switch to Ollama (free)

### Utilities
- `/help` - Show commands
- `/clear` - Clear screen
- `/status` - System status
- `/cost` - Usage costs
- `/exit` - Exit interactive mode

## 📊 Available Models (Working)

```
[1]  gpt-4o              - GPT-4 Optimized
[2]  gpt-4o-mini         - GPT-4 Mini (fast)
[3]  claude-3-opus       - Claude 3 Opus (best)
[4]  claude-3-5-sonnet   - Claude 3.5 Sonnet
[5]  claude-3-haiku      - Claude 3 Haiku (fast)
[6]  gemini-1.5-pro      - Gemini 1.5 Pro
[7]  gemini-1.5-flash    - Gemini Flash
[8]  groq-llama3.1-8b    - Ultra-fast Groq
[9]  groq-llama3.1-70b   - Groq 70B
[10] groq-mixtral        - Mixtral 8x7B
[11] openrouter-claude   - Claude via OpenRouter
[12] openrouter-gpt-4    - GPT-4 via OpenRouter
[13] ollama-llama3.1-8b  - Local Llama (FREE)
[14] ollama-qwen2.5-7b   - Local Qwen (FREE)
[15] gpt-4-turbo         - GPT-4 Turbo
```

## 💡 Usage Examples

### Basic Chat
```
> [gpt-4o] Hello, how are you?
I'm doing well, thank you! How can I help you today?
```

### Switch Models Mid-Conversation
```
> [gpt-4o] Explain recursion
[GPT explains recursion]
> [gpt-4o] /3
Switched to claude-3-opus
> [claude-3-opus] Can you explain it differently?
[Claude explains recursion differently]
```

### Quick Model Test
```
> [gpt-4o] /8
Switched to groq-llama3.1-8b
> [groq-llama3.1-8b] Count to 10
[Super fast response]
```

### Check Costs
```
> [gpt-4o] /cost
Recent costs:
2024-09-25 13:30  gpt-4o  $0.0021
2024-09-25 13:29  claude-3-opus  $0.0150
```

## 🔧 Troubleshooting

### Container not running?
```bash
cd ~/Projects/Dev-workflow
docker compose up -d
```

### Permission denied?
```bash
source ~/.zshrc
```

### Want one-shot queries instead?
```bash
# Use llm-quick for single queries
llm-quick "What is 2+2?"
```

## 🎨 Tips

1. **Start with `/models`** to see what's available
2. **Use numbers** (`/1`, `/2`) for quick switching
3. **Try `/fast`** for instant responses
4. **Use `/local`** for private/sensitive queries
5. **Check `/cost`** periodically to track spending

---

**Remember: Just type `llm` and start chatting!**
