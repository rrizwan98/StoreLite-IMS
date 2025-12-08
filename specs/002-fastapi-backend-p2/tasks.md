# Tasks: FastAPI Backend (Phase 2) - IMS REST API

**Input**: Specification from `/specs/002-fastapi-backend-p2/spec.md` + Plan from `/specs/002-fastapi-backend-p2/plan.md`
**Prerequisites**: Phase 1 console app complete with all business logic (inventory, billing services)

**Tests**: TDD-driven; tests written FIRST, executed BEFORE implementation (Red-Green-Refactor cycle per Constitution Principle II)

**Organization**: Tasks grouped by phase and user story to enable independent implementation and testing. All P1 user stories (US1-3, US6-7) are critical path; P2 stories (US4-5, US8) add functionality after core API works.

**Path Convention**: `backend/app/` for FastAPI code, `backend/tests/` for pytest (following plan.md structure)

**Status**:
- ✅ **Phase 1 Setup**: Pending (Database config, dependencies)
- ✅ **Phase 2 Foundation**: Pending (Models, schemas, error handlers)
- 🚀 **Phase 3-5 User Stories**: Ready after foundation complete
- ⏳ **Phase 6 Polish**: After all stories implemented

**Total Progress**: 0/65 tasks | Ready for TDD Red-Green-Refactor implementation

---

## Phase Overview & Dependencies

### User Story Dependencies

**P1 Stories (Critical Path - Must Complete First):**
1. **US1**: Create Item (POST /items) - Foundation for inventory
2. **US2**: List & Search Items (GET /items) - Read inventory
3. **US3**: Get Single Item (GET /items/{id}) - Item detail lookup
4. **US6**: Create Bill (POST /bills) - Revenue feature
5. **US7**: Get Bill Details (GET /bills/{id}) - Invoice display

**P2 Stories (Enhancement - After P1 Complete):**
6. **US4**: Update Item (PUT /items/{id}) - Inventory management
7. **US5**: Deactivate Item (DELETE /items/{id}) - Data cleanup
8. **US8**: List Bills (GET /bills) - Reporting

### Parallel Opportunities

**Foundation Phase** (all can run in parallel with shared infrastructure):
- Developers A, B, C: Work on models, schemas, database in parallel

**User Stories** (after foundation, these can run independently):
- Developer A: US1 + US2 + US3 (Inventory CRUD - P1)
- Developer B: US6 + US7 (Billing - P1)
- Developer C: US4 + US5 + US8 (Enhancements - P2)

Or all developers together on critical path (US1-3, US6-7), then enhancements.

---

## Phase 1: Setup (Project Infrastructure)

**Purpose**: Project initialization, dependencies, database connectivity, configuration

**Execution**: Sequential; foundation MUST be complete before Phase 2 begins

- [ ] T001 Create FastAPI project structure: `backend/app/` with `__init__.py`, `main.py`, `database.py`, `models.py`, `schemas.py`, `exceptions.py`, `routers/` directory
- [ ] T002 [P] Create `backend/tests/` directory with `conftest.py` and subdirs: `unit/`, `integration/`, `contract/`
- [ ] T003 Create `backend/requirements.txt` with dependencies: FastAPI, Uvicorn, SQLAlchemy[asyncio], psycopg2-binary, Pydantic, pytest, pytest-asyncio
- [ ] T004 [P] Create `backend/.env.example` with template: `DATABASE_URL=postgresql://user:pass@localhost/ims_db` and `APP_ENV=development`
- [ ] T005 [P] Create `backend/.env` with actual DATABASE_URL from Phase 1 (git-ignored)
- [ ] T006 Implement database connection in `backend/app/database.py`: SQLAlchemy engine, session management, async support using `sessionmaker(class_=AsyncSession)`
- [ ] T007 [P] Create pytest configuration in `backend/tests/conftest.py` with: test database fixture, FastAPI TestClient fixture, session fixtures

**Checkpoint**: Dependencies installed, database connected, pytest configured and running

---

## Phase 2: Foundation (Blocking Prerequisites)

**Purpose**: Core models, schemas, error handlers that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete (all tests must pass)

### Database Models & SQLAlchemy ORM

- [ ] T008 [P] Create Item model in `backend/app/models.py` with SQLAlchemy ORM: id (PK), name, category, unit, unit_price (NUMERIC 12,2), stock_qty (NUMERIC 12,3), is_active (bool), created_at, updated_at; include __tablename__ = 'items'
- [ ] T009 [P] Create Bill model in `backend/app/models.py`: id (PK), customer_name (optional), store_name (optional), total_amount (NUMERIC 12,2), created_at; include __tablename__ = 'bills'
- [ ] T010 [P] Create BillItem model in `backend/app/models.py`: id (PK), bill_id (FK), item_id (FK), item_name (snapshot), unit_price (snapshot NUMERIC 12,2), quantity (NUMERIC 12,3), line_total (NUMERIC 12,2); relationships to Bill
- [ ] T011 [P] Add SQLAlchemy relationships: Bill.bill_items (one-to-many), BillItem.bill (many-to-one)

