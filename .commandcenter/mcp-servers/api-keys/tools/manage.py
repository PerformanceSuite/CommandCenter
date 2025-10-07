"""
API Key management tools for MCP
"""

from typing import Dict, Any, Optional
from datetime import datetime
import os

from .storage import get_storage, APIKeyStorage
from ..config import load_routing_config, save_routing_config


class APIKeyManager:
    """High-level API key management"""

    def __init__(self):
        self.storage: APIKeyStorage = get_storage()
        self.routing_config = load_routing_config()

    def add_key(
        self,
        provider: str,
        api_key: Optional[str] = None,
        env_var: Optional[str] = None,
        description: str = "",
        expiration_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add an API key for a provider

        Args:
            provider: Provider name (anthropic, openai, google, local)
            api_key: API key to store (if not using env_var)
            env_var: Environment variable name containing the key
            description: Optional description
            expiration_date: Optional expiration date (ISO format)

        Returns:
            Result dictionary with success status and message
        """
        # Validate provider
        if provider not in self.routing_config["providers"]:
            return {
                "success": False,
                "error": f"Unknown provider: {provider}. Valid providers: {list(self.routing_config['providers'].keys())}"
            }

        # Get key from env_var if specified
        if env_var:
            api_key = os.getenv(env_var)
            if not api_key:
                return {
                    "success": False,
                    "error": f"Environment variable {env_var} not found or empty"
                }

        if not api_key:
            return {
                "success": False,
                "error": "Either api_key or env_var must be provided"
            }

        # Validate key format
        is_valid, error_msg = self.storage.validate_key_format(provider, api_key)
        if not is_valid:
            return {
                "success": False,
                "error": f"Invalid API key format: {error_msg}"
            }

        # Prepare metadata
        metadata = {
            "description": description,
            "env_var": env_var,
        }
        if expiration_date:
            metadata["expiration_date"] = expiration_date

        # Store the key
        try:
            self.storage.add_key(provider, api_key, metadata)
            return {
                "success": True,
                "message": f"API key for {provider} added successfully",
                "provider": provider,
                "encrypted": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to add API key: {str(e)}"
            }

    def remove_key(self, provider: str) -> Dict[str, Any]:
        """
        Remove an API key for a provider

        Args:
            provider: Provider name

        Returns:
            Result dictionary
        """
        success = self.storage.remove_key(provider)
        if success:
            return {
                "success": True,
                "message": f"API key for {provider} removed successfully",
                "provider": provider
            }
        else:
            return {
                "success": False,
                "error": f"No API key found for {provider}"
            }

    def rotate_key(
        self,
        provider: str,
        new_api_key: Optional[str] = None,
        env_var: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rotate an API key for a provider

        Args:
            provider: Provider name
            new_api_key: New API key
            env_var: Environment variable with new key

        Returns:
            Result dictionary
        """
        # Get new key from env_var if specified
        if env_var:
            new_api_key = os.getenv(env_var)
            if not new_api_key:
                return {
                    "success": False,
                    "error": f"Environment variable {env_var} not found or empty"
                }

        if not new_api_key:
            return {
                "success": False,
                "error": "Either new_api_key or env_var must be provided"
            }

        # Validate key format
        is_valid, error_msg = self.storage.validate_key_format(provider, new_api_key)
        if not is_valid:
            return {
                "success": False,
                "error": f"Invalid API key format: {error_msg}"
            }

        try:
            self.storage.rotate_key(provider, new_api_key)
            return {
                "success": True,
                "message": f"API key for {provider} rotated successfully",
                "provider": provider
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to rotate API key: {str(e)}"
            }

    def list_keys(self, include_metadata: bool = True) -> Dict[str, Any]:
        """
        List all stored API keys (without revealing actual keys)

        Args:
            include_metadata: Include metadata in response

        Returns:
            Dictionary with provider information
        """
        providers = self.storage.list_providers()
        result = {
            "providers": [],
            "total_count": len(providers)
        }

        for provider in providers:
            provider_info = {
                "name": provider,
                "has_key": True,
                "enabled": self.routing_config["providers"].get(provider, {}).get("enabled", False)
            }

            if include_metadata:
                metadata = self.storage.get_metadata(provider)
                if metadata:
                    provider_info["metadata"] = {
                        k: v for k, v in metadata.items()
                        if k not in ["encrypted"]  # Don't expose encryption details
                    }

            result["providers"].append(provider_info)

        return result

    def get_key_info(self, provider: str) -> Dict[str, Any]:
        """
        Get information about a specific provider's key

        Args:
            provider: Provider name

        Returns:
            Provider key information
        """
        if provider not in self.storage.list_providers():
            return {
                "success": False,
                "error": f"No API key found for {provider}"
            }

        metadata = self.storage.get_metadata(provider)
        config = self.routing_config["providers"].get(provider, {})

        return {
            "success": True,
            "provider": provider,
            "enabled": config.get("enabled", False),
            "models": config.get("models", []),
            "metadata": metadata or {},
            "has_key": True
        }

    def update_provider_config(
        self,
        provider: str,
        enabled: Optional[bool] = None,
        models: Optional[list] = None,
        rate_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update provider configuration

        Args:
            provider: Provider name
            enabled: Enable/disable provider
            models: List of models
            rate_limit: Rate limit

        Returns:
            Result dictionary
        """
        if provider not in self.routing_config["providers"]:
            return {
                "success": False,
                "error": f"Unknown provider: {provider}"
            }

        config = self.routing_config["providers"][provider]

        if enabled is not None:
            config["enabled"] = enabled

        if models is not None:
            config["models"] = models

        if rate_limit is not None:
            config["rate_limit"] = rate_limit

        save_routing_config(self.routing_config)

        return {
            "success": True,
            "message": f"Configuration for {provider} updated successfully",
            "provider": provider,
            "config": config
        }

    def get_audit_log(
        self,
        provider: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get audit log for key access

        Args:
            provider: Filter by provider (None for all)
            limit: Maximum entries to return

        Returns:
            Audit log entries
        """
        logs = self.storage.get_audit_log(provider, limit)

        return {
            "success": True,
            "entries": logs,
            "count": len(logs),
            "provider_filter": provider
        }


# Singleton
_manager = None


def get_manager() -> APIKeyManager:
    """Get singleton manager instance"""
    global _manager
    if _manager is None:
        _manager = APIKeyManager()
    return _manager
