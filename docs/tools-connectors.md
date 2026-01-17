# Tools & Connectors Guide

> Extend your AI assistant's capabilities by connecting external services. More tools = more automation = more time saved.

## Overview

IMS comes with built-in tools, but you can supercharge your AI by connecting external services. Each connector adds new abilities — send emails via Gmail, store files in Google Drive, sync with Notion, or add any custom MCP server.

**No API coding required. Connect with a few clicks.**

---

## Why Connect Tools?

### Without Connected Tools

Your AI can:
- ✅ Manage inventory
- ✅ Create bills
- ✅ Generate reports
- ❌ Send emails
- ❌ Store files externally
- ❌ Sync with other apps
- ❌ Use external services

### With Connected Tools

Your AI can:
- ✅ Everything above, plus...
- ✅ Email reports automatically
- ✅ Backup data to cloud storage
- ✅ Sync inventory with Notion
- ✅ Search the web for prices
- ✅ Use any MCP-compatible service

---

## Time Savings with Connected Tools

### Gmail Integration

| Task | Without Gmail | With Gmail | Savings |
|------|---------------|------------|---------|
| Email daily report | Manual compose & send (10 min) | Automatic (0 min) | 10 min |
| Send invoice to customer | Copy, paste, attach (5 min) | "Email invoice" (30 sec) | 4.5 min |
| Weekly supplier emails | Type each (20 min) | Scheduled (0 min) | 20 min |
| **Daily Total** | 35 min | < 1 min | **34 min** |

> **Monthly Savings: ~17 hours**

### Google Drive Integration

| Task | Without Drive | With Drive | Savings |
|------|---------------|------------|---------|
| Backup inventory list | Export → Upload → Organize (15 min) | "Backup to Drive" (1 min) | 14 min |
| Share reports | Export → Email (10 min) | "Save and share" (1 min) | 9 min |
| Store invoices | Manual filing (20 min/week) | Automatic (0 min) | 20 min |

### Notion Integration

| Task | Without Notion | With Notion | Savings |
|------|----------------|-------------|---------|
| Update inventory database | Manual copy (30 min) | Auto sync (0 min) | 30 min |
| Share with team | Export → Import (15 min) | Real-time (0 min) | 15 min |

---

## Built-in Tools

These tools are available immediately without any setup:

### 1. Inventory Tools
```
list_items      - View all inventory items
create_item     - Add new items
update_item     - Modify existing items
search_items    - Find items by name/category
delete_item     - Remove items (with confirmation)
```

**Example:**
```
You: Show me all electronics under Rs. 1000

AI: [Uses list_items + filter]

    Found 12 electronics items under Rs. 1000:
    1. USB Cable - Rs. 150 (45 in stock)
    2. Phone Stand - Rs. 299 (30 in stock)
    ...
```

### 2. Billing Tools
```
create_bill     - Generate invoices
get_bill        - Retrieve bill details
list_bills      - View bill history
export_invoice  - Download invoice PDF
```

**Example:**
```
You: Create a bill for 5 chargers and 3 cables for Ahmed

AI: [Uses create_bill]

    ✅ Invoice #INV-2025-0089 created
    Customer: Ahmed
    Total: Rs. 2,950

    Stock automatically updated.
```

### 3. Analytics Tools
```
inventory_health    - Stock levels, alerts, categories
sales_analytics     - Revenue, trends, comparisons
category_breakdown  - Category-wise analysis
trend_analysis      - Historical trends
```

**Example:**
```
You: How did last week compare to the week before?

AI: [Uses sales_analytics]

    📊 Week-over-Week Comparison:

    Last Week: Rs. 45,000
    Previous: Rs. 38,000
    Growth: +18.4% 📈

    Top performer: Winter collection (+45%)
```

### 4. Export Tools
```
export_csv      - Export data to CSV
export_excel    - Export to Excel format
export_pdf      - Generate PDF reports
```

### 5. File Search Tools
```
search_files    - Semantic search in uploaded files
get_file        - Retrieve specific file
list_files      - View all uploaded files
```

**Example:**
```
You: Find the invoice where we ordered Samsung products

AI: [Uses search_files with semantic search]

    Found 2 matching files:
    1. samsung_order_dec2024.pdf - Order #PO-2024-156
       Rs. 125,000 for Samsung accessories

    2. samsung_invoice_jan2025.pdf - Invoice #INV-5678
       Rs. 85,000 for phone cases
```

### 6. Web Search
```
web_search      - Search the internet
```

**Example:**
```
You: What's the current market price for Samsung Galaxy S24 cases?

AI: [Uses web_search]

    Current market prices for Samsung Galaxy S24 cases:
    • Basic silicone: Rs. 200-400
    • Premium leather: Rs. 800-1,500
    • Branded (Samsung): Rs. 2,000-3,500

    Your current price (Rs. 450) is competitive
    for basic cases.
```

---

## Pre-configured Connectors