### Pydantic Request/Response Schemas

- [ ] T012 [P] Create ItemCreate schema in `backend/app/schemas.py`: name, category, unit, unit_price (validated ≥0), stock_qty (validated ≥0); add Pydantic validator for non-negative numbers
- [ ] T013 [P] Create ItemUpdate schema in `backend/app/schemas.py`: unit_price (optional, ≥0), stock_qty (optional, ≥0), name (optional), category (optional), unit (optional); all fields optional
- [ ] T014 [P] Create ItemResponse schema in `backend/app/schemas.py`: id, name, category, unit, unit_price (as string), stock_qty, is_active, created_at, updated_at; with field_serializer for Decimal → string conversion
- [ ] T015 [P] Create BillItemCreate schema in `backend/app/schemas.py`: item_id, quantity (validated >0); no unit_price (auto-fetched)
- [ ] T016 [P] Create BillCreate schema in `backend/app/schemas.py`: items (array of BillItemCreate), customer_name (optional), store_name (optional)
- [ ] T017 [P] Create BillItemResponse schema in `backend/app/schemas.py`: item_name, unit_price (as string), quantity, line_total (as string)
- [ ] T018 [P] Create BillResponse schema in `backend/app/schemas.py`: id, customer_name, store_name, total_amount (as string), created_at, bill_items (array of BillItemResponse)

### Error Handling & Custom Exceptions

- [ ] T019 Create custom exceptions in `backend/app/exceptions.py`:
  - `ValidationError`: for 422 validation failures (with fields dict)
  - `BusinessLogicError`: for 400 business logic errors (with error message)
  - `NotFoundError`: for 404 not found errors
  - `DatabaseError`: for transaction/DB failures
- [ ] T020 Implement error handlers in `backend/app/main.py`:
  - `@app.exception_handler(ValidationError)`: return 422 with `{"error": "Validation failed", "fields": {...}}`
  - `@app.exception_handler(BusinessLogicError)`: return 400 with `{"error": "..."}`
  - `@app.exception_handler(NotFoundError)`: return 404 with `{"error": "..."}`
  - `@app.exception_handler(Exception)`: return 500 with generic error message

### FastAPI App Initialization

- [ ] T021 [P] Create main FastAPI app in `backend/app/main.py`: initialize FastAPI(), configure CORS, include routers (to be created in US stories), add error handlers
- [ ] T022 [P] Add startup/shutdown events in `backend/app/main.py`: verify database connection on startup, log app start

**Checkpoint**: All models, schemas, and error handlers defined and unit tested. TDD: write model/schema tests first (RED), create models/schemas (GREEN), refactor (REFACTOR).

---

## Phase 3: User Story 1 - Admin: Create New Inventory Item (Priority: P1) 🎯 MVP

**Goal**: Users can add new products to inventory via `POST /items` endpoint with full validation and persistence to PostgreSQL.

**Independent Test**: Call `POST /items` with valid data, verify item created in DB with auto-generated ID and all fields persisted correctly.

**Acceptance Criteria**:
- ✅ Valid POST request creates item with 201 status
- ✅ Item stored in database with auto-generated ID
- ✅ Validation rejects negative prices/stock (422 status)
- ✅ Missing required fields rejected with 422 status and field-level errors
- ✅ Duplicate item names allowed (different stores can have same product)
- ✅ Large decimal quantities accepted and stored correctly

### Unit Tests for US1 (TDD - Write FIRST)

- [ ] T023 [P] [US1] Unit test for ItemCreate schema validation in `backend/tests/unit/test_schemas.py`:
  - Test valid item creation payload passes validation
  - Test negative unit_price rejected
  - Test negative stock_qty rejected
  - Test missing required fields rejected with field errors
  - Test decimal quantities accepted (e.g., 100.5 for 100.5kg)
- [ ] T024 [P] [US1] Unit test for Item model constraints in `backend/tests/unit/test_models.py`:
  - Test Item model creation with all fields
  - Test model fields match schema
  - Test NUMERIC precision for prices/quantities

### Contract Tests for US1 (Endpoint-Level - Write FIRST)

- [ ] T025 [P] [US1] Contract test for POST /items endpoint in `backend/tests/contract/test_inventory_endpoints.py`:
  - Test: Valid request → 201 status, item returned with ID
  - Test: Negative price → 422 with field error
  - Test: Negative stock → 422 with field error
  - Test: Missing name → 422 with field error
  - Test: Duplicate name allowed → 201 status

### Integration Tests for US1 (Full Flow - Write FIRST)

