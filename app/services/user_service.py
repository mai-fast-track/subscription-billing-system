"""
User service - бизнес-логика для работы с пользователями
"""

from typing import Optional

from app.models.user import User
from app.services.base_service import BaseService


class UserService(BaseService):
    """Сервис для работы с пользователями"""

    async def get_user_by_id(self, user_id: int) -> User:
        """Получить пользователя по ID или выбросить исключение"""
        user = await self.uow.users.get_by_id_or_raise(user_id)
        return user

    async def get_user_by_telegram_id(self, telegram_id: int) -> User:
        """Получить пользователя по telegram_id"""
        user = await self.uow.users.get_by_telegram_id_or_raise(telegram_id)
        return user

    async def get_user_by_telegram_id_safe(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя безопасно (без исключения, если не найден)"""
        user = await self.uow.users.get_by_telegram_id(telegram_id)
        return user

    async def update_user_by_telegram_id(self, user_id: int, new_telegram_id: int) -> User:
        """Обновить телеграм пользователя"""
        user = await self.uow.users.update_telegram_id(user_id, new_telegram_id)
        return user

    async def create_user(self, telegram_id: int) -> User:
        """Создать нового пользователя"""
        user = await self.uow.users.create_user(telegram_id)
        return user

    async def get_or_create_user_by_telegram_id(self, telegram_id: int) -> User:
        """Получить пользователя или создать, если не существует"""
        user = await self.uow.users.get_or_create_by_telegram_id(telegram_id)
        return user

    async def get_all_users(self, skip: int = 0, limit: int = 100):
        """Получить всех пользователей с пагинацией"""
        users = await self.uow.users.get_all_users(skip=skip, limit=limit)
        return users
