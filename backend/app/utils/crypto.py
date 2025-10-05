"""
Encryption utilities for sensitive data (GitHub tokens, API keys)
"""

from cryptography.fernet import Fernet
from app.config import settings


class TokenEncryption:
    """Encrypt and decrypt sensitive tokens using Fernet symmetric encryption"""
    
    def __init__(self):
        # Get key from settings - must be 32 url-safe base64-encoded bytes
        # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        key_bytes = settings.SECRET_KEY.encode()[:32].ljust(32, b'=')
        
        # Create base64-encoded key for Fernet (44 chars)
        import base64
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        
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
