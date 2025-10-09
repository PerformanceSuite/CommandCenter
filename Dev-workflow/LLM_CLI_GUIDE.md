# 🎯 Simon Willison's LLM CLI Guide

The `llm` CLI is now configured to work with your Dev-workflow proxy! This gives you another powerful way to interact with all your models.

## ✅ Setup Complete

The `llm` CLI is installed and configured to:
- Use your local LiteLLM proxy (port 4000)
- Access ALL your configured models
- Work with convenient aliases

## 📚 Basic Usage

```bash
# Using full model names
llm -m openai/gpt-5 "Your question"
llm -m openai/claude-opus-4.1 "Complex task"
llm -m openai/gemini-2.5-pro "Analyze this"

# Using aliases (shorter!)
llm -m gpt5 "Your question"
llm -m opus "Complex task"  
llm -m gemini "Analyze this"
```

## 🚀 Available Aliases

| Alias | Full Model | Description |
|-------|------------|-------------|
| `gpt5` | openai/gpt-5 | Latest GPT-5 |
| `gpt4o` | openai/gpt-4o | GPT-4 Optimized |
| `o3` | openai/o3 | OpenAI o3 reasoning |
| `o4mini` | openai/o4-mini | Fast reasoning |
| `opus` | openai/claude-opus-4.1 | Claude Opus 4.1 |
| `sonnet` | openai/claude-sonnet-4 | Claude Sonnet 4 |
| `claude` | openai/claude-3.5-sonnet | Claude 3.5 Sonnet |
| `haiku` | openai/claude-3.5-haiku | Claude Haiku (fast) |
| `gemini` | openai/gemini-2.5-pro | Gemini 2.5 Pro |
| `flash` | openai/gemini-2.5-flash | Gemini Flash |
| `groq` | openai/groq-llama3.1-70b | Groq Llama 70B |
| `fast` | openai/groq-llama3.1-8b | Ultra-fast Groq |
| `local` | openai/ollama-llama3.1-8b | Local Llama |

## 💡 Advanced Features

### Piping and Files
```bash
# Pipe content to LLM
cat script.py | llm -m opus "Review this code"

# Analyze files
llm -m gpt5 < document.txt

# Save output
llm -m gemini "Write a README" > README.md
```

### System Prompts
```bash
# Set system prompt
llm -m claude -s "You are a helpful coding assistant" "Write a Python function"

# Save as template
llm -m opus --save reviewer "You are a code reviewer"
llm -m opus -t reviewer "Review this: $(cat code.py)"
```

### Conversation Mode
```bash
# Start a conversation
llm chat -m gpt5

# Continue previous conversation
llm logs -n 1 --continue
```

### Logging and History
```bash
# View recent queries
llm logs

# Search logs
llm logs -q "python"

# Get last response
llm logs -n 1 --json | jq '.response'
```

## 🔧 Configuration

### View Current Config
```bash
# Show all keys
llm keys

# Show model aliases
llm aliases

# Test connection
llm -m gpt4o "test"
```

### Add More Models
```bash
# Add any model from litellm.yaml
llm aliases set mynewmodel openai/model-name
```

### Change Settings
```bash
# Adjust timeout
llm keys set openai:timeout 120

# Change max tokens
llm keys set openai:max_tokens 4000
```

## 📊 Comparing Models

```bash
# Quick comparison
for model in gpt5 opus gemini; do
  echo "=== $model ==="
  echo "What is consciousness?" | llm -m $model --max-tokens 50
done

# Benchmark response times
time llm -m fast "Count to 10"
time llm -m local "Count to 10"
time llm -m opus "Count to 10"
```

## 🎨 Creative Uses

### Code Generation
```bash
llm -m opus "Write a Flask API for a todo app" > app.py
```

### Data Analysis
```bash
cat data.csv | llm -m gemini "Analyze this CSV and summarize key findings"
```

### Translation
```bash
echo "Hello world" | llm -m claude "Translate to Spanish, French, and Japanese"
```

### Git Commit Messages
```bash
git diff | llm -m fast "Generate a commit message for these changes"
```

## 🔌 Integration with Shell

Add to your `.zshrc`:
```bash
# LLM helper functions
ask() {
  llm -m "${1:-gpt4o}" "${@:2}"
}

code-review() {
  cat "$1" | llm -m opus "Review this code for bugs and improvements"
}

explain() {
  llm -m claude "Explain this in simple terms: $*"
}

# Usage:
# ask gpt5 "Your question"
# code-review script.py
# explain "quantum computing"
```

## 📝 Templates

Create useful templates:
```bash
# Save templates
llm --save bugfix "You are debugging code. Find and fix the bug."
llm --save optimize "Optimize this code for performance."
llm --save document "Write clear documentation for this code."

# Use templates
cat buggy.py | llm -t bugfix -m opus
cat slow.py | llm -t optimize -m gpt5
cat function.py | llm -t document -m claude
```

## ⚠️ Important Notes

1. **All models go through your local proxy** - The "openai/" prefix is just for compatibility
2. **Your actual API keys are secure** - The proxy handles authentication
3. **Costs are tracked in the proxy** - Check Docker logs for usage
4. **Make sure Docker is running** - `docker compose up -d` in Dev-workflow

## 🆘 Troubleshooting

```bash
# If llm command not found
export PATH="$PATH:/Users/danielconnolly/.local/bin"

# If connection refused
cd ~/Projects/Dev-workflow && docker compose up -d

# If model not working
llm -m openai/exact-model-name "test"  # Use full name

# Reset configuration
rm -rf ~/.config/io.datasette.llm/
./setup-llm-cli.sh
```

## 🎉 You're All Set!

You now have TWO ways to access your models:
1. **Direct CLI**: `./bin/ask` (in Dev-workflow)
2. **LLM CLI**: `llm` (anywhere in terminal)

Both use the same proxy, same models, same API keys. Choose whichever feels more comfortable!

---

**Pro Tip**: The `llm` CLI has many plugins available:
```bash
llm install llm-claude-3  # Direct Claude API support
llm install llm-gemini    # Direct Gemini support
# But you don't need these - your proxy handles everything!
```
