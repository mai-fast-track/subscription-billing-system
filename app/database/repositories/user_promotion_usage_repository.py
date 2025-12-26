"""
UserPromotionUsage repository - работа с использованием промокодов пользователями
"""

from typing import Optional

from app.database.base_repository import BaseRepository
from app.models.user_promotion_usage import UserPromotionUsage


class UserPromotionUsageRepository(BaseRepository[UserPromotionUsage]):
    """Repository для управления использованием промокодов пользователями"""

    def _get_model(self) -> type[UserPromotionUsage]:
        return UserPromotionUsage

    def _get_not_found_exception(self, id_: int) -> Exception:
        raise ValueError(f"UserPromotionUsage with id {id_} not found")

    async def has_user_used_promotion(self, user_id: int, promotion_id: int) -> bool:
        """Проверить, использовал ли пользователь промокод"""
        return await self.exists(user_id=user_id, promotion_id=promotion_id)

    async def create_usage(
        self, user_id: int, promotion_id: int, subscription_id: Optional[int] = None
    ) -> UserPromotionUsage:
        """Создать запись об использовании промокода"""
        usage = UserPromotionUsage(
            user_id=user_id,
            promotion_id=promotion_id,
            subscription_id=subscription_id,
        )
        return await self.create(usage)

    async def get_usage_by_subscription(self, subscription_id: int) -> Optional[UserPromotionUsage]:
        """Получить запись об использовании промокода по subscription_id"""
        return await self.get_by(subscription_id=subscription_id)
