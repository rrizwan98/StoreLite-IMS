"""
MCP tool implementations for inventory operations
"""
import logging
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Item
from app.mcp_server.exceptions import (
    MCPValidationError,
    MCPNotFoundError,
    MCPDatabaseError,
)
from app.mcp_server.utils import mcp_error_handler
from app.mcp_server.schemas import ItemRead, ItemListResponse, PaginationInfo

logger = logging.getLogger(__name__)


# ============================================================================
# Validation and conversion helpers (Task 19 REFACTOR)
# ============================================================================

VALID_CATEGORIES = {"Grocery", "Garments", "Beauty", "Utilities", "Other"}
VALID_UNITS = {"kg", "g", "liter", "ml", "piece", "box", "pack", "other"}


def validate_item_input(
    name: str,
    category: str,
    unit: str,
    unit_price: float,
    stock_qty: float
):
    """Validate item input fields."""
    if not name or len(name) > 255:
        raise MCPValidationError(
            "NAME_INVALID",
            "Name must be 1-255 characters"
        )

    if category not in VALID_CATEGORIES:
        raise MCPValidationError(
            "CATEGORY_INVALID",
            f"Category must be one of: {', '.join(sorted(VALID_CATEGORIES))}",
            {"category": category}
        )

    if unit not in VALID_UNITS:
        raise MCPValidationError(
            "UNIT_INVALID",
            f"Unit must be one of: {', '.join(sorted(VALID_UNITS))}",
            {"unit": unit}
        )

    if unit_price <= 0:
        raise MCPValidationError(
            "PRICE_INVALID",
            "Price must be > 0",
            {"unit_price": unit_price}
        )

    if stock_qty < 0:
        raise MCPValidationError(
            "QUANTITY_INVALID",
            "Stock qty must be >= 0",
            {"stock_qty": stock_qty}
        )


def convert_item_to_response(item_orm) -> dict:
    """Convert ORM Item to response dict."""
    if item_orm is None:
        return None

    return {
        "id": item_orm.id,
        "name": item_orm.name,
        "category": item_orm.category,
        "unit": item_orm.unit,
        "unit_price": float(item_orm.unit_price),
        "stock_qty": float(item_orm.stock_qty),
        "is_active": item_orm.is_active,
        "created_at": item_orm.created_at.isoformat() if item_orm.created_at else None,
        "updated_at": item_orm.updated_at.isoformat() if item_orm.updated_at else None,
    }


# ============================================================================
# Task 17-19: inventory_add_item (RED -> GREEN -> REFACTOR)
# ============================================================================

@mcp_error_handler("inventory_add_item")
async def inventory_add_item(
    name: str,
    category: str,
    unit: str,
    unit_price: float,
    stock_qty: float,
    session: AsyncSession
) -> dict:
    """Create new inventory item."""
    # Validate input
    validate_item_input(name, category, unit, unit_price, stock_qty)

    try:
        # Create item
        item = Item(
            name=name,
            category=category,
            unit=unit,
            unit_price=Decimal(str(unit_price)),
            stock_qty=Decimal(str(stock_qty)),
            is_active=True
        )

        session.add(item)
        await session.flush()  # Get the ID
        await session.commit()

        logger.info(f"Created item: {item.id} ({item.name})")
        return convert_item_to_response(item)

    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating item: {str(e)}")
        raise MCPDatabaseError("DATABASE_ERROR", str(e))


# ============================================================================
# Task 20-22: inventory_update_item (RED -> GREEN -> REFACTOR)
# ============================================================================

