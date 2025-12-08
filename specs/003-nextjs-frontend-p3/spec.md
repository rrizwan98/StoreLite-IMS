# Feature Specification: Next.js Frontend UI (Phase 3) - StoreLite IMS

**Feature Branch**: `003-nextjs-frontend-p3`
**Created**: 2025-12-08
**Status**: Draft
**Input**: Build Next.js frontend UI with admin inventory management and POS billing pages, connecting to FastAPI backend endpoints, ensuring perfect integration and seamless user workflows.

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

### User Story 1 - Store Admin: Add New Inventory Item (Priority: P1)

As a store admin, I want to add new products to the inventory through a web form on the Admin page so that the inventory system stays up-to-date with available products.

**Why this priority**: P1 - Foundational feature. Without the ability to add items via the UI, the entire inventory system is unusable. This is the first critical workflow for admin users.

**Independent Test**: Can be fully tested by navigating to `/admin`, filling out the "Add Item" form with all required fields, submitting it, and verifying the item appears in the inventory list without page refresh.

**Acceptance Scenarios**:

1. **Given** I'm on the `/admin` page, **When** I fill the "Add Item" form with name, category, unit, unit_price, and stock_qty, then click "Add Item", **Then** the form clears, a success message appears briefly, and the new item appears in the inventory table below
2. **Given** I leave a required field empty in the form, **When** I click "Add Item", **Then** the form shows a validation error message next to the empty field without submitting
3. **Given** I enter negative values for price or stock, **When** I click "Add Item", **Then** the form shows validation error preventing submission
4. **Given** the API call to add an item fails, **When** I submit the form, **Then** an error message appears asking me to try again
5. **Given** I add the same item name twice, **When** I submit both, **Then** both items are added (duplicates allowed as per business logic)

---

### User Story 2 - Store Admin: View and Search Inventory (Priority: P1)

As a store admin, I want to view all products in a searchable table and filter by name/category so that I can manage and understand current inventory levels.

**Why this priority**: P1 - Core management feature. Admins need visibility into inventory at all times to make informed decisions.

**Independent Test**: Can be fully tested by verifying the inventory table loads on `/admin` page, displays items from API, and filters work by typing in search/category fields.

**Acceptance Scenarios**:

1. **Given** I navigate to the `/admin` page, **When** the page loads, **Then** I see a table of all inventory items with columns: Name, Category, Unit, Price, Stock, and Actions
2. **Given** items exist in the database, **When** I search for "sugar" in the name search field, **Then** the table updates to show only items matching "sugar" (case-insensitive)
3. **Given** items exist with different categories, **When** I select "grocery" from the category dropdown, **Then** the table filters to show only grocery items
4. **Given** I apply both name and category filters, **When** I search, **Then** the table shows items matching both criteria (AND logic)
5. **Given** no items match my search, **When** I search, **Then** the table shows an empty state message "No items found"
6. **Given** the page is loading items from API, **When** the page first renders, **Then** a loading spinner appears until items are fetched
7. **Given** the API call to fetch items fails, **When** the page loads, **Then** an error message appears with a "Retry" button

---

### User Story 3 - Store Admin: Update Item Price and Stock (Priority: P1)

As a store admin, I want to click on an item in the inventory list and update its price or stock quantity so that I can keep inventory data current without adding duplicate items.

**Why this priority**: P1 - Critical for day-to-day inventory management. Stock adjustments happen frequently.

**Independent Test**: Can be fully tested by clicking an item's edit button, modifying price/stock, saving, and verifying the update appears in the list and is persisted in the database.

**Acceptance Scenarios**:

1. **Given** I see an item in the inventory table, **When** I click the "Edit" button on that row, **Then** a modal/form appears pre-filled with the item's current data (name, price, stock)
2. **Given** the edit form is open, **When** I change the unit_price to a new value and click "Save", **Then** the item updates in the table and the modal closes with a success message
3. **Given** the edit form is open, **When** I change the stock_qty and click "Save", **Then** the stock updates in the table
4. **Given** I try to save with negative price or stock, **When** I click "Save", **Then** validation errors appear on those fields without submitting
5. **Given** I change my mind while editing, **When** I click "Cancel", **Then** the modal closes without saving any changes
6. **Given** I save an update and the API fails, **When** the save completes, **Then** an error message appears allowing me to retry

