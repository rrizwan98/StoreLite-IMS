"""
Rate Limiting Service for AI Dashboard (Task T019)

Implements token bucket algorithm for 50 queries/hour per user limit.
Uses in-memory storage for MVP (can be upgraded to Redis for production).
"""

import time
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class RateLimitBucket:
    """Token bucket for rate limiting."""
    tokens: float
    last_refill: float
    window_requests: int = 0
    window_start: float = field(default_factory=time.time)


class RateLimiter:
    """
    Rate limiter using token bucket algorithm.

    Default configuration: 50 queries/hour per user (from /sp.clarify Q3)

    Features:
    - Per-user rate limiting
    - Configurable limits
    - Grace period warning at 80% usage
    - Thread-safe operations
    """

    def __init__(
        self,
        max_requests: int = 50,
        window_seconds: int = 3600,  # 1 hour
        warning_threshold: float = 0.8,  # Warn at 80% usage
    ):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests per window (default: 50)
            window_seconds: Window duration in seconds (default: 3600 = 1 hour)
            warning_threshold: Threshold for warning (default: 0.8 = 80%)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.warning_threshold = warning_threshold
        self._buckets: Dict[str, RateLimitBucket] = {}
        self._lock = Lock()

        logger.info(
            f"Rate limiter initialized: {max_requests} requests/{window_seconds}s per user"
        )

    def _get_bucket(self, user_id: str) -> RateLimitBucket:
        """Get or create bucket for user."""
        with self._lock:
            if user_id not in self._buckets:
                self._buckets[user_id] = RateLimitBucket(
                    tokens=float(self.max_requests),
                    last_refill=time.time(),
                )
            return self._buckets[user_id]

    def _refill_bucket(self, bucket: RateLimitBucket, current_time: float) -> None:
        """Refill tokens based on time elapsed."""
        elapsed = current_time - bucket.last_refill

        # Calculate tokens to add (linear refill over window)
        refill_rate = self.max_requests / self.window_seconds
        tokens_to_add = elapsed * refill_rate

        bucket.tokens = min(self.max_requests, bucket.tokens + tokens_to_add)
        bucket.last_refill = current_time

        # Reset window if it's expired
        if current_time - bucket.window_start >= self.window_seconds:
            bucket.window_requests = 0
            bucket.window_start = current_time

    def check_rate_limit(self, user_id: str) -> Tuple[bool, dict]:
        """
        Check if request is allowed and return status details.

        Args:
            user_id: User identifier (session_id or user_id)

        Returns:
            Tuple of (is_allowed, details_dict)
            details_dict contains:
                - remaining: Remaining requests in window
                - limit: Maximum requests per window
                - reset_at: ISO timestamp when limit resets
                - retry_after: Seconds until next request allowed (if rate limited)
                - warning: True if approaching limit
        """
        current_time = time.time()
        bucket = self._get_bucket(user_id)

        with self._lock:
            # Refill tokens
            self._refill_bucket(bucket, current_time)

            # Calculate reset time
            reset_time = bucket.window_start + self.window_seconds
            reset_at = datetime.fromtimestamp(reset_time).isoformat()

            # Check if request is allowed
            remaining = int(bucket.tokens)
            used_percentage = bucket.window_requests / self.max_requests
            is_warning = used_percentage >= self.warning_threshold

            if bucket.tokens >= 1:
                # Request allowed
                return True, {
                    "remaining": remaining,
                    "limit": self.max_requests,
                    "reset_at": reset_at,
                    "retry_after": None,
                    "warning": is_warning,
                    "used": bucket.window_requests,
                    "window_seconds": self.window_seconds,
                }
            else:
                # Rate limited
                # Calculate time until next token is available
                tokens_needed = 1 - bucket.tokens
                refill_rate = self.max_requests / self.window_seconds
                retry_after = tokens_needed / refill_rate

                return False, {
                    "remaining": 0,
                    "limit": self.max_requests,
                    "reset_at": reset_at,
                    "retry_after": int(retry_after) + 1,  # Round up
                    "warning": True,
                    "used": bucket.window_requests,
                    "window_seconds": self.window_seconds,
                }

    def consume(self, user_id: str) -> Tuple[bool, dict]:
        """
        Consume one request token if allowed.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (is_allowed, details_dict)
        """
        is_allowed, details = self.check_rate_limit(user_id)

        if is_allowed:
            bucket = self._get_bucket(user_id)
            with self._lock:
                bucket.tokens -= 1
                bucket.window_requests += 1
                details["remaining"] = int(bucket.tokens)
                details["used"] = bucket.window_requests

                logger.debug(
                    f"Rate limit consumed for {user_id}: "
                    f"{details['remaining']}/{self.max_requests} remaining"
                )
        else:
            logger.warning(
                f"Rate limit exceeded for {user_id}: "
                f"retry after {details['retry_after']}s"
            )

        return is_allowed, details

    def get_usage(self, user_id: str) -> dict:
        """
        Get current usage statistics for a user.

        Args:
            user_id: User identifier

        Returns:
            Usage statistics dict
        """
        _, details = self.check_rate_limit(user_id)
        return {
            "user_id": user_id,
            "used": details["used"],
            "remaining": details["remaining"],
            "limit": details["limit"],
            "reset_at": details["reset_at"],
            "warning": details["warning"],
            "percentage_used": round((details["used"] / self.max_requests) * 100, 1),
        }

    def reset_user(self, user_id: str) -> None:
        """
        Reset rate limit for a specific user (admin function).

        Args:
            user_id: User identifier to reset
        """
        with self._lock:
            if user_id in self._buckets:
                del self._buckets[user_id]
                logger.info(f"Rate limit reset for user: {user_id}")

    def cleanup_expired(self) -> int:
        """
        Clean up expired buckets to prevent memory growth.

        Returns:
            Number of buckets cleaned up
        """
        current_time = time.time()
        cleanup_threshold = self.window_seconds * 2  # Keep for 2 windows

        with self._lock:
            expired_users = [
                user_id for user_id, bucket in self._buckets.items()
                if current_time - bucket.last_refill > cleanup_threshold
            ]

            for user_id in expired_users:
                del self._buckets[user_id]

            if expired_users:
                logger.info(f"Cleaned up {len(expired_users)} expired rate limit buckets")

            return len(expired_users)


# Global rate limiter instance (singleton pattern for FastAPI)
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get or create the global rate limiter instance.

    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            max_requests=50,      # From /sp.clarify Q3
            window_seconds=3600,  # 1 hour
            warning_threshold=0.8,
        )
    return _rate_limiter
