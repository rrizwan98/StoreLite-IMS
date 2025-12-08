# Feature Specification: Console-Based Inventory & Billing System (Phases 1-7)

**Feature Branch**: `001-console-ims-p1`
**Created**: 2025-12-07
**Status**: Complete (Phases 1-7)
**Input**: Console-based Python inventory and billing system with PostgreSQL backend. Database URL configured in .env file. Python 3.12+.

## Phase Overview

- **Phase 1 (Completed)**: Core inventory (add, list, search, update) and basic billing
- **Phase 2 (Planned)**: REST API endpoints for inventory and billing operations
- **Phase 3 (Planned)**: Next.js frontend for web-based access
- **Phase 4 (Completed)**: Search enhancements (category, price range) and soft-delete operations
- **Phase 5 (Completed)**: Advanced billing with shopping cart management and itemized display
- **Phase 6 (Completed)**: Main menu with system statistics and enhanced UI formatting
- **Phase 7 (Completed)**: End-to-end workflow testing, contract tests, and professional receipt formatting

## Clarifications

### Session 2025-12-07

- Q: How should users select/enter categories during item creation? → A: Searchable dropdown with predefined categories (Grocery, Garments, Beauty, Utilities, Other). As user types, matching categories are suggested. User can only select from the filtered list; custom/non-existent categories are rejected. This prevents data entry errors and ensures data consistency.

- Q: How should users select/enter units (kg, liter, piece, etc.) during item creation? → A: Searchable dropdown with predefined units (kg, g, liter, ml, piece, box, pack, other). As user types, matching units are suggested. User can only select from the list; attempting to enter custom units must be rejected. This ensures consistency with categories and prevents inventory data quality issues.

- Q: When should customer_name be prompted during bill creation (required, optional, or not at all)? → A: Optional; system prompts user for customer_name during bill creation, but user can press Enter/skip to leave it blank. This allows tracking known customers while respecting privacy for cash sales and walk-in customers.

- Q: How should invalid menu selections be handled (re-prompt, return to main, silent ignore, or crash)? → A: Re-prompt with error message in the same menu context. Invalid input shows "Invalid choice. Please select from the menu above." and loops back to the current menu. This maintains user context and prevents frustration from restarting workflows.

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

### User Story 1 - Store Owner Adds Products to Inventory (Priority: P1)

A store owner needs to add new products to the inventory system via a simple console menu. They provide product details (name, category, unit, price, quantity) and the system saves it to PostgreSQL.

**Why this priority**: Core business requirement. Without the ability to add products, the entire system has no data to work with. This is the foundation of all other operations.

**Independent Test**: Can fully test by running the app, navigating to "Manage Inventory" → "Add new item", entering product data, and verifying it's saved in PostgreSQL and can be listed. Delivers immediate value: a populated inventory.

**Acceptance Scenarios**:

1. **Given** the app is running and user is in Manage Inventory menu, **When** user selects "Add new item" and enters name="Sugar", searches for category by typing "groc" (sees "Grocery" in suggestions), selects it, searches for unit by typing "k" (sees "kg" in suggestions), selects it, unit_price=150, stock_qty=100, **Then** the item is inserted into the `items` table and a success message is displayed.

1b. **Given** user is adding a new item and types a category or unit that doesn't exist (e.g., category="Electronic" or unit="tons"), **When** they attempt to confirm, **Then** the system shows a validation error requiring them to select from the predefined list.

2. **Given** user enters invalid data (unit_price=-5 or stock_qty="abc"), **When** submitting, **Then** the system shows a validation error and asks for re-entry without saving.

3. **Given** user successfully adds an item, **When** they select "List all items", **Then** the newly added item appears in the table.

---

### User Story 2 - Store Owner Searches and Updates Product Stock (Priority: P1)

Store owner needs to find products by name and update their price or stock quantity (e.g., receive new stock, adjust pricing).

**Why this priority**: Essential operational task. Stock levels must be accurate for billing operations. Price updates are frequent in retail.

**Independent Test**: Can fully test by adding a product, then searching for it, updating its price/stock, and verifying the changes persist in the database. Delivers immediate value: keep inventory accurate.

**Acceptance Scenarios**:

