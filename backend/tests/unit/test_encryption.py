"""
Unit tests for credential encryption module.

TDD Phase: RED - Write failing tests FIRST.

These tests define the expected behavior of the encryption module
before implementation exists. All tests should FAIL initially.
"""

import pytest
import os
import sys

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestCredentialEncryption:
    """Test AES-256 credential encryption using existing EncryptionService"""

    def test_encrypt_returns_non_empty_string(self):
        """Encryption should return a non-empty encrypted string"""
        from app.connectors.encryption import encrypt_credentials

        result = encrypt_credentials({"token": "secret"})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_encrypted_data_not_readable(self):
        """Encrypted data should not contain original values"""
        from app.connectors.encryption import encrypt_credentials

        plain = {"oauth_token": "my-secret-token-123", "api_key": "sk-abc123"}
        encrypted = encrypt_credentials(plain)

        # Original values should not be visible in encrypted output
        assert "my-secret-token-123" not in encrypted
        assert "oauth_token" not in encrypted
        assert "sk-abc123" not in encrypted
        assert "api_key" not in encrypted

    def test_decrypt_returns_original(self):
        """Decryption should return exact original data"""
        from app.connectors.encryption import encrypt_credentials, decrypt_credentials

        original = {
            "oauth_token": "secret-token",
            "refresh_token": "refresh-123",
            "api_key": "key-456"
        }
        encrypted = encrypt_credentials(original)
        decrypted = decrypt_credentials(encrypted)

        assert decrypted == original

    def test_different_inputs_produce_different_outputs(self):
        """Different inputs should produce different encrypted outputs"""
        from app.connectors.encryption import encrypt_credentials

        enc1 = encrypt_credentials({"a": "1"})
        enc2 = encrypt_credentials({"b": "2"})

        assert enc1 != enc2

    def test_same_input_produces_different_outputs(self):
        """Same input encrypted twice should produce different ciphertext (due to random IV)"""
        from app.connectors.encryption import encrypt_credentials

        data = {"token": "same-token"}
        enc1 = encrypt_credentials(data)
        enc2 = encrypt_credentials(data)

        # Fernet uses random IV, so same plaintext produces different ciphertext
        assert enc1 != enc2

    def test_invalid_encrypted_data_raises_error(self):
        """Invalid encrypted data should raise CredentialEncryptionError"""
        from app.connectors.encryption import decrypt_credentials, CredentialEncryptionError

        with pytest.raises(CredentialEncryptionError):
            decrypt_credentials("not-valid-encrypted-data")

    def test_empty_dict_encryption(self):
        """Empty dict should encrypt and decrypt successfully"""
        from app.connectors.encryption import encrypt_credentials, decrypt_credentials

        original = {}
        encrypted = encrypt_credentials(original)
        decrypted = decrypt_credentials(encrypted)

        assert decrypted == original

    def test_nested_dict_encryption(self):
        """Nested dict should encrypt and decrypt successfully"""
        from app.connectors.encryption import encrypt_credentials, decrypt_credentials

        original = {
            "oauth": {
                "access_token": "token-123",
                "refresh_token": "refresh-456",
                "scopes": ["read", "write"]
            },
            "settings": {
                "timeout": 30
            }
        }
        encrypted = encrypt_credentials(original)
        decrypted = decrypt_credentials(encrypted)

        assert decrypted == original

    def test_unicode_data_encryption(self):
        """Unicode data should encrypt and decrypt correctly"""
        from app.connectors.encryption import encrypt_credentials, decrypt_credentials

        original = {
            "name": "テスト",
            "description": "Тест 测试",
            "emoji": "🔐"
        }
        encrypted = encrypt_credentials(original)
        decrypted = decrypt_credentials(encrypted)

        assert decrypted == original

    def test_corrupted_ciphertext_raises_error(self):
        """Corrupted ciphertext should raise CredentialEncryptionError"""
        from app.connectors.encryption import encrypt_credentials, decrypt_credentials, CredentialEncryptionError

        encrypted = encrypt_credentials({"token": "secret"})
        # Corrupt the ciphertext
        corrupted = encrypted[:-5] + "XXXXX"

        with pytest.raises(CredentialEncryptionError):
            decrypt_credentials(corrupted)


class TestCredentialEncryptionEdgeCases:
    """Edge case tests for credential encryption"""

    def test_none_input_raises_error(self):
        """None input should raise TypeError or similar"""
        from app.connectors.encryption import encrypt_credentials

        with pytest.raises((TypeError, AttributeError)):
            encrypt_credentials(None)

    def test_non_serializable_raises_error(self):
        """Non-JSON-serializable input should raise error"""
        from app.connectors.encryption import encrypt_credentials, CredentialEncryptionError

        # Lambda is not JSON serializable
        with pytest.raises((TypeError, CredentialEncryptionError)):
            encrypt_credentials({"func": lambda x: x})

    def test_large_payload_encryption(self):
        """Large payload should encrypt successfully"""
        from app.connectors.encryption import encrypt_credentials, decrypt_credentials

        # Create a large payload (simulate many credentials)
        original = {f"key_{i}": f"value_{i}" * 100 for i in range(100)}
        encrypted = encrypt_credentials(original)
        decrypted = decrypt_credentials(encrypted)

        assert decrypted == original

    def test_empty_string_decrypt_raises_error(self):
        """Empty string should raise CredentialEncryptionError"""
        from app.connectors.encryption import decrypt_credentials, CredentialEncryptionError

        with pytest.raises(CredentialEncryptionError):
            decrypt_credentials("")

    def test_string_input_raises_error(self):
        """String input (instead of dict) should raise TypeError"""
        from app.connectors.encryption import encrypt_credentials

        with pytest.raises(TypeError):
            encrypt_credentials("not a dict")

    def test_list_input_raises_error(self):
        """List input (instead of dict) should raise TypeError"""
        from app.connectors.encryption import encrypt_credentials

        with pytest.raises(TypeError):
            encrypt_credentials(["not", "a", "dict"])

    def test_int_input_raises_error(self):
        """Int input (instead of dict) should raise TypeError"""
        from app.connectors.encryption import encrypt_credentials

        with pytest.raises(TypeError):
            encrypt_credentials(42)
