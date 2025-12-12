"""
Utility functions for MCP server
"""
import logging
from contextlib import asynccontextmanager
from functools import wraps
from typing import Dict, Any
from decimal import Decimal

from app.database import async_session
from app.mcp_server.exceptions import (
    MCPException,
    MCPValidationError,
    MCPNotFoundError,
    MCPInsufficientStockError,
    MCPDatabaseError,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Task 5: Database session management for MCP context
# ============================================================================

@asynccontextmanager
async def get_mcp_session():
    """
    Get async session for MCP tool with transaction management.

    MCP tools don't auto-commit; caller decides when to commit.
    Rolls back on exception.
    """
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================================================
# Task 11: Error response builder
# ============================================================================

def exception_to_error_response(exc: Exception) -> Dict[str, Any]:
    """
    Convert exception to standard error response.

    Args:
        exc: Exception to convert

    Returns:
        Dict with error, message, details structure
    """
    if isinstance(exc, MCPException):
        return {
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    else:
        # Generic exception -> DATABASE_ERROR
        return {
            "error": "DATABASE_ERROR",
            "message": str(exc),
            "details": {}
        }


# ============================================================================
# Error handler decorator for MCP tools
# ============================================================================

def mcp_error_handler(tool_name: str):
    """
    Decorator to convert service exceptions to MCP exceptions.

    Usage:
        @mcp_error_handler("tool_name")
        async def my_tool(...):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except MCPException:
                # Already converted
                raise
            except Exception as e:
                logger.error(
                    f"[{tool_name}] Unexpected error: {str(e)}",
                    exc_info=True
                )
                raise MCPDatabaseError("DATABASE_ERROR", str(e))

        return wrapper
    return decorator


# ============================================================================
# Helper functions for schema conversions
# ============================================================================

def convert_decimal_to_float(value):
    """Convert Decimal to float for JSON serialization."""
    if isinstance(value, Decimal):
        return float(value)
    return value


def decimal_to_str(value):
    """Convert Decimal to string for JSON serialization."""
    if isinstance(value, Decimal):
        return str(value)
    return value


# ============================================================================
# Case-Insensitive Category Handling
# ============================================================================

VALID_CATEGORIES = {"Grocery", "Garments", "Beauty", "Utilities", "Other"}


def get_valid_categories():
    """Return sorted list of valid categories (source of truth)."""
    return sorted(VALID_CATEGORIES)


def normalize_category(category: str) -> str:
    """
    Normalize user input category to valid category value.

    Tries exact match first, then case-insensitive match.
    Raises helpful error if no match found with valid categories listed.

    Args:
        category: User input category (any case)

    Returns:
        Normalized category name (proper case)

    Raises:
        MCPValidationError: If category not found
    """
    if not category or not isinstance(category, str):
        raise MCPValidationError(
            "CATEGORY_INVALID",
            "Category must be a non-empty string"
        )

    # Try exact match first (fastest path)
    if category in VALID_CATEGORIES:
        return category

    # Try case-insensitive match
    lower_input = category.lower()
    for valid_cat in sorted(VALID_CATEGORIES):
        if valid_cat.lower() == lower_input:
            return valid_cat

    # No match - provide helpful suggestions
    suggestions = ", ".join(sorted(VALID_CATEGORIES))
    raise MCPValidationError(
        "CATEGORY_INVALID",
        f"Category '{category}' not found. Valid categories: {suggestions}",
        {"category": category, "valid_categories": list(sorted(VALID_CATEGORIES))}
    )


def category_exists(category: str) -> bool:
    """
    Check if category exists (case-insensitive).

    Args:
        category: Category name to check (any case)

    Returns:
        True if category exists, False otherwise
    """
    if not category or not isinstance(category, str):
        return False

    # Check exact match
    if category in VALID_CATEGORIES:
        return True

    # Check case-insensitive match
    lower_input = category.lower()
    for valid_cat in VALID_CATEGORIES:
        if valid_cat.lower() == lower_input:
            return True

    return False