- [ ] T026 [US1] Integration test for item creation flow in `backend/tests/integration/test_inventory_flow.py`:
  - Test: Create item via POST → verify stored in DB
  - Test: Create item, retrieve via GET /items → verify appears in list
  - Test: Create multiple items → all appear in list

### Implementation for US1

- [ ] T027 Create inventory router in `backend/app/routers/inventory.py` with POST endpoint:
  - `@router.post("/items", response_model=ItemResponse, status_code=201)`
  - Accept ItemCreate schema
  - Validate using Pydantic (raises ValidationError for invalid data)
  - Create Item model instance
  - Insert into database session
  - Commit transaction
  - Return created item with 201 status
  - Catch database errors and raise BusinessLogicError
- [ ] T028 [P] [US1] Implement request validation in ItemCreate schema with @field_validator for non-negative constraints
- [ ] T029 [US1] Add structured logging to POST /items in router: log request details, response status, duration
- [ ] T030 [P] [US1] Include inventory router in main.py: `app.include_router(inventory_router, prefix="/api", tags=["inventory"])`

**Checkpoint**: User Story 1 complete and independently testable. Can demo "Create item" workflow.

---

## Phase 4: User Story 2 - Admin: List and Search Inventory Items (Priority: P1)

**Goal**: Users can retrieve all products or search by name/category via `GET /items` endpoint with filtering.

**Independent Test**: Call `GET /items`, verify all active items returned. Call `GET /items?name=sugar`, verify only matching items returned (case-insensitive).

**Acceptance Criteria**:
- ✅ GET /items returns all active items
- ✅ Inactive items (is_active=false) excluded
- ✅ Optional name filter: case-insensitive partial match
- ✅ Optional category filter: exact match
- ✅ Both filters combined: AND logic
- ✅ No results returns empty list with 200 status
- ✅ Results ordered by name alphabetically

### Unit Tests for US2 (TDD - Write FIRST)

- [ ] T031 [P] [US2] Unit test for GET /items query validation in `backend/tests/unit/test_schemas.py`:
  - Test valid filter parameters accepted
  - Test invalid parameters rejected (if any)

### Contract Tests for US2 (Endpoint-Level - Write FIRST)

- [ ] T032 [P] [US2] Contract test for GET /items endpoint in `backend/tests/contract/test_inventory_endpoints.py`:
  - Test: No filters → returns all active items
  - Test: name filter → case-insensitive match
  - Test: category filter → exact match
  - Test: both filters → AND logic
  - Test: no matches → empty list, 200 status
  - Test: inactive items excluded

### Integration Tests for US2 (Full Flow - Write FIRST)

- [ ] T033 [US2] Integration test for list/search flow in `backend/tests/integration/test_inventory_flow.py`:
  - Test: Add items, list all → all appear
  - Test: Search by name → correct items returned
  - Test: Search by category → correct items returned
  - Test: Case-insensitive search works

### Implementation for US2

- [ ] T034 Create GET /items endpoint in `backend/app/routers/inventory.py`:
  - `@router.get("/items", response_model=list[ItemResponse])`
  - Accept optional query params: name (str), category (str)
  - Query database: SELECT * FROM items WHERE is_active=true
  - Apply name filter if provided: WHERE name ILIKE '%{name}%'
  - Apply category filter if provided: WHERE category = {category}
  - Order by name ASC
  - Return list of ItemResponse
- [ ] T035 [P] [US2] Add structured logging to GET /items: log query params, result count, response status
- [ ] T036 [US2] Handle empty results gracefully: return empty list with 200 status, not error

**Checkpoint**: User Stories 1 & 2 complete. Can demo "Add item → List items" workflow.

---

## Phase 5: User Story 3 - Admin: Get Single Item Details (Priority: P1)

**Goal**: Users can retrieve details for a specific item by ID via `GET /items/{id}` endpoint.

**Independent Test**: Call `GET /items/{id}` with valid ID, verify item details returned. Call with invalid ID, verify 404 error.

**Acceptance Criteria**:
- ✅ Valid ID returns item with 200 status
- ✅ Invalid ID returns 404 error
- ✅ Non-numeric ID returns 422 validation error
- ✅ Soft-deleted items (is_active=false) return 404 (not found)

### Unit Tests for US3 (TDD - Write FIRST)

- [ ] T037 [P] [US3] Unit test for ID validation in `backend/tests/unit/test_schemas.py`:
  - Test valid numeric ID accepted
  - Test non-numeric ID rejected with 422

### Contract Tests for US3 (Endpoint-Level - Write FIRST)

- [ ] T038 [P] [US3] Contract test for GET /items/{id} endpoint in `backend/tests/contract/test_inventory_endpoints.py`:
  - Test: Valid ID → 200 status, item details returned
  - Test: Non-existent ID → 404 error
  - Test: Non-numeric ID → 422 validation error
  - Test: Soft-deleted item → 404 error

### Integration Tests for US3 (Full Flow - Write FIRST)

