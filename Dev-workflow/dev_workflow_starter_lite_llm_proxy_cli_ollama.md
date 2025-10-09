# Dev Workflow Starter: LiteLLM Proxy + CLI + Ollama

A minimal, vendor‑agnostic setup to run *all* your models (OpenAI, Anthropic, Google, Groq, OpenRouter, local Ollama) behind one local endpoint and a tiny CLI.

---

## 0) Project layout

```
./dev-workflow/
├─ .env.example
├─ litellm.yaml
├─ docker-compose.yml
├─ bin/
│  ├─ ask
│  └─ ask-json
└─ examples/
   ├─ curl-openai.sh
   ├─ curl-gemini.sh
   └─ llm-config.md
```

> Copy this folder anywhere (e.g., `~/Projects/dev-workflow`) and `chmod +x bin/*`.

---

## 1) Bring up LiteLLM Proxy (port 4000)

### Option A — Docker (recommended)

**docker-compose.yml**
```yaml
services:
  litellm:
    image: ghcr.io/berriai/litellm:main
    container_name: litellm
    ports:
      - "4000:4000"
    env_file:
      - .env
    volumes:
      - ./litellm.yaml:/app/litellm.yaml:ro
      - ./logs:/app/logs
    command: ["--config", "/app/litellm.yaml", "--port", "4000", "--host", "0.0.0.0"]
```

Run:
```bash
cp .env.example .env
# fill your API keys in .env
docker compose up -d
```

### Option B — Python
```bash
pipx install litellm
export LITELLM_CONFIG=./litellm.yaml
litellm --port 4000 --host 0.0.0.0
```

---

## 2) LiteLLM config (routes, fallbacks, logging)

**litellm.yaml**
```yaml
# One place to map friendly names → providers/models
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
  - model_name: o4-mini
    litellm_params:
      model: openai/o4-mini
  - model_name: claude-3.7
    litellm_params:
      model: anthropic/claude-3-7-sonnet
  - model_name: gemini-1.5-pro
    litellm_params:
      model: google/gemini-1.5-pro
  - model_name: groq-llama3.1-70b
    litellm_params:
      model: groq/llama-3.1-70b-versatile
  - model_name: openrouter-qwen2.5-32b
    litellm_params:
      model: openrouter/qwen2.5:32b
  - model_name: ollama-llama3.1-8b
    litellm_params:
      model: ollama/llama3.1:8b

# Provider credentials from environment
# (see .env.example)

# Routing & resilience
router_settings:
  num_retries: 2
  timeout: 120
  default_fallbacks:
    # If first choice fails/rate-limits, fall back in order
    gpt-4o:
      - claude-3.7
      - gemini-1.5-pro
    claude-3.7:
      - gpt-4o
      - gemini-1.5-pro
    gemini-1.5-pro:
      - gpt-4o
      - claude-3.7

# Logging & spend tracking (local SQLite)

general_settings:
  master_key: dev_master_key_please_change
  telemetry: false

litellm_settings:
  cache: true
  caching_redis: false
  set_verbose: false
  drop_params: true

proxy_logging:
  log_path: /app/logs/requests.log
  save: true
  print_verbose: false
  sqlite_path: /app/logs/litellm.db

# Rate limits (optional examples)
# proxy_rate_limiter:
#   tokens: 120
#   refill_rate: 120
#   window_seconds: 60
#   per_client: true
```

---

## 3) Secrets & keys

**.env.example**
```bash
# OpenAI
OPENAI_API_KEY=
# Anthropic
ANTHROPIC_API_KEY=
# Google Generative AI (Gemini)
GOOGLE_API_KEY=
# Groq
GROQ_API_KEY=
# OpenRouter
OPENROUTER_API_KEY=

# Ollama: no key required, ensure daemon is running
# If running Ollama on host: expose 11434 to the container if needed
# (not required if litellm also runs on host)
```

Fill `.env` with your real keys. Only add providers you use.

---

## 4) Tiny CLI front-ends

**bin/ask** — human-friendly chat via curl
```bash
#!/usr/bin/env bash
set -euo pipefail
MODEL="${MODEL:-gpt-4o}"   # default; override: MODEL=claude-3.7 ask "..."
ROLE="${ROLE:-user}"
URL="${URL:-http://localhost:4000/v1/chat/completions}"

prompt="$*"

curl -sS "$URL" \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer dev_master_key_please_change' \
  -d @<(cat <<JSON
{
  "model": "$MODEL",
  "messages": [
    {"role": "system", "content": "You are a concise, helpful coding assistant."},
    {"role": "$ROLE", "content": ${prompt@Q}}
  ],
  "temperature": ${TEMP:-0.2},
  "stream": false
}
JSON
) | jq -r '.choices[0].message.content'
```

