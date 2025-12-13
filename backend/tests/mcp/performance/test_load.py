"""
Task 43: Performance testing - Verify tools respond within <500ms
"""
import pytest
import asyncio
import time
import sys
import os
from decimal import Decimal

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.mcp_server.tools_inventory import (
    inventory_add_item,
    inventory_update_item,
    inventory_delete_item,
    inventory_list_items,
)
from app.mcp_server.tools_billing import (
    billing_create_bill,
    billing_get_bill,
    billing_list_bills,
)


class TestInventoryToolPerformance:
    """Test performance of inventory tools."""

    @pytest.mark.asyncio
    async def test_inventory_add_item_under_500ms(self, test_session):
        """Verify inventory_add_item completes in <500ms."""
        start_time = time.time()

        result = await inventory_add_item(
            name="Test Item",
            category="Grocery",
            unit="kg",
            unit_price=Decimal("10.00"),
            stock_qty=Decimal("100.0"),
            session=test_session
        )

        elapsed_ms = (time.time() - start_time) * 1000
        assert elapsed_ms < 500, f"inventory_add_item took {elapsed_ms:.2f}ms (expected <500ms)"
        assert result["id"] > 0
        assert result["name"] == "Test Item"

    @pytest.mark.asyncio
    async def test_inventory_update_item_under_500ms(self, test_session, sample_items):
        """Verify inventory_update_item completes in <500ms."""
        item = sample_items[0]

        start_time = time.time()

        result = await inventory_update_item(
            item_id=item.id,
            name="Updated Item",
            session=test_session
        )

        elapsed_ms = (time.time() - start_time) * 1000
        assert elapsed_ms < 500, f"inventory_update_item took {elapsed_ms:.2f}ms (expected <500ms)"
        assert result["name"] == "Updated Item"

    @pytest.mark.asyncio
    async def test_inventory_delete_item_under_500ms(self, test_session, sample_items):
        """Verify inventory_delete_item completes in <500ms."""
        item = sample_items[0]

        start_time = time.time()

        result = await inventory_delete_item(
            item_id=item.id,
            session=test_session
        )

        elapsed_ms = (time.time() - start_time) * 1000
        assert elapsed_ms < 500, f"inventory_delete_item took {elapsed_ms:.2f}ms (expected <500ms)"
        assert result["id"] == item.id

    @pytest.mark.asyncio
    async def test_inventory_list_items_under_500ms(self, test_session, sample_items):
        """Verify inventory_list_items completes in <500ms."""
        start_time = time.time()

        result = await inventory_list_items(
            page=1,
            limit=20,
            session=test_session
        )

        elapsed_ms = (time.time() - start_time) * 1000
        assert elapsed_ms < 500, f"inventory_list_items took {elapsed_ms:.2f}ms (expected <500ms)"
        assert "items" in result
        assert "pagination" in result


class TestBillingToolPerformance:
    """Test performance of billing tools."""

    @pytest.mark.asyncio
    async def test_billing_create_bill_under_500ms(self, test_session, sample_items):
        """Verify billing_create_bill completes in <500ms."""
        items = [
            {"item_id": sample_items[0].id, "quantity": Decimal("5")}
        ]

        start_time = time.time()

        result = await billing_create_bill(
            items=items,
            customer_name="Test Customer",
            store_name="Test Store",
            session=test_session
        )

        elapsed_ms = (time.time() - start_time) * 1000
        assert elapsed_ms < 500, f"billing_create_bill took {elapsed_ms:.2f}ms (expected <500ms)"
        assert result["id"] > 0
        assert len(result["items"]) == 1

    @pytest.mark.asyncio
    async def test_billing_list_bills_under_500ms(self, test_session, sample_bills):
        """Verify billing_list_bills completes in <500ms."""
        start_time = time.time()

        result = await billing_list_bills(
            page=1,
            limit=20,
            session=test_session
        )

        elapsed_ms = (time.time() - start_time) * 1000
        assert elapsed_ms < 500, f"billing_list_bills took {elapsed_ms:.2f}ms (expected <500ms)"
        assert "bills" in result
        assert "pagination" in result


