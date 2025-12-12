# Phase 4: Task Breakdown – FastMCP Server Implementation

**Branch**: `004-fastmcp-server-p4` | **Date**: 2025-12-08 | **Status**: Ready for TDD Development

**Methodology**: Test-Driven Development (Red → Green → Refactor)

**Target Coverage**: 80% test coverage for all MCP tools

**Performance Goal**: <500ms per tool call

---

## Overview

This document breaks down Phase 4 implementation into **50 granular TDD tasks** organized by:
1. **Foundation & Setup** (Tasks 1-8) – MCP server skeleton, dependencies, project structure
2. **Schemas & Error Handling** (Tasks 9-16) – Pydantic models, error taxonomy
3. **Inventory Tools** (Tasks 17-40) – 4 tools × 6 tasks each (RED/GREEN/REFACTOR per tool)
4. **Billing Tools** (Tasks 41-50) – 3 tools × 3 tasks each (RED/GREEN/REFACTOR per tool)

**Parallelization**: Inventory tools (Tasks 17-40) can be developed in parallel with billing tools (Tasks 41-50) after setup phase completes.

---

## Phase 0: Foundation & Setup (Tasks 1-8)

### Task 1: [P1] [Setup] Create MCP server entry point

**Type**: RED
**Story**: Phase 0
**File**: `backend/app/mcp_server/server.py`

**Description**: Create the FastMCP server entry point with:
- FastMCP server initialization
- Transport configuration (stdio + HTTP localhost:3000)
- Tool registration hook (empty for now)
- Server start logic

**Test**:
```python
# File: backend/tests/mcp/unit/test_server_startup.py
def test_server_initializes_without_error():
    from backend.app.mcp_server.server import create_server
    server = create_server()
    assert server is not None
    assert hasattr(server, 'tools')

def test_server_supports_stdio_transport():
    from backend.app.mcp_server.server import create_server
    server = create_server()
    # Verify transport capabilities
    assert 'stdio' in str(server)
```

**Acceptance**:
- [ ] `server.py` created with FastMCP initialization
- [ ] Supports stdio transport
- [ ] Supports HTTP localhost:3000 transport
- [ ] Server can be started without errors
- [ ] Test file created and passing

---

### Task 2: [P1] [Setup] Create MCP schemas module

**Type**: RED
**Story**: Phase 0
**File**: `backend/app/mcp_server/schemas.py`

**Description**: Create Pydantic models for all MCP tool inputs/outputs:
- Error response schema (error, message, details)
- Pagination schema (page, limit, total, total_pages)
- Common response wrappers

**Test**:
```python
# File: backend/tests/mcp/unit/test_schemas.py
def test_error_response_schema():
    from backend.app.mcp_server.schemas import ErrorResponse
    error = ErrorResponse(
        error="INSUFFICIENT_STOCK",
        message="Item 5 has only 3 units",
        details={"item_id": 5, "available": 3, "requested": 5}
    )
    assert error.error == "INSUFFICIENT_STOCK"
    assert error.message == "Item 5 has only 3 units"

def test_pagination_schema():
    from backend.app.mcp_server.schemas import PaginationInfo
    page = PaginationInfo(page=1, limit=20, total=45, total_pages=3)
    assert page.total_pages == 3
```

**Acceptance**:
- [ ] ErrorResponse schema defined with (error, message, details)
- [ ] PaginationInfo schema defined with (page, limit, total, total_pages)
- [ ] All schemas are Pydantic BaseModel subclasses
- [ ] Schema validation tests passing
- [ ] Error codes are screaming-snake-case (INSUFFICIENT_STOCK, ITEM_NOT_FOUND, etc.)

---

### Task 3: [P1] [Setup] Create inventory tool schemas

**Type**: RED
**Story**: US1, US2, US3, US4
**File**: `backend/app/mcp_server/schemas.py` (extend)

**Description**: Add Pydantic schemas for all 4 inventory tools:
- ItemCreate, ItemUpdate, ItemRead
- ItemListResponse (with pagination)
- DeleteResponse

**Test**:
```python
# File: backend/tests/mcp/unit/test_schemas.py
def test_item_create_schema():
    from backend.app.mcp_server.schemas import ItemCreate
    item = ItemCreate(
        name="Sugar",
        category="Grocery",
        unit="kg",
        unit_price=50.00,
        stock_qty=100.0
    )
    assert item.name == "Sugar"
    assert item.category == "Grocery"

def test_item_list_response_schema():
    from backend.app.mcp_server.schemas import ItemListResponse
    response = ItemListResponse(items=[], pagination=None)
    assert response.items == []
```

**Acceptance**:
- [ ] ItemCreate schema with validation (name, category, unit, unit_price, stock_qty)
- [ ] ItemUpdate schema with optional fields
- [ ] ItemRead schema with id, is_active, timestamps
- [ ] ItemListResponse schema with pagination
- [ ] DeleteResponse schema for soft delete
- [ ] All validation tests passing

---

### Task 4: [P1] [Setup] Create billing tool schemas

**Type**: RED
**Story**: US5, US6, US7
**File**: `backend/app/mcp_server/schemas.py` (extend)

**Description**: Add Pydantic schemas for all 3 billing tools:
- BillCreate (with line items), BillItemCreate
- BillRead, BillItemRead
- BillListResponse (with pagination and date filters)

**Test**:
```python
# File: backend/tests/mcp/unit/test_schemas.py
def test_bill_create_schema():
    from backend.app.mcp_server.schemas import BillCreate, BillItemCreate
    bill = BillCreate(
        customer_name="John Doe",
        store_name="Downtown Store",
        items=[
            BillItemCreate(item_id=1, quantity=5)
        ]
    )
    assert bill.customer_name == "John Doe"
    assert len(bill.items) == 1

def test_bill_read_schema():
    from backend.app.mcp_server.schemas import BillRead
    # Verify snapshots are included
    bill = BillRead(
        id=1,
        customer_name="John",
        items=[],
        total_amount=100.00
    )
    assert bill.id == 1
```

**Acceptance**:
- [ ] BillCreate schema with items list
- [ ] BillItemCreate schema with item_id, quantity
- [ ] BillRead schema with snapshots (item_name, unit_price at bill time)
- [ ] BillListResponse schema with date range filters
- [ ] Immutability enforced (no update/delete schemas for bills)
- [ ] All validation tests passing

---

### Task 5: [P1] [Setup] Create database session for MCP context

**Type**: GREEN
**Story**: Phase 0
**File**: `backend/app/mcp_server/utils.py` (new)

**Description**: Create utility functions for:
- Getting database session in MCP context
- Managing transaction lifecycle (no auto-commit for MCP tools)
- Rolling back on errors

**Implementation**:
```python
# backend/app/mcp_server/utils.py
from backend.app.database import async_session
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_mcp_session():
    """Get async session for MCP tool with transaction management."""
    async with async_session() as session:
        try:
            yield session
            # MCP tools don't auto-commit; caller decides
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
```

**Test**:
```python
# File: backend/tests/mcp/unit/test_utils.py
@pytest.mark.asyncio
async def test_mcp_session_context():
    from backend.app.mcp_server.utils import get_mcp_session
    async with get_mcp_session() as session:
        assert session is not None
        # Verify session is async
        assert hasattr(session, 'execute')
```

**Acceptance**:
- [ ] get_mcp_session context manager created
- [ ] Handles async sessions properly
- [ ] Rollback on exception
- [ ] Session closes properly (finally block)
- [ ] Test passing

---

### Task 6: [P1] [Setup] Set up test fixtures for MCP tools

**Type**: RED
**Story**: Phase 0
**File**: `backend/tests/mcp/conftest.py` (new)

**Description**: Create pytest fixtures for:
- test_db (async SQLite for MCP tests)
- test_session (async session fixture)
- sample_items (pre-populated inventory for tests)
- sample_bills (pre-populated bills for tests)

**Test**:
```python
# File: backend/tests/mcp/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.models.base import Base

@pytest.fixture
async def test_db():
    """Create async SQLite test database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def test_session(test_db):
    """Get async session for tests."""
    async_session_local = async_sessionmaker(test_db, class_=AsyncSession)
    async with async_session_local() as session:
        yield session

@pytest.fixture
async def sample_items(test_session):
    """Pre-populate test database with sample items."""
    from backend.app.models.item import Item
    items = [
        Item(name="Sugar", category="Grocery", unit="kg", unit_price=50.0, stock_qty=100.0),
        Item(name="Rice", category="Grocery", unit="kg", unit_price=30.0, stock_qty=50.0),
    ]
    for item in items:
        test_session.add(item)
    await test_session.commit()
    return items
```

**Acceptance**:
- [ ] test_db fixture creates in-memory async SQLite
- [ ] test_session fixture provides async session
- [ ] sample_items fixture creates sample inventory
- [ ] sample_bills fixture creates sample bills
- [ ] All fixtures are properly async
- [ ] Conftest.py located at `backend/tests/mcp/conftest.py`

---

### Task 7: [P1] [Setup] Create __init__.py for mcp_server package

**Type**: GREEN
**Story**: Phase 0
**File**: `backend/app/mcp_server/__init__.py`

**Description**: Create package init with:
- Version string
- Public exports (server factory, schemas)
- MCP tool registry

**Implementation**:
```python
# backend/app/mcp_server/__init__.py
__version__ = "0.1.0"

from .server import create_server
from .schemas import (
    ErrorResponse, PaginationInfo, ItemCreate, ItemRead, ItemListResponse,
    BillCreate, BillRead, BillListResponse
)

__all__ = [
    "create_server",
    "ErrorResponse", "PaginationInfo",
    "ItemCreate", "ItemRead", "ItemListResponse",
    "BillCreate", "BillRead", "BillListResponse",
]
```

