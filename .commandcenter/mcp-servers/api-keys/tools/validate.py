"""
API Key validation tools
"""

from typing import Dict, Any, Optional
import requests
from datetime import datetime

from .storage import get_storage
from ..config import load_routing_config


class APIKeyValidator:
    """Validate API keys for various providers"""

    def __init__(self):
        self.storage = get_storage()
        self.routing_config = load_routing_config()

    def validate_anthropic_key(self, api_key: str) -> tuple[bool, str]:
        """
        Validate Anthropic API key by making a test request

        Args:
            api_key: API key to validate

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Try to list models as a validation
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
            # Note: This is a lightweight check - we're not actually calling the API
            # In production, you might want to make a minimal API call
            if not api_key.startswith("sk-ant-"):
                return False, "Invalid Anthropic API key format (must start with 'sk-ant-')"

            # Basic format validation
            if len(api_key) < 40:
                return False, "API key appears too short"

            return True, "API key format is valid (actual validation requires API call)"
        except Exception as e:
            return False, f"Validation failed: {str(e)}"

    def validate_openai_key(self, api_key: str) -> tuple[bool, str]:
        """
        Validate OpenAI API key

        Args:
            api_key: API key to validate

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not api_key.startswith("sk-"):
                return False, "Invalid OpenAI API key format (must start with 'sk-')"

            if len(api_key) < 40:
                return False, "API key appears too short"

            return True, "API key format is valid (actual validation requires API call)"
        except Exception as e:
            return False, f"Validation failed: {str(e)}"

    def validate_google_key(self, api_key: str) -> tuple[bool, str]:
        """
        Validate Google API key

        Args:
            api_key: API key to validate

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if len(api_key) < 20:
                return False, "API key appears too short"

            return True, "API key format is valid (actual validation requires API call)"
        except Exception as e:
            return False, f"Validation failed: {str(e)}"

    def validate_local_endpoint(self, endpoint: str) -> tuple[bool, str]:
        """
        Validate local Ollama endpoint

        Args:
            endpoint: Endpoint URL

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Try to connect to the endpoint
            response = requests.get(f"{endpoint}/api/tags", timeout=2)
            if response.status_code == 200:
                return True, "Local endpoint is reachable"
            else:
                return False, f"Endpoint returned status code {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"Cannot reach endpoint: {str(e)}"

    def validate_key(self, provider: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate an API key for a provider

        Args:
            provider: Provider name
            api_key: API key to validate (if None, validates stored key)

        Returns:
            Validation result
        """
        # If no key provided, get from storage
        if api_key is None:
            api_key = self.storage.get_key(provider)
            if not api_key:
                return {
                    "success": False,
                    "error": f"No API key found for {provider}",
                    "provider": provider
                }

        # Validate based on provider
        validators = {
            "anthropic": self.validate_anthropic_key,
            "openai": self.validate_openai_key,
            "google": self.validate_google_key
        }

        if provider == "local":
            # For local, validate endpoint instead
            endpoint = self.routing_config["providers"]["local"].get("endpoint", "http://localhost:11434")
            is_valid, message = self.validate_local_endpoint(endpoint)
        elif provider in validators:
            is_valid, message = validators[provider](api_key)
        else:
            return {
                "success": False,
                "error": f"Unknown provider: {provider}",
                "provider": provider
            }

        return {
            "success": True,
            "provider": provider,
            "is_valid": is_valid,
            "message": message,
            "validated_at": datetime.utcnow().isoformat()
        }

    def validate_all_keys(self) -> Dict[str, Any]:
        """
        Validate all stored API keys

        Returns:
            Validation results for all providers
        """
        providers = self.storage.list_providers()
        results = []

        for provider in providers:
            result = self.validate_key(provider)
            results.append(result)

        # Also check local endpoint if enabled
        if self.routing_config["providers"]["local"].get("enabled", False):
            local_result = self.validate_key("local")
            results.append(local_result)

        valid_count = sum(1 for r in results if r.get("is_valid", False))

        return {
            "success": True,
            "total_providers": len(results),
            "valid_providers": valid_count,
            "invalid_providers": len(results) - valid_count,
            "results": results
        }

    def check_key_expiration(self, provider: str) -> Dict[str, Any]:
        """
        Check if a provider's key is expired

        Args:
            provider: Provider name

        Returns:
            Expiration status
        """
        metadata = self.storage.get_metadata(provider)
        if not metadata:
            return {
                "success": False,
                "error": f"No key found for {provider}"
            }

        expiration_date = metadata.get("expiration_date")
        if not expiration_date:
            return {
                "success": True,
                "provider": provider,
                "has_expiration": False,
                "is_expired": False
            }

        try:
            exp_date = datetime.fromisoformat(expiration_date)
            is_expired = datetime.utcnow() > exp_date
            days_until_expiration = (exp_date - datetime.utcnow()).days

            return {
                "success": True,
                "provider": provider,
                "has_expiration": True,
                "is_expired": is_expired,
                "expiration_date": expiration_date,
                "days_until_expiration": days_until_expiration
            }
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid expiration date format: {expiration_date}"
            }

    def check_all_expirations(self) -> Dict[str, Any]:
        """
        Check expiration status for all keys

        Returns:
            Expiration status for all providers
        """
        providers = self.storage.list_providers()
        results = []

        for provider in providers:
            result = self.check_key_expiration(provider)
            results.append(result)

        expired_count = sum(1 for r in results if r.get("is_expired", False))

        return {
            "success": True,
            "total_providers": len(results),
            "expired_count": expired_count,
            "results": results
        }


# Singleton
_validator = None


def get_validator() -> APIKeyValidator:
    """Get singleton validator instance"""
    global _validator
    if _validator is None:
        _validator = APIKeyValidator()
    return _validator
