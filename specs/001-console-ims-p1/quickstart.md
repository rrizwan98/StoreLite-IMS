# Quickstart Guide: Console-Based Inventory & Billing System (Phase 1)

**Date**: 2025-12-07 | **Branch**: `001-console-ims-p1`

## Overview

This guide covers local development setup, running the console app, and verifying core functionality.

## Prerequisites

- **Python 3.12+** (check with `python --version`)
- **PostgreSQL 12+** (local or Neon cloud-hosted)
- **PostgreSQL connection string** (DATABASE_URL environment variable)
- **Git** (to clone and manage the project)

## Step 1: Clone & Setup

```bash
# Clone the repository
git clone https://github.com/your-org/IMS-Simple-Inventory-.git
cd IMS-Simple-Inventory-
git checkout 001-console-ims-p1

# Create a Python virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies (using uv or pip)
# Option 1: Using uv (recommended in constitution)
uv pip install -e .

# Option 2: Using pip
pip install -r backend/requirements.txt
```

## Step 2: Configure Database

### Create .env file

In the `backend/` directory, create a `.env` file with your PostgreSQL connection string:

```bash
# File: backend/.env
DATABASE_URL=postgresql://username:password@localhost:5432/ims_dev
```

**For Neon Cloud PostgreSQL:**
```bash
DATABASE_URL=postgresql://user:password@ep-xyz.region.neon.tech/dbname
```

**For local PostgreSQL:**
```bash
# Create a local database first:
createdb ims_dev

# Then use:
DATABASE_URL=postgresql://postgres:password@localhost:5432/ims_dev
```

### Initialize Database

The app automatically creates tables on first run. Optionally, run the schema directly:

```bash
# From backend/ directory:
psql -d ims_dev -f schema.sql
```

## Step 3: Run the Application

```bash
# From backend/ directory (with venv activated):
python -m src.cli.main
```

**Expected Output:**
```
========================================
  Welcome to StoreLite IMS - Phase 1
========================================

Main Menu:
1. Manage Inventory
2. Create New Bill
3. Exit

Please select an option: _
```

## Step 4: Test Core Workflows

### Workflow 1: Add a Product

```
1. Main menu → Select "1" (Manage Inventory)
2. Inventory Menu → Select "1" (Add new item)
3. Enter product details:
   - Name: Sugar
   - Category: (type "groc" → suggestions appear → select "Grocery")
   - Unit: (type "k" → suggestions appear → select "kg")
   - Price per unit: 150
   - Stock quantity: 100
4. Confirm → Success message

Verify: Go back to "List all items" → Sugar should appear in the table
```

### Workflow 2: Search & Update Product

```
1. Main menu → Select "1" (Manage Inventory)
2. Inventory Menu → Select "3" (Search item by name)
3. Enter search term: "sug" (partial match)
4. Results show all items containing "sug"
5. Select item ID → View current details
6. Choose to update price or stock
7. Enter new value, confirm

Verify: List items again → updated price/stock reflected
```

### Workflow 3: Create a Bill

```
1. Main menu → Select "2" (Create New Bill)
2. Search for item: "sugar"
3. Select item → Enter quantity: 2
4. "Add more items?" → Yes/No
5. Review bill preview (items, unit prices, quantities, totals)
6. Confirm bill → Prompted for customer name & store name (press Enter to skip)
7. Invoice printed to console

Verify:
- Check that inventory stock decremented (go to Manage Inventory → Search "sugar" → stock now 98)
- Check that bill data persisted in database (to be verified in integration tests)
```

## Step 5: Run Tests

```bash
# From backend/ directory:

# Run all tests with coverage
pytest --cov=src tests/

# Run only unit tests
pytest tests/unit/

# Run only integration tests (requires active DB)
pytest tests/integration/

# Run only contract tests (CLI output validation)
pytest tests/contract/

# Run with verbose output
pytest -v tests/
```

**Expected Coverage**: ≥ 80% (per Constitution Principle II)

## Step 6: Verify Database Data

