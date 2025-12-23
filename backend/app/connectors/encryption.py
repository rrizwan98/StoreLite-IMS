"""
Credential encryption module for User MCP Connectors.

This module wraps the existing EncryptionService to provide dict-based
encryption for MCP connector credentials.

Uses Fernet (AES-128-CBC with HMAC) via the existing encryption_service.
"""

import json
import logging
from typing import Dict, Any

from app.services.encryption_service import (
    encrypt_token,
    decrypt_token,
    EncryptionError,
)

logger = logging.getLogger(__name__)


class CredentialEncryptionError(Exception):
    """Raised when credential encryption/decryption fails"""
    pass


def encrypt_credentials(credentials: Dict[str, Any]) -> str:
    """
    Encrypt credentials dict to an encrypted string.

    Args:
        credentials: Dictionary of credentials (e.g., {"oauth_token": "...", "api_key": "..."})

    Returns:
        Encrypted string (base64-encoded Fernet ciphertext)

    Raises:
        CredentialEncryptionError: If encryption fails
        TypeError: If credentials is not a dict

    Example:
        >>> encrypted = encrypt_credentials({"api_key": "sk-123"})
        >>> type(encrypted)
        <class 'str'>
    """
    if not isinstance(credentials, dict):
        raise TypeError(f"credentials must be a dict, got {type(credentials).__name__}")

    try:
        # Serialize dict to JSON string
        json_str = json.dumps(credentials, ensure_ascii=False)
    except TypeError as e:
        # Non-serializable data (e.g., lambda, custom objects)
        logger.error(f"Credentials contain non-serializable data: {e}")
        raise CredentialEncryptionError(f"Credentials contain non-serializable data: {e}")

    try:
        # Encrypt using existing service
        encrypted = encrypt_token(json_str)
        return encrypted
    except EncryptionError as e:
        logger.error(f"Failed to encrypt credentials: {e}")
        raise CredentialEncryptionError(f"Encryption failed: {e}")


def decrypt_credentials(encrypted: str) -> Dict[str, Any]:
    """
    Decrypt encrypted string back to credentials dict.

    Args:
        encrypted: Encrypted string (from encrypt_credentials)

    Returns:
        Dictionary of credentials

    Raises:
        CredentialEncryptionError: If decryption fails (invalid key, corrupted data, etc.)

    Example:
        >>> encrypted = encrypt_credentials({"api_key": "sk-123"})
        >>> decrypt_credentials(encrypted)
        {'api_key': 'sk-123'}
    """
    if not encrypted:
        raise CredentialEncryptionError("Empty encrypted data provided")

    try:
        # Decrypt using existing service
        json_str = decrypt_token(encrypted)
    except EncryptionError as e:
        logger.error(f"Failed to decrypt credentials: {e}")
        raise CredentialEncryptionError(f"Decryption failed: {e}")

    try:
        # Parse JSON back to dict
        credentials = json.loads(json_str)
        return credentials
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse decrypted credentials as JSON: {e}")
        raise CredentialEncryptionError(f"Invalid credential format: {e}")
