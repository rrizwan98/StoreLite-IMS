"""
End-to-end workflow tests (Phase 7)
Tests complete user journeys: Add Item -> Search -> Create Invoice -> View Results
"""

import pytest
from decimal import Decimal
from src.models.item import Item
from src.models.bill import Bill, BillItem
from src.services.inventory_service import InventoryService
from src.services.billing_service import BillingService
from src.cli.error_handler import ValidationError, ItemNotFoundError


class TestE2EAddItemWorkflow:
    """Test complete add item workflow"""

    def test_e2e_add_single_item_and_verify(self, test_session):
        """Test: Add item -> Verify it exists in inventory"""
        inventory_service = InventoryService(test_session)

        # Step 1: Add item
        item = inventory_service.add_item(
            name="Test Product",
            category="Grocery",
            unit="piece",
            unit_price=Decimal("100.00"),
            stock_qty=Decimal("50")
        )

        # Step 2: Verify item was added
        retrieved_item = inventory_service.get_item(item.id)
        assert retrieved_item.name == "Test Product"
        assert retrieved_item.unit_price == Decimal("100.00")
        assert retrieved_item.stock_qty == Decimal("50")
        assert retrieved_item.is_active is True

    def test_e2e_add_multiple_items_and_list(self, test_session):
        """Test: Add multiple items -> List all -> Verify count"""
        inventory_service = InventoryService(test_session)

        # Step 1: Add 3 items
        items_data = [
            ("Sugar", "Grocery", Decimal("50.00"), Decimal("100")),
            ("Rice", "Grocery", Decimal("40.00"), Decimal("150")),
            ("Milk", "Grocery", Decimal("60.00"), Decimal("200")),
        ]

        added_items = []
        for name, category, price, stock in items_data:
            item = inventory_service.add_item(
                name=name,
                category=category,
                unit="piece",
                unit_price=price,
                stock_qty=stock
            )
            added_items.append(item)

        # Step 2: List all items
        all_items = inventory_service.list_items()

        # Step 3: Verify all items exist
        assert len(all_items) >= 3
        item_names = [item.name for item in all_items]
        assert "Sugar" in item_names
        assert "Rice" in item_names
        assert "Milk" in item_names


class TestE2ESearchWorkflow:
    """Test complete search workflow"""

    def test_e2e_add_items_then_search_by_name(self, test_session):
        """Test: Add items -> Search by name -> Verify results"""
        inventory_service = InventoryService(test_session)

        # Step 1: Add items
        item1 = inventory_service.add_item(
            name="Premium Sugar",
            category="Grocery",
            unit="piece",
            unit_price=Decimal("100.00"),
            stock_qty=Decimal("50")
        )
        item2 = inventory_service.add_item(
            name="Regular Sugar",
            category="Grocery",
            unit="piece",
            unit_price=Decimal("80.00"),
            stock_qty=Decimal("100")
        )

        # Step 2: Search by name
        results = inventory_service.search_items("Sugar")

        # Step 3: Verify search results
        assert len(results) >= 2
        names = [item.name for item in results]
        assert "Premium Sugar" in names
        assert "Regular Sugar" in names

    def test_e2e_add_items_then_search_by_category(self, test_session):
        """Test: Add items with categories -> Search by category"""
        inventory_service = InventoryService(test_session)

        # Step 1: Add items in different categories
        grocery_items = [
            inventory_service.add_item(
                name="Rice",
                category="Grocery",
                unit="piece",
                unit_price=Decimal("40.00"),
                stock_qty=Decimal("100")
            ),
            inventory_service.add_item(
                name="Oil",
                category="Grocery",
                unit="piece",
                unit_price=Decimal("200.00"),
                stock_qty=Decimal("50")
            ),
        ]

        beauty_items = [
            inventory_service.add_item(
                name="Shampoo",
                category="Beauty",
                unit="piece",
                unit_price=Decimal("150.00"),
                stock_qty=Decimal("30")
            ),
        ]

        # Step 2: Search by category
        grocery_results = inventory_service.search_by_category("Grocery")

        # Step 3: Verify category search
        assert len(grocery_results) >= 2
        category_names = [item.name for item in grocery_results]
        assert "Rice" in category_names
        assert "Oil" in category_names

    def test_e2e_add_items_then_search_by_price_range(self, test_session):
        """Test: Add items with prices -> Search by price range"""
        inventory_service = InventoryService(test_session)

        # Step 1: Add items with various prices
        cheap = inventory_service.add_item(
            name="Budget Item",
            category="Grocery",
            unit="piece",
            unit_price=Decimal("25.00"),
            stock_qty=Decimal("100")
        )
        medium = inventory_service.add_item(
            name="Standard Item",
            category="Grocery",
            unit="piece",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("100")
        )
        expensive = inventory_service.add_item(
            name="Premium Item",
            category="Grocery",
            unit="piece",
            unit_price=Decimal("200.00"),
            stock_qty=Decimal("50")
        )

        # Step 2: Search price range 40-100
        results = inventory_service.search_by_price_range(
            Decimal("40.00"),
            Decimal("100.00")
        )

        # Step 3: Verify price range results
        result_names = [item.name for item in results]
        assert "Standard Item" in result_names
        # Budget item at 25 should not be in results
        # Premium item at 200 should not be in results


