"""
Entry point for IMS CLI application (T029)
Initializes database connection and starts main menu
"""

import sys
import logging
from src.db import get_db
from src.cli.main_menu import main_menu
from src.cli.ui_utils import display_header, display_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for IMS application"""
    try:
        display_header("STARTING IMS")

        # Get database instance
        db = get_db()

        # Verify database connection
        if not db.health_check():
            display_error("Failed to connect to database. Please check DATABASE_URL in .env file.")
            logger.error("Database health check failed")
            sys.exit(1)

        logger.info("Database connection established")

        # Get session
        with db.session() as session:
            # Start main menu
            main_menu(session)

    except KeyboardInterrupt:
        print("\n\nShutdown signal received. Exiting...")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        display_error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
