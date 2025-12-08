# Valid Item Categories

## Quick Reference

When creating or updating items in the StoreLite IMS, use **ONLY** these categories:

| Category | Example Items |
|----------|----------------|
| **Grocery** | Rice, Sugar, Milk, Oil, Flour, Spices |
| **Beauty** | Soap, Shampoo, Cream, Makeup, Perfume |
| **Garments** | Shirt, Pants, Dress, Shoes, Jacket |
| **Utilities** | Light Bulb, Batteries, Matches, Cleaning Supplies |

---

## Why These Categories?

The database enforces a **strict list** of categories to:
- Ensure data consistency
- Enable reliable reporting and filtering
- Prevent data entry errors

---

## What Changed

**Old (Invalid):**
- grocery (lowercase) ❌
- beauty (lowercase) ❌
- garments (lowercase) ❌
- utilities (lowercase) ❌
- other ❌

**New (Valid):**
- Grocery ✅
- Beauty ✅
- Garments ✅
- Utilities ✅

---

## Error Messages

### If You Try to Use Invalid Category

**Via UI:**
The category dropdown will only show the 4 valid options.

**Via API (curl/Postman):**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "category"],
      "msg": "Value error, Category must be one of: Grocery, Beauty, Garments, Utilities"
    }
  ]
}
```

---

## How to Create an Item

### Using the Admin Dashboard

1. Go to http://localhost:3000/admin
2. Click **"Add Item"** button
3. Fill in:
   - **Name:** Item name (e.g., "Basmati Rice")
   - **Category:** Select from dropdown ← **Only valid options shown**
   - **Unit:** kg, lbs, pcs, ltr, ml, box, pack, dozen, meter, cm
   - **Unit Price:** Price per unit (e.g., 250.50)
   - **Stock Qty:** Initial quantity (e.g., 100)
4. Click **"Create"**
5. Item is added successfully ✅

### Using API (curl example)

```bash
curl -X POST http://localhost:8000/api/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Basmati Rice",
    "category": "Grocery",
    "unit": "kg",
    "unit_price": 250.50,
    "stock_qty": 100
  }'
```

---

## Testing the Fix

To verify the fix is working:

1. **Start the application:**
   ```bash
   # Terminal 1: Backend
   cd backend
   python -m uvicorn app.main:app --reload

   # Terminal 2: Frontend
   cd frontend
   npm run dev
   ```

2. **Test creating an item:**
   - Navigate to http://localhost:3000/admin
   - Click "Add Item"
   - Try category dropdown
   - Verify only 4 options appear: Grocery, Beauty, Garments, Utilities
   - Select "Grocery"
   - Fill other details
   - Click "Create"
   - ✅ Item should create successfully

3. **Test invalid category (API only):**
   ```bash
   curl -X POST http://localhost:8000/api/items \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test",
       "category": "other",
       "unit": "box",
       "unit_price": 50,
       "stock_qty": 10
     }'
   ```
   - Should return 422 Unprocessable Entity
   - Error message shows valid categories

---

## FAQ

**Q: Can I add "other" as a category?**
A: No. The system only allows: Grocery, Beauty, Garments, Utilities.

**Q: Why was "other" removed?**
A: The database constraint doesn't allow it. It was a mistake in the frontend.

**Q: Can I add more categories?**
A: Only if you modify the database CHECK constraint and update both backend and frontend constants. This requires a code change.

**Q: What happens if I have data with "other" category?**
A: You'll need to update those items to one of the 4 valid categories or delete them.

**Q: Is the category case-sensitive?**
A: Yes! Use exactly: "Grocery", "Beauty", "Garments", "Utilities" (with capitals).

---

## Related Documentation

- `CATEGORY_CONSTRAINT_FIX.md` - Technical details of the fix
- `POS_FLOW_EXPLAINED.md` - How the POS system works
- `API_TROUBLESHOOTING.md` - Common API issues and solutions

---

**Last Updated:** 2025-12-08
