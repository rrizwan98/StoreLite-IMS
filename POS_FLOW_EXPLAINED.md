# POS (Point of Sale) Flow - Complete Guide

## Overview

The POS system is a real-time billing interface that allows salespersons to:
1. Search for items by name
2. Add items to a bill
3. Modify quantities and remove items
4. Generate a bill (which deducts stock)
5. View and print an invoice

---

## How the POS Section Works (Step-by-Step)

### Step 1: Item Search (`ItemSearch.tsx`)

**What happens:**
- User types in the search box
- As user types, the search is **debounced** (waits 300ms after user stops typing)
- Frontend calls `api.getItems({ name: searchQuery })`
- Backend returns matching items from the database

**Key Component:** `useSearch` hook (debounced search)
```typescript
export const useSearch = (searchFn, delay = 300) => {
  // Debounce prevents excessive API calls while user is typing
  // Only searches after 300ms of no typing
}
```

**Backend Response Example:**
```json
[
  {
    "id": 1,
    "name": "Rice",
    "category": "grocery",
    "unit": "kg",
    "unit_price": "299.99",    // ← Returns as STRING!
    "stock_qty": "46.00"        // ← Returns as STRING!
  }
]
```

### Step 2: Stock Check & Item Selection

**What happens:**
1. Search results are displayed in a dropdown
2. Items with `stock_qty <= 0` show as **disabled** (grayed out)
3. Items with stock show a status:
   - Stock < 10: Warning badge "X left" (yellow)
   - Stock >= 10: Success badge "In Stock" (green)
4. User clicks an item to select it

**Stock Check Logic:**
```typescript
if (parseFloat(item.stock_qty as any) <= 0) {
  // Disable button - item is out of stock
  disabled={true}
}
```

**⚠️ Issue (Now Fixed):**
- Backend returns `stock_qty` as **string** (e.g., `"46.00"`)
- Old code: `if (item.stock_qty === 0)` was comparing string to number
- This ALWAYS returned false, so items were always selectable (even when out of stock)
- **Fix:** Convert to number first: `parseFloat(item.stock_qty as any) <= 0`

### Step 3: Add Item to Bill (`useBill` hook)

**What happens when user selects an item:**
1. Item is added to bill state in `useBill` hook
2. If item already in bill, quantity is incremented
3. Line total is calculated: `quantity × unit_price`

**Code Flow:**
```typescript
const addItem = (item: Item) => {
  const unitPrice = parseFloat(item.unit_price as any) || 0;  // ← Convert string to number

  if (itemAlreadyInBill) {
    newQuantity = existingQuantity + 1;
    line_total = newQuantity * unitPrice;  // ← Now correct math
  } else {
    // Add new item with quantity=1
    line_total = unitPrice;
  }
}
```

**⚠️ Issue (Now Fixed):**
- Backend returns `unit_price` as **string** (e.g., `"299.99"`)
- Old code: `quantity * item.unit_price` was multiplying number × string = NaN
- Line totals would show as `NaN` or cause calculation errors
- **Fix:** Convert unit_price to number before multiplication

### Step 4: Display Bill Items (`BillItems.tsx`)

**What's shown:**
- Table with all items in current bill
- Columns: Item Name | Unit | Price | Quantity | Line Total | Actions
- Users can:
  - Edit quantity (with up/down input)
  - Remove item (delete button)

**Calculations:**
- Each row shows: `quantity × unit_price = line_total`
- Table footer shows: "X items in bill"

### Step 5: Bill Summary (`BillSummary.tsx`)

**Shows:**
- Subtotal (sum of all line totals)
- Taxes (if applicable - currently 0 in Phase 3)
- Discount (if applicable - currently 0 in Phase 3)
- **Grand Total**

**Formula:**
```
Subtotal = Σ(line_total for each item)
Total = Subtotal + Tax - Discount
```

### Step 6: Real-Time Stock Monitoring (`useStockMonitor` hook)

