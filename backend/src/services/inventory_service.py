"""
Inventory management service for items
"""

import logging
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..models.item import Item
from .validation import ValidationService
from ..cli.error_handler import ValidationError, ItemNotFoundError, DatabaseError

logger = logging.getLogger(__name__)


class InventoryService:
    """Service for managing inventory operations"""

    def __init__(self, session: Session):
        """
        Initialize service with database session

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def add_item(
        self,
        name: str,
        category: str,
        unit: str,
        unit_price: str | float | Decimal,
        stock_qty: str | float | Decimal,
    ) -> Item:
        """
        Add a new item to inventory

        Args:
            name: Item name
            category: Item category
            unit: Unit of measurement
            unit_price: Unit price
            stock_qty: Stock quantity

        Returns:
            Created Item object

        Raises:
            ValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        # Validate inputs
        is_valid, error_msg = ValidationService.validate_item_name(name)
        if not is_valid:
            raise ValidationError(error_msg)

        is_valid, error_msg = ValidationService.validate_category(category)
        if not is_valid:
            raise ValidationError(error_msg)

        is_valid, error_msg = ValidationService.validate_unit(unit)
        if not is_valid:
            raise ValidationError(error_msg)

        is_valid, error_msg = ValidationService.validate_price(unit_price)
        if not is_valid:
            raise ValidationError(error_msg)

        is_valid, error_msg = ValidationService.validate_non_negative(stock_qty)
        if not is_valid:
            raise ValidationError(error_msg)

        try:
            # Create and add item
            item = Item(
                name=name,
                category=category,
                unit=unit,
                unit_price=Decimal(str(unit_price)),
                stock_qty=Decimal(str(stock_qty)),
                is_active=True,
            )
            self.session.add(item)
            self.session.flush()  # Get ID without committing yet
            logger.info(f"Item added: {name} (ID: {item.id})")
            return item
        except Exception as e:
            logger.error(f"Failed to add item: {e}")
            raise DatabaseError(f"Failed to add item to database: {str(e)}")

    def list_items(self) -> List[Item]:
        """
        List all active items

        Returns:
            List of Item objects
        """
        try:
            items = self.session.query(Item).filter(Item.is_active == True).order_by(Item.name).all()
            logger.info(f"Listed {len(items)} items")
            return items
        except Exception as e:
            logger.error(f"Failed to list items: {e}")
            raise DatabaseError(f"Failed to retrieve items from database: {str(e)}")

    def get_item(self, item_id: int) -> Optional[Item]:
        """
        Get a single item by ID

        Args:
            item_id: Item ID

        Returns:
            Item object or None if not found
        """
        try:
            item = self.session.query(Item).filter(
                Item.id == item_id,
                Item.is_active == True
            ).first()
            if not item:
                raise ItemNotFoundError(f"Item with ID {item_id} not found")
            return item
        except ItemNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get item {item_id}: {e}")
            raise DatabaseError(f"Failed to retrieve item from database: {str(e)}")

    def search_items(self, query: str) -> List[Item]:
        """
        Search items by partial name (case-insensitive)

        Args:
            query: Search term

        Returns:
            List of matching Item objects
        """
        try:
            items = self.session.query(Item).filter(
                Item.name.ilike(f"%{query}%"),
                Item.is_active == True
            ).order_by(Item.name).all()
            logger.info(f"Search '{query}' returned {len(items)} items")
            return items
        except Exception as e:
            logger.error(f"Failed to search items: {e}")
            raise DatabaseError(f"Failed to search items: {str(e)}")

    def update_item(
        self,
        item_id: int,
        unit_price: Optional[str | float | Decimal] = None,
        stock_qty: Optional[str | float | Decimal] = None,
    ) -> Item:
        """
        Update item price and/or stock

        Args:
            item_id: Item ID
            unit_price: New unit price (optional)
            stock_qty: New stock quantity (optional)

        Returns:
            Updated Item object

        Raises:
            ValidationError: If validation fails
            ItemNotFoundError: If item not found
            DatabaseError: If database operation fails
        """
        try:
            item = self.get_item(item_id)

            # Validate and update price
            if unit_price is not None:
                is_valid, error_msg = ValidationService.validate_price(unit_price)
                if not is_valid:
                    raise ValidationError(error_msg)
                item.unit_price = Decimal(str(unit_price))

            # Validate and update stock
            if stock_qty is not None:
                is_valid, error_msg = ValidationService.validate_non_negative(stock_qty)
                if not is_valid:
                    raise ValidationError(error_msg)
                item.stock_qty = Decimal(str(stock_qty))

            self.session.flush()
            logger.info(f"Item updated: {item.id}")
            return item
        except (ValidationError, ItemNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to update item {item_id}: {e}")
            raise DatabaseError(f"Failed to update item: {str(e)}")

    def deduct_stock(self, item_id: int, quantity: Decimal) -> None:
        """
        Deduct stock from an item (used during bill creation)

        Args:
            item_id: Item ID
            quantity: Quantity to deduct

        Raises:
            ItemNotFoundError: If item not found
            ValidationError: If quantity is invalid or exceeds stock
            DatabaseError: If database operation fails
        """
        try:
            item = self.get_item(item_id)

            # Validate quantity
            is_valid, error_msg = ValidationService.validate_quantity(quantity)
            if not is_valid:
                raise ValidationError(error_msg)

            quantity_decimal = Decimal(str(quantity))

            # Check stock availability
            if item.stock_qty < quantity_decimal:
                raise ValidationError(
                    f"Insufficient stock for {item.name}. "
                    f"Available: {item.stock_qty}, Requested: {quantity_decimal}"
                )

            # Deduct stock
            item.stock_qty -= quantity_decimal
            self.session.flush()
            logger.info(f"Stock deducted for item {item_id}: -{quantity_decimal}")
        except (ValidationError, ItemNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to deduct stock for item {item_id}: {e}")
            raise DatabaseError(f"Failed to deduct stock: {str(e)}")

    def soft_delete_item(self, item_id: int) -> None:
        """
        Soft delete an item (mark as inactive)

        Args:
            item_id: Item ID

        Raises:
            ItemNotFoundError: If item not found
            DatabaseError: If database operation fails
        """
        try:
            item = self.session.query(Item).filter(Item.id == item_id).first()
            if not item:
                raise ItemNotFoundError(f"Item with ID {item_id} not found")

            item.is_active = False
            self.session.flush()
            logger.info(f"Item soft deleted: {item_id}")
        except ItemNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete item {item_id}: {e}")
            raise DatabaseError(f"Failed to delete item: {str(e)}")
