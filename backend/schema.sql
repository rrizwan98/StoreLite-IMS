-- Schema for Inventory Management System (Phase 1)
-- Created: 2025-12-07

-- Items table: Store product inventory
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('Grocery', 'Garments', 'Beauty', 'Utilities', 'Other')),
    unit VARCHAR(50) NOT NULL CHECK (unit IN ('kg', 'g', 'liter', 'ml', 'piece', 'box', 'pack', 'other')),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    stock_qty NUMERIC(10, 2) NOT NULL CHECK (stock_qty >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Bills table: Store invoice records
CREATE TABLE IF NOT EXISTS bills (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255),
    store_name VARCHAR(255),
    total_amount NUMERIC(12, 2) NOT NULL CHECK (total_amount >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Bill Items table: Store line items for each bill (with snapshots of price/name)
CREATE TABLE IF NOT EXISTS bill_items (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES items(id),
    item_name VARCHAR(255) NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    quantity NUMERIC(10, 2) NOT NULL CHECK (quantity > 0),
    line_total NUMERIC(12, 2) NOT NULL CHECK (line_total >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_items_active ON items(is_active);
CREATE INDEX IF NOT EXISTS idx_items_name ON items(name);
CREATE INDEX IF NOT EXISTS idx_bills_created_at ON bills(created_at);
CREATE INDEX IF NOT EXISTS idx_bill_items_bill_id ON bill_items(bill_id);
