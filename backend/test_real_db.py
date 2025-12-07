"""
End-to-end test with real database
Tests adding items and creating bills
"""

import sys
import os
from decimal import Decimal
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.db import get_db
from src.models.item import Item
from src.models.bill import Bill, BillItem
from src.services.inventory_service import InventoryService
from src.services.billing_service import BillingService
from sqlalchemy import text


def test_database_connection():
    """Test database connection"""
    print("\n" + "="*60)
    print("TEST 1: Database Connection")
    print("="*60)

    try:
        db = get_db()
        if db.health_check():
            print("[PASS] Database connection successful!")
            return True
        else:
            print("[FAIL] Database health check failed")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        return False


def test_create_schema():
    """Test creating database schema"""
    print("\n" + "="*60)
    print("TEST 2: Create Database Schema")
    print("="*60)

    try:
        db = get_db()

        with db.session_scope() as session:
            # Drop existing tables
            session.execute(text("DROP TABLE IF EXISTS bill_items CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS bills CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS items CASCADE"))
            session.commit()
            print("[PASS] Dropped existing tables")

            # Read and execute schema
            schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
            with open(schema_path, "r") as f:
                schema = f.read()

            statements = [s.strip() for s in schema.split(";") if s.strip()]
            for statement in statements:
                session.execute(text(statement))
            session.commit()
            print(f"[PASS] Created schema with {len(statements)} statements")

        return True
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        return False


def test_add_items():
    """Test adding items to inventory"""
    print("\n" + "="*60)
    print("TEST 3: Add Items to Inventory")
    print("="*60)

    try:
        db = get_db()

        with db.session_scope() as session:
            inventory_service = InventoryService(session)

            # Add first item
            item1 = inventory_service.add_item(
                name="Sugar",
                category="Grocery",
                unit="kg",
                unit_price=Decimal("50.00"),
                stock_qty=Decimal("100")
            )
            print(f"[PASS] Added Item 1: Sugar (ID: {item1.id})")

            # Add second item
            item2 = inventory_service.add_item(
                name="Rice",
                category="Grocery",
                unit="kg",
                unit_price=Decimal("40.00"),
                stock_qty=Decimal("150")
            )
            print(f"[PASS] Added Item 2: Rice (ID: {item2.id})")

            # Add third item
            item3 = inventory_service.add_item(
                name="Oil",
                category="Grocery",
                unit="liter",
                unit_price=Decimal("200.00"),
                stock_qty=Decimal("50")
            )
            print(f"[PASS] Added Item 3: Oil (ID: {item3.id})")

            return [item1, item2, item3]
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_list_items():
    """Test listing items"""
    print("\n" + "="*60)
    print("TEST 4: List Items")
    print("="*60)

    try:
        db = get_db()

        with db.session_scope() as session:
            inventory_service = InventoryService(session)
            items = inventory_service.list_items()

            print(f"[PASS] Listed {len(items)} items:")
            for item in items:
                print(f"   - {item.name}: {item.unit_price} {item.unit} (Stock: {item.stock_qty})")

            return items
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        return None


def test_create_bill(items):
    """Test creating a bill"""
    print("\n" + "="*60)
    print("TEST 5: Create Bill Draft")
    print("="*60)

    try:
        db = get_db()

        with db.session_scope() as session:
            billing_service = BillingService(session)

            # Create bill draft (initializes empty cart)
            billing_service.create_bill_draft()
            print(f"[PASS] Created Bill Draft (empty cart initialized)")

            return billing_service
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_add_items_to_bill(items):
    """Test adding items to bill"""
    print("\n" + "="*60)
    print("TEST 6: Add Items to Bill (Cart)")
    print("="*60)

    try:
        db = get_db()

        with db.session_scope() as session:
            billing_service = BillingService(session)
            billing_service.create_bill_draft()

            # Add items to cart
            bill_item1 = billing_service.add_to_cart(
                item_id=items[0].id,  # Sugar
                quantity=Decimal("2")
            )
            print(f"[PASS] Added to cart: 2x {items[0].name}")

            bill_item2 = billing_service.add_to_cart(
                item_id=items[1].id,  # Rice
                quantity=Decimal("3")
            )
            print(f"[PASS] Added to cart: 3x {items[1].name}")

            bill_item3 = billing_service.add_to_cart(
                item_id=items[2].id,  # Oil
                quantity=Decimal("1")
            )
            print(f"[PASS] Added to cart: 1x {items[2].name}")

            return billing_service
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_view_cart(billing_service):
    """Test viewing cart"""
    print("\n" + "="*60)
    print("TEST 7: View Cart")
    print("="*60)

    try:
        cart = billing_service.get_cart()

        print(f"[PASS] Cart Items ({len(cart)} items):")
        total = Decimal("0")
        for item in cart:
            subtotal = item["quantity"] * item["unit_price"]
            total += subtotal
            print(f"   - {item['item_name']}: {item['quantity']} x {item['unit_price']} = {subtotal}")

        print(f"\n[PASS] Cart Total: {total}")
        return total
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        return None