---

### User Story 4 - Salesperson: Search and Add Items to Bill (Priority: P1)

As a salesperson, I want to search for items on the POS page and quickly add them to a bill so that I can efficiently process customer purchases.

**Why this priority**: P1 - Core POS functionality. Without this, the billing system cannot function. This is the salesperson's primary workflow.

**Independent Test**: Can be fully tested by navigating to `/pos`, using the search box to find an item, selecting it, and seeing it appear in the cart/bill summary.

**Acceptance Scenarios**:

1. **Given** I'm on the `/pos` page, **When** I type "sugar" in the search box, **Then** a dropdown/list of matching items appears below showing name, price, and stock
2. **Given** matching items are shown in the search dropdown, **When** I click on one item, **Then** that item is added to the current bill with quantity 1 and appears in the "Bill Items" section
3. **Given** an item is already in the bill, **When** I click on the same item in search, **Then** the quantity for that item increases by 1 (or I see an option to increase quantity)
4. **Given** I search for a product with no matches, **When** I type a non-existent product name, **Then** the dropdown shows "No items found"
5. **Given** an item has low stock (less than quantity requested), **When** I try to add more than available stock, **Then** the system shows a warning that only X units are available and prevents over-ordering

---

### User Story 5 - Salesperson: Adjust Item Quantity and Remove Items (Priority: P1)

As a salesperson, I want to adjust quantities of items in the bill and remove items I added by mistake so that I can correct the bill before checkout.

**Why this priority**: P1 - Essential for POS workflow. Users need to fix mistakes easily.

**Independent Test**: Can be fully tested by adding items to a bill, adjusting quantity in the cart table, and seeing line totals update correctly.

**Acceptance Scenarios**:

1. **Given** I have items in the bill, **When** I see the Bill Items table, **Then** each row has a quantity field that I can edit
2. **Given** I modify a quantity field and click elsewhere or press Enter, **When** the change is confirmed, **Then** the line total updates to reflect new quantity
3. **Given** I want to remove an item from the bill, **When** I click the "Delete" or "Remove" button on a row, **Then** that item is removed and the bill total updates
4. **Given** I set quantity to 0, **When** I confirm the change, **Then** the item is removed from the bill
5. **Given** I try to set quantity higher than available stock, **When** I try to save, **Then** a warning appears showing available stock and prevents invalid quantity

---

### User Story 6 - Salesperson: View and Confirm Bill Total (Priority: P1)

As a salesperson, I want to see a running total of the bill as I add items and confirm the total before generating the invoice so that I can verify accuracy before finalizing.

**Why this priority**: P1 - Critical for transaction accuracy. Customers trust the total shown before paying.

**Independent Test**: Can be fully tested by adding items to a bill and verifying the subtotal and total calculate correctly (sum of line items).

**Acceptance Scenarios**:

1. **Given** I add items to a bill, **When** the Bill Items section is visible, **Then** a summary box at the bottom shows: Subtotal, and Grand Total
2. **Given** I have 3 items in the bill, **When** I look at the summary, **Then** the subtotal is the sum of all line totals calculated correctly
3. **Given** I modify a quantity, **When** the change is saved, **Then** the subtotal and grand total update immediately
4. **Given** I remove an item from the bill, **When** the item is deleted, **Then** the subtotal and grand total update correctly
5. **Given** I have no items in the bill, **When** the bill is empty, **Then** the total shows 0 or "No items yet"

---

### User Story 7 - Salesperson: Create and Print Invoice (Priority: P1)

As a salesperson, I want to click a "Generate Bill" button and see a printable invoice showing all items, quantities, prices, and the final total so that I can provide a receipt to the customer.

**Why this priority**: P1 - Closing workflow. Without invoice generation, the sale process is incomplete.

**Independent Test**: Can be fully tested by adding items to a bill, clicking "Generate Bill", and seeing a formatted invoice appear (with print button or capability).

**Acceptance Scenarios**:

