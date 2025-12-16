"""
Gmail OAuth2 Service for handling Google OAuth2 authorization flow.
Manages token exchange, refresh, and secure storage.
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from dataclasses import dataclass

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import UserConnection
from app.services.encryption_service import encrypt_token, decrypt_token, EncryptionError

logger = logging.getLogger(__name__)


# Gmail API scopes - minimal permissions
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",      # Send emails only
    "https://www.googleapis.com/auth/userinfo.email",  # Get user email
    "openid",                                           # OpenID Connect
]


class GmailOAuthError(Exception):
    """Base exception for Gmail OAuth errors"""
    pass


class GmailNotConnectedError(GmailOAuthError):
    """Raised when Gmail is not connected for a user"""
    pass


class GmailTokenError(GmailOAuthError):
    """Raised when token operations fail"""
    pass


@dataclass
class TokenData:
    """OAuth2 token data container"""
    access_token: str
    refresh_token: Optional[str]
    expiry: Optional[datetime]
    email: Optional[str] = None
    scopes: Optional[list] = None


class GmailOAuthService:
    """
    Service for managing Gmail OAuth2 authorization.
    Handles authorization URL generation, token exchange, refresh, and storage.
    """

    def __init__(self):
        """Initialize OAuth service with Google credentials from environment."""
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/gmail/callback")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

        if not self.client_id or not self.client_secret:
            logger.warning(
                "GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set. "
                "Gmail OAuth will not work until configured."
            )

    def _get_client_config(self) -> dict:
        """Get OAuth client configuration for Flow."""
        return {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri],
            }
        }

    def get_authorization_url(self, state: str) -> str:
        """
        Generate Google OAuth2 authorization URL.

        Args:
            state: CSRF protection state token

        Returns:
            Authorization URL to redirect user to

        Raises:
            GmailOAuthError: If OAuth is not configured
        """
        if not self.client_id or not self.client_secret:
            raise GmailOAuthError(
                "Gmail OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
            )

        flow = Flow.from_client_config(
            self._get_client_config(),
            scopes=GMAIL_SCOPES,
            redirect_uri=self.redirect_uri,
        )

        authorization_url, _ = flow.authorization_url(
            access_type="offline",           # Get refresh token
            include_granted_scopes="true",   # Incremental auth
            state=state,
            prompt="consent",                # Force consent to get refresh token
        )

        logger.info(f"Generated Gmail authorization URL with state: {state[:8]}...")
        return authorization_url

    async def exchange_code_for_tokens(self, code: str) -> TokenData:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            TokenData with access token, refresh token, and expiry

        Raises:
            GmailTokenError: If token exchange fails
        """
        try:
            flow = Flow.from_client_config(
                self._get_client_config(),
                scopes=GMAIL_SCOPES,
                redirect_uri=self.redirect_uri,
            )

            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Get user email
            email = await self._get_user_email(credentials)

            token_data = TokenData(
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                expiry=credentials.expiry,
                email=email,
                scopes=list(credentials.scopes) if credentials.scopes else GMAIL_SCOPES,
            )

            logger.info(f"Successfully exchanged code for tokens. Email: {email}")
            return token_data

        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            raise GmailTokenError(f"Failed to exchange authorization code: {e}")

    async def _get_user_email(self, credentials: Credentials) -> Optional[str]:
        """
        Get user's email from Google UserInfo API.

        Args:
            credentials: Valid OAuth2 credentials

        Returns:
            User's email address or None if failed
        """
        try:
            service = build("oauth2", "v2", credentials=credentials)
            user_info = service.userinfo().get().execute()
            return user_info.get("email")
        except Exception as e:
            logger.warning(f"Failed to get user email: {e}")
            return None

    async def refresh_access_token(self, refresh_token: str) -> TokenData:
        """
        Refresh an expired access token.

        Args:
            refresh_token: The refresh token to use

        Returns:
            TokenData with new access token and expiry

        Raises:
            GmailTokenError: If refresh fails
        """
        try:
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=GMAIL_SCOPES,
            )

            # Refresh the token
            request = Request()
            credentials.refresh(request)

            token_data = TokenData(
                access_token=credentials.token,
                refresh_token=refresh_token,  # Refresh token doesn't change
                expiry=credentials.expiry,
            )

            logger.info("Successfully refreshed access token")
            return token_data

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise GmailTokenError(f"Failed to refresh access token: {e}")

    async def revoke_tokens(self, access_token: str) -> bool:
        """
        Revoke OAuth2 tokens with Google.

        Args:
            access_token: The access token to revoke

        Returns:
            True if revocation successful, False otherwise
        """
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": access_token},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

            if response.status_code == 200:
                logger.info("Successfully revoked tokens")
                return True
            else:
                logger.warning(f"Token revocation returned status {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Token revocation failed: {e}")
            return False

    async def save_tokens_to_db(
        self,
        db: AsyncSession,
        user_id: int,
        token_data: TokenData,
    ) -> None:
        """
        Save encrypted OAuth tokens to database.

        Args:
            db: Database session
            user_id: User ID to save tokens for
            token_data: Token data to save
        """
        try:
            # Get user connection
            result = await db.execute(
                select(UserConnection).where(UserConnection.user_id == user_id)
            )
            connection = result.scalar_one_or_none()

            if not connection:
                raise GmailOAuthError(f"No connection found for user {user_id}")

            # Encrypt tokens
            connection.gmail_access_token = encrypt_token(token_data.access_token)
            connection.gmail_refresh_token = encrypt_token(token_data.refresh_token) if token_data.refresh_token else None

            # Convert expiry to naive UTC datetime for database (TIMESTAMP WITHOUT TIME ZONE)
            if token_data.expiry:
                if token_data.expiry.tzinfo is not None:
                    # Convert to UTC and remove timezone info
                    connection.gmail_token_expiry = token_data.expiry.replace(tzinfo=None)
                else:
                    connection.gmail_token_expiry = token_data.expiry
            else:
                connection.gmail_token_expiry = None

            connection.gmail_email = token_data.email
            # Use naive UTC datetime for connected_at (database expects TIMESTAMP WITHOUT TIME ZONE)
            connection.gmail_connected_at = datetime.utcnow()
            connection.gmail_scopes = token_data.scopes

            await db.commit()
            logger.info(f"Saved Gmail tokens for user {user_id}")

        except EncryptionError as e:
            await db.rollback()
            raise GmailTokenError(f"Failed to encrypt tokens: {e}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to save tokens to database: {e}")
            raise GmailOAuthError(f"Failed to save tokens: {e}")

    async def get_valid_access_token(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> str:
        """
        Get a valid access token for a user, refreshing if necessary.

        Args:
            db: Database session
            user_id: User ID to get token for

        Returns:
            Valid access token

        Raises:
            GmailNotConnectedError: If Gmail not connected
            GmailTokenError: If token refresh fails
        """
        result = await db.execute(
            select(UserConnection).where(UserConnection.user_id == user_id)
        )
        connection = result.scalar_one_or_none()

        if not connection or not connection.gmail_access_token:
            raise GmailNotConnectedError("Gmail is not connected for this user")

        # Check if token is expired (with 5 minute buffer)
        if connection.gmail_token_expiry:
            buffer_time = datetime.now(timezone.utc) + timedelta(minutes=5)
            # Make token_expiry timezone-aware if it isn't
            token_expiry = connection.gmail_token_expiry
            if token_expiry.tzinfo is None:
                token_expiry = token_expiry.replace(tzinfo=timezone.utc)
            if token_expiry < buffer_time:
                logger.info(f"Access token expired for user {user_id}, refreshing...")

                if not connection.gmail_refresh_token:
                    raise GmailTokenError("No refresh token available. Please reconnect Gmail.")

                try:
                    refresh_token = decrypt_token(connection.gmail_refresh_token)
                    new_tokens = await self.refresh_access_token(refresh_token)
                    new_tokens.email = connection.gmail_email  # Preserve email
                    new_tokens.scopes = connection.gmail_scopes  # Preserve scopes
                    await self.save_tokens_to_db(db, user_id, new_tokens)
                    return new_tokens.access_token
                except Exception as e:
                    logger.error(f"Token refresh failed for user {user_id}: {e}")
                    raise GmailTokenError(f"Failed to refresh token: {e}. Please reconnect Gmail.")

        # Return existing token
        return decrypt_token(connection.gmail_access_token)

    async def disconnect_gmail(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> bool:
        """
        Disconnect Gmail for a user (revoke tokens and clear from DB).

        Args:
            db: Database session
            user_id: User ID to disconnect

        Returns:
            True if disconnection successful
        """
        try:
            result = await db.execute(
                select(UserConnection).where(UserConnection.user_id == user_id)
            )
            connection = result.scalar_one_or_none()

            if not connection:
                return False

            # Revoke token with Google if we have one
            if connection.gmail_access_token:
                try:
                    access_token = decrypt_token(connection.gmail_access_token)
                    await self.revoke_tokens(access_token)
                except Exception as e:
                    logger.warning(f"Failed to revoke token with Google: {e}")

            # Clear Gmail fields
            connection.gmail_access_token = None
            connection.gmail_refresh_token = None
            connection.gmail_token_expiry = None
            connection.gmail_email = None
            connection.gmail_connected_at = None
            connection.gmail_recipient_email = None
            connection.gmail_scopes = None

            await db.commit()
            logger.info(f"Disconnected Gmail for user {user_id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to disconnect Gmail: {e}")
            raise GmailOAuthError(f"Failed to disconnect Gmail: {e}")


# Singleton instance
_gmail_oauth_service: Optional[GmailOAuthService] = None


def get_gmail_oauth_service() -> GmailOAuthService:
    """Get singleton Gmail OAuth service instance."""
    global _gmail_oauth_service
    if _gmail_oauth_service is None:
        _gmail_oauth_service = GmailOAuthService()
    return _gmail_oauth_service
