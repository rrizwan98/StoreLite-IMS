---
feature: 003-nextjs-frontend-p3
date: 2025-12-08
status: Ready for Implementation
total_tasks: 56
---

# Tasks: Next.js Frontend UI (Phase 3) - StoreLite IMS

**Input**: spec.md (8 user stories, P1/P2 priorities), plan.md (architecture, tech stack, folder structure)
**Prerequisites**: Phase 2 FastAPI backend running at `http://localhost:8000`, PostgreSQL accessible
**Organization**: Tasks organized by user story to enable independent implementation and testing

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story (US1–US8) - helps map tasks to spec requirements
- **Exact file paths**: Each task shows where code goes in `/frontend` folder structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize Next.js project structure, dependencies, and configuration

- [ ] T001 Create folder structure per plan.md: `frontend/app`, `frontend/components`, `frontend/lib`, `frontend/styles`, `frontend/public`
- [ ] T002 [P] Initialize Next.js 14+ project with `npx create-next-app@latest` in frontend directory
- [ ] T003 [P] Install core dependencies: TypeScript, Tailwind CSS, Axios in `frontend/package.json`
- [ ] T004 [P] Configure TypeScript: Enable strict mode in `frontend/tsconfig.json`
- [ ] T005 [P] Configure Tailwind CSS in `frontend/tailwind.config.js` with Next.js integration
- [ ] T006 [P] Set up ESLint and Prettier configs in `frontend/.eslintrc.json` and `frontend/.prettierrc`
- [ ] T007 Create `.env.local.example` with `NEXT_PUBLIC_API_URL=http://localhost:8000`
- [ ] T008 [P] Create `frontend/package.json` scripts: `dev`, `build`, `start`, `lint`, `type-check`
- [ ] T009 Create `frontend/README.md` with setup and getting-started instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities and infrastructure that ALL user stories depend on
**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T010 [P] Create type definitions file `frontend/lib/types.ts` with interfaces: Item, Bill, BillItem, APIError
- [ ] T011 [P] Create constants file `frontend/lib/constants.ts` with API_URL, categories, error codes
- [ ] T012 [P] Create validation rules file `frontend/lib/validation.ts` with validateItem(), validateBillItem() functions
- [ ] T013 Create API client wrapper `frontend/lib/api.ts` with:
  - APIClient class with retry logic (3 attempts, exponential backoff)
  - Methods: getItems(), getItem(), addItem(), updateItem(), createBill(), getBill()
  - Error mapping function mapError() per FR-019
  - Retry status indicator callback
- [ ] T014 [P] Create custom hooks file `frontend/lib/hooks.ts` with:
  - useItems() - fetch and cache items
  - useBill() - manage bill state
  - useSearch() - debounced search functionality
- [ ] T015 [P] Create shared components in `frontend/components/shared/`:
  - LoadingSpinner.tsx - simple loading indicator
  - ErrorMessage.tsx - user-friendly error display
  - SuccessToast.tsx - transient success messages
  - ErrorBoundary.tsx - React error boundary wrapper
- [ ] T016 [P] Create Header component in `frontend/components/shared/Header.tsx` with app title and logo
- [ ] T017 [P] Create Navigation component in `frontend/components/shared/Navigation.tsx` with /admin and /pos links
- [ ] T018 Create root layout `frontend/app/layout.tsx` with Header, Navigation, globals.css import
- [ ] T019 Create `frontend/app/globals.css` with Tailwind imports and base styles
- [ ] T020 [P] Create environment configuration loader in `frontend/lib/constants.ts` (read NEXT_PUBLIC_API_URL)
- [ ] T021 [P] Create error mapping service `frontend/lib/errorMap.ts` with ERROR_MESSAGES constant per FR-019

**Checkpoint**: Foundation ready - all user story tasks can now proceed in parallel

---

## Phase 3: User Story 1 - Store Admin: Add New Inventory Item (Priority: P1)

**Goal**: Enable admin users to add new products via form in Admin page; form validates client-side before API submission (FR-002, FR-017)

**Independent Test**: Navigate to `/admin`, fill "Add Item" form (name, category, unit, price, stock), submit, verify item appears in table and success message shown

