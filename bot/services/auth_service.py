"""
Authentication service for bot
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import jwt

api_client_path = Path(__file__).parent.parent / "api-client"
if str(api_client_path) not in sys.path:
    sys.path.insert(0, str(api_client_path))

from billing_core_api_client.api.authentication import auth_telegram_api_v1_auth_telegram_post
from billing_core_api_client.api.users import get_user_api_v1_users_user_id_get
from billing_core_api_client.models import HTTPValidationError, TelegramAuth, Token, User
from bot.core.api_client import get_api_client, get_authenticated_client

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations"""

    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key  # For JWT decoding if needed

    def _decode_token(self, token: str) -> Optional[dict]:
        """
        Decode JWT token to get user info

        Args:
            token: JWT token string

        Returns:
            Decoded token payload or None
        """
        try:
            # Decode without verification to get user_id
            decoded = jwt.decode(token, options={"verify_signature": False})
            return decoded
        except Exception as e:
            logger.warning(f"Failed to decode token: {e}")
            return None

    async def authenticate_telegram_user(self, telegram_id: int) -> tuple[User, Token]:
        """
        Authenticate user via Telegram ID

        This endpoint creates user if not exists and returns token.
        We decode the token to get user_id, then fetch user details.

        Args:
            telegram_id: Telegram user ID

        Returns:
            Tuple of (User, Token)

        Raises:
            Exception: If authentication fails
        """
        client = get_api_client()

        try:
            async with client:
                # Authenticate and get token
                token_response = await auth_telegram_api_v1_auth_telegram_post.asyncio(
                    client=client, body=TelegramAuth(telegram_id=telegram_id)
                )

                # Check for validation errors
                if isinstance(token_response, HTTPValidationError):
                    logger.error(f"Validation error authenticating telegram user {telegram_id}: {token_response}")
                    raise Exception(f"Validation error: {token_response}")

                # Happy path: check token response
                if not isinstance(token_response, Token):
                    logger.error(f"Invalid response type when authenticating: {type(token_response)}")
                    raise Exception("Failed to authenticate: invalid response")

                token = token_response

                # Decode token to get user_id
                token_payload = self._decode_token(token.access_token)
                if not token_payload or "user_id" not in token_payload:
                    raise Exception("Failed to decode token or user_id not found in token")

                user_id = token_payload["user_id"]

                # Get user info using authenticated client
                auth_client = get_authenticated_client(token.access_token)
                async with auth_client:
                    user_response = await get_user_api_v1_users_user_id_get.asyncio(user_id=user_id, client=auth_client)

                    # Check for validation errors
                    if isinstance(user_response, HTTPValidationError):
                        logger.error(f"Validation error getting user {user_id}: {user_response}")
                        raise Exception(f"Validation error: {user_response}")

                    # Happy path: check user response
                    if not isinstance(user_response, User):
                        logger.error(f"Invalid response type when getting user: {type(user_response)}")
                        raise Exception("Failed to get user: invalid response")

                    return user_response, token

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise
