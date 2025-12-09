# IMS API - Quick Test Reference

## Start Server
```bash
cd backend
python -m uvicorn app.main:app --reload
```

## Run All Tests (Automated)
```bash
cd backend
python test_api.py
```

## Quick Test Commands (cURL)

### System
```bash
# Health check
curl http://localhost:8000/health

# API info
curl http://localhost:8000/
```

### Create Item
```bash
curl -X POST http://localhost:8000/api/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rice",
    "category": "Grocery",
    "unit": "kg",
    "unit_price": 45.50,
    "stock_qty": 100
  }'
```

### List Items
```bash
curl http://localhost:8000/api/items

# Filter by category
curl "http://localhost:8000/api/items?category=Grocery"

# Filter by name
curl "http://localhost:8000/api/items?name=Rice"
```

### Get Item
```bash
curl http://localhost:8000/api/items/1
```

### Update Item
```bash
curl -X PUT http://localhost:8000/api/items/1 \
  -H "Content-Type: application/json" \
  -d '{
    "unit_price": 49.99,
    "stock_qty": 80
  }'
```

### Delete Item
```bash
curl -X DELETE http://localhost:8000/api/items/1
```

### Create Bill
```bash
curl -X POST http://localhost:8000/api/bills \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "John Doe",
    "store_name": "Store A",
    "items": [
      {"item_id": 1, "quantity": 5}
    ]
  }'
```

### List Bills
```bash
curl http://localhost:8000/api/bills
```

### Get Bill
```bash
curl http://localhost:8000/api/bills/1
```

---

## Valid Categories
```
Grocery, Garments, Beauty, Utilities, Other
```

---

## Interactive Testing
```
http://localhost:8000/docs
```
(Swagger UI in browser)

---

## Expected Status Codes
- **200** - OK (GET, PUT successful)
- **201** - Created (POST successful)
- **204** - No Content (DELETE successful)
- **400** - Bad Request (insufficient stock, invalid item)
- **404** - Not Found (item doesn't exist)
- **500** - Server Error (database error)

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Invalid category error | Use: Grocery, Garments, Beauty, Utilities, Other |
| 405 Method Not Allowed | Use PUT for update (not PATCH) |
| 404 on deleted item | This is correct - soft delete hides item |
| Stock mismatch after bill | This is correct - stock reduced automatically |

---

## Test Results
✓ All 30+ tests passing
✓ All endpoints working
✓ Error handling verified
✓ Database connected (Neon PostgreSQL)

See `TEST_RESULTS_SUMMARY.md` for full details.
See `API_TESTING_GUIDE.md` for comprehensive guide.