- [ ] T039 [US3] Integration test for single item detail flow in `backend/tests/integration/test_inventory_flow.py`:
  - Test: Create item, fetch by ID → correct details returned
  - Test: Fetch non-existent → 404 error
  - Test: Deactivate item, fetch → 404 error

### Implementation for US3

- [ ] T040 Create GET /items/{id} endpoint in `backend/app/routers/inventory.py`:
  - `@router.get("/items/{item_id}", response_model=ItemResponse)`
  - Path param: item_id (int, validated by FastAPI)
  - Query database: SELECT * FROM items WHERE id={item_id} AND is_active=true
  - If not found: raise NotFoundError with "Item not found"
  - Return ItemResponse with 200 status
- [ ] T041 [P] [US3] Add structured logging to GET /items/{id}: log item_id, found status
- [ ] T042 [US3] Handle not found gracefully: return 404 with error message, not 500

**Checkpoint**: User Stories 1, 2, 3 complete. Full inventory read/create workflow functional and independently testable.

---

## Phase 6: User Story 6 - Salesperson: Create Bill/Invoice (Priority: P1)

**Goal**: Users can create bills with multiple items, automatic total calculation, and atomic stock deduction via `POST /bills` endpoint.

**Independent Test**: Call `POST /bills` with valid items, verify bill created, totals calculated correctly, and stock decremented.

**Acceptance Criteria**:
- ✅ Valid POST request creates bill with 201 status
- ✅ Bill totals calculated correctly: line_total = unit_price × quantity, bill total = sum of line_totals
- ✅ Stock quantities decremented atomically after bill creation
- ✅ Insufficient stock returns 400 error before any changes
- ✅ Non-existent item returns 400 error
- ✅ Zero or negative quantity returns 422 validation error
- ✅ Decimal quantities (e.g., 2.5 kg) supported and calculated correctly
- ✅ Optional customer_name and store_name supported
- ✅ All-or-nothing atomicity: if any step fails, rollback entire transaction

### Unit Tests for US6 (TDD - Write FIRST)

- [ ] T043 [P] [US6] Unit test for BillCreate schema validation in `backend/tests/unit/test_schemas.py`:
  - Test valid bill payload passes validation
  - Test zero quantity rejected (422)
  - Test negative quantity rejected (422)
  - Test items array required
  - Test empty items array rejected
  - Test decimal quantity accepted
- [ ] T044 [P] [US6] Unit test for bill total calculation in `backend/tests/unit/test_services.py`:
  - Test line_total = unit_price × quantity
  - Test decimal calculations accurate
  - Test sum of line_totals equals bill total

### Contract Tests for US6 (Endpoint-Level - Write FIRST)

- [ ] T045 [P] [US6] Contract test for POST /bills endpoint in `backend/tests/contract/test_billing_endpoints.py`:
  - Test: Valid bill → 201 status, bill with ID returned
  - Test: Insufficient stock → 400 error
  - Test: Non-existent item → 400 error
  - Test: Zero quantity → 422 error
  - Test: Negative quantity → 422 error
  - Test: Decimal quantity → 201 status, accepted
  - Test: Optional customer/store names → 201 status with NULL values

### Integration Tests for US6 (Full Flow - Write FIRST)

- [ ] T046 [US6] Integration test for bill creation flow in `backend/tests/integration/test_billing_flow.py`:
  - Test: Create item with stock=100, create bill with qty=10 → bill created, stock = 90
  - Test: Create bill with multiple items → all line_totals calculated, stock decremented for all
  - Test: Create bill with insufficient stock → bill NOT created, stock unchanged
  - Test: Transaction rollback on error → no partial bills
  - Test: Decimal quantity → stock calculated correctly (e.g., stock=10kg, sell=2.5kg, remaining=7.5kg)

### Implementation for US6

- [ ] T047 Create POST /bills endpoint in `backend/app/routers/billing.py`:
  - `@router.post("/bills", response_model=BillResponse, status_code=201)`
  - Accept BillCreate schema
  - **Upfront Validation** (before any DB writes):
    - For each item in items array:
      - Fetch item from DB
      - Check if exists; if not, raise BusinessLogicError("Item not found")
      - Check if current stock_qty ≥ requested quantity; if not, raise BusinessLogicError("Insufficient stock for item {item_name}")
  - If any validation fails, raise error and return 400 (no bill created)
  - If all validations pass:
    - Begin transaction
    - Create Bill instance with total_amount = sum of (item.unit_price × quantity)
    - Insert Bill into database
    - For each item:
      - Create BillItem with snapshots (item_name, unit_price, quantity, line_total)
      - Insert BillItem into database
    - For each item:
      - Decrement item.stock_qty by sold quantity
      - Update item in database
    - Commit transaction
    - Return BillResponse with 201 status
  - On transaction failure:
    - Catch exception, rollback, raise DatabaseError
