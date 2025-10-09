# LLM CLI Configuration

Install & add an OpenAI-compatible provider pointing at the proxy:

```bash
pipx install llm
llm keys set openai     # paste ANY string; not used, proxy master key below
llm keys set openai:base_url http://localhost:4000/v1
llm keys set openai:api_key dev_master_key_please_change

# Use: llm -m gpt-4o "hello"
# Switch: llm -m claude-3.7 "rewrite this"
```
