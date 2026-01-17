# AI Agent Guide

> Your intelligent business assistant that understands natural language and executes complex inventory operations in seconds.

## Overview

The IMS AI Agent is powered by Google Gemini 2.5 Flash, optimized for business operations. It understands your inventory context, remembers conversations, and can perform multi-step tasks automatically.

**You don't need to build your own AI agent.** IMS provides a pre-configured, business-ready assistant that works immediately.

---

## What Can the AI Agent Do?

### Inventory Management
| Task | What You Say | What Happens |
|------|--------------|--------------|
| Add items | "Add 50 blue t-shirts at Rs. 350" | Item created with all details |
| Update stock | "Update rice stock to 200 kg" | Stock quantity updated |
| Check inventory | "How many phones do I have?" | Instant stock count |
| Search items | "Show all items under Rs. 500" | Filtered list displayed |
| Category view | "List all grocery items" | Category-wise inventory |

### Billing & Invoices
| Task | What You Say | What Happens |
|------|--------------|--------------|
| Create bill | "Bill 5 shirts and 2 pants for Ahmed" | Invoice generated |
| View bills | "Show today's bills" | Bill history displayed |
| Calculate totals | "What's the total for 10 items of each?" | Automatic calculation |
| Stock deduction | Automatic | Stock reduced on billing |

### Analytics & Reports
| Task | What You Say | What Happens |
|------|--------------|--------------|
| Sales report | "Show last week's sales" | Sales data with charts |
| Revenue analysis | "What's my total revenue this month?" | Revenue breakdown |
| Best sellers | "Top 5 selling items" | Ranked item list |
| Inventory health | "Show low stock items" | Stock alerts |
| Trends | "Compare this week vs last week" | Comparative analysis |

### File Operations
| Task | What You Say | What Happens |
|------|--------------|--------------|
| Upload files | Attach CSV/Excel in chat | Data imported |
| Search files | "Find invoice for order 123" | Semantic file search |
| Export data | "Export inventory to CSV" | Downloadable file |

### Email Integration
| Task | What You Say | What Happens |
|------|--------------|--------------|
| Send reports | "Email daily report to manager@company.com" | Report sent via Gmail |
| Invoice delivery | "Send invoice to customer" | Invoice emailed |

---

## Time Savings Comparison

### Adding Inventory Items

**Manual Process (Traditional):**
1. Open inventory module *(10 sec)*
2. Click "Add New Item" *(5 sec)*
3. Fill form: name, category, unit, price, quantity *(60 sec)*
4. Click Save *(5 sec)*
5. Repeat for each item...

**Total for 10 items: ~13 minutes**

**With AI Agent:**
```
"Add these items:
- 50 kg Basmati Rice @ Rs. 180/kg
- 30 liters Cooking Oil @ Rs. 350/liter
- 100 pieces Sugar packets @ Rs. 75 each
..."
```
**Total for 10 items: ~2 minutes**

> **Time Saved: 11 minutes** per batch entry

---

### Generating Reports

**Manual Process (Traditional):**
1. Navigate to Reports section *(10 sec)*
2. Select report type *(10 sec)*
3. Set date filters *(20 sec)*
4. Click Generate *(5 sec)*
5. Wait for processing *(30 sec)*
6. Export if needed *(20 sec)*

**Total: ~2 minutes per report**

**With AI Agent:**
```
"Show me last month's sales with top items and email it to me"
```
**Total: 30 seconds**

> **Time Saved: 1.5 minutes** per report

---

### Daily Operations Example

| Operation | Manual Time | AI Agent | Savings |
|-----------|-------------|----------|---------|
| Morning inventory check | 20 min | 2 min | 18 min |
| Process 10 bills | 30 min | 10 min | 20 min |
| End-of-day report | 15 min | 1 min | 14 min |
| Low stock alerts | 10 min | Automatic | 10 min |
| **Daily Total** | **75 min** | **13 min** | **62 min** |

> **Monthly Time Saved: ~31 hours**

---

## Real Conversation Examples

### Example 1: Complete Inventory Session

