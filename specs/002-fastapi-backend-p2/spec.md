# Feature Specification: FastAPI Backend (Phase 2) - IMS REST API

**Feature Branch**: `002-fastapi-backend-p2`
**Created**: 2025-12-08
**Status**: Draft
**Input**: Build FastAPI backend REST API for StoreLite IMS, converting Phase 1 console app into a production-ready API with PostgreSQL, SQLAlchemy ORM, comprehensive test coverage ensuring Postman compatibility and zero test failures.

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Admin: Create New Inventory Item (Priority: P1)

As a store admin, I want to add new products to the inventory through an API endpoint so that the system has current product master data. This is the foundation for all billing operations.

**Why this priority**: P1 - Core functionality. Without inventory items, no billing can occur. This is the first and most fundamental feature needed.

**Independent Test**: Can be fully tested by calling `POST /items` with valid data and verifying the item is created in PostgreSQL with correct values. Delivers the ability to populate inventory.

**Acceptance Scenarios**:

1. **Given** an empty items table, **When** I send a valid POST request to `/items` with name, category, unit, unit_price, and stock_qty, **Then** the item is created successfully with a 201 status and I receive the created item with an auto-generated ID
2. **Given** I provide duplicate product name, **When** I send POST request, **Then** the system allows duplicate names (since same product can exist in different stores)
3. **Given** I provide negative unit_price, **When** I send POST request, **Then** the system returns 422 validation error
4. **Given** I provide negative stock_qty, **When** I send POST request, **Then** the system returns 422 validation error
5. **Given** I provide a very large stock_qty (e.g., 999999.999), **When** I send POST request, **Then** the system accepts it and stores correctly
6. **Given** required fields are missing, **When** I send POST request, **Then** the system returns 422 validation error with specific field errors

---

### User Story 2 - Admin: List and Search Inventory Items (Priority: P1)

As a store admin, I want to retrieve all products or search by name/category through an API so that I can view and manage inventory.

**Why this priority**: P1 - Core functionality needed immediately after adding items. Enables inventory management and visibility.

**Independent Test**: Can be fully tested by calling `GET /items` with no filters and with filters (name, category), verifying correct items are returned in correct format.

**Acceptance Scenarios**:

1. **Given** items exist in database, **When** I call GET /items, **Then** I receive a list of all active items with complete details
2. **Given** items with name "Sugar" exist, **When** I call GET /items?name=sugar (case-insensitive), **Then** I receive only matching items
3. **Given** items with category "grocery" exist, **When** I call GET /items?category=grocery, **Then** I receive only items in that category
4. **Given** both name and category filters are provided, **When** I call GET /items?name=sugar&category=grocery, **Then** I receive items matching both criteria
5. **Given** inactive items (is_active=false) exist, **When** I call GET /items, **Then** only active items are returned
6. **Given** no items match the search criteria, **When** I call GET /items?name=nonexistent, **Then** I receive an empty list with status 200
7. **Given** I call GET /items, **Then** results are ordered by name alphabetically

---

### User Story 3 - Admin: Get Single Item Details (Priority: P1)

As a store admin, I want to retrieve details for a specific item by ID through an API so that I can view and verify product information.

**Why this priority**: P1 - Essential for item detail views, updates, and billing workflows.

**Independent Test**: Can be fully tested by calling `GET /items/{id}` with valid and invalid IDs, verifying correct data or error responses.

**Acceptance Scenarios**:

1. **Given** an item with ID 1 exists, **When** I call GET /items/1, **Then** I receive complete item details with status 200
2. **Given** an item with ID 999 doesn't exist, **When** I call GET /items/999, **Then** I receive 404 error with descriptive message
3. **Given** I provide non-numeric ID, **When** I call GET /items/abc, **Then** I receive 422 validation error
4. **Given** an item is soft-deleted (is_active=false), **When** I call GET /items/{id}, **Then** I receive 404 error (treat as non-existent)

---

### User Story 4 - Admin: Update Item Price and Stock (Priority: P2)

As a store admin, I want to update product prices and stock quantities through an API so that inventory data stays current.