**bin/ask-json** — returns the raw JSON
```bash
#!/usr/bin/env bash
set -euo pipefail
MODEL="${MODEL:-gpt-4o}"
URL="${URL:-http://localhost:4000/v1/chat/completions}"

prompt="$*"

curl -sS "$URL" \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer dev_master_key_please_change' \
  -d @<(cat <<JSON
{
  "model": "$MODEL",
  "messages": [
    {"role": "system", "content": "You output strict JSON when asked."},
    {"role": "user", "content": ${prompt@Q}}
  ],
  "temperature": ${TEMP:-0.0},
  "response_format": {"type": "json_object"},
  "stream": false
}
JSON
)
```

Usage:
```bash
bin/ask "Summarize the repo layout"
MODEL=claude-3.7 bin/ask "Draft a PR description"
MODEL=ollama-llama3.1-8b bin/ask "Brainstorm 10 ideas"
```

---

## 5) Local model (Ollama)

Install & pull a fast draft model:
```bash
brew install ollama
ollama serve &
ollama pull llama3.1:8b
```

> Already mapped in `litellm.yaml` as `ollama-llama3.1-8b`. Switch via `MODEL=ollama-llama3.1-8b`.

Optional higher-quality local:
```bash
o_llama=llama3.1:70b
o_mistral=nemotron-mini:4b-instruct
# pick any supported model; ensure your GPU/VRAM can handle it
```

---

## 6) Vendor-native (example: Gemini via REST)

**examples/curl-gemini.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
: "${GOOGLE_API_KEY:?Set GOOGLE_API_KEY}"
MODEL=${MODEL:-gemini-1.5-pro}
PROMPT=${1:-"Hello from curl"}

curl -sS \
  -H 'Content-Type: application/json' \
  -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${GOOGLE_API_KEY}" \
  -d @<(cat <<JSON
{ "contents": [{"role": "user", "parts": [{"text": ${PROMPT@Q}}]}] }
JSON
) | jq
```

**examples/curl-openai.sh** (against proxy)
```bash
#!/usr/bin/env bash
set -euo pipefail
PROMPT=${1:-"Hello from proxy"}

curl -sS http://localhost:4000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer dev_master_key_please_change' \
  -d @<(cat <<JSON
{ "model": "gpt-4o", "messages": [{"role":"user","content": ${PROMPT@Q}}] }
JSON
) | jq -r '.choices[0].message.content'
```

---

## 7) Simon Willison `llm` CLI (optional)

Install & add an OpenAI-compatible provider pointing at the proxy:

**examples/llm-config.md**
```bash
pipx install llm
llm keys set openai     # paste ANY string; not used, proxy master key below
llm keys set openai:base_url http://localhost:4000/v1
llm keys set openai:api_key dev_master_key_please_change

# Use: llm -m gpt-4o "hello"
# Switch: llm -m claude-3.7 "rewrite this"
```

---

## 8) Observability & spend

- Requests & latency logged to `./logs/requests.log` and SQLite `./logs/litellm.db`.
- Quick peek (from container):
  ```bash
  docker exec -it litellm sqlite3 /app/logs/litellm.db \
    'select datetime(timestamp, "unixepoch"), model, prompt_tokens, completion_tokens, total_cost from requests order by timestamp desc limit 20;'
  ```

Tips:
- Use `response_format: {type: "json_object"}` for tool-friendly outputs.
- Set `temperature` low (0–0.3) for coding/tasks; raise for ideation.
- Add `router_settings.default_fallbacks` for each favorite model.

---

## 9) Security notes

- The proxy is local only (binds to 0.0.0.0 → your machine). Do not expose 4000 publicly.
- Rotate `general_settings.master_key` if you ever share your machine.
- Keep `.env` out of version control.

---

## 10) Quick start checklist

1. `cp .env.example .env` and paste keys.
2. `docker compose up -d` (or run `litellm` directly)
3. `chmod +x bin/*`
4. `bin/ask "Who are you?"`
5. `MODEL=ollama-llama3.1-8b bin/ask "Draft 3 headlines"`
6. (Optional) `pipx install llm` and point it at `http://localhost:4000/v1`.

You now have one CLI and one URL for every model. Enjoy.