- [ ] T048 [P] [US6] Implement BillCreate schema with validators:
  - items: list of BillItemCreate (required, non-empty)
  - BillItemCreate: item_id (required), quantity (required, >0, validated by @field_validator)
  - customer_name, store_name: optional strings
- [ ] T049 [US6] Implement bill total calculation in service layer (optional, can be inline in router):
  - `calculate_bill_total(items_with_prices)` → sum of (unit_price × quantity)
- [ ] T050 [US6] Add structured logging to POST /bills: log items, stock validation, transaction status, final total
- [ ] T051 [P] [US6] Ensure NUMERIC precision preserved in Decimal calculations: use Python Decimal type for arithmetic
- [ ] T052 [US6] Return bill with all bill_items in response: include BillItemResponse with string prices, numeric quantities

**Checkpoint**: User Stories 1-3 & 6 complete. Full "Add item → Create bill" workflow functional.

---

## Phase 7: User Story 7 - Salesperson/Admin: Retrieve Bill Details (Priority: P1)

**Goal**: Users can retrieve complete bill details including all line items via `GET /bills/{id}` endpoint.

**Independent Test**: Call `GET /bills/{id}` with valid ID, verify bill with all line items returned. Call with invalid ID, verify 404 error.

**Acceptance Criteria**:
- ✅ Valid bill ID returns complete bill with header and all line items (200 status)
- ✅ Invalid bill ID returns 404 error
- ✅ Response includes all bill_items with snapshots (item_name, unit_price, quantity, line_total)
- ✅ Prices returned as strings, quantities as numbers
- ✅ Timestamp in ISO 8601 format

### Unit Tests for US7 (TDD - Write FIRST)

- [ ] T053 [P] [US7] Unit test for Bill model relationships in `backend/tests/unit/test_models.py`:
  - Test Bill.bill_items relationship returns all line items
  - Test BillItem fields match response schema

### Contract Tests for US7 (Endpoint-Level - Write FIRST)

- [ ] T054 [P] [US7] Contract test for GET /bills/{id} endpoint in `backend/tests/contract/test_billing_endpoints.py`:
  - Test: Valid bill ID → 200 status, complete bill returned
  - Test: Non-existent bill ID → 404 error
  - Test: Response includes all bill_items
  - Test: Prices returned as strings, quantities as numbers
  - Test: Timestamp in ISO 8601 format

### Integration Tests for US7 (Full Flow - Write FIRST)

- [ ] T055 [US7] Integration test for bill detail retrieval in `backend/tests/integration/test_billing_flow.py`:
  - Test: Create bill, retrieve by ID → complete bill with items returned
  - Test: Retrieve non-existent bill → 404 error
  - Test: Multiple bills exist, retrieve one → correct bill returned

### Implementation for US7

- [ ] T056 Create GET /bills/{id} endpoint in `backend/app/routers/billing.py`:
  - `@router.get("/bills/{bill_id}", response_model=BillResponse)`
  - Path param: bill_id (int)
  - Query database: SELECT * FROM bills WHERE id={bill_id}
  - If not found: raise NotFoundError("Bill not found")
  - Eager load bill_items: populate relationship or manual query
  - Return BillResponse with 200 status
- [ ] T057 [P] [US7] Implement BillResponse serialization:
  - Include all BillItem details (item_name, unit_price as string, quantity as number, line_total as string)
  - Include bill metadata (id, customer_name, store_name, total_amount as string, created_at in ISO format)
- [ ] T058 [US7] Add structured logging to GET /bills/{id}: log bill_id, item count, response status

**Checkpoint**: Core P1 Stories (1-3, 6-7) complete and tested. MVP "Create inventory → Create bill → View bill" workflow fully functional and Postman-compatible.

---

## Phase 8: User Story 4 - Admin: Update Item Price and Stock (Priority: P2)

**Goal**: Users can update product prices and stock quantities via `PUT /items/{id}` endpoint with partial update support.

**Independent Test**: Call `PUT /items/{id}` with new price/stock, verify changes persist in database.

**Acceptance Criteria**:
- ✅ Valid update returns updated item (200 status)
- ✅ Partial update: only provided fields updated, others unchanged
- ✅ Negative price returns 422 validation error
- ✅ Non-existent item returns 404 error
- ✅ Name and category can be updated if provided

### Unit Tests for US4 (TDD - Write FIRST)

- [ ] T059 [P] [US4] Unit test for ItemUpdate schema validation in `backend/tests/unit/test_schemas.py`:
  - Test all fields optional
  - Test negative price rejected
  - Test negative stock rejected
  - Test empty update (no fields) accepted

### Contract Tests for US4 (Endpoint-Level - Write FIRST)

- [ ] T060 [P] [US4] Contract test for PUT /items/{id} endpoint in `backend/tests/contract/test_inventory_endpoints.py`:
  - Test: Update price → 200 status, updated item returned
  - Test: Update stock → 200 status, updated item returned
  - Test: Update both → 200 status
  - Test: Negative price → 422 error
  - Test: Non-existent item → 404 error
  - Test: Partial update leaves other fields unchanged