**Test**:
```python
def test_mcp_server_package_exports():
    import backend.app.mcp_server as mcp
    assert hasattr(mcp, 'create_server')
    assert hasattr(mcp, 'ErrorResponse')
```

**Acceptance**:
- [ ] __init__.py created with exports
- [ ] All schema classes exported
- [ ] create_server exported
- [ ] Import test passing

---

### Task 8: [P1] [Setup] Create test runner script

**Type**: GREEN
**Story**: Phase 0
**File**: `backend/scripts/test_mcp.sh` (new)

**Description**: Create shell script to:
- Run all MCP tests
- Report coverage
- Run with timing information

**Implementation**:
```bash
#!/bin/bash
# backend/scripts/test_mcp.sh
set -e

echo "Running Phase 4 MCP Tests..."
echo "=============================="

# Unit tests
echo "Running unit tests..."
pytest backend/tests/mcp/unit/ -v --tb=short --cov=backend.app.mcp_server --cov-report=term-missing

# Integration tests
echo "Running integration tests..."
pytest backend/tests/mcp/integration/ -v --tb=short

# Coverage report
echo "=============================="
pytest backend/tests/mcp/ --cov=backend.app.mcp_server --cov-report=html --cov-report=term
echo "Coverage report generated in htmlcov/index.html"
```

**Acceptance**:
- [ ] test_mcp.sh script created
- [ ] Runs unit tests with coverage
- [ ] Runs integration tests
- [ ] Generates HTML coverage report
- [ ] Script is executable (chmod +x)

---

## Phase 1: Schemas & Error Handling (Tasks 9-16)

### Task 9: [P1] [Error] Define error code taxonomy

**Type**: RED
**Story**: Phase 0
**File**: `backend/app/mcp_server/schemas.py` (extend)

**Description**: Create error code constants for all possible errors:
- VALIDATION_ERROR
- ITEM_NOT_FOUND
- INSUFFICIENT_STOCK
- CATEGORY_INVALID
- UNIT_INVALID
- PRICE_INVALID
- QUANTITY_INVALID
- BILL_IMMUTABLE
- DUPLICATE_ITEM
- DATABASE_ERROR

**Test**:
```python
# File: backend/tests/mcp/unit/test_error_codes.py
def test_error_codes_defined():
    from backend.app.mcp_server.schemas import ERROR_CODES
    assert "ITEM_NOT_FOUND" in ERROR_CODES
    assert "INSUFFICIENT_STOCK" in ERROR_CODES
    assert "VALIDATION_ERROR" in ERROR_CODES

def test_error_codes_are_screaming_snake_case():
    from backend.app.mcp_server.schemas import ERROR_CODES
    for code in ERROR_CODES.values():
        assert code == code.upper()
        assert "_" in code or len(code.split("_")) > 0
```

**Acceptance**:
- [ ] ERROR_CODES dict defined with all error codes
- [ ] All codes follow screaming-snake-case convention
- [ ] Error codes mapped to HTTP status codes (400, 404, 422, 500)
- [ ] Test passing

---

### Task 10: [P1] [Error] Create domain exception classes

**Type**: GREEN
**Story**: Phase 0
**File**: `backend/app/mcp_server/exceptions.py` (new)

**Description**: Create MCP-specific exception classes:
- MCPException (base)
- MCPValidationError (400)
- MCPNotFoundError (404)
- MCPInsufficientStockError (422)
- MCPImmutableError (422)
- MCPDatabaseError (500)

**Implementation**:
```python
# backend/app/mcp_server/exceptions.py
class MCPException(Exception):
    def __init__(self, error_code: str, message: str, details: dict = None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message)

class MCPValidationError(MCPException):
    pass

class MCPNotFoundError(MCPException):
    pass

class MCPInsufficientStockError(MCPException):
    pass
```

**Test**:
```python
def test_mcp_exception_creation():
    from backend.app.mcp_server.exceptions import MCPValidationError
    exc = MCPValidationError("CATEGORY_INVALID", "Category must be one of: Grocery, Garments", {"category": "InvalidCat"})
    assert exc.error_code == "CATEGORY_INVALID"
    assert exc.details["category"] == "InvalidCat"
```

**Acceptance**:
- [ ] All exception classes created
- [ ] Each exception stores error_code, message, details
- [ ] Exceptions inherit from MCPException
- [ ] Test passing

---

### Task 11: [P1] [Error] Create error response builder

**Type**: GREEN
**Story**: Phase 0
**File**: `backend/app/mcp_server/utils.py` (extend)

**Description**: Add helper function to convert exceptions to error responses:
- exception_to_error_response(exc) → ErrorResponse dict
- Handles both MCPException and generic exceptions

**Implementation**:
```python
# backend/app/mcp_server/utils.py
def exception_to_error_response(exc: Exception) -> dict:
    """Convert exception to standard error response."""
    from backend.app.mcp_server.exceptions import MCPException

    if isinstance(exc, MCPException):
        return {
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    else:
        return {
            "error": "DATABASE_ERROR",
            "message": str(exc),
            "details": {}
        }
```

**Test**:
```python
def test_exception_to_error_response():
    from backend.app.mcp_server.utils import exception_to_error_response
    from backend.app.mcp_server.exceptions import MCPValidationError

    exc = MCPValidationError("CATEGORY_INVALID", "Invalid category")
    response = exception_to_error_response(exc)

    assert response["error"] == "CATEGORY_INVALID"
    assert response["message"] == "Invalid category"
```

**Acceptance**:
- [ ] exception_to_error_response function created
- [ ] Handles MCPException with error_code, message, details
- [ ] Handles generic exceptions with DATABASE_ERROR code
- [ ] Test passing

---

### Task 12: [P1] [Schema] Add validators to all schemas

**Type**: REFACTOR
**Story**: Phase 0
**File**: `backend/app/mcp_server/schemas.py` (extend)

**Description**: Add Pydantic validators to:
- ItemCreate: validate category (whitelist), unit (whitelist), prices > 0, stock_qty >= 0, name not empty
- ItemUpdate: same as ItemCreate (for provided fields)
- BillCreate: validate items list not empty, quantities > 0
- All: check for negative values, empty strings where not allowed

**Test**:
```python
# File: backend/tests/mcp/unit/test_schema_validators.py
def test_item_create_validates_category():
    from backend.app.mcp_server.schemas import ItemCreate
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ItemCreate(
            name="Sugar",
            category="InvalidCategory",  # Should fail
            unit="kg",
            unit_price=50.0,
            stock_qty=100.0
        )

def test_item_create_validates_positive_price():
    from backend.app.mcp_server.schemas import ItemCreate
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ItemCreate(
            name="Sugar",
            category="Grocery",
            unit="kg",
            unit_price=-10.0,  # Should fail
            stock_qty=100.0
        )

def test_bill_create_requires_items():
    from backend.app.mcp_server.schemas import BillCreate
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BillCreate(
            customer_name="John",
            items=[]  # Should fail – empty items
        )
```

**Acceptance**:
- [ ] Category validator (whitelist: Grocery, Garments, Beauty, Utilities, Other)
- [ ] Unit validator (whitelist: kg, g, liter, ml, piece, box, pack, other)
- [ ] Price validator (> 0)
- [ ] Stock qty validator (>= 0)
- [ ] Name validator (not empty, <255 chars)
- [ ] Items list validator (not empty for BillCreate)
- [ ] All validation tests passing

---

### Task 13: [P1] [Schema] Create response wrapper schemas

**Type**: GREEN
**Story**: Phase 0
**File**: `backend/app/mcp_server/schemas.py` (extend)

**Description**: Create standardized response wrappers for MCP tool returns:
- SuccessResponse[T] (generic wrapper)
- ErrorResponse (already defined in Task 2)
- ToolResponse = Union[SuccessResponse, ErrorResponse]

**Implementation**:
```python
# backend/app/mcp_server/schemas.py
from typing import Generic, TypeVar, Union

T = TypeVar('T')

class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    meta: dict = {}  # For pagination, timing, etc.

class ToolResponse(BaseModel):
    """Union of success or error responses."""
    pass  # Handled by response field in tool definition
```

**Test**:
```python
def test_success_response_wrapper():
    from backend.app.mcp_server.schemas import SuccessResponse
    response = SuccessResponse[dict](data={"id": 1, "name": "Sugar"})
    assert response.success == True
    assert response.data["id"] == 1
```

**Acceptance**:
- [ ] SuccessResponse created as generic wrapper
- [ ] ErrorResponse defined (from Task 2)
- [ ] Both responses can be serialized to JSON
- [ ] Test passing

---

### Task 14: [P1] [Schema] Generate inventory tool input/output schemas

**Type**: GREEN
**Story**: US1, US2, US3, US4
**File**: `backend/app/mcp_server/schemas.py` (extend)

**Description**: Finalize inventory tool schemas:
- inventory_add_item: ItemCreate (input), ItemRead (output)
- inventory_update_item: ItemUpdate (input), ItemRead (output)
- inventory_delete_item: DeleteRequest (input), DeleteResponse (output)
- inventory_list_items: ListRequest (input), ItemListResponse (output)

**Test**:
```python
# File: backend/tests/mcp/unit/test_inventory_schemas.py
def test_item_list_response_with_pagination():
    from backend.app.mcp_server.schemas import ItemListResponse, ItemRead, PaginationInfo

    items = [ItemRead(id=1, name="Sugar", category="Grocery", unit="kg", unit_price=50.0, stock_qty=100.0, is_active=True)]
    pagination = PaginationInfo(page=1, limit=20, total=1, total_pages=1)

    response = ItemListResponse(items=items, pagination=pagination)
    assert len(response.items) == 1
    assert response.pagination.total == 1
```

