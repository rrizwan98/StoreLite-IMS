"""
Domain Validator for Published Agent API (Phase 14)

Validates request Origin header against allowed domain patterns.
Used for CORS-like protection on the public API.

Supported Patterns:
- Exact match: "mystore.com"
- Wildcard subdomain: "*.mystore.com" (matches shop.mystore.com, api.mystore.com)
- Wildcard port: "localhost:*" (matches localhost:3000, localhost:8080)
- Any origin: "*" (not recommended for production)

Security Notes:
- This is an additional security layer, not a replacement for proper CORS
- Always validate on server-side, not just client-side
- Wildcard "*" should only be used for development
"""

import re
import logging
from typing import List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def validate_origin(
    origin: Optional[str],
    allowed_domains: List[str]
) -> bool:
    """
    Validate request Origin against allowed domain patterns.

    Args:
        origin: The Origin header value (e.g., "https://shop.mystore.com")
        allowed_domains: List of allowed domain patterns

    Returns:
        True if origin is allowed, False otherwise

    Examples:
        >>> validate_origin("https://shop.mystore.com", ["*.mystore.com"])
        True
        >>> validate_origin("https://evil.com", ["*.mystore.com"])
        False
        >>> validate_origin("http://localhost:3000", ["localhost:*"])
        True
        >>> validate_origin(None, ["*"])
        True  # Missing origin with "*" wildcard
    """
    # Handle missing origin
    if not origin:
        # If wildcard allowed, permit missing origin (for server-to-server)
        if "*" in allowed_domains:
            logger.debug("[Domain Validator] Missing origin allowed (wildcard)")
            return True
        logger.warning("[Domain Validator] Missing origin header")
        return False

    # Handle empty allowed list
    if not allowed_domains:
        logger.warning("[Domain Validator] No allowed domains configured")
        return False

    # Extract host from origin
    origin_host = extract_host(origin)
    if not origin_host:
        logger.warning(f"[Domain Validator] Could not extract host from: {origin}")
        return False

    # Check each pattern
    for pattern in allowed_domains:
        if match_domain_pattern(origin_host, pattern):
            logger.debug(
                f"[Domain Validator] Matched: {origin_host} -> {pattern}"
            )
            return True

    logger.warning(
        f"[Domain Validator] Origin not allowed: {origin_host}, "
        f"allowed: {allowed_domains}"
    )
    return False


def extract_host(origin: str) -> Optional[str]:
    """
    Extract host (with port if present) from origin URL.

    Args:
        origin: Origin URL (e.g., "https://shop.mystore.com:8080")

    Returns:
        Host string (e.g., "shop.mystore.com:8080") or None if invalid

    Examples:
        >>> extract_host("https://shop.mystore.com")
        "shop.mystore.com"
        >>> extract_host("http://localhost:3000")
        "localhost:3000"
        >>> extract_host("https://api.example.com:443")
        "api.example.com:443"
    """
    if not origin:
        return None

    try:
        # Handle origins that might not have a scheme
        if "://" not in origin:
            origin = "https://" + origin

        parsed = urlparse(origin)
        host = parsed.hostname or parsed.netloc

        if not host:
            return None

        # Include port if present (and not default)
        port = parsed.port
        if port:
            return f"{host}:{port}"

        return host

    except Exception as e:
        logger.error(f"[Domain Validator] Error parsing origin '{origin}': {e}")
        return None


def match_domain_pattern(host: str, pattern: str) -> bool:
    """
    Match a host against a domain pattern.

    Supports:
    - Exact match: "mystore.com"
    - Wildcard subdomain: "*.mystore.com"
    - Wildcard port: "localhost:*"
    - Any: "*"

    Args:
        host: Host to check (e.g., "shop.mystore.com")
        pattern: Pattern to match against

    Returns:
        True if host matches pattern

    Examples:
        >>> match_domain_pattern("mystore.com", "mystore.com")
        True
        >>> match_domain_pattern("shop.mystore.com", "*.mystore.com")
        True
        >>> match_domain_pattern("mystore.com", "*.mystore.com")
        False  # Wildcard requires subdomain
        >>> match_domain_pattern("localhost:3000", "localhost:*")
        True
    """
    # Normalize inputs
    host = host.lower().strip()
    pattern = pattern.lower().strip()

    # Empty pattern = no match
    if not pattern:
        return False

    # Universal wildcard
    if pattern == "*":
        return True

    # Exact match (case-insensitive)
    if host == pattern:
        return True

    # Wildcard subdomain pattern: *.example.com
    if pattern.startswith("*."):
        base_domain = pattern[2:]  # Remove "*."

        # Host must end with .base_domain (not just base_domain)
        # e.g., "shop.example.com" matches "*.example.com"
        # but "example.com" does NOT match "*.example.com"
        if host.endswith("." + base_domain):
            return True

        return False

    # Wildcard port pattern: localhost:*
    if pattern.endswith(":*"):
        base_host = pattern[:-2]  # Remove ":*"

        # Host must start with base_host and have a port
        if ":" in host:
            host_without_port = host.split(":")[0]
            if host_without_port == base_host:
                return True

        return False

    # No match
    return False


def normalize_domains(domains: List[str]) -> List[str]:
    """
    Normalize domain patterns (lowercase, strip whitespace).

    Args:
        domains: List of domain patterns

    Returns:
        Normalized list
    """
    return [d.lower().strip() for d in domains if d and d.strip()]


def is_localhost(origin: Optional[str]) -> bool:
    """
    Check if origin is localhost (any port).

    Args:
        origin: Origin URL

    Returns:
        True if localhost
    """
    if not origin:
        return False

    host = extract_host(origin)
    if not host:
        return False

    # Remove port if present
    host_without_port = host.split(":")[0]

    return host_without_port in ("localhost", "127.0.0.1", "::1")


def suggest_domain_pattern(domain: str) -> str:
    """
    Suggest a domain pattern for a given domain.

    Useful for helping users configure allowed domains.

    Args:
        domain: Domain name (e.g., "shop.mystore.com")

    Returns:
        Suggested pattern (e.g., "*.mystore.com")
    """
    if not domain:
        return "*"

    # Clean up
    domain = domain.lower().strip()

    # Remove protocol if present
    if "://" in domain:
        domain = extract_host(domain) or domain

    # Remove port
    domain = domain.split(":")[0]

    # Split into parts
    parts = domain.split(".")

    # If single part (e.g., "localhost"), return as-is with port wildcard
    if len(parts) == 1:
        return f"{domain}:*"

    # If two parts (e.g., "mystore.com"), return exact + wildcard
    if len(parts) == 2:
        return f"*.{domain}"

    # If more parts (e.g., "shop.mystore.com"), suggest wildcard for base
    base = ".".join(parts[-2:])
    return f"*.{base}"