```
You: Good morning! What's my inventory status?

AI: Good morning! Here's your inventory overview:
    📦 Total Items: 156
    💰 Total Value: Rs. 2,45,000
    ⚠️ Low Stock Alerts: 8 items
    📈 Top Category: Electronics (45 items)

    Would you like details on any category?

You: Show me the low stock items

AI: Here are items with stock below 10 units:

    1. Samsung Charger - 5 units (Min: 20)
    2. iPhone Cable - 3 units (Min: 15)
    3. Laptop Bag - 8 units (Min: 10)
    4. Mouse Pad - 2 units (Min: 25)
    ...

    Should I create a reorder list?

You: Yes, and email it to supplier@electronics.com

AI: ✅ Reorder list created and emailed to supplier@electronics.com

    Items included:
    - Samsung Charger: Order 50 units
    - iPhone Cable: Order 30 units
    - Laptop Bag: Order 20 units
    - Mouse Pad: Order 50 units

    Total estimated cost: Rs. 45,000
```

**Traditional way:** 45+ minutes of clicking, exporting, composing email
**With AI:** 3 minutes of conversation

---

### Example 2: Quick Billing Session

```
You: New bill for customer Rashid

AI: Starting new bill for Rashid. What items?

You: 3 blue shirts, 2 black pants, and 1 leather belt

AI: Bill created:
    ┌─────────────────────────────────────┐
    │ Customer: Rashid                    │
    │ Date: January 17, 2025              │
    ├─────────────────────────────────────┤
    │ 3x Blue Shirt      @ 850   = 2,550  │
    │ 2x Black Pants     @ 1,200 = 2,400  │
    │ 1x Leather Belt    @ 650   = 650    │
    ├─────────────────────────────────────┤
    │ Subtotal                    = 5,600 │
    │ Tax (5%)                    = 280   │
    │ TOTAL                       = 5,880 │
    └─────────────────────────────────────┘

    Invoice #INV-2025-0089

    Stock updated automatically.
    Print invoice?

You: Yes, and also send to rashid@email.com

AI: ✅ Invoice printed
    ✅ Invoice emailed to rashid@email.com
```

---

### Example 3: Analytics Deep Dive

```
You: How did January compare to December?

AI: 📊 January vs December Comparison:

    Revenue:
    • December: Rs. 4,50,000
    • January: Rs. 5,20,000
    • Growth: +15.5% 📈

    Top Performing:
    • Best Item: Winter Jackets (+45% sales)
    • Best Category: Garments (+22%)

    Concerns:
    • Electronics down 8%
    • 12 items not sold in January

    Would you like a detailed breakdown?

You: Why are electronics down?

AI: Analyzing electronics category...

    Key findings:
    1. Phone accessories: -15% (competitor opened nearby)
    2. Cables: -20% (seasonal - post-holiday dip)
    3. Headphones: +5% (new arrival doing well)

    Recommendation:
    Consider a 10% discount on slow-moving accessories
    to clear inventory before new stock arrives.
```

---

## AI Agent Capabilities

### Natural Language Understanding
The AI understands:
- Casual language: "gimme the sales report"
- Formal requests: "Please generate a comprehensive sales analysis"
- Context: "same thing for last week" (remembers previous query)
- Corrections: "actually make it 100, not 50"

### Smart Confirmations
For critical operations, AI asks for confirmation:

```
You: Delete all out-of-stock items

AI: ⚠️ This will permanently delete 23 items with 0 stock.

    Items to be deleted:
    - Old Model Phone Cases (12 variants)
    - Discontinued Accessories (8 items)
    - Seasonal Items (3 items)

    Are you sure? (yes/no)

You: yes

AI: ✅ 23 items deleted successfully.
    Backup created: backup_2025-01-17.json
```

### Multi-Step Tasks
Execute complex workflows in one request:

```
You: Check low stock items, create reorder list, calculate total cost,
     and schedule email to supplier for Monday 9 AM

AI: ✅ Task completed:

    1. Found 15 low-stock items
    2. Created reorder list (attached)
    3. Total cost: Rs. 1,25,000
    4. Scheduled email for Monday, Jan 20, 9:00 AM
       To: supplier@company.com
       Subject: Reorder Request - January Week 3
```

