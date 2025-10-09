# 🚀 Smart LLM Command with Auto-Start

## ✨ The Ultimate LLM Command!

Your `llm` command now **automatically starts everything** for you!

## 🎯 Key Features

### Auto-Start Magic 🪄
- **Starts Docker Desktop** if not running
- **Starts LiteLLM proxy** automatically
- **Waits for everything** to be ready
- **No manual setup needed!**

## 📚 Basic Usage

```bash
# Just ask - it handles EVERYTHING automatically!
llm "What is the meaning of life?"

# First time? It will:
# 1. Start Docker Desktop (if needed)
# 2. Start the LiteLLM proxy
# 3. Wait for everything to be ready
# 4. Then answer your question!

# Use slash commands for specific models
llm /gpt5 "Complex question"
llm /fast "Quick response"
llm /free "Private local query"
```

## ⚡ Slash Commands

### Top Models
- `/gpt5` - OpenAI GPT-5
- `/opus` - Claude Opus 4.1
- `/gemini` - Gemini 2.5 Pro

### Fast Options
- `/sonnet` - Claude Sonnet 4
- `/flash` - Gemini Flash
- `/groq` - Ultra-fast Groq

### Smart Selects
- `/smart` - Smartest model
- `/fast` - Fastest model
- `/free` - Local model (FREE)
- `/cheap` - Cheapest cloud

### Special Commands
- `/code` - Best for coding
- `/think` - Deep thinking
- `/reason` - Advanced reasoning

## 🛠️ System Commands

```bash
# Check everything
llm /status

# View help
llm /help

# Compare models
llm /compare "test question"

# Check costs
llm /cost

# Stop containers (save resources)
llm /stop
```

## 🌟 Auto-Start Behavior

When you run any query, the command will:

1. **Check Docker** → Start if needed (30s)
2. **Check LiteLLM** → Start if needed (10s)
3. **Verify ready** → Wait for API response
4. **Run query** → Process your request

### First Run Example:
```bash
$ llm "Hello world"
🚀 Starting Docker Desktop...
...
🔄 Starting LiteLLM proxy...
⏳ Waiting for LiteLLM to be ready...
✅ LiteLLM proxy is ready!
🤖 Using gpt-4o...

Hello! How can I help you today?
```

### Subsequent Runs:
```bash
$ llm /fast "What's 2+2?"
🤖 Using groq-llama3.1-8b...

2 + 2 = 4
```

## 💡 Pro Tips

### Set Your Default Model
```bash
# Add to ~/.zshrc
export LLM_MODEL="claude-sonnet-4"  # Your preference
```

### Quick Aliases
```bash
# Add to ~/.zshrc
alias ai='llm'
alias ask='llm'
alias smart='llm /smart'
alias fast='llm /fast'
alias code='llm /code'
```

### Save Resources
```bash
# When done for the day
llm /stop  # Stops containers, saves memory/CPU
```

### Morning Routine
```bash
# First query of the day auto-starts everything
llm "What's on my schedule today?"
# Everything starts automatically!
```

## 🎨 Example Workflows

### Quick Development Session
```bash
# Morning - everything auto-starts
llm /code "Write a Python REST API"

# Iterate fast
llm /fast "Add error handling"

# Polish with best model
llm /opus "Review and improve this code"

# End of day - clean up
llm /stop
```

### Research Workflow
```bash
# Start with fast exploration
llm /fast "What is quantum computing?"

# Deep dive with smart model
llm /smart "Explain quantum entanglement in detail"

# Compare perspectives
llm /compare "How do quantum computers work?"
```

## 🔧 Troubleshooting

### If Docker won't start:
```bash
# Manually start Docker Desktop
open -a "Docker Desktop"

# Wait 30 seconds, then try
llm /status
```

### If queries fail:
```bash
# Check status
llm /status

# Restart everything
llm /stop
llm /status  # This will auto-start
```

### Reset everything:
```bash
cd ~/Projects/Dev-workflow
docker compose down
docker compose up -d
llm /status
```

## 📊 Status Indicators

When you run `llm /status`:
- ✅ **Green checkmarks** = Running
- ❌ **Red X** = Not running (will auto-start)
- ⚠️ **Yellow warning** = Starting up

## 🎉 That's It!

Just type `llm` followed by your question. Everything else is automatic!

```bash
# It's this simple:
llm "How do I learn Python?"

# With model selection:
llm /gpt5 "Explain consciousness"

# Done for the day:
llm /stop
```

**No more manual Docker commands. No more checking if things are running. Just ask and get answers!** 🚀
