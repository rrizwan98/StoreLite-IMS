"""
File Upload Router for Schema Agent.

Handles file upload, processing, and retrieval for CSV, Excel, PDF, and Image files.
Files are processed using Python libraries and made available for Schema Agent analysis.

Version: 1.0
Date: December 29, 2025
"""

import os
import uuid
import logging
import asyncio
import aiofiles
from pathlib import Path
from datetime import datetime, timedelta
from typing import Annotated, Optional, Literal

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query, BackgroundTasks, Request
from starlette.datastructures import UploadFile as StarletteUploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UploadedFile, UserSettings
from app.routers.auth import get_current_user
from app.services.file_processor import file_processor, FileProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])

# Configuration
UPLOAD_DIR = Path("uploads")
MAX_FILES_PER_USER = 10
FILE_EXPIRY_HOURS = 24
FILE_EXPIRY_HOURS_48 = 48


# ============================================================================
# Pydantic Models
# ============================================================================

class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    file_id: str
    file_name: str
    file_type: str
    file_size: int
    status: str
    created_at: str
    expires_at: Optional[str] = None
    message: str = "File uploaded successfully"


class ChatKitAttachmentResponse(BaseModel):
    """
    Response model for ChatKit attachments.

    ChatKit expects attachments in this format:
    - id: Server-generated identifier for the uploaded file
    - mime_type: MIME type of the file
    - name: Original filename displayed in the UI
    - type: 'file' or 'image'
    - preview_url: (optional, for images) URL for rendering the image preview
    """
    id: str
    mime_type: str
    name: str
    type: Literal["file", "image"]
    preview_url: Optional[str] = None


class FileStatusResponse(BaseModel):
    """Response model for file status."""
    file_id: str
    file_name: str
    file_type: str
    file_size: int
    status: str
    processed_data: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: str
    expires_at: Optional[str] = None


class FileContentResponse(BaseModel):
    """Response model for file content."""
    file_id: str
    file_type: str
    total_rows: Optional[int] = None
    returned_rows: Optional[int] = None
    offset: int = 0
    data: list


class FileListResponse(BaseModel):
    """Response model for listing files."""
    files: list[FileStatusResponse]
    total: int
    max_files: int = MAX_FILES_PER_USER


class DeleteFileResponse(BaseModel):
    """Response model for file deletion."""
    status: str
    file_id: str
    message: str = "File deleted successfully"


# ============================================================================
# Helper Functions
# ============================================================================

def ensure_upload_dir(user_id: int) -> Path:
    """Ensure upload directory exists for user."""
    user_dir = UPLOAD_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


async def get_user_file_retention_hours(db: AsyncSession, user_id: int) -> int:
    """
    Return retention hours for uploaded files based on user settings.

    - keep_24h (default) -> 24
    - keep_48h -> 48
    - delete_immediately -> 24 (safety TTL; actual deletion handled after response)
    """
    try:
        result = await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
        settings = result.scalar_one_or_none()
        mode = settings.file_retention_mode if settings else "keep_24h"
    except Exception:
        mode = "keep_24h"

    if mode == "keep_48h":
        return FILE_EXPIRY_HOURS_48
    return FILE_EXPIRY_HOURS


async def cleanup_expired_files_for_user(user_id: int, db: AsyncSession) -> None:
    """
    Best-effort cleanup of expired files for a user so old/expired uploads don't
    count toward MAX_FILES_PER_USER and don't linger on disk.
    """
    try:
        now = datetime.utcnow()
        stmt = select(UploadedFile).where(
            and_(
                UploadedFile.user_id == user_id,
                UploadedFile.deleted_at.is_(None),
                UploadedFile.expires_at.is_not(None),
                UploadedFile.expires_at < now,
                UploadedFile.status != "deleted",
            )
        )
        result = await db.execute(stmt)
        expired = result.scalars().all()

        for f in expired:
            # Delete physical file (best-effort)
            try:
                if f.storage_path:
                    p = Path(f.storage_path)
                    if p.exists():
                        p.unlink()
            except Exception:
                pass

            f.status = "deleted"
            f.deleted_at = now

        if expired:
            await db.commit()
    except Exception:
        # Never block uploads due to cleanup issues
        await db.rollback()


