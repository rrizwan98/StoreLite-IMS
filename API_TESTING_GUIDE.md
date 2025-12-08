# IMS FastAPI - Complete API Testing Guide

## Overview

This guide provides comprehensive step-by-step instructions for testing all endpoints of the IMS (Inventory Management System) FastAPI backend. All endpoints have been tested and verified to work correctly with the Neon PostgreSQL database.

---

## Prerequisites

1. **Server Running**: FastAPI server must be running on `http://localhost:8000`
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. **Database Connected**: PostgreSQL (Neon) database is configured and running
   ```
   DATABASE_URL=postgresql://neondb_owner:npg_7Ln4QywGXgkZ@ep-withered-field-ad37lvs8-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
   ```

3. **Tools Available**:
   - cURL or Postman for manual testing
   - Python requests library for automated testing
   - Web browser for Swagger UI

---

## Quick Start - Automated Testing

### Option 1: Run Full Test Suite (Recommended)

```bash
cd backend
python test_api.py
```

This runs **comprehensive tests** covering all endpoints with:
- System health checks
- Item creation (4 categories)
- Listing and filtering items
- Getting single items
- Updating items
- Creating bills
- Listing and retrieving bills
- Error handling validation
- Soft delete functionality

**Expected Result**: All tests pass with 200/201/204 status codes

---

## Manual Testing - Step by Step

### Step 1: System Endpoints (No Auth Required)

These are basic health checks to verify the API is running.

#### 1.1 Health Check
```bash
curl -X GET http://localhost:8000/health
```

**Expected Response (200):**
```json
{
  "status": "ok",
  "service": "IMS REST API"
}
```

#### 1.2 Root API Info
```bash
curl -X GET http://localhost:8000/
```

**Expected Response (200):**
```json
{
  "service": "IMS REST API",
  "version": "0.1.0",
  "docs": "/docs",
  "openapi": "/openapi.json"
}
```

#### 1.3 Interactive Swagger UI (in Browser)
Open: `http://localhost:8000/docs`

This provides an interactive interface to test all endpoints.

---

### Step 2: Inventory Management (User Stories 1-5)

#### 2.1 Create Item (User Story 1)

**Important**: Categories are restricted to exactly 5 options:
- `Grocery`
- `Garments`
- `Beauty`
- `Utilities`
- `Other`

```bash
curl -X POST http://localhost:8000/api/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rice 5kg",
    "category": "Grocery",
    "unit": "kg",
    "unit_price": 45.50,
    "stock_qty": 100
  }'
```

**Expected Response (201):**
```json
{
  "id": 1,
  "name": "Rice 5kg",
  "category": "Grocery",
  "unit": "kg",
  "unit_price": "45.50",
  "stock_qty": "100.00",
  "is_active": true,
  "created_at": "2025-12-08T08:25:22.291481",
  "updated_at": "2025-12-08T08:25:22.291481"
}
```

**Save the item ID** (e.g., `1`) for later tests.

#### 2.2 Create Additional Items (for testing)

Create items in different categories:

**Garments:**
```bash
curl -X POST http://localhost:8000/api/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cotton T-Shirt",
    "category": "Garments",
    "unit": "piece",
    "unit_price": 299.99,
    "stock_qty": 50
  }'
```

**Beauty:**
```bash
curl -X POST http://localhost:8000/api/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Shampoo Bottle",
    "category": "Beauty",
    "unit": "liter",
    "unit_price": 199.00,
    "stock_qty": 75
  }'
```

**Utilities:**
```bash
curl -X POST http://localhost:8000/api/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Light Bulb LED",
    "category": "Utilities",
    "unit": "piece",
    "unit_price": 125.00,
    "stock_qty": 200
  }'
```

#### 2.3 List All Items (User Story 2)

```bash
curl -X GET http://localhost:8000/api/items
```

**Expected Response (200):** Array of all active items, sorted by name.

#### 2.4 Filter by Category

```bash
curl -X GET "http://localhost:8000/api/items?category=Grocery"
```

Returns only items in the "Grocery" category.

#### 2.5 Filter by Name (Partial Match)

