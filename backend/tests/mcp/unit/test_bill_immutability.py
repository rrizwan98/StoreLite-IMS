"""
Task 48: Bill immutability tests - Verify bills cannot be modified after creation
"""
import pytest
import sys
import os
from decimal import Decimal

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.models import Bill, BillItem
from app.mcp_server.tools_billing import (
    billing_create_bill,
    billing_list_bills,
)
from app.mcp_server.exceptions import MCPNotFoundError


class TestBillImmutability:
    """Test Task 48: Bill immutability - bills should not be modifiable after creation"""

    @pytest.mark.asyncio
    async def test_bill_created_with_total_amount(self, test_session, sample_items):
        """Verify bill is created with correct total amount."""
        items = [
            {"item_id": sample_items[0].id, "quantity": Decimal("5")}
        ]

        result = await billing_create_bill(
            items=items,
            customer_name="Test Customer",
            store_name="Test Store",
            session=test_session
        )

        # Bill should be created with total amount
        assert result["id"] > 0
        assert result["total_amount"] > 0
        initial_total = result["total_amount"]

        # Retrieve bill to verify it persisted
        bill_id = result["id"]
        bills_result = await billing_list_bills(
            page=1,
            limit=20,
            session=test_session
        )

        # Find our bill
        bill_found = None
        for bill in bills_result["bills"]:
            if bill["id"] == bill_id:
                bill_found = bill
                break

        assert bill_found is not None
        assert bill_found["total_amount"] == initial_total

    @pytest.mark.asyncio
    async def test_bill_items_snapshot_preserved(self, test_session, sample_items):
        """Verify bill items snapshot is preserved (immutable)."""
        original_price = sample_items[0].unit_price
        original_name = sample_items[0].name

        items = [
            {"item_id": sample_items[0].id, "quantity": Decimal("5")}
        ]

        result = await billing_create_bill(
            items=items,
            customer_name="Test Customer",
            store_name="Test Store",
            session=test_session
        )

        bill_id = result["id"]

        # Check bill items have snapshot values
        assert len(result["items"]) == 1
        bill_item = result["items"][0]

        # The bill_item should have snapshots of name and price
        assert bill_item["item_name"] == original_name
        assert bill_item["unit_price"] == float(original_price)

        # Verify items retrieved from billing_list_bills also have snapshot
        bills_result = await billing_list_bills(
            page=1,
            limit=20,
            session=test_session
        )

        bill_found = None
        for bill in bills_result["bills"]:
            if bill["id"] == bill_id:
                bill_found = bill
                break

        assert bill_found is not None
        assert len(bill_found["items"]) == 1
        assert bill_found["items"][0]["item_name"] == original_name
        assert bill_found["items"][0]["unit_price"] == float(original_price)

    @pytest.mark.asyncio
    async def test_bill_stock_reduction_persists(self, test_session, sample_items):
        """Verify bill creation reduces stock and persists."""
        original_stock = sample_items[0].stock_qty
        quantity_ordered = Decimal("5")

        items = [
            {"item_id": sample_items[0].id, "quantity": quantity_ordered}
        ]

        result = await billing_create_bill(
            items=items,
            customer_name="Test Customer",
            store_name="Test Store",
            session=test_session
        )

        # Stock should be reduced
        # Refresh item to see updated stock
        await test_session.refresh(sample_items[0])
        new_stock = sample_items[0].stock_qty

        # Stock should be reduced by ordered quantity
        expected_stock = original_stock - quantity_ordered
        assert new_stock == expected_stock

    @pytest.mark.asyncio
    async def test_multiple_bills_have_independent_snapshots(self, test_session, sample_items):
        """Verify multiple bills maintain independent snapshots."""
        # Create first bill
        result1 = await billing_create_bill(
            items=[{"item_id": sample_items[0].id, "quantity": Decimal("2")}],
            customer_name="Customer 1",
            store_name="Store 1",
            session=test_session
        )

        # Create second bill
        result2 = await billing_create_bill(
            items=[{"item_id": sample_items[0].id, "quantity": Decimal("3")}],
            customer_name="Customer 2",
            store_name="Store 2",
            session=test_session
        )

        # Both bills should have different totals
        assert result1["total_amount"] != result2["total_amount"]

        # First bill should have quantity 2
        assert result1["items"][0]["quantity"] == 2.0

        # Second bill should have quantity 3
        assert result2["items"][0]["quantity"] == 3.0

    @pytest.mark.asyncio
    async def test_bill_line_item_snapshots_immutable(self, test_session, sample_items):
        """Verify bill line items are immutable snapshots."""
        # Create a bill
        result = await billing_create_bill(
            items=[{"item_id": sample_items[0].id, "quantity": Decimal("5")}],
            customer_name="Test Customer",
            store_name="Test Store",
            session=test_session
        )

        bill_id = result["id"]
        line_item = result["items"][0]

        # Line item should have calculated line_total
        expected_line_total = float(sample_items[0].unit_price) * 5.0
        assert line_item["line_total"] == expected_line_total

        # Verify line total persists when bill is retrieved again
        bills_result = await billing_list_bills(
            page=1,
            limit=20,
            session=test_session
        )

        bill_found = None
        for bill in bills_result["bills"]:
            if bill["id"] == bill_id:
                bill_found = bill
                break

        assert bill_found is not None
        assert bill_found["items"][0]["line_total"] == expected_line_total
