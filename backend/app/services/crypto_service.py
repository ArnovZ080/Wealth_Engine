"""
Crypto Service — Fernet symmetric encryption for API credentials.
"""

from cryptography.fernet import Fernet
from app.config import get_settings

settings = get_settings()

class CryptoService:
    """
    Encrypts and decrypts sensitive strings using a master key.
    """
    def __init__(self, key: str | None = None):
        # Fallback to a hardcoded key if env not provided (for dev only, will warn)
        self.key = key or settings.credential_encryption_key
        if not self.key:
            # Note: In production, this MUST be set.
            raise ValueError("CREDENTIAL_ENCRYPTION_KEY not set in environment.")
        self.fernet = Fernet(self.key.encode())

    def encrypt(self, plaintext: str) -> str:
        """Encrypts plaintext to a base64 string."""
        if not plaintext:
            return ""
        return self.fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypts a base64 ciphertext string."""
        if not ciphertext:
            return ""
        return self.fernet.decrypt(ciphertext.encode()).decode()

# Global singleton
_crypto_service = None

def get_crypto_service() -> CryptoService:
    global _crypto_service
    if _crypto_service is None:
        _crypto_service = CryptoService()
    return _crypto_service

def encrypt(plaintext: str) -> str:
    return get_crypto_service().encrypt(plaintext)

def decrypt(ciphertext: str) -> str:
    return get_crypto_service().decrypt(ciphertext)