class TestE2ESoftDeleteWorkflow:
    """Test soft delete workflow"""

    def test_e2e_add_item_then_soft_delete_then_verify_inactive(self, test_session):
        """Test: Add item -> Soft delete -> Verify marked inactive"""
        inventory_service = InventoryService(test_session)

        # Step 1: Add item
        item = inventory_service.add_item(
            name="Temporary Item",
            category="Grocery",
            unit="piece",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("100")
        )
        item_id = item.id

        # Step 2: Verify item is active
        active_item = inventory_service.get_item(item_id)
        assert active_item.is_active is True

        # Step 3: Soft delete item
        updated_item = inventory_service.update_item(item_id, is_active=False)

        # Step 4: Verify item marked inactive
        assert updated_item.is_active is False

        # Step 5: List should exclude inactive items
        all_active = inventory_service.list_items()
        active_ids = [i.id for i in all_active]
        assert item_id not in active_ids

    def test_e2e_soft_deleted_item_not_in_search_results(self, test_session):
        """Test: Add item -> Delete -> Not in search results"""
        inventory_service = InventoryService(test_session)

        # Step 1: Add item
        item = inventory_service.add_item(
            name="Search Test Item",
            category="Grocery",
            unit="piece",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("100")
        )

        # Step 2: Verify in search
        results = inventory_service.search_items("Search Test Item")
        assert len(results) >= 1

        # Step 3: Soft delete
        inventory_service.update_item(item.id, is_active=False)

        # Step 4: Verify not in search results
        results_after = inventory_service.search_items("Search Test Item")
        result_ids = [i.id for i in results_after]
        assert item.id not in result_ids


