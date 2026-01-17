# Developer Documentation

> Complete API reference and integration guide for developers building on top of IMS.

## Overview

IMS provides a comprehensive REST API and a unique **Published Agents** feature that lets you create AI-powered chat interfaces for your users — without building AI infrastructure yourself.

---

## Quick Start

### Base URL
```
Production: https://your-backend-url.com
Local: http://localhost:8000
```

### Authentication
All API requests require a JWT Bearer token:
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     https://api.example.com/api/items
```

### Get Your Token
```bash
# Login
curl -X POST https://api.example.com/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "you@example.com", "password": "your-password"}'

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

---

## Time Savings for Developers

### Without IMS Published Agents

Building AI chat for your app requires:

| Task | Time Estimate |
|------|---------------|
| Set up LLM infrastructure | 2-4 weeks |
| Build conversation management | 1-2 weeks |
| Create tool integrations | 2-3 weeks |
| Implement rate limiting | 1 week |
| Build admin dashboard | 2 weeks |
| Security & authentication | 1-2 weeks |
| Testing & debugging | 2 weeks |
| **Total** | **11-16 weeks** |

### With IMS Published Agents

| Task | Time |
|------|------|
| Create Published Agent | 5 minutes |
| Get embed code | 30 seconds |
| Add to your website | 10 minutes |
| **Total** | **~15 minutes** |

> **Developer Time Saved: 10-15 weeks**

---

## Published Agents

### What are Published Agents?

Published Agents let you create AI-powered chat widgets that:
- Query your database using natural language
- Can be embedded on any website
- Have rate limiting and access control built-in
- Work without any AI/ML knowledge

### Create a Published Agent

```bash
curl -X POST https://api.example.com/api/developer/agents \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Customer Support Bot",
       "description": "Helps customers check order status",
       "allowed_tables": ["orders", "products", "customers"],
       "access_mode": "read_only",
       "rate_limit_per_minute": 30,
       "allowed_domains": ["https://mystore.com", "https://support.mystore.com"],
       "expires_at": "2025-12-31T23:59:59Z"
     }'
```

**Response:**
```json
{
  "id": "pub_agent_abc123",
  "name": "Customer Support Bot",
  "api_key": "ims_pk_live_xxxxxxxxxxxx",
  "status": "active",
  "created_at": "2025-01-17T10:00:00Z"
}
```

### Embed on Your Website

Get the embed code:
```bash
curl https://api.example.com/api/developer/agents/pub_agent_abc123/embed \
     -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```html
<!-- Add this to your website -->
<script src="https://api.example.com/embed/chat.js"></script>
<div id="ims-chat"
     data-agent-id="pub_agent_abc123"
     data-api-key="ims_pk_live_xxxxxxxxxxxx">
</div>
<script>
  IMSChat.init({
    container: '#ims-chat',
    theme: 'light',
    position: 'bottom-right'
  });
</script>
```

### Your Users Can Now Chat

```
User: What's the status of order #12345?

Bot: Order #12345:
     • Status: Shipped
     • Items: 3x Blue T-Shirt, 1x Jeans
     • Tracking: FX123456789
     • Expected delivery: January 20, 2025
```

**No AI code written. No LLM API keys managed. Just works.**

---

## API Reference

### Authentication Endpoints

#### Sign Up
```http
POST /auth/signup
```
```json
{
  "email": "user@example.com",
  "password": "secure-password",
  "full_name": "John Doe"
}
```

#### Login
```http
POST /auth/login
```
```json
{
  "email": "user@example.com",
  "password": "secure-password"
}
```

#### Refresh Token
```http
POST /auth/refresh
```
```json
{
  "refresh_token": "your-refresh-token"
}
```

---

### Inventory Endpoints

#### List Items
```http
GET /api/items?name=shirt&category=garments
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| name | string | Filter by name (partial match) |
| category | string | Filter by category |
| limit | integer | Max items to return (default: 100) |
| offset | integer | Pagination offset |

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Blue T-Shirt",
      "category": "garments",
      "unit": "piece",
      "price": 350.00,
      "stock_quantity": 50,
      "is_active": true,
      "created_at": "2025-01-15T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

#### Create Item
```http
POST /api/items
```
```json
{
  "name": "Blue T-Shirt",
  "category": "garments",
  "unit": "piece",
  "price": 350.00,
  "stock_quantity": 50
}
```

