# Tasks: Console-Based Inventory & Billing System (Phases 1-7)

**Input**: Design documents from `/specs/001-console-ims-p1/`
**Prerequisites**: plan.md (architecture & decisions), spec.md (user stories), data-model.md (entities & schema), quickstart.md (setup guide)

**Tests**: TDD-driven; tests written FIRST, executed BEFORE implementation (Red-Green-Refactor cycle per Constitution Principle II)

**Organization**: Tasks grouped by phase and user story to enable independent implementation and testing. All three Phase 1 user stories are P1 priority; Phases 4-7 enhance and extend functionality.

**Path Convention**: `backend/src/` and `backend/tests/` (monolithic console app structure per plan.md)

**Status**:
- ✅ **Phase 1 Tasks**: COMPLETE (Core inventory & billing) - All tests PASSING
- ✅ **Phase 4 Tasks**: COMPLETE (Search enhancements & soft-delete) - All tests PASSING
- ✅ **Phase 5 Tasks**: COMPLETE (Shopping cart management) - All tests PASSING
- ✅ **Phase 6 Tasks**: COMPLETE (Main menu & statistics) - All tests PASSING
- ✅ **Phase 7 Tasks**: COMPLETE (Receipt formatting & comprehensive testing) - All tests PASSING
- 🚀 **Phase 2 Tasks**: IN PROGRESS (FastAPI Backend) - Specification & Planning COMPLETE

**Total Progress**:
- ✅ **Phases 1, 4-7**: 121 unit tests passing | All functionality implemented and tested
- 🚀 **Phase 2**: Spec complete, Plan complete, Ready for implementation
- ⏳ **Phase 3+**: Scheduled for future phases

---

## Phases 4-7 Summary

### Phase 4: Search Enhancements & Soft-Delete
- ✅ Search items by category (case-insensitive)
- ✅ Search items by price range (min/max validation)
- ✅ Soft-delete items (mark inactive, preserve history)
- ✅ Exclude inactive items from all operations
- ✅ Unit tests + integration tests

### Phase 5: Shopping Cart Management
- ✅ In-memory cart with add/view/update/remove operations
- ✅ Stock validation during cart operations
- ✅ Automatic line total and cart total calculation
- ✅ Itemized cart display format
- ✅ Prevention of empty cart confirmation
- ✅ Unit tests + integration tests

### Phase 6: Main Menu & System Statistics
- ✅ Enhanced main menu with category headers
- ✅ System statistics display (active item count)
- ✅ Improved UI formatting and spacing
- ✅ Contract tests for output format consistency

### Phase 7: Receipt Formatting & Testing
- ✅ Professional receipt format with:
  - Bill ID and timestamp
  - Customer name and store name (if provided)
  - Itemized list showing: item name, quantity, unit price, line total
  - Grand total amount
- ✅ End-to-end workflow tests (11 tests)
- ✅ Contract tests (25 tests)
- ✅ All tests passing

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, database schema, and foundational modules

**Execution**: Sequential; foundation MUST be complete before Phase 2 begins

- [ ] T001 Create backend directory structure (models/, services/, cli/, db.py) per plan.md
- [ ] T002 Create schema.sql with DDL for items, bills, bill_items tables per data-model.md
- [ ] T003 Initialize pyproject.toml with dependencies (SQLAlchemy, psycopg2, pytest, python-dotenv)
- [ ] T004 [P] Create .env.example with DATABASE_URL template
- [ ] T005 [P] Create backend/src/__init__.py and package structure
- [ ] T006 Implement database.py with SQLAlchemy session setup and connection management (reads DATABASE_URL from .env)
- [ ] T007 [P] Create pytest configuration (conftest.py with test database fixtures)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, services, and validation infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & ORM Models

- [ ] T008 [P] Create Item model in backend/src/models/item.py with SQLAlchemy ORM (id, name, category, unit, unit_price, stock_qty, is_active, timestamps)
- [ ] T009 [P] Create Bill model in backend/src/models/bill.py with SQLAlchemy ORM (id, customer_name, store_name, total_amount, created_at)
- [ ] T010 [P] Create BillItem model in backend/src/models/bill.py with SQLAlchemy ORM (id, bill_id, item_id, item_name, unit_price, quantity, line_total)
- [ ] T011 [P] Create Pydantic schemas in backend/src/models/schemas.py (ItemCreate, ItemUpdate, BillCreate, BillItemCreate - for Phase 2 API reuse)

