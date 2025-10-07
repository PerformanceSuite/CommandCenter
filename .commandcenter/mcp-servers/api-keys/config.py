"""
Configuration for API Key Manager MCP Server
"""

import os
from pathlib import Path
from typing import Dict, Any
import json

# Base directory for API Key Manager
BASE_DIR = Path(__file__).parent

# Storage paths
KEYS_FILE = BASE_DIR / ".keys.enc"
USAGE_FILE = BASE_DIR / "usage.json"
ROUTING_CONFIG_FILE = BASE_DIR / "routing_config.json"

# Encryption settings (uses backend crypto utils)
ENCRYPT_KEYS = os.getenv("ENCRYPT_API_KEYS", "true").lower() == "true"

# Default routing configuration
DEFAULT_ROUTING_CONFIG = {
    "providers": {
        "anthropic": {
            "enabled": True,
            "api_key_env": "ANTHROPIC_API_KEY",
            "models": [
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ],
            "rate_limit": 100,
            "cost_per_1k_input_tokens": 0.003,
            "cost_per_1k_output_tokens": 0.015,
            "max_tokens": 200000
        },
        "openai": {
            "enabled": True,
            "api_key_env": "OPENAI_API_KEY",
            "models": [
                "gpt-4-turbo-preview",
                "gpt-4",
                "gpt-3.5-turbo"
            ],
            "rate_limit": 60,
            "cost_per_1k_input_tokens": 0.01,
            "cost_per_1k_output_tokens": 0.03,
            "max_tokens": 128000
        },
        "google": {
            "enabled": False,
            "api_key_env": "GOOGLE_API_KEY",
            "models": [
                "gemini-pro",
                "gemini-pro-vision"
            ],
            "rate_limit": 60,
            "cost_per_1k_input_tokens": 0.0005,
            "cost_per_1k_output_tokens": 0.0015,
            "max_tokens": 32000
        },
        "local": {
            "enabled": True,
            "endpoint": "http://localhost:11434",
            "models": [
                "codellama:13b",
                "mistral:7b",
                "llama2:13b"
            ],
            "cost_per_1k_input_tokens": 0.0,
            "cost_per_1k_output_tokens": 0.0,
            "max_tokens": 4096
        }
    },
    "routing": {
        "code_generation": "anthropic",
        "code_review": "anthropic",
        "embeddings": "local",
        "analysis": "openai",
        "chat": "anthropic",
        "summarization": "anthropic",
        "data_extraction": "openai"
    },
    "fallback_order": ["anthropic", "openai", "google", "local"],
    "budget": {
        "enabled": True,
        "daily_limit": 10.0,
        "monthly_limit": 100.0,
        "alert_threshold": 0.8
    }
}

# Default usage tracking structure
DEFAULT_USAGE_STATS = {
    "providers": {},
    "total_requests": 0,
    "total_input_tokens": 0,
    "total_output_tokens": 0,
    "total_cost": 0.0,
    "last_reset": None,
    "daily_stats": {},
    "monthly_stats": {}
}


def load_routing_config() -> Dict[str, Any]:
    """Load routing configuration from file or create default"""
    if ROUTING_CONFIG_FILE.exists():
        with open(ROUTING_CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        save_routing_config(DEFAULT_ROUTING_CONFIG)
        return DEFAULT_ROUTING_CONFIG


def save_routing_config(config: Dict[str, Any]) -> None:
    """Save routing configuration to file"""
    with open(ROUTING_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def load_usage_stats() -> Dict[str, Any]:
    """Load usage statistics from file or create default"""
    if USAGE_FILE.exists():
        with open(USAGE_FILE, 'r') as f:
            return json.load(f)
    else:
        save_usage_stats(DEFAULT_USAGE_STATS)
        return DEFAULT_USAGE_STATS


def save_usage_stats(stats: Dict[str, Any]) -> None:
    """Save usage statistics to file"""
    with open(USAGE_FILE, 'w') as f:
        json.dump(stats, f, indent=2)


def ensure_files_exist() -> None:
    """Ensure all required files exist"""
    if not ROUTING_CONFIG_FILE.exists():
        save_routing_config(DEFAULT_ROUTING_CONFIG)

    if not USAGE_FILE.exists():
        save_usage_stats(DEFAULT_USAGE_STATS)

    if not KEYS_FILE.exists():
        # Create empty encrypted keys file
        KEYS_FILE.touch(mode=0o600)  # Restricted permissions
