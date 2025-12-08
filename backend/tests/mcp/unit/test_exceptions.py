"""
Tests for MCP exception classes
"""
import pytest


class TestMCPExceptions:
    """Tests for exception classes."""

    def test_mcp_validation_error_creation(self):
        """Test creating a validation error."""
        from backend.app.mcp_server.exceptions import MCPValidationError

        exc = MCPValidationError(
            "CATEGORY_INVALID",
            "Category must be one of: Grocery, Garments",
            {"category": "InvalidCat"}
        )

        assert exc.error_code == "CATEGORY_INVALID"
        assert exc.message == "Category must be one of: Grocery, Garments"
        assert exc.details["category"] == "InvalidCat"

    def test_mcp_not_found_error_creation(self):
        """Test creating a not found error."""
        from backend.app.mcp_server.exceptions import MCPNotFoundError

        exc = MCPNotFoundError("ITEM_NOT_FOUND", "Item 5 not found")
        assert exc.error_code == "ITEM_NOT_FOUND"

    def test_mcp_insufficient_stock_error_creation(self):
        """Test creating an insufficient stock error."""
        from backend.app.mcp_server.exceptions import MCPInsufficientStockError

        exc = MCPInsufficientStockError(
            "INSUFFICIENT_STOCK",
            "Item 5 has only 3 units",
            {"item_id": 5, "available": 3, "requested": 5}
        )

        assert exc.error_code == "INSUFFICIENT_STOCK"
        assert exc.details["available"] == 3


class TestErrorResponseBuilder:
    """Tests for error response builder."""

    def test_exception_to_error_response_mcp_exception(self):
        """Test converting MCPException to error response."""
        from backend.app.mcp_server.utils import exception_to_error_response
        from backend.app.mcp_server.exceptions import MCPValidationError

        exc = MCPValidationError("CATEGORY_INVALID", "Invalid category")
        response = exception_to_error_response(exc)

        assert response["error"] == "CATEGORY_INVALID"
        assert response["message"] == "Invalid category"
        assert isinstance(response["details"], dict)

    def test_exception_to_error_response_generic_exception(self):
        """Test converting generic exception to DATABASE_ERROR."""
        from backend.app.mcp_server.utils import exception_to_error_response

        exc = Exception("Something went wrong")
        response = exception_to_error_response(exc)

        assert response["error"] == "DATABASE_ERROR"
        assert "Something went wrong" in response["message"]