### Implementation for User Story 1

- [ ] T022 [P] [US1] Create AddItemForm component `frontend/components/admin/AddItemForm.tsx` with:
  - Form fields: name, category (dropdown), unit, unit_price, stock_qty
  - Client-side validation via validateItem() from lib/validation.ts
  - Submit handler calls api.addItem()
  - Shows field-level validation errors (FR-017)
  - Disables button during submission (FR-018)
- [ ] T023 [P] [US1] Create SuccessToast integration in AddItemForm to show "Item added successfully" message
- [ ] T024 [US1] Create admin layout `frontend/app/admin/layout.tsx` with admin-specific navigation
- [ ] T025 [US1] Create admin page `frontend/app/admin/page.tsx` that:
  - Imports and renders AddItemForm component
  - Implements onItemAdded callback to refresh inventory table (will be added in US2)
  - Wraps components in ErrorBoundary

**Checkpoint**: User Story 1 complete - admin can add items via form with validation and success feedback

---

## Phase 4: User Story 2 - Store Admin: View and Search Inventory (Priority: P1)

**Goal**: Display all inventory items in searchable table with filters by name and category (FR-003, FR-004, FR-018)

**Independent Test**: Navigate to `/admin`, verify table loads with all items, search by name filters results in <1s, category filter works, empty state shown when no matches

### Implementation for User Story 2

- [ ] T026 [P] [US2] Create ItemsTable component `frontend/components/admin/ItemsTable.tsx` with:
  - Column headers: Name, Category, Unit, Price, Stock, Actions
  - Displays items passed as prop
  - Shows loading spinner during API calls
  - Renders empty state message "No items found" when table is empty
  - Includes Edit and Delete buttons in Actions column
- [ ] T027 [P] [US2] Create search/filter components `frontend/components/admin/Filters.tsx` with:
  - Name search input (debounced, case-insensitive substring match per FR-004)
  - Category dropdown filter (exact match)
  - Clear filters button
  - Calls parent callback on filter change
- [ ] T028 [P] [US2] Create useItems custom hook in `frontend/lib/hooks.ts` to:
  - Fetch items on component mount via api.getItems()
  - Handle loading and error states
  - Support filtering by name and category (client-side or server-side query params)
  - Return: items, loading, error, refetch function
- [ ] T029 [US2] Update admin page `frontend/app/admin/page.tsx` to:
  - Import and use useItems() hook
  - Render Filters component with state management
  - Render ItemsTable with filtered items
  - Pass items to AddItemForm's onItemAdded to trigger refresh
  - Show LoadingSpinner while items loading
  - Show ErrorMessage with Retry button on API error (FR-007 concept)
  - Integrate real-time item updates: call refetch() when AddItemForm adds item

**Checkpoint**: User Story 2 complete - admin can view all items, search by name, filter by category

---

## Phase 5: User Story 3 - Store Admin: Update Item Price and Stock (Priority: P1)

**Goal**: Allow admins to edit item price and stock via modal form (FR-005, FR-017)

**Independent Test**: Click Edit button on item, modify price/stock, click Save, verify changes appear in table and are persisted

### Implementation for User Story 3

- [ ] T030 [P] [US3] Create EditItemModal component `frontend/components/admin/EditItemModal.tsx` with:
  - Modal/dialog showing pre-filled form with current item data (name, category, unit, unit_price, stock_qty)
  - Client-side validation on save (same validateItem rules - no negative prices/stock)
  - Save button calls api.updateItem() with item ID and new data
  - Cancel button closes modal without saving
  - Shows field-level validation errors if save attempted with invalid data (FR-017)
  - Disables Save button during submission (FR-018)
  - Shows error message if API call fails with retry button (FR-020 pattern)
  - Success message on successful update
- [ ] T031 [US3] Update ItemsTable component `frontend/components/admin/ItemsTable.tsx` to:
  - Add Edit button in Actions column that opens EditItemModal
  - Pass item data to modal as prop
  - Implement onSave callback to refresh items list after successful edit
  - Pass onEdit callback to modal
