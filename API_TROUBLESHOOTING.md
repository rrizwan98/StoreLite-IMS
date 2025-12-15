# API Connection Troubleshooting Guide

## Common Issues & Solutions

### Issue 1: Frontend Getting 404 Errors (RESOLVED)
**Symptoms**:
```
GET /items HTTP/1.1" 404 Not Found
GET /items?name=sugar HTTP/1.1" 404 Not Found
```

**Cause**: Frontend was calling `/items` instead of `/api/items`

**Solution**: ✅ Fixed in commit `1270c27`
- All frontend endpoints now use `/api/` prefix
- Backend router prefixes all paths with `/api`

**Verification**:
```bash
# Test correct endpoint
curl http://localhost:8000/api/items
# ✅ Should return 200 OK with items

# Old incorrect endpoint (should fail)
curl http://localhost:8000/items
# ❌ Will return 404 Not Found
```

---

### Issue 2: Backend Not Running
**Symptoms**:
```
Connection refused
ECONNREFUSED 127.0.0.1:8000
```

**Solution**:
```bash
# Start backend in a terminal
cd backend
python -m uvicorn app.main:app --reload

# You should see:
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

### Issue 3: Frontend Can't Connect to Backend
**Symptoms**:
- No data loading in admin/pos pages
- All API calls fail

**Solutions**:

1. **Check backend is running**:
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "ok", "service": "IMS REST API"}
   ```

2. **Check environment variable** (if not localhost):
   ```bash
   # In frontend/.env.local
   NEXT_PUBLIC_API_URL=http://localhost:8000
   # Change localhost:8000 if backend is on different server
   ```

3. **Check CORS is enabled**:
   - Backend has CORS middleware enabled
   - Frontend can call from any origin
   - Should see `Access-Control-Allow-*` headers in response

---

### Issue 4: Stock Monitoring Not Working
**Symptoms**:
- Stock warnings not appearing even when stock becomes 0

**Solutions**:

1. **Check polling interval**:
   - Stock monitor polls every 5 seconds
   - Wait up to 5 seconds to see warning

2. **Check backend stock deduction**:
   ```bash
   # Verify stock was actually reduced in admin
   curl http://localhost:8000/api/items/1
   # Check stock_qty value
   ```

3. **Check warning component**:
   - Warning appears at top of POS page
   - May auto-dismiss after 5 seconds
   - Click X to dismiss manually

---

## Correct Endpoint Format

### Backend Routing
All endpoints are prefixed with `/api`:

```
Backend Router Prefix: /api

GET    /api/items              → List items
GET    /api/items/{id}         → Get single item
POST   /api/items              → Create item
PUT    /api/items/{id}         → Update item
POST   /api/bills              → Create bill
GET    /api/bills/{id}         → Get bill
```

### Frontend API Client
All calls use the `/api` prefix:

```typescript
// frontend/lib/api.ts

async getItems() {
  return this.request('GET', '/api/items');  // ✅ Correct
}

async addItem(data) {
  return this.request('POST', '/api/items', data);  // ✅ Correct
}

async createBill(data) {
  return this.request('POST', '/api/bills', data);  // ✅ Correct
}
```

---

## Testing Endpoints

### Test with curl

```bash
# 1. Get all items
curl http://localhost:8000/api/items

# 2. Search items
curl "http://localhost:8000/api/items?name=rice"

# 3. Filter by category
curl "http://localhost:8000/api/items?category=Grocery"

# 4. Create item
curl -X POST http://localhost:8000/api/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Item",
    "category": "Test",
    "unit": "piece",
    "unit_price": 100,
    "stock_qty": 10
  }'

# 5. Get item by ID
curl http://localhost:8000/api/items/1

# 6. Update item
curl -X PUT http://localhost:8000/api/items/1 \
  -H "Content-Type: application/json" \
  -d '{"unit_price": 150, "stock_qty": 20}'
```

### Test with Frontend

1. Start backend: `python -m uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open http://localhost:3000/admin
4. Try adding an item → should work (no 404 errors)
5. Search for items → should work and find items
6. Go to /pos → search should work
7. Add items to bill → should work

---

## Network Debugging

### Check Network Tab in Browser DevTools

1. Open Chrome DevTools (F12)
2. Go to "Network" tab
3. Try an action (e.g., search for items)
4. Look for requests starting with `/api/items`
5. Check response status (should be 200, not 404)

### Expected Requests

**From Admin Page**:
- `GET /api/items` → 200 OK
- `GET /api/items?name=X` → 200 OK
- `POST /api/items` → 201 Created
- `PUT /api/items/1` → 200 OK

**From POS Page**:
- `GET /api/items` → 200 OK (repeated as user searches)
- `GET /api/items?name=X` → 200 OK (search results)
- `POST /api/bills` → 201 Created
- `GET /api/bills/1` → 200 OK (invoice data)

---

## Common HTTP Status Codes

| Status | Meaning | Solution |
|--------|---------|----------|
| 200 OK | Request succeeded | ✅ All good |
| 201 Created | Resource created | ✅ Item/bill created |
| 400 Bad Request | Invalid data | Check input validation |
| 404 Not Found | Endpoint not found | Check `/api/` prefix |
| 422 Unprocessable | Validation error | Check required fields |
| 500 Server Error | Backend error | Check server logs |

---

## Server Logs

### Backend Console Output
```
INFO:     127.0.0.1:50630 - "GET /api/items HTTP/1.1" 200 OK
         ↑ IP         ↑ Method/Path           ↑ Status Code
```

**Good logs**:
```
"GET /api/items HTTP/1.1" 200 OK
"GET /api/items?name=rice HTTP/1.1" 200 OK
```

**Bad logs (before fix)**:
```
"GET /items HTTP/1.1" 404 Not Found     ❌ Missing /api/
```

---

## Quick Checklist

Before using the application:

- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:3000
- [ ] Can curl `http://localhost:8000/health` successfully
- [ ] Frontend `.env.local` has correct API URL
- [ ] Browser DevTools show requests to `/api/items` (not `/items`)
- [ ] API responses have 200/201 status codes
- [ ] No CORS errors in browser console
- [ ] Admin page loads and shows items table
- [ ] POS page can search and find items
- [ ] Stock warnings appear when item becomes unavailable

---

## Still Having Issues?

1. **Check logs**: Look at backend console output
2. **Check network**: Open DevTools Network tab and inspect requests
3. **Check endpoints**: Verify using curl commands above
4. **Restart services**: Kill and restart both backend and frontend
5. **Clear cache**: Hard refresh browser (Ctrl+Shift+R)
6. **Check database**: Verify SQLite database exists and has data

---

## Reference Documents

- `ENDPOINT_FIX_SUMMARY.md` - Details of the API path fix
- `GETTING_STARTED_PHASE3.md` - Quick start guide
- `PHASE3_COMPLETION_SUMMARY.md` - Full feature overview
- `frontend/TESTING.md` - Manual test scenarios

---

**Last Updated**: 2025-12-08
**Status**: ✅ All endpoints working correctly