```bash
curl -X GET "http://localhost:8000/api/items?name=Rice"
```

Returns items containing "Rice" in the name (case-insensitive).

#### 2.6 Get Single Item (User Story 3)

Replace `1` with actual item ID:

```bash
curl -X GET http://localhost:8000/api/items/1
```

**Expected Response (200):** Single item details.

#### 2.7 Update Item (User Story 4)

**Important**: Use `PUT` method (not PATCH).

Replace `1` with actual item ID:

```bash
curl -X PUT http://localhost:8000/api/items/1 \
  -H "Content-Type: application/json" \
  -d '{
    "unit_price": 49.99,
    "stock_qty": 80
  }'
```

**Expected Response (200):** Updated item with new values.

Note: You can update any field individually or multiple fields:
- `name`
- `category`
- `unit`
- `unit_price`
- `stock_qty`

#### 2.8 Soft Delete Item (User Story 5)

Replace `1` with actual item ID:

```bash
curl -X DELETE http://localhost:8000/api/items/1
```

**Expected Response (204):** No content returned.

**Verify deletion:**
```bash
curl -X GET http://localhost:8000/api/items/1
```

Should return **404 Not Found**:
```json
{
  "error": "Not found",
  "details": "Item with id 1 not found"
}
```

---

### Step 3: Billing & Invoicing (User Stories 6-8)

#### 3.1 Create Bill (User Story 6)

Use actual item IDs from step 2:

```bash
curl -X POST http://localhost:8000/api/bills \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "John Doe",
    "store_name": "Store A",
    "items": [
      {
        "item_id": 1,
        "quantity": 5
      },
      {
        "item_id": 2,
        "quantity": 2
      }
    ]
  }'
```

**Expected Response (201):**
```json
{
  "id": 1,
  "customer_name": "John Doe",
  "store_name": "Store A",
  "total_amount": "1497.48",
  "created_at": "2025-12-08T08:26:00.853776",
  "bill_items": [
    {
      "item_name": "Rice 5kg",
      "unit_price": "45.50",
      "quantity": "5.00",
      "line_total": "227.50"
    },
    {
      "item_name": "Cotton T-Shirt",
      "unit_price": "299.99",
      "quantity": "2.00",
      "line_total": "599.98"
    }
  ]
}
```

**Key Features:**
- Stock quantities are automatically reduced
- Line totals are calculated (unit_price × quantity)
- Total amount is the sum of all line totals
- Decimal precision is maintained (returned as strings)

**Save the bill ID** for later tests.

#### 3.2 List All Bills (User Story 8)

```bash
curl -X GET http://localhost:8000/api/bills
```

**Expected Response (200):** Array of all bills with their items.

#### 3.3 Get Single Bill (User Story 7)

Replace `1` with actual bill ID:

```bash
curl -X GET http://localhost:8000/api/bills/1
```

**Expected Response (200):** Complete bill details with all line items.

---

## Error Handling Tests

### Test 4.1: Invalid Category

```bash
curl -X POST http://localhost:8000/api/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Invalid Item",
    "category": "Electronics",
    "unit": "piece",
    "unit_price": 100.00,
    "stock_qty": 10
  }'
```

**Expected Response (500):** Database constraint violation
```json
{
  "error": "Internal server error",
  "details": "A database error occurred. Please try again later."
}
```

**Note**: Category must be one of: Grocery, Garments, Beauty, Utilities, Other

### Test 4.2: Get Non-existent Item

```bash
curl -X GET http://localhost:8000/api/items/9999
```

**Expected Response (404):**
```json
{
  "error": "Not found",
  "details": "Item with id 9999 not found"
}
```

### Test 4.3: Insufficient Stock

```bash
curl -X POST http://localhost:8000/api/bills \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test User",
    "store_name": "Test Store",
    "items": [
      {
        "item_id": 1,
        "quantity": 10000
      }
    ]
  }'
```

**Expected Response (400):**
```json
{
  "error": "Business logic error",
  "details": "Insufficient stock for item 'Rice 5kg': required=10000, available=95.00"
}
```