### Shared Services & Utilities

- [ ] T012 Create validation service in backend/src/services/validation.py with functions for:
  - Validate category (must be one of: Grocery, Garments, Beauty, Utilities, Other)
  - Validate unit (must be one of: kg, g, liter, ml, piece, box, pack, other)
  - Validate prices/quantities (non-negative, numeric, proper type)
- [ ] T013 [P] Create UI utilities in backend/src/cli/ui_utils.py with functions for:
  - Display formatted tables (items list, bill preview)
  - Display searchable dropdown menus (for categories, units)
  - Display error/success messages
  - Format bill invoice output
- [ ] T014 Create error handling utilities in backend/src/cli/error_handler.py with custom exceptions and user-friendly error messages
- [ ] T015 [P] Configure logging in backend/src/services/database.py and backend/src/cli/main.py (print-based for console, structured for Phase 2)

### Database Initialization

- [ ] T016 Implement database initialization function in backend/src/db.py to create tables from schema.sql on first run if tables don't exist

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Store Owner Adds Products to Inventory (Priority: P1) 🎯 MVP

**Goal**: Users can add new products to inventory with name, category (searchable dropdown), unit (searchable dropdown), price, and stock quantity. System validates input and persists to PostgreSQL.

**Independent Test**: Add a product via console, verify it appears in "List all items", verify data in PostgreSQL database.

**Acceptance Criteria**:
- ✅ Searchable category dropdown (type "groc" → see "Grocery" → select)
- ✅ Searchable unit dropdown (type "k" → see "kg" → select)
- ✅ Validation rejects invalid categories/units (must select from predefined list)
- ✅ Validation rejects negative prices/stock, non-numeric input
- ✅ Item stored in PostgreSQL with all fields
- ✅ Success message displayed after add
- ✅ Item appears in "List all items" table

### Unit Tests for User Story 1 (TDD - Write FIRST, ensure FAIL before implementation)

- [ ] T017 [P] [US1] Unit test for category validation in tests/unit/test_validation.py (test valid categories pass, invalid fail)
- [ ] T018 [P] [US1] Unit test for unit validation in tests/unit/test_validation.py (test valid units pass, invalid fail)
- [ ] T019 [P] [US1] Unit test for price validation in tests/unit/test_validation.py (test non-negative, numeric, decimal)
- [ ] T020 [P] [US1] Unit test for stock quantity validation in tests/unit/test_validation.py (test non-negative, numeric, decimal)
- [ ] T021 [P] [US1] Unit test for Item model constraints in tests/unit/test_models.py (test model creation, required fields, unique constraint)

### Integration Tests for User Story 1 (TDD - Write FIRST, ensure FAIL before implementation)

- [ ] T022 [US1] Integration test for "add item" flow in tests/integration/test_inventory_flow.py:
  - Test: Create item via InventoryService.add_item() → verify stored in DB → retrieve via list() → verify all fields match
  - Test: Add item with valid category/unit → success
  - Test: Add item with invalid category → validation error, not stored
  - Test: Add item with invalid unit → validation error, not stored
  - Test: Add item with negative price → validation error, not stored
  - Test: Add item with negative stock → validation error, not stored

### Implementation for User Story 1

- [ ] T023 Create InventoryService in backend/src/services/inventory_service.py with methods:
  - `add_item(name, category, unit, unit_price, stock_qty)` → validates → inserts into DB → returns success/error
  - `list_items()` → queries items WHERE is_active=true ORDER BY name → returns list of Item objects
  - (Other methods added in US2, but structure prepared here)

- [ ] T024 [P] [US1] Create inventory_menu.py in backend/src/cli/inventory_menu.py with:
  - `display_add_item_menu()` → prompts for name, category (searchable dropdown), unit (searchable dropdown), price, stock
  - Input validation loop (re-prompt on invalid input in same context per FR-001a)
  - Call InventoryService.add_item() with validated input
  - Display success message with item details

