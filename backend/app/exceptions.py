"""
Custom exception classes for IMS FastAPI backend
"""


class ValidationError(Exception):
    """Raised when request validation fails (422 status)"""

    def __init__(self, message: str, fields: dict = None):
        self.message = message
        self.fields = fields or {}
        super().__init__(self.message)


class BusinessLogicError(Exception):
    """Raised when business logic validation fails (400 status)"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class NotFoundError(Exception):
    """Raised when requested resource is not found (404 status)"""

    def __init__(self, message: str = "Not found"):
        self.message = message
        super().__init__(self.message)


class DatabaseError(Exception):
    """Raised when database operation fails (500 status)"""

    def __init__(self, message: str = "Database error"):
        self.message = message
        super().__init__(self.message)
