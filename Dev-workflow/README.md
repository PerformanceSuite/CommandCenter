# 🚀 Dev-Workflow: Interactive LLM Terminal

**Your personal AI command center!** An interactive terminal interface for ALL major LLM providers with zero friction setup.

## ✨ What You Get

Just type `llm` and enter an interactive AI environment like Gemini/Claude:
- 🎯 **Interactive chat interface** - Persistent session with model switching
- 🤖 **15+ AI models** - OpenAI, Anthropic, Google, Groq, local models
- 🚀 **Auto-starts everything** - Docker and proxy handled automatically
- 💬 **Real-time model switching** - Change models mid-conversation
- 📊 **Cost tracking** - Know exactly what you're spending
- 🔒 **Secure** - API keys in one protected location

## 🎯 Quick Start

```bash
# That's it! Just type:
llm

# You'll enter an interactive environment:
> LLM

Tips for getting started:
1. Ask questions, paste files, or describe tasks.
2. Be specific for the best results.
3. Type /models to see available models.
4. Type /help for more commands.

> [gpt-4o] Hello!
Hello! How can I assist you today?

> [gpt-4o] /models
# Shows all available models with numbers

> [gpt-4o] /3
Switched to Claude 3 Opus

> [claude-3-opus] Write a haiku
# Claude responds with a haiku
```

## 🤖 Available Models

### Currently Working Models

| Number | Command | Model | Description |
|--------|---------|-------|-------------|
| 1 | `/1` or `/gpt4` | gpt-4o | GPT-4 Optimized (default) |
| 2 | `/2` | gpt-4o-mini | GPT-4 Mini (faster) |
| 3 | `/3` or `/opus` | claude-3-opus | Claude 3 Opus (most capable) |
| 4 | `/4` or `/sonnet` | claude-3-5-sonnet | Claude 3.5 Sonnet |
| 5 | `/5` or `/haiku` | claude-3-haiku | Claude 3 Haiku (fast) |
| 6 | `/6` or `/gemini` | gemini-1.5-pro | Gemini 1.5 Pro |
| 7 | `/7` or `/flash` | gemini-1.5-flash | Gemini Flash (fast) |
| 8 | `/8` or `/fast` | groq-llama3.1-8b | Ultra-fast responses |
| 9 | `/9` or `/groq` | groq-llama3.1-70b | Groq 70B model |
| 10 | `/10` | groq-mixtral | Mixtral 8x7B |
| 11 | `/11` | openrouter-claude | Claude via OpenRouter |
| 12 | `/12` | openrouter-gpt-4 | GPT-4 via OpenRouter |
| 13 | `/13` or `/local` | ollama-llama3.1 | Local Llama (FREE) |
| 14 | `/14` | ollama-qwen2.5 | Local Qwen (FREE) |
| 15 | `/15` | gpt-4-turbo | GPT-4 Turbo |

## 📚 Interactive Commands

While in the LLM environment:

| Command | Description |
|---------|-------------|
| `/models` | List all available models with numbers |
| `/1` to `/15` | Quick switch to model by number |
| `/gpt4`, `/opus`, `/gemini`, etc | Switch by name |
| `/help` | Show all commands |
| `/clear` | Clear screen |
| `/status` | Check system status |
| `/cost` | View usage costs |
| `/exit` or `/quit` | Exit interactive mode |

## 🛠️ Setup

### Prerequisites
- Docker Desktop
- Terminal (zsh)
- API keys for providers you want to use

### Installation
1. Clone this repository
2. Add your API keys to `.env`
3. Source your `.zshrc`
4. Type `llm`

The system auto-starts Docker and the LiteLLM proxy on first use!

## 📂 Project Structure

```
Dev-workflow/
├── bin/
│   ├── llm-interactive    # Interactive CLI (main)
│   ├── ask                # Query script
│   └── llm                # One-shot query tool
├── litellm.yaml           # Model configurations
├── docker-compose.yml     # Container setup
├── .env                   # API keys (create from .env.example)
└── *.md                   # Documentation files
```

## 🔧 Configuration

### Default Model
Edit `~/.zshrc`:
```bash
export LLM_MODEL="claude-3-opus"  # Your preference
```

### Add More Models
Edit `litellm.yaml` to add new models or providers.

### API Keys
Store in `.env`:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...
```

## 💡 Usage Examples

### Interactive Conversation
```bash
llm
> [gpt-4o] Explain quantum computing
# Get explanation
> [gpt-4o] /opus
> [claude-3-opus] Now explain it to a 5 year old
# Get simpler explanation from Claude
```

### Quick Model Comparison
```bash
llm
> [gpt-4o] /models
# See all models
> [gpt-4o] What is consciousness?
# GPT-4 answer
> [gpt-4o] /3
> [claude-3-opus] What is consciousness?
# Claude's answer
> [claude-3-opus] /6
> [gemini-1.5-pro] What is consciousness?
# Gemini's answer
```

### Cost Tracking
```bash
llm
> [gpt-4o] /cost
# Shows recent usage and costs
> [gpt-4o] /status
# Shows system status
```

## 🐳 Docker Management

The system auto-manages Docker, but you can control it manually:

```bash
# Check if running
docker ps | grep litellm

# View logs
docker logs litellm

# Restart
cd ~/Projects/Dev-workflow
docker compose restart

# Stop
docker compose down
```

## 🆘 Troubleshooting

### If LLM won't start:
```bash
# Make sure Docker Desktop is running
open -a "Docker Desktop"

# Restart the container
cd ~/Projects/Dev-workflow
docker compose down
docker compose up -d

# Try again
llm
```

### If "permission denied":
```bash
chmod +x /Users/danielconnolly/Projects/Dev-workflow/bin/llm-interactive
source ~/.zshrc
```

### If queries fail:
1. Check Docker is running: `docker ps`
2. Check logs: `docker logs litellm`
3. Verify API keys in `.env`
4. Try a different model: `/models` then `/1`

## 📚 Documentation Files

- **README.md** - This file, main documentation
- **MODEL_GUIDE.md** - Detailed model information
- **DOCUMENTATION_INDEX.md** - Overview of all docs
- **litellm.yaml** - Model configuration reference

## 🎉 Features

✅ **Working Now:**
- Interactive chat interface like Gemini
- 15+ models from all major providers
- Auto-start Docker and proxy
- Model switching mid-conversation
- Cost tracking
- Clean, simple interface

🚧 **Coming Soon:**
- Conversation history saving
- Custom system prompts
- File upload support
- Multi-turn context management

## 📝 License

MIT - Use freely!

## 🙏 Credits

Built on:
- [LiteLLM](https://github.com/BerriAI/litellm) - Universal LLM proxy
- Docker for containerization
- Bash for the interactive interface

---

**Just type `llm` and start chatting with AI!** 🚀
