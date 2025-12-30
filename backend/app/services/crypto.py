"""Encryption utilities for storing API keys securely."""

import os
from pathlib import Path

from cryptography.fernet import Fernet

# Default key path - can be overridden via env var
DEFAULT_KEY_PATH = Path.home() / ".commandcenter" / "secret.key"


def get_key_path() -> Path:
    """Get the path to the secret key file."""
    env_path = os.environ.get("COMMANDCENTER_KEY_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_KEY_PATH


def get_or_create_secret_key() -> str:
    """Get existing secret key or create a new one."""
    key_path = get_key_path()

    if key_path.exists():
        return key_path.read_text().strip()

    # Create directory if needed
    key_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate new key
    key = Fernet.generate_key().decode()
    key_path.write_text(key)

    # Secure permissions (owner read/write only)
    key_path.chmod(0o600)

    return key


def get_fernet() -> Fernet:
    """Get Fernet instance with the secret key."""
    key = get_or_create_secret_key()
    return Fernet(key.encode())


def encrypt_key(plaintext: str) -> str:
    """Encrypt an API key for storage."""
    if not plaintext:
        return ""
    f = get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_key(ciphertext: str) -> str:
    """Decrypt a stored API key."""
    if not ciphertext:
        return ""
    f = get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


def mask_key(key: str) -> str:
    """Mask an API key for display (show first 7 and last 4 chars)."""
    if not key or len(key) < 12:
        return "***"
    return f"{key[:7]}***{key[-4:]}"
