# Feature Specification: FastMCP Server for Inventory & Billing

**Feature Branch**: `004-fastmcp-server-p4`
**Created**: 2025-12-08
**Status**: Draft
**Input**: User description: "Convert the logic of the existing FastAPI endpoints into the MCP server. Users should be able to add, update, or delete inventory, as well as create bills, retrieve all bills, and get a bill by its ID."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Admin Adds Inventory Item via MCP Tool (Priority: P1)

A store admin uses an MCP client (like Claude Code or a local agent) to add a new inventory item to the StoreLite system without interacting with the FastAPI web UI.

**Why this priority**: Adding inventory is a core operation and the foundation for all billing workflows. It must work via MCP tools so agents and local tools can access it directly.

**Independent Test**: Can be fully tested by calling the `inventory_add_item` MCP tool with item details, verifying the item is persisted in PostgreSQL, and confirming it appears in subsequent inventory queries.

**Acceptance Scenarios**:

1. **Given** an MCP client is connected to the StoreLite FastMCP server, **When** the client calls `inventory_add_item(name="Sugar", category="Grocery", unit="kg", unit_price=160, stock_qty=10)`, **Then** the item is created in the `items` table with all fields correctly stored.
2. **Given** an item already exists with the same name, **When** the admin adds another item with the same name but different category, **Then** both items are stored separately.
3. **Given** invalid input (e.g., negative price), **When** the admin calls `inventory_add_item`, **Then** the tool rejects it with a clear error message describing the validation failure.

---

### User Story 2 - Admin Updates Inventory Item via MCP Tool (Priority: P1)

A store admin updates an existing inventory item (price, stock quantity) via MCP tool without touching the web interface.

**Why this priority**: Price and stock updates are frequent operations; MCP accessibility ensures agents can assist with inventory maintenance.

**Independent Test**: Can be fully tested by calling `inventory_update_item` with an item ID and new values, verifying the database reflects the changes, and confirming queries return updated values.

**Acceptance Scenarios**:

1. **Given** an item exists in the inventory, **When** the admin calls `inventory_update_item(item_id=5, unit_price=180)`, **Then** the item's price is updated and the `updated_at` timestamp is refreshed.
2. **Given** an item exists, **When** the admin calls `inventory_update_item(item_id=5, stock_qty=25)`, **Then** the stock quantity is updated without modifying other fields.
3. **Given** an item ID that does not exist, **When** the admin calls `inventory_update_item(item_id=999, ...)`, **Then** the tool returns an error indicating the item was not found.

---

### User Story 3 - Admin Deletes Inventory Item via MCP Tool (Priority: P1)

A store admin deactivates an inventory item from the system via MCP tool by marking it inactive.

**Why this priority**: Item lifecycle management (including deactivation) is essential for a complete inventory system. MCP support ensures agents can manage the full lifecycle while preserving historical integrity.

**Independent Test**: Can be fully tested by calling `inventory_delete_item` with an item ID, verifying the item's `is_active` flag is set to `FALSE` in the database, and confirming it no longer appears in active inventory queries.

**Acceptance Scenarios**:

1. **Given** an item exists and is marked as active, **When** the admin calls `inventory_delete_item(item_id=5)`, **Then** the item's `is_active` flag is set to `FALSE` in the database.
2. **Given** an item is already inactive, **When** the admin tries to delete it again, **Then** the system returns an idempotent success message (succeeds without error).
3. **Given** an item is marked inactive, **When** a query lists all active items via `inventory_list_items()`, **Then** the deleted item does not appear in the results.

---

### User Story 4 - Agent Lists Inventory Items via MCP Tool (Priority: P1)

An AI agent or user queries the inventory to search or list items, with optional filters by name or category.

**Why this priority**: Listing and searching inventory is fundamental for both admin and billing workflows. Agents need this to provide inventory information and to validate items before creating bills.

**Independent Test**: Can be fully tested by calling `inventory_list_items` with various filter combinations, verifying the returned list matches expected items, and confirming pagination/limits are respected.