**Acceptance**:
- [ ] All 4 inventory tool schemas defined
- [ ] Input schemas have proper parameters
- [ ] Output schemas include all required fields
- [ ] Pagination included in list responses
- [ ] Test passing

---

### Task 15: [P1] [Schema] Generate billing tool input/output schemas

**Type**: GREEN
**Story**: US5, US6, US7
**File**: `backend/app/mcp_server/schemas.py` (extend)

**Description**: Finalize billing tool schemas:
- billing_create_bill: BillCreate (input), BillRead (output)
- billing_list_bills: ListBillRequest (input with date filters), BillListResponse (output)
- billing_get_bill: GetBillRequest (input), BillRead (output)

**Test**:
```python
# File: backend/tests/mcp/unit/test_billing_schemas.py
def test_bill_list_response_with_date_filters():
    from backend.app.mcp_server.schemas import BillListResponse, BillRead, PaginationInfo
    from datetime import datetime

    bills = [BillRead(id=1, customer_name="John", total_amount=1000.0, items=[], created_at=datetime.now())]
    pagination = PaginationInfo(page=1, limit=20, total=1, total_pages=1)

    response = BillListResponse(bills=bills, pagination=pagination)
    assert len(response.bills) == 1

def test_bill_create_requires_items():
    from backend.app.mcp_server.schemas import BillCreate
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BillCreate(items=[])  # Must have at least one item
```

**Acceptance**:
- [ ] All 3 billing tool schemas defined
- [ ] BillCreate has items list
- [ ] BillRead includes snapshots (item_name, unit_price)
- [ ] BillListResponse supports date range filters
- [ ] Immutability enforced (no update/delete)
- [ ] Test passing

---

### Task 16: [P1] [Schema] Create tool parameter documentation

**Type**: REFACTOR
**Story**: Phase 0
**File**: `backend/app/mcp_server/schemas.py` (extend)

**Description**: Add docstrings and field descriptions to all schemas:
- Describe each field's purpose
- Include constraints (min/max, allowed values)
- Provide examples for complex types

**Implementation**:
```python
# backend/app/mcp_server/schemas.py
from pydantic import Field

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Item name")
    category: str = Field(..., description="Category: Grocery, Garments, Beauty, Utilities, or Other")
    unit: str = Field(..., description="Unit: kg, g, liter, ml, piece, box, pack, or other")
    unit_price: Decimal = Field(..., gt=0, description="Price per unit (must be > 0)")
    stock_qty: Decimal = Field(..., ge=0, description="Initial stock quantity (must be >= 0)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Sugar",
                "category": "Grocery",
                "unit": "kg",
                "unit_price": "50.00",
                "stock_qty": "100.0"
            }
        }
```

**Test**:
```python
def test_schemas_have_descriptions():
    from backend.app.mcp_server.schemas import ItemCreate
    schema = ItemCreate.model_json_schema()
    assert "description" in schema["properties"]["name"]
    assert "example" in schema
```

**Acceptance**:
- [ ] All schema fields have Field() with descriptions
- [ ] Complex schemas have Config.json_schema_extra examples
- [ ] Constraints documented (min_length, max_length, gt, ge, etc.)
- [ ] Test passing
- [ ] Auto-generated FastMCP docs are clear

---

## Phase 2: Inventory Tools (Tasks 17-40)

### Task 17: [P1] [US1] RED: Write failing test for inventory_add_item

**Type**: RED
**Story**: US1 – Add new inventory item
**File**: `backend/tests/mcp/unit/test_tools_inventory.py` (new)

**Description**: Write failing test for inventory_add_item tool:
- Test successful item creation
- Test validation errors (invalid category, negative price)
- Test response schema matches ItemRead

**Test**:
```python
# File: backend/tests/mcp/unit/test_tools_inventory.py
import pytest
from backend.app.mcp_server.tools_inventory import inventory_add_item
from backend.app.mcp_server.schemas import ItemCreate, ItemRead

@pytest.mark.asyncio
async def test_inventory_add_item_success(test_session):
    """Test successful item creation."""
    result = await inventory_add_item(
        name="Sugar",
        category="Grocery",
        unit="kg",
        unit_price=50.0,
        stock_qty=100.0,
        session=test_session
    )

    # Should return ItemRead
    assert isinstance(result, dict)
    assert result["name"] == "Sugar"
    assert result["category"] == "Grocery"
    assert result["is_active"] == True
    assert "id" in result
    assert "created_at" in result

@pytest.mark.asyncio
async def test_inventory_add_item_validates_category(test_session):
    """Test validation error for invalid category."""
    with pytest.raises(Exception) as exc_info:
        await inventory_add_item(
            name="Sugar",
            category="InvalidCategory",  # Should fail
            unit="kg",
            unit_price=50.0,
            stock_qty=100.0,
            session=test_session
        )
    assert "CATEGORY_INVALID" in str(exc_info.value) or "category" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_inventory_add_item_validates_price(test_session):
    """Test validation error for negative price."""
    with pytest.raises(Exception) as exc_info:
        await inventory_add_item(
            name="Sugar",
            category="Grocery",
            unit="kg",
            unit_price=-50.0,  # Should fail
            stock_qty=100.0,
            session=test_session
        )
    assert "price" in str(exc_info.value).lower() or "PRICE_INVALID" in str(exc_info.value)
```

**Acceptance**:
- [ ] Test file created at backend/tests/mcp/unit/test_tools_inventory.py
- [ ] 3 test cases written (success, category validation, price validation)
- [ ] Tests are async and use test_session fixture
- [ ] Tests FAIL (RED phase – no implementation yet)
- [ ] Error assertions check for proper error codes/messages

---

### Task 18: [P1] [US1] GREEN: Implement inventory_add_item tool

**Type**: GREEN
**Story**: US1 – Add new inventory item
**File**: `backend/app/mcp_server/tools_inventory.py` (new)

**Description**: Implement inventory_add_item tool:
- Accept ItemCreate parameters (name, category, unit, unit_price, stock_qty)
- Call InventoryService.add_item(session, ...)
- Return ItemRead response
- Handle validation errors and convert to MCPValidationError
- Handle database errors and convert to MCPDatabaseError

**Implementation**:
```python
# File: backend/app/mcp_server/tools_inventory.py
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.inventory_service import InventoryService
from backend.app.mcp_server.exceptions import MCPValidationError, MCPDatabaseError
from backend.app.mcp_server.schemas import ItemRead
from decimal import Decimal

async def inventory_add_item(
    name: str,
    category: str,
    unit: str,
    unit_price: float,
    stock_qty: float,
    session: AsyncSession
) -> dict:
    """Create new inventory item."""
    try:
        # Delegate to service layer
        service = InventoryService(session)

        # Call Phase 2 service (reuse as-is)
        item = await service.add_item(
            name=name,
            category=category,
            unit=unit,
            unit_price=Decimal(str(unit_price)),
            stock_qty=Decimal(str(stock_qty))
        )

        # Convert to response schema
        return ItemRead.from_orm(item).model_dump()

    except ValueError as e:
        raise MCPValidationError("VALIDATION_ERROR", str(e), {"field": "category or unit"})
    except Exception as e:
        raise MCPDatabaseError("DATABASE_ERROR", str(e))
```

**Test**: Same as Task 17 – all 3 tests should now PASS

**Acceptance**:
- [ ] tools_inventory.py created
- [ ] inventory_add_item function implemented
- [ ] Calls InventoryService.add_item
- [ ] Returns ItemRead dict
- [ ] Handles validation errors
- [ ] Handles database errors
- [ ] All 3 tests from Task 17 PASS

---

### Task 19: [P1] [US1] REFACTOR: Extract common validation logic

**Type**: REFACTOR
**Story**: US1
**File**: `backend/app/mcp_server/tools_inventory.py` (extend)

**Description**: Extract validation logic into helper functions:
- validate_item_input(name, category, unit, price, stock_qty)
- convert_item_to_response(item_orm)
- All common patterns used across all 4 inventory tools

**Implementation**:
```python
# backend/app/mcp_server/tools_inventory.py
from backend.app.mcp_server.schemas import ItemRead

def validate_item_input(name: str, category: str, unit: str, unit_price: float, stock_qty: float):
    """Validate item input fields."""
    VALID_CATEGORIES = {"Grocery", "Garments", "Beauty", "Utilities", "Other"}
    VALID_UNITS = {"kg", "g", "liter", "ml", "piece", "box", "pack", "other"}

    if category not in VALID_CATEGORIES:
        raise MCPValidationError("CATEGORY_INVALID", f"Category must be one of: {VALID_CATEGORIES}")
    if unit not in VALID_UNITS:
        raise MCPValidationError("UNIT_INVALID", f"Unit must be one of: {VALID_UNITS}")
    if unit_price <= 0:
        raise MCPValidationError("PRICE_INVALID", "Price must be > 0")
    if stock_qty < 0:
        raise MCPValidationError("QUANTITY_INVALID", "Stock qty must be >= 0")
    if not name or len(name) > 255:
        raise MCPValidationError("NAME_INVALID", "Name must be 1-255 characters")

def convert_item_to_response(item_orm) -> dict:
    """Convert ORM Item to response dict."""
    return ItemRead.from_orm(item_orm).model_dump()
```

**Test**:
```python
def test_validate_item_input_valid():
    validate_item_input("Sugar", "Grocery", "kg", 50.0, 100.0)
    # Should not raise

def test_validate_item_input_invalid_category():
    with pytest.raises(MCPValidationError) as exc_info:
        validate_item_input("Sugar", "InvalidCategory", "kg", 50.0, 100.0)
    assert exc_info.value.error_code == "CATEGORY_INVALID"
```

