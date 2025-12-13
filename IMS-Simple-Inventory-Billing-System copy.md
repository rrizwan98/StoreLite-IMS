# **📦 Project Name**

**StoreLite IMS** – Simple Inventory & Billing System

---

## **1\. High-Level Overview**

**Goal**  
 A minimal, extensible **inventory \+ billing system** that:

* Supports **multiple store types** (grocery, utilities, beauty, garments, etc.)

* Has **two main workflows**:

  1. **Inventory UI** – for adding/updating items in the database (admin / owner side)

  2. **Billing UI** – for the salesperson to search items, enter quantity, and print an invoice

**Phases**

1. **Phase 1 – Console Python \+ PostgreSQL**

   * Manage inventory from a CLI (add/update/list items in PostgreSQL)

   * Create bills from the CLI (cart, totals, simple invoice printout)

2. **Phase 2 – FastAPI Backend (still PostgreSQL)**

   * Wrap the same database & logic in a REST API

   * Test via Swagger docs / Postman / browser

3. **Phase 3 – Next.js Frontend**

   * 2 pages:

     * `/admin` → Inventory management

     * `/pos` → Billing / POS screen

   * Connect frontend to FastAPI → full web-based inventory management system

---

## **2\. Core Requirements**

### **Functional Requirements**

1. **Inventory Management**

   * Add item:

     * Name (e.g., Sugar, Flour)

     * Category (grocery, garments, etc.)

     * Unit (kg, liter, piece)

     * Unit price

     * Current stock quantity

   * List / search items by:

     * Name

     * Category

   * Update item:

     * Price

     * Stock quantity

     * Optionally rename / recategorize

2. **Billing / Invoice**

   * Start a new bill for a customer

   * Search items (by name substring)

   * For each line item:

     * Select item

     * Enter quantity

     * System calculates line total (price × quantity)

   * Calculate bill total:

     * Subtotal

     * (Later: discount, tax fields if needed)

   * Adjust stock in inventory (subtract sold quantity)

   * Display a **printable invoice** (console / web)

3. **Multi-store (future-ready)**

   * For now:

     * Optional `store_name` field on bills

   * Later:

     * Dedicated `stores` table and per-store stock

### **Non-Functional Requirements**

* Simple local development setup using **PostgreSQL**, not SQLite.

