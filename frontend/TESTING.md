# StoreLite IMS - Manual Testing Guide

This document provides manual test scenarios to validate all functional requirements for the Next.js frontend Phase 3 implementation.

## Test Environment Setup

1. Ensure FastAPI backend is running at `http://localhost:8000`
2. Start the frontend dev server: `cd frontend && npm run dev`
3. Access the application at `http://localhost:3000`
4. Use browser DevTools for network monitoring and debugging

## Test Scenarios

### Scenario 1: Admin - Add Item (User Story 1)
**Objective**: Verify admin can add new inventory item with validation

**Steps**:
1. Navigate to `/admin` page
2. Fill in "Add Item" form:
   - Name: "Test Item"
   - Category: "Groceries"
   - Unit: "kg"
   - Unit Price: 150.50
   - Stock Quantity: 100
3. Click "Add Item" button
4. Verify:
   - Success message appears
   - Item appears in inventory table below
   - Form resets for next entry

**Expected Outcomes**:
- ✅ Item added to database
- ✅ Real-time table update shows new item
- ✅ Success toast message displayed
- ✅ Form fields cleared for next entry

---

### Scenario 2: Admin - Search and Filter (User Story 2)
**Objective**: Verify admin can search and filter inventory

**Steps**:
1. Navigate to `/admin` page
2. In the Filters section:
   - Type "Test Item" in Name search box
   - Verify table filters as you type (debounced, <1s response)
3. Clear name search
4. Select "Groceries" from Category dropdown
5. Verify only Groceries items show
6. Click "Clear Filters" button
7. Verify all items reappear

**Expected Outcomes**:
- ✅ Search filters case-insensitive substring match
- ✅ Category filter exact match
- ✅ Table updates in real-time without page reload
- ✅ Clear Filters button resets both search and category

---

### Scenario 3: Admin - Edit Item (User Story 3)
**Objective**: Verify admin can edit existing item price and stock

**Steps**:
1. Navigate to `/admin` page
2. Find any item in table
3. Click "Edit" button in Actions column
4. Modal opens with current item data
5. Modify:
   - Unit Price: Change to 200.00
   - Stock Quantity: Change to 50
6. Click "Save" button
7. Verify:
   - Modal closes
   - Table reflects updated values
   - Success message shown
8. Optional: Try editing to invalid values (negative price) - should show validation error

**Expected Outcomes**:
- ✅ Edit modal displays current data
- ✅ Changes persisted to database
- ✅ Table updates immediately
- ✅ Validation errors prevent invalid edits
- ✅ Client-side validation prevents negative prices/stock

---

### Scenario 4: POS - Search and Add to Bill (User Story 4)
**Objective**: Verify salesperson can search items and add to bill

**Steps**:
1. Navigate to `/pos` page
2. In "Search Items" section:
   - Type item name in search box
   - Verify dropdown shows matching items with name, price, stock
3. Click item in dropdown
4. Verify:
   - Item appears in "Bill Items" table with qty=1
   - Search box clears for next item
5. Add 3-4 different items
6. Verify all appear in Bill Items table with correct prices

**Expected Outcomes**:
- ✅ Search is debounced and responsive (<300ms)
- ✅ Items can only be added if stock > 0 (warning shown if stock=0)
- ✅ Quantity starts at 1
- ✅ Line totals calculated correctly (unit_price × quantity)
- ✅ Bill items table shows all columns: Name, Unit, Qty, Price, Total

---

### Scenario 5: POS - Adjust Quantity and Remove Items (User Story 5)
**Objective**: Verify salesperson can edit quantities and remove items

**Steps**:
1. From Scenario 4, have 3-4 items in bill
2. For first item:
   - Click on Quantity field
   - Change to 5
   - Verify line total updates immediately (e.g., 150.50 × 5 = 752.50)
3. For second item:
   - Click Delete/Remove button
   - Item removed from table
4. Modify one more item's quantity to 0
   - Item should be automatically removed

