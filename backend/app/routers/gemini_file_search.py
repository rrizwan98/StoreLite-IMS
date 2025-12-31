"""
Gemini File Search Router.

Handles file uploads to Gemini File Search API for semantic search.
Files are stored in per-user FileSearchStores with embeddings for RAG.

Version: 1.0
Date: December 30, 2025
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.routers.auth import get_current_user
from app.services.gemini_file_search_service import gemini_file_search_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/file-search", tags=["gemini-file-search"])


# ============================================================================
# Pydantic Models
# ============================================================================

class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    id: int
    filename: str
    status: str
    message: str


class FileDocument(BaseModel):
    """Response model for a file document."""
    id: int
    filename: str
    status: str
    size: int
    mime_type: str
    created_at: str
    error: Optional[str] = None


class FileListResponse(BaseModel):
    """Response model for listing files."""
    files: List[FileDocument]
    total: int


class FileStatusResponse(BaseModel):
    """Response model for file status."""
    id: int
    filename: str
    status: str
    error: Optional[str] = None


class DeleteFileResponse(BaseModel):
    """Response model for file deletion."""
    success: bool
    message: str


class SearchResponse(BaseModel):
    """Response model for file search."""
    answer: str
    citations: List[dict]
    has_files: bool
    file_count: Optional[int] = None
    processing: Optional[bool] = None
    error: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="File to upload for semantic search"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload file to user's Gemini FileSearchStore.

    Supported file types:
    - Documents: PDF, DOCX, DOC, TXT, MD, CSV
    - Spreadsheets: XLSX, XLS
    - Images: PNG, JPG, JPEG, GIF, WEBP

    Maximum file size: 100MB

    The file will be processed and indexed for semantic search.
    Status will be 'processing' initially, then 'ready' when complete.
    """
    try:
        # Read file content
        content = await file.read()
        content_type = file.content_type or "application/octet-stream"

        logger.info(f"[FileSearch] Upload request: {file.filename}, type={content_type}, size={len(content)}")

        # Upload to Gemini
        doc = await gemini_file_search_service.upload_file(
            user_id=user.id,
            filename=file.filename or "unnamed",
            content=content,
            content_type=content_type,
            db=db
        )

        logger.info(f"[FileSearch] File uploaded: doc_id={doc.id}, status={doc.status}")

        return FileUploadResponse(
            id=doc.id,
            filename=doc.original_filename,
            status=doc.status,
            message="File uploaded. Processing embeddings..."
        )

    except ValueError as e:
        logger.error(f"[FileSearch] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"[FileSearch] Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/files", response_model=FileListResponse)
async def list_files(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all files uploaded by the user.

    Returns files with their processing status:
    - processing: File is being indexed
    - ready: File is ready for search
    - failed: Processing failed (check error field)
    """
    try:
        docs = await gemini_file_search_service.list_files(user.id, db)

        files = [
            FileDocument(
                id=doc.id,
                filename=doc.original_filename,
                status=doc.status,
                size=doc.file_size,
                mime_type=doc.mime_type,
                created_at=doc.created_at.isoformat() + 'Z',
                error=doc.error_message
            )
            for doc in docs
        ]

        return FileListResponse(
            files=files,
            total=len(files)
        )

    except Exception as e:
        logger.error(f"[FileSearch] List files error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/files/{doc_id}/status", response_model=FileStatusResponse)
async def get_file_status(
    doc_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get file processing status.

    Use this endpoint to poll for processing completion.
    """
    try:
        status = await gemini_file_search_service.get_file_status(user.id, doc_id, db)

        if not status:
            raise HTTPException(status_code=404, detail="File not found")

        return FileStatusResponse(
            id=status["id"],
            filename=status["filename"],
            status=status["status"],
            error=status.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FileSearch] Get status error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get file status: {str(e)}")


@router.delete("/files/{doc_id}", response_model=DeleteFileResponse)
async def delete_file(
    doc_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a file from the user's FileSearchStore.

    This removes the file from both the database and Gemini's storage.
    The file will no longer be searchable.
    """
    try:
        success = await gemini_file_search_service.delete_file(user.id, doc_id, db)

        if not success:
            raise HTTPException(status_code=404, detail="File not found")

        return DeleteFileResponse(
            success=True,
            message="File deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FileSearch] Delete error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.post("/search", response_model=SearchResponse)
async def search_files(
    query: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search user's uploaded files using semantic search.

    This endpoint performs a semantic search across all user's uploaded files
    and returns an answer with citations.

    Note: This endpoint is primarily for testing. In production, the Schema Agent
    will use the file_search tool which calls the service directly.
    """
    try:
        result = await gemini_file_search_service.search_files(user.id, query, db)

        return SearchResponse(
            answer=result["answer"],
            citations=result.get("citations", []),
            has_files=result.get("has_files", False),
            file_count=result.get("file_count"),
            processing=result.get("processing"),
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"[FileSearch] Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
