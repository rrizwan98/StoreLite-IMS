# Data Model & Database Schema (Phase 1)

**Date**: 2025-12-07 | **Branch**: `001-console-ims-p1` | **Source**: spec.md, plan.md

## Overview

Three core entities support Phase 1 inventory and billing operations:
- **Item**: Product master data with stock tracking and pricing
- **Bill**: Invoice header with customer and store metadata
- **BillItem**: Line items in each bill with historical price/name snapshots

## Entity Definitions

### Entity: Item

**Purpose**: Represents a product in inventory. Each item has a unique name (within active items), category, unit of measurement, pricing, and stock level.

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO INCREMENT | Unique item identifier |
| `name` | TEXT | NOT NULL, UNIQUE (when is_active=true) | Product name (case-sensitive for search, but case-insensitive ILIKE used in queries per FR-005) |
| `category` | TEXT | NOT NULL, ENUM-like validation | One of: Grocery, Garments, Beauty, Utilities, Other. Validated in application layer; database stores as TEXT for flexibility |
| `unit` | TEXT | NOT NULL, ENUM-like validation | One of: kg, g, liter, ml, piece, box, pack, other. Validated in application layer |
| `unit_price` | NUMERIC(12,2) | NOT NULL, ≥ 0 | Price per unit (e.g., price per kg). Stored with 2 decimal places |
| `stock_qty` | NUMERIC(12,3) | NOT NULL, ≥ 0 | Current quantity in stock. Stored with 3 decimal places to support fractional units (e.g., 2.5 kg) per edge case note in spec |
| `is_active` | BOOLEAN | DEFAULT TRUE | Soft delete flag; inactive items excluded from list/search by default (FR-004, FR-005) |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation time (UTC) |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP, ON UPDATE CURRENT_TIMESTAMP | Last modification time (UTC) |

**Validation Rules**:
- `name`: Non-empty, required; no hardcoded max length in database (application layer enforces reasonable limit, e.g., 255 chars)
- `category`: Must be one of predefined values; rejected if not in list (FR-002a)
- `unit`: Must be one of predefined values; rejected if not in list (FR-002b)
- `unit_price`: Must be ≥ 0 (FR-002, FR-007); rejected if negative
- `stock_qty`: Must be ≥ 0 (FR-002, FR-007); rejected if negative; decimal quantities allowed (e.g., 2.5 kg)
- `is_active`: Defaults to true; soft delete prevents hard removal (Constitution Principle IV)

**Relationships**:
- One Item → Many BillItems (when item is sold)
- One Item → Many inventory transactions (search, update operations)

**Constraints**:
- Unique constraint: `(name, is_active)` — allows "inactive" duplicate names, but no two active items with same name
- Index on `name` for case-insensitive search (ILIKE query optimization per FR-005)
- Index on `is_active` for fast filtering (exclude inactive from lists)
- Foreign key from BillItem.item_id → Item.id (cascade delete handled via soft delete flag)

---

### Entity: Bill

**Purpose**: Represents a sales invoice header. Each bill is created when a salesperson confirms a set of line items, optionally associates customer/store info, and triggers inventory stock deductions.

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO INCREMENT | Unique bill/invoice identifier |
| `customer_name` | TEXT | NULL allowed (optional) | Name of customer (if known); nullable for anonymous/walk-in sales per FR-012a, FR-016 |
| `store_name` | TEXT | NULL allowed (optional) | Name of store (if multi-location, else can be NULL or store default per FR-016) |
| `total_amount` | NUMERIC(12,2) | NOT NULL, ≥ 0 | Grand total of bill (sum of all bill_items.line_total); calculated in application layer, stored for audit/performance |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Bill creation date/time (UTC); immutable after creation |

**Validation Rules**:
- `customer_name`: Optional; if provided, can be any non-empty string (no format validation)
- `store_name`: Optional; if provided, can be any non-empty string
- `total_amount`: Must be ≥ 0; calculated as SUM(bill_items.line_total) before INSERT; validated in application
- `created_at`: Set automatically; not modifiable

**Relationships**:
- One Bill → Many BillItems (one-to-many)
- One Bill → implicit references to Items (via BillItems)

