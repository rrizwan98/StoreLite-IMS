"""
Custom exceptions and error handling for IMS
"""

import logging

logger = logging.getLogger(__name__)


class IMSException(Exception):
    """Base exception for IMS"""

    pass


class ValidationError(IMSException):
    """Raised when input validation fails"""

    pass


class ItemNotFoundError(IMSException):
    """Raised when an item is not found"""

    pass


class InsufficientStockError(IMSException):
    """Raised when item stock is insufficient"""

    pass


class BillingError(IMSException):
    """Raised when billing operation fails"""

    pass


class DatabaseError(IMSException):
    """Raised when database operation fails"""

    pass


def format_error_message(error: Exception, context: str = "") -> str:
    """
    Format error message for user display (no stack traces)

    Args:
        error: Exception object
        context: Additional context about the error

    Returns:
        User-friendly error message
    """
    error_map = {
        ValidationError: "Invalid input provided",
        ItemNotFoundError: "Item not found",
        InsufficientStockError: "Insufficient stock available",
        BillingError: "Billing operation failed",
        DatabaseError: "Database error occurred",
    }

    error_type = type(error)
    base_message = error_map.get(error_type, "An error occurred")

    if str(error):
        message = f"{base_message}: {str(error)}"
    else:
        message = base_message

    if context:
        message = f"{message} ({context})"

    return message


def log_error(error: Exception, context: str = "", level: int = logging.ERROR) -> None:
    """
    Log error with full context for debugging

    Args:
        error: Exception object
        context: Additional context
        level: Logging level
    """
    logger.log(level, f"{context}: {str(error)}", exc_info=True)
