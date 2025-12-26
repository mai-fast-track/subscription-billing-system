"""
Authentication service
"""

from app.core.security import JWTHandler
from app.models.user import User
from app.schemas.auth import TelegramAuth
from app.services.base_service import BaseService


class AuthService(BaseService):
    """Authentication service"""

    async def get_or_create_user(self, telegram_id: int) -> User:
        """
        Get existing user or create new one by telegram_id
        """
        user = await self.uow.users.get_or_create_by_telegram_id(telegram_id)
        return user

    @staticmethod
    def create_token_for_user(user: User) -> str:
        """
        Create JWT token for user
        """
        token = JWTHandler.create_access_token(user_id=user.id, telegram_id=user.telegram_id, role=user.role.value)
        return token

    async def authenticate_telegram_user(self, auth_data: TelegramAuth) -> tuple[User, str]:
        """
        Complete authentication flow
        """
        user = await self.get_or_create_user(auth_data.telegram_id)
        token = self.create_token_for_user(user)
        return user, token