**What happens in background:**
- Every 5 seconds, hook fetches fresh item data
- Checks if any items currently in bill are now out of stock
- If yes, shows dismissible warning at top of page

**Example Warning:**
```
⚠️ Rice is now out of stock
```

**⚠️ Issue (Now Fixed):**
- When checking `item.stock_qty <= 0`, stock_qty was a string
- String comparison `"0" <= 0` doesn't work as expected
- **Fix:** Convert to number: `parseFloat(item.stock_qty as any) <= 0`

### Step 7: Generate Bill (`GenerateBillButton.tsx`)

**What happens when user clicks "Generate Bill":**
1. Frontend sends POST request to `/api/bills`
2. Request includes:
   ```json
   {
     "customer_name": "John Doe" (optional),
     "items": [
       { "item_id": 1, "quantity": 2 },
       { "item_id": 3, "quantity": 1 }
     ]
   }
   ```
3. Backend:
   - Validates stock availability
   - Deducts stock from inventory
   - Creates bill record in database
   - Returns bill ID
4. Frontend stores bill ID and shows invoice view

### Step 8: View & Print Invoice (`InvoiceView.tsx`)

**What's displayed:**
- Invoice header with store name
- Invoice number and date/time
- Customer name (if provided)
- Itemized list with prices and quantities
- **Grand Total** in large text
- Footer with "Thank you for your purchase" message

**Actions:**
- **Print Invoice:** Opens browser print dialog (Ctrl+P)
- **New Bill:** Clears current bill and returns to search screen

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  POS PAGE (pos/page.tsx)                │
└─────────────────────────────────────────────────────────┘
                              │
                 ┌────────────┼────────────┐
                 │            │            │
        ┌────────▼──────┐  ┌──▼────────┐  ┌──▼──────────────┐
        │ ItemSearch    │  │ useBill   │  │ useStockMonitor │
        │ (FR-006)      │  │ (FR-008)  │  │ (FR-021)        │
        └────────┬──────┘  └──┬────────┘  └──┬──────────────┘
                 │            │              │
        ┌────────▼──────────┐ │ addItem      │ polling
        │ api.getItems()    │ │ updateQty    │ every 5s
        │ /api/items?name=X │ │ removeItem   │
        └───────────────────┘ │              │
                              │              │
                 ┌────────────┴──────────────┘
                 │
        ┌────────▼─────────────────────┐
        │   STATE: BillItems[]          │
        │   - item_id, quantity, etc    │
        └────────┬─────────────────────┘
                 │
    ┌────────────┼────────────────────┐
    │            │                    │
┌───▼──────┐ ┌──▼──────────┐ ┌───────▼──┐
│BillItems │ │BillSummary  │ │Generate   │
│Display   │ │ (totals)    │ │ Button    │
└───┬──────┘ └──┬──────────┘ └───────┬──┘
    │           │                    │
    │           │                    │
    └───────────┼────────┬───────────┘
                │        │
                │    POST /api/bills
                │    (item_id, qty)
                │        │
                │    ┌───▼────────────┐
                │    │ Backend:       │
                │    │ - Validate stk │
                │    │ - Deduct stk   │
                │    │ - Create bill  │
                │    └───┬────────────┘
                │        │ billId
                │    ┌───▼────────────┐
                │    │ InvoiceView    │
                │    │ - Show invoice │
                │    │ - Print option │
                │    └────────────────┘
