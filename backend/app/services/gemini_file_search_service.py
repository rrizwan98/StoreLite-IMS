"""
Gemini File Search Service for managing user file uploads and semantic search.

Uses Google's Gemini Files API for:
- Uploading files for processing
- Using files with generate_content for semantic search

Note: Uses the standard Gemini Files API (not Vertex AI file_search_stores).
Files are uploaded and stored for 48 hours, then auto-deleted.

Version: 1.1
Date: December 30, 2025
"""

import os
import uuid
import asyncio
import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserFileSearchStore, UserFileDocument

logger = logging.getLogger(__name__)


class GeminiFileSearchService:
    """Service for Gemini Files API operations."""

    # Supported file types for Gemini Files API
    ALLOWED_MIME_TYPES = {
        # Documents
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
        "application/vnd.ms-excel",  # xls
        "text/csv",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
        "application/msword",  # doc
        "text/markdown",
        "text/plain",
        # Images
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
    }

    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

    def __init__(self):
        """Initialize the Gemini client."""
        self._client = None

    @property
    def client(self):
        """Lazy-load Gemini client."""
        if self._client is None:
            try:
                from google import genai
                api_key = os.getenv('GEMINI_API_KEY')
                if not api_key:
                    raise ValueError("GEMINI_API_KEY not configured")
                self._client = genai.Client(api_key=api_key)
            except ImportError:
                raise ImportError("google-genai package not installed. Run: pip install google-genai")
        return self._client

    def validate_file(self, content_type: str, file_size: int) -> tuple[bool, str]:
        """
        Validate file type and size.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if content_type not in self.ALLOWED_MIME_TYPES:
            allowed = ", ".join(sorted(self.ALLOWED_MIME_TYPES))
            return False, f"File type '{content_type}' not supported. Allowed: {allowed}"

        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE // (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return False, f"File size ({actual_mb:.1f}MB) exceeds maximum ({max_mb}MB)"

        return True, ""

    async def get_or_create_store(
        self,
        user_id: int,
        db: AsyncSession
    ) -> UserFileSearchStore:
        """
        Get existing FileSearchStore or create new one (ONE per user).

        Note: For standard Gemini API, we just track user's files in DB.
        There's no actual "store" in Gemini - files are uploaded individually.

        Args:
            user_id: User's ID
            db: Database session

        Returns:
            UserFileSearchStore instance
        """
        # Check if user already has a store
        result = await db.execute(
            select(UserFileSearchStore).where(
                UserFileSearchStore.user_id == user_id
            )
        )
        store = result.scalar_one_or_none()

        if store:
            logger.debug(f"Found existing store for user {user_id}: {store.id}")
            return store

        # Create new store record in DB (no actual Gemini store creation)
        logger.info(f"Creating new file store record for user {user_id}")

        store = UserFileSearchStore(
            user_id=user_id,
            gemini_store_id=f"user_{user_id}_files",  # Just a placeholder ID
            display_name=f"User {user_id} Files"
        )
        db.add(store)
        await db.commit()
        await db.refresh(store)

        logger.info(f"Created file store record: {store.id}")
        return store

    async def upload_file(
        self,
        user_id: int,
        filename: str,
        content: bytes,
        content_type: str,
        db: AsyncSession
    ) -> UserFileDocument:
        """
        Upload file to Gemini Files API.

        Args:
            user_id: User's ID
            filename: Original filename
            content: File content bytes
            content_type: MIME type
            db: Database session

        Returns:
            UserFileDocument instance
        """
        # Validate
        is_valid, error = self.validate_file(content_type, len(content))
        if not is_valid:
            raise ValueError(error)

        # Get or create store
        store = await self.get_or_create_store(user_id, db)

        # Save file temporarily (Windows-compatible path)
        temp_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "gemini_temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{filename}")

        with open(temp_path, "wb") as f:
            f.write(content)

        # Create DB record with "processing" status
        doc = UserFileDocument(
            store_id=store.id,
            original_filename=filename,
            display_name=filename,
            mime_type=content_type,
            file_size=len(content),
            status="processing"
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        logger.info(f"Created document record: {doc.id} for file {filename}")

        # Start background upload task
        try:
            task = asyncio.create_task(
                self._process_upload(store, doc.id, temp_path, content_type)
            )
            # Add callback to log any errors
            def handle_task_result(t):
                try:
                    t.result()
                except Exception as e:
                    logger.error(f"Background upload task failed: {e}")
            task.add_done_callback(handle_task_result)
            logger.info(f"Background upload task started for doc {doc.id}")
        except Exception as e:
            logger.error(f"Failed to start background task: {e}")
            # Update status to failed immediately
            doc.status = "failed"
            doc.error_message = f"Failed to start upload: {str(e)}"
            await db.commit()

        return doc

    async def _process_upload(
        self,
        store: UserFileSearchStore,
        doc_id: int,
        file_path: str,
        mime_type: str
    ):
        """
        Background task: Upload file to Gemini Files API.

        Args:
            store: User's FileSearchStore
            doc_id: Document ID in DB
            file_path: Path to temp file
            mime_type: MIME type of the file
        """
        logger.info(f"[BG Task] Starting upload for doc {doc_id}, file: {file_path}")

        # Import here to avoid circular imports
        from app.database import async_session

        try:
            from google.genai import types

            # Upload to Gemini Files API
            logger.info(f"[BG Task] Uploading to Gemini Files API: {file_path}")

            # Run synchronous upload in thread pool to not block event loop
            loop = asyncio.get_event_loop()

            def do_upload():
                return self.client.files.upload(
                    file=file_path,
                    config=types.UploadFileConfig(
                        display_name=os.path.basename(file_path).split('_', 1)[-1],  # Remove UUID prefix
                        mime_type=mime_type
                    )
                )

            logger.info(f"[BG Task] Calling Gemini API...")
            gemini_file = await loop.run_in_executor(None, do_upload)

            logger.info(f"[BG Task] File uploaded to Gemini: {gemini_file.name}, state={gemini_file.state}")

            # Small files are usually ACTIVE immediately, check first
            if gemini_file.state.name == "ACTIVE":
                logger.info(f"File already ACTIVE: {gemini_file.name}")
            else:
                # Wait for file to be processed (state should become ACTIVE)
                max_wait = 60  # 1 minute max for small files
                waited = 0
                poll_interval = 1  # Poll every 1 second

                while gemini_file.state.name == "PROCESSING" and waited < max_wait:
                    await asyncio.sleep(poll_interval)
                    waited += poll_interval

                    # Run get in thread pool too
                    def do_get():
                        return self.client.files.get(name=gemini_file.name)

                    gemini_file = await loop.run_in_executor(None, do_get)
                    logger.debug(f"Polling file state: {gemini_file.state.name}, waited={waited}s")

                if gemini_file.state.name == "FAILED":
                    raise Exception("Gemini file processing failed")

                if gemini_file.state.name != "ACTIVE":
                    raise TimeoutError(f"File processing timed out after {max_wait}s (state: {gemini_file.state.name})")

            # Update status in new session
            async with async_session() as new_db:
                result = await new_db.execute(
                    select(UserFileDocument).where(UserFileDocument.id == doc_id)
                )
                doc = result.scalar_one_or_none()

                if doc:
                    doc.status = "ready"
                    doc.gemini_doc_id = gemini_file.name  # e.g., "files/abc123"
                    await new_db.commit()
                    logger.info(f"Document {doc_id} is now ready: {gemini_file.name}")

        except Exception as e:
            import traceback
            logger.error(f"[BG Task] File upload failed for doc {doc_id}: {e}")
            logger.error(f"[BG Task] Traceback: {traceback.format_exc()}")

            # Update status to failed
            from app.database import async_session
            async with async_session() as new_db:
                result = await new_db.execute(
                    select(UserFileDocument).where(UserFileDocument.id == doc_id)
                )
                doc = result.scalar_one_or_none()

                if doc:
                    doc.status = "failed"
                    doc.error_message = str(e)[:500]  # Limit error message length
                    await new_db.commit()

        finally:
            # Cleanup temp file
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Removed temp file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove temp file: {e}")

    async def search_files(
        self,
        user_id: int,
        query: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Search user's files using Gemini's generate_content with file context.

        Args:
            user_id: User's ID
            query: Search query
            db: Database session

        Returns:
            Dict with 'answer' and 'citations'
        """
        # Get user's store
        result = await db.execute(
            select(UserFileSearchStore).where(
                UserFileSearchStore.user_id == user_id
            )
        )
        store = result.scalar_one_or_none()

        if not store:
            return {
                "answer": "You haven't uploaded any files yet. Please upload files first using the 'Use File Search' option in the + menu.",
                "citations": [],
                "has_files": False
            }

        # Get ready files
        docs_result = await db.execute(
            select(UserFileDocument).where(
                UserFileDocument.store_id == store.id,
                UserFileDocument.status == "ready"
            )
        )
        ready_docs = docs_result.scalars().all()

        if not ready_docs:
            # Check if any are still processing
            processing_result = await db.execute(
                select(UserFileDocument).where(
                    UserFileDocument.store_id == store.id,
                    UserFileDocument.status == "processing"
                )
            )
            processing_docs = processing_result.scalars().all()

            if processing_docs:
                return {
                    "answer": f"Your files are still processing ({len(processing_docs)} file(s)). Please wait a moment and try again.",
                    "citations": [],
                    "has_files": True,
                    "processing": True
                }

            return {
                "answer": "No files are ready for search. Please upload files first.",
                "citations": [],
                "has_files": False
            }

        # Build content with file references
        try:
            from google.genai import types

            logger.info(f"Searching {len(ready_docs)} files for user {user_id}: {query[:50]}...")

            # Get file references for all ready documents
            file_parts = []
            valid_docs = []

            for doc in ready_docs:
                if doc.gemini_doc_id:
                    try:
                        # Get the file from Gemini to ensure it still exists
                        gemini_file = self.client.files.get(name=doc.gemini_doc_id)
                        if gemini_file.state.name == "ACTIVE":
                            file_parts.append(gemini_file)
                            valid_docs.append(doc)
                        else:
                            logger.warning(f"File {doc.gemini_doc_id} not active: {gemini_file.state.name}")
                    except Exception as e:
                        logger.warning(f"Could not get file {doc.gemini_doc_id}: {e}")

            if not file_parts:
                return {
                    "answer": "Your files may have expired (Gemini files expire after 48 hours). Please re-upload your files.",
                    "citations": [],
                    "has_files": True,
                    "error": "Files expired"
                }

            # Create content with files and query
            # Use a system instruction to guide the model to search through the files
            system_instruction = """You are a helpful assistant that searches through the user's uploaded documents to answer their questions.

When answering:
1. Search through ALL provided documents carefully
2. Cite specific documents when providing information
3. If the answer is not in the documents, say so clearly
4. Provide direct quotes when relevant
5. Format citations as: [Source: filename]"""

            # Build content parts: first the files, then the query
            contents = []
            for f in file_parts:
                contents.append(f)
            contents.append(f"Based on the uploaded documents, please answer: {query}")

            response = self.client.models.generate_content(
                model="gemini-robotics-er-1.5-preview",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3  # Lower temperature for more factual responses
                )
            )

            answer = response.text if response.text else "No relevant information found in your files."

            # Build citations from the valid docs used
            citations = []
            for doc in valid_docs:
                citations.append({
                    "source": doc.original_filename,
                    "text": f"Document included in search context"
                })

            return {
                "answer": answer,
                "citations": citations,
                "has_files": True,
                "file_count": len(valid_docs)
            }

        except Exception as e:
            logger.error(f"File search failed: {e}")
            return {
                "answer": f"An error occurred while searching your files: {str(e)}",
                "citations": [],
                "has_files": True,
                "error": str(e)
            }

    async def list_files(
        self,
        user_id: int,
        db: AsyncSession
    ) -> List[UserFileDocument]:
        """
        List all files for user.

        Args:
            user_id: User's ID
            db: Database session

        Returns:
            List of UserFileDocument instances
        """
        result = await db.execute(
            select(UserFileSearchStore).where(
                UserFileSearchStore.user_id == user_id
            )
        )
        store = result.scalar_one_or_none()

        if not store:
            return []

        docs_result = await db.execute(
            select(UserFileDocument)
            .where(UserFileDocument.store_id == store.id)
            .order_by(UserFileDocument.created_at.desc())
        )
        return list(docs_result.scalars().all())

    async def get_file_status(
        self,
        user_id: int,
        doc_id: int,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        Get file processing status.

        Args:
            user_id: User's ID
            doc_id: Document ID
            db: Database session

        Returns:
            Dict with status info or None if not found
        """
        result = await db.execute(
            select(UserFileDocument)
            .join(UserFileSearchStore)
            .where(
                UserFileDocument.id == doc_id,
                UserFileSearchStore.user_id == user_id
            )
        )
        doc = result.scalar_one_or_none()

        if not doc:
            return None

        return {
            "id": doc.id,
            "filename": doc.original_filename,
            "status": doc.status,
            "error": doc.error_message
        }

    async def delete_file(
        self,
        user_id: int,
        doc_id: int,
        db: AsyncSession
    ) -> bool:
        """
        Delete file from Gemini and DB.

        Args:
            user_id: User's ID
            doc_id: Document ID
            db: Database session

        Returns:
            True if deleted, False if not found
        """
        # Get document with user verification
        result = await db.execute(
            select(UserFileDocument)
            .join(UserFileSearchStore)
            .where(
                UserFileDocument.id == doc_id,
                UserFileSearchStore.user_id == user_id
            )
        )
        doc = result.scalar_one_or_none()

        if not doc:
            return False

        # Delete from Gemini (if has gemini_doc_id)
        if doc.gemini_doc_id:
            try:
                self.client.files.delete(name=doc.gemini_doc_id)
                logger.info(f"Deleted file from Gemini: {doc.gemini_doc_id}")
            except Exception as e:
                logger.warning(f"Failed to delete from Gemini (may already be deleted/expired): {e}")

        # Delete from DB
        await db.delete(doc)
        await db.commit()

        logger.info(f"Deleted document from DB: {doc_id}")
        return True


# Singleton instance
gemini_file_search_service = GeminiFileSearchService()
