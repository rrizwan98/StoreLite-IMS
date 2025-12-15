# Enhanced Agent System Prompt - Agent Tool Usage Guide

## Overview

The agent now has a comprehensive system prompt that guides it to intelligently use MCP tools to answer user questions about inventory and billing operations. The agent is responsible for:

1. **Understanding user queries** - Parse what information the user needs
2. **Calling appropriate tools** - Execute MCP tools to fetch current data
3. **Processing results** - Format tool results into clear answers
4. **Providing data-driven responses** - Base all answers on actual database data

## System Prompt Structure

### Core Responsibilities
The agent understands it must:
- Answer questions by calling the appropriate tools
- Provide accurate, data-driven responses based on tool results
- Execute inventory and billing operations when requested
- Guide users through multi-step processes

### Tool Usage Guidelines

#### For Inventory Queries
When users ask about items, stock, or categories:
```
User Query: "tell me the grocery items in db?"
Agent Action: Call inventory_list_items(category="Grocery")
Response: Returns specific items with names, quantities, prices, categories
```

#### For Adding Items
When users want to add new inventory:
```
User Query: "Add a new widget"
Agent Action: Ask for required fields (name, category, unit, price, stock)
Then Call: inventory_add_item(name="widget", category="...", ...)
Response: Confirms addition with item ID
```

#### For Updating Items
When users want to modify inventory:
```
User Query: "Update item quantity to 100"
Agent Action: Ask which item if unclear, then call inventory_update_item()
Response: Confirms update with new values
```

#### For Deleting Items
When users request deletion:
```
User Query: "Delete item X"
Agent Action: Ask for confirmation (destructive action)
If confirmed: Call inventory_delete_item(item_id=...)
Response: Confirms deletion
```

#### For Billing Operations
When users need bill management:
```
User Query: "Create a bill for John Smith with items X and Y"
Agent Action: Ask for confirmation (destructive action)
If confirmed: Call billing_create_bill(customer_name="John", items=[...])
Response: Returns bill details with total amount
```

## Response Strategy

The agent follows a structured approach:

1. **Parse the question** - Understand what data is needed
2. **Call appropriate tool(s)** - Fetch current data from database
3. **Format results** - Convert tool output into readable response
4. **Provide details** - Include specific numbers, names, categories, IDs
5. **Handle dependencies** - Call multiple tools in logical order if needed

## Key Behaviors

### Always Fetch Fresh Data
- **No assumptions** - The agent queries the database for current information
- **Real-time accuracy** - Every response is based on latest data
- **Complete information** - Provides full details from tool results

### Clear and Specific
- **Named items** - Lists items by name, not just "item 1, item 2"
- **Quantities and prices** - Includes actual numbers
- **Categories** - Specifies which category each item belongs to
- **Confirmation details** - Shows what was added/modified with confirmation

### Safe Operations
- **Confirmation required** - Asks before destructive actions (billing, deletion)
- **User verification** - Ensures user really wants to proceed
- **Detailed confirmation** - Shows exactly what will be deleted/created

### Concise Responses
- **To the point** - Focuses on answering the question
- **Well-formatted** - Uses lists, bullet points, or tables
- **Not verbose** - Avoids unnecessary explanation

## Example Interactions

### Query Example 1: List All Items
```
User: "What items do we have?"
Agent:
  1. Calls: inventory_list_items()
  2. Receives: List of all items with details
  3. Responds: "We have X items in stock:
     - Item A (Category: Electronics, Stock: 50 units, Price: $25)
     - Item B (Category: Supplies, Stock: 100 units, Price: $5)
     ..."
```

### Query Example 2: Category-Specific Query
```
User: "How many groceries are in stock?"
Agent:
  1. Calls: inventory_list_items(category="Grocery")
  2. Receives: List of grocery items
  3. Calculates: Total units
  4. Responds: "We have 3 grocery items with 250 total units in stock:
     - Rice (100 units, $2/unit)
     - Wheat (75 units, $1.50/unit)
     - Sugar (75 units, $3/unit)"
```

### Operation Example: Create Bill
```
User: "Create a bill for customer Alice with item X (qty 5) and item Y (qty 3)"
Agent:
  1. Asks: "Are you sure you want to create a bill for Alice with 5x Item X and 3x Item Y?"
  2. User confirms: "yes"
  3. Calls: billing_create_bill(customer_name="Alice", items=[...])
  4. Receives: Bill ID, total amount, item details
  5. Responds: "Bill created successfully!
     Bill ID: 123
     Customer: Alice
     Items: 5x Item X + 3x Item Y
     Total: $XXX.XX"
```

### Operation Example: Delete Item
```
User: "Delete item 42"
Agent:
  1. Asks: "Are you sure you want to delete item 42? This cannot be undone."
  2. User confirms: "yes"
  3. Calls: inventory_delete_item(item_id=42)
  4. Responds: "Item 42 has been permanently deleted."
```

## How This Improves Agent Behavior

### Before (Old Prompt)
- Agent might not call tools consistently
- Responses could be generic or assumption-based
- Missing specific data in answers
- Uncertain behavior on new query types

### After (New Prompt)
- Agent actively uses tools for all queries
- Responses include specific data from database
- Proper handling of all operation types
- Consistent, predictable behavior
- Clear guidance on when to ask for confirmation

## Tool Mapping

| User Intent | Tool to Call | Parameters |
|-------------|-------------|------------|
| List items | inventory_list_items | category (optional) |
| Add item | inventory_add_item | name, category, unit, unit_price, stock_qty |
| Update item | inventory_update_item | item_id, name, unit_price, stock_qty |
| Delete item | inventory_delete_item | item_id |
| List bills | billing_list_bills | (none) |
| Get bill details | billing_get_bill | bill_id |
| Create bill | billing_create_bill | customer_name, items array |

## Safety Mechanisms

### Destructive Action Confirmation
The agent is instructed to ALWAYS ask for confirmation before:
- Creating bills (financial impact)
- Deleting items (data loss)
- Clearing stock

### Data Validation
The agent is instructed to:
- Never assume or make up data
- Always fetch from database before responding
- Require necessary parameters before executing
- Ask for clarification on ambiguous requests

## Implementation

**File:** `backend/app/agents/agent.py:666-746`

**Method:** `_generate_system_prompt()`

The system prompt is generated dynamically and provided to the OpenAI Agents SDK LiteLLM model on agent initialization.

## Testing

The improved system prompt has been validated to:
- ✓ Work with all existing tests
- ✓ Properly handle inventory queries
- ✓ Request confirmations for destructive actions
- ✓ Call appropriate MCP tools
- ✓ Process tool results correctly

All tests pass: 3/3

## Future Enhancements

Potential improvements:
1. Add advanced filtering options
2. Support for search by multiple criteria
3. Inventory forecasting based on trends
4. Automatic low-stock alerts
5. Customer history and preferences
6. Multi-store inventory management