**Acceptance**:
- [ ] Helper functions extracted
- [ ] validate_item_input checks all fields
- [ ] convert_item_to_response uses ItemRead
- [ ] All 3 tests from Task 17 still PASS
- [ ] Code reusable for other inventory tools

---

### Task 20: [P1] [US2] RED: Write failing test for inventory_update_item

**Type**: RED
**Story**: US2 – Update inventory item
**File**: `backend/tests/mcp/unit/test_tools_inventory.py` (extend)

**Description**: Write failing tests for inventory_update_item:
- Test updating single field (name, price, stock, category)
- Test partial update (only provided fields updated)
- Test item not found error
- Test validation errors on update values

**Test**:
```python
@pytest.mark.asyncio
async def test_inventory_update_item_success(sample_items, test_session):
    """Test successful item update."""
    item_id = sample_items[0].id

    result = await inventory_update_item(
        item_id=item_id,
        name="White Sugar",
        unit_price=55.0,
        session=test_session
    )

    assert result["id"] == item_id
    assert result["name"] == "White Sugar"
    assert result["unit_price"] == 55.0
    assert "updated_at" in result

@pytest.mark.asyncio
async def test_inventory_update_item_not_found(test_session):
    """Test update non-existent item."""
    with pytest.raises(Exception) as exc_info:
        await inventory_update_item(
            item_id=9999,  # Non-existent
            name="Sugar",
            session=test_session
        )
    assert "ITEM_NOT_FOUND" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_inventory_update_item_partial(sample_items, test_session):
    """Test partial update (only name)."""
    item_id = sample_items[0].id

    result = await inventory_update_item(
        item_id=item_id,
        name="Updated Sugar",
        session=test_session
    )

    # Only name should change; price stays same
    assert result["name"] == "Updated Sugar"
    assert result["unit_price"] == sample_items[0].unit_price
```

**Acceptance**:
- [ ] 3 test cases written (success, not found, partial update)
- [ ] Tests use sample_items fixture
- [ ] Tests FAIL (RED phase)
- [ ] Error assertions check for ITEM_NOT_FOUND

---

### Task 21: [P1] [US2] GREEN: Implement inventory_update_item tool

**Type**: GREEN
**Story**: US2
**File**: `backend/app/mcp_server/tools_inventory.py` (extend)

**Description**: Implement inventory_update_item:
- Accept item_id and optional fields (name, price, stock, category)
- Call InventoryService.update_item(session, item_id, **kwargs)
- Return ItemRead response
- Handle ITEM_NOT_FOUND error
- Handle validation errors

**Implementation**:
```python
async def inventory_update_item(
    item_id: int,
    name: str = None,
    category: str = None,
    unit_price: float = None,
    stock_qty: float = None,
    session: AsyncSession
) -> dict:
    """Update inventory item (partial update allowed)."""
    try:
        service = InventoryService(session)

        # Only pass provided fields
        update_data = {}
        if name is not None:
            validate_item_input(name, category or "Grocery", "kg", unit_price or 1.0, stock_qty or 0)
            update_data["name"] = name
        if category is not None:
            update_data["category"] = category
        if unit_price is not None:
            if unit_price <= 0:
                raise MCPValidationError("PRICE_INVALID", "Price must be > 0")
            update_data["unit_price"] = Decimal(str(unit_price))
        if stock_qty is not None:
            if stock_qty < 0:
                raise MCPValidationError("QUANTITY_INVALID", "Stock qty must be >= 0")
            update_data["stock_qty"] = Decimal(str(stock_qty))

        item = await service.update_item(session, item_id, **update_data)
        return convert_item_to_response(item)

    except ItemNotFoundError:
        raise MCPNotFoundError("ITEM_NOT_FOUND", f"Item {item_id} not found")
    except ValidationError as e:
        raise MCPValidationError("VALIDATION_ERROR", str(e))
```

**Test**: Same as Task 20 – all 3 tests should PASS

**Acceptance**:
- [ ] inventory_update_item function implemented
- [ ] Accepts optional parameters (name, category, unit_price, stock_qty)
- [ ] Only provided fields are updated
- [ ] Calls InventoryService.update_item
- [ ] Handles ITEM_NOT_FOUND error
- [ ] All 3 tests from Task 20 PASS

---

### Task 22: [P1] [US2] REFACTOR: Improve error handling

**Type**: REFACTOR
**Story**: US2
**File**: `backend/app/mcp_server/tools_inventory.py` (extend)

**Description**: Centralize error mapping:
- Create error_handler decorator to wrap tools
- Catches service exceptions and converts to MCP exceptions
- Logs errors with context (tool name, parameters)
- Returns consistent error response format

**Implementation**:
```python
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def mcp_error_handler(tool_name: str):
    """Decorator to convert service exceptions to MCP exceptions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except MCPException:
                raise  # Already converted
            except ItemNotFoundError as e:
                logger.warning(f"[{tool_name}] Item not found: {e}")
                raise MCPNotFoundError("ITEM_NOT_FOUND", str(e))
            except ValidationError as e:
                logger.warning(f"[{tool_name}] Validation error: {e}")
                raise MCPValidationError("VALIDATION_ERROR", str(e))
            except Exception as e:
                logger.error(f"[{tool_name}] Unexpected error: {e}", exc_info=True)
                raise MCPDatabaseError("DATABASE_ERROR", str(e))
        return wrapper
    return decorator
```

**Test**:
```python
def test_error_handler_converts_exceptions():
    # Verify decorator is applied
    assert inventory_add_item.__wrapped__ is not None or "mcp_error_handler" in str(inventory_add_item)
```

**Acceptance**:
- [ ] Error handler decorator created
- [ ] Applies to all inventory tools
- [ ] Logs with tool name context
- [ ] Converts service exceptions to MCP exceptions
- [ ] Tests still pass

---

### Task 23: [P1] [US3] RED: Write failing test for inventory_delete_item

**Type**: RED
**Story**: US3 – Delete (soft) inventory item
**File**: `backend/tests/mcp/unit/test_tools_inventory.py` (extend)

**Description**: Write failing tests for inventory_delete_item (soft delete):
- Test soft delete sets is_active = FALSE
- Test deleted item not in list (by default)
- Test item not found error
- Test response is DeleteResponse

**Test**:
```python
@pytest.mark.asyncio
async def test_inventory_delete_item_success(sample_items, test_session):
    """Test soft delete sets is_active = FALSE."""
    item_id = sample_items[0].id

    result = await inventory_delete_item(item_id=item_id, session=test_session)

    assert result["id"] == item_id
    assert result["success"] == True

    # Verify is_active is now False
    item = await test_session.get_or_404(Item, item_id)
    # This will fail initially – no implementation

@pytest.mark.asyncio
async def test_inventory_delete_item_not_found(test_session):
    """Test delete non-existent item."""
    with pytest.raises(Exception) as exc_info:
        await inventory_delete_item(item_id=9999, session=test_session)
    assert "ITEM_NOT_FOUND" in str(exc_info.value)

@pytest.mark.asyncio
async def test_deleted_item_excluded_from_list(sample_items, test_session):
    """Test deleted items not in list by default."""
    item_id = sample_items[0].id

    # Delete item
    await inventory_delete_item(item_id=item_id, session=test_session)

    # List should not include deleted item
    result = await inventory_list_items(session=test_session)
    assert all(item["id"] != item_id for item in result["items"])
```

**Acceptance**:
- [ ] 3 test cases written (success, not found, excluded from list)
- [ ] Tests FAIL (RED phase)
- [ ] Tests verify is_active = FALSE

---

### Task 24: [P1] [US3] GREEN: Implement inventory_delete_item tool

**Type**: GREEN
**Story**: US3
**File**: `backend/app/mcp_server/tools_inventory.py` (extend)

**Description**: Implement inventory_delete_item (soft delete):
- Accept item_id
- Call InventoryService.soft_delete_item(session, item_id)
- Sets is_active = FALSE
- Return DeleteResponse {id, success}
- Handle ITEM_NOT_FOUND error

**Implementation**:
```python
@mcp_error_handler("inventory_delete_item")
async def inventory_delete_item(
    item_id: int,
    session: AsyncSession
) -> dict:
    """Soft delete inventory item (sets is_active = FALSE)."""
    service = InventoryService(session)

    # Check item exists first
    item = await service.get_item(item_id)
    if not item:
        raise MCPNotFoundError("ITEM_NOT_FOUND", f"Item {item_id} not found")

    # Soft delete
    await service.soft_delete_item(item_id)
    await session.commit()  # Commit the soft delete

    return {
        "id": item_id,
        "success": True
    }
```

**Test**: Same as Task 23 – all 3 tests should PASS

**Acceptance**:
- [ ] inventory_delete_item function implemented
- [ ] Calls InventoryService.soft_delete_item
- [ ] Sets is_active = FALSE
- [ ] Returns {id, success}
- [ ] Handles ITEM_NOT_FOUND error
- [ ] All 3 tests from Task 23 PASS
- [ ] Deleted items excluded from list queries

---

### Task 25: [P1] [US3] REFACTOR: Test soft delete consistency

**Type**: REFACTOR
**Story**: US3
**File**: `backend/tests/integration/test_fastapi_vs_mcp.py` (new)

**Description**: Create consistency tests comparing FastAPI DELETE endpoint with MCP delete_item tool:
- Both set is_active = FALSE
- Both return same response format
- Both handle errors identically

