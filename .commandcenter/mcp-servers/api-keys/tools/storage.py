"""
Secure API key storage with encryption
Uses backend crypto utilities for encryption
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

# Add backend to path to access crypto utils
BACKEND_PATH = Path(__file__).parent.parent.parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND_PATH))

try:
    from app.utils.crypto import encrypt_token, decrypt_token
    CRYPTO_AVAILABLE = True
except ImportError:
    # Fallback if backend not available (for testing)
    CRYPTO_AVAILABLE = False
    print("Warning: Backend crypto utilities not available. Using plaintext storage.")

from ..config import KEYS_FILE, ENCRYPT_KEYS


class APIKeyStorage:
    """Secure storage for API keys with encryption"""

    def __init__(self):
        self.keys_file = KEYS_FILE
        self.keys_data: Dict[str, Any] = self._load_keys()

    def _load_keys(self) -> Dict[str, Any]:
        """Load encrypted keys from file"""
        if not self.keys_file.exists():
            return {
                "keys": {},
                "metadata": {},
                "audit_log": []
            }

        try:
            with open(self.keys_file, 'r') as f:
                content = f.read()
                if not content.strip():
                    return {
                        "keys": {},
                        "metadata": {},
                        "audit_log": []
                    }
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                "keys": {},
                "metadata": {},
                "audit_log": []
            }

    def _save_keys(self) -> None:
        """Save encrypted keys to file"""
        self.keys_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.keys_file, 'w') as f:
            json.dump(self.keys_data, f, indent=2)
        # Set restrictive permissions
        os.chmod(self.keys_file, 0o600)

    def _log_access(self, action: str, provider: str, details: str = "") -> None:
        """Log key access for audit trail"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "provider": provider,
            "details": details
        }
        self.keys_data["audit_log"].append(log_entry)

        # Keep only last 100 log entries
        if len(self.keys_data["audit_log"]) > 100:
            self.keys_data["audit_log"] = self.keys_data["audit_log"][-100:]

        self._save_keys()

    def add_key(self, provider: str, api_key: str, metadata: Optional[Dict] = None) -> bool:
        """
        Add or update an API key for a provider

        Args:
            provider: Provider name (e.g., 'anthropic', 'openai')
            api_key: The API key to store
            metadata: Optional metadata (expiration, description, etc.)

        Returns:
            True if successful
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        # Encrypt the key if crypto is available and enabled
        encrypted_key = api_key
        if CRYPTO_AVAILABLE and ENCRYPT_KEYS:
            try:
                encrypted_key = encrypt_token(api_key)
            except Exception as e:
                raise ValueError(f"Failed to encrypt API key: {e}")

        # Store encrypted key
        self.keys_data["keys"][provider] = encrypted_key

        # Store metadata
        if metadata is None:
            metadata = {}
        metadata.update({
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "encrypted": CRYPTO_AVAILABLE and ENCRYPT_KEYS
        })
        self.keys_data["metadata"][provider] = metadata

        # Log the action
        self._log_access("add_key", provider, "Key added successfully")

        # Save to file
        self._save_keys()

        return True

    def get_key(self, provider: str) -> Optional[str]:
        """
        Retrieve and decrypt an API key for a provider

        Args:
            provider: Provider name

        Returns:
            Decrypted API key or None if not found
        """
        encrypted_key = self.keys_data["keys"].get(provider)
        if not encrypted_key:
            return None

        # Decrypt the key if it was encrypted
        metadata = self.keys_data["metadata"].get(provider, {})
        if metadata.get("encrypted", False) and CRYPTO_AVAILABLE and ENCRYPT_KEYS:
            try:
                decrypted_key = decrypt_token(encrypted_key)
                # Log access (but not the key itself!)
                self._log_access("get_key", provider, "Key retrieved")
                return decrypted_key
            except Exception as e:
                self._log_access("get_key_error", provider, f"Decryption failed: {str(e)}")
                raise ValueError(f"Failed to decrypt API key for {provider}: {e}")

        # Log access
        self._log_access("get_key", provider, "Key retrieved (plaintext)")
        return encrypted_key

    def remove_key(self, provider: str) -> bool:
        """
        Remove an API key for a provider

        Args:
            provider: Provider name

        Returns:
            True if successful, False if key didn't exist
        """
        if provider in self.keys_data["keys"]:
            del self.keys_data["keys"][provider]
            if provider in self.keys_data["metadata"]:
                del self.keys_data["metadata"][provider]

            self._log_access("remove_key", provider, "Key removed")
            self._save_keys()
            return True
        return False

    def rotate_key(self, provider: str, new_api_key: str) -> bool:
        """
        Rotate an API key (backup old, add new)

        Args:
            provider: Provider name
            new_api_key: New API key

        Returns:
            True if successful
        """
        # Get old metadata
        old_metadata = self.keys_data["metadata"].get(provider, {}).copy()

        # Add rotation info to metadata
        rotation_metadata = {
            "rotated_at": datetime.utcnow().isoformat(),
            "rotation_count": old_metadata.get("rotation_count", 0) + 1,
            "previous_created_at": old_metadata.get("created_at")
        }

        # Add new key with rotation metadata
        return self.add_key(provider, new_api_key, rotation_metadata)

    def list_providers(self) -> list:
        """List all providers with stored keys"""
        return list(self.keys_data["keys"].keys())

    def get_metadata(self, provider: str) -> Optional[Dict]:
        """Get metadata for a provider's key"""
        return self.keys_data["metadata"].get(provider)

    def get_audit_log(self, provider: Optional[str] = None, limit: int = 50) -> list:
        """
        Get audit log entries

        Args:
            provider: Filter by provider (None for all)
            limit: Maximum number of entries to return

        Returns:
            List of audit log entries
        """
        logs = self.keys_data["audit_log"]

        if provider:
            logs = [log for log in logs if log.get("provider") == provider]

        return logs[-limit:]

    def validate_key_format(self, provider: str, api_key: str) -> tuple[bool, str]:
        """
        Validate API key format for a provider

        Args:
            provider: Provider name
            api_key: API key to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Provider-specific validation
        validators = {
            "anthropic": lambda k: (
                k.startswith("sk-ant-"),
                "Anthropic keys must start with 'sk-ant-'"
            ),
            "openai": lambda k: (
                k.startswith("sk-"),
                "OpenAI keys must start with 'sk-'"
            ),
            "google": lambda k: (
                len(k) > 20,  # Basic length check
                "Google API keys must be at least 20 characters"
            ),
        }

        validator = validators.get(provider)
        if validator:
            is_valid, error_msg = validator(api_key)
            if not is_valid:
                return False, error_msg

        # Generic validation
        if len(api_key) < 10:
            return False, "API key is too short"

        return True, ""


# Singleton instance
_storage = None


def get_storage() -> APIKeyStorage:
    """Get singleton storage instance"""
    global _storage
    if _storage is None:
        _storage = APIKeyStorage()
    return _storage