### Integration Tests for US4 (Full Flow - Write FIRST)

- [ ] T061 [US4] Integration test for item update flow in `backend/tests/integration/test_inventory_flow.py`:
  - Test: Create item, update price → DB reflects change
  - Test: Update stock, verify in list → change visible
  - Test: Update non-existent item → 404 error

### Implementation for US4

- [ ] T062 Create PUT /items/{id} endpoint in `backend/app/routers/inventory.py`:
  - `@router.put("/items/{item_id}", response_model=ItemResponse)`
  - Path param: item_id (int)
  - Accept ItemUpdate schema (all fields optional)
  - Query database: SELECT * FROM items WHERE id={item_id}
  - If not found: raise NotFoundError("Item not found")
  - Update only provided fields:
    - If unit_price provided: item.unit_price = unit_price
    - If stock_qty provided: item.stock_qty = stock_qty
    - If name provided: item.name = name
    - If category provided: item.category = category
    - If unit provided: item.unit = unit
  - Update updated_at timestamp
  - Commit transaction
  - Return updated ItemResponse with 200 status
- [ ] T063 [P] [US4] Implement ItemUpdate schema with all fields optional
- [ ] T064 [US4] Add structured logging to PUT /items/{id}: log item_id, fields updated, response status

**Checkpoint**: P2 enhancement stories starting. Core inventory management complete.

---

## Phase 9: User Story 5 - Admin: Deactivate Items (Priority: P2)

**Goal**: Users can soft-delete items via `DELETE /items/{id}` endpoint without losing historical data.

**Independent Test**: Call `DELETE /items/{id}`, verify item no longer appears in list but historical bills still reference it.

**Acceptance Criteria**:
- ✅ Valid delete marks item as inactive (is_active=false) with 204 or 200 status
- ✅ Deactivated items excluded from GET /items list
- ✅ Deactivated items return 404 when fetched by ID
- ✅ Non-existent item returns 404 error
- ✅ Historical billing data preserved (bills still reference deactivated items)

### Unit Tests for US5 (TDD - Write FIRST)

- [ ] T065 [P] [US5] Unit test for soft-delete logic in `backend/tests/unit/test_models.py`:
  - Test is_active = false marks item as deleted
  - Test soft-deleted items excluded from queries

### Contract Tests for US5 (Endpoint-Level - Write FIRST)

- [ ] T066 [P] [US5] Contract test for DELETE /items/{id} endpoint in `backend/tests/contract/test_inventory_endpoints.py`:
  - Test: Valid ID → 204 status (or 200)
  - Test: Non-existent ID → 404 error
  - Test: Deleted item no longer in GET /items list
  - Test: Deleted item returns 404 when fetched by ID

### Integration Tests for US5 (Full Flow - Write FIRST)

- [ ] T067 [US5] Integration test for soft-delete flow in `backend/tests/integration/test_inventory_flow.py`:
  - Test: Create item, delete it, list items → item not in list
  - Test: Delete item with historical bills → bills still accessible
  - Test: Delete non-existent item → 404 error

### Implementation for US5

- [ ] T068 Create DELETE /items/{id} endpoint in `backend/app/routers/inventory.py`:
  - `@router.delete("/items/{item_id}", status_code=204)`
  - Path param: item_id (int)
  - Query database: SELECT * FROM items WHERE id={item_id}
  - If not found: raise NotFoundError("Item not found")
  - Set item.is_active = false
  - Update updated_at timestamp
  - Commit transaction
  - Return 204 status (no content)
- [ ] T069 [P] [US5] Verify all item queries filter by is_active=true: check GET /items, GET /items/{id} exclude inactive
- [ ] T070 [US5] Add structured logging to DELETE /items/{id}: log item_id, deactivation status

**Checkpoint**: Item management complete (create, read, update, deactivate).

---

## Phase 10: User Story 8 - Admin: List All Bills (Priority: P2)

**Goal**: Users can retrieve all bills with optional filtering via `GET /bills` endpoint for reporting.

**Independent Test**: Call `GET /bills`, verify all bills returned. Call `GET /bills?start_date=...&end_date=...`, verify filtered by date range.

**Acceptance Criteria**:
- ✅ GET /bills returns all bills (no pagination - return all)
- ✅ Optional date range filtering (start_date, end_date)
- ✅ Optional customer_name filter (partial match)
- ✅ No results returns empty list with 200 status
- ✅ Timestamps in ISO 8601 format

### Unit Tests for US8 (TDD - Write FIRST)

- [ ] T071 [P] [US8] Unit test for date range filtering logic in `backend/tests/unit/test_services.py`:
  - Test bills within date range selected
  - Test bills outside date range excluded
  - Test date parsing (ISO 8601 format)