- [ ] T032 [US3] Create ItemActions component `frontend/components/admin/ItemActions.tsx` (refactor Edit/Delete buttons)
  - Edit button triggers modal open
  - Delete button (optional for US3, but prepare structure)
  - Can be used in ItemsTable for cleaner code
- [ ] T033 [US3] Update admin page `frontend/app/admin/page.tsx` to:
  - Manage EditItemModal visibility state
  - Pass selected item to modal
  - Implement onSave handler to refresh items via refetch()
  - Update ItemsTable to show updated items after edit

**Checkpoint**: User Story 3 complete - admin can edit existing items with validation and error handling

---

## Phase 6: User Story 4 - Salesperson: Search and Add Items to Bill (Priority: P1)

**Goal**: Enable salesperson to search items and add them to bill with quantity 1 (FR-006, FR-007, FR-008)

**Independent Test**: Navigate to `/pos`, search for item by name, select from dropdown, verify item appears in Bill Items table with qty 1

### Implementation for User Story 4

- [ ] T034 [P] [US4] Create ItemSearch component `frontend/components/pos/ItemSearch.tsx` with:
  - Search input box (debounced, substring match per FR-006)
  - Dropdown showing matching items: name, price, stock (FR-006)
  - Click item to add to bill
  - Shows "No items found" when no matches
  - Prevents adding items with zero stock with warning message (FR-005 from spec: "low stock warning")
- [ ] T035 [P] [US4] Create BillItems component `frontend/components/pos/BillItems.tsx` to display:
  - Table with columns: Item Name, Unit, Quantity (editable), Unit Price, Line Total (FR-008)
  - Starting empty state message "No items in bill yet"
  - Quantity field as text input (will be made editable in US5)
  - Delete button per row (implemented in US5)
- [ ] T036 [P] [US4] Create useBill custom hook in `frontend/lib/hooks.ts` to:
  - Manage bill state: items array with (item_id, item_name, unit, unit_price, quantity)
  - addItem(item) function - adds item with qty 1, or increments qty if already in bill (FR-007)
  - Return: bill, addItem, removeItem (for US5), updateQuantity (for US5)
- [ ] T037 [US4] Create POS layout `frontend/app/pos/layout.tsx` with POS-specific navigation
- [ ] T038 [US4] Create POS page `frontend/app/pos/page.tsx` that:
  - Imports and renders ItemSearch component
  - Imports and renders BillItems component
  - Manages bill state via useBill() hook
  - Passes addItem callback from useBill to ItemSearch
  - Wraps in ErrorBoundary

**Checkpoint**: User Story 4 complete - salesperson can search items and add to bill

---

## Phase 7: User Story 5 - Salesperson: Adjust Item Quantity and Remove Items (Priority: P1)

**Goal**: Allow quantity editing and item removal from bill with automatic total recalculation (FR-009, FR-010)

**Independent Test**: Add items to bill, modify quantity in table, delete item, verify line totals and grand total update correctly

### Implementation for User Story 5

- [ ] T039 [P] [US5] Update BillItems component `frontend/components/pos/BillItems.tsx` to:
  - Make Quantity field editable (input type="number" with validation)
  - Add Delete/Remove button per row
  - On quantity change: call updateQuantity() from useBill hook
  - On delete: call removeItem() from useBill hook
  - Show warning if quantity exceeds available stock (FR-005 from spec: "stock limit warning")
  - Prevent quantity > available stock (client-side validation per FR-005)
- [ ] T040 [US5] Update useBill hook in `frontend/lib/hooks.ts` to:
  - Implement updateQuantity(itemIndex, newQty) - updates quantity, validates against stock
  - Implement removeItem(itemIndex) - removes item from bill
  - Both methods trigger bill summary re-render
- [ ] T041 [US5] Update POS page `frontend/app/pos/page.tsx` to:
  - Pass updateQuantity and removeItem callbacks from useBill to BillItems component
  - Ensure bill total updates in real-time when quantities change

**Checkpoint**: User Story 5 complete - salesperson can adjust quantities and remove items

---

## Phase 8: User Story 6 - Salesperson: View and Confirm Bill Total (Priority: P1)

