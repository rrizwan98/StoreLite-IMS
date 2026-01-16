"""
Support Service for handling support tickets and email notifications.

Provides functionality to:
- Create support tickets
- Send email notifications to support team
- Retrieve user tickets

v1.0: Initial implementation
"""

import logging
import os
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models import SupportTicket, User

logger = logging.getLogger(__name__)

# Environment configuration for support email
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@storelite.app")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@storelite.app")


@dataclass
class CreateTicketRequest:
    """Request data for creating a support ticket"""
    subject: str
    category: str
    description: str
    email: Optional[str] = None


@dataclass
class CreateTicketResult:
    """Result of creating a support ticket"""
    success: bool
    ticket_id: str
    message: str


class SupportService:
    """
    Service for managing support tickets and notifications.
    """

    def __init__(self):
        """Initialize support service."""
        self.support_email = SUPPORT_EMAIL

    def _generate_ticket_id(self) -> str:
        """
        Generate a unique ticket ID.
        Format: IMS-YYYY-NNNNNN (e.g., IMS-2025-001234)
        """
        import random
        year = datetime.utcnow().year
        random_num = random.randint(100000, 999999)
        return f"IMS-{year}-{random_num}"

    async def create_ticket(
        self,
        db: AsyncSession,
        request: CreateTicketRequest,
        user_id: Optional[int] = None,
    ) -> CreateTicketResult:
        """
        Create a new support ticket.

        Args:
            db: Database session
            request: Ticket creation request
            user_id: Optional user ID if authenticated

        Returns:
            CreateTicketResult with ticket ID
        """
        try:
            # Generate unique ticket ID
            ticket_id = self._generate_ticket_id()

            # Ensure ticket ID is unique
            max_retries = 5
            for _ in range(max_retries):
                existing = await db.execute(
                    select(SupportTicket).where(SupportTicket.ticket_id == ticket_id)
                )
                if not existing.scalar_one_or_none():
                    break
                ticket_id = self._generate_ticket_id()

            # Get user email if authenticated and no email provided
            contact_email = request.email
            if not contact_email and user_id:
                user = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user_obj = user.scalar_one_or_none()
                if user_obj:
                    contact_email = user_obj.email

            # Create ticket
            ticket = SupportTicket(
                ticket_id=ticket_id,
                user_id=user_id,
                subject=request.subject,
                category=request.category,
                description=request.description,
                email=contact_email,
                status="open",
            )

            db.add(ticket)
            await db.commit()
            await db.refresh(ticket)

            logger.info(f"Created support ticket: {ticket_id}")

            # Send email notification (async/background)
            try:
                await self._send_notification_email(ticket, contact_email)
            except Exception as e:
                # Log but don't fail ticket creation if email fails
                logger.warning(f"Failed to send notification email for ticket {ticket_id}: {e}")

            return CreateTicketResult(
                success=True,
                ticket_id=ticket_id,
                message="Your support ticket has been submitted. We'll respond within 24 hours.",
            )

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create support ticket: {e}")
            raise Exception(f"Failed to create support ticket: {e}")

    async def get_user_tickets(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 20,
    ) -> List[SupportTicket]:
        """
        Get tickets for a specific user.

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of tickets to return

        Returns:
            List of support tickets
        """
        result = await db.execute(
            select(SupportTicket)
            .where(SupportTicket.user_id == user_id)
            .order_by(desc(SupportTicket.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_ticket_by_id(
        self,
        db: AsyncSession,
        ticket_id: str,
        user_id: Optional[int] = None,
    ) -> Optional[SupportTicket]:
        """
        Get a specific ticket by ID.

        Args:
            db: Database session
            ticket_id: Ticket ID (e.g., "IMS-2025-001234")
            user_id: Optional user ID for authorization check

        Returns:
            SupportTicket or None
        """
        query = select(SupportTicket).where(SupportTicket.ticket_id == ticket_id)

        # If user_id provided, ensure ticket belongs to user
        if user_id:
            query = query.where(SupportTicket.user_id == user_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def _send_notification_email(
        self,
        ticket: SupportTicket,
        contact_email: Optional[str],
    ) -> bool:
        """
        Send email notification to support team.

        Args:
            ticket: The created support ticket
            contact_email: User's contact email

        Returns:
            True if email sent successfully
        """
        # Skip if SMTP not configured
        if not SMTP_USER or not SMTP_PASSWORD:
            logger.info(f"SMTP not configured, skipping email for ticket {ticket.ticket_id}")
            return False

        try:
            # Build email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[IMS Support] New Ticket: {ticket.ticket_id} - {ticket.subject}"
            msg["From"] = SMTP_FROM
            msg["To"] = self.support_email

            # Plain text version
            text_content = f"""
New Support Ticket Received
============================

Ticket ID: {ticket.ticket_id}
Category: {ticket.category.replace('_', ' ').title()}
Status: Open
Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

---

User Information:
- User ID: {ticket.user_id or 'Anonymous'}
- Email: {contact_email or 'Not provided'}

---

Subject: {ticket.subject}

Description:
{ticket.description}

---

This ticket was automatically generated from the StoreLite IMS help system.
            """

            # HTML version
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f5f5f5; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 24px 30px; color: white;">
            <h1 style="margin: 0; font-size: 20px;">New Support Ticket</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">{ticket.ticket_id}</p>
        </div>

        <!-- Ticket Info -->
        <div style="padding: 30px;">
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
                <tr>
                    <td style="padding: 8px 0; color: #6b7280; width: 120px;">Category:</td>
                    <td style="padding: 8px 0; font-weight: 500;">
                        <span style="display: inline-block; padding: 4px 12px; background: #f3f4f6; border-radius: 12px; font-size: 13px;">
                            {ticket.category.replace('_', ' ').title()}
                        </span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Status:</td>
                    <td style="padding: 8px 0;">
                        <span style="display: inline-block; padding: 4px 12px; background: #dcfce7; color: #166534; border-radius: 12px; font-size: 13px;">
                            Open
                        </span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">Created:</td>
                    <td style="padding: 8px 0;">{ticket.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6b7280;">User:</td>
                    <td style="padding: 8px 0;">{contact_email or 'Anonymous'} (ID: {ticket.user_id or 'N/A'})</td>
                </tr>
            </table>

            <!-- Subject -->
            <div style="margin-bottom: 20px;">
                <h3 style="margin: 0 0 8px 0; color: #1f2937; font-size: 16px;">Subject</h3>
                <p style="margin: 0; padding: 12px 16px; background: #f9fafb; border-radius: 6px; color: #374151;">
                    {ticket.subject}
                </p>
            </div>

            <!-- Description -->
            <div>
                <h3 style="margin: 0 0 8px 0; color: #1f2937; font-size: 16px;">Description</h3>
                <div style="padding: 16px; background: #f9fafb; border-radius: 6px; color: #374151; white-space: pre-wrap; line-height: 1.6;">
{ticket.description}
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div style="background: #f9fafb; padding: 16px 30px; border-top: 1px solid #e5e7eb;">
            <p style="margin: 0; color: #6b7280; font-size: 12px; text-align: center;">
                This ticket was automatically generated from StoreLite IMS.
            </p>
        </div>
    </div>
</body>
</html>
            """

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, self.support_email, msg.as_string())

            logger.info(f"Support notification email sent for ticket {ticket.ticket_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send support notification email: {e}")
            raise


# Singleton instance
_support_service: Optional[SupportService] = None


def get_support_service() -> SupportService:
    """Get singleton support service instance."""
    global _support_service
    if _support_service is None:
        _support_service = SupportService()
    return _support_service