**Why this priority**: P2 - Important for ongoing inventory management, but less critical than initial CRUD setup.

**Independent Test**: Can be fully tested by calling `PUT /items/{id}` with updates and verifying changes persist in database.

**Acceptance Scenarios**:

1. **Given** an item with ID 1 exists, **When** I send PUT request with new unit_price, **Then** the price is updated and I receive the updated item
2. **Given** an item with ID 1 exists, **When** I send PUT request with new stock_qty, **Then** the stock is updated and I receive the updated item
3. **Given** an item with ID 1 exists, **When** I send PUT request updating both price and stock, **Then** both are updated correctly
4. **Given** I provide partial update (only some fields), **When** I send PUT request, **Then** only provided fields are updated, others remain unchanged
5. **Given** I provide negative price in update, **When** I send PUT request, **Then** the system returns 422 validation error
6. **Given** an item doesn't exist, **When** I send PUT request to /items/999, **Then** I receive 404 error
7. **Given** I update name or category (optional), **When** I send PUT request, **Then** those fields are updated if provided

---

### User Story 5 - Admin: Deactivate Items (Priority: P2)

As a store admin, I want to deactivate (soft delete) products without losing historical data so that inventory stays clean but audit trail remains.

**Why this priority**: P2 - Important for data integrity but can be implemented after core CRUD.

**Independent Test**: Can be fully tested by calling `DELETE /items/{id}` or `PUT /items/{id}` with is_active=false and verifying item no longer appears in lists.

**Acceptance Scenarios**:

1. **Given** an item with ID 1 exists and is_active=true, **When** I send DELETE request or PUT with is_active=false, **Then** the item is deactivated
2. **Given** an item is deactivated, **When** I call GET /items, **Then** the deactivated item doesn't appear in the list
3. **Given** an item is deactivated, **When** I call GET /items/{id}, **Then** I receive 404 error
4. **Given** an item doesn't exist, **When** I send DELETE request to /items/999, **Then** I receive 404 error
5. **Given** an item is deactivated, **When** I call GET /bills that include this item, **Then** historical billing data is preserved

---

### User Story 6 - Salesperson: Create Bill/Invoice (Priority: P1)

As a salesperson, I want to create a bill with multiple items, quantities, and have the system calculate totals and update stock automatically so that I can process customer purchases quickly.

**Why this priority**: P1 - Core revenue-generating feature. Without billing, the system has no business value.

**Independent Test**: Can be fully tested by calling `POST /bills` with valid items and quantities, verifying bill is created, totals calculated correctly, and stock is decremented.

**Acceptance Scenarios**:

1. **Given** items with sufficient stock exist, **When** I send POST /bills with customer_name, store_name, and items array with quantities, **Then** bill is created with 201 status and correct totals
2. **Given** a bill is created with items, **When** I review the response, **Then** I receive bill_id, total_amount, and all bill_items with calculated line_totals
3. **Given** I create a bill with 2kg sugar at 160/kg and 1 shampoo at 200, **When** the bill is processed, **Then** total_amount = (2*160) + (1*200) = 520
4. **Given** an item has stock_qty=5kg and I try to buy 10kg, **When** I submit the bill, **Then** the system returns 400 error "Insufficient stock"
5. **Given** I reference an item_id that doesn't exist, **When** I submit the bill, **Then** the system returns 400 error "Item not found"
6. **Given** I provide quantity=0, **When** I submit the bill, **Then** the system returns 422 validation error
7. **Given** I provide negative quantity, **When** I submit the bill, **Then** the system returns 422 validation error
8. **Given** a bill is created successfully, **When** I query inventory, **Then** stock quantities are decremented by sold quantities
9. **Given** I create a bill with quantities using decimals (e.g., 1.5 kg), **When** the bill is processed, **Then** stock is decremented with decimal precision
10. **Given** customer_name and store_name are optional, **When** I create a bill without these fields, **Then** the bill is created successfully with NULL/empty values

---

### User Story 7 - Salesperson/Admin: Retrieve Bill Details (Priority: P1)

As a salesperson or admin, I want to retrieve complete bill details by bill ID so that I can display invoices and verify transactions.