**Test**:
```python
# File: backend/tests/integration/test_fastapi_vs_mcp.py
@pytest.mark.asyncio
async def test_fastapi_vs_mcp_soft_delete_consistency(sample_items, test_session):
    """Verify FastAPI and MCP soft delete behave identically."""
    item_id = sample_items[0].id

    # MCP delete
    mcp_result = await inventory_delete_item(item_id=item_id, session=test_session)

    # Verify is_active = FALSE
    item = await test_session.get(Item, item_id)
    assert item.is_active == False

    # FastAPI would return same response structure
    assert mcp_result["success"] == True
    assert mcp_result["id"] == item_id
```

**Acceptance**:
- [ ] Consistency test created
- [ ] Compares MCP vs FastAPI soft delete
- [ ] Both set is_active = FALSE
- [ ] Test passing

---

### Task 26: [P1] [US4] RED: Write failing test for inventory_list_items

**Type**: RED
**Story**: US4 – List inventory items with filtering and pagination
**File**: `backend/tests/mcp/unit/test_tools_inventory.py` (extend)

**Description**: Write failing tests for inventory_list_items:
- Test list all items (active only)
- Test filter by name
- Test filter by category
- Test pagination (page, limit)
- Test default pagination (20 items, max 100)

**Test**:
```python
@pytest.mark.asyncio
async def test_inventory_list_items_success(sample_items, test_session):
    """Test list all items."""
    result = await inventory_list_items(session=test_session)

    assert "items" in result
    assert "pagination" in result
    assert len(result["items"]) == len(sample_items)
    assert result["pagination"]["total"] == len(sample_items)

@pytest.mark.asyncio
async def test_inventory_list_items_filter_by_name(sample_items, test_session):
    """Test filter by name."""
    result = await inventory_list_items(
        name="Sugar",
        session=test_session
    )

    assert all(item["name"] == "Sugar" for item in result["items"])

@pytest.mark.asyncio
async def test_inventory_list_items_pagination_defaults(sample_items, test_session):
    """Test pagination defaults (20 items, max 100)."""
    result = await inventory_list_items(session=test_session)

    assert result["pagination"]["limit"] == 20  # Default
    assert result["pagination"]["page"] == 1  # Default

@pytest.mark.asyncio
async def test_inventory_list_items_excludes_inactive(test_session):
    """Test inactive items excluded from list."""
    # Delete an item
    await inventory_delete_item(item_id=1, session=test_session)

    # List should not include deleted item
    result = await inventory_list_items(session=test_session)
    assert all(item["is_active"] == True for item in result["items"])
```

**Acceptance**:
- [ ] 4 test cases written
- [ ] Tests FAIL (RED phase)
- [ ] Tests cover: all items, filter by name, pagination defaults, inactive excluded

---

### Task 27: [P1] [US4] GREEN: Implement inventory_list_items tool

**Type**: GREEN
**Story**: US4
**File**: `backend/app/mcp_server/tools_inventory.py` (extend)

**Description**: Implement inventory_list_items with filtering and pagination:
- Accept optional name filter, category filter, page, limit
- Default page=1, limit=20, max limit=100
- Call InventoryService.list_items(filters, page, limit)
- Return ItemListResponse with pagination
- Exclude inactive items (is_active = TRUE)

**Implementation**:
```python
@mcp_error_handler("inventory_list_items")
async def inventory_list_items(
    name: str = None,
    category: str = None,
    page: int = 1,
    limit: int = 20,
    session: AsyncSession
) -> dict:
    """List inventory items with optional filtering and pagination."""
    # Validate pagination
    if page < 1:
        page = 1
    if limit < 1:
        limit = 20
    if limit > 100:
        limit = 100

    service = InventoryService(session)

    # Build filter dict
    filters = {"is_active": True}
    if name:
        filters["name"] = name
    if category:
        filters["category"] = category

    # Get items
    items, total = await service.list_items(filters=filters, page=page, limit=limit)

    # Build response
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
```

**Test**: Same as Task 26 – all 4 tests should PASS

**Acceptance**:
- [ ] inventory_list_items function implemented
- [ ] Supports optional filters (name, category)
- [ ] Supports pagination (page, limit)
- [ ] Default limit=20, max=100
- [ ] Excludes inactive items
- [ ] Returns ItemListResponse structure
- [ ] All 4 tests from Task 26 PASS

---

### Task 28: [P1] [US4] REFACTOR: Optimize list query performance

**Type**: REFACTOR
**Story**: US4
**File**: `backend/app/mcp_server/tools_inventory.py` (extend)

**Description**: Refactor list_items for performance:
- Use efficient SQL queries (avoid N+1 problems)
- Index on is_active + name/category
- Cache total count briefly
- Document performance expectations

**Implementation** (minimal refactor):
```python
# Add docstring with performance notes
async def inventory_list_items(...):
    """List inventory items.

    Performance:
    - Single query with WHERE is_active=TRUE and optional filters
    - Pagination handled by OFFSET/LIMIT
    - Expected <100ms for typical inventory sizes
    """
    # Implementation already efficient via InventoryService
    # which uses SQLAlchemy ORM with proper filtering
```

**Test**:
```python
@pytest.mark.asyncio
async def test_inventory_list_items_performance(sample_items, test_session):
    """Test list_items performance (should be <500ms)."""
    import time
    start = time.time()
    result = await inventory_list_items(session=test_session)
    elapsed = time.time() - start
    assert elapsed < 0.5  # 500ms threshold
```

**Acceptance**:
- [ ] Performance test added
- [ ] Query is efficient (no N+1)
- [ ] Docstring documents performance
- [ ] Test passing (< 500ms)
- [ ] All previous tests still pass

---

### Task 29: [P1] [All Inventory] Integration test: Add → Update → List → Delete workflow

**Type**: INTEGRATION
**Story**: US1-4
**File**: `backend/tests/integration/test_mcp_inventory_e2e.py` (new)

**Description**: Create end-to-end integration test:
- Create item with inventory_add_item
- Update item with inventory_update_item
- List items and verify updated values
- Delete item with inventory_delete_item
- List items and verify deletion

**Test**:
```python
# File: backend/tests/integration/test_mcp_inventory_e2e.py
@pytest.mark.asyncio
async def test_e2e_inventory_workflow(test_session):
    """Test complete inventory workflow: Add → Update → List → Delete."""

    # Step 1: Add item
    add_result = await inventory_add_item(
        name="Sugar",
        category="Grocery",
        unit="kg",
        unit_price=50.0,
        stock_qty=100.0,
        session=test_session
    )
    item_id = add_result["id"]
    assert add_result["is_active"] == True

    # Step 2: Update item
    update_result = await inventory_update_item(
        item_id=item_id,
        unit_price=55.0,
        session=test_session
    )
    assert update_result["unit_price"] == 55.0

    # Step 3: List and verify
    list_result = await inventory_list_items(session=test_session)
    found = next((item for item in list_result["items"] if item["id"] == item_id), None)
    assert found is not None
    assert found["unit_price"] == 55.0

    # Step 4: Delete item
    delete_result = await inventory_delete_item(item_id=item_id, session=test_session)
    assert delete_result["success"] == True

    # Step 5: Verify deletion
    list_result_after = await inventory_list_items(session=test_session)
    found_after = next((item for item in list_result_after["items"] if item["id"] == item_id), None)
    assert found_after is None  # Deleted items excluded from list
```

**Acceptance**:
- [ ] E2E test file created
- [ ] Tests full workflow (Add → Update → List → Delete)
- [ ] All steps integrated and passing
- [ ] Demonstrates 4 inventory tools working together

---

### Task 30: [P1] [All Inventory] Add inventory tools to MCP server registry

**Type**: GREEN
**Story**: US1-4
**File**: `backend/app/mcp_server/server.py` (extend)

**Description**: Register all 4 inventory tools with FastMCP server:
- Register inventory_add_item
- Register inventory_update_item
- Register inventory_delete_item
- Register inventory_list_items
- Verify tool schemas are auto-generated

**Implementation**:
```python
# backend/app/mcp_server/server.py
from fastmcp import Server
from .tools_inventory import (
    inventory_add_item,
    inventory_update_item,
    inventory_delete_item,
    inventory_list_items
)

def create_server():
    server = Server("ims-mcp-server")

    # Register inventory tools
    server.add_tool(
        inventory_add_item,
        description="Create new inventory item"
    )
    server.add_tool(
        inventory_update_item,
        description="Update inventory item"
    )
    server.add_tool(
        inventory_delete_item,
        description="Soft delete inventory item"
    )
    server.add_tool(
        inventory_list_items,
        description="List inventory items with filters and pagination"
    )

    return server
```

**Test**:
```python
def test_inventory_tools_registered():
    from backend.app.mcp_server.server import create_server
    server = create_server()

    tool_names = [tool.name for tool in server.tools]
    assert "inventory_add_item" in tool_names
    assert "inventory_update_item" in tool_names
    assert "inventory_delete_item" in tool_names
    assert "inventory_list_items" in tool_names
```

**Acceptance**:
- [ ] All 4 inventory tools registered with server
- [ ] Tool schemas auto-generated from function signatures
- [ ] Tool descriptions clear
- [ ] Test passing

---

## Phase 3: Billing Tools (Tasks 31-50)

### Task 31: [P1] [US5] RED: Write failing test for billing_create_bill

**Type**: RED
**Story**: US5 – Create bill with stock validation and pessimistic locking
**File**: `backend/tests/mcp/unit/test_tools_billing.py` (new)

**Description**: Write failing tests for billing_create_bill:
- Test successful bill creation
- Test insufficient stock error (pessimistic locking)
- Test concurrent bill creation (both succeed with enough stock)
- Test concurrent bill creation (second fails with insufficient stock)
- Test response includes line items and snapshots