```

---

## Data Type Issues (Explained)

### The Problem

Backend (FastAPI/SQLAlchemy) returns all **numeric fields as STRINGS** in JSON:

```json
{
  "unit_price": "299.99",      // String, not number!
  "stock_qty": "46.00",        // String, not number!
  "line_total": "1499.95"      // String, not number!
}
```

### Why?

SQLAlchemy's `Decimal` type (used for currency/quantities) serializes to strings in JSON for precision. This prevents floating-point math errors in financial calculations.

### What Breaks Without Conversion?

| Operation | Without Fix | With Fix |
|-----------|------------|----------|
| `stock_qty === 0` | `"46.00" === 0` → false | `parseFloat("46.00") === 0` → false ✅ |
| `qty * price` | `2 * "299.99"` → NaN ❌ | `2 * 299.99` → 599.98 ✅ |
| `stock_qty < 10` | `"5.00" < 10` → true ✅ | Still works but inconsistent |
| `.toFixed(2)` | `"299.99".toFixed()` → error ❌ | `(299.99).toFixed(2)` → "299.99" ✅ |

### Solution Applied

Wrap all numeric fields with `parseFloat()` before:
1. **Math operations:** `quantity * parseFloat(unit_price)`
2. **Comparisons:** `parseFloat(stock_qty) <= 0`
3. **Formatting:** `(parseFloat(price) || 0).toFixed(2)`

---

## Files Modified to Fix POS Issues

### 1. `frontend/components/pos/ItemSearch.tsx`
- Line 36: Stock check - convert string to number
- Line 121: Disabled state - convert string to number
- Lines 131-139: Stock status display - convert string to number

### 2. `frontend/lib/hooks.ts` - `useBill` function
- Lines 61-62: Convert unit_price in addItem()
- Lines 86: Store converted unit_price in bill state
- Lines 107: Convert unit_price in updateQuantity()

### 3. `frontend/lib/hooks.ts` - `useStockMonitor` function
- Lines 312-313: Convert stock_qty for availability check

### 4. `frontend/components/admin/ItemsTable.tsx`
- Lines 65-71: Stock status display - convert string to number

---

## Testing the POS Flow

### Quick Test:
1. Navigate to http://localhost:3000/pos
2. Search for an item (e.g., "rice")
3. Item appears in dropdown (should be clickable if stock > 0)
4. Click item → adds to bill
5. Verify line total shows correct calculation
6. Modify quantity → line total updates
7. Remove item → removed from bill
8. Click "Generate Bill" → creates invoice
9. Invoice shows with correct prices and total

### Expected Outcomes:
- ✅ Item can be selected when in stock
- ✅ Line totals display as currency (₹XXX.XX)
- ✅ Bill summary shows correct grand total
- ✅ Invoice prints properly
- ✅ Stock warnings appear if item becomes unavailable

---

## Key Files in POS Flow

| File | Purpose |
|------|---------|
| `frontend/app/pos/page.tsx` | Main POS page - orchestrates components |
| `frontend/components/pos/ItemSearch.tsx` | Search items with dropdown |
| `frontend/components/pos/BillItems.tsx` | Display items in bill with edit/remove |
| `frontend/components/pos/BillSummary.tsx` | Show totals |
| `frontend/components/pos/GenerateBillButton.tsx` | Submit bill to backend |
| `frontend/components/pos/InvoiceView.tsx` | Display & print invoice |
| `frontend/components/pos/StockWarning.tsx` | Real-time stock warnings |
| `frontend/lib/hooks.ts` | useBill, useSearch, useStockMonitor |
| `frontend/lib/api.ts` | API calls to backend |

---

## Common Issues & Solutions

### Issue: Item can't be selected
**Cause:** Stock qty comparison using string
**Solution:** Use `parseFloat(stock_qty) <= 0`

### Issue: Line total shows NaN
**Cause:** Multiplying quantity × string price
**Solution:** Convert unit_price to number before multiplication

### Issue: Stock warnings not working
**Cause:** Stock availability check using string comparison
**Solution:** Convert stock_qty to number before comparing

### Issue: Prices show as "NaN.NaN"
**Cause:** Calling `.toFixed()` on string
**Solution:** `(parseFloat(price) || 0).toFixed(2)`

---

## Phase 3 Requirements Met

✅ **FR-006:** Item search with real-time results
✅ **FR-007:** Add items to bill
✅ **FR-008:** Display bill items with edit/remove
✅ **FR-012:** Generate bill with stock deduction
✅ **FR-013:** View invoice
✅ **FR-014:** Print invoice
✅ **FR-021:** Real-time stock monitoring

---

**Last Updated:** 2025-12-08
**Status:** ✅ All POS functionality working
