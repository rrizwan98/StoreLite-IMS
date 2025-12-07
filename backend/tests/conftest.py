"""
Pytest configuration and fixtures for IMS tests
"""

import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Use test database URL from environment or default
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://user:password@localhost:5432/ims_test_db"
)


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine"""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    return engine


@pytest.fixture(scope="function")
def test_session(test_engine):
    """
    Create a fresh test session for each test
    Sets up schema before test and tears down after
    """
    # Create tables from schema.sql
    with test_engine.begin() as connection:
        # Drop existing tables
        connection.execute(text("DROP TABLE IF EXISTS bill_items CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS bills CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS items CASCADE"))

        # Read and execute schema.sql
        schema_path = "backend/schema.sql"
        if os.path.exists(schema_path):
            with open(schema_path, "r") as f:
                schema = f.read()

            statements = [s.strip() for s in schema.split(";") if s.strip()]
            for statement in statements:
                connection.execute(text(statement))

    # Create session factory
    TestSessionLocal = sessionmaker(bind=test_engine, expire_on_commit=False)
    session = TestSessionLocal()

    yield session

    # Cleanup
    session.close()

    # Drop tables after test
    with test_engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS bill_items CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS bills CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS items CASCADE"))


@pytest.fixture(scope="function")
def mock_session(test_session):
    """Alias for test_session for convenience in tests"""
    return test_session


# Markers for test classification
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "contract: mark test as a contract test")
