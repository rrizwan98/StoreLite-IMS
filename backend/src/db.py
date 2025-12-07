"""
Database connection and session management using SQLAlchemy
"""

import logging
import os
from contextlib import contextmanager
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ims_db")


class Database:
    """Database connection manager"""

    def __init__(self, database_url: str = DATABASE_URL):
        """
        Initialize database connection

        Args:
            database_url: PostgreSQL connection string

        Raises:
            ValueError: If DATABASE_URL is invalid
        """
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")

        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using
            echo=False,  # Set to True for SQL debugging
        )

        # Set up session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False,
        )

        # Configure SQLAlchemy to use SERIALIZABLE isolation level for transactions
        @event.listens_for(self.engine, "connect")
        def set_isolation_level(dbapi_conn, connection_record):
            dbapi_conn.set_isolation_level(3)  # SERIALIZABLE

        logger.info("Database initialized with connection pool")

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    @contextmanager
    def session_scope(self):
        """Context manager for database sessions with automatic cleanup"""
        session = self.get_session()
        try:
            yield session
            session.commit()
            logger.debug("Database transaction committed")
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction rolled back due to error: {e}")
            raise
        finally:
            session.close()

    def init_db(self, script_path: str = "backend/schema.sql") -> bool:
        """
        Initialize database schema from SQL script

        Args:
            script_path: Path to schema.sql file

        Returns:
            True if initialization succeeded, False otherwise
        """
        try:
            with self.session_scope() as session:
                # Check if tables already exist
                result = session.execute(
                    text(
                        """
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables
                            WHERE table_name = 'items'
                        )
                        """
                    )
                )
                tables_exist = result.scalar()

                if tables_exist:
                    logger.info("Database tables already exist, skipping initialization")
                    return True

                # Read and execute schema.sql
                if not os.path.exists(script_path):
                    logger.error(f"Schema file not found at {script_path}")
                    return False

                with open(script_path, "r") as f:
                    schema = f.read()

                # Split by semicolon and execute each statement
                statements = [s.strip() for s in schema.split(";") if s.strip()]
                for statement in statements:
                    session.execute(text(statement))

                session.commit()
                logger.info("Database schema initialized successfully")
                return True

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False

    def health_check(self) -> bool:
        """
        Check database connectivity

        Returns:
            True if database is accessible, False otherwise
        """
        try:
            with self.session_scope() as session:
                session.execute(text("SELECT 1"))
            logger.info("Database health check passed")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def close(self):
        """Close database connections"""
        self.engine.dispose()
        logger.info("Database connections closed")


# Global database instance (lazy initialization)
db = None


def get_db():
    """Get or create global database instance"""
    global db
    if db is None:
        db = Database()
    return db
