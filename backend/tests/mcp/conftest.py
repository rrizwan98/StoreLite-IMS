"""
Pytest fixtures for MCP tests
"""
import pytest
import sys
import os
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database import Base

# Register models once at module load time
from app.models import Item, Bill, BillItem


def pytest_configure(config):
    """Register models once per test session."""
    # Models are now registered with Base
    pass


@pytest.fixture
async def test_db():
    """Create async SQLite in-memory test database."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_session(test_db):
    """Get async session for tests."""
    async_session_local = async_sessionmaker(
        test_db,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_local() as session:
        yield session


@pytest.fixture
async def sample_items(test_session):
    """Pre-populate test database with sample items."""
    from app.models import Item

    items = [
        Item(
            name="Sugar",
            category="Grocery",
            unit="kg",
            unit_price=Decimal("50.00"),
            stock_qty=Decimal("100.0"),
            is_active=True
        ),
        Item(
            name="Rice",
            category="Grocery",
            unit="kg",
            unit_price=Decimal("30.00"),
            stock_qty=Decimal("50.0"),
            is_active=True
        ),
    ]

    for item in items:
        test_session.add(item)

    await test_session.commit()

    # Refresh to get IDs
    for item in items:
        await test_session.refresh(item)

    return items


@pytest.fixture
async def sample_bills(test_session, sample_items):
    """Pre-populate test database with sample bills."""
    from app.models import Bill, BillItem
    from decimal import Decimal

    bills = []
    for i, item in enumerate(sample_items):
        bill = Bill(
            customer_name=f"Customer {i+1}",
            store_name="Test Store",
            total_amount=Decimal("500.00")
        )
        test_session.add(bill)
        await test_session.flush()

        # Add line item
        line_item = BillItem(
            bill_id=bill.id,
            item_id=item.id,
            item_name=item.name,
            unit_price=item.unit_price,
            quantity=Decimal("5.0"),
            line_total=item.unit_price * Decimal("5.0")
        )
        test_session.add(line_item)
        bills.append(bill)

    await test_session.commit()

    # Refresh to ensure relationships are loaded
    for bill in bills:
        await test_session.refresh(bill)

    return bills