- [ ] T025 [P] [US1] Create searchable_dropdown() function in backend/src/cli/ui_utils.py:
  - Takes list of options (e.g., ["Grocery", "Garments", "Beauty", "Utilities", "Other"])
  - Displays menu and accepts user input
  - Filters options as user types (partial match, case-insensitive)
  - Returns selected option or None if invalid

- [ ] T026 [P] [US1] Create format_items_table() function in backend/src/cli/ui_utils.py:
  - Takes list of Item objects
  - Formats as table: ID, Name, Category, Unit, Price, Stock
  - Prints to console with column alignment

- [ ] T027 [US1] Integrate "List all items" menu option in backend/src/cli/inventory_menu.py:
  - Call InventoryService.list_items()
  - Format with format_items_table() utility
  - Display to user

- [ ] T028 [US1] Implement error handling in InventoryService.add_item():
  - Catch database errors (FK constraint, unique constraint, etc.)
  - Return user-friendly error message (not stack trace)
  - Log error with context for debugging

- [ ] T029 [US1] Add logging to inventory operations in backend/src/services/inventory_service.py:
  - Log each add_item() call with user input, success/failure, timestamp

**Checkpoint**: User Story 1 complete and independently testable. Can demo "Add product and list items" workflow.

---

## Phase 4: User Story 2 - Store Owner Searches and Updates Product Stock (Priority: P1)

**Goal**: Users can search for products by partial name (case-insensitive), view details, and update price or stock quantity.

**Independent Test**: Add a product, search for it by partial name, update its price/stock, verify changes persist in database.

**Acceptance Criteria**:
- ✅ Search by partial name (e.g., "sug" finds "Sugar")
- ✅ Case-insensitive search (ILIKE in PostgreSQL)
- ✅ Search results display ID, Name, Category, Unit, Price, Stock
- ✅ Select item by ID → show current details
- ✅ Allow update of price (validate non-negative)
- ✅ Allow update of stock (validate non-negative, decimal allowed)
- ✅ Validate update input (reject negative, non-numeric)
- ✅ Update persisted to database
- ✅ Change immediately visible in list/search results

### Unit Tests for User Story 2 (TDD - Write FIRST, ensure FAIL before implementation)

- [ ] T030 [P] [US2] Unit test for Item model update in tests/unit/test_models.py (test price/stock update, constraints)

### Integration Tests for User Story 2 (TDD - Write FIRST, ensure FAIL before implementation)

- [ ] T031 [US2] Integration test for "search item" flow in tests/integration/test_inventory_flow.py:
  - Test: Search with partial name → returns all matching items
  - Test: Search is case-insensitive (ILIKE)
  - Test: Search returns empty if no match
  - Test: Select item from search → show details
  - Test: Update price → verify in DB and search results
  - Test: Update stock → verify in DB and search results
  - Test: Update with negative value → validation error, not applied

### Implementation for User Story 2

- [ ] T032 Extend InventoryService in backend/src/services/inventory_service.py with methods:
  - `search_items(query)` → queries items WHERE name ILIKE '%query%' AND is_active=true → returns list
  - `get_item(item_id)` → queries items WHERE id=item_id AND is_active=true → returns Item or None
  - `update_item(item_id, unit_price=None, stock_qty=None)` → validates → updates DB → returns success/error

- [ ] T033 [P] [US2] Create search_item_menu() in backend/src/cli/inventory_menu.py:
  - Prompt for search term
  - Call InventoryService.search_items()
  - Display results in formatted table with IDs
  - Prompt to select item by ID
  - Display current item details
  - Prompt to update price or stock (or both)

- [ ] T034 [P] [US2] Create item_detail_view() in backend/src/cli/ui_utils.py:
  - Display single item details (name, category, unit, price, stock, created_at, updated_at)
  - Display "Select action: Update price / Update stock / Back to search"

