"""
MCP tool implementations for billing operations (user-scoped)
"""
import logging
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models import Bill, BillItem, Item
from app.mcp_server.exceptions import (
    MCPValidationError,
    MCPNotFoundError,
    MCPInsufficientStockError,
    MCPDatabaseError,
)
from app.mcp_server.utils import mcp_error_handler

logger = logging.getLogger(__name__)


# ============================================================================
# Task 31-33: billing_create_bill (RED -> GREEN -> REFACTOR)
# ============================================================================

@mcp_error_handler("billing_create_bill")
async def billing_create_bill(
    items: list,
    customer_name: str = None,
    store_name: str = None,
    session: AsyncSession = None,
    user_id: Optional[int] = None
) -> dict:
    """
    Create a bill with line items (user-scoped).

    Args:
        items: List of dicts with item_id and quantity
        customer_name: Optional customer name
        store_name: Optional store name
        session: AsyncSession for database operations
        user_id: Optional user ID to scope bill and items

    Returns:
        Bill response with line items and total amount
    """
    if not items or len(items) == 0:
        raise MCPValidationError(
            "BILL_EMPTY",
            "Bill must have at least one item"
        )

    try:
        # Validate all items exist and have sufficient stock
        bill_items_to_add = []
        total_amount = Decimal("0.00")

        for item_request in items:
            item_id = item_request.get("item_id")
            quantity = Decimal(str(item_request.get("quantity", 0)))

            if quantity <= 0:
                raise MCPValidationError(
                    "QUANTITY_INVALID",
                    f"Item {item_id}: Quantity must be > 0"
                )

            # Get item - filter by user_id if provided
            conditions = [Item.id == item_id]
            if user_id is not None:
                conditions.append(Item.user_id == user_id)

            stmt = select(Item).where(and_(*conditions))
            result = await session.execute(stmt)
            item = result.scalar_one_or_none()

            if not item:
                raise MCPNotFoundError("ITEM_NOT_FOUND", f"Item {item_id} not found")

            # Check stock
            if item.stock_qty < quantity:
                raise MCPInsufficientStockError(
                    "INSUFFICIENT_STOCK",
                    f"Item {item.name}: Need {quantity}, have {item.stock_qty}",
                    {
                        "item_id": item_id,
                        "item_name": item.name,
                        "available": float(item.stock_qty),
                        "requested": float(quantity)
                    }
                )

            # Calculate line total
            line_total = item.unit_price * quantity
            total_amount += line_total

            bill_items_to_add.append({
                "item": item,
                "quantity": quantity,
                "line_total": line_total
            })

        # Create bill - associate with user if provided
        bill = Bill(
            customer_name=customer_name,
            store_name=store_name,
            total_amount=total_amount,
            user_id=user_id  # Associate bill with user
        )
        session.add(bill)
        await session.flush()  # Get bill ID

        # Add line items and reduce stock
        for item_data in bill_items_to_add:
            item = item_data["item"]
            quantity = item_data["quantity"]

            # Add line item with snapshot
            line_item = BillItem(
                bill_id=bill.id,
                item_id=item.id,
                item_name=item.name,
                unit_price=item.unit_price,
                quantity=quantity,
                line_total=item_data["line_total"]
            )
            session.add(line_item)

            # Reduce stock
            item.stock_qty -= quantity

        await session.commit()
        logger.info(f"Created bill: {bill.id} with total {total_amount}")

        # Convert to response
        return {
            "id": bill.id,
            "customer_name": bill.customer_name,
            "store_name": bill.store_name,
            "items": [
                {
                    "item_id": item_data["item"].id,
                    "item_name": item_data["item"].name,
                    "unit_price": float(item_data["item"].unit_price),
                    "quantity": float(item_data["quantity"]),
                    "line_total": float(item_data["line_total"])
                }
                for item_data in bill_items_to_add
            ],
            "total_amount": float(total_amount),
            "created_at": bill.created_at.isoformat() if bill.created_at else None
        }

    except (MCPValidationError, MCPNotFoundError, MCPInsufficientStockError):
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating bill: {str(e)}")
        raise MCPDatabaseError("DATABASE_ERROR", str(e))


