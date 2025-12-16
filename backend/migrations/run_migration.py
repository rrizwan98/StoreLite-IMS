"""
Run database migrations.

Usage:
    python migrations/run_migration.py                           # Run all migrations
    python migrations/run_migration.py 010_add_gmail_oauth_columns.sql  # Run specific migration

Available migrations:
    - add_schema_agent_columns.sql      (Phase 9: Schema Agent)
    - 010_add_gmail_oauth_columns.sql   (Phase 10: Gmail Tool)

Or run SQL directly:
    psql -U your_user -d your_database -f migrations/<filename>.sql
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


async def run_migration(sql_file: str = None):
    """Run database migration(s)."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Please set it in your .env file")
        sys.exit(1)

    migrations_dir = Path(__file__).parent

    # Determine which migrations to run
    if sql_file:
        sql_files = [migrations_dir / sql_file]
        if not sql_files[0].exists():
            print(f"ERROR: Migration file not found: {sql_file}")
            print(f"\nAvailable migrations:")
            for f in sorted(migrations_dir.glob("*.sql")):
                print(f"  - {f.name}")
            sys.exit(1)
    else:
        # Run all SQL files in order
        sql_files = sorted(migrations_dir.glob("*.sql"))

    if not sql_files:
        print("No migration files found.")
        sys.exit(0)

    # Read SQL files
    migrations = []
    for sql_path in sql_files:
        with open(sql_path, "r") as f:
            migrations.append((sql_path.name, f.read()))

    print(f"Connecting to database...")
    print(f"Migrations to run: {[m[0] for m in migrations]}\n")

    try:
        conn = await asyncpg.connect(database_url)

        for migration_name, sql in migrations:
            print(f"Running: {migration_name}")
            print("-" * 50)

            # Execute each statement separately
            statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]

            for stmt in statements:
                if stmt:
                    try:
                        await conn.execute(stmt)
                        # Show first 60 chars of statement
                        stmt_preview = stmt.replace('\n', ' ')[:60]
                        print(f"  OK: {stmt_preview}...")
                    except Exception as e:
                        # Column might already exist
                        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                            stmt_preview = stmt.replace('\n', ' ')[:60]
                            print(f"  SKIP (already exists): {stmt_preview}...")
                        else:
                            print(f"  ERROR: {e}")

            print()

        await conn.close()
        print("All migrations completed successfully!")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Get optional migration file from command line
    sql_file = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(run_migration(sql_file))