- [ ] T035 [US2] Implement update_item_menu() in backend/src/cli/inventory_menu.py:
  - Prompt user to select field to update (price or stock)
  - Get new value, validate
  - Call InventoryService.update_item()
  - Display success/error message
  - Show updated details

- [ ] T036 [US2] Add logging to search/update operations in backend/src/services/inventory_service.py

**Checkpoint**: User Stories 1 & 2 complete. Can demo full "Manage Inventory" workflow: add → list → search → update.

---

## Phase 5: User Story 3 - Salesperson Creates an Invoice for Customer (Priority: P1)

**Goal**: Users create invoices by searching for products, adding to cart, reviewing bill preview, confirming with optional customer/store names, then printing receipt and updating inventory atomically.

**Independent Test**: Create a bill with 2-3 items, verify totals calculated, verify inventory stock decremented, verify invoice printed.

**Acceptance Criteria**:
- ✅ Start bill creation from main menu
- ✅ Search for product and add to cart with quantity
- ✅ Validate stock availability (quantity ≤ stock_qty)
- ✅ Calculate line_total (unit_price × quantity) for each item
- ✅ Allow adding multiple items (or stopping to review)
- ✅ Display bill preview with items, unit prices, quantities, line totals, grand total
- ✅ Confirm or cancel bill before persisting
- ✅ Prompt for optional customer_name and store_name (user can press Enter to skip)
- ✅ Insert bill into DB, insert bill_items with snapshots, decrement inventory stock atomically
- ✅ Print formatted invoice to console (bill ID, date/time, customer/store, line items, grand total)
- ✅ All-or-nothing stock decrement (no partial updates if bill fails)

### Unit Tests for User Story 3 (TDD - Write FIRST, ensure FAIL before implementation)

- [ ] T037 [P] [US3] Unit test for Bill model in tests/unit/test_models.py (test model creation, foreign keys)
- [ ] T038 [P] [US3] Unit test for BillItem model in tests/unit/test_models.py (test model creation, snapshots)
- [ ] T039 [P] [US3] Unit test for line_total calculation in tests/unit/test_billing_service.py (test unit_price × quantity)

### Integration Tests for User Story 3 (TDD - Write FIRST, ensure FAIL before implementation)

- [ ] T040 [US3] Integration test for "create bill" flow in tests/integration/test_billing_flow.py:
  - Test: Search for item, add to cart with valid quantity → verify in cart
  - Test: Add item with quantity > stock → validation error, not added
  - Test: Add multiple items → verify all in cart
  - Test: Review bill preview → verify totals calculated correctly
  - Test: Confirm bill with customer/store names → verify in DB
  - Test: Confirm bill with empty customer/store names (press Enter) → verify NULL in DB
  - Test: Verify inventory stock decremented after bill (line_qty decremented from stock_qty)
  - Test: Verify all bill_items have snapshots of price/name
  - Test: Cancel bill before confirm → verify no changes to DB or inventory
  - Test: Bill creation with empty cart → validation error (at least 1 item required)

### Implementation for User Story 3

- [ ] T041 Create BillingService in backend/src/services/billing_service.py with methods:
  - `create_bill_draft()` → initialize in-memory cart (list)
  - `add_to_cart(item_id, quantity)` → validates stock → adds (item, quantity) tuple to cart → returns success/error
  - `get_cart()` → returns current cart
  - `clear_cart()` → empties cart
  - `calculate_bill_total(cart)` → sums line_totals → returns total
  - `confirm_bill(cart, customer_name=None, store_name=None)` → validates stock for all items → inserts Bill → inserts BillItems with snapshots → decrements inventory atomically → returns bill_id or error

- [ ] T042 [P] [US3] Implement billing_menu.py in backend/src/cli/billing_menu.py:
  - `display_create_bill_menu()` → main bill creation workflow
  - Loop: Search for item → select item → enter quantity → validate stock → add to cart
  - After adding item, ask "Add more items? (y/n)"
  - If no, show cart summary

- [ ] T043 [P] [US3] Create bill_preview() function in backend/src/cli/ui_utils.py:
  - Takes cart and calculated totals
  - Displays formatted table: Item Name, Unit, Qty, Unit Price, Line Total
  - Shows grand total at bottom
  - Prompts "Confirm bill? (y/n)"