These connectors are ready to use with one-click OAuth:

### Gmail Connector

**What It Does:**
- Send emails from your Gmail account
- Attach files and reports
- Schedule email delivery

**Setup:**
1. Go to **Settings → Connectors**
2. Click **Connect Gmail**
3. Sign in with Google
4. Grant email permissions
5. Done!

**Example Uses:**
```
"Email daily sales report to manager@company.com"
"Send invoice to customer.ahmed@email.com"
"Every Monday, email restock list to supplier"
```

**Permissions Required:**
- Send emails on your behalf
- Read email addresses (for auto-complete)

---

### Google Drive Connector

**What It Does:**
- Store files in your Drive
- Organize in folders
- Share files and reports
- Backup inventory data

**Setup:**
1. Go to **Settings → Connectors**
2. Click **Connect Google Drive**
3. Sign in with Google
4. Grant Drive permissions
5. Done!

**Example Uses:**
```
"Save this report to Google Drive"
"Backup inventory to Drive/IMS Backups folder"
"Store all invoices in Drive automatically"
```

**Permissions Required:**
- Create files in Drive
- Manage Drive folders
- Share files (optional)

---

### Notion Connector

**What It Does:**
- Sync inventory to Notion databases
- Create pages from reports
- Update Notion tables automatically

**Setup:**
1. Go to **Settings → Connectors**
2. Click **Connect Notion**
3. Authorize IMS access
4. Select workspace and pages
5. Done!

**Example Uses:**
```
"Sync inventory to my Notion database"
"Create a Notion page with monthly report"
"Update Notion when stock changes"
```

**Permissions Required:**
- Read and write Notion pages
- Access to selected databases

---

## Custom MCP Connectors

### What is MCP?

MCP (Model Context Protocol) is an open standard that lets AI assistants connect to any compatible service. Think of it as "USB for AI" — any MCP server can plug into IMS.

### Why Custom Connectors?

Pre-configured connectors cover common needs, but you might need:
- Internal company tools
- Industry-specific services
- Custom databases
- Proprietary systems

### Adding a Custom Connector

**Step 1: Get MCP Server URL**
Your service needs an MCP endpoint. Examples:
```
https://your-crm.com/mcp/
https://internal-api.company.com/mcp/v1/
http://localhost:3001/mcp/
```

**Step 2: Add Connector**
1. Go to **Settings → Connectors**
2. Click **Add Custom Connector**
3. Enter details:
   - Name: "My CRM"
   - Server URL: https://your-crm.com/mcp/
   - Authentication: API Key or OAuth

**Step 3: Test Connection**
Click **Test** to verify:
- Server is reachable
- Authentication works
- Tools are discovered

**Step 4: Start Using**
```
You: Show customers from CRM who haven't ordered in 30 days

AI: [Uses custom CRM connector]

    Found 15 inactive customers:
    1. ABC Company - Last order: Dec 15
    2. XYZ Store - Last order: Dec 10
    ...

    Want me to draft follow-up emails?
```

---

### Custom Connector Examples

#### Example 1: ERP Integration

```yaml
Name: SAP Connector
URL: https://sap.company.com/mcp/
Auth: OAuth2
Tools discovered:
  - get_purchase_orders
  - create_goods_receipt
  - check_material_stock
  - get_vendor_info
```

**Usage:**
```
You: Check SAP for pending purchase orders

AI: [Uses SAP connector]

    3 pending POs in SAP:
    1. PO-2025-0045 - Electronics - Rs. 125,000
    2. PO-2025-0046 - Garments - Rs. 85,000
    3. PO-2025-0047 - Office Supplies - Rs. 15,000
```

#### Example 2: Accounting Software

```yaml
Name: QuickBooks Connector
URL: https://qb-mcp.company.com/
Auth: API Key
Tools discovered:
  - create_invoice
  - get_account_balance
  - record_expense
  - generate_report
```

**Usage:**
```
You: Create a QuickBooks invoice for today's sales

AI: [Uses QuickBooks connector]

    ✅ QuickBooks Invoice Created
    Invoice #: QBI-2025-0234
    Amount: Rs. 45,600
    Synced with IMS bill #INV-2025-0089
```

#### Example 3: Shipping Service

```yaml
Name: FedEx Tracker
URL: https://fedex-mcp.logistics.com/
Auth: API Key
Tools discovered:
  - create_shipment
  - track_package
  - get_rates
  - schedule_pickup
```

**Usage:**
```
You: Track the shipment for order #12345

AI: [Uses FedEx connector]

    📦 Tracking: FX123456789

    Status: In Transit
    Location: Karachi Hub
    Expected Delivery: Jan 20, 2025, 2:00 PM

    History:
    • Jan 17, 10:00 AM - Picked up
    • Jan 17, 4:00 PM - Arrived at hub
    • Jan 18, 8:00 AM - Out for delivery
```

---

## Managing Connectors