class TestSequentialRequests:
    """Test sequential performance of tools."""

    @pytest.mark.asyncio
    async def test_sequential_inventory_operations(self, test_session):
        """Test multiple inventory operations in sequence."""
        start_time = time.time()

        # Run 5 sequential add_item operations
        results = []
        for i in range(5):
            result = await inventory_add_item(
                name=f"Item {i}",
                category="Grocery",
                unit="kg",
                unit_price=Decimal("10.00"),
                stock_qty=Decimal("100.0"),
                session=test_session
            )
            results.append(result)

        elapsed_ms = (time.time() - start_time) * 1000
        assert len(results) == 5
        assert elapsed_ms < 2500, f"5 sequential adds took {elapsed_ms:.2f}ms (expected <2500ms total)"

        # Verify all items were created
        for i, result in enumerate(results):
            assert result["name"] == f"Item {i}"

    @pytest.mark.asyncio
    async def test_sequential_billing_operations(self, test_session, sample_items):
        """Test multiple billing operations in sequence."""
        start_time = time.time()

        # Run 3 sequential bill creations
        results = []
        for i in range(3):
            result = await billing_create_bill(
                items=[
                    {"item_id": sample_items[0].id, "quantity": Decimal("2")}
                ],
                customer_name=f"Customer {i}",
                store_name="Test Store",
                session=test_session
            )
            results.append(result)

        elapsed_ms = (time.time() - start_time) * 1000
        assert len(results) == 3
        assert elapsed_ms < 1500, f"3 sequential bills took {elapsed_ms:.2f}ms (expected <1500ms total)"


class TestLoadTest:
    """Stress test with moderate volume requests."""

    @pytest.mark.asyncio
    async def test_high_volume_inventory_operations(self, test_session):
        """Test inventory operations under load (20 items sequentially)."""
        start_time = time.time()

        # Create 20 items sequentially
        results = []
        for i in range(20):
            result = await inventory_add_item(
                name=f"Bulk Item {i}",
                category="Grocery" if i % 2 == 0 else "Utilities",
                unit="kg",
                unit_price=Decimal("10.00"),
                stock_qty=Decimal("100.0"),
                session=test_session
            )
            results.append(result)

        elapsed_time = time.time() - start_time
        elapsed_ms = elapsed_time * 1000

        assert len(results) == 20
        assert elapsed_ms < 10000, f"20 sequential adds took {elapsed_ms:.2f}ms (expected <10000ms)"

        # Calculate average time per item
        avg_time_per_item = (elapsed_time / 20) * 1000
        assert avg_time_per_item < 500, f"Average time per item: {avg_time_per_item:.2f}ms (expected <500ms)"

    @pytest.mark.asyncio
    async def test_mixed_operation_performance(self, test_session, sample_items):
        """Test mixed operations (add, list, update, delete) in sequence."""
        start_time = time.time()

        # 1. Add item
        new_item = await inventory_add_item(
            name="Mixed Op Item",
            category="Grocery",
            unit="kg",
            unit_price=Decimal("15.00"),
            stock_qty=Decimal("50.0"),
            session=test_session
        )
        item_id = new_item["id"]

        # 2. List items
        list_result = await inventory_list_items(
            page=1,
            limit=20,
            session=test_session
        )

        # 3. Update item
        update_result = await inventory_update_item(
            item_id=item_id,
            name="Updated Mixed Op Item",
            session=test_session
        )

        # 4. Delete item
        delete_result = await inventory_delete_item(
            item_id=item_id,
            session=test_session
        )

        elapsed_ms = (time.time() - start_time) * 1000
        assert elapsed_ms < 2000, f"Mixed operations took {elapsed_ms:.2f}ms (expected <2000ms)"
        assert len(list_result["items"]) > 0
