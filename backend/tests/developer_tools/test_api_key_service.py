"""
Unit Tests for API Key Service (Phase 14)

Tests API key generation, hashing, and validation.
"""

import pytest
from app.services.api_key_service import (
    generate_api_key,
    hash_api_key,
    parse_api_key,
    is_valid_key_format,
    mask_api_key,
    generate_display_prefix,
)


# =============================================================================
# Tests for generate_api_key
# =============================================================================

class TestGenerateApiKey:
    """Tests for API key generation."""

    def test_generate_returns_tuple(self):
        """Test that generation returns a tuple."""
        result = generate_api_key()
        assert isinstance(result, tuple)
        assert len(result) == 3  # (full_key, key_hash, prefix)

    def test_generate_has_prefix(self):
        """Test that generated key has correct prefix."""
        full_key, key_hash, prefix = generate_api_key()
        assert full_key.startswith("pa_live_")

    def test_generate_sufficient_length(self):
        """Test that generated key has sufficient length."""
        full_key, key_hash, prefix = generate_api_key()
        # Prefix (8) + 32 hex chars = 40 minimum
        assert len(full_key) >= 40

    def test_generate_unique_keys(self):
        """Test that each generation produces unique key."""
        keys = [generate_api_key()[0] for _ in range(10)]
        assert len(set(keys)) == 10

    def test_generate_hash_different_from_key(self):
        """Test that hash is different from key."""
        full_key, key_hash, prefix = generate_api_key()
        assert full_key != key_hash

    def test_generate_prefix_is_subset(self):
        """Test that prefix is subset of full key."""
        full_key, key_hash, prefix = generate_api_key()
        # Prefix should be start of key (possibly with ... or masking)
        assert prefix.startswith("pa_live_")


# =============================================================================
# Tests for hash_api_key
# =============================================================================

class TestHashApiKey:
    """Tests for API key hashing."""

    def test_hash_returns_string(self):
        """Test that hash returns a string."""
        key = "pa_live_abc123def456"
        hashed = hash_api_key(key)
        assert isinstance(hashed, str)

    def test_hash_different_from_original(self):
        """Test that hash is different from original key."""
        key = "pa_live_abc123def456"
        hashed = hash_api_key(key)
        assert hashed != key

    def test_hash_deterministic(self):
        """Test that same key produces same hash."""
        key = "pa_live_abc123def456"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)
        assert hash1 == hash2

    def test_hash_different_keys_different_hashes(self):
        """Test that different keys produce different hashes."""
        key1 = "pa_live_abc123"
        key2 = "pa_live_def456"
        hash1 = hash_api_key(key1)
        hash2 = hash_api_key(key2)
        assert hash1 != hash2


# =============================================================================
# Tests for parse_api_key
# =============================================================================

class TestParseApiKey:
    """Tests for API key parsing."""

    def test_parse_valid_key(self):
        """Test parsing a valid key."""
        # Key must have exactly 32 hex chars after prefix (16 bytes * 2)
        key = "pa_live_3d2be987000ba0912b298497a5cd02ab"  # exactly 32 hex chars
        prefix, secret = parse_api_key(key)
        assert prefix == "pa_live_"
        assert secret == "3d2be987000ba0912b298497a5cd02ab"

    def test_parse_returns_tuple(self):
        """Test that parse returns a tuple."""
        # Generate a valid key for testing
        full_key, _, _ = generate_api_key()
        result = parse_api_key(full_key)
        assert isinstance(result, tuple)
        assert len(result) == 2


# =============================================================================
# Tests for is_valid_key_format
# =============================================================================

class TestIsValidKeyFormat:
    """Tests for key format validation."""

    def test_valid_format(self):
        """Test that valid format is accepted."""
        # Key must have exactly 32 hex chars after prefix
        key = "pa_live_3d2be987000ba0912b298497a5cd02ab"  # exactly 32 hex chars
        assert is_valid_key_format(key) is True

    def test_invalid_prefix(self):
        """Test that invalid prefix is rejected."""
        key = "invalid_abc123def456"
        assert is_valid_key_format(key) is False

    def test_too_short(self):
        """Test that too short key is rejected."""
        key = "pa_live_abc"
        assert is_valid_key_format(key) is False

    def test_empty_string(self):
        """Test that empty string is rejected."""
        assert is_valid_key_format("") is False

    def test_generated_key_is_valid(self):
        """Test that generated keys pass validation."""
        full_key, _, _ = generate_api_key()
        assert is_valid_key_format(full_key) is True


# =============================================================================
# Tests for mask_api_key
# =============================================================================

class TestMaskApiKey:
    """Tests for API key masking."""

    def test_mask_hides_secret(self):
        """Test that masking hides the secret part."""
        key = "pa_live_abc123def456ghi789"
        masked = mask_api_key(key)
        # Should show prefix but hide most of secret
        assert "pa_live_" in masked
        assert "abc123def456ghi789" not in masked

    def test_mask_returns_string(self):
        """Test that mask returns a string."""
        key = "pa_live_abc123"
        masked = mask_api_key(key)
        assert isinstance(masked, str)


# =============================================================================
# Tests for generate_display_prefix
# =============================================================================

class TestGenerateDisplayPrefix:
    """Tests for display prefix generation."""

    def test_display_prefix_shorter_than_key(self):
        """Test that display prefix is shorter than full key."""
        key = "pa_live_abc123def456ghi789jkl012"
        prefix = generate_display_prefix(key)
        assert len(prefix) < len(key)

    def test_display_prefix_starts_with_pa(self):
        """Test that display prefix starts correctly."""
        key = "pa_live_abc123def456"
        prefix = generate_display_prefix(key)
        assert prefix.startswith("pa_live_")