async def ensure_capacity_for_new_upload(user_id: int, db: AsyncSession) -> None:
    """
    Ensure the user has room for at least one new upload.

    If the user is at/over the MAX_FILES_PER_USER limit, we prune the oldest
    active files (best-effort). This prevents ChatKit from failing uploads with 400
    and improves UX (instant attachment handling).
    """
    try:
        now = datetime.utcnow()
        stmt = (
            select(UploadedFile)
            .where(
                and_(
                    UploadedFile.user_id == user_id,
                    UploadedFile.deleted_at.is_(None),
                    UploadedFile.status != "deleted",
                )
            )
            .order_by(UploadedFile.created_at.asc())
        )
        result = await db.execute(stmt)
        files = result.scalars().all()
        if len(files) < MAX_FILES_PER_USER:
            return

        # Keep room for 1 new file
        to_prune_count = len(files) - (MAX_FILES_PER_USER - 1)
        to_prune = files[:to_prune_count]

        for f in to_prune:
            try:
                if f.storage_path:
                    p = Path(f.storage_path)
                    if p.exists():
                        p.unlink()
            except Exception:
                pass
            f.status = "deleted"
            f.deleted_at = now

        await db.commit()
        logger.info(f"[Files] Pruned {len(to_prune)} old file(s) for user {user_id} to make room for new upload")
    except Exception as e:
        await db.rollback()
        logger.warning(f"[Files] Failed to prune old files for user {user_id}: {e}")


async def save_upload_file(upload_file: UploadFile, destination: Path) -> int:
    """Save uploaded file to disk and return file size."""
    file_size = 0
    async with aiofiles.open(destination, 'wb') as out_file:
        while content := await upload_file.read(1024 * 1024):  # 1MB chunks
            file_size += len(content)
            await out_file.write(content)
    return file_size


