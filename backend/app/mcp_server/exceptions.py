"""
MCP-specific exception classes for error handling
"""


class MCPException(Exception):
    """Base exception for all MCP operations."""

    def __init__(
        self,
        error_code: str,
        message: str,
        details: dict = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def __str__(self):
        return f"{self.error_code}: {self.message}"


class MCPValidationError(MCPException):
    """Validation error (400)."""
    pass


class MCPNotFoundError(MCPException):
    """Resource not found error (404)."""
    pass


class MCPInsufficientStockError(MCPException):
    """Insufficient stock error (422)."""
    pass


class MCPImmutableError(MCPException):
    """Immutable resource error (422)."""
    pass


class MCPDatabaseError(MCPException):
    """Database operation error (500)."""
    pass