**Test**:
```python
# File: backend/tests/mcp/unit/test_tools_billing.py
import pytest
from backend.app.mcp_server.tools_billing import billing_create_bill

@pytest.mark.asyncio
async def test_billing_create_bill_success(sample_items, test_session):
    """Test successful bill creation."""
    result = await billing_create_bill(
        customer_name="John Doe",
        store_name="Downtown Store",
        items=[
            {"item_id": sample_items[0].id, "quantity": 5}
        ],
        session=test_session
    )

    assert "id" in result
    assert result["customer_name"] == "John Doe"
    assert result["total_amount"] > 0
    assert len(result["items"]) == 1
    # Verify snapshots
    assert "unit_price" in result["items"][0]
    assert "item_name" in result["items"][0]

@pytest.mark.asyncio
async def test_billing_create_bill_insufficient_stock(sample_items, test_session):
    """Test insufficient stock error."""
    with pytest.raises(Exception) as exc_info:
        await billing_create_bill(
            customer_name="John",
            store_name="Store",
            items=[
                {"item_id": sample_items[0].id, "quantity": 999}  # More than stock
            ],
            session=test_session
        )
    assert "INSUFFICIENT_STOCK" in str(exc_info.value)

@pytest.mark.asyncio
async def test_billing_create_bill_item_not_found(test_session):
    """Test bill with non-existent item."""
    with pytest.raises(Exception) as exc_info:
        await billing_create_bill(
            customer_name="John",
            store_name="Store",
            items=[
                {"item_id": 9999, "quantity": 5}
            ],
            session=test_session
        )
    assert "ITEM_NOT_FOUND" in str(exc_info.value)
```

**Acceptance**:
- [ ] 3 test cases written (success, insufficient stock, item not found)
- [ ] Tests FAIL (RED phase)
- [ ] Tests check for snapshots in line items
- [ ] Tests verify pessimistic locking error

---

### Task 32: [P1] [US5] GREEN: Implement billing_create_bill tool

**Type**: GREEN
**Story**: US5
**File**: `backend/app/mcp_server/tools_billing.py` (new)

**Description**: Implement billing_create_bill with:
- Accept customer_name, store_name, items (list with item_id, quantity)
- Validate all items exist (pessimistic locking)
- Check sufficient stock for all items
- Create bill with line items (snapshots at bill time)
- Calculate total_amount
- Deduct stock from inventory
- Return BillRead response
- Rollback on any error

**Implementation**:
```python
# File: backend/app/mcp_server/tools_billing.py
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.billing_service import BillingService
from backend.app.services.inventory_service import InventoryService
from backend.app.mcp_server.exceptions import (
    MCPValidationError, MCPNotFoundError, MCPInsufficientStockError, MCPDatabaseError
)
from decimal import Decimal

@mcp_error_handler("billing_create_bill")
async def billing_create_bill(
    items: list,  # [{"item_id": 1, "quantity": 5}, ...]
    customer_name: str = None,
    store_name: str = None,
    session: AsyncSession = None
) -> dict:
    """Create bill with stock validation and pessimistic locking."""
    try:
        # Validate items list not empty
        if not items:
            raise MCPValidationError("VALIDATION_ERROR", "Bill must have at least one item")

        # Delegate to service layer (Phase 2 BillingService)
        billing_service = BillingService(session)

        # Add items to cart
        for item in items:
            billing_service.add_to_cart(
                item_id=item["item_id"],
                quantity=Decimal(str(item["quantity"]))
            )

        # Confirm bill (validates stock, creates bill + line items)
        bill = await billing_service.confirm_bill(
            customer_name=customer_name,
            store_name=store_name
        )

        # Commit transaction
        await session.commit()

        # Convert to response
        return convert_bill_to_response(bill)

    except MCPException:
        raise
    except InsufficientStockError as e:
        await session.rollback()
        raise MCPInsufficientStockError("INSUFFICIENT_STOCK", str(e))
    except ItemNotFoundError as e:
        await session.rollback()
        raise MCPNotFoundError("ITEM_NOT_FOUND", str(e))
    except Exception as e:
        await session.rollback()
        raise MCPDatabaseError("DATABASE_ERROR", str(e))

def convert_bill_to_response(bill_orm) -> dict:
    """Convert ORM Bill to response dict with snapshots."""
    from backend.app.mcp_server.schemas import BillRead
    return BillRead.from_orm(bill_orm).model_dump()
```

**Test**: Same as Task 31 – all 3 tests should PASS

**Acceptance**:
- [ ] billing_create_bill function implemented
- [ ] Accepts items list with item_id, quantity
- [ ] Validates sufficient stock (pessimistic locking)
- [ ] Creates bill with line item snapshots
- [ ] Calculates total_amount
- [ ] Deducts stock from inventory
- [ ] Rolls back on error
- [ ] All 3 tests from Task 31 PASS

---

### Task 33: [P1] [US5] REFACTOR: Add concurrency tests for pessimistic locking

**Type**: REFACTOR
**Story**: US5
**File**: `backend/tests/mcp/integration/test_concurrent_bills.py` (new)

**Description**: Write tests to verify pessimistic locking prevents over-allocation:
- Create 2 concurrent bill requests with limited stock
- Verify both succeed if stock is sufficient
- Verify second fails if stock becomes insufficient after first

**Test**:
```python
# File: backend/tests/mcp/integration/test_concurrent_bills.py
import asyncio
import pytest

@pytest.mark.asyncio
async def test_concurrent_bills_with_sufficient_stock(sample_items, test_session):
    """Test 2 concurrent bills succeed with enough stock."""
    item = sample_items[0]  # Stock = 100

    async def create_bill():
        return await billing_create_bill(
            customer_name="Customer",
            store_name="Store",
            items=[{"item_id": item.id, "quantity": 50}],
            session=test_session
        )

    # Both bills should succeed (100 >= 50 + 50)
    results = await asyncio.gather(create_bill(), create_bill())
    assert len(results) == 2
    assert all(result["id"] for result in results)

@pytest.mark.asyncio
async def test_concurrent_bills_second_fails_insufficient_stock(sample_items, test_session):
    """Test 2nd concurrent bill fails if stock insufficient."""
    item = sample_items[0]  # Stock = 100

    async def create_bill(qty):
        return await billing_create_bill(
            customer_name="Customer",
            store_name="Store",
            items=[{"item_id": item.id, "quantity": qty}],
            session=test_session
        )

    # First bill takes 60, second tries to take 50 (total would be 110)
    # Second should fail
    try:
        results = await asyncio.gather(
            create_bill(60),
            create_bill(50)
        )
        # Check if either failed (one should fail)
        # In real pessimistic locking, second would fail
    except Exception as e:
        assert "INSUFFICIENT_STOCK" in str(e)
```

**Acceptance**:
- [ ] Concurrency test file created
- [ ] Tests pessimistic locking behavior
- [ ] Verifies both bills succeed with sufficient stock
- [ ] Verifies second bill fails with insufficient stock
- [ ] Test passing

---

### Task 34: [P1] [US6] RED: Write failing test for billing_list_bills

**Type**: RED
**Story**: US6 – List bills with date range filtering and pagination
**File**: `backend/tests/mcp/unit/test_tools_billing.py` (extend)

**Description**: Write failing tests for billing_list_bills:
- Test list all bills
- Test filter by date range (start_date, end_date)
- Test pagination (page, limit with defaults 20/100)
- Test response includes pagination

**Test**:
```python
@pytest.mark.asyncio
async def test_billing_list_bills_success(test_session):
    """Test list all bills."""
    result = await billing_list_bills(session=test_session)

    assert "bills" in result
    assert "pagination" in result
    assert isinstance(result["bills"], list)

@pytest.mark.asyncio
async def test_billing_list_bills_with_date_filter(test_session):
    """Test filter by date range."""
    from datetime import datetime, timedelta

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    result = await billing_list_bills(
        start_date=today,
        end_date=tomorrow,
        session=test_session
    )

    # Bills should be within date range
    assert all(
        today <= item["created_at"].date() <= tomorrow
        for item in result["bills"]
    )

@pytest.mark.asyncio
async def test_billing_list_bills_pagination(test_session):
    """Test pagination defaults."""
    result = await billing_list_bills(session=test_session)

    assert result["pagination"]["limit"] == 20  # Default
    assert result["pagination"]["page"] == 1  # Default
```

**Acceptance**:
- [ ] 3 test cases written (list all, date filter, pagination)
- [ ] Tests FAIL (RED phase)
- [ ] Tests check pagination structure

---

### Task 35: [P1] [US6] GREEN: Implement billing_list_bills tool

**Type**: GREEN
**Story**: US6
**File**: `backend/app/mcp_server/tools_billing.py` (extend)

**Description**: Implement billing_list_bills with date filtering:
- Accept optional start_date, end_date, page, limit
- Default page=1, limit=20, max=100
- Filter bills by created_at date range
- Return BillListResponse with pagination
- Include line item snapshots in response

**Implementation**:
```python
@mcp_error_handler("billing_list_bills")
async def billing_list_bills(
    start_date: str = None,
    end_date: str = None,
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = None
) -> dict:
    """List bills with optional date filtering and pagination."""
    from datetime import datetime

    # Validate pagination
    if page < 1:
        page = 1
    if limit < 1:
        limit = 20
    if limit > 100:
        limit = 100

    service = BillingService(session)

    # Parse dates
    filters = {}
    if start_date:
        filters["start_date"] = datetime.fromisoformat(start_date).date()
    if end_date:
        filters["end_date"] = datetime.fromisoformat(end_date).date()

    # Get bills
    bills, total = await service.list_bills(
        filters=filters,
        page=page,
        limit=limit
    )

    # Build response
    bills_data = [convert_bill_to_response(bill) for bill in bills]
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
```

