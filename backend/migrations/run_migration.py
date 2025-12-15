"""
Run database migration to add Schema Agent columns.

Usage:
    python migrations/run_migration.py

Or run the SQL directly:
    psql -U your_user -d your_database -f migrations/add_schema_agent_columns.sql
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def run_migration():
    """Run the schema agent migration."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Please set it in your .env file")
        sys.exit(1)

    # Read SQL file
    sql_path = Path(__file__).parent / "add_schema_agent_columns.sql"
    with open(sql_path, "r") as f:
        sql = f.read()

    print(f"Connecting to database...")

    try:
        conn = await asyncpg.connect(database_url)

        print("Running migration...")

        # Execute each statement separately
        statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]

        for stmt in statements:
            if stmt:
                try:
                    await conn.execute(stmt)
                    print(f"  OK: {stmt[:60]}...")
                except Exception as e:
                    # Column might already exist
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print(f"  SKIP (already exists): {stmt[:60]}...")
                    else:
                        print(f"  ERROR: {e}")

        await conn.close()
        print("\nMigration completed successfully!")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_migration())
