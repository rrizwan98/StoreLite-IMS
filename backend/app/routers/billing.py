"""
Billing and invoice management API endpoints (User Stories 6-8)
"""

import logging
from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Item, Bill, BillItem, User
from app.schemas import BillCreate, BillResponse, BillItemResponse
from app.exceptions import NotFoundError, BusinessLogicError, DatabaseError
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["billing"])


@router.post("/bills", response_model=BillResponse, status_code=201)
async def create_bill(
    bill_data: BillCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    US6: Create a new bill/invoice with multiple items (user-scoped)

    POST /bills
    """
    logger.info(f"Creating bill with {len(bill_data.items)} items for user {current_user.id}")

    try:
        # Phase 1: Upfront validation - check all items exist (for this user) and have sufficient stock
        items_with_prices = []
        total_amount = Decimal("0.00")

        for bill_item_data in bill_data.items:
            # Fetch item from DB - filter by current user's items
            query = select(Item).where(
                and_(Item.id == bill_item_data.item_id, Item.user_id == current_user.id)
            )
            result = await db.execute(query)
            item = result.scalar_one_or_none()

            if not item:
                logger.warning(f"Item not found: id={bill_item_data.item_id} for user {current_user.id}")
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
        logger.info(f"All validations passed, creating bill with total={total_amount} for user {current_user.id}")

        # Create bill - associate with current user
        bill = Bill(
            user_id=current_user.id,  # Associate bill with current user
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

        # Refresh bill and load relationships
        await db.refresh(bill)
        query = select(BillItem).where(BillItem.bill_id == bill.id)
        result = await db.execute(query)
        bill_items = result.scalars().all()

        # Build response object
        response_bill = BillResponse(
            id=bill.id,
            customer_name=bill.customer_name,
            store_name=bill.store_name,
            total_amount=bill.total_amount,
            created_at=bill.created_at,
            bill_items=[
                BillItemResponse(
                    item_name=item.item_name,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                    line_total=item.line_total
                ) for item in bill_items
            ]
        )

        logger.info(f"Bill created successfully: id={bill.id}, total={total_amount}")
        return response_bill

    except (BusinessLogicError, NotFoundError):
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error creating bill: {str(e)}", exc_info=True)
        await db.rollback()
        raise DatabaseError(f"Failed to create bill: {str(e)}")


@router.get("/bills/{bill_id}", response_model=BillResponse)
async def get_bill(
    bill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    US7: Retrieve bill details with all line items (user-scoped)

    GET /bills/{id}
    """
    logger.info(f"Getting bill: id={bill_id} for user {current_user.id}")

    try:
        # Filter by current user's bills only
        query = select(Bill).where(
            and_(Bill.id == bill_id, Bill.user_id == current_user.id)
        )
        result = await db.execute(query)
        bill = result.scalar_one_or_none()

        if not bill:
            logger.warning(f"Bill not found: id={bill_id} for user {current_user.id}")
            raise NotFoundError(f"Bill with id {bill_id} not found")

        # Eager load bill items
        try:
            bill_items_query = select(BillItem).where(BillItem.bill_id == bill.id)
            bill_items_result = await db.execute(bill_items_query)
            bill_items = bill_items_result.scalars().all()

            # Create response object
            response_bill = BillResponse(
                id=bill.id,
                customer_name=bill.customer_name,
                store_name=bill.store_name,
                total_amount=bill.total_amount,
                created_at=bill.created_at,
                bill_items=[
                    BillItemResponse(
                        item_name=item.item_name,
                        unit_price=item.unit_price,
                        quantity=item.quantity,
                        line_total=item.line_total
                    ) for item in bill_items
                ]
            )
            logger.info(f"Bill found: id={bill_id}, items={len(bill_items)}")
            return response_bill
        except Exception as item_error:
            logger.warning(f"Error loading items for bill {bill_id}: {str(item_error)}")
            # Return bill with empty items
            return BillResponse(
                id=bill.id,
                customer_name=bill.customer_name,
                store_name=bill.store_name,
                total_amount=bill.total_amount,
                created_at=bill.created_at,
                bill_items=[]
            )

    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting bill: {str(e)}", exc_info=True)
        raise DatabaseError(f"Failed to get bill: {str(e)}")


@router.get("/bills", response_model=List[BillResponse])
async def list_bills(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    US8: List all bills (user-scoped)

    GET /bills
    """
    logger.info(f"Listing all bills for user {current_user.id}")

    try:
        # Filter by current user's bills only
        query = select(Bill).where(Bill.user_id == current_user.id).order_by(Bill.created_at.desc())
        result = await db.execute(query)
        bills = result.scalars().all()

        # Build response with bill items
        response_bills = []
        for bill in bills:
            try:
                bill_items_query = select(BillItem).where(BillItem.bill_id == bill.id)
                bill_items_result = await db.execute(bill_items_query)
                bill_items = bill_items_result.scalars().all()

                # Create response object with loaded items
                response_bill = BillResponse(
                    id=bill.id,
                    customer_name=bill.customer_name,
                    store_name=bill.store_name,
                    total_amount=bill.total_amount,
                    created_at=bill.created_at,
                    bill_items=[
                        BillItemResponse(
                            item_name=item.item_name,
                            unit_price=item.unit_price,
                            quantity=item.quantity,
                            line_total=item.line_total
                        ) for item in bill_items
                    ]
                )
                response_bills.append(response_bill)
            except Exception as item_error:
                logger.warning(f"Error loading items for bill {bill.id}: {str(item_error)}")
                # Return bill with empty items
                response_bill = BillResponse(
                    id=bill.id,
                    customer_name=bill.customer_name,
                    store_name=bill.store_name,
                    total_amount=bill.total_amount,
                    created_at=bill.created_at,
                    bill_items=[]
                )
                response_bills.append(response_bill)

        logger.info(f"Found {len(response_bills)} bills")
        return response_bills

    except Exception as e:
        logger.error(f"Error listing bills: {str(e)}", exc_info=True)
        raise DatabaseError(f"Failed to list bills: {str(e)}")