async def process_file_background(
    file_id: str,
    file_path: str,
    file_type: str,
    file_name: str,
    db_url: str
):
    """Background task to process uploaded file."""
    from app.database import async_session

    async with async_session() as db:
        try:
            # Process file
            result = await file_processor.process(file_path, file_type, file_name)

            # Update database record
            stmt = select(UploadedFile).where(UploadedFile.file_id == file_id)
            db_result = await db.execute(stmt)
            file_record = db_result.scalar_one_or_none()

            if file_record:
                file_record.status = 'ready'
                file_record.processed_data = result
                await db.commit()
                logger.info(f"File {file_id} processed successfully")

        except Exception as e:
            logger.error(f"Error processing file {file_id}: {e}")

            # Update with error status
            stmt = select(UploadedFile).where(UploadedFile.file_id == file_id)
            db_result = await db.execute(stmt)
            file_record = db_result.scalar_one_or_none()

            if file_record:
                file_record.status = 'error'
                file_record.error_message = str(e)
                await db.commit()


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(description="File to upload (CSV, Excel, PDF, or Image)")],
    description: Annotated[Optional[str], Form()] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file for Schema Agent analysis.

    Supported file types:
    - CSV (.csv) - up to 10MB
    - Excel (.xlsx, .xls) - up to 10MB
    - PDF (.pdf) - up to 20MB
    - Image (.png, .jpg, .jpeg, .gif, .webp) - up to 5MB

    Files are automatically deleted after 24 hours.
    Maximum 10 files per user.
    """
    # Cleanup expired files first so they don't count against the per-user limit
    await cleanup_expired_files_for_user(user.id, db)
    # Ensure room for a new upload (prevents 400 when user hits limit)
    await ensure_capacity_for_new_upload(user.id, db)

    # Check file count limit
    stmt = select(UploadedFile).where(
        and_(
            UploadedFile.user_id == user.id,
            UploadedFile.status != 'deleted',
            UploadedFile.deleted_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    existing_files = result.scalars().all()

    if len(existing_files) >= MAX_FILES_PER_USER:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "max_files_exceeded",
                "message": f"Maximum {MAX_FILES_PER_USER} files allowed. Please delete some files first."
            }
        )

    # Validate file
    filename = file.filename or "unnamed"
    content_type = file.content_type or ""

    # Read file to get size (we'll save it after validation)
    content = await file.read()
    file_size = len(content)
    await file.seek(0)  # Reset for saving

    is_valid, error_msg, file_type = FileProcessor.validate_file(filename, file_size, content_type)

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_file",
                "message": error_msg
            }
        )

    # Generate file ID and paths
    file_id = str(uuid.uuid4())
    user_dir = ensure_upload_dir(user.id)
    file_ext = Path(filename).suffix
    storage_path = user_dir / f"{file_id}{file_ext}"

    # Save file
    try:
        async with aiofiles.open(storage_path, 'wb') as out_file:
            await out_file.write(content)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "save_failed",
                "message": "Failed to save uploaded file"
            }
        )

    # Calculate expiry time
    retention_hours = await get_user_file_retention_hours(db, user.id)
    expires_at = datetime.utcnow() + timedelta(hours=retention_hours)

    # Create database record
    file_record = UploadedFile(
        file_id=file_id,
        user_id=user.id,
        file_name=filename,
        file_type=file_type,
        file_size=file_size,
        mime_type=content_type,
        status='processing',
        storage_path=str(storage_path),
        expires_at=expires_at
    )

    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)

    # Start background processing
    background_tasks.add_task(
        process_file_background,
        file_id=file_id,
        file_path=str(storage_path),
        file_type=file_type,
        file_name=filename,
        db_url=""  # Will use default session
    )

    logger.info(f"File uploaded: {file_id} ({filename}) by user {user.id}")

    return FileUploadResponse(
        file_id=file_id,
        file_name=filename,
        file_type=file_type,
        file_size=file_size,
        status='processing',
        created_at=file_record.created_at.isoformat() + 'Z',
        expires_at=expires_at.isoformat() + 'Z',
        message="File uploaded successfully. Processing in background."
    )


@router.get("/{file_id}", response_model=FileStatusResponse)
async def get_file_status(
    file_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get file processing status and metadata."""
    stmt = select(UploadedFile).where(
        and_(
            UploadedFile.file_id == file_id,
            UploadedFile.user_id == user.id,
            UploadedFile.deleted_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "file_not_found",
                "message": "File not found or has been deleted"
            }
        )

    # Check expiry
    if file_record.is_expired:
        raise HTTPException(
            status_code=410,
            detail={
                "error": "file_expired",
                "message": "File has expired and is no longer available"
            }
        )

    return FileStatusResponse(
        file_id=file_record.file_id,
        file_name=file_record.file_name,
        file_type=file_record.file_type,
        file_size=file_record.file_size,
        status=file_record.status,
        processed_data=file_record.processed_data,
        error_message=file_record.error_message,
        created_at=file_record.created_at.isoformat() + 'Z',
        expires_at=file_record.expires_at.isoformat() + 'Z' if file_record.expires_at else None
    )


