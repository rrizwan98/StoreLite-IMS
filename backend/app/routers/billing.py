"""
Billing and invoice management API endpoints (User Stories 6-8)
"""

import logging
from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Item, Bill, BillItem
from app.schemas import BillCreate, BillResponse
from app.exceptions import NotFoundError, BusinessLogicError, DatabaseError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["billing"])


@router.post("/bills", response_model=BillResponse, status_code=201)
async def create_bill(bill_data: BillCreate, db: AsyncSession = Depends(get_db)):
    """
    US6: Create a new bill/invoice with multiple items

    POST /bills
    """
    logger.info(f"Creating bill with {len(bill_data.items)} items")

    try:
        # Phase 1: Upfront validation - check all items exist and have sufficient stock
        items_with_prices = []
        total_amount = Decimal("0.00")

        for bill_item_data in bill_data.items:
            # Fetch item from DB
            query = select(Item).where(Item.id == bill_item_data.item_id)
            result = await db.execute(query)
            item = result.scalar_one_or_none()

            if not item:
                logger.warning(f"Item not found: id={bill_item_data.item_id}")
                raise BusinessLogicError(f"Item with id {bill_item_data.item_id} not found")

            # Check sufficient stock
            if item.stock_qty < bill_item_data.quantity:
                logger.warning(
                    f"Insufficient stock for item {item.name}: "
                    f"required={bill_item_data.quantity}, available={item.stock_qty}"
                )
                raise BusinessLogicError(
                    f"Insufficient stock for item '{item.name}': "
                    f"required={bill_item_data.quantity}, available={item.stock_qty}"
                )

            # Calculate line total
            line_total = item.unit_price * bill_item_data.quantity
            total_amount += line_total

            items_with_prices.append({
                "item": item,
                "quantity": bill_item_data.quantity,
                "line_total": line_total,
            })

        # Phase 2: All validations passed, create bill atomically
        logger.info(f"All validations passed, creating bill with total={total_amount}")

        # Create bill
        bill = Bill(
            customer_name=bill_data.customer_name,
            store_name=bill_data.store_name,
            total_amount=total_amount,
        )
        db.add(bill)
        await db.flush()  # Get the bill ID

        # Create bill items with snapshots
        for item_price_info in items_with_prices:
            item = item_price_info["item"]
            quantity = item_price_info["quantity"]
            line_total = item_price_info["line_total"]

            bill_item = BillItem(
                bill_id=bill.id,
                item_id=item.id,
                item_name=item.name,
                unit_price=item.unit_price,
                quantity=quantity,
                line_total=line_total,
            )
            db.add(bill_item)

        # Update stock quantities
        for item_price_info in items_with_prices:
            item = item_price_info["item"]
            quantity = item_price_info["quantity"]
            item.stock_qty -= quantity

        # Commit all changes
        await db.commit()
        await db.refresh(bill)

        logger.info(f"Bill created successfully: id={bill.id}, total={total_amount}")
        return bill

    except (BusinessLogicError, NotFoundError):
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error creating bill: {str(e)}", exc_info=True)
        await db.rollback()
        raise DatabaseError(f"Failed to create bill: {str(e)}")


@router.get("/bills/{bill_id}", response_model=BillResponse)
async def get_bill(bill_id: int, db: AsyncSession = Depends(get_db)):
    """
    US7: Retrieve bill details with all line items

    GET /bills/{id}
    """
    logger.info(f"Getting bill: id={bill_id}")

    try:
        query = select(Bill).where(Bill.id == bill_id)
        result = await db.execute(query)
        bill = result.scalar_one_or_none()

        if not bill:
            logger.warning(f"Bill not found: id={bill_id}")
            raise NotFoundError(f"Bill with id {bill_id} not found")

        # Eager load bill items
        query = select(BillItem).where(BillItem.bill_id == bill.id)
        result = await db.execute(query)
        bill.bill_items = result.scalars().all()

        logger.info(f"Bill found: id={bill_id}, items={len(bill.bill_items)}")
        return bill

    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting bill: {str(e)}")
        raise DatabaseError(f"Failed to get bill: {str(e)}")


@router.get("/bills", response_model=List[BillResponse])
async def list_bills(db: AsyncSession = Depends(get_db)):
    """
    US8: List all bills

    GET /bills
    """
    logger.info("Listing all bills")

    try:
        query = select(Bill).order_by(Bill.created_at.desc())
        result = await db.execute(query)
        bills = result.scalars().all()

        # Load bill items for each bill
        for bill in bills:
            query = select(BillItem).where(BillItem.bill_id == bill.id)
            result = await db.execute(query)
            bill.bill_items = result.scalars().all()

        logger.info(f"Found {len(bills)} bills")
        return bills

    except Exception as e:
        logger.error(f"Error listing bills: {str(e)}")
        raise DatabaseError(f"Failed to list bills: {str(e)}")
