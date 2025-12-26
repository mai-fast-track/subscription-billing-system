"""
User service for bot
"""

import logging

from billing_core_api_client.models import User
from bot.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class UserService:
    """Service for user operations"""

    def __init__(self):
        self._auth_service = AuthService()

    async def get_or_create_user_by_telegram_id(self, telegram_id: int) -> User:
        """
        Get or create user by Telegram ID

        This will authenticate the user, which creates them if they don't exist

        Args:
            telegram_id: Telegram user ID

        Returns:
            User object

        Raises:
            Exception: If operation fails
        """
        try:
            user, _ = await self._auth_service.authenticate_telegram_user(telegram_id)
            return user
        except Exception as e:
            logger.error(f"Failed to get or create user: {e}")
            raise
