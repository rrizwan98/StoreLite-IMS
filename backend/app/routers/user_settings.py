"""
User Settings Router

Currently supports:
- File retention policy for ChatKit attachments/uploads:
  - keep_24h
  - keep_48h
  - delete_immediately
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, UserSettings
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user-settings", tags=["user-settings"])


class FileRetentionResponse(BaseModel):
    file_retention_mode: str


class FileRetentionUpdateRequest(BaseModel):
    file_retention_mode: str = Field(..., description="keep_24h | keep_48h | delete_immediately")


async def _get_or_create_settings(db: AsyncSession, user_id: int) -> UserSettings:
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    settings = result.scalar_one_or_none()
    if settings:
        return settings

    settings = UserSettings(user_id=user_id, file_retention_mode="keep_24h")
    db.add(settings)
    await db.commit()
    await db.refresh(settings)
    return settings


@router.get("/file-retention", response_model=FileRetentionResponse)
async def get_file_retention(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    settings = await _get_or_create_settings(db, user.id)
    return FileRetentionResponse(file_retention_mode=settings.file_retention_mode)


@router.put("/file-retention", response_model=FileRetentionResponse)
async def update_file_retention(
    payload: FileRetentionUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mode = payload.file_retention_mode
    if mode not in ("keep_24h", "keep_48h", "delete_immediately"):
        raise HTTPException(status_code=400, detail="Invalid file_retention_mode")

    settings = await _get_or_create_settings(db, user.id)
    settings.file_retention_mode = mode
    settings.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(settings)
    logger.info(f"[UserSettings] user_id={user.id} file_retention_mode={mode}")
    return FileRetentionResponse(file_retention_mode=settings.file_retention_mode)