1. **Given** I have items in the bill and the total is ready, **When** I click "Generate Bill", **Then** the system sends the bill data to the API to create a bill record
2. **Given** the API successfully creates a bill, **When** the response returns, **Then** an invoice view appears showing: Store name, Date/Time, all line items with name, qty, unit price, line total, and Grand Total
3. **Given** the invoice is displayed, **When** I click "Print" or press Ctrl+P, **Then** the browser print dialog opens and the invoice is formatted for receipt paper
4. **Given** the API call to create a bill fails (insufficient stock, invalid data), **When** the generation completes, **Then** an error message appears explaining the issue and suggesting corrections
5. **Given** a bill is successfully created, **When** the invoice is generated, **Then** the bill is saved in the database with a unique Bill ID that is displayed on the invoice
6. **Given** I generate a bill, **When** the bill is created, **Then** the inventory stock quantities are automatically reduced by the quantities sold

---

### User Story 8 - Salesperson: Start New Bill After Invoice (Priority: P2)

As a salesperson, I want to clear the current bill and start a fresh one after printing an invoice so that I can serve the next customer without manual clearing.

**Why this priority**: P2 - Workflow convenience. Essential for efficient POS operation but can be handled with a "New Bill" button.

**Independent Test**: Can be fully tested by generating a bill, then clicking "New Bill" or "Clear" and verifying the cart empties and search is ready for next customer.

**Acceptance Scenarios**:

1. **Given** I've just generated and viewed an invoice, **When** I click "New Bill" or "Clear Bill" button, **Then** the bill items table clears, the total resets to 0, and the search box is ready for the next customer
2. **Given** the bill is cleared, **When** I search for a new item, **Then** I can immediately add items for the next customer

---

### Edge Cases

- What happens if the FastAPI backend is temporarily unavailable when the user tries to add an item or create a bill?
- What if an item's stock changes in the database while a salesperson is viewing the POS page (concurrent access)?
- What if the user tries to add an item with fractional units (e.g., 2.5 kg) when the system only allows whole numbers?
- How does the UI handle very long item names that overflow the table columns?
- What if a user refreshes the page or closes the browser while editing a bill (before generating)?

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: The frontend MUST be built using Next.js 14+ (App Router) with TypeScript for type safety.
- **FR-002**: The Admin page (`/admin`) MUST display a form to add new inventory items with fields: Name, Category (dropdown), Unit, Unit Price, Stock Quantity.
- **FR-003**: The Admin page MUST display an inventory table showing all active items with columns: Name, Category, Unit, Price, Stock, and Actions (Edit/Delete buttons).
- **FR-004**: The Admin page MUST support filtering/searching items by Name (substring match, case-insensitive) and Category (exact match).
- **FR-005**: The Admin page MUST allow clicking an "Edit" button to open a modal/form to update an item's price, stock, and optionally name/category.
- **FR-006**: The POS page (`/pos`) MUST have a search box that queries items by name (substring match) and displays matching items in a dropdown.
- **FR-007**: The POS page MUST allow selecting an item from the search dropdown to add it to the current bill with quantity 1.
- **FR-008**: The POS page MUST display a "Bill Items" table showing all items in the current bill with columns: Item Name, Unit, Quantity (editable), Unit Price, Line Total.
- **FR-009**: The POS page MUST allow editing quantity directly in the Bill Items table, with line totals updating automatically.
- **FR-010**: The POS page MUST allow removing individual items from the bill via a "Delete" button or swiping (mobile-friendly option).
- **FR-011**: The POS page MUST display a Bill Summary showing Subtotal and Grand Total, updating in real-time as items are added/removed/modified.
- **FR-012**: The POS page MUST include a "Generate Bill" button that sends the bill data (customer name optional, items array with item_id and quantity) to `POST /bills` on the FastAPI backend.
- **FR-013**: The POS page MUST display an invoice view (after bill generation) showing Store Name, Date/Time, all line items, and Grand Total in a format suitable for printing (A4 or receipt paper width).
- **FR-014**: The invoice view MUST include a "Print" button that triggers the browser print dialog (window.print()).
- **FR-015**: The invoice view MUST include a "New Bill" or "Clear" button to reset the bill and search for the next customer.
- **FR-016**: All API calls (add item, list items, update item, create bill) MUST use the FastAPI backend endpoints at `http://localhost:8000` (configurable via environment variables for different environments).
- **FR-017**: All forms and inputs MUST validate data client-side before sending to the API (e.g., positive prices/quantities, required fields).
- **FR-018**: The UI MUST display loading spinners while API calls are in progress and disable buttons during submission to prevent double-clicks.
- **FR-019**: All API errors MUST be caught and displayed to the user as user-friendly messages (map backend errors to readable explanations); technical errors logged for debugging, not shown to user.
- **FR-020**: API calls that fail MUST automatically retry up to 3 times with visible status indicator (e.g., "Retrying...") before showing error; users can manually trigger additional retries via "Retry" button.
- **FR-021**: The POS page MUST monitor item stock in real-time (background polling); if an item's stock drops to zero while in bill, show warning overlay without removing item automatically.
- **FR-022**: Bill generation MUST validate current stock levels at the moment of "Generate Bill" click; reject if insufficient stock with explanation of which items are affected.
- **FR-023**: The frontend MUST be responsive and work on desktop (1920x1080, 1366x768) and tablet (iPad) devices, with mobile support optional for Phase 3.