**Why this priority**: P1 - Essential for invoice display and bill verification.

**Independent Test**: Can be fully tested by calling `GET /bills/{id}` and verifying complete bill with all line items is returned.

**Acceptance Scenarios**:

1. **Given** a bill with ID 1 exists, **When** I call GET /bills/1, **Then** I receive complete bill details including header and all bill_items with line_totals
2. **Given** a bill with ID 999 doesn't exist, **When** I call GET /bills/999, **Then** I receive 404 error
3. **Given** a bill exists with multiple line items, **When** I call GET /bills/{id}, **Then** all line_items are returned with item_name, unit_price, quantity, and line_total
4. **Given** I retrieve a bill, **Then** the response includes created_at timestamp in ISO format

---

### User Story 8 - Admin: List All Bills (Priority: P2)

As a store admin, I want to retrieve a list of all bills with optional filtering so that I can view transaction history and generate reports.

**Why this priority**: P2 - Important for reporting and audit, but less critical than core billing.

**Independent Test**: Can be fully tested by calling `GET /bills` with and without filters, verifying correct bills are returned.

**Acceptance Scenarios**:

1. **Given** bills exist in database, **When** I call GET /bills, **Then** I receive paginated list of bills with ID, customer_name, total_amount, and created_at
2. **Given** bills exist from different dates, **When** I call GET /bills?start_date=2025-01-01&end_date=2025-01-31, **Then** I receive only bills created within that date range
3. **Given** bills exist with different customers, **When** I call GET /bills?customer_name=Ali, **Then** I receive only bills for that customer (partial match supported)
4. **Given** no bills exist, **When** I call GET /bills, **Then** I receive empty list with status 200

### Edge Cases