**Goal**: Display running bill total that updates as items are added/removed/modified (FR-011)

**Independent Test**: Add items to bill, verify Subtotal and Grand Total display and calculate correctly, modify quantity, verify totals update immediately

### Implementation for User Story 6

- [ ] T042 [P] [US6] Create BillSummary component `frontend/components/pos/BillSummary.tsx` with:
  - Display Subtotal (sum of all line totals)
  - Display Grand Total (currently same as subtotal - no tax/discount in Phase 3)
  - Format currency properly (e.g., $123.45)
  - Show "No items yet" or "$0.00" when bill is empty (FR-011 empty state)
  - Accepts bill object as prop with items array
  - Re-renders when bill changes
- [ ] T043 [US6] Update POS page `frontend/app/pos/page.tsx` to:
  - Import and render BillSummary component below BillItems
  - Pass current bill from useBill hook to BillSummary
  - Verify totals update automatically when quantities change or items added/removed
- [ ] T044 [US6] Create utility function in `frontend/lib/validation.ts` or new `frontend/lib/calculations.ts`:
  - calculateLineTotal(unitPrice, quantity) - returns line total
  - calculateSubtotal(billItems) - sums all line totals
  - calculateGrandTotal(subtotal) - returns subtotal (no tax/discount for Phase 3)

**Checkpoint**: User Story 6 complete - bill totals display and update in real-time

---

## Phase 9: User Story 7 - Salesperson: Create and Print Invoice (Priority: P1)

**Goal**: Generate bill record in backend and display printable invoice (FR-012, FR-013, FR-014, FR-022)

**Independent Test**: Add items to bill, click Generate Bill, verify invoice appears with store name/date/items/total, click Print, verify print dialog opens

### Implementation for User Story 7

- [ ] T045 [P] [US7] Create GenerateBillButton component `frontend/components/pos/GenerateBillButton.tsx` with:
  - Button text: "Generate Bill" or "Checkout"
  - Validates bill has at least 1 item before allowing click
  - Calls api.createBill() with bill data: items array (item_id, quantity), optional customer_name
  - Handles API error (insufficient stock, validation error) with user-friendly message per FR-019
  - Shows "Generating..." state during API call
  - Disables button during submission (FR-018)
  - On success: calls parent callback with created bill ID
- [ ] T046 [P] [US7] Create InvoiceView component `frontend/components/pos/InvoiceView.tsx` with:
  - Conditionally rendered after bill generation
  - Displays: Store name, Date/Time, Bill ID, all line items (name, qty, unit price, line total), Grand Total
  - Formatted for printing (clean layout, good for receipt paper or A4)
  - Print button that calls window.print() (FR-014)
  - New Bill/Clear button to reset bill and return to search (US8 integration)
- [ ] T047 [US7] Create print styles in `frontend/app/globals.css` with:
  - @media print rules for InvoiceView component
  - Hide navigation/buttons during print
  - Format for receipt paper width (80mm) or A4
  - Ensure readability on printed output
- [ ] T048 [US7] Update POS page `frontend/app/pos/page.tsx` to:
  - Add state to track generated bill (null when not generated, bill object when generated)
  - Render GenerateBillButton if bill not generated
  - Render InvoiceView if bill is generated (conditional rendering)
  - Pass GenerateBillButton.onSuccess callback to update generated bill state
  - Stock validation at bill generation per FR-022: backend API handles this, frontend shows error if insufficient stock

**Checkpoint**: User Story 7 complete - salesperson can generate and print invoices

---

## Phase 10: User Story 8 - Salesperson: Start New Bill After Invoice (Priority: P2)

**Goal**: Clear bill and return to search after printing invoice (FR-015, FR-023)

**Independent Test**: Generate invoice, click New Bill/Clear, verify bill items empty, search box ready for next customer

### Implementation for User Story 8

- [ ] T049 [US8] Create NewBillButton in InvoiceView component `frontend/components/pos/InvoiceView.tsx` that:
  - Button text: "New Bill" or "Clear Bill"
  - Calls parent callback on click
  - Resets generated bill state