### View Connected Services

**Settings → Connectors** shows:

```
┌────────────────────────────────────────────────────────────────┐
│ CONNECTED SERVICES                                             │
├────────────────────────────────────────────────────────────────┤
│ ✅ Gmail                                                       │
│    Connected as: manager@company.com                          │
│    Last used: Today, 10:30 AM                                 │
│    [Disconnect] [Test]                                        │
│                                                                │
│ ✅ Google Drive                                                │
│    Connected as: manager@company.com                          │
│    Storage used: 2.3 GB                                       │
│    [Disconnect] [Test]                                        │
│                                                                │
│ ⚠️ Notion                                                     │
│    Token expired - Reconnect required                         │
│    [Reconnect]                                                │
│                                                                │
│ ✅ Custom: SAP Connector                                       │
│    URL: https://sap.company.com/mcp/                          │
│    Tools: 4 available                                         │
│    [Disconnect] [Test] [Edit]                                 │
└────────────────────────────────────────────────────────────────┘
```

### Disconnect a Service

1. Find the connector in Settings
2. Click **Disconnect**
3. Confirm removal
4. Tokens are deleted securely

### Refresh OAuth Tokens

Most connectors auto-refresh tokens. If one expires:
1. You'll see ⚠️ warning
2. Click **Reconnect**
3. Sign in again
4. Done!

---

## Security

### How We Protect Your Data

1. **Encrypted Storage**
   - All credentials encrypted at rest
   - AES-256 encryption
   - Secure key management

2. **OAuth Best Practices**
   - Never store passwords
   - Use refresh tokens
   - Minimal permission scopes

3. **User Isolation**
   - Your connectors are only visible to you
   - No cross-user access
   - Separate encryption keys

4. **Token Rotation**
   - Tokens refreshed automatically
   - Short-lived access tokens
   - Revocation on disconnect

### What Permissions Are Shared

| Connector | We Can | We Cannot |
|-----------|--------|-----------|
| Gmail | Send emails on your behalf | Read your inbox |
| Drive | Create/manage files in IMS folder | Access other folders |
| Notion | Update connected databases | Access private pages |
| Custom | Only what you configure | Nothing beyond scope |

---

## Troubleshooting

### Connector Not Working

**Check:**
1. Is the connector status "Connected"?
2. Has the OAuth token expired?
3. Is the service URL accessible?
4. Are permissions correct?

### Gmail Emails Not Sending

**Solutions:**
1. Reconnect Gmail
2. Check spam folder
3. Verify recipient address
4. Check Gmail sending limits

### Custom Connector Fails

**Debug Steps:**
1. Test URL manually
2. Verify API key/credentials
3. Check MCP server logs
4. Try simpler query first

### OAuth Redirect Issues

**Solutions:**
1. Clear browser cookies
2. Try incognito mode
3. Check popup blocker
4. Use different browser

---

## Best Practices

### 1. Connect Essential Services First
```
Priority 1: Gmail (for notifications)
Priority 2: Drive (for backups)
Priority 3: Business-specific tools
```

### 2. Regular Health Checks
Monthly: Review connector status
Action: Reconnect expired tokens

### 3. Minimal Permissions
Only grant what's needed:
```
❌ Full Drive access
✅ IMS folder access only
```

### 4. Document Custom Connectors
Keep track of:
- Server URLs
- Authentication methods
- Available tools
- Contact person for issues

### 5. Test Before Production Use
```
You: Test Gmail connector

AI: Testing Gmail...
    ✅ Connection successful
    ✅ Can send emails
    ✅ Account: manager@company.com
```

---

## Building Custom MCP Servers

For developers who want to create their own connectors:

### Basic MCP Server Structure

```python
from mcp_server import MCPServer, Tool

server = MCPServer(name="My Custom Service")

@server.tool("get_customers")
def get_customers(limit: int = 10):
    """Retrieve customer list"""
    # Your logic here
    return customers

@server.tool("create_order")
def create_order(customer_id: str, items: list):
    """Create a new order"""
    # Your logic here
    return order

server.run(port=3001)
```

### Expose via HTTPS

```python
# For production
server.run(
    host="0.0.0.0",
    port=443,
    ssl_cert="/path/to/cert.pem",
    ssl_key="/path/to/key.pem"
)
```

### Add Authentication

```python
@server.middleware
def authenticate(request):
    api_key = request.headers.get("X-API-Key")
    if not validate_api_key(api_key):
        raise UnauthorizedError()
```

---

## Summary

| Feature | Without Connectors | With Connectors |
|---------|-------------------|-----------------|
| Email reports | Manual | Automatic |
| File backup | Manual upload | One command |
| External data | Not available | Integrated |
| Automation | Limited | Unlimited |
| Time spent | Hours | Minutes |

**Connect your first tool today and unlock the full power of IMS!**

---

[← Back to Main Docs](./index.md) | [Developer Guide →](./developer.md)