**Acceptance Scenarios**:

1. **Given** several items exist in the database, **When** the user calls `inventory_list_items()` with no filters, **Then** all active items are returned.
2. **Given** items with names containing "sugar" exist, **When** the user calls `inventory_list_items(name="sugar")`, **Then** only matching items are returned.
3. **Given** items in different categories exist, **When** the user calls `inventory_list_items(category="Grocery")`, **Then** only items in that category are returned.
4. **Given** a large number of items exist, **When** the user calls `inventory_list_items` with pagination parameters, **Then** results are paginated correctly.

---

### User Story 5 - Salesperson Creates a Bill via MCP Tool (Priority: P1)

A salesperson (or agent) creates a bill by selecting items and quantities via an MCP tool, without using the web form.

**Why this priority**: Billing is the second core workflow. MCP accessibility allows agents to automate bill creation based on natural language or API calls.

**Independent Test**: Can be fully tested by calling `billing_create_bill` with a list of item IDs and quantities, verifying the bill and bill_items are created in the database, inventory is decremented, and totals are calculated correctly.

**Acceptance Scenarios**:

1. **Given** items exist in inventory with sufficient stock, **When** the salesperson calls `billing_create_bill(customer_name="Ali", store_name="Store #1", items=[{item_id=1, quantity=2}, {item_id=3, quantity=1.5}])`, **Then** a new bill is created with correct line items and totals, and inventory stock is decremented.
2. **Given** an item has 5 kg in stock, **When** the salesperson tries to create a bill with 10 kg of that item, **Then** the system rejects the bill with an error indicating insufficient stock.
3. **Given** valid bill input, **When** the bill is created, **Then** the bill ID and all line items (including snapshots of prices at sale time) are stored in the database.
4. **Given** a bill is created, **When** the salesperson queries the inventory after, **Then** the stock quantities reflect the deduction from the bill.

---

### User Story 6 - User Retrieves All Bills via MCP Tool (Priority: P2)

A user (admin or reporting agent) retrieves a list of all bills created in the system for auditing or analysis.

**Why this priority**: Retrieving historical bills is important for reporting and auditing, but secondary to the core add/update/bill operations.

**Independent Test**: Can be fully tested by calling `billing_list_bills` and verifying all previously created bills are returned with correct metadata (date, customer, total).

**Acceptance Scenarios**:

1. **Given** several bills exist in the database, **When** the user calls `billing_list_bills()`, **Then** all bills are returned with headers (id, customer_name, total_amount, created_at).
2. **Given** bills created over multiple days exist, **When** the user calls `billing_list_bills(start_date=..., end_date=...)`, **Then** only bills within the date range are returned.
3. **Given** many bills exist, **When** the user calls `billing_list_bills` with pagination, **Then** results are paginated correctly.

---

### User Story 7 - User Retrieves a Specific Bill via MCP Tool (Priority: P1)

A user retrieves the full details of a specific bill (header + line items) to review or reprint an invoice.

**Why this priority**: Retrieving individual bills is essential for invoice printing and verification. Agents need this to provide bill details to users.

**Independent Test**: Can be fully tested by calling `billing_get_bill(bill_id=X)`, verifying the returned structure includes bill header and all associated line items with correct pricing and quantities.

**Acceptance Scenarios**:

1. **Given** a bill exists with ID 5, **When** the user calls `billing_get_bill(bill_id=5)`, **Then** the full bill (header + all line items) is returned.
2. **Given** a bill ID that does not exist, **When** the user calls `billing_get_bill(bill_id=999)`, **Then** the system returns an error indicating the bill was not found.
3. **Given** a bill exists, **When** the user calls `billing_get_bill`, **Then** all line items include the snapshot of item name, unit price, quantity, and line total at the time of sale.

---

### Edge Cases