- [ ] T044 [P] [US3] Create invoice_printer() function in backend/src/cli/ui_utils.py:
  - Takes Bill and list of BillItems
  - Displays formatted invoice:
    - Bill ID, Date/Time
    - Customer Name (if provided, else blank)
    - Store Name (if provided, else blank)
    - Line items table
    - Grand Total
    - Thank you message

- [ ] T045 [US3] Implement bill confirmation flow in backend/src/cli/billing_menu.py:
  - Show bill preview
  - Prompt "Confirm bill? (y/n)"
  - If yes: prompt for optional customer_name (press Enter to skip → None)
  - Prompt for optional store_name (press Enter to skip → None)
  - Call BillingService.confirm_bill()
  - On success: print invoice, clear cart, return to main menu
  - On error: show error message, ask to retry/cancel

- [ ] T046 [US3] Implement stock validation in BillingService.confirm_bill():
  - For each cart item: check current stock_qty ≥ quantity
  - If any fail validation: raise error, ROLLBACK transaction, do NOT insert bill
  - If all pass: proceed with INSERT and DECREMENT in single transaction

- [ ] T047 [US3] Implement atomic stock decrement in BillingService.confirm_bill():
  - Use PostgreSQL transaction (BEGIN/COMMIT)
  - Insert bill → insert all bill_items → decrement all inventory items → COMMIT
  - If any step fails: ROLLBACK entire operation
  - Do NOT allow partial updates (all-or-nothing)

- [ ] T048 [US3] Add logging to billing operations in backend/src/services/billing_service.py:
  - Log each bill creation with cart items, customer, store, total, inventory decrements

**Checkpoint**: All User Stories 1, 2, 3 complete. Full "Manage Inventory + Create Bill" workflow functional and independently testable.

---

## Phase 6: Main Menu & CLI Integration

**Purpose**: Integrate all user stories into main menu application loop

- [ ] T049 Create main.py in backend/src/cli/main.py with:
  - Main menu loop (Manage Inventory / Create New Bill / Exit)
  - Input validation (re-prompt on invalid in same context per FR-001a)
  - Route to inventory_menu.py or billing_menu.py
  - Handle exit gracefully

- [ ] T050 [P] Implement main_menu() function in backend/src/cli/main.py:
  - Display options (1. Manage Inventory, 2. Create New Bill, 3. Exit)
  - Prompt for selection
  - Validate input (1, 2, 3 only)
  - Route to appropriate submenu

- [ ] T051 [P] Extend inventory_menu.py with main inventory submenu:
  - Display options (1. Add new item, 2. List all items, 3. Search item by name, 4. Back to main menu)
  - Route to add/list/search workflows
  - Handle invalid input with re-prompt in same context

- [ ] T052 Create application entry point in backend/src/cli/main.py:
  - Initialize database (create tables if not exist)
  - Load environment variables (.env)
  - Start main menu loop
  - Handle database connection errors gracefully

**Checkpoint**: Integrated console application with all menus and workflows.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Testing, documentation, and final validation

### Unit Test Coverage

- [ ] T053 [P] Add remaining unit tests for edge cases in tests/unit/:
  - Empty cart validation
  - Zero price handling (allowed per spec)
  - Decimal quantity calculations
  - Special characters in item names/customer names
  - Very long names (truncation/validation)

### Integration Test Coverage

- [ ] T054 [P] Add end-to-end integration tests in tests/integration/test_e2e.py:
  - Full workflow: Add item → List → Search → Create bill → Verify invoice → Check inventory
  - Multiple users in sequence (cart isolation)
  - Database persistence across app restarts (add item, close app, reopen, verify item still there)

### Contract Tests (CLI Output)

- [ ] T055 [P] [US1] Contract test for add item menu output format in tests/contract/test_cli_output.py
- [ ] T056 [P] [US2] Contract test for search results table format in tests/contract/test_cli_output.py
- [ ] T057 [P] [US3] Contract test for invoice format in tests/contract/test_cli_output.py

### Code Quality & Coverage