- [ ] T050 [US8] Update useBill hook in `frontend/lib/hooks.ts` to:
  - Add clearBill() function that resets items array to empty
  - Export clearBill for use in POS page
- [ ] T051 [US8] Update POS page `frontend/app/pos/page.tsx` to:
  - Implement NewBillButton.onClick handler to:
    - Call clearBill() from useBill hook
    - Reset generated bill state to null
    - Focus search input for next customer
    - ItemSearch component becomes visible again

**Checkpoint**: User Story 8 complete - full workflow: add items → generate bill → print → clear → next customer

---

## Phase 11: Resilience & Cross-Cutting Concerns

**Purpose**: Implement retry logic, real-time stock monitoring, and error handling across all user stories

### API Retry Logic (FR-020)

- [ ] T052 [P] Implement auto-retry in `frontend/lib/api.ts`:
  - Wrap all API calls in retry logic (3 attempts with exponential backoff)
  - Show "Retrying..." status to user (in error message or toast)
  - On final failure: show error message with manual "Retry" button
  - Manual retry button re-attempts the failed operation
- [ ] T053 [P] Add retry status indicator callback in APIClient:
  - Option 1: Toast component shows retry attempt (1/3, 2/3)
  - Option 2: In-line text in ErrorMessage shows retry status
  - Callback invoked on each retry attempt

### Real-Time Stock Monitoring (FR-021)

- [ ] T054 [US4-US7] [P] Create useStockMonitor custom hook in `frontend/lib/hooks.ts` that:
  - Polls items in current bill every 5-10 seconds (configurable)
  - Checks stock levels via api.getItems() or dedicated api.checkStock() endpoint
  - Returns: warning message if any item stock = 0, unavailable items list
- [ ] T055 [US4-US7] Update POS page `frontend/app/pos/page.tsx` to:
  - Import useStockMonitor hook
  - Display warning overlay if item becomes unavailable: "X is now out of stock"
  - Do NOT automatically remove item from bill (per clarification)
  - Show warning until bill is cleared or item stock replenished
- [ ] T056 [P] Create warning overlay component `frontend/components/pos/StockWarning.tsx`:
  - Displays over bill items
  - Shows which items are unavailable
  - Dismissible or auto-dismiss after N seconds
  - Styled as alert/warning box

**Checkpoint**: Resilience features complete - retry logic and stock monitoring functional

---

## Phase 12: Polish & Validation

**Purpose**: Cross-cutting improvements, testing, and final validation

- [ ] T057 [P] Responsive design validation:
  - Test Admin page on 1920x1080, 1366x768 desktop resolutions
  - Test POS page on iPad tablet (landscape and portrait)
  - Use Tailwind responsive classes for layout
  - Ensure tables are readable and buttons accessible
- [ ] T058 [P] Run `npm run type-check` to verify all TypeScript types are correct
- [ ] T059 [P] Run `npm run build` to verify production build succeeds with no warnings
- [ ] T060 [P] Run `npm run lint` to check ESLint and Prettier standards
- [ ] T061 Create `frontend/TESTING.md` with manual test scenarios:
  - Scenario 1: Add item → verify in table (US1-US2)
  - Scenario 2: Edit item price → verify update (US3)
  - Scenario 3: Search and add 5 items → generate bill → print (US4-US7)
  - Scenario 4: After print, click New Bill → verify empty (US8)
  - Scenario 5: API failure during add item → verify retry → success (T052-T053)
  - Scenario 6: Stock drops to zero while bill open → verify warning (T054-T056)
- [ ] T062 [P] Create `frontend/.gitignore` to exclude node_modules, .next, .env.local, *.log
- [ ] T063 [P] Create `frontend/LICENSE` (copy from project root or use MIT)
- [ ] T064 Run complete end-to-end workflow test:
  - Start FastAPI backend at http://localhost:8000
  - Run `cd frontend && npm run dev` to start dev server
  - Navigate to http://localhost:3000/admin
  - Test Admin workflow: add item → search → edit
  - Navigate to http://localhost:3000/pos
  - Test POS workflow: search → add items → generate bill → print → new bill
  - Verify all FR requirements met (functional, performance, resilience)