#### Update Item
```http
PUT /api/items/{id}
```
```json
{
  "price": 399.00,
  "stock_quantity": 75
}
```

#### Get Item
```http
GET /api/items/{id}
```

---

### Billing Endpoints

#### Create Bill
```http
POST /api/billing
```
```json
{
  "customer_name": "Ahmed Khan",
  "items": [
    {"item_id": 1, "quantity": 3},
    {"item_id": 5, "quantity": 2}
  ]
}
```

**Response:**
```json
{
  "id": 42,
  "invoice_number": "INV-2025-0042",
  "customer_name": "Ahmed Khan",
  "items": [
    {
      "item_id": 1,
      "item_name": "Blue T-Shirt",
      "quantity": 3,
      "unit_price": 350.00,
      "total": 1050.00
    },
    {
      "item_id": 5,
      "item_name": "Black Pants",
      "quantity": 2,
      "unit_price": 899.00,
      "total": 1798.00
    }
  ],
  "subtotal": 2848.00,
  "tax": 142.40,
  "total_amount": 2990.40,
  "created_at": "2025-01-17T14:30:00Z"
}
```

#### List Bills
```http
GET /api/billing?date_from=2025-01-01&date_to=2025-01-31
```

#### Get Bill
```http
GET /api/billing/{id}
```

---

### Analytics Endpoints

#### Inventory Health
```http
GET /api/analytics/inventory-health
```

**Response:**
```json
{
  "total_items": 156,
  "total_value": 245000.00,
  "low_stock_count": 8,
  "out_of_stock_count": 3,
  "category_breakdown": {
    "electronics": {"count": 45, "value": 125000},
    "garments": {"count": 67, "value": 85000},
    "grocery": {"count": 44, "value": 35000}
  },
  "alerts": [
    {
      "item_id": 12,
      "name": "Samsung Charger",
      "current_stock": 5,
      "minimum_stock": 20,
      "severity": "critical"
    }
  ]
}
```

#### Sales Analytics
```http
GET /api/analytics/sales?period=monthly&year=2025
```

---

### Published Agent Endpoints

#### Create Agent
```http
POST /api/developer/agents
```
```json
{
  "name": "Support Bot",
  "description": "Customer support assistant",
  "allowed_tables": ["orders", "products"],
  "access_mode": "read_only",
  "rate_limit_per_minute": 30,
  "allowed_domains": ["https://mysite.com"],
  "expires_at": "2025-12-31T23:59:59Z"
}
```

#### List Agents
```http
GET /api/developer/agents
```

#### Update Agent
```http
PUT /api/developer/agents/{id}
```

#### Delete Agent
```http
DELETE /api/developer/agents/{id}
```

#### Regenerate API Key
```http
POST /api/developer/agents/{id}/regenerate-key
```

#### Get Usage Stats
```http
GET /api/developer/agents/{id}/usage
```

**Response:**
```json
{
  "agent_id": "pub_agent_abc123",
  "period": "2025-01",
  "total_requests": 15420,
  "successful_requests": 15105,
  "failed_requests": 315,
  "average_response_time_ms": 1250,
  "unique_users": 892,
  "daily_breakdown": [
    {"date": "2025-01-15", "requests": 523},
    {"date": "2025-01-16", "requests": 612}
  ]
}
```

---

### Public Chat API (For Published Agents)

This endpoint is for external users chatting with your published agent:

```http
POST /api/v1/public/chat
X-API-Key: ims_pk_live_xxxxxxxxxxxx
Origin: https://mysite.com
```
```json
{
  "message": "What's the status of order #12345?",
  "thread_id": "optional-thread-id-for-continuity"
}
```

**Response:**
```json
{
  "response": "Order #12345 is currently shipped and expected to arrive on January 20, 2025.",
  "thread_id": "thread_xyz789",
  "metadata": {
    "tables_queried": ["orders"],
    "query_time_ms": 245
  }
}
```

---

## Database Connection

### Check Connection
```http
GET /db-connect/status
```

### Connect Database
```http
POST /db-connect
```
```json
{
  "connection_type": "own_database",
  "database_uri": "postgresql://user:pass@host:5432/dbname"
}
```

### Get Schema
```http
GET /db-connect/schema
```

**Response:**
```json
{
  "tables": [
    {
      "name": "products",
      "columns": [
        {"name": "id", "type": "integer", "primary_key": true},
        {"name": "name", "type": "varchar(255)"},
        {"name": "price", "type": "decimal(10,2)"},
        {"name": "stock", "type": "integer"}
      ]
    }
  ],
  "last_updated": "2025-01-17T10:00:00Z"
}
```