- [ ] T058 [P] Run pytest with coverage: `pytest --cov=src tests/` → verify ≥80% coverage
- [ ] T059 [P] Fix any coverage gaps identified (add tests or code refactoring)
- [ ] T060 [P] Code formatting and linting (if using black/flake8)

### Documentation

- [ ] T061 Create/update README.md in backend/ with:
  - Project overview
  - Setup instructions (refer to quickstart.md)
  - How to run the app
  - How to run tests
  - Architecture overview (models, services, CLI structure)

- [ ] T062 [P] Add docstrings to all public functions in src/services/, src/cli/, src/models/
- [ ] T063 [P] Add inline comments to complex logic (stock validation, atomic transactions, dropdown filtering)

### Final Validation

- [ ] T064 Run quickstart.md validation manually:
  - Follow all steps in quickstart.md
  - Verify each workflow works (add → list → search → update → create bill)
  - Verify no console errors/stack traces
  - Verify data persists in PostgreSQL

- [ ] T065 Perform manual testing on edge cases from spec:
  - Test decimal quantities (e.g., 2.5 kg)
  - Test zero prices (allowed)
  - Test very large quantities
  - Test item deletion between search and cart add (item not found error)
  - Test database connection loss during bill creation (handled gracefully)

- [ ] T066 Verify all constitution principles are met:
  - ✅ Separation of Concerns: models, services, cli separated
  - ✅ TDD: 80%+ coverage, tests written first
  - ✅ Database-First: soft deletes, snapshots, atomic transactions
  - ✅ Simplicity: no premature abstraction, direct ORM queries
  - ✅ Observability: logging added to all operations
  - ✅ Local-First: .env for DATABASE_URL, no hardcoded secrets
  - ✅ Error Handling: graceful messages, no stack traces to user

**Checkpoint**: Phase 1 complete, tested, documented, and ready for Phase 2 FastAPI refactoring.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies → Start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 → BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 → Can start after Phase 2
- **Phase 4 (US2)**: Depends on Phase 2 → Can start after Phase 2 (parallel with US1 if staffed)
- **Phase 5 (US3)**: Depends on Phase 2 → Can start after Phase 2 (parallel with US1/US2 if staffed)
- **Phase 6 (Integration)**: Depends on Phase 3, 4, 5 → After all user stories
- **Phase 7 (Polish)**: Depends on all phases → Final phase

### User Story Dependencies

- **User Story 1** (Add Item): No dependencies on other stories; can start immediately after Phase 2
- **User Story 2** (Search/Update): No dependencies on other stories; can start immediately after Phase 2
- **User Story 3** (Create Bill): Requires US1 (items to sell); can start after Phase 2 with mock items or after US1 complete

### Within Each User Story

- Tests MUST be written FIRST and FAIL before implementation (Red phase)
- Models before services
- Services before CLI menus
- Core implementation before integration
- Each story complete and tested before moving to next

### Parallel Opportunities

#### Phase 1 Setup Tasks Parallelizable
- T004, T005, T007: Database config, packages, pytest fixtures (can run in parallel)
- Developer A: T001-T003, T006 (schema, database setup)
- Developer B: T004, T005, T007 (packages, fixtures)

#### Phase 2 Foundational Tasks Parallelizable
- T008-T011: All models can be created in parallel
- T012, T013: Validation service and UI utilities can be created in parallel
- Developer A: T008-T011 (models, schemas)
- Developer B: T012-T015 (validation, UI, error handling)
- Developer C: T016 (database initialization)

#### Phase 3-5 User Stories Can Run in Parallel
Once Phase 2 is complete, with multiple developers:
- Developer A: Phase 3 (US1 - Add Item)
- Developer B: Phase 4 (US2 - Search/Update)
- Developer C: Phase 5 (US3 - Create Bill) — after US1 items available or with mock data

#### Within User Story Tests & Models Parallelizable
- Tests [P] marked (T017-T021 for US1, T030 for US2, T037-T039 for US3): Write all tests in parallel
- Models [P] marked: Create models in parallel, then services depend on them

---

## Parallel Execution Examples

