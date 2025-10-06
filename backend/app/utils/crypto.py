"""
Encryption utilities for sensitive data (GitHub tokens, API keys)
"""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from app.config import settings


class TokenEncryption:
    """Encrypt and decrypt sensitive tokens using Fernet symmetric encryption"""

    def __init__(self):
        # Use PBKDF2 to derive a proper encryption key from SECRET_KEY
        # This is cryptographically secure regardless of SECRET_KEY length
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=settings.ENCRYPTION_SALT.encode(),
            iterations=100000,
            backend=default_backend()
        )

        # Derive key from SECRET_KEY
        key = kdf.derive(settings.SECRET_KEY.encode())

        # Create base64-encoded key for Fernet (44 chars)
        fernet_key = base64.urlsafe_b64encode(key)

        self.cipher = Fernet(fernet_key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string"""
        if not plaintext:
            return ""
        
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string"""
        if not ciphertext:
            return ""
        
        try:
            decrypted_bytes = self.cipher.decrypt(ciphertext.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt token: {e}")


# Singleton
_token_encryption = None

def get_token_encryption() -> TokenEncryption:
    """Get singleton TokenEncryption instance"""
    global _token_encryption
    if _token_encryption is None:
        _token_encryption = TokenEncryption()
    return _token_encryption

def encrypt_token(token: str) -> str:
    """Encrypt a token"""
    if not settings.ENCRYPT_TOKENS:
        return token
    return get_token_encryption().encrypt(token)

def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a token"""
    if not settings.ENCRYPT_TOKENS:
        return encrypted_token
    return get_token_encryption().decrypt(encrypted_token)
