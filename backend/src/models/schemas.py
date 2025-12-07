"""
Pydantic schemas for request/response validation
Used for Phase 2+ API and as contracts for serialization
"""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, validator


class ItemCreate(BaseModel):
    """Schema for creating a new item"""

    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(...)
    unit: str = Field(...)
    unit_price: Decimal = Field(..., ge=0)
    stock_qty: Decimal = Field(..., ge=0)

    @validator("category")
    def validate_category(cls, v):
        valid_categories = ["Grocery", "Garments", "Beauty", "Utilities", "Other"]
        if v not in valid_categories:
            raise ValueError(f"Invalid category. Must be one of {valid_categories}")
        return v

    @validator("unit")
    def validate_unit(cls, v):
        valid_units = ["kg", "g", "liter", "ml", "piece", "box", "pack", "other"]
        if v not in valid_units:
            raise ValueError(f"Invalid unit. Must be one of {valid_units}")
        return v

    class Config:
        from_attributes = True


class ItemUpdate(BaseModel):
    """Schema for updating an item"""

    unit_price: Optional[Decimal] = Field(None, ge=0)
    stock_qty: Optional[Decimal] = Field(None, ge=0)

    class Config:
        from_attributes = True


class ItemResponse(ItemCreate):
    """Schema for item response"""

    id: int
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class BillItemCreate(BaseModel):
    """Schema for creating a bill item"""

    item_id: int
    item_name: str = Field(..., min_length=1, max_length=255)
    unit_price: Decimal = Field(..., ge=0)
    quantity: Decimal = Field(..., gt=0)
    line_total: Decimal = Field(..., ge=0)

    class Config:
        from_attributes = True


class BillItemResponse(BillItemCreate):
    """Schema for bill item response"""

    id: int
    bill_id: int
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class BillCreate(BaseModel):
    """Schema for creating a bill"""

    customer_name: Optional[str] = Field(None, max_length=255)
    store_name: Optional[str] = Field(None, max_length=255)
    total_amount: Decimal = Field(..., ge=0)

    class Config:
        from_attributes = True


class BillResponse(BillCreate):
    """Schema for bill response"""

    id: int
    created_at: Optional[str] = None
    bill_items: list[BillItemResponse] = []

    class Config:
        from_attributes = True