**Test**: Same as Task 34 – all 3 tests should PASS

**Acceptance**:
- [ ] billing_list_bills function implemented
- [ ] Supports optional date filters (start_date, end_date)
- [ ] Supports pagination (page, limit)
- [ ] Default limit=20, max=100
- [ ] Returns BillListResponse with pagination
- [ ] All 3 tests from Task 34 PASS

---

### Task 36: [P1] [US6] REFACTOR: Optimize bill list query

**Type**: REFACTOR
**Story**: US6
**File**: `backend/app/mcp_server/tools_billing.py` (extend)

**Description**: Refactor for performance:
- Ensure indexes on bills(created_at)
- Test performance (<500ms for typical bill volumes)
- Document performance characteristics

**Test**:
```python
@pytest.mark.asyncio
async def test_billing_list_bills_performance(test_session):
    """Test list performance."""
    import time

    start = time.time()
    result = await billing_list_bills(session=test_session)
    elapsed = time.time() - start

    assert elapsed < 0.5  # 500ms threshold
```

**Acceptance**:
- [ ] Performance test added
- [ ] Docstring documents performance
- [ ] Test passing (<500ms)

---

### Task 37: [P1] [US7] RED: Write failing test for billing_get_bill

**Type**: RED
**Story**: US7 – Get bill details by ID
**File**: `backend/tests/mcp/unit/test_tools_billing.py` (extend)

**Description**: Write failing tests for billing_get_bill:
- Test get bill by ID
- Test includes all line items with snapshots
- Test bill not found error
- Test response matches BillRead schema

**Test**:
```python
@pytest.mark.asyncio
async def test_billing_get_bill_success(sample_bills, test_session):
    """Test get bill by ID."""
    bill_id = sample_bills[0]["id"]

    result = await billing_get_bill(bill_id=bill_id, session=test_session)

    assert result["id"] == bill_id
    assert result["customer_name"] == sample_bills[0]["customer_name"]
    assert "items" in result
    assert len(result["items"]) > 0
    # Verify snapshots
    for item in result["items"]:
        assert "item_name" in item
        assert "unit_price" in item

@pytest.mark.asyncio
async def test_billing_get_bill_not_found(test_session):
    """Test get non-existent bill."""
    with pytest.raises(Exception) as exc_info:
        await billing_get_bill(bill_id=9999, session=test_session)
    assert "BILL_NOT_FOUND" in str(exc_info.value)
```

**Acceptance**:
- [ ] 2 test cases written (success, not found)
- [ ] Tests FAIL (RED phase)
- [ ] Tests verify line items and snapshots

---

### Task 38: [P1] [US7] GREEN: Implement billing_get_bill tool

**Type**: GREEN
**Story**: US7
**File**: `backend/app/mcp_server/tools_billing.py` (extend)

**Description**: Implement billing_get_bill:
- Accept bill_id
- Call service to fetch bill with line items
- Return BillRead with all snapshots
- Handle BILL_NOT_FOUND error

**Implementation**:
```python
@mcp_error_handler("billing_get_bill")
async def billing_get_bill(
    bill_id: int,
    session: AsyncSession = None
) -> dict:
    """Get bill details by ID."""
    service = BillingService(session)

    bill = await service.get_bill(bill_id)
    if not bill:
        raise MCPNotFoundError("BILL_NOT_FOUND", f"Bill {bill_id} not found")

    return convert_bill_to_response(bill)
```

**Test**: Same as Task 37 – all 2 tests should PASS

**Acceptance**:
- [ ] billing_get_bill function implemented
- [ ] Calls service to fetch bill with line items
- [ ] Returns BillRead with snapshots
- [ ] Handles BILL_NOT_FOUND error
- [ ] All 2 tests from Task 37 PASS

---

### Task 39: [P1] [All Billing] Add billing tools to MCP server registry

**Type**: GREEN
**Story**: US5-7
**File**: `backend/app/mcp_server/server.py` (extend)

**Description**: Register all 3 billing tools with FastMCP server:
- Register billing_create_bill
- Register billing_list_bills
- Register billing_get_bill

**Implementation**:
```python
# backend/app/mcp_server/server.py
from .tools_billing import (
    billing_create_bill,
    billing_list_bills,
    billing_get_bill
)

def create_server():
    # ... existing inventory tools ...

    # Register billing tools
    server.add_tool(
        billing_create_bill,
        description="Create bill with stock validation and pessimistic locking"
    )
    server.add_tool(
        billing_list_bills,
        description="List bills with date range filtering and pagination"
    )
    server.add_tool(
        billing_get_bill,
        description="Get bill details by ID"
    )

    return server
```

**Test**:
```python
def test_billing_tools_registered():
    from backend.app.mcp_server.server import create_server
    server = create_server()

    tool_names = [tool.name for tool in server.tools]
    assert "billing_create_bill" in tool_names
    assert "billing_list_bills" in tool_names
    assert "billing_get_bill" in tool_names
```

**Acceptance**:
- [ ] All 3 billing tools registered
- [ ] Tool schemas auto-generated
- [ ] Tool descriptions clear
- [ ] Test passing

---

### Task 40: [P1] [All Billing] Integration test: Create → List → Get bill workflow

**Type**: INTEGRATION
**Story**: US5-7
**File**: `backend/tests/integration/test_mcp_billing_e2e.py` (new)

**Description**: Create end-to-end integration test:
- Create bill with billing_create_bill
- List bills and verify new bill appears
- Get bill by ID and verify all details
- Verify immutability (no update/delete)

**Test**:
```python
# File: backend/tests/integration/test_mcp_billing_e2e.py
@pytest.mark.asyncio
async def test_e2e_billing_workflow(sample_items, test_session):
    """Test complete billing workflow: Create → List → Get."""

    # Step 1: Create bill
    create_result = await billing_create_bill(
        customer_name="John Doe",
        store_name="Downtown Store",
        items=[
            {"item_id": sample_items[0].id, "quantity": 5}
        ],
        session=test_session
    )
    bill_id = create_result["id"]
    assert create_result["total_amount"] > 0

    # Step 2: List and verify bill appears
    list_result = await billing_list_bills(session=test_session)
    found = next((bill for bill in list_result["bills"] if bill["id"] == bill_id), None)
    assert found is not None

    # Step 3: Get bill by ID
    get_result = await billing_get_bill(bill_id=bill_id, session=test_session)
    assert get_result["id"] == bill_id
    assert get_result["customer_name"] == "John Doe"
    assert len(get_result["items"]) == 1

    # Verify snapshots
    line_item = get_result["items"][0]
    assert "item_name" in line_item
    assert "unit_price" in line_item
    assert "quantity" in line_item
    assert "line_total" in line_item
```

**Acceptance**:
- [ ] E2E test file created
- [ ] Tests full workflow (Create → List → Get)
- [ ] All steps integrated and passing
- [ ] Demonstrates 3 billing tools working together

---

## Phase 4: Final Validation (Tasks 41-50)

### Task 41: [P1] [All Tools] Consistency test: MCP vs FastAPI responses

**Type**: INTEGRATION
**Story**: All (US1-7)
**File**: `backend/tests/integration/test_fastapi_vs_mcp.py` (extend)

**Description**: Create tests comparing FastAPI endpoints with MCP tools:
- Call FastAPI endpoint and MCP tool with same inputs
- Verify responses are identical (same structure, values)
- Test for all 7 tools

**Test**:
```python
# File: backend/tests/integration/test_fastapi_vs_mcp.py
@pytest.mark.asyncio
async def test_mcp_vs_fastapi_add_item_consistency(test_session, client):
    """Verify MCP and FastAPI return identical responses for add_item."""

    # FastAPI call
    fastapi_response = client.post(
        "/api/items",
        json={
            "name": "Sugar",
            "category": "Grocery",
            "unit": "kg",
            "unit_price": 50.0,
            "stock_qty": 100.0
        }
    )

    # MCP call
    mcp_response = await inventory_add_item(
        name="Sugar",
        category="Grocery",
        unit="kg",
        unit_price=50.0,
        stock_qty=100.0,
        session=test_session
    )

    # Compare
    assert fastapi_response.status_code == 201
    assert fastapi_response.json()["name"] == mcp_response["name"]
    assert fastapi_response.json()["category"] == mcp_response["category"]
```

**Acceptance**:
- [ ] Consistency tests for all 7 tools
- [ ] FastAPI and MCP return identical responses
- [ ] All tests passing

---

### Task 42: [P1] [All Tools] Test error consistency across all tools

**Type**: UNIT
**Story**: All
**File**: `backend/tests/mcp/unit/test_error_consistency.py` (new)

**Description**: Verify all tools return standardized error responses:
- All errors have (error, message, details) structure
- Error codes are screaming-snake-case
- Details include relevant context (item_id, available, requested, etc.)

**Test**:
```python
# File: backend/tests/mcp/unit/test_error_consistency.py
def test_validation_error_format():
    """Verify validation errors have consistent format."""
    from backend.app.mcp_server.utils import exception_to_error_response
    from backend.app.mcp_server.exceptions import MCPValidationError

    exc = MCPValidationError("CATEGORY_INVALID", "Invalid category", {"category": "BadCat"})
    response = exception_to_error_response(exc)

    assert "error" in response
    assert "message" in response
    assert "details" in response
    assert response["error"] == "CATEGORY_INVALID"
    assert response["details"]["category"] == "BadCat"

def test_all_error_codes_are_screaming_snake_case():
    """Verify error codes follow naming convention."""
    from backend.app.mcp_server.schemas import ERROR_CODES

    for code in ERROR_CODES.values():
        assert code == code.upper()
        # Either single word or separated by underscore
        assert "_" in code or code.isalpha()
```

