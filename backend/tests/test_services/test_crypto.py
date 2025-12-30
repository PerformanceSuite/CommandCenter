# backend/tests/test_services/test_crypto.py
from app.services.crypto import decrypt_key, encrypt_key, get_or_create_secret_key


def test_encrypt_decrypt_roundtrip():
    """Encrypted key can be decrypted back to original."""
    original = "sk-ant-api03-test-key-12345"
    encrypted = encrypt_key(original)
    decrypted = decrypt_key(encrypted)
    assert decrypted == original


def test_encrypted_differs_from_original():
    """Encrypted value is not the same as original."""
    original = "sk-ant-api03-test-key-12345"
    encrypted = encrypt_key(original)
    assert encrypted != original


def test_encrypt_empty_string():
    """Empty string encrypts and decrypts correctly."""
    encrypted = encrypt_key("")
    assert decrypt_key(encrypted) == ""


def test_get_or_create_secret_key_creates_file(tmp_path, monkeypatch):
    """Secret key file is created if it doesn't exist."""
    key_path = tmp_path / "secret.key"
    monkeypatch.setenv("COMMANDCENTER_KEY_PATH", str(key_path))

    key = get_or_create_secret_key()

    assert key_path.exists()
    assert len(key) == 44  # Fernet key is 44 chars base64