### Contract Tests for US8 (Endpoint-Level - Write FIRST)

- [ ] T072 [P] [US8] Contract test for GET /bills endpoint in `backend/tests/contract/test_billing_endpoints.py`:
  - Test: No filters → all bills returned
  - Test: Date range filter → bills within range returned
  - Test: Customer name filter → matching bills returned
  - Test: No results → empty list, 200 status
  - Test: Timestamps in ISO 8601 format

### Integration Tests for US8 (Full Flow - Write FIRST)

- [ ] T073 [US8] Integration test for bill listing flow in `backend/tests/integration/test_billing_flow.py`:
  - Test: Create multiple bills, list all → all returned
  - Test: Create bills on different dates, filter by date → correct subset returned
  - Test: Create bills for different customers, filter → correct subset returned

### Implementation for US8

- [ ] T074 Create GET /bills endpoint in `backend/app/routers/billing.py`:
  - `@router.get("/bills", response_model=list[BillResponse])`
  - Accept optional query params: start_date (ISO date), end_date (ISO date), customer_name (str)
  - Query database: SELECT * FROM bills WHERE created_at BETWEEN start_date AND end_date
  - Apply customer_name filter if provided: WHERE customer_name ILIKE '%{customer_name}%'
  - Order by created_at DESC (newest first)
  - Return list of BillResponse with 200 status
- [ ] T075 [P] [US8] Implement date range parsing:
  - Accept ISO 8601 date format (YYYY-MM-DD)
  - Convert to datetime with start of day (00:00:00) and end of day (23:59:59)
  - Validate date format, reject invalid dates with 422 error
- [ ] T076 [US8] Add structured logging to GET /bills: log filter params, result count, response status

**Checkpoint**: P2 enhancement stories complete. Full system functional with reporting capabilities.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Testing, documentation, observability, and final validation

### Unit Test Coverage & Edge Cases

- [ ] T077 [P] Add remaining unit tests for edge cases in `backend/tests/unit/`:
  - Extremely large decimal values (NUMERIC max)
  - Decimal precision in calculations (Decimal type)
  - Empty/null optional fields
  - Special characters in item names, customer names
  - Very long names (no truncation limit in Phase 2, but test handling)
  - Zero price items (allowed per spec)
  - Concurrent operations (if applicable)

### Integration Test Coverage

- [ ] T078 [P] Add end-to-end integration tests in `backend/tests/integration/test_e2e.py`:
  - Full workflow: Add item → List → Search → Create bill → Verify invoice → Check stock → Retrieve bill
  - Multiple items in single bill → totals calculated correctly
  - Multiple bills sequentially → each processed independently
  - Database persistence across app restarts (add item, restart, retrieve)

### Contract Tests (API Contract Validation)

- [ ] T079 [P] Add error response format validation tests in `backend/tests/contract/test_error_responses.py`:
  - 422 Validation errors have correct format: `{"error": "Validation failed", "fields": {...}}`
  - 400 Business logic errors have format: `{"error": "..."}`
  - 404 Not found errors have format: `{"error": "..."}`
  - All error responses have consistent structure

- [ ] T080 [P] Add response format validation tests in `backend/tests/contract/test_response_formats.py`:
  - All prices/totals returned as strings (e.g., "160.50")
  - All quantities returned as numbers (e.g., 2.5)
  - All timestamps in ISO 8601 format
  - All response codes match spec (201, 200, 422, 400, 404)

### Code Quality & Coverage

- [ ] T081 [P] Run pytest with coverage: `pytest --cov=backend/app backend/tests/ -v --tb=short`
  - Target: ≥90% coverage on core logic (models, schemas, routers, services)
  - Identify coverage gaps
- [ ] T082 [P] Fix any coverage gaps: add tests or refactor code to improve testability
- [ ] T083 [P] Code formatting and linting (if using black/flake8):
  - `black backend/app backend/tests`
  - `flake8 backend/app backend/tests` (or ruff check)

### Documentation & Swagger

- [ ] T084 [P] Verify Swagger/OpenAPI docs at `GET /docs`:
  - All endpoints documented
  - Request/response schemas shown correctly
  - Error codes documented
  - Can import schema into Postman

- [ ] T085 Create/update `backend/README.md` with:
  - Project overview
  - Setup instructions (clone, .env, pip install, database setup)
  - How to run the app: `uvicorn app.main:app --reload --port 8000`
  - How to run tests: `pytest tests/ -v --cov=app`
  - Architecture overview (routers, services, models, schemas)
  - Example API calls (curl or Postman examples)

- [ ] T086 [P] Create `backend/QUICKSTART.md` with:
  - Step-by-step guide to test all endpoints
  - Example requests/responses for each endpoint
  - Postman collection import instructions
  - Troubleshooting common issues

### Final Validation & Testing

