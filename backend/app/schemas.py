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


# ============ ChatKit Schemas (Phase 6) ============
# Pure vanilla ChatKit web component integration
# See: https://openai.github.io/chatkit-js/

class ChatKitMessage(BaseModel):
    """Request schema for ChatKit /agent/chat endpoint (vanilla JS integration)"""
    session_id: str = Field(
        ...,
        description="Tab-lifetime session ID (generated by client)",
        example="session-1733750000000-abc123def456"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User's natural language message",
        example="Add 10kg sugar at 160 per kg under grocery category"
    )
    user_id: Optional[str] = Field(
        None,
        description="Optional user ID for context (from app auth)"
    )
    thread_id: Optional[str] = Field(
        None,
        description="Optional thread ID for conversation grouping"
    )

    class Config:
        from_attributes = True


class ChatKitResponse(BaseModel):
    """Response schema for ChatKit /agent/chat endpoint (vanilla JS integration)"""
    session_id: str = Field(
        ...,
        description="Echo back session ID for client tracking"
    )
    message: str = Field(
        ...,
        description="Agent's response text (displayed in ChatKit)"
    )
    type: str = Field(
        default="text",
        description="Response type: 'text', 'item_created', 'bill_created', 'item_list', 'error'",
        example="item_created"
    )
    structured_data: Optional[dict] = Field(
        None,
        description="Structured JSON for UI rendering (bills, items, etc.)",
        example={
            "item_id": 1,
            "name": "Sugar",
            "category": "Grocery",
            "unit_price": 160.0,
            "stock_qty": 100
        }
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if type='error'"
    )

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "session_id": "session-1733750000000-abc123def456",
                "message": "Added Sugar to inventory successfully.",
                "type": "item_created",
                "structured_data": {
                    "item_id": 1,
                    "name": "Sugar",
                    "category": "Grocery",
                    "unit_price": 160.0,
                    "stock_qty": 100
                },
                "timestamp": "2025-12-09T10:30:45.123456",
                "error": None
            }
        }


class ChatKitSession(BaseModel):
    """Session creation request for ChatKit"""
    user_id: Optional[str] = Field(
        None,
        description="User identifier from app authentication"
    )

    class Config:
        from_attributes = True


class ChatKitSessionResponse(BaseModel):
    """Session creation response for ChatKit client"""
    session_id: str = Field(
        ...,
        description="New tab-lifetime session ID",
        example="session-1733750000000-abc123def456"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Session creation timestamp"
    )

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ============ User MCP Connectors Schemas (Feature 008) ============

from enum import Enum
from pydantic import HttpUrl
from typing import Any, Dict


class AuthType(str, Enum):
    """Authentication type for MCP connectors"""
    NONE = "none"
    OAUTH = "oauth"
    API_KEY = "api_key"


# --- System Tools Schemas ---

class SystemToolResponse(BaseModel):
    """System tool with user's connection status"""
    id: str
    name: str
    description: str
    icon: str
    category: str
    auth_type: str
    is_enabled: bool
    is_beta: bool
    is_connected: bool = False  # User-specific
    config: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ToolConnectRequest(BaseModel):
    """Request to connect to a system tool"""
    config: Optional[Dict[str, Any]] = None


class SystemToolsListResponse(BaseModel):
    """Response for listing system tools"""
    tools: List[SystemToolResponse]
    total: int


# --- User Connector Schemas ---

class DiscoveredTool(BaseModel):
    """Tool discovered from MCP server"""
    name: str
    description: Optional[str] = None
    inputSchema: Optional[Dict[str, Any]] = None


class ConnectorCreateRequest(BaseModel):
    """Request to create a new connector"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    server_url: HttpUrl
    auth_type: AuthType = AuthType.NONE
    auth_config: Optional[Dict[str, Any]] = None


class ConnectorUpdateRequest(BaseModel):
    """Request to update a connector"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class ConnectorTestRequest(BaseModel):
    """Request to test a connector before saving"""
    server_url: HttpUrl
    auth_type: AuthType = AuthType.NONE
    auth_config: Optional[Dict[str, Any]] = None


class ConnectorTestResponse(BaseModel):
    """Response from connection test"""
    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    tools: Optional[List[DiscoveredTool]] = None


class ConnectorToggleRequest(BaseModel):
    """Request to enable/disable a connector"""
    is_active: bool


class ConnectorResponse(BaseModel):
    """Full connector response"""
    id: int
    name: str
    description: Optional[str]
    server_url: str
    auth_type: str
    is_active: bool
    is_verified: bool
    discovered_tools: Optional[List[DiscoveredTool]] = None
    tool_count: int = 0
    last_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConnectorListResponse(BaseModel):
    """List of user's connectors"""
    connectors: List[ConnectorResponse]
    total: int


class DeleteResponse(BaseModel):
    """Generic delete response"""
    success: bool
    message: str


# --- Combined Tools Response (for Apps Menu) ---

class AppsTool(BaseModel):
    """Tool for Apps menu display"""
    id: str
    name: str
    description: Optional[str]
    type: str  # 'system' or 'connector'
    connector_id: Optional[int] = None  # For connector tools
    connector_name: Optional[str] = None
    is_connected: bool
    icon: Optional[str] = None


class AppsMenuResponse(BaseModel):
    """Response for Apps menu with all available tools"""
    system_tools: List[SystemToolResponse]
    user_connectors: List[ConnectorResponse]