1. **Given** items exist in inventory, **When** user selects "Search item by name" and enters "sug", **Then** the system returns all items with names containing "sug" (case-insensitive).

2. **Given** a search returns results, **When** user selects one by item ID, **Then** the system shows current details and allows updating price/stock.

3. **Given** user updates stock_qty from 100 to 150, **When** confirming, **Then** the database is updated and the change is immediately visible in list/search results.

4. **Given** user tries to update an item to negative stock, **When** submitting, **Then** validation prevents the update and shows an error.

---

### User Story 3 - Salesperson Creates an Invoice for Customer (Priority: P1)

A salesperson creates an invoice by searching for products, selecting quantities, reviewing the bill summary, and confirming. The system calculates totals, validates stock, and saves the bill with updated inventory.

**Why this priority**: Core transactional requirement. This is the revenue-generating operation. Without billing, there's no income recording.

**Independent Test**: Can fully test by creating a bill with 2-3 items, confirming it saves correctly with totals calculated, and verifying inventory stock is decremented. Delivers immediate value: complete sale-to-inventory-update workflow.

**Acceptance Scenarios**:

1. **Given** the main menu is showing, **When** user selects "Create New Bill", **Then** the system starts an in-memory cart and prompts to search for items.

2. **Given** user searches for "sugar" and gets 3 results, **When** they select item ID 1 and enter quantity=2, **Then** the system checks if stock is ≥2, calculates line_total (price × 2), and adds it to cart.

3. **Given** user enters quantity exceeding available stock (e.g., stock=10, quantity=15), **When** submitting, **Then** the system warns "Insufficient stock" and prompts to re-enter.

4. **Given** user has added 2 items to cart, **When** they choose "Finish adding items", **Then** the system shows a bill preview with all items, unit prices, quantities, line totals, and grand total.

5. **Given** bill preview is shown, **When** user confirms (y/n), **Then**: System prompts for optional customer_name (user can press Enter to skip), prompts for optional store_name (user can press Enter to skip), then inserts bill into `bills` table, inserts each cart item into `bill_items` with snapshots of price/name, decrements inventory stock for each item, and prints invoice to console.

5b. **Given** user is asked for customer_name during bill confirmation, **When** they press Enter (no input), **Then** the bill is saved with customer_name as NULL, allowing tracking of anonymous customers.

6. **Given** bill is created, **When** invoice prints, **Then** it shows: bill ID, date/time, customer name (if provided, otherwise blank), store name (if provided, otherwise blank), line items (name, unit, qty, unit_price, line_total), and grand total.

---

### Edge Cases

- What happens if user selects an item that was deleted between search and adding to cart? (Should validate item still exists and is active before adding to bill)
- How does the system handle decimal quantities (e.g., 2.5 kg of flour)? (Accepted; stored as NUMERIC(12,3))
- What if the database connection is lost during bill confirmation? (User is informed; partial bill not saved)
- Can a user create a bill with zero items? (No; system should require at least one item before confirming)
- What if unit_price is 0? (Allowed; system should not reject, as some stores may have free items)
- What if user types a category name that partially matches (e.g., "groc" matching "Grocery")? (Suggestions shown; user must select exact match from dropdown, not free-form entry allowed)
- What if user types a unit name that partially matches (e.g., "ki" matching "kg")? (Suggestions shown; user must select exact match from dropdown, not free-form entry allowed)

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST display a main menu with options: "Manage Inventory", "Create New Bill", "Exit"

- **FR-001a**: System MUST validate all menu selections and re-prompt with "Invalid choice. Please select from the menu above." if user enters an invalid option. The system MUST remain in the current menu context (not return to main menu) until valid input is received.

- **FR-002**: System MUST allow users to add items to inventory with fields: name (required), category (required, selected from predefined list), unit (required), unit_price (required, ≥0), stock_qty (required, ≥0)

- **FR-002a**: System MUST provide a searchable category dropdown during item creation with predefined categories (Grocery, Garments, Beauty, Utilities, Other). As user types, matching categories are suggested. User can only select from the list; attempting to confirm with a non-existent category must show a validation error.

- **FR-002b**: System MUST provide a searchable unit dropdown during item creation with predefined units (kg, g, liter, ml, piece, box, pack, other). As user types, matching units are suggested. User can only select from the list; attempting to confirm with a non-existent unit must show a validation error.