---

## Scheduler Endpoints

#### Create Scheduled Task
```http
POST /scheduler/tasks
```
```json
{
  "query": "Send low stock report",
  "scheduled_at": "2025-01-20T09:00:00Z",
  "tools": ["analytics", "gmail"]
}
```

#### List Tasks
```http
GET /scheduler/tasks
```

#### Cancel Task
```http
DELETE /scheduler/tasks/{id}
```

---

## File Handling

#### Upload File
```http
POST /api/files/upload
Content-Type: multipart/form-data
```

#### List Files
```http
GET /api/files
```

#### Delete File
```http
DELETE /api/files/{id}
```

#### Search Files (Semantic)
```http
POST /api/file-search/search
```
```json
{
  "query": "invoice for Samsung products",
  "limit": 10
}
```

---

## MCP Connectors

#### List Connectors
```http
GET /api/connectors
```

#### Add Connector
```http
POST /api/connectors
```
```json
{
  "name": "My Custom MCP",
  "server_url": "https://my-mcp-server.com",
  "auth_type": "api_key",
  "api_key": "my-api-key"
}
```

#### Update Connector
```http
PUT /api/connectors/{id}
```

#### Delete Connector
```http
DELETE /api/connectors/{id}
```

---

## Error Handling

All errors return structured responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid item data",
    "details": {
      "price": "Price must be positive",
      "stock_quantity": "Stock cannot be negative"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `UNAUTHORIZED` | 401 | Missing/invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `SERVER_ERROR` | 500 | Internal server error |

---

## Rate Limiting

API requests are rate limited:

| Endpoint Type | Limit |
|---------------|-------|
| Authentication | 10/minute |
| Read operations | 100/minute |
| Write operations | 30/minute |
| Published Agent API | Configurable |

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705500000
```

---

## Webhooks (Coming Soon)

Register webhooks for events:
- `item.created`
- `item.updated`
- `bill.created`
- `stock.low`
- `task.completed`

---

## SDKs

### Python
```python
from ims import IMSClient

client = IMSClient(api_key="your-api-key")

# List items
items = client.items.list(category="electronics")

# Create item
item = client.items.create(
    name="New Product",
    price=999.00,
    stock_quantity=50
)

# Create bill
bill = client.billing.create(
    customer_name="Customer",
    items=[{"item_id": 1, "quantity": 2}]
)
```

### JavaScript/TypeScript
```typescript
import { IMSClient } from '@ims/sdk';

const client = new IMSClient({ apiKey: 'your-api-key' });

// List items
const items = await client.items.list({ category: 'electronics' });

// Create item
const item = await client.items.create({
  name: 'New Product',
  price: 999.00,
  stockQuantity: 50
});
```

---

## Best Practices

### 1. Use Pagination
Always paginate large result sets:
```http
GET /api/items?limit=50&offset=100
```

### 2. Handle Errors Gracefully
```python
try:
    item = client.items.get(id=999)
except NotFoundError:
    print("Item not found")
except RateLimitError:
    time.sleep(60)
    retry()
```

### 3. Use Thread IDs for Chat
Maintain conversation context:
```python
thread_id = None

# First message
response = client.chat("Hello", thread_id=thread_id)
thread_id = response.thread_id

# Follow-up uses same thread
response = client.chat("Show more", thread_id=thread_id)
```

### 4. Refresh Tokens Proactively
```python
if token_expires_in < 300:  # 5 minutes
    new_tokens = client.auth.refresh(refresh_token)
```

---

## Security Recommendations

1. **Store API keys securely** - Use environment variables, never commit to code
2. **Use HTTPS** - All requests should be over HTTPS
3. **Rotate API keys** - Regenerate Published Agent keys periodically
4. **Set domain restrictions** - Limit which domains can use your agent
5. **Use read-only mode** - Unless write access is necessary
6. **Set expiration dates** - Don't leave agents active indefinitely

---

## API Documentation

Interactive API documentation available at:
- **Swagger UI**: `https://api.example.com/docs`
- **ReDoc**: `https://api.example.com/redoc`
- **OpenAPI Spec**: `https://api.example.com/openapi.json`

---

[← Back to Main Docs](./index.md) | [Tools & Connectors →](./tools-connectors.md)
