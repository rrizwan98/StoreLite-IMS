# FastAPI Backend Quick Start Guide

## Starting the Server (Windows)

### Option 1: Using Batch File (Easiest)
```bash
cd backend
run_dev.bat
```

### Option 2: Manual Command
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8001
```

### Option 3: Using Uvicorn Directly
```bash
cd backend
uvicorn app.main:app --reload --port 8001
```

---

## Accessing the API

Once the server starts, you'll see:
```
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
```

### Swagger UI (Interactive Testing)
**URL**: http://127.0.0.1:8001/docs

The Swagger UI allows you to:
- View all available endpoints
- Test endpoints directly in the browser
- See request/response examples
- Auto-generate API documentation

### OpenAPI JSON
**URL**: http://127.0.0.1:8001/openapi.json

### Health Check
**URL**: http://127.0.0.1:8001/health
**Response**: `{"status": "ok", "service": "IMS REST API"}`

---

## Testing in Postman

### 1. Create Item
```
POST http://127.0.0.1:8001/api/items
Content-Type: application/json

{
  "name": "Sugar",
  "category": "Grocery",
  "unit": "kg",
  "unit_price": "10.50",
  "stock_qty": "100.000"
}
```

### 2. List Items
```
GET http://127.0.0.1:8001/api/items
```

### 3. Create Bill
```
POST http://127.0.0.1:8001/api/bills
Content-Type: application/json

{
  "items": [
    {"item_id": 1, "quantity": "10.000"}
  ],
  "customer_name": "John Doe",
  "store_name": "Store 1"
}
```

### 4. Get Bill Details
```
GET http://127.0.0.1:8001/api/bills/1
```

### 5. List Bills
```
GET http://127.0.0.1:8001/api/bills
```

---

## API Endpoints

### Inventory Management
- **POST /api/items** - Create new item
- **GET /api/items** - List items (supports filters: ?name=...&category=...)
- **GET /api/items/{id}** - Get item details
- **PUT /api/items/{id}** - Update item
- **DELETE /api/items/{id}** - Deactivate item (soft-delete)

### Billing Management
- **POST /api/bills** - Create bill with items
- **GET /api/bills/{id}** - Get bill details
- **GET /api/bills** - List all bills

---

## Database

### Current Setup
- **Development**: SQLite (automatically created at `ims_dev.db`)
- **Production**: PostgreSQL (set DATABASE_URL environment variable)

### Using PostgreSQL

1. Set environment variable:
```bash
set DATABASE_URL=postgresql://user:password@localhost:5432/ims_db
```

2. Restart the server

Or add to `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/ims_db
```

---

## Common Issues & Solutions

### Issue: "Address already in use"
**Solution**: The server is already running on port 8001. Either:
1. Close the existing server (Ctrl+C)
2. Use a different port: `uvicorn app.main:app --reload --port 8002`

### Issue: "Connection refused" or "Cannot connect to database"
**Solution**: This is normal for development. The app will use SQLite automatically.
No action needed - just use the API normally.

### Issue: Swagger UI doesn't load (blank page)
**Solution**:
1. Make sure server is running and shows "Uvicorn running on http://127.0.0.1:8001"
2. Clear browser cache (Ctrl+Shift+Delete)
3. Try incognito mode
4. Try a different browser

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/unit/test_schemas.py -v
```

Run with coverage:
```bash
pytest tests/ --cov=app
```

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, error handlers
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── exceptions.py        # Custom exceptions
│   └── routers/
│       ├── inventory.py     # Inventory endpoints
│       └── billing.py       # Billing endpoints
├── tests/
│   ├── conftest.py          # Pytest configuration
│   ├── unit/               # Unit tests
│   └── contract/           # API endpoint tests
├── requirements.txt
├── pyproject.toml
├── run_dev.bat              # Windows startup script
├── run_dev.sh               # Linux/Mac startup script
└── README.md
```

---

## Next Steps

1. **Test the API**: Open Swagger UI and try the endpoints
2. **Create sample data**: Use POST /api/items to add items
3. **Test billing**: Create bills and verify stock updates
4. **Run tests**: Execute `pytest tests/ -v` to verify everything works
5. **Integrate with Frontend**: Next.js frontend will call `/api/*` endpoints

---

## Support

For detailed documentation, see:
- `IMPLEMENTATION_SUMMARY.md` - Complete implementation details
- `specs/002-fastapi-backend-p2/spec.md` - Feature specification
- `specs/002-fastapi-backend-p2/plan.md` - Architecture and design
