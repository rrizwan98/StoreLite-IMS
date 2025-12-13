"""
Authentication Service

Handles password hashing, JWT token generation/validation, and user authentication.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 7


# ============================================================================
# Pydantic Models
# ============================================================================

class TokenData(BaseModel):
    """Data extracted from JWT token"""
    user_id: int
    email: str
    exp: Optional[datetime] = None


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    """User registration data"""
    email: str
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login data"""
    email: str
    password: str


class UserResponse(BaseModel):
    """User data response (no sensitive info)"""
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    has_connection: bool = False
    connection_type: Optional[str] = None
    mcp_status: Optional[str] = None

    model_config = {"from_attributes": True}


# ============================================================================
# Password Functions
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # Truncate password to 72 bytes (bcrypt limit) to avoid errors
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# ============================================================================
# JWT Functions
# ============================================================================

def create_access_token(user_id: int, email: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int, email: str) -> str:
    """Create JWT refresh token"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        email = payload.get("email")
        if user_id is None or email is None:
            return None
        return TokenData(user_id=user_id, email=email)
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def create_tokens(user_id: int, email: str) -> Token:
    """Create both access and refresh tokens"""
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id, email)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
    )


# ============================================================================
# User Authentication Functions
# ============================================================================

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Create a new user"""
    # Check if email already exists
    existing = await get_user_by_email(db, user_data.email)
    if existing:
        raise ValueError("Email already registered")

    # Create new user
    user = User(
        email=user_data.email.lower().strip(),
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info(f"[Auth] Created new user: {user.email}")
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = await get_user_by_email(db, email.lower().strip())
    if not user:
        logger.warning(f"[Auth] Login attempt for non-existent email: {email}")
        return None
    if not user.is_active:
        logger.warning(f"[Auth] Login attempt for inactive user: {email}")
        return None
    if not verify_password(password, user.password_hash):
        logger.warning(f"[Auth] Invalid password for: {email}")
        return None

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    logger.info(f"[Auth] User logged in: {email}")
    return user


async def get_current_user(db: AsyncSession, token: str) -> Optional[User]:
    """Get current user from JWT token"""
    token_data = decode_token(token)
    if not token_data:
        return None

    user = await get_user_by_id(db, token_data.user_id)
    if not user or not user.is_active:
        return None

    return user