* Use a proper PostgreSQL driver / ORM:

  * Phase 1 can use `psycopg2` directly or SQLAlchemy as an ORM. ([DataCamp](https://www.datacamp.com/tutorial/tutorial-postgresql-python?utm_source=chatgpt.com))

* Easy to extend (clean separation of database layer, business logic, and UI/API).

---

## **3\. Data Model (PostgreSQL Schema)**

We’ll use **PostgreSQL** from Phase 1 onward. A typical Python \+ Postgres stack uses `psycopg2` or SQLAlchemy; both work well with FastAPI and are widely documented. ([FastAPI](https://fastapi.tiangolo.com/tutorial/sql-databases/?utm_source=chatgpt.com))

### **3.1 Tables**

#### **`items` (inventory)**

| Column | Type | Description |
| ----- | ----- | ----- |
| id | SERIAL PRIMARY KEY | Item ID |
| name | TEXT NOT NULL | Item name (Sugar, Flour, etc.) |
| category | TEXT | grocery / garments / beauty / etc. |
| unit | TEXT | kg / liter / piece, etc. |
| unit\_price | NUMERIC(12,2) | Price per unit |
| stock\_qty | NUMERIC(12,3) | Current quantity in stock |
| is\_active | BOOLEAN | TRUE \= active, FALSE \= inactive |
| created\_at | TIMESTAMPTZ | Creation timestamp |
| updated\_at | TIMESTAMPTZ | Last update timestamp |

This is a typical inventory-style table: product definition \+ stock quantity and pricing. ([Python in Plain English](https://python.plainenglish.io/adding-a-production-grade-database-to-your-fastapi-project-local-setup-50107b10d539?utm_source=chatgpt.com))

#### **`bills` (invoice header)**

| Column | Type | Description |
| ----- | ----- | ----- |
| id | SERIAL PRIMARY KEY | Bill ID |
| customer\_name | TEXT | Optional |
| store\_name | TEXT | Optional |
| total\_amount | NUMERIC(12,2) | Final total |
| created\_at | TIMESTAMPTZ | Bill creation time |

#### **`bill_items` (invoice line items)**

| Column | Type | Description |
| ----- | ----- | ----- |
| id | SERIAL PRIMARY KEY | Line item ID |
| bill\_id | INT NOT NULL | FK → `bills.id` |
| item\_id | INT NOT NULL | FK → `items.id` |
| item\_name | TEXT | Snapshot of item name at sale time |
| unit\_price | NUMERIC(12,2) | Snapshot of unit price at sale time |
| quantity | NUMERIC(12,3) | Quantity sold |
| line\_total | NUMERIC(12,2) | unit\_price × quantity |

This gives a clean separation between product master data (`items`) and historical invoices (`bills` \+ `bill_items`), similar to many real-world billing/ERP schemas. ([TestDriven.io](https://testdriven.io/blog/fastapi-postgres-websockets/?utm_source=chatgpt.com))

---

## **4\. Phase 1 – Console-Based Python App (with PostgreSQL)**

### **4.1 Tech Stack**

* Python 3.x

* PostgreSQL (local or cloud)

* Python DB layer:

  * Option A: **`psycopg2`** (direct SQL) ([DataCamp](https://www.datacamp.com/tutorial/tutorial-postgresql-python?utm_source=chatgpt.com))

  * Option B: **SQLAlchemy** ORM (recommended if you want to reuse models easily in FastAPI) ([FastAPI](https://fastapi.tiangolo.com/tutorial/sql-databases/?utm_source=chatgpt.com))

For clarity, the docs can treat the DB access as an abstraction (`db.py`), and you can choose whether the implementation uses psycopg2 or SQLAlchemy internally.

### **4.2 Example Folder Structure**

storelite\_phase1/  
  ├─ main.py          \# entry point, top-level menus  
  ├─ db.py            \# PostgreSQL connection & table creation  
  ├─ inventory.py     \# inventory CRUD functions  
  ├─ billing.py       \# billing workflow & invoice printing  
  └─ schema.sql       \# optional: raw SQL for initial table setup

### **4.3 Inventory Features (Console)**

**Main Menu (CLI):**

1. Manage Inventory

2. Create New Bill

3. Exit

**Manage Inventory Submenu:**

1. Add new item

2. List all items

3. Search item by name

4. Update item (price / stock)

5. Back

**Add New Item – Flow:**

* Prompt user for:

  * `name`

  * `category`

  * `unit` (kg, piece, etc.)

  * `unit_price`

  * `stock_qty`

* Validate:

  * `unit_price ≥ 0`

  * `stock_qty ≥ 0`

* Call `db.py` function to `INSERT` into `items`.

* Print success message.

**List Items – Flow:**

Run:

 SELECT id, name, category, unit, unit\_price, stock\_qty  
FROM items  
WHERE is\_active \= TRUE  
ORDER BY name;

*   
* Print as a simple table:

  * ID, Name, Category, Unit, Price, Stock

**Search Item by Name – Flow:**

* Ask user for a search string.

Query:

 SELECT id, name, category, unit, unit\_price, stock\_qty  
FROM items  
WHERE is\_active \= TRUE  
  AND name ILIKE %search\_term%;

*   
* Show matching rows.

**Update Item – Flow:**

* Ask for `item_id`.

* Fetch current item.

* For each updatable field (price, stock):

  * Ask for new value (or press Enter to keep old).

* Run `UPDATE` in PostgreSQL.

* Print updated info.

---

### **4.4 Billing / Invoice Features (Console)**

**Create New Bill – Flow:**

1. Start a new bill (in memory).

2. Loop to add line items:

   * Prompt for search text → query `items` table with `ILIKE`.

   * Show matching items with IDs.

   * Ask user to select an `item_id`.

   * Ask for quantity.

   * Check stock:

     * If requested `qty > stock_qty` → warn and re-enter.

   * Compute:

     * `line_total = unit_price * quantity`

   * Add to an in-memory `cart` list.

   * Ask “Add another item? (y/n)”

3. Once user chooses `n`:

   * Compute bill total:

     * `total_amount = sum(line_total for each cart item)`

   * Show preview:

     * All line items with quantities, prices, line totals

     * Summary (subtotal/total)

   * Ask “Confirm and save? (y/n)”

4. On confirm:

Insert into `bills`:

 INSERT INTO bills (customer\_name, store\_name, total\_amount, created\_at)  
VALUES (...);

*   
  * Get the new `bill_id`.

  * For each cart line:

    * Insert into `bill_items`.

Deduct stock:

 UPDATE items  
SET stock\_qty \= stock\_qty \- :quantity,  
    updated\_at \= NOW()  
WHERE id \= :item\_id;

*   
5. Print invoice:

   * Simple console layout:

     * Store name

     * Date/time

     * Each line: item name, unit, qty, unit price, line total

     * Final total

   * Optionally also write this to a `.txt` file for record keeping.

This pattern (Python \+ PostgreSQL console program with inventory and billing) is exactly how many tutorial projects introduce inventory logic before moving to APIs. ([Tiger Data](https://www.tigerdata.com/learn/how-to-use-psycopg2-the-postgresql-adapter-for-python?utm_source=chatgpt.com))

---

## **5\. Phase 2 – FastAPI Backend (with PostgreSQL)**

Now we keep PostgreSQL as the single source of truth and add a **REST API** using FastAPI.

### **5.1 Tech Stack**

* Python 3.x

* FastAPI ([FastAPI](https://fastapi.tiangolo.com/tutorial/sql-databases/?utm_source=chatgpt.com))

* Uvicorn (ASGI server)

* Database layer:

  * Recommended: **SQLAlchemy ORM \+ PostgreSQL** so it can scale nicely. ([GitHub](https://github.com/jod35/Build-a-fastapi-and-postgreSQL-API-with-SQLAlchemy?utm_source=chatgpt.com))

### **5.2 Suggested Folder Structure**

storelite\_api/  
  ├─ app/  
  │   ├─ main.py          \# FastAPI app, include routers  
  │   ├─ database.py      \# engine, session, Base for PostgreSQL  
  │   ├─ models.py        \# SQLAlchemy models: Item, Bill, BillItem  
  │   ├─ schemas.py       \# Pydantic models: ItemCreate, ItemRead, BillCreate, BillRead  
  │   ├─ routers/  
  │   │   ├─ inventory.py \# /items endpoints  
  │   │   └─ billing.py   \# /bills endpoints  
  │   └─ services/  
  │       └─ billing.py   \# core billing logic: stock checks, bill creation  
  └─ requirements.txt

### **5.3 Key Endpoints**

**Inventory (`/items`)**

* `GET /items`

  * List all active items, with optional query params:

    * `name` (search by name)

    * `category`

* `POST /items`

  * Create a new item (like the CLI “Add new item”).

* `GET /items/{id}`

  * Get a single item by ID.

* `PUT /items/{id}`

  * Update price, stock, metadata.

* `DELETE /items/{id}` or soft delete

  * Either hard delete or set `is_active = FALSE`.

**Billing (`/bills`)**

* `POST /bills`

Request body example:

 {  
  "customer\_name": "Ali",  
  "store\_name": "Utility Store \#1",  
  "items": \[  
    { "item\_id": 1, "quantity": 2 },  
    { "item\_id": 5, "quantity": 1.5 }  
  \]  
}

*   
  * Server-side logic:

    * Validate items exist & stock is enough.

    * Compute line totals & grand total.

    * Create bill \+ bill\_items rows.

    * Update inventory stock.

  * Response:

    * Full bill with line items and totals.

* `GET /bills/{id}`

  * Return bill header \+ line items (used later by frontend to show invoice).

* `GET /bills`

  * List bills (with optional filters, like date range).

There are many guides and example repos for “FastAPI \+ SQLAlchemy \+ PostgreSQL” building simple inventory-style APIs; you can follow one as a technical reference for configuring the DB engine and session. ([GitHub](https://github.com/jod35/Build-a-fastapi-and-postgreSQL-API-with-SQLAlchemy?utm_source=chatgpt.com))

### **5.4 Testing the API**

Run:

 uvicorn app.main:app \--reload

*   
* Open:

  * `http://localhost:8000/docs` (Swagger UI auto-generated by FastAPI)

* From Swagger UI:

  * Test `/items` (create, list, update)

  * Test `/bills` (create and read)

* Confirm:

  * Inventory changes reflect correctly in PostgreSQL.

  * Bills and bill\_items are created as expected.

---

## **6\. Phase 3 – Next.js Frontend**

Now we connect a **Next.js** frontend to the FastAPI API. Next.js \+ FastAPI is a well-known and solid combination for modern full-stack apps. ([Reddit](https://www.reddit.com/r/FastAPI/comments/1es9twk/is_fastapi_a_good_choice_to_use_with_nextjs_on/?utm_source=chatgpt.com))

### **6.1 Tech Stack**

* Next.js 14 (App Router)

* TypeScript (recommended)

* Tailwind CSS or any lightweight UI library

* HTTP client:

  * Native `fetch` or Axios

* Backend: FastAPI (Phase 2\) with PostgreSQL

### **6.2 High-Level App Structure**

storelite\_frontend/  
  ├─ app/  
  │   ├─ layout.tsx  
  │   ├─ page.tsx         \# Landing page with links to /admin and /pos  
  │   ├─ admin/  
  │   │   └─ page.tsx     \# Inventory management UI  
  │   └─ pos/  
  │       └─ page.tsx     \# POS / Billing UI  
  └─ lib/  
      └─ api.ts           \# helper wrapper for calling FastAPI endpoints

---

### **6.3 `/admin` – Inventory Management Page**

**Features**

* **Add New Item Form**

  * Fields:

    * Name

    * Category (dropdown: Grocery, Utilities, Beauty, Garments, Other...)

    * Unit

    * Unit price

    * Initial stock quantity

  * On submit:

    * Send `POST /items` to FastAPI.

    * On success, refresh the items list.

* **Items Table**

  * Display:

    * Name, category, unit, price, stock.

  * Search:

    * Client-side filter or API `GET /items?name=...`

  * Edit:

    * Click row to open a small dialog or inline form to update price/stock.

    * Send `PUT /items/{id}`.

  * Deactivate:

    * Optional toggle to set `is_active = false`.

This pattern mirrors typical inventory CRUD dashboards in React/Next.js tutorials; you just hit FastAPI instead of Node/Django. ([TestDriven.io](https://testdriven.io/blog/fastapi-react/?utm_source=chatgpt.com))

---

### **6.4 `/pos` – POS / Billing Page**

**Intent:** This is the simple interface your store’s salesperson will use.

**Flow**

1. **Search & Add Items**

   * Search bar at top:

     * User types item name → call `GET /items?name=query`.

     * Show dropdown / list of matches.

   * On selecting an item:

     * Open a row in the “Current Bill” section:

       * Show name, unit, price.

       * Input for quantity.

       * Show line total \= price × quantity.

2. **Cart / Bill Summary**

   * A table or list of all selected items:

     * Item name

     * Quantity

     * Unit price

     * Line total

   * At bottom:

     * Subtotal \= sum of line totals.

     * (Optional: discount/tax fields later).

     * Final total.

3. **Generate Bill**

   * Button “Generate Bill”.

   * On click:

     * Send one `POST /bills` request with:

       * `customer_name` (optional input)

       * `store_name` (configurable or selected)

       * `items` array: `{item_id, quantity}`.

   * On success:

     * Show invoice view (from API response).

     * Optionally reset the form/cart.

4. **Invoice Print**

   * Invoice layout page/section:

     * Store name

     * Date/time

     * List of line items

     * Grand total

   * Use `window.print()` to let browser print it as a receipt.

There are multiple examples online showing how to call FastAPI endpoints from Next.js using `fetch` and render the data; you can follow those patterns directly. ([Athar Naveed](https://atharnaveed.medium.com/full-stack-connecting-next-js-15-with-fastapi-part-1-4a12af2b2b6f?utm_source=chatgpt.com))

---

## **7\. Future Roadmap: AI Agents & Automation**

Once the core **PostgreSQL \+ FastAPI \+ Next.js** system is stable, you can gradually attach AI agents (e.g., via Claude / OpenAI) to make it “smart”.

Ideas:

1. **Sales Analytics Agent**

   * Reads `bills` \+ `bill_items` from PostgreSQL.

   * Answers questions like:

     * “What are the top 10 best-selling items this month?”

     * “Which category is generating the most revenue?”

   * Could run scheduled analytics and email simple reports.

2. **Low Stock Alert Agent**

   * Periodically query `items` for `stock_qty` below threshold.

   * Send Slack/Email/WhatsApp alerts: “Sugar is below 5 kg” etc.

3. **Natural Language Query**

   * A small chat UI where the store owner types:

     * “Show me all bills from yesterday.”

     * “How much revenue did we make on beauty products last week?”

   * Agent translates to SQL, queries PostgreSQL, and responds with a summary.

PostgreSQL is a good choice here because it’s robust and works well with Python-based APIs and reporting tools. ([Python in Plain English](https://python.plainenglish.io/adding-a-production-grade-database-to-your-fastapi-project-local-setup-50107b10d539?utm_source=chatgpt.com))

---

## **8\. Execution Plan – What You Actually Do Next**

**Phase 1**

1. Set up PostgreSQL locally (or Neon/Supabase/ElephantSQL).

2. Create `items`, `bills`, `bill_items` tables using the schema above.

3. Implement `db.py` (Postgres connection \+ helper functions).

4. Implement `inventory.py` and `billing.py` with console menus.

5. Manually test adding items and generating a bill.

**Phase 2**

1. Create a FastAPI project.

2. Configure SQLAlchemy with PostgreSQL (engine, session, models). ([GitHub](https://github.com/jod35/Build-a-fastapi-and-postgreSQL-API-with-SQLAlchemy?utm_source=chatgpt.com))

3. Implement `/items` and `/bills` endpoints using the existing logic.

4. Test via Swagger UI (`/docs`).

**Phase 3**

1. Scaffold a Next.js app.

2. Build `/admin` and `/pos` routes/pages.

3. Add API calls to FastAPI for inventory and billing.

4. Test the full flow end-to-end:

   * Admin adds products.

   * POS page creates bills.

   * PostgreSQL reflects the stock and invoice data correctly.

# **9\. Phase 4 – FastMCP Server for Inventory & Billing**

In this phase, we take the existing **FastAPI \+ PostgreSQL** logic (Inventory \+ Billing) and expose it as an **MCP server** using **FastMCP**.

## **9.1 Goal**

* Wrap your existing backend capabilities (add item, search items, create bill, fetch bill) as **MCP tools**.

* So any LLM agent (Claude, OpenAI Agents SDK, etc.) can call these tools via MCP in a standard way. ([GitHub](https://github.com/modelcontextprotocol?utm_source=chatgpt.com))

FastMCP is a Python framework that makes it easy to build production-ready MCP servers with tools, resources, prompts, and automatic schema generation. ([GitHub](https://github.com/jlowin/fastmcp?utm_source=chatgpt.com))

## **9.2 Tech Stack**

* Python 3.x

* **FastMCP** (Python) – from `mcp.server.fastmcp import FastMCP` ([Model Context Protocol](https://modelcontextprotocol.io/docs/develop/build-server?utm_source=chatgpt.com))

* PostgreSQL (same DB as Phases 1–3)

* Reuse your **service layer** from FastAPI (e.g. `services.billing`, `services.inventory`).

## **9.3 Suggested Folder Layout**

Add a new folder to your backend repo:

storelite\_api/  
  ├─ app/                 \# existing FastAPI app  
  ├─ mcp\_server/  
  │   ├─ \_\_init\_\_.py  
  │   ├─ server.py        \# FastMCP server entry point  
  │   ├─ tools\_inventory.py  
  │   └─ tools\_billing.py  
  └─ ...

* `app/` continues to serve HTTP API (Phase 2).

* `mcp_server/` exposes **the same business logic** via MCP tools.

## **9.4 Designing MCP Tools**

Conceptually, MCP has:

* **Tools** → “do something” (like POST endpoints: add item, create bill). ([Prefect](https://www.prefect.io/fastmcp?utm_source=chatgpt.com))

* **Resources** → “load data” into context (like GET endpoints: list items, fetch bill). ([Prefect](https://www.prefect.io/fastmcp?utm_source=chatgpt.com))

For StoreLite IMS, you can start with tools like:

### **Inventory tools**

* `inventory_add_item`

  * Inputs: `name`, `category`, `unit`, `unit_price`, `stock_qty`

  * Side effect: inserts row in `items` \+ returns created item

* `inventory_list_items`

  * Optional filters: `name`, `category`, `active_only`

  * Returns: paginated list of items

* `inventory_update_item`

  * Inputs: `item_id`, optional fields to update (price, stock, etc.)

### **Billing tools**

* `billing_create_bill`

  * Inputs:

    * `customer_name` (optional)

    * `store_name` (optional)

    * `items`: list of `{ item_id, quantity }`

  * Logic:

    * Validate stock

    * Create `bills` \+ `bill_items`

    * Update inventory

  * Returns: full bill payload

* `billing_get_bill`

  * Inputs: `bill_id`

  * Returns: bill header \+ line items (for re-printing invoice, etc.)

## **9.5 Implementing FastMCP Server (High-Level)**

Following FastMCP docs / MCP Python examples: ([Model Context Protocol](https://modelcontextprotocol.io/docs/develop/build-server?utm_source=chatgpt.com))

* In `server.py`:

Create server:

 from mcp.server.fastmcp import FastMCP

mcp \= FastMCP("storelite")

*   
  * Import your tools (`tools_inventory`, `tools_billing`).

  * Run server with stdio or HTTP transport depending on where you’ll host it.

* In `tools_inventory.py` / `tools_billing.py`:

Decorate Python functions that call into your service layer:

 from mcp.server.fastmcp import tool  
from app.services.inventory import add\_item, list\_items

@tool  
def inventory\_add\_item(name: str, category: str, unit: str,  
                       unit\_price: float, stock\_qty: float) \-\> dict:  
    """  
    Create a new inventory item in StoreLite IMS.  
    """  
    return add\_item(name=name, category=category, unit=unit,  
                    unit\_price=unit\_price, stock\_qty=stock\_qty)

*   
  * FastMCP uses **type hints \+ docstrings** to auto-generate tool schema for MCP clients. ([Model Context Protocol](https://modelcontextprotocol.io/docs/develop/build-server?utm_source=chatgpt.com))

## **9.6 Transports & Integration Targets**

You want this MCP server to be usable by:

* Claude Code / local dev tools (via stdio).

* OpenAI Agents SDK (via Hosted MCP tool or HTTP/stdio bridge). ([OpenAI GitHub](https://openai.github.io/openai-agents-python/mcp/?utm_source=chatgpt.com))

So:

* Define one **stdio entry point** for dev and local testing.

* Optionally define an **HTTP entry point** if you plan to run this as a network service for multiple agents.

---

# **10\. Phase 5 – OpenAI Agents Using MCP Tools \+ FastAPI**

Now we build **LLM agents** (OpenAI Agents SDK) that use the StoreLite MCP server to perform inventory & billing operations from **natural language conversations**.

## **10.1 Goal**

* Replace manual forms / CLI steps with an **agent** that understands:

  * “Add 20kg sugar to inventory at 160 per kg under grocery”

  * “Create a bill for 2kg sugar and 1 pack of tea for customer Ali”

  * “Show me all items low on stock in the beauty category”

* The agent internally calls MCP tools (`inventory_add_item`, `billing_create_bill`, etc.).

* Expose this agent via **FastAPI** endpoint(s), so your UI (Next.js) can send chat-style messages to the agent.

The OpenAI Agents SDK is designed exactly for this: you register **tools**, including Hosted MCP tools, and the agent chooses when to call them. ([OpenAI Platform](https://platform.openai.com/docs/guides/agents-sdk?utm_source=chatgpt.com))

## **10.2 Tech Stack**

* OpenAI **Agents SDK** (Python) ([OpenAI Platform](https://platform.openai.com/docs/guides/agents-sdk?utm_source=chatgpt.com))

* HostedMCPTool or MCP integration helper to expose your FastMCP server to the agent. ([OpenAI GitHub](https://openai.github.io/openai-agents-python/tools/?utm_source=chatgpt.com))

* FastAPI (same backend) to provide `/agent/chat` endpoint.

* Existing StoreLite FastMCP server from Phase 4\.

## **10.3 Agent Design**

Define an agent like **StoreLite Inventory & Billing Agent** with:

* **Role / instructions**:

  * You are an assistant for a small store inventory and billing system.

  * You help admins manage inventory (add/update/list items).

  * You help sales staff create invoices.

  * Always confirm actions before writing to the database.

* **Tools**:

  * Hosted MCP tool connected to `storelite` MCP server.

  * Tools: `inventory_add_item`, `inventory_list_items`, `inventory_update_item`, `billing_create_bill`, `billing_get_bill`.

Per OpenAI docs, you can register MCP-based tools so the agent can call them like normal tools. ([OpenAI GitHub](https://openai.github.io/openai-agents-python/mcp/?utm_source=chatgpt.com))

## **10.4 Conversational Flows (Examples)**

1. **Admin – Add inventory item**

   * User: “Add 10 kg sugar at 160 per kg under grocery category.”

   * Agent:

     * Parses the sentence.

     * Calls `inventory_add_item(name="Sugar", category="Grocery", unit="kg", unit_price=160, stock_qty=10)`.

     * Replies: “I’ve added 10kg of Sugar at 160 per kg under Grocery. Current stock: 10 kg.”

2. **Admin – Update stock**

   * User: “Increase stock of flour by 25 kg.”

   * Agent:

     * Calls `inventory_list_items` with search “flour”.

     * If multiple items → asks user to clarify.

     * Once item selected, calls `inventory_update_item` to adjust `stock_qty`.

     * Confirms result.

3. **Salesperson – Create bill**

   * User: “Create a bill for 2kg sugar and 1 shampoo bottle for customer Ali.”

   * Agent:

     * Finds matching items via `inventory_list_items`.

     * Asks to confirm if multiple matches.

     * Calls `billing_create_bill(...)`.

     * Responds with bill summary and bill ID.

## **10.5 FastAPI \+ Agent Integration**

Add a simple API on top of the agent:

storelite\_api/  
  ├─ app/  
  │   ├─ main.py          \# include /agent routes  
  │   ├─ routes\_agent.py  \# /agent/chat  
  │   └─ agents/  
  │       └─ storelite\_agent.py  
  └─ ...

* `/agent/chat` endpoint:

  * Accepts `session_id` (optional) \+ `message` from the frontend.

  * Forwards message to the Agents SDK’s **Runner**, which uses the MCP tools.

  * Streams or returns final assistant reply \+ any structured data (e.g., bill ID).

On the frontend, you can later replace manual inventory/billing forms with a **chat assistant** or mix both (forms \+ AI chat).

DigitalOcean / blog articles show end-to-end examples of integrating MCP tools with OpenAI Agents SDK, including best practices for security and tool design. ([DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-use-mcp-with-openai-agents?utm_source=chatgpt.com))

---

# **11\. Test-Driven Development (TDD) Strategy for Backend**

You said: “backend ka jitna bhi procedure hai, we want TDD.”  
 So we’ll apply **TDD across Phases 2, 4, and 5**:

* Phase 2 – FastAPI REST API to PostgreSQL

* Phase 4 – FastMCP server tools

* Phase 5 – OpenAI Agents integration

## **11.1 General TDD Principles**

We follow the classic TDD loop: ([Medium](https://medium.com/%40kasperjuunge/fastapi-an-example-of-test-driven-development-%EF%B8%8F-21109ea901ae?utm_source=chatgpt.com))

1. **Write a failing test** for a small behavior.

2. **Implement minimal code** to make it pass.

3. **Refactor** to keep code clean (without breaking tests).

We use:

* **pytest** as the main testing framework.

* For FastAPI:

  * `TestClient` / HTTPX-based client for endpoint tests. ([FastAPI](https://fastapi.tiangolo.com/tutorial/testing/?utm_source=chatgpt.com))

* For DB:

  * A **test Postgres database** or schema with fixtures.

* For MCP:

  * Direct function tests on tools, plus optional integration tests that spin up the FastMCP server.

* For Agents:

  * Tests that simulate tool calls or run the agent in a controlled environment.

Several open-source examples and courses demonstrate TDD with FastAPI, Postgres, pytest, and Docker. ([TestDriven.io](https://testdriven.io/courses/tdd-fastapi/?utm_source=chatgpt.com))

## **11.2 TDD in Phase 2 – FastAPI \+ PostgreSQL**

Types of tests:

1. **Unit tests for services**

   * Example: `services.billing.create_bill`:

     * Given items with certain stock, when we call create\_bill with specific quantities:

       * It returns correct totals.

       * It decreases stock correctly.

       * It rejects over-quantity with an error.

2. **API tests**

   * Use FastAPI TestClient / HTTPX:

     * `POST /items` creates an item and returns 201 \+ JSON.

     * `GET /items` returns a list including newly created item.

     * `POST /bills` returns bill payload and updates DB.

3. **Test DB fixture**

   * Use a dedicated test database (e.g. `storelite_test`) or schema.

   * Setup/teardown fixtures to create and drop tables or run migrations for each test run.

## **11.3 TDD in Phase 4 – FastMCP Tools**

Here, your tools are **adapters** on top of service layer logic.

1. **Unit tests**

   * Test tool functions directly (without starting MCP server process):

     * `inventory_add_item()` returns the same structure as service.

     * `billing_create_bill()` calls service correctly and propagates errors.

2. **Integration tests (optional but ideal)**

   * Spin up FastMCP server (maybe via subprocess or test harness). ([MCPcat](https://mcpcat.io/guides/building-mcp-server-python-fastmcp/?utm_source=chatgpt.com))

   * Use MCP client (e.g., from MCP Python SDK) to call tools:

     * Verify responses and side effects in Postgres.

## **11.4 TDD in Phase 5 – Agents \+ MCP \+ FastAPI**

1. **Tool wiring tests**

   * Ensure HostedMCPTool / MCP integration is correctly configured:

     * Agent can see the tools.

     * Tool schemas match expected parameters.

2. **Conversation-level tests (semi-integration)**

   * Example: test function `test_agent_can_create_bill`:

     * Provide user message: “Create a bill with 2kg sugar...”

     * Mock or use a real test MCP server.

     * Assert:

       * Agent decides to call `billing_create_bill`.

       * Final response contains a valid bill ID and summary.

3. **FastAPI endpoint tests**

   * `POST /agent/chat`:

     * With a given message, returns an agent response.

     * Check that HTTP status is correct, and structure is as expected.

Got it, that constraint makes sense 👍  
 I’ll **update the spec conceptually** so Phase 4–5 are aligned with:

* **MCP servers \= local only (localhost/stdio/http)** for testing,

* **Agents use `gemini-2.5-flash-lite` (Gemini lite LLM)** inside OpenAI Agents SDK,

* Therefore no OpenAI **Hosted MCP** (because that requires OpenAI models on the agent).

---

## **9\. Phase 4 – FastMCP Server for Inventory & Billing (Local Only in Testing Phase)**

In this phase, we still take the existing **FastAPI \+ PostgreSQL** logic (Inventory \+ Billing) and expose it as an **MCP server** using **FastMCP**, **but**:

**Important constraint (initial/testing phase):**  
 All MCP servers will run **locally** (via `localhost` HTTP or `stdio`) and will only be used from your own environment.  
 We will **not** use OpenAI’s Hosted MCP feature, because our agent will use **`gemini-2.5-flash-lite`** as the model, and Hosted MCP currently requires an OpenAI model to be selected for the agent.

(That matches OpenAI’s current design: Hosted MCP is tightly integrated with OpenAI models inside the Agents platform; if you don’t use an OpenAI model, you can’t attach Hosted MCP in production mode.)

### **9.1 Goal (updated)**

* Wrap the backend capabilities (add item, search items, create bill, fetch bill) as **MCP tools** using **FastMCP**.

* Run the MCP server **locally**:

  * **`stdio`** when using Claude Code / local MCP clients.

  * **`http://127.0.0.1:<port>`** when testing from your own custom agent code.

* Use these local MCP servers **only in your own dev environment** during the initial/testing phase.

Later, if you decide to add an OpenAI model as a primary or backup model in the Agents SDK, you can revisit Hosted MCP; but for now the architecture is explicitly **local MCP \+ Gemini-lite model**.

### **9.6 Transports & Integration Targets (updated)**

* For development:

  * **Stdio transport**  
     Used by tools like Claude Code, local MCP test clients, etc.

  * **Local HTTP transport**  
     e.g. `http://localhost:8001`  
     Used by your custom agent runner that runs Gemini-based agents and needs MCP access.

* No Hosted MCP configuration in OpenAI dashboard for this phase, because:

  * The agent’s primary model is `gemini-2.5-flash-lite`.

  * Hosted MCP in OpenAI’s ecosystem is only available when an OpenAI model is selected for the agent, not when using a non-OpenAI base model.

---

## **10\. Phase 5 – OpenAI Agents Using Local MCP Tools \+ FastAPI (with Gemini Lite)**

In this phase, we still build **OpenAI Agents SDK–based agents**, but:

* The **LLM** \= `gemini-2.5-flash-lite` (via the Gemini model integration in the Agents SDK).

* The **tools** \= **local MCP servers** (FastMCP over Inventory/Billing), not Hosted MCP.

* The agent calls MCP tools over `localhost` (HTTP) or via a local MCP client bridge.

### **10.1 Goal (updated)**

* Let admin/sales users use **natural language** to:

  * Add/update inventory

  * Create bills

  * Query stock and sales

* The agent:

  * Runs on top of **`gemini-2.5-flash-lite`** as the reasoning model.

  * Uses **local MCP tools** (Inventory & Billing MCP server) for database operations.

* No Hosted MCP in this phase; all MCP usage is through local connections.

### **10.2 Tech Stack (updated)**

* OpenAI **Agents SDK** (for orchestration and tool handling).

* **Gemini 2.5 Flash Lite** as the agent’s LLM (`model="gemini-2.5-flash-lite"` in the agent config).

* **Local FastMCP server** for StoreLite IMS:

  * Exposed via `stdio` and/or `http://localhost:<port>`.

* FastAPI backend continues to exist:

  * Used both as a classic REST API (Phase 2/3)

  * And as the underlying business logic for MCP tools (Phase 4).

### **10.3 Agent Design (unchanged concept, updated implementation detail)**

* The agent keeps the same **role** and **tool list**:

  * Tools:

    * `inventory_add_item`

    * `inventory_list_items`

    * `inventory_update_item`

    * `billing_create_bill`

    * `billing_get_bill`

* But now:

  * These tools are **MCP tools provided by a local FastMCP server**, not Hosted MCP tools.

  * The agent process itself is responsible for:

    * Connecting to the local MCP server (via an MCP client / HostedMCPTool equivalent for localhost).

    * Calling these tools when needed.

### **10.5 FastAPI \+ Agent Integration (unchanged concept)**

We still expose an endpoint like `/agent/chat`:

* Input: `session_id`, `message`

* Inside handler:

  * Pass message to the Agents SDK–based runner.

  * The runner is configured with:

    * `model="gemini-2.5-flash-lite"`

    * Tools backed by your local MCP server.

* Output:

  * The agent’s response text.

  * Optionally, structured info like bill details, etc.

**Key difference from Hosted MCP world:**  
 All MCP calls stay within your own infrastructure (local dev or your own server), rather than being hosted and managed by OpenAI as Hosted MCP tools.

---

## **11\. TDD (unchanged, just note local MCP usage)**

The TDD strategy described before still applies exactly the same way:

* **Phase 2** – tests for FastAPI services \+ endpoints.

* **Phase 4** – tests for MCP tools:

  * Unit tests on tool functions (direct Python calls).

  * Optional integration tests where you run the local FastMCP server and call it like a real client over `stdio`/`localhost`.

* **Phase 5** – tests for the Agent:

  * Simulate user messages.

  * Mock or spin up a real local MCP server.

  * Assert that:

    * The agent chooses the correct tools.

    * The DB state changes as expected.

    * The final answer to the user is correct.

---

## **12\. Phase 6 – ChatKit Frontend for the StoreLite Agent**

### **12.1 Goal**

Expose your **StoreLite Inventory & Billing Agent** through a **ready-made chat UI** using **OpenAI ChatKit**, so:

* UI \= **fully powered by ChatKit** (no custom chat components).

* Backend \= **your own FastAPI \+ Agents SDK \+ Gemini-lite \+ MCP**, running locally.

* ChatKit is used in **self-hosted backend mode**, where:

  * ChatKit renders the UI.

  * ChatKit sends chat requests to **your backend** instead of OpenAI’s hosted workflows. ([OpenAI GitHub](https://openai.github.io/chatkit-js/))

You already have:

* Phase 5 agent: `StoreLite Agent` using `gemini-2.5-flash-lite` \+ MCP tools.

* FastAPI endpoint(s) that can handle: “user message → agent → response”.

Now we add **ChatKit on the frontend** as a thin UI wrapper on top of this.

---

### **12.2 Background: How ChatKit Fits In**

**ChatKit** is OpenAI’s UI framework / web component for building chat experiences:

* Provides a **complete chat interface** out of the box (messages list, composer, streaming, attachments, widgets, etc.). ([OpenAI GitHub](https://openai.github.io/chatkit-js/))

* Can work with:

  * **Managed backend** → OpenAI Agent Builder workflow (workflowId).

  * **Self-hosted backend** → your own server via ChatKit Python SDK or custom API config. ([OpenAI GitHub](https://openai.github.io/chatkit-js/))

In your case:

* We choose **self-hosted backend** because:

  * You’re using **Gemini-lite** \+ custom MCP tools, not a pure OpenAI workflow.

  * You already have FastAPI and Agents SDK orchestrating everything.

ChatKit’s job is just:

Embed a `<ChatKit>` UI component, point it at your **ChatKit-compatible API URL**, and it will handle streaming messages in and out. ([OpenAI GitHub](https://openai.github.io/chatkit-js/))

---

### **12.3 Preconditions Before Adding ChatKit UI**

Before touching the frontend, you should have:

1. **FastAPI backend agent endpoint working** (Phase 5):

   * Example behavior:

     * `POST /agent/chat`

       * Input: { session\_id, user\_message }

       * Output: streamed or chunked agent response (text \+ optional metadata).

   * It internally calls:

     * Agents SDK with `model="gemini-2.5-flash-lite"`.

     * MCP tools for inventory/billing operations.

2. **Plan for ChatKit backend mode**:

   * For a **proper ChatKit integration**, ideal setup:

     * Add a **ChatKit-compatible layer** in FastAPI using the **ChatKit Python SDK** (self-hosted backend mode).

     * This layer translates ChatKit’s conversation protocol → your existing agent runner.

   * In docs, we’ll just call this the **“ChatKit backend endpoint”**, e.g.:

     * `http://localhost:8000/chatkit` *(example)*

3. **Existing frontend project** (from Phase 3):

   * Next.js app already exists for admin `/admin` and POS `/pos`.

   * You’ll now add a new route e.g. `/agent` or `/assistant`.

---

### **12.4 Decide Which ChatKit Flavor You’ll Use**

ChatKit offers two main frontend integration styles:

1. **React bindings** (`@openai/chatkit-react`)

   * You use a `<ChatKit />` React component within Next.js.

   * This is ideal since your app is already React/Next.

2. **Vanilla Web Component** (`<openai-chatkit />`)

   * Framework-agnostic, can be added directly to DOM.

   * Also supported in Next.js, but React wrapper is smoother.

For this spec we’ll assume:

**Option A – React+Next.js with the ChatKit React component**  
 UI is still 100% ChatKit; you are only dropping in the official component, not building any custom chat UI.

---

### **12.5 Step-by-Step – Wiring ChatKit UI (High-Level)**

#### **Step 1 – Install ChatKit SDK in the frontend**

* Add the official ChatKit packages to your Next.js frontend:

  * `@openai/chatkit` (underlying JS SDK)

  * `@openai/chatkit-react` (React wrapper)

* This gives you:

  * The `ChatKit` React component.

  * The `useChatKit` hook that manages the chat state and connection to your backend.

*(You’re not writing custom UI — you’re just rendering this component.)*

---

#### **Step 2 – Configure environment variables for ChatKit**

Create/update your frontend `.env` (or `.env.local`) with:

* **API URL** → where ChatKit should send chat traffic:

  * For dev: something like `http://localhost:8000/chatkit`.

* **Domain key or identifier for your environment** (if you choose to use it as a logical env name; in self-hosted mode it can be a simple string).

* Optionally, a **public config** variable for the ChatKit API URL so you can read it on the client.

For example (conceptually):

* `NEXT_PUBLIC_CHATKIT_API_URL` → `"http://localhost:8000/chatkit"`

* `NEXT_PUBLIC_CHATKIT_DOMAIN_KEY` → `"domain_pk_localhost_dev"`

ChatKit uses `api.url` and `api.domainKey` / `customApi` in its options to know where to send requests.

---

#### **Step 3 – Decide how ChatKit talks to your backend (self-hosted mode)**

In **self-hosted backend mode**, ChatKit doesn’t talk to OpenAI directly; instead it calls your own HTTP endpoints.

From the docs:

* Managed vs self-hosted:

  * Managed → `api: { url: <OpenAI ChatKit API>, domainKey }`

  * Self-hosted → use the **Python SDK** and/or a **custom API config** to route to your server.

For your setup:

1. Your **FastAPI app** exposes an endpoint like `/chatkit` that understands ChatKit’s protocol.

2. In the frontend, ChatKit’s options will be configured roughly as:

   * “Use `api.url = NEXT_PUBLIC_CHATKIT_API_URL`”

   * Or if you go for the advanced pattern: provide a **custom `fetch`** implementation in ChatKit options that:

     * Sends POST/GET to your FastAPI `/chatkit` endpoint.

     * Attaches any headers you want (e.g. auth tokens).

The advanced “custom backend” flow gives full control over routing, tools, security, etc.

---

#### **Step 4 – Create a dedicated “Agent Chat” page in Next.js**

In your Next.js app:

* Create a new route like `/agent` (App Router) or an equivalent page.

* This page is **only responsible for rendering ChatKit** and maybe a simple title/header around it.

High-level structure of that page:

1. The page loads and reads environment vars for:

   * ChatKit API URL

   * Domain key / any optional config

2. The page calls `useChatKit` (from `@openai/chatkit-react`) with options:

   * `api.url` set to your FastAPI ChatKit backend URL.

   * `api.domainKey` (optional) as your environment identifier.

   * Any theming or start-screen configuration you want (e.g. a welcome message like *“Ask me anything about inventory and billing”*).

3. The hook returns a `control` object that you pass into the `ChatKit` component.

4. You render `<ChatKit />` as the **only chat UI** on the page.

Net result:

* When the user types a message:

  * ChatKit sends it to `http://localhost:8000/chatkit` (self-hosted backend).

  * Your backend passes it to the StoreLite Agent (Gemini-lite \+ MCP).

  * ChatKit streams the answer back into the chat widget.

---

#### **Step 5 – Connect ChatKit requests to your StoreLite Agent on the backend**

On the backend (FastAPI):

* You already have a **runner** that can:

  * Take `user_message` \+ `session_id`.

  * Call:

    * Agents SDK with `model="gemini-2.5-flash-lite"`.

    * MCP tools (`inventory_add_item`, `billing_create_bill`, etc.).

  * Return a response stream or final message.

To integrate with ChatKit, your new `/chatkit` endpoint must:

1. Accept ChatKit’s request format:

   * Typically includes user message, thread / session IDs, etc.

2. Map that to your agent runner:

   * Extract user text.

   * Map ChatKit conversation ID → your internal `session_id`.

3. Stream the agent’s response back in the format ChatKit expects:

   * ChatKit Python SDK docs \+ advanced FastAPI samples show the exact protocol structure.

You now have this flow:

**Browser ChatKit UI → FastAPI /chatkit → StoreLite Agent (Gemini \+ MCP) → FastAPI → ChatKit UI**

All the complex logic (tools, inventory DB writes, billing) lives in the agent \+ MCP tools, **not** in the UI.

---

#### **Step 6 – Basic theming & branding (optional)**

ChatKit allows:

* Accent color

* Fonts

* Header text and icon

* Start screen prompts, etc.

For this project:

* Keep customizations **minimal** to respect your “pure ChatKit” intent:

  * Set:

    * App name (“StoreLite Assistant”).

    * Primary color that matches your brand.

    * Initial greeting like:

      * “Hi, I’m your StoreLite inventory & billing assistant. I can add items, update stock, and create bills for you.”

You’re still not building custom UI — you’re just passing options to ChatKit.

---

#### **Step 7 – Manual test flow**

Once the page and backend are wired:

1. Start your FastAPI backend (with ChatKit endpoint \+ agent).

2. Start your Next.js frontend.

3. Open `/agent` in the browser.

Test scenarios:

1. **Add inventory via chat**

   * User: “Add 10kg sugar at 160 per kg under grocery.”

   * Expected:

     * ChatKit sends message to backend.

     * Agent calls MCP `inventory_add_item`.

     * Response appears in chat: “Added 10kg Sugar at 160 per kg in Grocery category.”

2. **Create bill via chat**

   * User: “Create a bill for Ali: 2kg sugar and 1 shampoo bottle.”

   * Expected:

     * Agent looks up items, calls `billing_create_bill`.

     * Chat shows bill summary:

       * Items, quantities, total, bill ID.

3. **Query stock**

   * User: “Show me all items with stock less than 5 units in beauty category.”

   * Expected:

     * Agent calls `inventory_list_items` with filters.

     * Chat responds with a small table summary.

If these flows work from ChatKit UI, your full pipeline is live.

---

### **12.6 Where This Fits in Your Overall Phases**

Quick recap of the full project now:

1. **Phase 1** – Console Python \+ PostgreSQL.

2. **Phase 2** – FastAPI \+ PostgreSQL (REST API).

3. **Phase 3** – Next.js admin \+ POS UI.

4. **Phase 4** – FastMCP server wrapping inventory & billing.

5. **Phase 5** – OpenAI Agents SDK \+ Gemini-lite, using MCP tools, exposed via FastAPI.

6. **Phase 6 (this)** – ChatKit UI:

   * Pure ChatKit SDK (no custom chat UI).

   * Self-hosted backend mode talking to your FastAPI agent backend.