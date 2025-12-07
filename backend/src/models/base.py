"""
Shared SQLAlchemy Base for all ORM models
Ensures all models use the same metadata object
"""

from sqlalchemy.orm import declarative_base

# Single shared Base for all models
Base = declarative_base()
