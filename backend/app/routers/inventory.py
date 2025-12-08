"""
Inventory management API endpoints (User Stories 1-5)
"""

import logging
from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Item
from app.schemas import ItemCreate, ItemUpdate, ItemResponse
from app.exceptions import NotFoundError, DatabaseError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["inventory"])


@router.post("/items", response_model=ItemResponse, status_code=201)
async def create_item(item_data: ItemCreate, db: AsyncSession = Depends(get_db)):
    """
    US1: Create a new inventory item

    POST /items
    """
    logger.info(f"Creating item: {item_data.name}")
    try:
        new_item = Item(
            name=item_data.name,
            category=item_data.category,
            unit=item_data.unit,
            unit_price=item_data.unit_price,
            stock_qty=item_data.stock_qty,
            is_active=True,
        )
        db.add(new_item)
        await db.commit()
        await db.refresh(new_item)
        logger.info(f"Item created successfully: id={new_item.id}")
        return new_item
    except Exception as e:
        logger.error(f"Error creating item: {str(e)}")
        await db.rollback()
        raise DatabaseError(f"Failed to create item: {str(e)}")


@router.get("/items", response_model=List[ItemResponse])
async def list_items(
    name: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    US2: List and search inventory items

    GET /items?name=...&category=...
    """
    logger.info(f"Listing items with filters: name={name}, category={category}")
    try:
        query = select(Item).where(Item.is_active == True)

        if name:
            query = query.where(Item.name.ilike(f"%{name}%"))

        if category:
            query = query.where(Item.category == category)

        query = query.order_by(Item.name.asc())
        result = await db.execute(query)
        items = result.scalars().all()
        logger.info(f"Found {len(items)} items")
        return items
    except Exception as e:
        logger.error(f"Error listing items: {str(e)}")
        raise DatabaseError(f"Failed to list items: {str(e)}")


@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """
    US3: Get single item details

    GET /items/{id}
    """
    logger.info(f"Getting item: id={item_id}")
    try:
        query = select(Item).where(
            and_(Item.id == item_id, Item.is_active == True)
        )
        result = await db.execute(query)
        item = result.scalar_one_or_none()

        if not item:
            logger.warning(f"Item not found: id={item_id}")
            raise NotFoundError(f"Item with id {item_id} not found")

        logger.info(f"Item found: id={item_id}")
        return item
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting item: {str(e)}")
        raise DatabaseError(f"Failed to get item: {str(e)}")


@router.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_data: ItemUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    US4: Update item price and stock

    PUT /items/{id}
    """
    logger.info(f"Updating item: id={item_id}")
    try:
        # Get the item
        query = select(Item).where(Item.id == item_id)
        result = await db.execute(query)
        item = result.scalar_one_or_none()

        if not item:
            logger.warning(f"Item not found for update: id={item_id}")
            raise NotFoundError(f"Item with id {item_id} not found")

        # Update fields if provided
        if item_data.name is not None:
            item.name = item_data.name
        if item_data.category is not None:
            item.category = item_data.category
        if item_data.unit is not None:
            item.unit = item_data.unit
        if item_data.unit_price is not None:
            item.unit_price = item_data.unit_price
        if item_data.stock_qty is not None:
            item.stock_qty = item_data.stock_qty

        await db.commit()
        await db.refresh(item)
        logger.info(f"Item updated successfully: id={item_id}")
        return item
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error updating item: {str(e)}")
        await db.rollback()
        raise DatabaseError(f"Failed to update item: {str(e)}")


@router.delete("/items/{item_id}", status_code=204)
async def deactivate_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """
    US5: Deactivate (soft-delete) an item

    DELETE /items/{id}
    """
    logger.info(f"Deactivating item: id={item_id}")
    try:
        # Get the item
        query = select(Item).where(Item.id == item_id)
        result = await db.execute(query)
        item = result.scalar_one_or_none()

        if not item:
            logger.warning(f"Item not found for deactivation: id={item_id}")
            raise NotFoundError(f"Item with id {item_id} not found")

        # Soft delete: mark as inactive
        item.is_active = False
        await db.commit()
        logger.info(f"Item deactivated successfully: id={item_id}")
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error deactivating item: {str(e)}")
        await db.rollback()
        raise DatabaseError(f"Failed to deactivate item: {str(e)}")