---

## Available Tools

The AI Agent has access to these tools:

| Tool | Purpose | Example Use |
|------|---------|-------------|
| **list_items** | View inventory | "Show all items" |
| **create_item** | Add new items | "Add 50 shirts" |
| **update_item** | Modify items | "Update price to 500" |
| **search_items** | Find specific items | "Find items with 'phone'" |
| **create_bill** | Generate invoices | "Create bill for Ahmed" |
| **get_analytics** | Business insights | "Monthly revenue" |
| **send_email** | Gmail integration | "Email report" |
| **search_files** | Find in uploads | "Find invoice 123" |
| **export_data** | Download data | "Export to CSV" |
| **web_search** | Search internet | "Latest market prices" |

---

## Tips for Best Results

### Be Specific
```
❌ "Add stuff"
✅ "Add 50 Samsung Galaxy S24 cases at Rs. 450 each in Electronics category"
```

### Use Context
```
You: Show Electronics inventory
AI: [shows 45 items]
You: Filter by price under 1000  ← AI understands context
AI: [shows 12 items under Rs. 1000 in Electronics]
```

### Chain Commands
```
"Add 100 new items from the attached Excel,
 show me the summary,
 and flag any duplicates"
```

### Let AI Suggest
```
You: What should I do about slow inventory?

AI: Based on your data, I recommend:
    1. 15% discount on items not sold in 30 days
    2. Bundle slow items with popular ones
    3. Clear 8 obsolete items (list attached)
```

---

## File Processing

### Supported File Types
- **CSV**: Inventory lists, bulk data
- **Excel (.xlsx)**: Complex spreadsheets
- **PDF**: Invoices, documents
- **Images**: Product photos, receipts

### Upload and Process

```
You: [Attaches inventory.csv]
     Import this inventory file

AI: Processing inventory.csv...

    ✅ Found 150 items
    ⚠️ 3 items have missing prices
    ⚠️ 5 items already exist (will update)

    Preview:
    | Name          | Category | Price | Stock |
    |---------------|----------|-------|-------|
    | Blue T-Shirt  | Garments | 350   | 50    |
    | Black Jeans   | Garments | 899   | 30    |
    ...

    Proceed with import?

You: Yes, set missing prices to 0

AI: ✅ 150 items imported
    • 142 new items created
    • 5 existing items updated
    • 3 items imported with Rs. 0 price (review later)
```

---

## Session Continuity

Your conversation history is saved:

```
You: (Monday) Add 100 shirts

AI: ✅ Added 100 shirts

--- Next Day ---

You: (Tuesday) How many shirts do I have now?

AI: You have 85 shirts remaining.
    15 were sold since you added them yesterday.
```

---

## Error Handling

The AI gracefully handles errors:

```
You: Add -50 items

AI: ❌ Cannot add negative quantity.
    Did you mean to reduce stock? Try:
    "Reduce shirt stock by 50"

You: Bill 100 phones

AI: ⚠️ You only have 45 phones in stock.
    Options:
    1. Bill available 45 phones
    2. Cancel this bill
    3. Add backorder for 55 phones

    What would you like to do?
```

---

## Why Not Build Your Own AI Agent?

| Building Your Own | Using IMS AI Agent |
|-------------------|-------------------|
| 3-6 months development | Ready to use today |
| API costs add up | Included in platform |
| Need ML expertise | No technical knowledge needed |
| Maintenance overhead | Always updated |
| Training required | Pre-trained on inventory ops |
| Integration work | Built-in integrations |

**IMS AI Agent saves you:**
- Development time: 500+ hours
- API costs: Rs. 50,000+/month
- Maintenance: Ongoing effort

---

## Getting Started

1. **Open Chat**: Click the chat icon on any page
2. **Start Talking**: Type your first message
3. **Explore**: Try the example commands above
4. **Connect Tools**: Add Gmail, Drive for more power

---

*The AI Agent is your business partner that never sleeps, never forgets, and always gets faster.*

[← Back to Main Docs](./index.md) | [Scheduler Guide →](./scheduler.md)