### Test 4.4: Non-existent Item in Bill

```bash
curl -X POST http://localhost:8000/api/bills \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test User",
    "store_name": "Test Store",
    "items": [
      {
        "item_id": 9999,
        "quantity": 1
      }
    ]
  }'
```

**Expected Response (400):**
```json
{
  "error": "Business logic error",
  "details": "Item with id 9999 not found"
}
```

---

## API Endpoints Summary

### System Endpoints
| Method | Endpoint | Status | Description |
|--------|----------|--------|-------------|
| GET | `/health` | 200 | Health check |
| GET | `/` | 200 | API root info |
| GET | `/docs` | 200 | Swagger UI |
| GET | `/openapi.json` | 200 | OpenAPI schema |

### Inventory Endpoints
| Method | Endpoint | Status | Description |
|--------|----------|--------|-------------|
| POST | `/api/items` | 201 | Create item |
| GET | `/api/items` | 200 | List items |
| GET | `/api/items?category=X` | 200 | Filter by category |
| GET | `/api/items?name=X` | 200 | Filter by name |
| GET | `/api/items/{id}` | 200 | Get single item |
| PUT | `/api/items/{id}` | 200 | Update item |
| DELETE | `/api/items/{id}` | 204 | Soft delete item |

### Billing Endpoints
| Method | Endpoint | Status | Description |
|--------|----------|--------|-------------|
| POST | `/api/bills` | 201 | Create bill |
| GET | `/api/bills` | 200 | List bills |
| GET | `/api/bills/{id}` | 200 | Get single bill |

---

## Valid Category Values

The system enforces these exact categories (case-sensitive):
```
- Grocery
- Garments
- Beauty
- Utilities
- Other
```

---

## Response Formats

### Item Response
```json
{
  "id": 1,
  "name": "string",
  "category": "string",
  "unit": "string",
  "unit_price": "decimal_as_string",
  "stock_qty": "decimal_as_string",
  "is_active": true,
  "created_at": "ISO_datetime",
  "updated_at": "ISO_datetime"
}
```

### Bill Response
```json
{
  "id": 1,
  "customer_name": "string",
  "store_name": "string",
  "total_amount": "decimal_as_string",
  "created_at": "ISO_datetime",
  "bill_items": [
    {
      "item_name": "string",
      "unit_price": "decimal_as_string",
      "quantity": "decimal_as_string",
      "line_total": "decimal_as_string"
    }
  ]
}
```

---

## Testing Checklist

- [ ] Server starts without errors
- [ ] Health check responds with 200
- [ ] Root endpoint works
- [ ] Can create items with valid categories
- [ ] Can list all items
- [ ] Can filter by category
- [ ] Can filter by name
- [ ] Can get single item
- [ ] Can update item price and stock
- [ ] Can soft delete item (404 after deletion)
- [ ] Can create bill with multiple items
- [ ] Stock quantities decrease after bill creation
- [ ] Cannot create bill with invalid category (500 error)
- [ ] Cannot create bill with insufficient stock (400 error)
- [ ] Cannot create bill with non-existent item (400 error)
- [ ] Can list all bills
- [ ] Can get single bill with all items

---

## Common Issues & Solutions

### Issue: Invalid category error
**Solution**: Use only the 5 valid categories: Grocery, Garments, Beauty, Utilities, Other

### Issue: 405 Method Not Allowed on update
**Solution**: Use `PUT` method, not `PATCH`

### Issue: Stock quantity shows different after bill creation
**Solution**: This is correct behavior - stock is automatically reduced when bill is created

### Issue: Bill returns 500 error
**Solution**: Ensure all item IDs exist and have sufficient stock before creating bill

### Issue: Decimal precision issues
**Solution**: All decimal values (prices, quantities, totals) are returned as strings to maintain precision

---

## Additional Resources

- **Interactive API Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Test Script**: `backend/test_api.py` (Python)
- **Test Bash Script**: `backend/test_api.sh` (Bash)

---

## Support

For issues or questions, refer to:
1. API Documentation in Swagger UI
2. Server logs in FastAPI terminal
3. Database logs in Neon console