- What happens when a user tries to add an item with missing required fields (e.g., no name)?
- How does the system handle concurrent updates to the same item's stock?
- What happens when a bill references an item that was deleted after the bill was created?
- How does the system handle very large inventory lists or bill retrieval with thousands of items?
- What happens if an MCP tool is called while the database connection is unavailable?

---

## Clarifications *(resolved during spec review)*

### Session 2025-12-08

- Q: Should `inventory_delete_item` use soft delete (mark inactive) or hard delete (remove from DB)? → A: Soft delete (set `is_active = FALSE`). Items remain in database for historical accuracy and to prevent orphaned bill references.
- Q: How should concurrent bill creation handle inventory over-allocation? → A: Pessimistic locking (row-level locks). Stock is locked during validation; if insufficient after locking, the bill is rejected atomically. Prevents race conditions and maintains accuracy.
- Q: What are the default and maximum page sizes for paginated responses? → A: Default page size 20, maximum 100. Tools accept optional `page` (1-indexed) and `limit` (1-100) parameters to control pagination.
- Q: Should bills be modifiable after creation, or immutable? → A: Immutable. Bills cannot be modified or deleted after creation (audit trail integrity). Corrections require cancellation and re-creation. No update/delete tools for bills.
- Q: What error response format should MCP tools use? → A: Structured JSON: `{"error": "<CODE>", "message": "<text>", "details": {...}}`. Error codes are screaming-snake-case (e.g., INSUFFICIENT_STOCK). Enables agent parsing while supporting human-readable messages.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose an `inventory_add_item` MCP tool that accepts name, category, unit, unit_price, and stock_qty and creates a new item in the `items` table.
- **FR-002**: System MUST expose an `inventory_update_item` MCP tool that accepts item_id and optional fields (unit_price, stock_qty, name, category) and updates the item in the database.
- **FR-003**: System MUST expose an `inventory_delete_item` MCP tool that accepts item_id and marks the item as inactive (sets `is_active = FALSE`) via soft delete. Deleted items remain in the database for historical accuracy but are excluded from all active inventory queries.
- **FR-004**: System MUST expose an `inventory_list_items` MCP tool that returns all active items with optional filters by name and category, and supports pagination. Default page size is 20 items; maximum page size is 100 items. Tool accepts optional `page` (1-indexed) and `limit` (1-100) parameters.
- **FR-005**: System MUST expose a `billing_create_bill` MCP tool that accepts customer_name, store_name, and an array of {item_id, quantity} objects, validates stock, creates a bill with line items, and decrements inventory.
- **FR-006**: System MUST expose a `billing_list_bills` MCP tool that returns all bills with optional date range filtering and pagination. Default page size is 20 bills; maximum page size is 100 bills. Tool accepts optional `page` (1-indexed), `limit` (1-100), `start_date`, and `end_date` parameters.
- **FR-007**: System MUST expose a `billing_get_bill` MCP tool that accepts a bill_id and returns the bill header plus all associated line items.
- **FR-008**: System MUST reuse existing service layer logic from FastAPI (e.g., services.inventory, services.billing) to ensure consistency between REST API and MCP tools.
- **FR-009**: System MUST validate all inputs (e.g., non-negative prices, valid item IDs, sufficient stock) and return errors in a standard JSON structure: `{"error": "<ERROR_CODE>", "message": "<human-readable message>", "details": {...}}`. Error codes are screaming-snake-case (e.g., INSUFFICIENT_STOCK, ITEM_NOT_FOUND, INVALID_PRICE). This allows agents to programmatically handle errors while humans read descriptive messages.
- **FR-010**: System MUST maintain transaction integrity and prevent inventory over-allocation via pessimistic locking (row-level locks) during bill creation. When multiple concurrent bills target the same items, stock is locked during validation and decremented atomically. If any item has insufficient stock after locking, the entire bill is rejected before any writes occur.
- **FR-011**: System MUST support both stdio (for local development and Claude Code) and HTTP (for agent runners) transports for the MCP server.
- **FR-012**: System MUST snapshot item name and unit_price at the time of bill creation in bill_items for historical accuracy.
- **FR-013**: System MUST treat bills as immutable once created. No updates or deletions are allowed on bill headers or line items. If corrections are needed, users must cancel the bill and create a new one. MCP tools do NOT expose update or delete operations for bills.

