#!/bin/bash

# LLM CLI Setup Script for Dev-workflow
# This configures Simon Willison's llm CLI to use your local LiteLLM proxy

echo "🔧 Configuring Simon Willison's llm CLI for Dev-workflow..."

# Set the OpenAI key (dummy value, proxy handles real auth)
echo "dummy-key-proxy-handles-auth" | /Users/danielconnolly/.local/bin/llm keys set openai

# Configure the base URL to point to local proxy
/Users/danielconnolly/.local/bin/llm keys set openai:base_url http://localhost:4000/v1
/Users/danielconnolly/.local/bin/llm keys set openai:api_key dev_master_key_please_change

# Create useful aliases for all models
echo "📝 Creating model aliases..."

# OpenAI Models
/Users/danielconnolly/.local/bin/llm aliases set gpt5 openai/gpt-5
/Users/danielconnolly/.local/bin/llm aliases set gpt4o openai/gpt-4o
/Users/danielconnolly/.local/bin/llm aliases set o3 openai/o3
/Users/danielconnolly/.local/bin/llm aliases set o4mini openai/o4-mini

# Anthropic Models  
/Users/danielconnolly/.local/bin/llm aliases set opus openai/claude-opus-4.1
/Users/danielconnolly/.local/bin/llm aliases set sonnet openai/claude-sonnet-4
/Users/danielconnolly/.local/bin/llm aliases set claude openai/claude-3.5-sonnet
/Users/danielconnolly/.local/bin/llm aliases set haiku openai/claude-3.5-haiku

# Google Models
/Users/danielconnolly/.local/bin/llm aliases set gemini openai/gemini-2.5-pro
/Users/danielconnolly/.local/bin/llm aliases set flash openai/gemini-2.5-flash

# Groq Models
/Users/danielconnolly/.local/bin/llm aliases set groq openai/groq-llama3.1-70b
/Users/danielconnolly/.local/bin/llm aliases set fast openai/groq-llama3.1-8b

# Local Models
/Users/danielconnolly/.local/bin/llm aliases set local openai/ollama-llama3.1-8b

echo "✅ Configuration complete!"
echo ""
echo "📚 Usage examples:"
echo "  llm -m gpt5 'Your question'"
echo "  llm -m opus 'Complex task'"
echo "  llm -m fast 'Quick response'"
echo "  llm -m local 'Private query'"
echo ""
echo "💡 Tip: Add /Users/danielconnolly/.local/bin to your PATH:"
echo "  export PATH=\"\$PATH:/Users/danielconnolly/.local/bin\""
