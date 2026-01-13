"""
Rate Limiter for Published Agents (Phase 14)

Per-API-key rate limiting using sliding window algorithm.
Separate from the main rate_limiter.py which is user-based.

Key Differences from main rate_limiter:
- Keyed by API key ID (not user ID)
- Per-minute limits (not hourly)
- Sliding window (not token bucket)
- Async-compatible for FastAPI

Design:
- Uses collections.deque for efficient sliding window
- O(1) check operation (amortized)
- Memory cleanup for inactive keys
- Thread-safe with asyncio.Lock
"""

import asyncio
import logging
import time
from collections import deque
from typing import Dict, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

# Default window size (1 minute)
DEFAULT_WINDOW_SECONDS = 60

# Cleanup inactive entries after this many seconds
CLEANUP_THRESHOLD_SECONDS = 300  # 5 minutes


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class RateLimitWindow:
    """
    Sliding window for rate limiting.

    Stores timestamps of requests within the window.
    Old timestamps are pruned on each check.
    """
    timestamps: deque = field(default_factory=deque)
    last_accessed: float = field(default_factory=time.time)


# =============================================================================
# Rate Limiter Service
# =============================================================================

class PublishedAgentRateLimiter:
    """
    Sliding window rate limiter for published agent API keys.

    Each API key has its own window tracking request timestamps.
    The window slides with time - old requests expire automatically.

    Thread Safety:
    - Uses asyncio.Lock for async operations
    - Safe for concurrent FastAPI requests

    Memory Management:
    - Old entries automatically pruned on access
    - Periodic cleanup of inactive keys
    """

    def __init__(self, window_seconds: int = DEFAULT_WINDOW_SECONDS):
        """
        Initialize rate limiter.

        Args:
            window_seconds: Size of sliding window in seconds (default: 60)
        """
        self._window_seconds = window_seconds
        self._windows: Dict[str, RateLimitWindow] = {}
        self._lock = asyncio.Lock()

        logger.info(
            f"[Published Agent Rate Limiter] Initialized with "
            f"{window_seconds}s sliding window"
        )

    async def check_rate_limit(
        self,
        key_id: str,
        limit: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit.

        Does NOT consume a request - use record_request() after successful processing.

        Args:
            key_id: The published agent config ID (or API key hash)
            limit: Maximum requests per window

        Returns:
            Tuple of (allowed, remaining, reset_seconds)
            - allowed: True if request is allowed
            - remaining: Number of remaining requests in window
            - reset_seconds: Seconds until oldest request expires
        """
        async with self._lock:
            current_time = time.time()
            window = self._get_or_create_window(key_id)

            # Prune expired timestamps
            self._prune_window(window, current_time)

            # Count requests in window
            request_count = len(window.timestamps)
            remaining = max(0, limit - request_count)

            # Calculate reset time (when oldest request expires)
            if window.timestamps:
                oldest = window.timestamps[0]
                reset_seconds = max(0, int(self._window_seconds - (current_time - oldest)))
            else:
                reset_seconds = self._window_seconds

            # Check if allowed
            allowed = request_count < limit

            if not allowed:
                logger.warning(
                    f"[Rate Limit] Exceeded for key {key_id[:8]}...: "
                    f"{request_count}/{limit}, reset in {reset_seconds}s"
                )

            return allowed, remaining, reset_seconds

    async def record_request(self, key_id: str) -> None:
        """
        Record a request for rate limiting.

        Call this AFTER successfully processing a request.

        Args:
            key_id: The published agent config ID
        """
        async with self._lock:
            current_time = time.time()
            window = self._get_or_create_window(key_id)

            # Add current timestamp
            window.timestamps.append(current_time)
            window.last_accessed = current_time

            logger.debug(
                f"[Rate Limit] Recorded request for {key_id[:8]}...: "
                f"{len(window.timestamps)} requests in window"
            )

    async def get_usage(
        self,
        key_id: str,
        limit: int
    ) -> Dict:
        """
        Get current usage statistics for an API key.

        Args:
            key_id: The published agent config ID
            limit: Maximum requests per window

        Returns:
            Dict with usage statistics
        """
        allowed, remaining, reset_seconds = await self.check_rate_limit(key_id, limit)

        async with self._lock:
            window = self._windows.get(key_id)
            request_count = len(window.timestamps) if window else 0

        return {
            "key_id": key_id[:8] + "...",
            "limit": limit,
            "used": request_count,
            "remaining": remaining,
            "reset_seconds": reset_seconds,
            "window_seconds": self._window_seconds,
            "allowed": allowed,
        }

    async def get_rate_limit_headers(
        self,
        key_id: str,
        limit: int
    ) -> Dict[str, str]:
        """
        Get HTTP headers for rate limit response.

        Args:
            key_id: The published agent config ID
            limit: Maximum requests per window

        Returns:
            Dict of header name -> value
        """
        allowed, remaining, reset_seconds = await self.check_rate_limit(key_id, limit)

        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_seconds),
            "X-RateLimit-Window": str(self._window_seconds),
        }

    async def reset_key(self, key_id: str) -> None:
        """
        Reset rate limit for a specific key (admin function).

        Args:
            key_id: The published agent config ID
        """
        async with self._lock:
            if key_id in self._windows:
                del self._windows[key_id]
                logger.info(f"[Rate Limit] Reset for key {key_id[:8]}...")

    async def cleanup_inactive(self) -> int:
        """
        Clean up inactive windows to prevent memory growth.

        Should be called periodically (e.g., every 5 minutes).

        Returns:
            Number of windows cleaned up
        """
        async with self._lock:
            current_time = time.time()
            inactive_keys = [
                key_id
                for key_id, window in self._windows.items()
                if current_time - window.last_accessed > CLEANUP_THRESHOLD_SECONDS
            ]

            for key_id in inactive_keys:
                del self._windows[key_id]

            if inactive_keys:
                logger.info(
                    f"[Rate Limit] Cleaned up {len(inactive_keys)} inactive windows"
                )

            return len(inactive_keys)

    def _get_or_create_window(self, key_id: str) -> RateLimitWindow:
        """Get or create window for key (not async-safe, call within lock)."""
        if key_id not in self._windows:
            self._windows[key_id] = RateLimitWindow()
        return self._windows[key_id]

    def _prune_window(self, window: RateLimitWindow, current_time: float) -> None:
        """Remove expired timestamps from window (not async-safe, call within lock)."""
        cutoff = current_time - self._window_seconds

        # Remove timestamps older than window
        while window.timestamps and window.timestamps[0] < cutoff:
            window.timestamps.popleft()


# =============================================================================
# Global Instance (Singleton)
# =============================================================================

_rate_limiter: Optional[PublishedAgentRateLimiter] = None


def get_published_agent_rate_limiter() -> PublishedAgentRateLimiter:
    """
    Get the global published agent rate limiter instance.

    Returns:
        PublishedAgentRateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = PublishedAgentRateLimiter(
            window_seconds=DEFAULT_WINDOW_SECONDS
        )
    return _rate_limiter


async def check_and_record_rate_limit(
    key_id: str,
    limit: int
) -> Tuple[bool, Dict[str, str]]:
    """
    Convenience function to check rate limit and record if allowed.

    This is the main entry point for rate limiting in request handlers.

    Args:
        key_id: The published agent config ID
        limit: Maximum requests per window (from config.rate_limit_per_minute)

    Returns:
        Tuple of (allowed, headers)
        - allowed: True if request is allowed
        - headers: Rate limit headers to include in response
    """
    limiter = get_published_agent_rate_limiter()

    # Check limit
    allowed, remaining, reset_seconds = await limiter.check_rate_limit(key_id, limit)

    # Build headers
    headers = {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(reset_seconds),
    }

    if allowed:
        # Record the request
        await limiter.record_request(key_id)
        # Update remaining after recording
        headers["X-RateLimit-Remaining"] = str(max(0, remaining - 1))

    return allowed, headers