def test_confirm_bill(billing_service):
    """Test confirming bill (finalize)"""
    print("\n" + "="*60)
    print("TEST 8: Confirm & Finalize Bill")
    print("="*60)

    try:
        final_bill = billing_service.confirm_bill(
            customer_name="John Doe",
            store_name="Store A"
        )
        print(f"[PASS] Bill finalized!")
        print(f"   - Bill ID: {final_bill.id}")
        print(f"   - Customer: {final_bill.customer_name}")
        print(f"   - Store: {final_bill.store_name}")
        print(f"   - Total Amount: {final_bill.total_amount}")
        print(f"   - Created At: {final_bill.created_at}")

        return final_bill
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_search_items():
    """Test searching items"""
    print("\n" + "="*60)
    print("TEST 9: Search Items")
    print("="*60)

    try:
        db = get_db()

        with db.session_scope() as session:
            inventory_service = InventoryService(session)

            results = inventory_service.search_items("Sugar")
            print(f"[PASS] Searched for 'Sugar': Found {len(results)} items")
            for item in results:
                print(f"   - {item.name}: {item.unit_price} {item.unit}")

            return results
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        return None


def test_update_item(items):
    """Test updating item"""
    print("\n" + "="*60)
    print("TEST 10: Update Item")
    print("="*60)

    try:
        db = get_db()

        with db.session_scope() as session:
            inventory_service = InventoryService(session)

            item_id = items[0].id
            old_price = items[0].unit_price
            new_price = Decimal("55.00")

            updated_item = inventory_service.update_item(
                item_id=item_id,
                unit_price=new_price
            )

            print(f"[PASS] Updated Item {item_id} ({updated_item.name})")
            print(f"   - Old Price: {old_price}")
            print(f"   - New Price: {updated_item.unit_price}")

            return updated_item
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("IMS END-TO-END DATABASE TEST SUITE")
    print("="*60)

    results = {
        "connection": test_database_connection(),
        "schema": test_create_schema(),
    }

    if not results["schema"]:
        print("\n[FAIL] Failed to create schema. Stopping tests.")
        return

    # Use a single session for all subsequent operations
    db = get_db()
    with db.session_scope() as session:
        inventory_service = InventoryService(session)

        # Add items
        try:
            print("\n" + "="*60)
            print("TEST 3: Add Items to Inventory")
            print("="*60)

            item1 = inventory_service.add_item(
                name="Sugar",
                category="Grocery",
                unit="kg",
                unit_price=Decimal("50.00"),
                stock_qty=Decimal("100")
            )
            print(f"[PASS] Added Item 1: Sugar (ID: {item1.id})")

            item2 = inventory_service.add_item(
                name="Rice",
                category="Grocery",
                unit="kg",
                unit_price=Decimal("40.00"),
                stock_qty=Decimal("150")
            )
            print(f"[PASS] Added Item 2: Rice (ID: {item2.id})")

            item3 = inventory_service.add_item(
                name="Oil",
                category="Grocery",
                unit="liter",
                unit_price=Decimal("200.00"),
                stock_qty=Decimal("50")
            )
            print(f"[PASS] Added Item 3: Oil (ID: {item3.id})")

            items = [item1, item2, item3]
            results["list"] = True
        except Exception as e:
            print(f"[FAIL] Error adding items: {str(e)}")
            import traceback
            traceback.print_exc()
            return

        # List items
        try:
            print("\n" + "="*60)
            print("TEST 4: List Items")
            print("="*60)

            items_list = inventory_service.list_items()
            print(f"[PASS] Listed {len(items_list)} items:")
            for item in items_list:
                print(f"   - {item.name}: {item.unit_price} {item.unit} (Stock: {item.stock_qty})")
            results["list"] = True
        except Exception as e:
            print(f"[FAIL] Error listing items: {str(e)}")
            results["list"] = False

        # Search items
        try:
            print("\n" + "="*60)
            print("TEST 9: Search Items")
            print("="*60)

            results_search = inventory_service.search_items("Sugar")
            print(f"[PASS] Searched for 'Sugar': Found {len(results_search)} items")
            for item in results_search:
                print(f"   - {item.name}: {item.unit_price} {item.unit}")
            results["search"] = True
        except Exception as e:
            print(f"[FAIL] Error searching items: {str(e)}")
            results["search"] = False

        # Update item
        try:
            print("\n" + "="*60)
            print("TEST 10: Update Item")
            print("="*60)

            item_id = items[0].id
            old_price = items[0].unit_price
            new_price = Decimal("55.00")

            updated_item = inventory_service.update_item(
                item_id=item_id,
                unit_price=new_price
            )

            print(f"[PASS] Updated Item {item_id} ({updated_item.name})")
            print(f"   - Old Price: {old_price}")
            print(f"   - New Price: {updated_item.unit_price}")
            results["update"] = True
        except Exception as e:
            print(f"[FAIL] Error updating item: {str(e)}")
            results["update"] = False

        # Billing operations - all in same session
        try:
            print("\n" + "="*60)
            print("TEST 5: Create Bill Draft")
            print("="*60)

            billing_service = BillingService(session)
            billing_service.create_bill_draft()
            print(f"[PASS] Created Bill Draft (empty cart initialized)")
            results["create_bill"] = True
        except Exception as e:
            print(f"[FAIL] Error creating bill draft: {str(e)}")
            results["create_bill"] = False
            return

        # Add items to cart
        try:
            print("\n" + "="*60)
            print("TEST 6: Add Items to Bill (Cart)")
            print("="*60)

            bill_item1 = billing_service.add_to_cart(
                item_id=items[0].id,  # Sugar
                quantity=Decimal("2")
            )
            print(f"[PASS] Added to cart: 2x {items[0].name}")

            bill_item2 = billing_service.add_to_cart(
                item_id=items[1].id,  # Rice
                quantity=Decimal("3")
            )
            print(f"[PASS] Added to cart: 3x {items[1].name}")

            bill_item3 = billing_service.add_to_cart(
                item_id=items[2].id,  # Oil
                quantity=Decimal("1")
            )
            print(f"[PASS] Added to cart: 1x {items[2].name}")
            results["add_to_bill"] = True
        except Exception as e:
            print(f"[FAIL] Error adding items to bill: {str(e)}")
            import traceback
            traceback.print_exc()
            results["add_to_bill"] = False
            return

        # View cart
        try:
            print("\n" + "="*60)
            print("TEST 7: View Cart")
            print("="*60)

            cart = billing_service.get_cart()
            print(f"[PASS] Cart Items ({len(cart)} items):")
            total = Decimal("0")
            for item in cart:
                subtotal = item["quantity"] * item["unit_price"]
                total += subtotal
                print(f"   - {item['item_name']}: {item['quantity']} x {item['unit_price']} = {subtotal}")

            print(f"\n[PASS] Cart Total: {total}")
            results["view_cart"] = True
        except Exception as e:
            print(f"[FAIL] Error viewing cart: {str(e)}")
            results["view_cart"] = False

        # Confirm bill
        try:
            print("\n" + "="*60)
            print("TEST 8: Confirm & Finalize Bill")
            print("="*60)

            final_bill = billing_service.confirm_bill(
                customer_name="John Doe",
                store_name="Store A"
            )
            print(f"[PASS] Bill finalized!")
            print(f"   - Bill ID: {final_bill.id}")
            print(f"   - Customer: {final_bill.customer_name}")
            print(f"   - Store: {final_bill.store_name}")
            print(f"   - Total Amount: {final_bill.total_amount}")
            print(f"   - Created At: {final_bill.created_at}")
            results["confirm"] = True
        except Exception as e:
            print(f"[FAIL] Error confirming bill: {str(e)}")
            import traceback
            traceback.print_exc()
            results["confirm"] = False

    # Final summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n[PASS] PASSED: {passed}/{total} tests")

    for test_name, result in results.items():
        status = "[PASS] PASS" if result else "[FAIL] FAIL"
        print(f"  {status}: {test_name}")

    if passed == total:
        print("\n*** ALL TESTS PASSED!")
    else:
        print(f"\n[WARN]  {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