- [ ] T087 Run all tests: `pytest backend/tests/ -v` → 100% pass rate, no flaky tests
- [ ] T088 [P] Manual testing in Postman (or curl):
  - Test all endpoints with valid data → expect success
  - Test all endpoints with invalid data → expect correct errors
  - Create full workflow: add item → list → search → create bill → view bill
  - Verify stock decrements correctly
  - Verify error messages are user-friendly
  - Verify no stack traces in error responses

- [ ] T089 [P] Performance testing (manual):
  - Test GET /items with 1000+ items in database → response time < 200ms
  - Test POST /bills → response time < 500ms
  - Log response times for future optimization reference

- [ ] T090 Verify all constitution principles are met:
  - ✅ Separation of Concerns: backend in /backend, no frontend yet
  - ✅ TDD: >90% coverage, all tests passing
  - ✅ Phased Implementation: Phase 2 reuses Phase 1 logic, no duplication
  - ✅ Database-First: PostgreSQL with ORM, snapshots in bill_items, soft deletes
  - ✅ Contract-First APIs: Pydantic schemas, Swagger docs, custom error formats
  - ✅ Local-First Development: .env for DATABASE_URL, no hardcoded secrets
  - ✅ Simplicity Over Abstraction: Direct SQLAlchemy queries, no repo pattern
  - ✅ Observability: Structured logging on all endpoints

- [ ] T091 Create test report documenting:
  - Total test count: 60+ tests
  - Coverage percentage: >90%
  - Pass rate: 100%
  - Edge cases covered (decimals, large numbers, concurrent, etc.)
  - Postman compatibility verified

**Checkpoint**: Phase 2 complete, all tests passing, documentation complete, ready for Phase 3 frontend integration.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies → Start immediately
- **Phase 2 (Foundation)**: Depends on Phase 1 → BLOCKS all user stories
- **Phase 3-5 (US1-3)**: Depend on Phase 2 → Can start after Phase 2, run in parallel
- **Phase 6-7 (US6-7)**: Depend on Phase 2 → Can start after Phase 2, run in parallel with US1-3
- **Phase 8-10 (US4-5, US8)**: Depend on Phase 2 → Can start after Phase 2, after P1 stories preferred
- **Phase 11 (Polish)**: Depends on all stories → Final phase

### Parallel Opportunities

**Foundation Phase** (all independent - can run in parallel):
```
Developer A: T008-T011 (SQLAlchemy models)
Developer B: T012-T018 (Pydantic schemas)
Developer C: T019-T022 (Error handlers, app init)
```

**P1 User Stories** (after foundation, independent stories):
```
Developer A: US1-3 (Inventory: Create, List, Get) - T023-T042
Developer B: US6-7 (Billing: Create, Get) - T043-T058
Developer C: (Optional) Running tests in parallel, fixing issues
```

**P2 Enhancement Stories** (after P1, independent):
```
Developer A: US4-5 (Inventory: Update, Delete) - T059-T070
Developer B: US8 (Billing: List) - T071-T076
Developer C: (Optional) Polish, testing, documentation
```

---

## Implementation Strategies

### MVP First (Recommended - Fast to working app)

**Scope**: Just P1 stories (US1-3, US6-7)

1. **Complete Phase 1 Setup** (T001-T007): ~1 hour
2. **Complete Phase 2 Foundation** (T008-T022): ~2-3 hours
3. **Complete P1 Stories in Parallel**:
   - Developer A: US1-3 (Inventory CRUD)
   - Developer B: US6-7 (Billing)
   - Both: ~4-6 hours total
4. **Test & Polish** (T077-T091): ~1-2 hours

**Total**: ~8-12 hours for working MVP that can demo to users

**Benefits**:
- Delivers core "Add item → Create bill" workflow quickly
- Can gather feedback early
- P2 stories (enhancements) can be added later based on priorities

### Incremental Delivery (If all features needed)

1. Setup + Foundation (Phase 1-2)
2. **DEPLOY**: P1 stories only (US1-3, US6-7) → Users can manage inventory and create bills
3. Add US4-5 (Update/Deactivate items) → More inventory control
4. Add US8 (List bills) → Reporting capability
5. Polish and optimize

---

## Task Checklist Format Validation

✅ All tasks follow the format:
- `- [ ]` (checkbox)
- `[TaskID]` (T001-T091 sequential)
- `[P]` (parallelizable only)
- `[USX]` (user story label, only in user story phases)
- Description with exact file path

✅ Task organization:
- Setup phase (T001-T007)
- Foundation phase (T008-T022)
- User stories (P1 first: T023-T058, then P2: T059-T076)
- Polish phase (T077-T091)

✅ All tests marked as TDD (write FIRST, RED phase)

---

**Ready to begin? Start with Phase 1 Setup (T001-T007), then Phase 2 Foundation (T008-T022).**
**After foundation passes all tests, teams can split and work on user stories in parallel.**