### Key Entities

- **Item (Inventory)**: Represents a product in the store. Attributes: id, name, category, unit, unit_price, stock_qty, is_active, created_at, updated_at. Relationships: referenced by bill_items.
- **Bill (Invoice Header)**: Represents a sales transaction. Attributes: id, customer_name, store_name, total_amount, created_at. Relationships: has many bill_items; references multiple items indirectly.
- **BillItem (Invoice Line Item)**: Represents a single line in a bill. Attributes: id, bill_id (FK), item_id (FK), item_name (snapshot), unit_price (snapshot), quantity, line_total. Relationships: belongs to bill and item.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 7 MCP tools are implemented and callable via stdio and HTTP transports without errors.
- **SC-002**: MCP tools correctly validate inputs and reject invalid data with descriptive error messages (e.g., negative prices, missing required fields).
- **SC-003**: Inventory operations (add, update, delete, list) correctly persist changes to PostgreSQL and reflect those changes in subsequent queries.
- **SC-004**: Bill creation correctly calculates totals, decrements inventory, and stores snapshots of item prices at the time of sale.
- **SC-005**: Bill retrieval returns complete bill data including all line items with correct pricing and quantities.
- **SC-006**: MCP tools handle concurrent requests without data corruption or lost updates (transaction integrity).
- **SC-007**: All MCP tool responses follow a consistent JSON schema that can be easily consumed by downstream agents and clients.
- **SC-008**: MCP server can be started, accepts tool calls, and returns responses within 500ms for typical operations.
- **SC-009**: All existing FastAPI REST endpoints continue to work and return identical results to MCP tools for the same operations (consistency).
- **SC-010**: All error responses from MCP tools follow the standard JSON error schema with `error` (screaming-snake-case code), `message` (human-readable text), and optional `details` object. No tool returns plain text or unstructured errors.

---

## Assumptions

1. The existing FastAPI backend (Phase 2) and PostgreSQL database are fully functional and stable.
2. Service layer logic (services.inventory, services.billing) can be reused or refactored into MCP tools without significant changes.
3. MCP transports (stdio and HTTP) are supported by the FastMCP library and can be configured with minimal setup.
4. Users have a basic understanding of MCP concepts (tools, resources, transports) but may not be expert developers.
5. The initial phase focuses on local MCP (stdio and localhost HTTP); no external/hosted MCP integration is required.
6. Inventory items are uniquely identified by ID; duplicate names in different categories are allowed.
7. Bill creation should use soft delete for items (is_active = FALSE) rather than hard delete, to preserve historical integrity.

---

## Out of Scope

- OpenAI Hosted MCP integration (Phase 5 consideration).
- MCP resources (e.g., exposing inventory/bills as queryable resources); only tools are in scope.
- Custom MCP prompts or system instructions; focus on tool functionality.
- Frontend UI integration; this phase is backend API exposure only.
- Real-time inventory sync or multi-store distributed logic; single-store/database scope.
- Advanced error recovery or retry logic beyond basic validation.

---

## Acceptance Checklist

- [ ] FastMCP server project structure is created with separate modules for inventory and billing tools.
- [ ] All 7 MCP tools are implemented and pass unit tests.
- [ ] Service layer is refactored (if needed) to be reusable by both FastAPI and MCP.
- [ ] stdio and HTTP transports are configured and tested.
- [ ] All tool inputs are validated with clear error messages.
- [ ] Integration tests verify tools work end-to-end with PostgreSQL.
- [ ] Documentation explains how to start the MCP server and call tools.
- [ ] Consistency tests confirm FastAPI endpoints and MCP tools return identical results.
