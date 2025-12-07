"""
Inventory management service for items
"""

import logging
from decimal import Decimal
from typing import List, Optional, Union
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

    def search_by_category(self, category: str) -> List[Item]:
        """
        Search for items by category (case-insensitive)

        Args:
            category: Category name to search for

        Returns:
            List of active items matching the category
        """
        # Validate category exists
        valid_categories = ["Grocery", "Garments", "Beauty", "Utilities", "Other"]
        category_lower = category.lower()

        if category_lower not in [c.lower() for c in valid_categories]:
            return []  # Invalid category returns empty list

        # Search case-insensitive, only active items
        items = self.session.query(Item).filter(
            Item.is_active == True,
            Item.category.ilike(category)
        ).all()

        logger.info(f"Searched items by category '{category}': found {len(items)} items")
        return items

    def search_by_price_range(self, min_price: Decimal, max_price: Decimal) -> List[Item]:
        """
        Search for items by price range (inclusive)

        Args:
            min_price: Minimum unit price (inclusive)
            max_price: Maximum unit price (inclusive)

        Returns:
            List of active items within price range

        Raises:
            ValueError: If min_price > max_price
        """
        if min_price > max_price:
            raise ValueError("min_price must be <= max_price")

        # Search within price range, only active items
        items = self.session.query(Item).filter(
            Item.is_active == True,
            Item.unit_price >= min_price,
            Item.unit_price <= max_price
        ).all()

        logger.info(f"Searched items by price range [{min_price}-{max_price}]: found {len(items)} items")
        return items

    def update_item(
        self,
        item_id: int,
        name: Optional[str] = None,
        category: Optional[str] = None,
        unit: Optional[str] = None,
        unit_price: Optional[Union[str, float, Decimal]] = None,
        stock_qty: Optional[Union[str, float, Decimal]] = None,
        is_active: Optional[bool] = None,
    ) -> Item:
        """
        Update item fields

        Args:
            item_id: Item ID
            name: New name (optional)
            category: New category (optional)
            unit: New unit (optional)
            unit_price: New price (optional)
            stock_qty: New stock quantity (optional)
            is_active: New active status (optional) - False = soft delete

        Returns:
            Updated Item object

        Raises:
            ValidationError: If validation fails
            ItemNotFoundError: If item not found
            DatabaseError: If database operation fails
        """
        try:
            item = self.session.query(Item).filter(Item.id == item_id).first()
            if not item:
                raise ItemNotFoundError(f"Item {item_id} not found")

            # Update fields only if provided
            if name is not None:
                is_valid, error_msg = ValidationService.validate_item_name(name)
                if not is_valid:
                    raise ValidationError(error_msg)
                item.name = name

            if category is not None:
                is_valid, error_msg = ValidationService.validate_category(category)
                if not is_valid:
                    raise ValidationError(error_msg)
                item.category = category

            if unit is not None:
                is_valid, error_msg = ValidationService.validate_unit(unit)
                if not is_valid:
                    raise ValidationError(error_msg)
                item.unit = unit

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

            if is_active is not None:
                item.is_active = is_active

            self.session.flush()
            action = "deactivated" if is_active == False else "updated"
            logger.info(f"Item {item_id} {action}")
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