@mcp_error_handler("inventory_update_item")
async def inventory_update_item(
    item_id: int,
    name: str = None,
    category: str = None,
    unit: str = None,
    unit_price: float = None,
    stock_qty: float = None,
    session: AsyncSession = None
) -> dict:
    """Update inventory item (partial update allowed)."""
    try:
        # Get item
        stmt = select(Item).where(Item.id == item_id)
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise MCPNotFoundError("ITEM_NOT_FOUND", f"Item {item_id} not found")

        # Validate and update fields
        if name is not None:
            if not name or len(name) > 255:
                raise MCPValidationError(
                    "NAME_INVALID",
                    "Name must be 1-255 characters"
                )
            item.name = name

        if category is not None:
            if category not in VALID_CATEGORIES:
                raise MCPValidationError(
                    "CATEGORY_INVALID",
                    f"Category must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
                )
            item.category = category

        if unit is not None:
            if unit not in VALID_UNITS:
                raise MCPValidationError(
                    "UNIT_INVALID",
                    f"Unit must be one of: {', '.join(sorted(VALID_UNITS))}"
                )
            item.unit = unit

        if unit_price is not None:
            if unit_price <= 0:
                raise MCPValidationError("PRICE_INVALID", "Price must be > 0")
            item.unit_price = Decimal(str(unit_price))

        if stock_qty is not None:
            if stock_qty < 0:
                raise MCPValidationError("QUANTITY_INVALID", "Stock qty must be >= 0")
            item.stock_qty = Decimal(str(stock_qty))

        await session.commit()
        logger.info(f"Updated item: {item_id}")
        return convert_item_to_response(item)

    except MCPValidationError:
        await session.rollback()
        raise
    except MCPNotFoundError:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating item: {str(e)}")
        raise MCPDatabaseError("DATABASE_ERROR", str(e))


# ============================================================================
# Task 23-25: inventory_delete_item (RED -> GREEN -> REFACTOR)
# ============================================================================

@mcp_error_handler("inventory_delete_item")
async def inventory_delete_item(
    item_id: int,
    session: AsyncSession = None
) -> dict:
    """Soft delete inventory item (sets is_active = FALSE)."""
    try:
        # Get item
        stmt = select(Item).where(Item.id == item_id)
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise MCPNotFoundError("ITEM_NOT_FOUND", f"Item {item_id} not found")

        # Soft delete
        item.is_active = False
        await session.commit()

        logger.info(f"Soft deleted item: {item_id}")

        return {
            "id": item_id,
            "success": True
        }

    except MCPNotFoundError:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting item: {str(e)}")
        raise MCPDatabaseError("DATABASE_ERROR", str(e))


# ============================================================================
# Task 26-28: inventory_list_items (RED -> GREEN -> REFACTOR)
# ============================================================================

@mcp_error_handler("inventory_list_items")
async def inventory_list_items(
    name: str = None,
    category: str = None,
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = None
) -> dict:
    """
    List inventory items with optional filtering and pagination.

    Performance:
    - Single query with WHERE is_active=TRUE and optional filters
    - Pagination handled by OFFSET/LIMIT
    - Expected <100ms for typical inventory sizes
    """
    try:
        # Validate pagination
        if page < 1:
            page = 1
        if limit < 1:
            limit = 20
        if limit > 100:
            limit = 100

        # Build filter query
        stmt = select(Item).where(Item.is_active == True)

        if name:
            stmt = stmt.where(Item.name.ilike(f"%{name}%"))

        if category:
            stmt = stmt.where(Item.category == category)

        # Get total count
        count_stmt = select(Item).where(Item.is_active == True)
        if name:
            count_stmt = count_stmt.where(Item.name.ilike(f"%{name}%"))
        if category:
            count_stmt = count_stmt.where(Item.category == category)

        count_result = await session.execute(count_stmt)
        total = len(count_result.scalars().all())

        # Get paginated items
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)

        result = await session.execute(stmt)
        items = result.scalars().all()

        # Convert to response
        items_data = [convert_item_to_response(item) for item in items]
        total_pages = (total + limit - 1) // limit  # Ceiling division

        return {
            "items": items_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages
            }
        }

    except Exception as e:
        logger.error(f"Error listing items: {str(e)}")
        raise MCPDatabaseError("DATABASE_ERROR", str(e))
