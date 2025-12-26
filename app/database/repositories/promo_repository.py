"""
Promotion repository - работа с промокодами
"""

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, or_, select

from app.core.enums import PromotionType
from app.core.exceptions import PromotionNotFound
from app.database.base_repository import BaseRepository
from app.models.promotion import Promotion
from app.models.user_promotion_usage import UserPromotionUsage


class PromotionRepository(BaseRepository[Promotion]):
    """Repository для управления промокодами"""

    def _get_model(self) -> type[Promotion]:
        return Promotion

    def _get_not_found_exception(self, id_: int) -> Exception:
        return PromotionNotFound(id_)

    async def get_by_code(self, code: str) -> Optional[Promotion]:
        """Получить промокод по коду"""
        code_upper = code.upper()
        return await self.get_by(code=code_upper)

    async def get_by_code_or_raise(self, code: str) -> Promotion:
        """Получить промокод по коду или выбросить исключение"""
        promotion = await self.get_by_code(code)
        if not promotion:
            raise PromotionNotFound(code)
        return promotion

    async def increment_usage(self, promotion_id: int) -> Promotion:
        """
        Увеличить счетчик использований промокода.

        Raises:
            ValueError: Если промокод достиг лимита использований
        """
        promotion = await self.get_by_id_or_raise(promotion_id)

        # Проверка лимита использований перед увеличением
        if promotion.max_uses is not None and promotion.current_uses >= promotion.max_uses:
            raise ValueError("Promotion has reached maximum usage limit")

        promotion.current_uses += 1
        promotion.updated_at = datetime.now(timezone.utc)
        return await self.update(promotion)

    async def get_available_promotions_for_user(self, user_id: int) -> Sequence[Promotion]:
        """
        Получить доступные промокоды для пользователя.

        Включает:
        - Общие промокоды (assigned_user_id = None)
        - Личные промокоды пользователя (assigned_user_id = user_id)

        Фильтрует по:
        - Активности (is_active = True)
        - Валидности дат (valid_from <= now, valid_until >= now или None)
        - Типу (bonus_days - единственный поддерживаемый тип)
        - Лимиту использований (если max_uses указан, проверяет current_uses < max_uses)
        - Исключает промокоды, которые пользователь уже использовал

        Args:
            user_id: ID пользователя

        Returns:
            Sequence доступных промокодов (без использованных пользователем)
        """
        now = datetime.now(timezone.utc)

        # Используем LEFT JOIN для проверки использования промокода пользователем
        # и фильтруем только те, где UserPromotionUsage.id IS NULL (не использованы)
        stmt = (
            select(Promotion)
            .outerjoin(
                UserPromotionUsage,
                and_(UserPromotionUsage.promotion_id == Promotion.id, UserPromotionUsage.user_id == user_id),
            )
            .where(
                and_(
                    Promotion.is_active == True,  # noqa: E712
                    Promotion.type == PromotionType.bonus_days.value,
                    Promotion.valid_from <= now,
                    or_(Promotion.valid_until.is_(None), Promotion.valid_until >= now),
                    # Общие промокоды или личные промокоды пользователя
                    or_(Promotion.assigned_user_id.is_(None), Promotion.assigned_user_id == user_id),
                    # Промокод не использован пользователем
                    UserPromotionUsage.id.is_(None),
                    # Проверка лимита использований (если max_uses указан)
                    or_(Promotion.max_uses.is_(None), Promotion.current_uses < Promotion.max_uses),
                )
            )
            .order_by(Promotion.created_at.desc())
        )

        result = await self._session.execute(stmt)
        return result.scalars().all()