### Example 1: Single Developer (Sequential MVP Path)
```
1. Complete T001-T007 (Phase 1 Setup)
2. Complete T008-T016 (Phase 2 Foundational)
3. Complete T017-T029 (Phase 3 US1 - Add Item)
   ✓ Stop and validate US1 independently
4. Complete T030-T036 (Phase 4 US2 - Search/Update)
   ✓ Stop and validate US1+US2
5. Complete T037-T048 (Phase 5 US3 - Create Bill)
   ✓ Stop and validate all three stories
6. Complete T049-T052 (Phase 6 Integration)
7. Complete T053-T066 (Phase 7 Polish)
```

### Example 2: Two Developers (Setup + Parallel Stories)
```
Developer A + B together:
1. Complete T001-T007 (Phase 1 Setup)
2. Complete T008-T016 (Phase 2 Foundational)

Then split:
Developer A:
- T017-T021 tests for US1 (parallel with Dev B)
- T022 integration test for US1 (parallel with Dev B)
- T023-T029 implementation for US1

Developer B:
- T030 tests for US2 (parallel with Dev A)
- T031 integration test for US2 (parallel with Dev A)
- T032-T036 implementation for US2

After both finish:
- T037-T048 US3 (can be done by either, or split if 3 developers)
- T049-T052 Integration (both together or one developer)
- T053-T066 Polish (both together)
```

### Example 3: Parallel Phase 2 (Foundation Tasks)
```
Developer A:
- T008-T011 (Create models Item, Bill, BillItem, schemas)

Developer B:
- T012-T015 (Create validation service, UI utils, error handling, logging config)

Developer C:
- T016 (Database initialization)

Merge when complete, then proceed to Phase 3-5 in parallel.
```

---

## Implementation Strategy

### MVP First (Recommended for Phase 1)

1. **Complete Setup (Phase 1)**: T001-T007
   - Database schema ready, project structure set up

2. **Complete Foundation (Phase 2)**: T008-T016
   - All models, validation, utilities ready
   - **CRITICAL**: No user story work possible until this is done

3. **Complete User Story 1 Only (Phase 3)**: T017-T029
   - Add item + list item fully working
   - **STOP and VALIDATE**: Users can add and view products
   - Suitable for demo or early user feedback

4. **Optionally continue**:
   - Phase 4 (US2): Search/Update functionality
   - Phase 5 (US3): Billing/Invoice functionality
   - Phase 6: Main menu integration
   - Phase 7: Polish and testing

**Why MVP-first?**: Delivers working "Add Product" feature within shortest time; can gather feedback and iterate. Each additional user story adds value without breaking previous ones.

### Incremental Delivery (If User Stories Must Be Sequential)

1. Setup + Foundational (all phases 1-2)
2. **DEPLOY**: US1 only (Add/List items) — *Users can manage inventory*
3. Add US2 (Search/Update) — *More control over inventory*
4. Add US3 (Create Bill) — *Full POS system*
5. Polish and optimize

### Parallel Team Strategy (If 3+ Developers)

With 3 developers:

1. **All together**: Complete Setup (Phase 1) + Foundation (Phase 2)

2. **Split by user story** (after Phase 2):
   - Developer A: User Story 1 (Add Item) — Phases 3 + own tests
   - Developer B: User Story 2 (Search/Update) — Phase 4 + own tests
   - Developer C: User Story 3 (Create Bill) — Phase 5 + own tests

3. **Merge and integrate**: Phases 6-7 (can be done by one or all)

Each developer works independently on their story; integration happens at the end.

---

## TDD Workflow: Red-Green-Refactor

For each task, follow Constitution Principle II (Test-Driven Development):

### Red Phase
1. Write test(s) for the feature
2. Run test → **FAILS** (because feature not implemented)
3. Document what test expects

### Green Phase
4. Implement minimal code to make test PASS
5. Run test → **PASSES**
6. Don't over-engineer; keep it simple

### Refactor Phase
7. Refactor code for clarity/performance without breaking test
8. Run test → **STILL PASSES**
9. Commit when test passes

### Example: Adding an Item

