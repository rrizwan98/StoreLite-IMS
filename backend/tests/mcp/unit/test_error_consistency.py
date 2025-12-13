"""
Task 42: Error consistency tests - Verify all tools return standardized error responses
"""
import pytest
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.mcp_server.schemas import ERROR_CODES
from app.mcp_server.exceptions import (
    MCPValidationError,
    MCPNotFoundError,
    MCPInsufficientStockError,
)
from app.mcp_server.utils import exception_to_error_response


class TestErrorFormat:
    """Test error response formatting."""

    def test_validation_error_format(self):
        """Verify validation errors have consistent format."""
        exc = MCPValidationError(
            "CATEGORY_INVALID",
            "Invalid category",
            {"category": "BadCat"}
        )
        response = exception_to_error_response(exc)

        assert "error" in response
        assert "message" in response
        assert "details" in response
        assert response["error"] == "CATEGORY_INVALID"
        assert response["details"]["category"] == "BadCat"

    def test_not_found_error_format(self):
        """Verify not found errors have consistent format."""
        exc = MCPNotFoundError(
            "ITEM_NOT_FOUND",
            "Item 5 not found"
        )
        response = exception_to_error_response(exc)

        assert response["error"] == "ITEM_NOT_FOUND"
        assert "Item 5" in response["message"]
        assert isinstance(response["details"], dict)

    def test_insufficient_stock_error_format(self):
        """Verify insufficient stock errors have consistent format."""
        exc = MCPInsufficientStockError(
            "INSUFFICIENT_STOCK",
            "Not enough stock",
            {"available": 3, "requested": 5}
        )
        response = exception_to_error_response(exc)

        assert response["error"] == "INSUFFICIENT_STOCK"
        assert response["details"]["available"] == 3
        assert response["details"]["requested"] == 5

    def test_generic_exception_converts_to_database_error(self):
        """Verify generic exceptions convert to DATABASE_ERROR."""
        exc = Exception("Something went wrong")
        response = exception_to_error_response(exc)

        assert response["error"] == "DATABASE_ERROR"
        assert "Something went wrong" in response["message"]


class TestErrorCodeNaming:
    """Test error code naming conventions."""

    def test_all_error_codes_are_screaming_snake_case(self):
        """Verify error codes follow naming convention."""
        for code in ERROR_CODES.values():
            # All caps
            assert code == code.upper(), f"Code {code} is not uppercase"
            # Only letters, numbers, and underscores
            assert all(c.isupper() or c == "_" or c.isdigit() for c in code), \
                f"Code {code} contains invalid characters"

    def test_required_error_codes_exist(self):
        """Verify all required error codes are defined."""
        required_codes = [
            "VALIDATION_ERROR",
            "ITEM_NOT_FOUND",
            "INSUFFICIENT_STOCK",
            "CATEGORY_INVALID",
            "UNIT_INVALID",
            "PRICE_INVALID",
            "QUANTITY_INVALID",
            "DATABASE_ERROR",
            "BILL_NOT_FOUND",
        ]

        for code in required_codes:
            assert code in ERROR_CODES, f"Required error code {code} not found"


class TestErrorDetails:
    """Test error details include relevant context."""

    def test_validation_error_includes_field_context(self):
        """Verify validation errors include field information."""
        exc = MCPValidationError(
            "PRICE_INVALID",
            "Price must be > 0",
            {"field": "unit_price", "value": -50.0}
        )
        response = exception_to_error_response(exc)

        assert response["details"]["field"] == "unit_price"
        assert response["details"]["value"] == -50.0

    def test_insufficient_stock_includes_inventory_context(self):
        """Verify insufficient stock errors include stock information."""
        exc = MCPInsufficientStockError(
            "INSUFFICIENT_STOCK",
            "Sugar: need 50, have 10",
            {
                "item_id": 1,
                "item_name": "Sugar",
                "available": 10,
                "requested": 50
            }
        )
        response = exception_to_error_response(exc)

        assert response["details"]["item_id"] == 1
        assert response["details"]["item_name"] == "Sugar"
        assert response["details"]["available"] == 10
        assert response["details"]["requested"] == 50

    def test_not_found_error_includes_resource_id(self):
        """Verify not found errors include resource information."""
        exc = MCPNotFoundError(
            "ITEM_NOT_FOUND",
            "Item 999 not found",
            {"resource": "Item", "id": 999}
        )
        response = exception_to_error_response(exc)

        assert response["details"]["resource"] == "Item"
        assert response["details"]["id"] == 999
