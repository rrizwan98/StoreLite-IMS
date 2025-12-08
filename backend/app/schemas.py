"""
Pydantic request/response schemas for IMS FastAPI backend
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, field_validator, Field


# ============ Item Schemas ============

class ItemCreate(BaseModel):
    """Request schema for creating a new item"""
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    unit: str = Field(..., min_length=1, max_length=50)
    unit_price: Decimal = Field(..., decimal_places=2, ge=0)
    stock_qty: Decimal = Field(..., decimal_places=3, ge=0)

    @field_validator("unit_price", "stock_qty", mode="before")
    @classmethod
    def validate_numeric(cls, v):
        if v is None:
            return v
        try:
            return Decimal(str(v))
        except:
            raise ValueError("Must be a valid decimal number")

    @field_validator("unit_price")
    @classmethod
    def validate_unit_price_non_negative(cls, v):
        if v < 0:
            raise ValueError("Unit price must be >= 0")
        return v

    @field_validator("stock_qty")
    @classmethod
    def validate_stock_qty_non_negative(cls, v):
        if v < 0:
            raise ValueError("Stock quantity must be >= 0")
        return v


class ItemUpdate(BaseModel):
    """Request schema for updating an item"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    unit_price: Optional[Decimal] = Field(None, decimal_places=2, ge=0)
    stock_qty: Optional[Decimal] = Field(None, decimal_places=3, ge=0)

    @field_validator("unit_price", "stock_qty", mode="before")
    @classmethod
    def validate_numeric(cls, v):
        if v is None:
            return v
        try:
            return Decimal(str(v))
        except:
            raise ValueError("Must be a valid decimal number")

    @field_validator("unit_price")
    @classmethod
    def validate_unit_price_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("Unit price must be >= 0")
        return v

    @field_validator("stock_qty")
    @classmethod
    def validate_stock_qty_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("Stock quantity must be >= 0")
        return v


class ItemResponse(BaseModel):
    """Response schema for item"""
    id: int
    name: str
    category: str
    unit: str
    unit_price: str  # Return as string for precision
    stock_qty: Decimal  # Return as number for quantities
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    def __init__(self, **data):
        super().__init__(**data)
        # Convert unit_price to string if it's a Decimal
        if isinstance(self.unit_price, Decimal):
            self.unit_price = str(self.unit_price)
        elif isinstance(self.unit_price, (int, float)):
            self.unit_price = f"{Decimal(str(self.unit_price)):.2f}"


# ============ Bill Item Schemas ============

class BillItemCreate(BaseModel):
    """Request schema for creating a bill line item"""
    item_id: int = Field(..., gt=0)
    quantity: Decimal = Field(..., decimal_places=3, gt=0)

    @field_validator("quantity", mode="before")
    @classmethod
    def validate_quantity_numeric(cls, v):
        if v is None:
            return v
        try:
            return Decimal(str(v))
        except:
            raise ValueError("Quantity must be a valid decimal number")

    @field_validator("quantity")
    @classmethod
    def validate_quantity_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be > 0")
        return v


class BillItemResponse(BaseModel):
    """Response schema for bill line item"""
    item_name: str
    unit_price: str  # Return as string for precision
    quantity: Decimal  # Return as number for quantities
    line_total: str  # Return as string for precision

    class Config:
        from_attributes = True

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure string conversions
        if isinstance(self.unit_price, Decimal):
            self.unit_price = str(self.unit_price)
        elif isinstance(self.unit_price, (int, float)):
            self.unit_price = f"{Decimal(str(self.unit_price)):.2f}"

        if isinstance(self.line_total, Decimal):
            self.line_total = str(self.line_total)
        elif isinstance(self.line_total, (int, float)):
            self.line_total = f"{Decimal(str(self.line_total)):.2f}"


# ============ Bill Schemas ============

class BillCreate(BaseModel):
    """Request schema for creating a bill"""
    items: List[BillItemCreate] = Field(..., min_length=1)
    customer_name: Optional[str] = Field(None, max_length=255)
    store_name: Optional[str] = Field(None, max_length=255)

    @field_validator("items")
    @classmethod
    def validate_items_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Bill must contain at least one item")
        return v


class BillResponse(BaseModel):
    """Response schema for bill"""
    id: int
    customer_name: Optional[str]
    store_name: Optional[str]
    total_amount: str  # Return as string for precision
    created_at: datetime
    bill_items: List[BillItemResponse]

    class Config:
        from_attributes = True

    def __init__(self, **data):
        super().__init__(**data)
        # Convert total_amount to string if it's a Decimal
        if isinstance(self.total_amount, Decimal):
            self.total_amount = str(self.total_amount)
        elif isinstance(self.total_amount, (int, float)):
            self.total_amount = f"{Decimal(str(self.total_amount)):.2f}"