class TestE2EBillingWorkflow:
    """Test complete billing workflow"""

    def test_e2e_add_items_then_create_bill_then_verify_deduction(self, test_session):
        """Test: Add items -> Create bill -> Verify stock deducted"""
        inventory_service = InventoryService(test_session)
        billing_service = BillingService(test_session)

        # Step 1: Add items to inventory
        item1 = inventory_service.add_item(
            name="Sugar",
            category="Grocery",
            unit="piece",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("100")
        )
        item2 = inventory_service.add_item(
            name="Rice",
            category="Grocery",
            unit="piece",
            unit_price=Decimal("40.00"),
            stock_qty=Decimal("150")
        )

        # Step 2: Create bill
        billing_service.create_bill_draft()
        billing_service.add_to_cart(item1.id, Decimal("10"))
        billing_service.add_to_cart(item2.id, Decimal("20"))

        # Step 3: Confirm bill
        bill = billing_service.confirm_bill(
            customer_name="Test Customer",
            store_name="Test Store"
        )

        # Step 4: Verify bill created
        assert bill.customer_name == "Test Customer"
        assert bill.store_name == "Test Store"
        assert len(bill.bill_items) == 2
        assert bill.total_amount == Decimal("1300.00")  # 50*10 + 40*20

        # Step 5: Verify stock deducted
        updated_item1 = inventory_service.get_item(item1.id)
        updated_item2 = inventory_service.get_item(item2.id)
        assert updated_item1.stock_qty == Decimal("90")  # 100 - 10
        assert updated_item2.stock_qty == Decimal("130")  # 150 - 20

    def test_e2e_multi_cart_operations_then_bill(self, test_session):
        """Test: Add items -> Update quantities -> Remove items -> Bill"""
        inventory_service = InventoryService(test_session)
        billing_service = BillingService(test_session)

        # Step 1: Add items
        item = inventory_service.add_item(
            name="Test Item",
            category="Grocery",
            unit="piece",
            unit_price=Decimal("100.00"),
            stock_qty=Decimal("100")
        )

        # Step 2: Create cart
        billing_service.create_bill_draft()

        # Step 3: Add item
        billing_service.add_to_cart(item.id, Decimal("5"))
        cart = billing_service.get_cart()
        assert len(cart) == 1

        # Step 4: Update quantity
        updated = billing_service.update_cart_item_quantity(item.id, Decimal("10"))
        assert updated["quantity"] == Decimal("10")

        # Step 5: Verify cart reflects update
        cart = billing_service.get_cart()
        assert cart[0]["quantity"] == Decimal("10")
        assert cart[0]["line_total"] == Decimal("1000.00")

        # Step 6: Confirm bill
        bill = billing_service.confirm_bill()
        assert bill.total_amount == Decimal("1000.00")

    def test_e2e_cannot_bill_with_insufficient_stock(self, test_session):
        """Test: Try to bill with quantity exceeding stock -> Error"""
        inventory_service = InventoryService(test_session)
        billing_service = BillingService(test_session)

        # Step 1: Add item with limited stock
        item = inventory_service.add_item(
            name="Limited Item",
            category="Grocery",
            unit="piece",
            unit_price=Decimal("100.00"),
            stock_qty=Decimal("5")
        )

        # Step 2: Try to add more than available
        billing_service.create_bill_draft()

        with pytest.raises(ValidationError, match="Insufficient stock"):
            billing_service.add_to_cart(item.id, Decimal("10"))


class TestE2ECompleteJourney:
    """Test full system journey: Add -> Search -> Update -> Bill -> Verify"""

    def test_e2e_complete_system_journey(self, test_session):
        """
        Complete journey:
        1. Add 3 items with different prices
        2. Search by category
        3. Update prices
        4. Create bill with items
        5. Verify all changes
        """
        inventory_service = InventoryService(test_session)
        billing_service = BillingService(test_session)

        # Step 1: Add items
        items = []
        original_stocks = []
        for i in range(3):
            item = inventory_service.add_item(
                name=f"Item {i+1}",
                category="Grocery",
                unit="piece",
                unit_price=Decimal(f"{50 + i*20}.00"),
                stock_qty=Decimal(f"{100 + i*50}")
            )
            items.append(item)
            original_stocks.append(item.stock_qty)

        # Step 2: Search by category
        grocery_items = inventory_service.search_by_category("Grocery")
        assert len(grocery_items) >= 3

        # Step 3: Update first item's price
        updated = inventory_service.update_item(items[0].id, unit_price=Decimal("75.00"))
        assert updated.unit_price == Decimal("75.00")

        # Step 4: Create bill with all items
        billing_service.create_bill_draft()
        for item in items:
            billing_service.add_to_cart(item.id, Decimal("5"))

        # Step 5: Verify cart total
        total = billing_service.calculate_bill_total()
        # Item 1: 75*5 = 375, Item 2: 70*5 = 350, Item 3: 90*5 = 450
        assert total == Decimal("1175.00")

        # Step 6: Confirm bill
        bill = billing_service.confirm_bill(customer_name="Journey Test")
        assert bill.customer_name == "Journey Test"
        assert len(bill.bill_items) == 3

        # Step 7: Verify stock deducted for all
        for idx, item in enumerate(items):
            updated_item = inventory_service.get_item(item.id)
            assert updated_item.stock_qty == original_stocks[idx] - Decimal("5")
