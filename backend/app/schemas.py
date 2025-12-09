"""
Pydantic request/response schemas for IMS FastAPI backend
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, field_validator, field_serializer, Field

# Valid item categories (source of truth, proper case)
VALID_CATEGORIES = {'Grocery', 'Garments', 'Beauty', 'Utilities', 'Other'}


# ============ Item Schemas ============

class ItemCreate(BaseModel):
    """Request schema for creating a new item"""
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    unit: str = Field(..., min_length=1, max_length=50)
    unit_price: Decimal = Field(..., decimal_places=2, ge=0)
    stock_qty: Decimal = Field(..., decimal_places=3, ge=0)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        """Normalize category to valid case-insensitive format"""
        if not v or not isinstance(v, str):
            raise ValueError("Category must be a non-empty string")

        # Try exact match first
        if v in VALID_CATEGORIES:
            return v

        # Try case-insensitive match
        lower_input = v.lower()
        for valid_cat in sorted(VALID_CATEGORIES):
            if valid_cat.lower() == lower_input:
                return valid_cat

        # No match found
        suggestions = ", ".join(sorted(VALID_CATEGORIES))
        raise ValueError(f"Category '{v}' not found. Valid categories: {suggestions}")


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

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        """Normalize category to valid case-insensitive format (allows None for partial updates)"""
        if v is None:
            return None

        if not isinstance(v, str):
            raise ValueError("Category must be a string")

        # Try exact match first
        if v in VALID_CATEGORIES:
            return v

        # Try case-insensitive match
        lower_input = v.lower()
        for valid_cat in sorted(VALID_CATEGORIES):
            if valid_cat.lower() == lower_input:
                return valid_cat

        # No match found
        suggestions = ", ".join(sorted(VALID_CATEGORIES))
        raise ValueError(f"Category '{v}' not found. Valid categories: {suggestions}")

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
    unit_price: Decimal  # Store as Decimal internally
    stock_qty: Decimal  # Store as Decimal internally
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_serializer('unit_price')
    def serialize_unit_price(self, value: Decimal) -> str:
        """Serialize unit_price to string for JSON response"""
        return str(value)

    @field_serializer('stock_qty')
    def serialize_stock_qty(self, value: Decimal) -> str:
        """Serialize stock_qty to string for JSON response"""
        return str(value)


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
    unit_price: Decimal  # Store as Decimal internally
    quantity: Decimal  # Store as Decimal internally
    line_total: Decimal  # Store as Decimal internally

    class Config:
        from_attributes = True

    @field_serializer('unit_price', 'quantity', 'line_total')
    def serialize_decimals(self, value: Decimal) -> str:
        """Serialize decimal fields to string for JSON response"""
        return str(value)


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
    total_amount: Decimal  # Store as Decimal internally
    created_at: datetime
    bill_items: List[BillItemResponse]

    class Config:
        from_attributes = True

    @field_serializer('total_amount')
    def serialize_total_amount(self, value: Decimal) -> str:
        """Serialize total_amount to string for JSON response"""
        return str(value)


# ============ Agent Schemas (Phase 5) ============

class AgentMessageRequest(BaseModel):
    """Request schema for agent chat endpoint"""
    session_id: str = Field(..., min_length=1, max_length=255, description="Conversation session ID")
    message: str = Field(..., min_length=1, max_length=4096, description="User message in natural language")
    metadata: Optional[dict] = Field(None, description="Optional metadata (user_context, store_name, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "user123-session",
                "message": "Add 10kg sugar to inventory",
                "metadata": {"user_id": "user123", "store_name": "Store A"}
            }
        }


class ToolCall(BaseModel):
    """Tool call made by agent"""
    tool: str = Field(..., description="Tool/function name")
    arguments: dict = Field(..., description="Tool arguments")
    result: Optional[dict] = Field(None, description="Tool execution result")


class AgentMessageResponse(BaseModel):
    """Response schema for agent chat endpoint"""
    session_id: str = Field(..., description="Conversation session ID")
    response: str = Field(..., description="Agent's natural language response")
    status: str = Field(..., description="Response status: success, pending_confirmation, or error")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="List of tool calls made by agent")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "session_id": "user123-session",
                "response": "Added 10kg sugar to inventory. Current stock: 25kg",
                "status": "success",
                "tool_calls": [
                    {
                        "tool": "add_inventory_item",
                        "arguments": {"item_name": "sugar", "quantity": 10, "unit": "kg"},
                        "result": {"status": "success", "item_id": 42}
                    }
                ]
            }
        }
