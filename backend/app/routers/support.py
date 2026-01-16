"""
Support Router - API endpoints for support ticket management.

Endpoints:
- POST /support/tickets - Create a new support ticket
- GET /support/tickets - List user's tickets
- GET /support/tickets/{ticket_id} - Get specific ticket

v1.0: Initial implementation
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import get_optional_user, get_current_user
from app.services.support_service import (
    get_support_service,
    CreateTicketRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/support", tags=["support"])


# ============================================================================
# Pydantic Models
# ============================================================================

class CreateTicketRequestModel(BaseModel):
    """Request model for creating a support ticket"""
    subject: str = Field(..., min_length=1, max_length=255, description="Ticket subject")
    category: str = Field(
        ...,
        description="Ticket category",
        pattern="^(bug_report|feature_request|question|other)$"
    )
    description: str = Field(..., min_length=10, description="Detailed description of the issue")
    email: Optional[EmailStr] = Field(None, description="Contact email for response")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Cannot connect to database",
                "category": "bug_report",
                "description": "When I try to connect my PostgreSQL database, I get a timeout error after 30 seconds.",
                "email": "user@example.com"
            }
        }


class CreateTicketResponseModel(BaseModel):
    """Response model for created ticket"""
    success: bool
    ticket_id: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "ticket_id": "IMS-2025-123456",
                "message": "Your support ticket has been submitted. We'll respond within 24 hours."
            }
        }


class TicketModel(BaseModel):
    """Response model for a support ticket"""
    id: int
    ticket_id: str
    user_id: Optional[int]
    subject: str
    category: str
    description: str
    email: Optional[str]
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/tickets",
    response_model=CreateTicketResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create a support ticket",
    description="Submit a new support ticket. Can be used by authenticated or anonymous users.",
)
async def create_ticket(
    request: CreateTicketRequestModel,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """
    Create a new support ticket.

    - **subject**: Brief description of the issue (required)
    - **category**: One of: bug_report, feature_request, question, other
    - **description**: Detailed description of the issue (min 10 chars)
    - **email**: Contact email (optional, auto-filled from account if logged in)

    Returns ticket ID on success. Email notification sent to support team.
    """
    try:
        service = get_support_service()

        user_id = current_user.id if current_user else None

        ticket_request = CreateTicketRequest(
            subject=request.subject,
            category=request.category,
            description=request.description,
            email=request.email,
        )

        result = await service.create_ticket(db, ticket_request, user_id)

        return CreateTicketResponseModel(
            success=result.success,
            ticket_id=result.ticket_id,
            message=result.message,
        )

    except Exception as e:
        logger.error(f"Failed to create support ticket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create support ticket: {str(e)}",
        )


@router.get(
    "/tickets",
    response_model=List[TicketModel],
    summary="List user's tickets",
    description="Get all support tickets for the authenticated user.",
)
async def list_tickets(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    List support tickets for the authenticated user.

    Returns list of tickets ordered by creation date (newest first).
    """
    try:
        service = get_support_service()

        tickets = await service.get_user_tickets(db, current_user.id, limit)

        return [
            TicketModel(
                id=ticket.id,
                ticket_id=ticket.ticket_id,
                user_id=ticket.user_id,
                subject=ticket.subject,
                category=ticket.category,
                description=ticket.description,
                email=ticket.email,
                status=ticket.status,
                created_at=ticket.created_at.isoformat(),
                updated_at=ticket.updated_at.isoformat(),
            )
            for ticket in tickets
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list support tickets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list support tickets: {str(e)}",
        )


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketModel,
    summary="Get ticket details",
    description="Get details of a specific support ticket.",
)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get details of a specific support ticket.

    - **ticket_id**: The ticket ID (e.g., "IMS-2025-123456")

    Only returns tickets belonging to the authenticated user.
    """
    try:
        service = get_support_service()

        ticket = await service.get_ticket_by_id(db, ticket_id, current_user.id)

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {ticket_id} not found",
            )

        return TicketModel(
            id=ticket.id,
            ticket_id=ticket.ticket_id,
            user_id=ticket.user_id,
            subject=ticket.subject,
            category=ticket.category,
            description=ticket.description,
            email=ticket.email,
            status=ticket.status,
            created_at=ticket.created_at.isoformat(),
            updated_at=ticket.updated_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get support ticket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get support ticket: {str(e)}",
        )