**Constraints**:
- Index on `created_at` for bill listing by date range (future reporting)
- Foreign key references from BillItem.bill_id → Bill.id (cascade delete: if bill deleted, line items deleted; mitigated by soft delete pattern)

---

### Entity: BillItem

**Purpose**: Represents a single line item in a bill (one item, with quantity and snapshot of price/name at time of sale). Historical snapshots prevent data inconsistency if an item is later edited or deleted.

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO INCREMENT | Unique line item identifier |
| `bill_id` | INTEGER | FOREIGN KEY (bills.id), NOT NULL | Reference to parent bill; cascade delete if bill deleted |
| `item_id` | INTEGER | FOREIGN KEY (items.id), NOT NULL | Reference to item sold (for audit trail; but price/name stored separately) |
| `item_name` | TEXT | NOT NULL | Snapshot of item.name at time of sale (e.g., "Sugar" as it appeared when bill created) |
| `unit_price` | NUMERIC(12,2) | NOT NULL, ≥ 0 | Snapshot of item.unit_price at time of sale (e.g., if price changes later, invoice shows historic price) |
| `quantity` | NUMERIC(12,3) | NOT NULL, > 0 | Quantity sold; decimal allowed (e.g., 2.5 kg per edge case in spec) |
| `line_total` | NUMERIC(12,2) | NOT NULL, ≥ 0 | Calculated as unit_price * quantity; stored for invoice display and audit |

**Validation Rules**:
- `bill_id`: Must reference valid bill; foreign key constraint enforced
- `item_id`: Must reference valid item; foreign key constraint enforced
- `item_name`: Snapshot of item name (non-empty); not editable after INSERT
- `unit_price`: Snapshot of price (≥ 0); not editable after INSERT
- `quantity`: Must be > 0 (at least one unit sold); ≤ item.stock_qty at time of bill creation (validated in application before INSERT per FR-009)
- `line_total`: Calculated as unit_price * quantity; not editable after INSERT (application calculates and stores)

**Relationships**:
- Many BillItems → One Bill (many-to-one via bill_id)
- Many BillItems → One Item (many-to-one via item_id; allows tracking which items appear in which bills)

**Constraints**:
- Foreign key on `bill_id` (CASCADE DELETE if bill deleted)
- Foreign key on `item_id` (RESTRICT if item deleted; use soft delete flag to avoid this)
- Index on `bill_id` for efficient retrieval of items in a bill
- Index on `item_id` for audit trail (which bills sold a given item)

---

## Database Schema (SQL DDL)

### Table: items

```sql
CREATE TABLE items (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  unit TEXT NOT NULL,
  unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
  stock_qty NUMERIC(12, 3) NOT NULL CHECK (stock_qty >= 0),
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
  UNIQUE (name, is_active)
);

CREATE INDEX idx_items_active ON items (is_active);
CREATE INDEX idx_items_name_search ON items (LOWER(name));
```

### Table: bills

```sql
CREATE TABLE bills (
  id SERIAL PRIMARY KEY,
  customer_name TEXT,
  store_name TEXT,
  total_amount NUMERIC(12, 2) NOT NULL CHECK (total_amount >= 0),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_bills_created_at ON bills (created_at);
```

### Table: bill_items

```sql
CREATE TABLE bill_items (
  id SERIAL PRIMARY KEY,
  bill_id INTEGER NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
  item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
  item_name TEXT NOT NULL,
  unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
  quantity NUMERIC(12, 3) NOT NULL CHECK (quantity > 0),
  line_total NUMERIC(12, 2) NOT NULL CHECK (line_total >= 0)
);

CREATE INDEX idx_bill_items_bill_id ON bill_items (bill_id);
CREATE INDEX idx_bill_items_item_id ON bill_items (item_id);
```

---

## Key Design Decisions

### 1. Soft Delete (is_active flag)
- **Decision**: Use `is_active` boolean instead of hard delete
- **Rationale**: Constitution Principle IV (Database-First Design) requires soft deletes for audit trail and historical integrity
- **Impact**: All list/search queries filter `WHERE is_active = TRUE`; allows recovery of accidentally deleted items