- **FR-003**: System MUST validate all item input fields before saving to database

- **FR-004**: System MUST list all active items in a formatted table showing: ID, Name, Category, Unit, Price, Stock (ordered by name)

- **FR-005**: System MUST support case-insensitive search for items by name (using ILIKE pattern matching)

- **FR-006**: System MUST allow users to update an item's price and/or stock quantity without changing the item ID

- **FR-007**: System MUST prevent invalid data updates (negative prices/stock) through validation

- **FR-008**: System MUST support creating a bill by searching items and adding them to an in-memory cart with quantities

- **FR-009**: System MUST validate stock availability before allowing an item to be added to bill (quantity ≤ current stock_qty)

- **FR-010**: System MUST calculate line totals (unit_price × quantity) and grand total (sum of all line totals) automatically

- **FR-011**: System MUST show a bill preview with all line items, quantities, prices, line totals, and grand total before confirmation

- **FR-012**: System MUST allow user to confirm or cancel bill creation before persisting to database

- **FR-012a**: System MUST prompt user for optional customer_name and store_name after bill confirmation. User can press Enter to skip either field, leaving it NULL in the database.

- **FR-013**: System MUST insert bill into `bills` table and each line item into `bill_items` table with price/name snapshots on confirmation

- **FR-014**: System MUST atomically decrement inventory stock for each sold item (all items decremented or none, no partial updates)

- **FR-015**: System MUST print a formatted invoice to console showing: bill ID, date/time, customer name (if provided), store name (if provided), line items, and grand total

- **FR-016**: System MUST support optional customer_name and store_name fields for bills (nullable in database)

- **FR-017**: System MUST establish connection to PostgreSQL using DATABASE_URL from environment variables

- **FR-018**: System MUST create all required tables on first run if they don't exist (items, bills, bill_items)

### Phase 4 Functional Requirements (Search Enhancements & Soft-Delete)

- **FR-019**: System MUST support searching items by category with case-insensitive matching
- **FR-020**: System MUST support searching items by price range (min and max) with Decimal validation
- **FR-021**: System MUST support soft-delete of items (marking as is_active=FALSE) instead of physical deletion
- **FR-022**: System MUST exclude inactive items from all search results, list displays, and billing operations
- **FR-023**: System MUST preserve historical data of deleted items for billing/audit purposes (no physical deletion)
- **FR-024**: System MUST display appropriate confirmation warnings when soft-deleting items

### Phase 5 Functional Requirements (Shopping Cart Management)

- **FR-025**: System MUST support in-memory shopping cart with add, view, update quantity, and remove operations
- **FR-026**: System MUST validate stock availability during cart operations (prevent adding more than available)
- **FR-027**: System MUST calculate line totals (quantity × unit_price) and cart total automatically
- **FR-028**: System MUST display itemized cart view showing item name, unit price, quantity, and line total
- **FR-029**: System MUST allow updating item quantities in cart with real-time stock validation
- **FR-030**: System MUST allow removing items from cart before bill confirmation
- **FR-031**: System MUST prevent bill confirmation with an empty cart (require at least one item)

### Phase 6 Functional Requirements (Main Menu & System Statistics)

- **FR-032**: System MUST display enhanced main menu with category headers and system statistics
- **FR-033**: System MUST show count of active items in inventory on main menu
- **FR-034**: System MUST format menu output for clarity with improved spacing and visual hierarchy

### Phase 7 Functional Requirements (Receipt Formatting & Testing)

- **FR-035**: System MUST display professional receipt format on bill confirmation with:
  - Bill ID and timestamp
  - Customer name and store name (if provided)
  - Itemized list showing: item name, quantity, unit price, and line total
  - Grand total amount
- **FR-036**: System MUST pass end-to-end workflow tests covering complete user journeys
- **FR-037**: System MUST pass contract tests validating CLI output format consistency

### Key Entities *(include if feature involves data)*

- **Item**: Represents a product in inventory. Attributes: id (auto), name (text), category (text), unit (text), unit_price (decimal), stock_qty (decimal), is_active (boolean), created_at (timestamp), updated_at (timestamp)