**Expected Outcomes**:
- ✅ Quantity field editable with number input
- ✅ Line totals recalculate immediately
- ✅ Grand total updates in real-time
- ✅ Delete button removes specific item only
- ✅ Qty=0 auto-removes item

---

### Scenario 6: POS - View and Confirm Bill Total (User Story 6)
**Objective**: Verify bill totals display and update correctly

**Steps**:
1. Have 3-4 items in bill from previous scenarios
2. Verify Bill Summary sidebar shows:
   - Item count (e.g., "3 items")
   - Subtotal (sum of all line totals)
   - Grand Total (same as subtotal for Phase 3)
3. Modify quantities of 2-3 items
4. Verify totals recalculate immediately
5. Remove all items
6. Verify:
   - "No items yet" or "$0.00" message shown
   - Summary still visible and accessible

**Expected Outcomes**:
- ✅ Subtotal = sum of (qty × unit_price) for all items
- ✅ Grand Total displayed prominently
- ✅ Currency formatted as INR (₹X.XX)
- ✅ Totals update instantly with quantity changes
- ✅ Empty bill state handled gracefully

---

### Scenario 7: POS - Generate and Print Invoice (User Story 7)
**Objective**: Verify bill generation and invoice printing

**Steps**:
1. Add 3-5 items to bill (Scenario 4)
2. Click "Generate Bill" button
3. Verify:
   - API call succeeds
   - Invoice View appears replacing bill form
   - Shows: Store name, Bill ID, Date/Time, all items, Grand Total
4. Review invoice layout:
   - Store name at top
   - Invoice/Receipt title
   - Bill ID and date/time
   - Line items table (Name, Unit, Qty, Price, Total)
   - Subtotal and Grand Total
   - Thank you message
5. Click "Print Invoice" button
6. Verify:
   - Print dialog opens
   - Layout is optimized for printing (receipt or A4)
   - Navigation and buttons hidden in print preview
