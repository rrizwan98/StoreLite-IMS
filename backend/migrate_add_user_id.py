"""
Migration script to add user_id columns to items and bills tables.
Run this once to update existing database schema.

Usage: python migrate_add_user_id.py
"""

import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ims_db")

# Convert to async URL
if DATABASE_URL.startswith("postgresql://"):
    base_url = DATABASE_URL.split("?")[0] if "?" in DATABASE_URL else DATABASE_URL
    ASYNC_DATABASE_URL = base_url.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("sqlite://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Default to SQLite if no database is configured
if ASYNC_DATABASE_URL == "postgresql+asyncpg://user:password@localhost:5432/ims_db" or not ASYNC_DATABASE_URL:
    ASYNC_DATABASE_URL = "sqlite+aiosqlite:///ims_dev.db"

print(f"Migrating database: {ASYNC_DATABASE_URL}")

engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def run_migration():
    """Add user_id columns to items and bills tables"""
    async with engine.begin() as conn:
        # Check if we're using SQLite or PostgreSQL
        is_sqlite = 'sqlite' in ASYNC_DATABASE_URL.lower()

        try:
            if is_sqlite:
                # SQLite migration - check if column exists first
                result = await conn.execute(text("PRAGMA table_info(items)"))
                columns = [row[1] for row in result.fetchall()]

                if 'user_id' not in columns:
                    print("Adding user_id column to items table...")
                    await conn.execute(text("""
                        ALTER TABLE items ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
                    """))
                    print("Added user_id to items table")
                else:
                    print("user_id column already exists in items table")

                result = await conn.execute(text("PRAGMA table_info(bills)"))
                columns = [row[1] for row in result.fetchall()]

                if 'user_id' not in columns:
                    print("Adding user_id column to bills table...")
                    await conn.execute(text("""
                        ALTER TABLE bills ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
                    """))
                    print("Added user_id to bills table")
                else:
                    print("user_id column already exists in bills table")
            else:
                # PostgreSQL migration
                print("Adding user_id column to items table (if not exists)...")
                await conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                      WHERE table_name='items' AND column_name='user_id') THEN
                            ALTER TABLE items ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
                            CREATE INDEX IF NOT EXISTS ix_items_user_id ON items(user_id);
                        END IF;
                    END $$;
                """))
                print("Added user_id to items table")

                print("Adding user_id column to bills table (if not exists)...")
                await conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                      WHERE table_name='bills' AND column_name='user_id') THEN
                            ALTER TABLE bills ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
                            CREATE INDEX IF NOT EXISTS ix_bills_user_id ON bills(user_id);
                        END IF;
                    END $$;
                """))
                print("Added user_id to bills table")

            print("\nMigration completed successfully!")
            print("\nIMPORTANT: Existing items and bills will have user_id=NULL.")
            print("They will not be visible to any user until assigned.")

        except Exception as e:
            print(f"Migration error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_migration())
