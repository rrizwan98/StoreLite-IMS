"""
User MCP Connectors Module

This module handles user-managed MCP server connections, including:
- Connector CRUD operations (manager.py)
- Connection validation (validator.py)
- MCP client for external servers (mcp_client.py)
- Credential encryption (encryption.py)
"""

from .encryption import encrypt_credentials, decrypt_credentials, CredentialEncryptionError
from .mcp_client import UserMCPClient, ValidationResult
from .validator import validate_mcp_connection

# These will be imported as they're implemented:
# from .manager import ConnectorManager

__all__ = [
    "encrypt_credentials",
    "decrypt_credentials",
    "CredentialEncryptionError",
    "UserMCPClient",
    "ValidationResult",
    "validate_mcp_connection",
]