7. Cancel print dialog (don't actually print unless testing printer)

**Expected Outcomes**:
- ✅ Bill created in backend via API
- ✅ Invoice displays all bill details
- ✅ Invoice formatting is professional and readable
- ✅ Print dialog opens on click
- ✅ Print layout optimized (no buttons, good spacing)
- ✅ Works on receipt paper (80mm) and A4

---

### Scenario 8: POS - Start New Bill (User Story 8)
**Objective**: Verify workflow can continue after printing invoice

**Steps**:
1. From Scenario 7, have invoice displayed
2. Click "New Bill" button
3. Verify:
   - Invoice disappears
   - Bill entry form returns
   - Bill items table is empty
   - Search box is visible and focused
   - Bill Summary shows "$0.00" or "No items"
4. Add items again to verify workflow continues

**Expected Outcomes**:
- ✅ Bill state cleared completely
- ✅ Can immediately add items to new bill
- ✅ No data from previous bill remains
- ✅ Full workflow cycle works: search → add → generate → print → new bill

---

### Scenario 9: Resilience - API Retry with Failure (User Story 11)
**Objective**: Verify retry logic and error handling

**Steps**:
1. Stop the FastAPI backend
2. Navigate to `/pos` and try to search for items
3. Observe:
   - Network error occurs
   - Error message shown in search area
   - "Retry" button available
4. Start the FastAPI backend again
5. Click "Retry" button
6. Verify:
   - Search completes successfully
   - Items load and display

**Expected Outcomes**:
- ✅ API failures are caught and displayed
- ✅ User-friendly error messages shown
- ✅ Retry button allows re-attempt
- ✅ Retry logic with exponential backoff (3 attempts)
- ✅ "Retrying..." status shown during retries

---

### Scenario 10: Stock Monitoring - Real-time Stock Depletion Warning (User Story 11)
**Objective**: Verify stock monitoring detects unavailable items

**Prerequisites**:
- Have an item with limited stock (e.g., 2 units)
- Have two instances of the system: one admin, one POS

**Steps**:
1. In POS: Add item with limited stock (qty=1) to bill
2. In Admin: Edit that same item to reduce stock to 0
3. Wait 5-10 seconds for polling
4. In POS: Observe warning overlay appears:
   - "⚠️ Item is now out of stock"
   - Yellow/warning styling
   - Dismissible X button
5. Item remains in bill (not auto-removed)
6. Click X to dismiss warning
7. Back in Admin: Replenish stock to 10
8. In POS: Warning disappears within 5-10 seconds

**Expected Outcomes**:
- ✅ Stock monitor polls every 5-10 seconds
- ✅ Real-time warning appears when item goes out of stock
- ✅ Warning names specific items
- ✅ Item NOT auto-removed from bill
- ✅ Warning dismissible or auto-disappears
- ✅ Warning clears when stock replenished

---

## Device & Responsive Testing (Phase 12)

### Desktop Resolutions
Test on:
- 1920×1080 (Full HD): Admin and POS pages fully responsive
- 1366×768 (Laptop): Tables visible, no horizontal scroll needed
- 1280×720 (Tablet landscape): All buttons accessible, readable

### Tablet Testing (iPad)
Test on:
- Landscape: 1024×768 - POS page sidebar should adapt
- Portrait: 768×1024 - Layout should stack vertically

### Mobile (if supported)
- Verify responsive classes applied
- Admin table may be horizontal-scrollable on small screens

---

## Build & Type Checking (Phase 12)

### Type Checking
```bash
cd frontend
npm run type-check
# Expected: No TypeScript errors
```

### Production Build
```bash
cd frontend
npm run build
# Expected: Build succeeds with no warnings
```

### Linting
```bash
cd frontend
npm run lint
# Expected: No ESLint or Prettier violations
```

---

## End-to-End Workflow Test

**Complete User Journey** (30 minutes):

1. **Admin workflow**:
   - ✅ Add 5 new items with various categories
   - ✅ Search for items by name
   - ✅ Filter by category
   - ✅ Edit prices for 2 items
   - ✅ Verify all updates reflected

2. **POS workflow**:
   - ✅ Search and add 3-4 items to bill
   - ✅ Adjust quantities
   - ✅ Generate bill
   - ✅ Review invoice
   - ✅ Print invoice (preview only)
   - ✅ Start new bill

3. **Error recovery**:
   - ✅ Stop backend briefly, observe error
   - ✅ Restart backend and retry
   - ✅ Complete operation successfully

4. **Final verification**:
   - ✅ Navigate between /admin and /pos
   - ✅ All pages load correctly
   - ✅ No console errors
   - ✅ Responsive on different screens

---

## Success Criteria Checklist

For Phase 3 to be considered complete, all of the following must pass:

- [ ] All 8 User Story scenarios (1-8) pass completely
- [ ] Resilience scenarios (9-10) pass
- [ ] Responsive design works on 3+ devices
- [ ] Production build succeeds: `npm run build`
- [ ] Type check succeeds: `npm run type-check`
- [ ] Linting passes: `npm run lint`
- [ ] No console errors during testing
- [ ] All FR requirements met (see spec.md)

---

## Debugging Tips

### Network Issues
- Use DevTools Network tab to monitor API calls
- Check that FastAPI backend is running: `curl http://localhost:8000/items`
- Verify NEXT_PUBLIC_API_URL in `.env.local`

### TypeScript Errors
- Run `npm run type-check` to identify issues
- Check that all imports use correct paths
- Verify type definitions in `lib/types.ts`

### Component Not Rendering
- Check browser console for React errors
- Verify ErrorBoundary is wrapping components
- Check component imports are correct

### Styling Issues
- Verify Tailwind CSS is configured: `npm run build`
- Check globals.css is imported in layout.tsx
- Verify no conflicting class names

---

## Notes

- Backend URL must be `http://localhost:8000` (configurable in `.env.local`)
- All tests should use the SQLite database (`ims_dev.db`)
- Test data is persisted; can reset by deleting database file
- Performance target: <1s response for all API calls
- No authentication in Phase 3 (all endpoints open)
