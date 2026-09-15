"""
Token encryption service — Phase 5.

GitHub PATs are encrypted at rest using Fernet symmetric encryption.
The FERNET_KEY setting must be a valid URL-safe base64-encoded 32-byte key.

Per NFR-001 and security.md:
- Tokens are NEVER logged.
- Tokens are NEVER returned in API responses.
- Tokens are decrypted in-process only when needed for a GitHub API call.

To generate a valid key:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
from cryptography.fernet import Fernet, InvalidToken
from backend.app.core.config import settings


def _get_fernet() -> Fernet:
    """Return a Fernet instance using the configured key."""
    key = settings.FERNET_KEY
    if not key or key == "YOUR_FERNET_KEY":
        raise RuntimeError(
            "FERNET_KEY is not configured. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(plaintext_token: str) -> str:
    """
    Encrypt a GitHub PAT for at-rest storage.
    Returns URL-safe base64-encoded ciphertext as a string.
    """
    fernet = _get_fernet()
    return fernet.encrypt(plaintext_token.encode("utf-8")).decode("utf-8")


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a stored encrypted PAT.
    Raises InvalidToken if the ciphertext is tampered or the key is wrong.
    """
    fernet = _get_fernet()
    try:
        return fernet.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        raise ValueError("Cannot decrypt GitHub token — key mismatch or corrupted token")
