# repository/user.py
from collections.abc import Sequence
from datetime import datetime
from typing import Optional

from app.core.exceptions import UserNotFound
from app.database.base_repository import BaseRepository
from app.models import User


class UserRepository(BaseRepository[User]):
    """Repository для управления пользователями"""

    def _get_model(self) -> type[User]:
        return User

    # ========== GET методы ==========

    def _get_not_found_exception(self, id_: int) -> Exception:
        return UserNotFound(id_)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по telegram_id"""
        return await self.get_by(telegram_id=telegram_id)

    async def get_by_telegram_id_or_raise(self, telegram_id: int) -> User:
        """Получить пользователя по telegram_id или выбросить исключение"""
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            raise UserNotFound(telegram_id)
        return user

    # async def get_by_id_or_raise(self, user_id: int) -> User:
    #     """Получить пользователя по ID или выбросить исключение"""
    #     user = await self.get_by_id(user_id)
    #     if not user:
    #         raise UserNotFound(user_id)
    #     return user

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        """Получить всех пользователей с пагинацией"""
        return await self.get_all(skip=skip, limit=limit)

    # ========== CREATE методы ==========

    async def create_user(self, telegram_id: int) -> User:
        """Создать нового пользователя"""
        if telegram_id <= 0:
            raise ValueError("Telegram ID должен быть положительным числом")

        user = User(telegram_id=telegram_id)
        return await self.create(user)

    async def get_or_create_by_telegram_id(self, telegram_id: int) -> User:
        """Получить пользователя или создать, если не существует"""
        # Пытаемся получить
        user = await self.get_by_telegram_id(telegram_id)

        # Если не найден - создаем
        if not user:
            user = await self.create_user(telegram_id)

        return user

    # ========== UPDATE методы ==========

    async def update_telegram_id(self, user_id: int, new_telegram_id: int) -> User:
        """Обновить telegram_id пользователя"""
        user = await self.get_by_id_or_raise(user_id)

        existing = await self.get_by_telegram_id(new_telegram_id)
        if existing and existing.id != user.id:
            raise ValueError(f"Telegram ID {new_telegram_id} уже используется другим пользователем")

        user.telegram_id = new_telegram_id
        user.updated_at = datetime.utcnow()
        return await self.update(user)

    async def update_user_profile(
        self,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> User:
        """Обновить профиль пользователя"""
        user = await self.get_by_id_or_raise(user_id)

        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if username is not None:
            user.username = username

        user.updated_at = datetime.utcnow()
        return await self.update(user)

    async def deactivate_user(self, user_id: int) -> User:
        """Деактивировать пользователя"""
        user = await self.get_by_id_or_raise(user_id)
        user.is_active = False
        user.updated_at = datetime.utcnow()
        return await self.update(user)

    async def activate_user(self, user_id: int) -> User:
        """Активировать пользователя"""
        user = await self.get_by_id_or_raise(user_id)
        user.is_active = True
        user.updated_at = datetime.utcnow()
        return await self.update(user)

    # ========== UTILITY методы ==========

    async def user_exists_by_telegram_id(self, telegram_id: int) -> bool:
        """Проверить существует ли пользователь по telegram_id"""
        user = await self.get_by_telegram_id(telegram_id)
        return user is not None

    async def count_active_users(self) -> int:
        """Получить количество активных пользователей"""
        return await self.count(is_active=True)

    async def count_total_users(self) -> int:
        """Получить общее количество пользователей"""
        return await self.count()

    async def update_saved_payment_method(self, user_id: int, payment_method_id: str) -> User:
        """Обновить сохраненный платежный метод пользователя"""
        user = await self.get_by_id_or_raise(user_id)
        user.saved_payment_method_id = payment_method_id
        user.updated_at = datetime.utcnow()
        return await self.update(user)

    async def clear_saved_payment_method(self, user_id: int) -> User:
        """Очистить сохраненный платежный метод пользователя"""
        user = await self.get_by_id_or_raise(user_id)
        user.saved_payment_method_id = None
        user.updated_at = datetime.utcnow()
        return await self.update(user)
