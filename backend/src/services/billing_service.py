"""
Billing and invoice management service
"""

import logging
from decimal import Decimal
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from ..models.bill import Bill, BillItem
from ..models.item import Item
from .validation import ValidationService
from .inventory_service import InventoryService
from ..cli.error_handler import ValidationError, ItemNotFoundError, BillingError, DatabaseError

logger = logging.getLogger(__name__)


class BillingService:
    """Service for managing billing and invoice operations"""

    def __init__(self, session: Session):
        """
        Initialize service with database session

        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.inventory_service = InventoryService(session)
        self.cart: List[Dict] = []

    def create_bill_draft(self) -> None:
        """Initialize a new bill draft (empty cart)"""
        self.cart = []
        logger.info("Bill draft created")

    def add_to_cart(self, item_id: int, quantity: str | float | Decimal) -> Dict:
        """
        Add item to cart

        Args:
            item_id: Item ID
            quantity: Quantity to add

        Returns:
            Dictionary with cart item details

        Raises:
            ValidationError: If validation fails
            ItemNotFoundError: If item not found
        """
        # Validate quantity
        is_valid, error_msg = ValidationService.validate_quantity(quantity)
        if not is_valid:
            raise ValidationError(error_msg)

        quantity_decimal = Decimal(str(quantity))

        # Get item
        item = self.inventory_service.get_item(item_id)

        # Check stock
        if item.stock_qty < quantity_decimal:
            raise ValidationError(
                f"Insufficient stock for {item.name}. "
                f"Available: {item.stock_qty}, Requested: {quantity_decimal}"
            )

        # Calculate line total
        line_total = item.unit_price * quantity_decimal

        # Create cart item
        cart_item = {
            "item_id": item.id,
            "item_name": item.name,
            "unit": item.unit,
            "quantity": quantity_decimal,
            "unit_price": item.unit_price,
            "line_total": line_total,
        }

        self.cart.append(cart_item)
        logger.info(f"Item added to cart: {item.name} (qty: {quantity_decimal})")
        return cart_item

    def get_cart(self) -> List[Dict]:
        """Get current cart contents"""
        return self.cart.copy()

    def clear_cart(self) -> None:
        """Clear the cart"""
        self.cart = []
        logger.info("Cart cleared")

    def calculate_bill_total(self) -> Decimal:
        """
        Calculate total bill amount

        Returns:
            Total amount
        """
        total = Decimal("0")
        for item in self.cart:
            total += item["line_total"]
        return total

    def confirm_bill(
        self,
        customer_name: Optional[str] = None,
        store_name: Optional[str] = None,
    ) -> Bill:
        """
        Confirm and create bill

        Args:
            customer_name: Optional customer name
            store_name: Optional store name

        Returns:
            Created Bill object

        Raises:
            ValidationError: If cart is empty or validation fails
            BillingError: If billing operation fails
            DatabaseError: If database operation fails
        """
        if not self.cart:
            raise ValidationError("Cart is empty. Add items before confirming bill.")

        try:
            # Validate all items have stock before proceeding
            for cart_item in self.cart:
                item = self.inventory_service.get_item(cart_item["item_id"])
                if item.stock_qty < cart_item["quantity"]:
                    raise ValidationError(
                        f"Insufficient stock for {item.name}. "
                        f"Available: {item.stock_qty}, Requested: {cart_item['quantity']}"
                    )

            # Calculate total
            total_amount = self.calculate_bill_total()

            # Create bill
            bill = Bill(
                customer_name=customer_name if customer_name else None,
                store_name=store_name if store_name else None,
                total_amount=total_amount,
            )
            self.session.add(bill)
            self.session.flush()  # Get bill ID

            # Create bill items and deduct stock
            for cart_item in self.cart:
                bill_item = BillItem(
                    bill_id=bill.id,
                    item_id=cart_item["item_id"],
                    item_name=cart_item["item_name"],
                    unit_price=cart_item["unit_price"],
                    quantity=cart_item["quantity"],
                    line_total=cart_item["line_total"],
                )
                self.session.add(bill_item)

                # Deduct stock
                self.inventory_service.deduct_stock(
                    cart_item["item_id"],
                    cart_item["quantity"]
                )

            self.session.flush()
            logger.info(f"Bill created: {bill.id} with {len(self.cart)} items, total: {total_amount}")

            # Clear cart after successful bill
            self.clear_cart()
            return bill

        except (ValidationError, ItemNotFoundError):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to create bill: {e}")
            raise DatabaseError(f"Failed to create bill: {str(e)}")