```bash
# Check items table
psql -d ims_dev -c "SELECT id, name, category, unit, unit_price, stock_qty FROM items WHERE is_active = true ORDER BY name;"

# Check bills table
psql -d ims_dev -c "SELECT id, customer_name, store_name, total_amount, created_at FROM bills ORDER BY created_at DESC LIMIT 5;"

# Check bill_items table
psql -d ims_dev -c "SELECT bi.id, bi.bill_id, bi.item_name, bi.quantity, bi.unit_price, bi.line_total FROM bill_items bi ORDER BY bi.bill_id DESC LIMIT 10;"
```

## Troubleshooting

### Issue: DATABASE_URL not found
**Solution**: Ensure `.env` file is in `backend/` directory and app loads it at startup.

```python
# In backend/src/db.py:
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
```

### Issue: Connection refused (PostgreSQL not running)
**Solution**: Start PostgreSQL service or use Neon cloud.

```bash
# For local PostgreSQL on macOS:
brew services start postgresql

# For Linux (systemd):
sudo systemctl start postgresql

# For Windows:
# Start PostgreSQL via Services app or pg_ctl
```

### Issue: Tests fail with "table does not exist"
**Solution**: Ensure `conftest.py` creates test tables or run `schema.sql` against test database.

```python
# In backend/tests/conftest.py:
@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create tables for tests"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
```

### Issue: Invalid choice error in menus
**Solution**: Ensure valid input (e.g., "1", "2", "3" for main menu). System re-prompts if invalid.

## File Structure for Phase 1

```
backend/
├── src/
│   ├── cli/main.py          # Entry point
│   ├── cli/inventory_menu.py
│   ├── cli/billing_menu.py
│   ├── cli/ui_utils.py
│   ├── services/inventory_service.py
│   ├── services/billing_service.py
│   ├── models/item.py
│   ├── models/bill.py
│   ├── db.py               # SQLAlchemy setup
│   └── __init__.py
├── tests/
│   ├── unit/test_*.py
│   ├── integration/test_*.py
│   ├── contract/test_cli_output.py
│   └── conftest.py
├── .env.example
├── .env                    # (Your local DATABASE_URL)
├── schema.sql             # DDL for tables
├── pyproject.toml         # Dependencies
└── requirements.txt       # (if using pip)
```

## Next Steps

1. **Develop Features**: Follow tasks.md for TDD (Red-Green-Refactor) cycle
2. **Write Tests First**: Ensure 80%+ coverage before each commit
3. **Run Tests Frequently**: `pytest` before every commit
4. **Code Review**: Verify against Constitution Principle compliance
5. **Phase 2 Preparation**: Plan FastAPI wrapping (services will be reused)

## Useful Commands

```bash
# Activate venv
source venv/bin/activate

# Run app
python -m src.cli.main

# Run tests
pytest --cov=src tests/

# Check test coverage
pytest --cov=src --cov-report=html tests/
# Open htmlcov/index.html in browser to view detailed coverage

# Format code (if using black)
black src/ tests/

# Lint code (if using flake8)
flake8 src/ tests/

# Check types (if using mypy)
mypy src/
```

## Database Backup & Reset

```bash
# Backup current database
pg_dump -d ims_dev > ims_dev_backup.sql

# Reset database (delete all data)
psql -d ims_dev -c "DROP TABLE IF EXISTS bill_items, bills, items;"
psql -d ims_dev -f schema.sql

# Restore from backup
psql -d ims_dev < ims_dev_backup.sql
```

## Success Criteria

You've successfully completed Phase 1 local setup if:

- ✅ App runs without errors
- ✅ Main menu displays and accepts input
- ✅ Can add a product and see it in the list
- ✅ Can search for a product by partial name
- ✅ Can create a bill and inventory stock decrements
- ✅ All tests pass with ≥80% coverage
- ✅ Data persists in PostgreSQL across app restarts

## Resources

- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **pytest Docs**: https://docs.pytest.org/
- **Constitution**: See `.specify/memory/constitution.md`
- **Feature Spec**: See `/specs/001-console-ims-p1/spec.md`
- **Implementation Plan**: See `/specs/001-console-ims-p1/plan.md`

---

**Ready to develop?** Proceed to `/sp.tasks` to generate actionable tasks for Phase 1 implementation.