# ============================================================================
# Task 34-36: billing_get_bill (RED -> GREEN -> REFACTOR)
# ============================================================================

@mcp_error_handler("billing_get_bill")
async def billing_get_bill(
    bill_id: int,
    session: AsyncSession = None,
    user_id: Optional[int] = None
) -> dict:
    """Get bill details with line items (user-scoped)."""
    try:
        # Filter by user_id if provided
        conditions = [Bill.id == bill_id]
        if user_id is not None:
            conditions.append(Bill.user_id == user_id)

        stmt = select(Bill).where(and_(*conditions))
        result = await session.execute(stmt)
        bill = result.scalar_one_or_none()

        if not bill:
            raise MCPNotFoundError("BILL_NOT_FOUND", f"Bill {bill_id} not found")

        # Convert to response
        return {
            "id": bill.id,
            "customer_name": bill.customer_name,
            "store_name": bill.store_name,
            "items": [
                {
                    "id": item.id,
                    "item_id": item.item_id,
                    "item_name": item.item_name,
                    "unit_price": float(item.unit_price),
                    "quantity": float(item.quantity),
                    "line_total": float(item.line_total)
                }
                for item in bill.bill_items
            ],
            "total_amount": float(bill.total_amount),
            "created_at": bill.created_at.isoformat() if bill.created_at else None
        }

    except MCPNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting bill: {str(e)}")
        raise MCPDatabaseError("DATABASE_ERROR", str(e))


# ============================================================================
# Task 37-39: billing_list_bills (RED -> GREEN -> REFACTOR)
# ============================================================================

@mcp_error_handler("billing_list_bills")
async def billing_list_bills(
    start_date: str = None,
    end_date: str = None,
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = None,
    user_id: Optional[int] = None
) -> dict:
    """
    List bills with optional date filtering and pagination (user-scoped).
    """
    try:
        # Validate pagination
        if page < 1:
            page = 1
        if limit < 1:
            limit = 20
        if limit > 100:
            limit = 100

        # Build base conditions with user_id filter if provided
        base_conditions = []
        if user_id is not None:
            base_conditions.append(Bill.user_id == user_id)

        # Build query with eager loading of relationships
        if base_conditions:
            stmt = select(Bill).options(selectinload(Bill.bill_items)).where(and_(*base_conditions))
        else:
            stmt = select(Bill).options(selectinload(Bill.bill_items))

        # Date filtering
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                stmt = stmt.where(Bill.created_at >= start_dt)
            except ValueError:
                raise MCPValidationError(
                    "DATE_INVALID",
                    "start_date must be ISO 8601 format"
                )

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                stmt = stmt.where(Bill.created_at <= end_dt)
            except ValueError:
                raise MCPValidationError(
                    "DATE_INVALID",
                    "end_date must be ISO 8601 format"
                )

        # Get total count with same filters
        if base_conditions:
            count_stmt = select(Bill).where(and_(*base_conditions))
        else:
            count_stmt = select(Bill)
        if start_date:
            count_stmt = count_stmt.where(Bill.created_at >= start_dt)
        if end_date:
            count_stmt = count_stmt.where(Bill.created_at <= end_dt)

        count_result = await session.execute(count_stmt)
        total = len(count_result.scalars().all())

        # Get paginated bills with eager loading
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit).order_by(Bill.created_at.desc())

        result = await session.execute(stmt)
        bills = result.scalars().all()

        # Convert to response
        bills_data = [
            {
                "id": bill.id,
                "customer_name": bill.customer_name,
                "store_name": bill.store_name,
                "items": [
                    {
                        "item_id": item.item_id,
                        "item_name": item.item_name,
                        "unit_price": float(item.unit_price),
                        "quantity": float(item.quantity),
                        "line_total": float(item.line_total)
                    }
                    for item in bill.bill_items
                ],
                "total_amount": float(bill.total_amount),
                "created_at": bill.created_at.isoformat() if bill.created_at else None
            }
            for bill in bills
        ]

        total_pages = (total + limit - 1) // limit

        return {
            "bills": bills_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages
            }
        }

    except (MCPValidationError):
        raise
    except Exception as e:
        logger.error(f"Error listing bills: {str(e)}")
        raise MCPDatabaseError("DATABASE_ERROR", str(e))
