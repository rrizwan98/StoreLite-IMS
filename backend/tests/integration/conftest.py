"""
Pytest configuration for integration tests - provides test_session fixture for old CLI tests
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Create a temporary SQLite database for testing
_temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
_temp_db.close()
TEST_DATABASE_URL = f"sqlite:///{_temp_db.name.replace(chr(92), '/')}"


@pytest.fixture(scope="function")
def test_session():
    """
    Provide a test database session using SQLite
    This fixture is used by the old CLI integration tests (src/services)
    """
    # Create engine with SQLite
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create session factory
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )

    # Create all tables before test
    from src.models.base import Base
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    yield session

    # Cleanup after test
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def cleanup_temp_db():
    """Cleanup temporary database file after all tests"""
    yield
    # Note: Keep the temp file for now to avoid file locking issues on Windows
    # It will be cleaned up when the test session ends