@router.get("/{file_id}/content", response_model=FileContentResponse)
async def get_file_content(
    file_id: str,
    format: Literal["json", "csv", "raw"] = Query(default="json", description="Output format"),
    limit: int = Query(default=1000, le=10000, description="Maximum rows to return"),
    offset: int = Query(default=0, ge=0, description="Starting row offset"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get processed file content.

    For tabular data (CSV/Excel), returns paginated rows.
    For PDF, returns text and tables.
    For images, returns base64 encoded content.
    """
    stmt = select(UploadedFile).where(
        and_(
            UploadedFile.file_id == file_id,
            UploadedFile.user_id == user.id,
            UploadedFile.deleted_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=404,
            detail={"error": "file_not_found", "message": "File not found"}
        )

    if file_record.is_expired:
        raise HTTPException(
            status_code=410,
            detail={"error": "file_expired", "message": "File has expired"}
        )

    if file_record.status != 'ready':
        raise HTTPException(
            status_code=400,
            detail={
                "error": "file_not_ready",
                "message": f"File is not ready. Current status: {file_record.status}"
            }
        )

    processed_data = file_record.processed_data or {}

    # Handle tabular data (CSV/Excel)
    if file_record.file_type in ['csv', 'excel']:
        preview = processed_data.get('preview', [])
        total_rows = processed_data.get('row_count', len(preview))

        # Note: For full data access, would need to re-read file
        # This returns the preview data with pagination
        data_slice = preview[offset:offset + limit]

        return FileContentResponse(
            file_id=file_id,
            file_type=file_record.file_type,
            total_rows=total_rows,
            returned_rows=len(data_slice),
            offset=offset,
            data=data_slice
        )

    # Handle PDF
    elif file_record.file_type == 'pdf':
        return FileContentResponse(
            file_id=file_id,
            file_type='pdf',
            total_rows=processed_data.get('page_count', 0),
            returned_rows=1,
            offset=0,
            data=[{
                'text_content': processed_data.get('text_content', ''),
                'tables': processed_data.get('tables', []),
                'page_count': processed_data.get('page_count', 0)
            }]
        )

    # Handle Image
    elif file_record.file_type == 'image':
        return FileContentResponse(
            file_id=file_id,
            file_type='image',
            total_rows=1,
            returned_rows=1,
            offset=0,
            data=[{
                'width': processed_data.get('width'),
                'height': processed_data.get('height'),
                'format': processed_data.get('format'),
                'base64_content': processed_data.get('base64_content')
            }]
        )

    return FileContentResponse(
        file_id=file_id,
        file_type=file_record.file_type,
        data=[processed_data]
    )


@router.delete("/{file_id}", response_model=DeleteFileResponse)
async def delete_file(
    file_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an uploaded file."""
    stmt = select(UploadedFile).where(
        and_(
            UploadedFile.file_id == file_id,
            UploadedFile.user_id == user.id,
            UploadedFile.deleted_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=404,
            detail={"error": "file_not_found", "message": "File not found"}
        )

    # Mark as deleted in database
    file_record.status = 'deleted'
    file_record.deleted_at = datetime.utcnow()

    # Delete physical file
    if file_record.storage_path:
        try:
            storage_path = Path(file_record.storage_path)
            if storage_path.exists():
                storage_path.unlink()
                logger.info(f"Deleted file from disk: {storage_path}")
        except Exception as e:
            logger.warning(f"Failed to delete file from disk: {e}")

    await db.commit()

    logger.info(f"File deleted: {file_id} by user {user.id}")

    return DeleteFileResponse(
        status="deleted",
        file_id=file_id,
        message="File deleted successfully"
    )


async def get_user_from_request(request: Request, db: AsyncSession) -> User:
    """
    Extract and validate user from request.

    Supports multiple authentication methods:
    1. Authorization header (Bearer token)
    2. Query parameter (token=xxx) - used by ChatKit file uploads since it
       doesn't use the custom api.fetch for direct uploads
    """
    from app.services.auth_service import decode_token

    token = None

    # Try Authorization header first
    auth_header = request.headers.get("authorization", "")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        logger.info("[Auth] Token from Authorization header")

    # Fall back to query parameter (for ChatKit direct uploads)
    if not token:
        token = request.query_params.get("token")
        if token:
            logger.info("[Auth] Token from query parameter")

    if not token:
        logger.error("[Auth] No token found in header or query params")
        raise HTTPException(status_code=401, detail="Missing authentication token")

    token_data = decode_token(token)

    if not token_data:
        logger.error("[Auth] Token decode failed")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Get user from database
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()

    if not user:
        logger.error(f"[Auth] User not found: {token_data.user_id}")
        raise HTTPException(status_code=401, detail="User not found")

    logger.info(f"[Auth] Authenticated user: {user.id}")
    return user


@router.post("/chatkit-upload")
async def chatkit_upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file via ChatKit's attachment system.

    This endpoint returns the response format expected by ChatKit:
    - id: file_id
    - mime_type: file MIME type
    - name: original filename
    - type: 'file' or 'image'
    - preview_url: (for images) preview URL

    ChatKit sends file in multipart/form-data with field name 'file'.
    """
    logger.info(f"[ChatKit Upload] === REQUEST START ===")

    # Log request details
    content_type = request.headers.get("content-type", "")
    logger.info(f"[ChatKit Upload] Content-Type: {content_type}")

    # Parse form data
    try:
        form = await request.form()
        logger.info(f"[ChatKit Upload] Form fields: {list(form.keys())}")
    except Exception as e:
        logger.error(f"[ChatKit Upload] Form parse error: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": "form_parse_error", "message": str(e)}
        )

    def _is_upload_file(v: object) -> bool:
        return isinstance(v, (UploadFile, StarletteUploadFile)) or (
            hasattr(v, "filename") and hasattr(v, "read")
        )

    # Get file from form - ChatKit commonly uses 'file', but we also accept any UploadFile field
    file = form.get("file")
    if file is None:
        # Fallback: find first upload-like field
        for k in form.keys():
            v = form.get(k)
            if _is_upload_file(v):
                logger.info(f"[ChatKit Upload] Using fallback upload field '{k}'")
                file = v
                break

    if file is None:
        logger.error(f"[ChatKit Upload] No 'file' field in form")
        return JSONResponse(
            status_code=400,
            content={"error": "no_file", "message": "No file field in request"}
        )

    # Check if it's actually an uploaded file
    if not hasattr(file, 'filename') or not hasattr(file, 'read'):
        logger.error(f"[ChatKit Upload] 'file' is not an upload: {type(file)}")
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_file", "message": f"Expected file upload, got {type(file).__name__}"}
        )

    logger.info(f"[ChatKit Upload] File: {file.filename}, type: {file.content_type}")

    # Get user from auth header (not using Depends since we need to parse form first)
    user = await get_user_from_request(request, db)
    logger.info(f"[ChatKit Upload] User authenticated: {user.id}")

    # Cleanup expired files first so they don't count against the per-user limit
    await cleanup_expired_files_for_user(user.id, db)
    # Ensure room for a new upload (prevents 400 when user hits limit)
    await ensure_capacity_for_new_upload(user.id, db)

    # Check file count limit
    stmt = select(UploadedFile).where(
        and_(
            UploadedFile.user_id == user.id,
            UploadedFile.status != 'deleted',
            UploadedFile.deleted_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    existing_files = result.scalars().all()

    if len(existing_files) >= MAX_FILES_PER_USER:
        logger.error(f"[ChatKit Upload] max_files_exceeded user_id={user.id} count={len(existing_files)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "max_files_exceeded",
                "message": f"Maximum {MAX_FILES_PER_USER} files allowed. Please delete some files first."
            }
        )

    # Validate file
    filename = file.filename or "unnamed"
    content_type = file.content_type or ""

    # Read file to get size (we'll save it after validation)
    content = await file.read()
    file_size = len(content)
    await file.seek(0)  # Reset for saving

    # Some browsers/uploaders send filename like "blob" with no extension and/or mime as application/octet-stream.
    # Infer a better mime/type from bytes to avoid false 400s for valid images/PDFs.
    if (not content_type) or content_type == "application/octet-stream":
        try:
            import imghdr
            inferred_img = imghdr.what(None, h=content)
            if content[:4] == b"%PDF":
                content_type = "application/pdf"
                logger.info("[ChatKit Upload] Inferred PDF from bytes")
            elif inferred_img in ("png", "jpeg", "gif"):
                content_type = f"image/{'jpeg' if inferred_img == 'jpeg' else inferred_img}"
                logger.info(f"[ChatKit Upload] Inferred image/{inferred_img} from bytes")
        except Exception:
            pass

    is_valid, error_msg, file_type = FileProcessor.validate_file(filename, file_size, content_type)

    if not is_valid:
        logger.error(f"[ChatKit Upload] invalid_file user_id={user.id} filename={filename} mime={content_type} size={file_size} err={error_msg}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_file",
                "message": error_msg
            }
        )

    # Generate file ID and paths
    file_id = str(uuid.uuid4())
    user_dir = ensure_upload_dir(user.id)
    file_ext = Path(filename).suffix
    storage_path = user_dir / f"{file_id}{file_ext}"

    # Save file
    try:
        async with aiofiles.open(storage_path, 'wb') as out_file:
            await out_file.write(content)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "save_failed",
                "message": "Failed to save uploaded file"
            }
        )

    # Calculate expiry time
    retention_hours = await get_user_file_retention_hours(db, user.id)
    expires_at = datetime.utcnow() + timedelta(hours=retention_hours)

    # Create database record
    file_record = UploadedFile(
        file_id=file_id,
        user_id=user.id,
        file_name=filename,
        file_type=file_type,
        file_size=file_size,
        mime_type=content_type,
        status='processing',
        storage_path=str(storage_path),
        expires_at=expires_at
    )

    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)

    # Start background processing
    background_tasks.add_task(
        process_file_background,
        file_id=file_id,
        file_path=str(storage_path),
        file_type=file_type,
        file_name=filename,
        db_url=""
    )

    logger.info(f"ChatKit file uploaded: {file_id} ({filename}) by user {user.id}")

    # Return ChatKit-compatible response.
    #
    # IMPORTANT: ChatKit JS expects camelCase fields (mimeType, previewUrl).
    # We also include snake_case for backwards compatibility with any internal callers.
    chatkit_type: Literal["file", "image"] = "image" if file_type == "image" else "file"

    preview_url = None
    if file_type == "image":
        base_url = str(request.base_url).rstrip("/")
        preview_url = f"{base_url}/api/files/{file_id}/preview"

    payload = {
        "id": file_id,
        "name": filename,
        "type": chatkit_type,
        # camelCase (ChatKit JS)
        "mimeType": content_type,
        "previewUrl": preview_url,
        # snake_case (compat)
        "mime_type": content_type,
        "preview_url": preview_url,
    }

    return JSONResponse(content=payload)


@router.get("/{file_id}/preview")
async def get_file_preview(
    file_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get image preview for ChatKit attachments.

    Returns the actual image file for display in ChatKit.

    Note: This endpoint does NOT require authentication because:
    1. <img> tags cannot send Authorization headers
    2. The file_id is a random UUID that acts as a secret URL
    3. Files auto-expire after 24 hours

    Security is provided by:
    - Random UUID file IDs (unguessable)
    - Auto-expiry of files
    - Only the uploading user receives the file_id
    """
    from fastapi.responses import FileResponse

    # Look up file by ID only (no user validation for preview)
    # The random UUID provides security through obscurity
    stmt = select(UploadedFile).where(
        and_(
            UploadedFile.file_id == file_id,
            UploadedFile.deleted_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=404,
            detail={"error": "file_not_found", "message": "File not found"}
        )

    if file_record.is_expired:
        raise HTTPException(
            status_code=410,
            detail={"error": "file_expired", "message": "File has expired"}
        )

    if file_record.file_type != 'image':
        raise HTTPException(
            status_code=400,
            detail={"error": "not_image", "message": "Preview only available for images"}
        )

    storage_path = Path(file_record.storage_path)
    if not storage_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"error": "file_missing", "message": "File not found on disk"}
        )

    return FileResponse(
        path=storage_path,
        media_type=file_record.mime_type,
        filename=file_record.file_name
    )


@router.get("", response_model=FileListResponse)
async def list_files(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all files uploaded by the user."""
    stmt = select(UploadedFile).where(
        and_(
            UploadedFile.user_id == user.id,
            UploadedFile.deleted_at.is_(None)
        )
    ).order_by(UploadedFile.created_at.desc())

    result = await db.execute(stmt)
    files = result.scalars().all()

    # Filter out expired files
    active_files = [f for f in files if not f.is_expired]

    file_responses = [
        FileStatusResponse(
            file_id=f.file_id,
            file_name=f.file_name,
            file_type=f.file_type,
            file_size=f.file_size,
            status=f.status,
            processed_data=None,  # Don't include full data in list
            error_message=f.error_message,
            created_at=f.created_at.isoformat() + 'Z',
            expires_at=f.expires_at.isoformat() + 'Z' if f.expires_at else None
        )
        for f in active_files
    ]

    return FileListResponse(
        files=file_responses,
        total=len(file_responses),
        max_files=MAX_FILES_PER_USER
    )


# ============================================================================
# File Analysis Tool (for Schema Agent)
# ============================================================================

async def get_file_for_analysis(
    file_id: str,
    user_id: int,
    db: AsyncSession
) -> Optional[dict]:
    """
    Get file data for Schema Agent analysis.

    Returns processed data ready for agent use.
    """
    stmt = select(UploadedFile).where(
        and_(
            UploadedFile.file_id == file_id,
            UploadedFile.user_id == user_id,
            UploadedFile.status == 'ready',
            UploadedFile.deleted_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record or file_record.is_expired:
        return None

    return {
        'file_id': file_record.file_id,
        'file_name': file_record.file_name,
        'file_type': file_record.file_type,
        'processed_data': file_record.processed_data
    }


async def analyze_file_data(
    file_id: str,
    query: str,
    operation: str,
    user_id: int,
    db: AsyncSession
) -> dict:
    """
    Analyze file data based on user query.

    This function is called by Schema Agent's analyze_file tool.

    Args:
        file_id: The uploaded file ID
        query: User's question about the file
        operation: Type of analysis (summary, filter, aggregate, search, extract)
        user_id: Current user ID
        db: Database session

    Returns:
        Analysis results
    """
    file_data = await get_file_for_analysis(file_id, user_id, db)

    if not file_data:
        return {
            'error': 'File not found or not ready',
            'file_id': file_id
        }

    processed = file_data['processed_data'] or {}
    file_type = file_data['file_type']

    if operation == 'summary':
        if file_type in ['csv', 'excel']:
            return {
                'file_name': file_data['file_name'],
                'file_type': file_type,
                'row_count': processed.get('row_count', 0),
                'column_count': processed.get('column_count', 0),
                'columns': processed.get('columns', []),
                'statistics': processed.get('statistics', {}),
                'preview': processed.get('preview', [])[:5]
            }
        elif file_type == 'pdf':
            return {
                'file_name': file_data['file_name'],
                'file_type': file_type,
                'page_count': processed.get('page_count', 0),
                'table_count': len(processed.get('tables', [])),
                'text_preview': processed.get('text_content', '')[:1000]
            }
        elif file_type == 'image':
            return {
                'file_name': file_data['file_name'],
                'file_type': file_type,
                'width': processed.get('width'),
                'height': processed.get('height'),
                'format': processed.get('format')
            }

    elif operation == 'search':
        if file_type == 'pdf':
            text = processed.get('text_content', '')
            # Simple search
            query_lower = query.lower()
            lines = text.split('\n')
            matches = [line.strip() for line in lines if query_lower in line.lower()]
            return {
                'query': query,
                'matches': matches[:20],
                'total_matches': len(matches)
            }
        elif file_type in ['csv', 'excel']:
            preview = processed.get('preview', [])
            matches = []
            query_lower = query.lower()
            for row in preview:
                for val in row.values():
                    if query_lower in str(val).lower():
                        matches.append(row)
                        break
            return {
                'query': query,
                'matches': matches[:20],
                'total_matches': len(matches)
            }

    elif operation == 'aggregate':
        if file_type in ['csv', 'excel']:
            stats = processed.get('statistics', {})
            return {
                'statistics': stats,
                'row_count': processed.get('row_count', 0)
            }

    elif operation == 'extract':
        return {
            'file_name': file_data['file_name'],
            'data': processed
        }

    # Default: return full processed data
    return {
        'file_name': file_data['file_name'],
        'file_type': file_type,
        'data': processed
    }