```python
# RED: Write test first (tests/integration/test_inventory_flow.py)
def test_add_item_success():
    service = InventoryService(test_db)
    result = service.add_item("Sugar", "Grocery", "kg", 150, 100)
    assert result["success"] == True

    item = service.get_item_by_name("Sugar")
    assert item.name == "Sugar"
    assert item.category == "Grocery"
    assert item.stock_qty == 100

# Run: pytest tests/integration/test_inventory_flow.py::test_add_item_success
# Result: FAIL (InventoryService.add_item not implemented)

# GREEN: Implement minimal code
class InventoryService:
    def add_item(self, name, category, unit, unit_price, stock_qty):
        # Validate
        if not self.validate_category(category):
            return {"success": False, "error": "Invalid category"}

        # Create and save item
        item = Item(name=name, category=category, unit=unit,
                   unit_price=unit_price, stock_qty=stock_qty)
        self.session.add(item)
        self.session.commit()
        return {"success": True, "item_id": item.id}

# Run: pytest tests/integration/test_inventory_flow.py::test_add_item_success
# Result: PASS

# REFACTOR: Improve without breaking test
class InventoryService:
    def add_item(self, name, category, unit, unit_price, stock_qty):
        # Validate all inputs
        self._validate_add_item_input(name, category, unit, unit_price, stock_qty)

        # Create item
        item = self._create_item(name, category, unit, unit_price, stock_qty)

        # Persist
        self.session.add(item)
        self.session.commit()

        return {"success": True, "item_id": item.id}

# Run: pytest tests/integration/test_inventory_flow.py::test_add_item_success
# Result: STILL PASSES ✓ Commit!
```

---

## Checkpoints & Validation

Stop at each checkpoint to validate that the user story works independently:

### After Phase 3 (US1 - Add Item)
- [ ] Can add a product via console
- [ ] Product appears in "List all items"
- [ ] Data persists in PostgreSQL
- [ ] Validation rejects invalid input
- [ ] No crashes or stack traces

### After Phase 4 (US1 + US2 - Add + Search/Update)
- [ ] Can search for products by partial name
- [ ] Can update price/stock
- [ ] Changes visible immediately in list/search
- [ ] Previous add functionality still works

### After Phase 5 (US1 + US2 + US3 - Full workflow)
- [ ] Can create bill, add items, calculate totals
- [ ] Stock decremented after bill
- [ ] Invoice printed correctly
- [ ] Previous add/search functionality still works
- [ ] Data persists across app restarts

### After Phase 6 (Integrated menus)
- [ ] Main menu displays options (1, 2, 3)
- [ ] All submenus work (Manage Inventory, Create Bill)
- [ ] Can exit gracefully
- [ ] Input validation re-prompts on error

### After Phase 7 (Polish)
- [ ] 80%+ test coverage achieved
- [ ] All edge cases tested
- [ ] No console errors or warnings
- [ ] Documentation complete
- [ ] Constitution compliance verified

---

## Commit Strategy

Commit after each completed task or logical group. Example commits:

```
T001-T007: Create project structure and schema
T008-T011: Implement ORM models (Item, Bill, BillItem)
T012-T016: Create validation service and utilities
T017-T022: Add unit & integration tests for US1 (Red phase)
T023-T029: Implement add item functionality (Green + Refactor)
T030-T036: Implement search/update functionality (US2)
T037-T048: Implement billing functionality (US3)
T049-T052: Integrate main menu
T053-T066: Add tests and polish
```

Each commit should be small, focused, and passing tests.

---

## Notes

- **[P] tasks**: Different files, no dependencies → can run in parallel
- **[US#] label**: Maps task to specific user story for traceability
- **Tests FIRST**: Write tests before implementation (Red-Green-Refactor)
- **Independent stories**: Each story independently testable; can stop at any checkpoint
- **Atomic transactions**: Use PostgreSQL transactions for bill operations (all-or-nothing)
- **No hardcoded secrets**: Use .env for DATABASE_URL
- **Graceful errors**: User-friendly messages, never show stack traces
- **80%+ coverage**: Target for all code per Constitution Principle II

---

**Ready to begin? Start with Phase 1 (Setup) tasks.**