**Checkpoint**: Phase 3 frontend implementation complete and validated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories
- **Phase 3-10 (User Stories 1-8)**: All depend on Phase 2 completion
  - P1 stories (US1-US7) should be completed in order: US1 → US2 → US3 → US4 → US5 → US6 → US7
  - P2 story (US8) depends on US7 completion
  - Can proceed sequentially or if team capacity allows: US1+US2+US3 in parallel, then US4+US5+US6 in parallel
- **Phase 11 (Resilience)**: Can be done during US implementation or as final polish
- **Phase 12 (Polish)**: Final phase after all user stories

### Within Each Phase

- **Setup Phase**: All [P] tasks can run in parallel
- **Foundational Phase**: T013 (APIClient) should be done before T014 (hooks) since hooks use API client
- **User Story Phases**: Models/components marked [P] can run in parallel; page integration (non-[P]) must wait for components
- **Resilience Phase**: Can be integrated throughout or added after core user stories complete

### Parallel Opportunities

- **Parallel by Phase**:
  - Phase 1: All [P] tasks (T002, T003, T004, T005, T006, T008)
  - Phase 2: T010-T012 (types, constants, validation), T015-T017 (shared components), T020-T021 (config) can run in parallel
  - Phase 3-8: Component creation tasks ([P] marked) can run in parallel per user story; page integration tasks must wait

- **Parallel by Story** (if multiple developers):
  - After Phase 2: Developer A on US1+US2+US3 (Admin features), Developer B on US4+US5+US6+US7 (POS features)
  - Within US: All component creation can happen in parallel

### Within Each User Story: Component Parallelization

**User Story 4 (Search & Add)**:
```
T034: ItemSearch component
T035: BillItems component
T036: useBill hook
All [P] - run together, then T037-T038 (page integration)
```

**User Story 7 (Generate Bill)**:
```
T045: GenerateBillButton component
T046: InvoiceView component
T047: Print styles
All [P] - run together, then T048 (page integration)
```

---

## Implementation Strategy

### MVP First (User Stories 1-7 Only)

1. Complete **Phase 1: Setup** (T001-T009)
2. Complete **Phase 2: Foundational** (T010-T021) - **CRITICAL**
3. Complete **Phase 3: US1** (T022-T025) - Admin can add items
4. **STOP & VALIDATE**: Test US1 independently before proceeding
5. Complete **Phase 4: US2** (T026-T029) - Admin can search/view items
6. Complete **Phase 5: US3** (T030-T033) - Admin can edit items
7. Complete **Phase 6: US4** (T034-T038) - Salesperson can search and add to bill
8. Complete **Phase 7: US5** (T039-T041) - Can adjust quantities and remove items
9. Complete **Phase 8: US6** (T042-T044) - Bill total displays correctly
10. Complete **Phase 9: US7** (T045-T048) - Can generate and print invoice
11. **STOP & VALIDATE**: Full end-to-end test: add items → search → bill → print
12. Deploy Phase 3 MVP (US1-US7)

### Add P2 Story

13. Complete **Phase 10: US8** (T049-T051) - New Bill button for workflow continuity
14. **STOP & VALIDATE**: Complete workflow test end-to-end

### Add Resilience & Polish

15. Complete **Phase 11: Resilience** (T052-T056) - Retry logic and stock monitoring
16. Complete **Phase 12: Polish** (T057-T064) - Validation and testing

### Total Scope

- **MVP (US1-US7, no tests)**: ~20 tasks (T001-T051 up to core implementation)
- **Full Phase 3 (US1-US8 + resilience)**: ~56 tasks (T001-T064)
- **Estimated effort**: 4-6 weeks for 1 developer (sequential), 2-3 weeks with 2 developers (parallel)

---

## Status & Next Steps

✅ **READY FOR IMPLEMENTATION**

- Specification complete (spec.md)
- Architecture planned (plan.md)
- Tasks generated (this file)
- Phase 2 FastAPI backend operational

**Next**: Pick first task (T001) and begin Phase 1 setup, following the implementation strategy above.

