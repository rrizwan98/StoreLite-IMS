"""
API Key Service for Developer Tools (Phase 14)

Handles generation, hashing, and validation of API keys for published agents.

Key Features:
- Generates secure API keys in format: pa_live_[32-hex-chars]
- Stores only SHA-256 hash (original key shown only once)
- Validates API keys efficiently via indexed hash lookup

Security Design:
- API keys are 128-bit random (secrets.token_hex(16))
- SHA-256 hash stored in database (64 hex chars)
- Original key never logged or stored
- Prefix stored separately for display ("pa_live_abc1...")
"""

import hashlib
import secrets
import logging
from typing import Optional, Tuple
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.published_agent import PublishedAgentConfig

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

# API Key prefix for identification
API_KEY_PREFIX = "pa_live_"

# Length of random hex part (32 chars = 128 bits)
API_KEY_RANDOM_LENGTH = 16  # token_hex(16) = 32 hex chars

# Display prefix length (for showing in dashboard)
API_KEY_DISPLAY_PREFIX_LENGTH = 12  # "pa_live_abc1..."


# =============================================================================
# Key Generation Functions
# =============================================================================

def generate_api_key() -> Tuple[str, str, str]:
    """
    Generate a new API key with hash and display prefix.

    Returns:
        Tuple of (full_key, hash, display_prefix)

        Example:
        - full_key: "pa_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
        - hash: "sha256_64_char_hex_string..."
        - display_prefix: "pa_live_a1b2..."

    Security Notes:
    - Uses secrets.token_hex() for cryptographically secure randomness
    - Full key is only returned at creation time (never stored)
    - Only the hash is stored in database
    """
    # Generate random part (32 hex chars = 128 bits of entropy)
    random_part = secrets.token_hex(API_KEY_RANDOM_LENGTH)

    # Combine prefix with random part
    full_key = f"{API_KEY_PREFIX}{random_part}"

    # Calculate SHA-256 hash for storage
    key_hash = hash_api_key(full_key)

    # Create display prefix for showing in dashboard
    display_prefix = full_key[:API_KEY_DISPLAY_PREFIX_LENGTH] + "..."

    logger.info(f"[API Key] Generated new key with prefix: {display_prefix}")

    return full_key, key_hash, display_prefix


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256.

    Args:
        api_key: The full API key string (e.g., "pa_live_abc123...")

    Returns:
        64-character hex string (SHA-256 hash)

    Notes:
    - Same key always produces same hash (deterministic)
    - Used for O(1) lookup via indexed column
    """
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def parse_api_key(api_key: str) -> Tuple[str, str]:
    """
    Parse API key into prefix and random parts.

    Args:
        api_key: Full API key string

    Returns:
        Tuple of (prefix, random_part)

    Raises:
        ValueError: If key format is invalid
    """
    if not api_key or not api_key.startswith(API_KEY_PREFIX):
        raise ValueError(f"Invalid API key format. Expected prefix: {API_KEY_PREFIX}")

    random_part = api_key[len(API_KEY_PREFIX):]

    if len(random_part) != API_KEY_RANDOM_LENGTH * 2:  # hex is 2 chars per byte
        raise ValueError("Invalid API key length")

    return API_KEY_PREFIX, random_part


def is_valid_key_format(api_key: str) -> bool:
    """
    Check if API key has valid format (without database lookup).

    Args:
        api_key: API key to validate

    Returns:
        True if format is valid, False otherwise
    """
    try:
        parse_api_key(api_key)
        return True
    except ValueError:
        return False


# =============================================================================
# Key Validation Functions
# =============================================================================

async def validate_api_key(
    api_key: str,
    db: AsyncSession
) -> PublishedAgentConfig:
    """
    Validate an API key and return the associated config.

    This is the main entry point for API key validation in request handling.

    Args:
        api_key: The full API key from X-API-Key header
        db: Database session

    Returns:
        PublishedAgentConfig if key is valid and active

    Raises:
        HTTPException(401): If key is invalid, inactive, or expired
        HTTPException(401): If key format is wrong

    Flow:
    1. Validate key format (quick check, no DB)
    2. Hash the key
    3. Lookup config by hash (indexed O(1))
    4. Check is_active flag
    5. Check expires_at (if set)
    """
    # Step 1: Quick format validation
    if not api_key:
        logger.warning("[API Key] Empty API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_api_key",
                "message": "API key is required. Provide it in the X-API-Key header."
            }
        )

    if not is_valid_key_format(api_key):
        logger.warning(f"[API Key] Invalid format: {api_key[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_api_key_format",
                "message": "Invalid API key format. Keys should start with 'pa_live_'"
            }
        )

    # Step 2: Hash the key for lookup
    key_hash = hash_api_key(api_key)

    # Step 3: Lookup by hash (indexed column)
    result = await db.execute(
        select(PublishedAgentConfig).where(
            PublishedAgentConfig.api_key_hash == key_hash
        )
    )
    config = result.scalar_one_or_none()

    # Step 4: Check if key exists
    if config is None:
        logger.warning(f"[API Key] Key not found: {api_key[:12]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_api_key",
                "message": "The provided API key is invalid or has been revoked."
            }
        )

    # Step 5: Check if active
    if not config.is_active:
        logger.warning(f"[API Key] Inactive key used: {config.api_key_prefix}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "api_key_inactive",
                "message": "This API key has been deactivated."
            }
        )

    # Step 6: Check expiration
    if config.expires_at and config.expires_at < datetime.utcnow():
        logger.warning(f"[API Key] Expired key used: {config.api_key_prefix}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "api_key_expired",
                "message": "This API key has expired."
            }
        )

    logger.info(f"[API Key] Validated successfully: {config.api_key_prefix} (agent: {config.name})")
    return config


async def get_config_by_api_key_hash(
    key_hash: str,
    db: AsyncSession
) -> Optional[PublishedAgentConfig]:
    """
    Get config by API key hash (internal use).

    Args:
        key_hash: SHA-256 hash of the API key
        db: Database session

    Returns:
        PublishedAgentConfig or None if not found
    """
    result = await db.execute(
        select(PublishedAgentConfig).where(
            PublishedAgentConfig.api_key_hash == key_hash
        )
    )
    return result.scalar_one_or_none()


# =============================================================================
# Utility Functions
# =============================================================================

def mask_api_key(api_key: str) -> str:
    """
    Mask API key for logging (show only prefix).

    Args:
        api_key: Full API key

    Returns:
        Masked string like "pa_live_abc1...xxxx"
    """
    if not api_key or len(api_key) < 12:
        return "***"

    return api_key[:12] + "..." + api_key[-4:]


def generate_display_prefix(api_key: str) -> str:
    """
    Generate display prefix from full API key.

    Args:
        api_key: Full API key

    Returns:
        Display prefix like "pa_live_abc1..."
    """
    if not api_key or len(api_key) < API_KEY_DISPLAY_PREFIX_LENGTH:
        return api_key + "..."

    return api_key[:API_KEY_DISPLAY_PREFIX_LENGTH] + "..."