- **Bill**: Represents a sales invoice header. Attributes: id (auto), customer_name (text, optional), store_name (text, optional), total_amount (decimal), created_at (timestamp)

- **BillItem**: Represents a line item in a bill (many-to-one with Bill, many-to-one with Item). Attributes: id (auto), bill_id (FK), item_id (FK), item_name (text snapshot), unit_price (decimal snapshot), quantity (decimal), line_total (decimal)

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Users can complete adding a product and see it listed within 30 seconds (from start of "Add new item" to verified in "List all items")

- **SC-002**: Users can search for a product by partial name and get results in under 2 seconds for an inventory of 1000+ items

- **SC-003**: Users can create a complete bill (search, add 3 items, confirm) in under 5 minutes (with reasonable typing speed)

- **SC-004**: All inventory stock decrements happen atomically — no partial updates if bill creation fails

- **SC-005**: Console interface is clear and user-friendly with descriptive prompts (no cryptic error messages; all validation errors explain what went wrong and how to fix it)

- **SC-006**: PostgreSQL data persists across app restarts (all added items and bills remain in database)

- **SC-007**: 100% of valid inventory operations (add, list, search, update) succeed without crashing

- **SC-008**: 100% of valid bill operations (create, calculate, confirm) succeed without data loss or corruption

- **SC-009**: Invalid input is caught and rejected before reaching the database (all validation happens in application layer)

- **SC-010**: System handles database errors gracefully with user-friendly messages instead of stack traces

---

## Assumptions

- **Database Access**: User has already configured `DATABASE_URL` environment variable pointing to a Neon PostgreSQL instance (or any PostgreSQL 12+). The format is: `postgresql://user:password@host/dbname`

- **Python Version**: Python 3.12+ is installed and available as `python` or `python3` in the environment

- **No Authentication**: Phase 1 is single-user (console-based); no user authentication or multi-user support required

- **Simple UI**: Console-based only; no GUI required. User interaction via standard input/output (print statements and input() calls)

- **No Persistence of Cart**: Cart exists only in memory during a session. If the app crashes before confirming a bill, the cart is lost (acceptable for Phase 1)

- **Stock Deduction**: Stock is decremented immediately upon bill confirmation; no "pending" or "reserved" stock concept in Phase 1

- **Concurrency**: Single-user/single-session assumption; no concurrent access to the database from multiple app instances (acceptable for Phase 1)

- **Invoice Output**: Invoice is printed to console; optional file write (e.g., .txt) is nice-to-have but not required

- **No Discount/Tax**: Phase 1 focuses on basic billing; discount and tax fields are skipped (mentioned as "later" in requirements)

---

## Out of Scope (Phase 1)

- Multi-user authentication and authorization
- Graphical user interface (GUI)
- Web API or REST endpoints (Phase 2)
- Next.js frontend (Phase 3)
- MCP server integration (Phase 4)
- AI agent integration (Phase 5)
- Discount, tax, or promotional pricing
- Invoice PDF export (console output only)
- Bulk import of products
- Sales reporting and analytics
- Multiple store/location support (Phase 1 has optional store_name field but no per-store stock isolation)
- Barcode scanning
- Payment processing

---

## Technical Constraints

- **Database**: Must use PostgreSQL (Neon or self-hosted), not SQLite
- **Language**: Python 3.12+
- **Database Library**: psycopg2 OR SQLAlchemy ORM (user choice, abstracted via db.py)
- **No External UI Frameworks**: Console UI only (no Tkinter, PyQt, etc. in Phase 1)
- **Environment Configuration**: DATABASE_URL must be read from .env file or environment variable
- **Directory Structure**: Follow the suggested structure: main.py, db.py, inventory.py, billing.py, schema.sql (optional)

---

## Acceptance Criteria Summary

✅ All three user stories (Add Products, Search/Update, Create Bill) are independently testable and complete
✅ All inventory operations are validated and persisted to PostgreSQL
✅ Bill creation validates stock, calculates totals, updates inventory atomically, and prints receipt
✅ Console UI is clear with helpful error messages
✅ No implementation details leak into spec (no mention of psycopg2 vs SQLAlchemy specifics in user-facing behavior)
✅ All edge cases are identified