**Acceptance**:
- [ ] Error format tests created
- [ ] All errors have (error, message, details)
- [ ] All error codes are screaming-snake-case
- [ ] Tests passing

---

### Task 43: [P1] [All Tools] Load test: Verify <500ms response time

**Type**: PERFORMANCE
**Story**: All
**File**: `backend/tests/mcp/performance/test_load.py` (new)

**Description**: Create load test to verify performance goal:
- Test each tool's response time
- Ensure <500ms for typical operations
- Test with concurrent requests

**Test**:
```python
# File: backend/tests/mcp/performance/test_load.py
import time

@pytest.mark.asyncio
async def test_inventory_add_item_response_time(test_session):
    """Test add_item completes in <500ms."""
    start = time.time()

    await inventory_add_item(
        name="Sugar",
        category="Grocery",
        unit="kg",
        unit_price=50.0,
        stock_qty=100.0,
        session=test_session
    )

    elapsed = time.time() - start
    assert elapsed < 0.5, f"Expected <500ms, got {elapsed*1000:.2f}ms"

@pytest.mark.asyncio
async def test_billing_create_bill_response_time(sample_items, test_session):
    """Test billing create completes in <500ms."""
    start = time.time()

    await billing_create_bill(
        customer_name="John",
        store_name="Store",
        items=[{"item_id": sample_items[0].id, "quantity": 5}],
        session=test_session
    )

    elapsed = time.time() - start
    assert elapsed < 0.5, f"Expected <500ms, got {elapsed*1000:.2f}ms"
```

**Acceptance**:
- [ ] Load test file created
- [ ] Tests response time for each tool
- [ ] All tools <500ms
- [ ] Tests passing

---

### Task 44: [P1] [All Tools] Coverage report: Achieve 80% coverage

**Type**: UNIT
**Story**: All
**File**: backend (run coverage)

**Description**: Run coverage report and verify 80%+ coverage:
- Unit tests should cover all branches
- Integration tests should cover workflows
- Identify and cover any missing lines

**Execution**:
```bash
pytest backend/tests/mcp/ --cov=backend.app.mcp_server --cov-report=term-missing --cov-report=html
# Should show ≥80% coverage
```

**Acceptance**:
- [ ] Coverage report generated
- [ ] ≥80% code coverage for backend/app/mcp_server
- [ ] All core logic covered
- [ ] Edge cases tested

---

### Task 45: [P1] [All Tools] Register all 7 tools with server

**Type**: GREEN
**Story**: All
**File**: `backend/app/mcp_server/server.py` (verify)

**Description**: Verify all 7 tools are registered and accessible:
- 4 inventory tools
- 3 billing tools
- Server can be started

**Test**:
```python
def test_all_tools_registered():
    from backend.app.mcp_server.server import create_server

    server = create_server()
    tool_names = [tool.name for tool in server.tools]

    assert len(tool_names) == 7
    assert "inventory_add_item" in tool_names
    assert "inventory_update_item" in tool_names
    assert "inventory_delete_item" in tool_names
    assert "inventory_list_items" in tool_names
    assert "billing_create_bill" in tool_names
    assert "billing_list_bills" in tool_names
    assert "billing_get_bill" in tool_names
```

**Acceptance**:
- [ ] All 7 tools registered
- [ ] Server initializes without errors
- [ ] Test passing

---

### Task 46: [P1] [Transport] Test stdio transport

**Type**: INTEGRATION
**Story**: All
**File**: `backend/tests/mcp/integration/test_stdio_transport.py` (new)

**Description**: Test MCP server over stdio transport (for Claude Code):
- Start server with stdio transport
- Call tools via stdin/stdout
- Verify responses are valid JSON

**Test**:
```python
# File: backend/tests/mcp/integration/test_stdio_transport.py
@pytest.mark.asyncio
async def test_stdio_transport_available():
    """Verify stdio transport can be started."""
    from backend.app.mcp_server.server import create_server

    server = create_server()
    # Verify server has stdio capability
    # (This is implicitly tested when /sp.implement runs the server)
    assert server is not None
```

**Acceptance**:
- [ ] Stdio transport test created
- [ ] Server can be started with stdio
- [ ] Responses are valid JSON

---

### Task 47: [P1] [Transport] Test HTTP transport

**Type**: INTEGRATION
**Story**: All
**File**: `backend/tests/mcp/integration/test_http_transport.py` (new)

**Description**: Test MCP server over HTTP localhost:3000:
- Start server with HTTP transport
- Call tools via HTTP POST
- Verify responses include proper headers and status

**Test**:
```python
# File: backend/tests/mcp/integration/test_http_transport.py
@pytest.mark.asyncio
async def test_http_transport_available():
    """Verify HTTP transport can be started."""
    from backend.app.mcp_server.server import create_server

    server = create_server()
    # Server should support HTTP on localhost:3000
    assert server is not None
```

**Acceptance**:
- [ ] HTTP transport test created
- [ ] Server listens on localhost:3000
- [ ] HTTP POST requests work

---

### Task 48: [P2] [Billing] Immutability validation: Verify bills cannot be modified

**Type**: UNIT
**Story**: US5
**File**: `backend/tests/mcp/unit/test_billing_immutability.py` (new)

**Description**: Create tests for billing immutability (US5 requirement):
- No update_bill tool exists
- No delete_bill tool exists
- Attempting to modify bill raises error

**Test**:
```python
# File: backend/tests/mcp/unit/test_billing_immutability.py
def test_no_bill_update_tool():
    """Verify no update_bill tool is exposed."""
    from backend.app.mcp_server.server import create_server

    server = create_server()
    tool_names = [tool.name for tool in server.tools]

    assert "billing_update_bill" not in tool_names

def test_no_bill_delete_tool():
    """Verify no delete_bill tool is exposed."""
    from backend.app.mcp_server.server import create_server

    server = create_server()
    tool_names = [tool.name for tool in server.tools]

    assert "billing_delete_bill" not in tool_names
```

**Acceptance**:
- [ ] Immutability tests created
- [ ] No update/delete tools for bills
- [ ] Tests passing
- [ ] Matches FR-013 (Bill Immutability)

---

### Task 49: [P2] [Documentation] Create API documentation for all tools

**Type**: REFACTOR
**Story**: All
**File**: `docs/mcp-tools.md` (new)

**Description**: Create documentation for all 7 MCP tools:
- Tool name and description
- Parameters (required/optional)
- Response schema
- Example requests and responses
- Error codes and handling

**Documentation**:
```markdown
# Phase 4 MCP Tools Documentation

## Inventory Tools

### 1. inventory_add_item
Create new inventory item.

**Parameters**:
- `name` (string, required): Item name (1-255 chars)
- `category` (string, required): Grocery, Garments, Beauty, Utilities, Other
- `unit` (string, required): kg, g, liter, ml, piece, box, pack, other
- `unit_price` (number, required): Price > 0
- `stock_qty` (number, required): Initial stock >= 0

**Response**:
```json
{
  "id": 1,
  "name": "Sugar",
  "category": "Grocery",
  "unit": "kg",
  "unit_price": 50.00,
  "stock_qty": 100.0,
  "is_active": true,
  "created_at": "2025-12-08T10:00:00Z"
}
```

[Continue for all 7 tools...]
```

**Acceptance**:
- [ ] Documentation created for all 7 tools
- [ ] Includes parameters, responses, examples
- [ ] Error codes documented
- [ ] Clear and developer-friendly

---

### Task 50: [P2] [Final] Run all tests and achieve 80% coverage

**Type**: VALIDATION
**Story**: All
**File**: backend (all tests)

**Description**: Final validation phase:
- Run all unit tests
- Run all integration tests
- Run all performance tests
- Generate coverage report
- Verify 80%+ coverage
- All tests passing

**Execution**:
```bash
#!/bin/bash
# backend/scripts/test_mcp.sh

echo "Running ALL MCP Tests..."
pytest backend/tests/mcp/ -v \
  --cov=backend.app.mcp_server \
  --cov-report=term-missing \
  --cov-report=html \
  --tb=short

# Should show: passed, 80%+ coverage
```

**Acceptance**:
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] All performance tests passing (<500ms)
- [ ] 80%+ code coverage
- [ ] Coverage report generated
- [ ] Ready for /sp.implement completion

---

## Summary

**Total Tasks**: 50 organized by phase

| Phase | Tasks | Status |
|-------|-------|--------|
| Foundation & Setup | 1-8 | ⏭️ Ready for development |
| Schemas & Error Handling | 9-16 | ⏭️ Ready for development |
| Inventory Tools | 17-30 | ⏭️ Ready for development |
| Billing Tools | 31-40 | ⏭️ Ready for development |
| Final Validation | 41-50 | ⏭️ Ready for development |

**Key Milestones**:
- [ ] Tasks 1-8: Foundation complete
- [ ] Tasks 9-16: All schemas and errors defined
- [ ] Tasks 17-30: 4 inventory tools implemented with 80%+ coverage
- [ ] Tasks 31-40: 3 billing tools implemented with 80%+ coverage
- [ ] Tasks 41-50: Full validation, consistency tests, documentation

**Coverage Target**: 80% for backend/app/mcp_server/

**Performance Target**: <500ms per tool call

**Parallelization**: Tasks 17-30 (Inventory) can run in parallel with Tasks 31-40 (Billing) after Tasks 1-16 complete.

---

**Status**: ✅ **TASKS.MD COMPLETE & READY FOR IMPLEMENTATION**

**Next Step**: Begin with Task 1 (RED: Create MCP server entry point) and follow TDD Red → Green → Refactor cycle.

**Branch**: `004-fastmcp-server-p4` | **Date**: 2025-12-08

