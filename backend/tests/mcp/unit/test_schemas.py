"""
Unit tests for MCP schemas
"""
import pytest
from pydantic import ValidationError
from decimal import Decimal
from datetime import datetime


class TestErrorResponse:
    """Tests for ErrorResponse schema."""

    def test_error_response_creation(self):
        """Test creating an error response."""
        from app.mcp_server.schemas import ErrorResponse

        error = ErrorResponse(
            error="INSUFFICIENT_STOCK",
            message="Item 5 has only 3 units",
            details={"item_id": 5, "available": 3, "requested": 5}
        )

        assert error.error == "INSUFFICIENT_STOCK"
        assert error.message == "Item 5 has only 3 units"
        assert error.details["item_id"] == 5


class TestPaginationInfo:
    """Tests for PaginationInfo schema."""

    def test_pagination_info_creation(self):
        """Test creating pagination info."""
        from app.mcp_server.schemas import PaginationInfo

        page = PaginationInfo(page=1, limit=20, total=45, total_pages=3)
        assert page.total_pages == 3
        assert page.page == 1
        assert page.limit == 20


class TestItemCreate:
    """Tests for ItemCreate schema."""

    def test_item_create_success(self):
        """Test creating a valid item."""
        from app.mcp_server.schemas import ItemCreate

        item = ItemCreate(
            name="Sugar",
            category="Grocery",
            unit="kg",
            unit_price=50.0,
            stock_qty=100.0
        )

        assert item.name == "Sugar"
        assert item.category == "Grocery"
        assert item.unit_price == 50.0

    def test_item_create_validates_category(self):
        """Test category validation."""
        from app.mcp_server.schemas import ItemCreate

        with pytest.raises(ValidationError):
            ItemCreate(
                name="Sugar",
                category="InvalidCategory",
                unit="kg",
                unit_price=50.0,
                stock_qty=100.0
            )

    def test_item_create_validates_unit(self):
        """Test unit validation."""
        from app.mcp_server.schemas import ItemCreate

        with pytest.raises(ValidationError):
            ItemCreate(
                name="Sugar",
                category="Grocery",
                unit="InvalidUnit",
                unit_price=50.0,
                stock_qty=100.0
            )

    def test_item_create_validates_positive_price(self):
        """Test price validation."""
        from app.mcp_server.schemas import ItemCreate

        with pytest.raises(ValidationError):
            ItemCreate(
                name="Sugar",
                category="Grocery",
                unit="kg",
                unit_price=-10.0,
                stock_qty=100.0
            )

    def test_item_create_validates_nonnegative_stock(self):
        """Test stock quantity validation."""
        from app.mcp_server.schemas import ItemCreate

        with pytest.raises(ValidationError):
            ItemCreate(
                name="Sugar",
                category="Grocery",
                unit="kg",
                unit_price=50.0,
                stock_qty=-10.0
            )

    def test_item_create_validates_name_length(self):
        """Test name validation."""
        from app.mcp_server.schemas import ItemCreate

        # Empty name should fail
        with pytest.raises(ValidationError):
            ItemCreate(
                name="",
                category="Grocery",
                unit="kg",
                unit_price=50.0,
                stock_qty=100.0
            )


class TestItemRead:
    """Tests for ItemRead schema."""

    def test_item_read_creation(self):
        """Test creating an ItemRead response."""
        from app.mcp_server.schemas import ItemRead

        item = ItemRead(
            id=1,
            name="Sugar",
            category="Grocery",
            unit="kg",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("100.0"),
            is_active=True,
            created_at=datetime.now()
        )

        assert item.id == 1
        assert item.name == "Sugar"
        assert item.is_active is True


class TestItemListResponse:
    """Tests for ItemListResponse schema."""

    def test_item_list_response_with_pagination(self):
        """Test ItemListResponse with pagination."""
        from app.mcp_server.schemas import ItemListResponse, ItemRead, PaginationInfo

        items = [
            ItemRead(
                id=1,
                name="Sugar",
                category="Grocery",
                unit="kg",
                unit_price=Decimal("50.00"),
                stock_qty=Decimal("100.0"),
                is_active=True
            )
        ]
        pagination = PaginationInfo(page=1, limit=20, total=1, total_pages=1)

        response = ItemListResponse(items=items, pagination=pagination)
        assert len(response.items) == 1
        assert response.pagination.total == 1


class TestBillCreate:
    """Tests for BillCreate schema."""

    def test_bill_create_success(self):
        """Test creating a bill."""
        from app.mcp_server.schemas import BillCreate, BillItemCreate

        bill = BillCreate(
            customer_name="John Doe",
            store_name="Downtown Store",
            items=[BillItemCreate(item_id=1, quantity=5)]
        )

        assert bill.customer_name == "John Doe"
        assert len(bill.items) == 1

    def test_bill_create_requires_items(self):
        """Test that bills require at least one item."""
        from app.mcp_server.schemas import BillCreate

        with pytest.raises(ValidationError):
            BillCreate(
                customer_name="John",
                store_name="Store",
                items=[]
            )

    def test_bill_create_validates_quantities(self):
        """Test quantity validation in bill items."""
        from app.mcp_server.schemas import BillCreate, BillItemCreate

        with pytest.raises(ValidationError):
            BillCreate(
                customer_name="John",
                store_name="Store",
                items=[BillItemCreate(item_id=1, quantity=-5)]
            )


class TestBillRead:
    """Tests for BillRead schema."""

    def test_bill_read_creation(self):
        """Test creating a BillRead response."""
        from app.mcp_server.schemas import BillRead

        bill = BillRead(
            id=1,
            customer_name="John",
            store_name="Store",
            items=[],
            total_amount=Decimal("100.00"),
            created_at=datetime.now()
        )

        assert bill.id == 1
        assert bill.customer_name == "John"


class TestErrorCodes:
    """Tests for error code taxonomy."""

    def test_error_codes_defined(self):
        """Test that all required error codes are defined."""
        from app.mcp_server.schemas import ERROR_CODES

        required_codes = [
            "ITEM_NOT_FOUND",
            "INSUFFICIENT_STOCK",
            "VALIDATION_ERROR",
            "CATEGORY_INVALID",
        ]

        for code in required_codes:
            assert code in ERROR_CODES

    def test_error_codes_are_screaming_snake_case(self):
        """Test that error codes follow naming convention."""
        from app.mcp_server.schemas import ERROR_CODES

        for code in ERROR_CODES.values():
            assert code == code.upper()
            # Should be screaming snake case
            assert all(c.isupper() or c == "_" for c in code)
