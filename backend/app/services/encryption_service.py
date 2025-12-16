"""
Encryption service for securing OAuth2 tokens in database.
Uses Fernet symmetric encryption (AES-128-CBC).
"""

import os
import logging
from cryptography.fernet import Fernet, InvalidToken
from typing import Optional

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Raised when encryption/decryption fails"""
    pass


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data like OAuth tokens.
    Uses Fernet (AES-128-CBC with HMAC).
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption service with key from env or parameter.

        Args:
            encryption_key: Optional base64-encoded 32-byte key.
                          If not provided, reads from TOKEN_ENCRYPTION_KEY env var.
        """
        self._key = encryption_key or os.getenv("TOKEN_ENCRYPTION_KEY")

        if not self._key:
            logger.warning(
                "TOKEN_ENCRYPTION_KEY not set. Generating temporary key. "
                "This is NOT safe for production - tokens will be unrecoverable after restart!"
            )
            self._key = Fernet.generate_key().decode()

        try:
            self._fernet = Fernet(self._key.encode() if isinstance(self._key, str) else self._key)
        except Exception as e:
            logger.error(f"Failed to initialize Fernet with provided key: {e}")
            raise EncryptionError(
                "Invalid encryption key. Ensure TOKEN_ENCRYPTION_KEY is a valid Fernet key. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt

        Returns:
            Base64-encoded encrypted string

        Raises:
            EncryptionError: If encryption fails
        """
        if not plaintext:
            return ""

        try:
            encrypted = self._fernet.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt data: {e}")

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            EncryptionError: If decryption fails (invalid key or corrupted data)
        """
        if not ciphertext:
            return ""

        try:
            decrypted = self._fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except InvalidToken:
            logger.error("Decryption failed: Invalid token (wrong key or corrupted data)")
            raise EncryptionError(
                "Failed to decrypt data. The encryption key may have changed or data is corrupted."
            )
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Failed to decrypt data: {e}")

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key.

        Returns:
            Base64-encoded 32-byte key suitable for TOKEN_ENCRYPTION_KEY env var
        """
        return Fernet.generate_key().decode()


# Singleton instance for use across the application
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """
    Get the singleton encryption service instance.

    Returns:
        EncryptionService instance
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def encrypt_token(token: str) -> str:
    """
    Convenience function to encrypt a token.

    Args:
        token: The token string to encrypt

    Returns:
        Encrypted token string
    """
    return get_encryption_service().encrypt(token)


def decrypt_token(encrypted_token: str) -> str:
    """
    Convenience function to decrypt a token.

    Args:
        encrypted_token: The encrypted token string

    Returns:
        Decrypted token string
    """
    return get_encryption_service().decrypt(encrypted_token)