### 2. Snapshot of Price & Name in BillItem
- **Decision**: Store `item_name` and `unit_price` in BillItem (duplicate of Item table data at time of sale)
- **Rationale**: If an item is edited or deleted later, the bill still shows what the price and name were when sold (historical accuracy per Constitution Principle IV)
- **Impact**: BillItems are immutable records; changes to Item do not affect already-created bills

### 3. Decimal Quantities (NUMERIC 12,3)
- **Decision**: Allow fractional units (e.g., 2.5 kg) via NUMERIC(12,3) for both stock_qty and quantity
- **Rationale**: Spec edge case: "How does the system handle decimal quantities? (Accepted; stored as NUMERIC(12,3))"
- **Impact**: Supports sell-by-weight scenarios (e.g., Dairy, Flour, Spices); not limited to whole units

### 4. Optional Customer/Store Names
- **Decision**: Both customer_name and store_name are nullable
- **Rationale**: Spec FR-012a and clarification: "Optional; system prompts user for customer_name during bill creation, but user can press Enter/skip to leave it blank"
- **Impact**: Supports anonymous sales (privacy) while allowing tracking of known customers

### 5. Total Amount Stored (Not Calculated on Retrieval)
- **Decision**: Store `bills.total_amount` as denormalized data (sum of bill_items.line_total)
- **Rationale**: Simplifies invoice display; prevents SQL complexity on large bills; audit trail (total amount at time of sale)
- **Impact**: Application layer is responsible for calculating and validating total before INSERT

### 6. Indexes for Performance
- **Decision**: Indexes on commonly queried columns (is_active, name, bill_id, item_id, created_at)
- **Rationale**: Spec success criterion SC-002: "Users can search for a product by partial name and get results in under 2 seconds for an inventory of 1000+ items"
- **Impact**: Case-insensitive ILIKE search on name is optimized; list/search filters fast

---

## Validation & Constraints

### Application Layer Validation
These checks happen in Python before any database operation:

- **Category enum**: Must be exactly one of (Grocery, Garments, Beauty, Utilities, Other) — case-sensitive match
- **Unit enum**: Must be exactly one of (kg, g, liter, ml, piece, box, pack, other) — case-sensitive match
- **Price/Stock non-negative**: Reject if unit_price < 0 or stock_qty < 0
- **Stock availability**: Before adding item to bill, validate stock_qty >= quantity (FR-009)
- **Bill minimum**: Bill must have ≥ 1 item (edge case: "Can a user create a bill with zero items? No")
- **Zero price allowed**: unit_price = 0 is permitted (edge case: "What if unit_price is 0? Allowed")

### Database Layer Validation
These constraints are enforced by PostgreSQL:

- CHECK constraints on numeric fields (unit_price ≥ 0, stock_qty ≥ 0, quantity > 0, line_total ≥ 0)
- UNIQUE constraint on (name, is_active) to prevent duplicate active items
- FOREIGN KEY constraints to maintain referential integrity
- NOT NULL constraints on required fields

### Atomicity for Bill Operations
- **Transaction Scope**: Entire bill creation (validate stock → insert bill → insert line items → decrement stock) wrapped in single PostgreSQL transaction
- **Rollback**: If any step fails, entire bill is rolled back; no partial updates (FR-014)

---

## Migration Strategy

### Initial Schema Creation (Phase 1)
Run `schema.sql` on first app start if tables don't exist.

### No Migrations in Phase 1
Schema is stable; no migrations needed between Phase 1 releases.

### Phase 2+ Considerations
If schema changes (e.g., add discount field, tax), use Alembic (SQLAlchemy migration tool) to version migrations.

---

## Conclusion

This data model supports all Phase 1 functional requirements:
- ✅ Inventory management (add, list, search, update items)
- ✅ Bill creation with stock validation and atomic decrements
- ✅ Historical data preservation (price/name snapshots, soft deletes)
- ✅ Performance targets (indexed queries, optimized for 1000+ item inventory)
- ✅ Audit trail (timestamps, snapshots, foreign keys)

Ready for implementation in Phase 1 tasks.
