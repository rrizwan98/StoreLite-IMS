"""
Utility functions for MCP server
"""
import logging
from contextlib import asynccontextmanager
from functools import wraps
from typing import Dict, Any
from decimal import Decimal

from backend.app.database import async_session
from backend.app.mcp_server.exceptions import (
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
