"""
Pydantic schemas for MCP tools (FastMCP)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# ============================================================================
# TASK 2: Common Schemas (Error handling, pagination, response wrappers)
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response structure."""
    error: str = Field(..., description="Error code (e.g., ITEM_NOT_FOUND)")
    message: str = Field(..., description="Human-readable error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error context")


class PaginationInfo(BaseModel):
    """Pagination information for list responses."""
    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total items available")
    total_pages: int = Field(..., ge=0, description="Total pages available")


class SuccessResponse(BaseModel):
    """Generic success response wrapper."""
    success: bool = Field(default=True, description="Always true for success")
    data: Any = Field(..., description="Response data")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadata (pagination, timing, etc.)")


# Error code taxonomy
ERROR_CODES = {
    "VALIDATION_ERROR": "VALIDATION_ERROR",
    "ITEM_NOT_FOUND": "ITEM_NOT_FOUND",
    "INSUFFICIENT_STOCK": "INSUFFICIENT_STOCK",
    "CATEGORY_INVALID": "CATEGORY_INVALID",
    "UNIT_INVALID": "UNIT_INVALID",
    "PRICE_INVALID": "PRICE_INVALID",
    "QUANTITY_INVALID": "QUANTITY_INVALID",
    "BILL_IMMUTABLE": "BILL_IMMUTABLE",
    "DUPLICATE_ITEM": "DUPLICATE_ITEM",
    "DATABASE_ERROR": "DATABASE_ERROR",
    "BILL_NOT_FOUND": "BILL_NOT_FOUND",
}


# ============================================================================
# TASK 3: Inventory Tool Schemas
# ============================================================================

VALID_CATEGORIES = {"Grocery", "Garments", "Beauty", "Utilities", "Other"}
VALID_UNITS = {"kg", "g", "liter", "ml", "piece", "box", "pack", "other"}


class ItemCreate(BaseModel):
    """Schema for creating a new inventory item."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Item name"
    )
    category: str = Field(
        ...,
        description=f"Category: {', '.join(sorted(VALID_CATEGORIES))}"
    )
    unit: str = Field(
        ...,
        description=f"Unit: {', '.join(sorted(VALID_UNITS))}"
    )
    unit_price: float = Field(
        ...,
        gt=0,
        description="Price per unit (must be > 0)"
    )
    stock_qty: float = Field(
        ...,
        ge=0,
        description="Initial stock quantity (must be >= 0)"
    )

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of: {VALID_CATEGORIES}")
        return v

    @field_validator('unit')
    @classmethod
    def validate_unit(cls, v):
        if v not in VALID_UNITS:
            raise ValueError(f"Unit must be one of: {VALID_UNITS}")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Sugar",
                "category": "Grocery",
                "unit": "kg",
                "unit_price": 50.00,
                "stock_qty": 100.0
            }
        }
    }


class ItemUpdate(BaseModel):
    """Schema for updating inventory item (partial update allowed)."""
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Item name"
    )
    category: Optional[str] = Field(
        None,
        description=f"Category: {', '.join(sorted(VALID_CATEGORIES))}"
    )
    unit: Optional[str] = Field(
        None,
        description=f"Unit: {', '.join(sorted(VALID_UNITS))}"
    )
    unit_price: Optional[float] = Field(
        None,
        gt=0,
        description="Price per unit (must be > 0)"
    )
    stock_qty: Optional[float] = Field(
        None,
        ge=0,
        description="Stock quantity (must be >= 0)"
    )

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        if v is not None and v not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of: {VALID_CATEGORIES}")
        return v

    @field_validator('unit')
    @classmethod
    def validate_unit(cls, v):
        if v is not None and v not in VALID_UNITS:
            raise ValueError(f"Unit must be one of: {VALID_UNITS}")
        return v


class ItemRead(BaseModel):
    """Schema for reading inventory item."""
    id: int
    name: str
    category: str
    unit: str
    unit_price: Decimal
    stock_qty: Decimal
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ItemListResponse(BaseModel):
    """Response for listing inventory items."""
    items: List[ItemRead] = Field(..., description="List of items")
    pagination: Optional[PaginationInfo] = Field(None, description="Pagination info")


class DeleteResponse(BaseModel):
    """Response for soft delete operations."""
    id: int = Field(..., description="ID of deleted item")
    success: bool = Field(default=True, description="Whether deletion was successful")


# ============================================================================
# TASK 4: Billing Tool Schemas
# ============================================================================

class BillItemCreate(BaseModel):
    """Schema for creating a line item in a bill."""
    item_id: int = Field(..., description="ID of inventory item")
    quantity: float = Field(..., gt=0, description="Quantity to bill (must be > 0)")


class BillCreate(BaseModel):
    """Schema for creating a new bill."""
    items: List[BillItemCreate] = Field(
        ...,
        min_length=1,
        description="Line items (must have at least one)"
    )
    customer_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Customer name"
    )
    store_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Store name"
    )

    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Bill must have at least one item")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "customer_name": "John Doe",
                "store_name": "Downtown Store",
                "items": [
                    {"item_id": 1, "quantity": 5}
                ]
            }
        }
    }


class BillItemRead(BaseModel):
    """Schema for reading a line item from a bill."""
    id: Optional[int] = None
    item_id: int
    item_name: str = Field(..., description="Snapshot of item name at bill time")
    unit_price: Decimal = Field(..., description="Snapshot of unit price at bill time")
    quantity: Decimal
    line_total: Decimal

    model_config = {"from_attributes": True}


class BillRead(BaseModel):
    """Schema for reading a bill."""
    id: int
    customer_name: Optional[str] = None
    store_name: Optional[str] = None
    items: List[BillItemRead] = Field(default_factory=list, description="Line items with snapshots")
    total_amount: Decimal
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BillListResponse(BaseModel):
    """Response for listing bills."""
    bills: List[BillRead] = Field(..., description="List of bills")
    pagination: Optional[PaginationInfo] = Field(None, description="Pagination info")


class ListBillRequest(BaseModel):
    """Request parameters for listing bills."""
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format)")
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")


class GetBillRequest(BaseModel):
    """Request parameters for getting a specific bill."""
    bill_id: int = Field(..., description="Bill ID")