### Key Entities *(include if feature involves data)*

- **Item**: Represents a product in inventory. Attributes: id, name, category, unit, unit_price, stock_qty, is_active, created_at, updated_at. Fetched from API via `GET /items`.
- **Bill**: Represents a completed transaction. Attributes: id, customer_name (optional), store_name (optional), total_amount, created_at. Created via API `POST /bills`.
- **BillItem**: Represents a line item in a bill. Attributes: id, bill_id (FK), item_id (FK), item_name (snapshot), unit_price (snapshot), quantity, line_total. Part of bill creation.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Admin users can add a new inventory item through the form in under 30 seconds from page load to item appearing in the table.
- **SC-002**: Admin users can search for an item by name or category and see filtered results update within 1 second.
- **SC-003**: Salesperson can add an item to a bill from search to seeing it in the cart in under 10 seconds.
- **SC-004**: Salesperson can complete a 5-item bill (search, add quantities, generate invoice) in under 3 minutes without errors.
- **SC-005**: Bill totals are calculated correctly (line totals + grand total) with 100% accuracy on all test cases.
- **SC-006**: Generated invoices are printable and display all required information (items, quantities, prices, total) in a readable format.
- **SC-007**: API integration is fully functional with zero connection errors to FastAPI backend when backend is running.
- **SC-008**: All validation errors are shown to users within 500ms of form submission with specific field feedback.
- **SC-009**: Page responsiveness: Admin and POS pages load in under 3 seconds on a standard internet connection (50 Mbps).
- **SC-010**: User satisfaction: 95% of admin and salesperson users can complete primary task (add item or create bill) on first attempt without documentation.

## Clarifications

### Session 2025-12-08

- Q: API failure retry strategy → A: Auto-retry with immediate feedback (up to 3 attempts with visible status indicator) plus manual retry button for user control
- Q: Concurrent stock updates on open POS bill → A: Real-time stock monitoring with warning overlay; validate stock at bill generation time
- Q: API error message handling → A: User-friendly error wrapper with technical details hidden in logs; field-specific validation feedback

## Assumptions

- FastAPI backend is running on `http://localhost:8000` (configurable via `NEXT_PUBLIC_API_URL` environment variable).
- Category values are predefined and will be provided as a dropdown list (grocery, beauty, garments, utilities, other).
- Customer name on bills is optional; if not provided, it defaults to "Walk-in" or blank.
- Stock quantities use decimal values (e.g., 2.5 kg) and are not restricted to integers.
- Soft delete via `is_active = false` is handled by the API; frontend only displays active items.
- Bill printing uses the browser's native `window.print()` without external print library.
- Authentication/authorization is not required for Phase 3 (all users can access all pages); this will be added in a future phase.
- CORS is properly configured on the FastAPI backend to allow requests from the Next.js frontend.

## Out of Scope for Phase 3

- User authentication and authorization
- Mobile-optimized UI (desktop-first, tablet support only)
- Real-time inventory sync across multiple terminals
- Payment processing integration
- Inventory history/audit logs
- Multi-store management
- Customer profiles or saved bills
- Discount or tax calculations
- Barcode/QR scanning

## Dependencies

- **Phase 2 – FastAPI Backend**: Must be running and fully functional with all `/items` and `/bills` endpoints implemented and tested.
- **PostgreSQL Database**: Must be accessible by the backend and populated with schema from Phase 2.
- **Environment Setup**: `.env.local` or environment variables for `NEXT_PUBLIC_API_URL`.