- What happens when stock is exactly zero and someone tries to create a bill with that item? (System returns insufficient stock error)
- How does system handle concurrent bill creation for same item when stock is limited? (First request that reserves stock wins; subsequent requests fail)
- What happens if database connection fails mid-transaction during bill creation? (Transaction rolls back; no partial bills created)
- How are decimal quantities (e.g., 2.5 kg) handled in stock calculations? (System uses NUMERIC(12,3) precision for accurate decimals)
- What happens if user provides extremely large numbers for price or quantity? (System accepts up to NUMERIC(12,2) and NUMERIC(12,3) limits respectively)
- How does system handle deleted items referenced in historical bills? (Item snapshots in bill_items preserve historical data; deleted items don't affect bill display)

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

**Inventory Management**

- **FR-001**: System MUST provide `POST /items` endpoint to create new inventory items with name, category, unit, unit_price (≥0), and stock_qty (≥0)
- **FR-002**: System MUST provide `GET /items` endpoint to list all active items with optional filtering by name (case-insensitive partial match) and category
- **FR-003**: System MUST provide `GET /items/{id}` endpoint to retrieve complete details for a single item by ID
- **FR-004**: System MUST provide `PUT /items/{id}` endpoint to update item price, stock quantity, and metadata (name, category, unit)
- **FR-005**: System MUST provide soft-delete functionality via `DELETE /items/{id}` or `PUT /items/{id}` with is_active=false to deactivate items without losing historical data
- **FR-006**: System MUST validate that unit_price and stock_qty are non-negative and return 422 status for invalid values
- **FR-007**: System MUST validate that all required fields (name, category, unit, unit_price, stock_qty) are provided when creating items and return 422 for missing fields
- **FR-008**: System MUST store item metadata including created_at and updated_at timestamps automatically

**Billing & Invoice**

- **FR-009**: System MUST provide `POST /bills` endpoint to create bills with customer_name (optional), store_name (optional), and array of items with quantities
- **FR-010**: System MUST validate that all items in bill request exist in database and return 400 error if any item doesn't exist
- **FR-011**: System MUST validate that all requested stock quantities are available BEFORE creating any bill records (upfront validation); if any item has insufficient stock, return 400 error with message "Insufficient stock" immediately without creating bill/items/stock updates
- **FR-012**: System MUST calculate line_total for each bill item as (unit_price × quantity) with decimal precision (NUMERIC(12,2))
- **FR-013**: System MUST calculate bill total_amount as sum of all line_totals with decimal precision
- **FR-014**: System MUST support decimal quantities (e.g., 2.5 kg) for items sold by weight/volume
- **FR-015**: System MUST create bill_items entries capturing item_name and unit_price snapshots at time of sale for historical accuracy
- **FR-016**: System MUST atomically decrement stock quantities in inventory after bill creation succeeds (transaction must complete or rollback entirely)
- **FR-017**: System MUST provide `GET /bills/{id}` endpoint to retrieve complete bill with header and all line items
- **FR-018**: System MUST provide `GET /bills` endpoint to list ALL bills without pagination (no limit/offset) with optional date range filtering (start_date, end_date); returns complete list of bills for the date range or all bills if no date range specified
- **FR-019**: System MUST validate that bill quantities are positive (>0) and return 422 error for zero or negative quantities
- **FR-020**: System MUST store bill metadata including created_at timestamp in ISO 8601 format

**Data Integrity & Validation**

- **FR-021**: System MUST use transactions to ensure that bill creation is atomic (either entire bill+items+stock updates succeed or all rollback)
- **FR-022**: System MUST validate all numeric inputs against PostgreSQL column constraints (NUMERIC types, precision/scale)
- **FR-023**: System MUST return appropriate HTTP status codes: 200 for success, 201 for resource creation, 400 for business logic errors, 404 for not found, 422 for validation errors, 500 for server errors
- **FR-024**: System MUST return validation error details in custom format: `{"error": "Validation failed", "fields": {"field_name": "error message"}}` for all 422 validation errors (e.g., `{"error": "Validation failed", "fields": {"unit_price": "must be >= 0"}}`)
- **FR-025**: System MUST return business logic errors (400 status) in format: `{"error": "Error description"}` (e.g., `{"error": "Insufficient stock"}` for stock validation failures)

**API Standards**

- **FR-026**: System MUST use SQLAlchemy ORM for all database operations to ensure consistent data access
- **FR-027**: System MUST use Pydantic models for request/response validation and serialization
- **FR-028**: System MUST implement proper error handling with descriptive error messages in response bodies
- **FR-029**: System MUST support JSON request/response format for all endpoints
- **FR-030**: System MUST document all endpoints in Swagger UI accessible at `/docs`
- **FR-031**: System MUST return prices and totals as strings in JSON responses (e.g., `"unit_price": "160.50"`) and quantities as numbers (e.g., `"quantity": 2.5`) to preserve exact NUMERIC decimal precision
- **FR-032**: System MUST validate all stock quantities upfront before creating any bill records; if any item has insufficient stock, return 400 error immediately without creating bill/items/stock updates

---

### Key Entities *(include if feature involves data)*

**Item (Inventory Master Data)**
- Represents a product in the store
- Attributes: id (auto-generated), name, category, unit, unit_price (NUMERIC 12,2), stock_qty (NUMERIC 12,3), is_active (boolean), created_at, updated_at
- Relationships: Referenced by bill_items (historical snapshots, not direct FK references)

**Bill (Invoice Header)**
- Represents a single transaction/invoice
- Attributes: id (auto-generated), customer_name (optional), store_name (optional), total_amount (NUMERIC 12,2), created_at
- Relationships: Has many bill_items (1:N relationship)

**BillItem (Invoice Line Item)**
- Represents a single line in a bill/invoice
- Attributes: id, bill_id (FK → bills.id), item_id (FK → items.id), item_name (snapshot), unit_price (snapshot in NUMERIC 12,2), quantity (NUMERIC 12,3), line_total (NUMERIC 12,2)
- Relationships: Belongs to bill; references item (for historical data, snapshots stored to preserve pricing at time of sale)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All FastAPI endpoints return correct HTTP status codes (201 for creation, 200 for success, 422 for validation, 400 for business logic errors, 404 for not found) with error responses in custom format: 422 errors include `{"error": "...", "fields": {"field_name": "error message"}}`, 400 errors include `{"error": "..."}`
- **SC-002**: All endpoints are fully testable and working correctly when tested via Postman (zero errors, correct response bodies, correct data persistence)
- **SC-003**: Comprehensive pytest test suite covers all endpoints with positive and negative test cases (minimum 60+ tests covering all functional requirements)
- **SC-004**: Test suite achieves >90% code coverage on core business logic (services, models, schemas)
- **SC-005**: All tests pass consistently (100% pass rate, zero flaky tests)
- **SC-006**: Bills created via API correctly decrement stock in database (verified by querying items table after bill creation)
- **SC-007**: Decimal quantities and prices are handled with correct precision: prices/totals returned as strings (e.g., "160.50"), quantities as numbers; verified in Postman JSON responses
- **SC-008**: Transaction handling ensures no partial bills are created if any step fails (all-or-nothing atomicity)
- **SC-009**: Swagger/OpenAPI documentation at `/docs` auto-generates for all endpoints with correct request/response schemas
- **SC-010**: API response time for item list (GET /items) is under 200ms for dataset of 1000+ items
- **SC-011**: API response time for bill creation (POST /bills) is under 500ms

---

## Clarifications

### Session 2025-12-08

- **Q1**: Error response structure format → **A**: Custom format with field-level errors: `{"error": "Validation failed", "fields": {"unit_price": "must be >= 0"}}`
- **Q2**: Bill listing pagination behavior → **A**: Return all bills without pagination (no limit/offset); aligns with Phase 2 scope and small dataset assumption
- **Q3**: Decimal precision in JSON responses → **B**: Return prices/totals as strings (`"unit_price": "160.50"`), quantities as numbers (`"quantity": 2.5`) to preserve exact NUMERIC precision
- **Q4**: Stock validation timing in bill creation → **A**: Validate all stock upfront before any database writes; if insufficient, return 400 error immediately; if sufficient, create bill+items+decrement in atomic transaction

---

## Assumptions & Constraints

### Assumptions

- PostgreSQL database from Phase 1 is available and contains the schema (items, bills, bill_items tables)
- SQLAlchemy ORM will be used for all database operations
- Pydantic will be used for request/response validation
- Uvicorn will run the FastAPI application locally on port 8000
- CORS will be configured to allow requests from frontend (Phase 3) which may be on different port
- Session-based or stateless request handling (no persistent session state needed)
- All timestamps use UTC and ISO 8601 format
- Decimal quantities and prices use PostgreSQL NUMERIC type for precision

### Constraints

- Out of scope: Authentication & Authorization (all endpoints accessible without auth in Phase 2)
- Out of scope: Pagination limits (Phase 2 assumes small datasets; pagination can be added later)
- Out of scope: Advanced filtering (only basic name/category search for Phase 2)
- Out of scope: Discount/tax fields (basic bill total only; can be added in Phase 2 enhancement)
- Out of scope: Concurrent stock reservation (optimistic locking not required for Phase 2)
- Out of scope: Rate limiting and request throttling
- Out of scope: Data export/import functionality
- Out of scope: Multi-store stock management (single store for Phase 2; multi-store field exists for future use)

---

## Definition of Done (DoD)

A requirement is considered "done" when:

1. **Code**: Implementation in FastAPI/SQLAlchemy following folder structure specified
2. **Tests**: Comprehensive pytest tests exist covering positive and negative scenarios
3. **Documentation**: Swagger/OpenAPI docs auto-generate correctly
4. **Verification**: All acceptance scenarios pass when tested via Postman
5. **Data**: PostgreSQL reflects changes correctly (verified via direct query or Postman GET requests)
6. **Quality**: Code follows Python PEP 8 style guidelines and SQLAlchemy best practices
7. **Integration**: No breaking changes to existing database schema from Phase 1

---

## Next Steps (After Specification Approval)

1. **Clarify** any ambiguous requirements via `/sp.clarify`
2. **Plan** architectural implementation via `/sp.plan`
3. **Break down** into testable tasks via `/sp.tasks`
4. **Implement** with TDD (red-green-refactor) via `/sp.implement`
5. **Test** all endpoints via Postman and ensure zero failures
