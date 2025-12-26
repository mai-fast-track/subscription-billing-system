from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, select

from app.core.enums import SubscriptionStatus
from app.core.exceptions import SubscriptionNotFound
from app.database.base_repository_sync import BaseRepositorySync
from app.models import Subscription


class SubscriptionRepositorySync(BaseRepositorySync[Subscription]):
    """Синхронный Repository для управления подписками (для Celery)"""

    def _get_model(self) -> type[Subscription]:
        return Subscription

    def _get_not_found_exception(self, id_):
        return SubscriptionNotFound(id_)

    def get_subscription_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Получить подписку по ID"""
        return self.get_by_id(subscription_id)

    def get_subscription_by_id_or_raise(self, subscription_id: int) -> Subscription:
        """Получить подписку по ID или выбросить исключение"""
        return self.get_by_id_or_raise(subscription_id)

    def get_subscriptions_ending_today(self) -> Sequence[Subscription]:
        """Получить все активные подписки, которые заканчиваются сегодня (SYNC)"""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        stmt = select(Subscription).where(
            and_(
                Subscription.status == SubscriptionStatus.active.value,
                Subscription.end_date >= today_start,
                Subscription.end_date < today_end,
            )
        )
        result = self._session.execute(stmt)
        return result.scalars().all()

    def get_subscriptions_ending_tomorrow(self) -> Sequence[Subscription]:
        """Получить все активные подписки, которые заканчиваются завтра (SYNC)"""
        tomorrow_start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        tomorrow_end = tomorrow_start + timedelta(days=1)

        stmt = select(Subscription).where(
            and_(
                Subscription.status == SubscriptionStatus.active.value,
                Subscription.end_date >= tomorrow_start,
                Subscription.end_date < tomorrow_end,
            )
        )
        result = self._session.execute(stmt)
        return result.scalars().all()

    def get_for_payment_with_lock(self, subscription_id: int) -> Optional[Subscription]:
        """
        Получить подписку с блокировкой строки для безопасного платежа.
        SELECT ... FOR UPDATE.

        Это предотвращает гонки между автосписанием и отменой подписки.
        """
        stmt = select(Subscription).where(Subscription.id == subscription_id).with_for_update()
        result = self._session.execute(stmt)
        return result.scalars().first()

    def update_subscription(self, subscription: Subscription) -> Subscription:
        """Обновить подписку"""
        subscription.updated_at = datetime.now(timezone.utc)
        return self.update(subscription)

    def is_subscription_already_extended(self, subscription_id: int) -> bool:
        """
        Проверить, не была ли подписка уже продлена.
        Используется для идемпотентности - если подписка уже продлена,
        не нужно создавать новый платеж.
        """
        subscription = self.get_subscription_by_id(subscription_id)
        if not subscription:
            return False

        # Если end_date больше чем сегодня, значит подписка уже продлена
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        # Подписка считается продленной, если end_date >= завтра
        return subscription.end_date >= tomorrow

    def get_subscriptions_by_status(self, status: str) -> Sequence[Subscription]:
        """
        Получить все подписки с указанным статусом (SYNC).

        Args:
            status: Статус подписки

        Returns:
            Sequence подписок
        """
        stmt = select(Subscription).where(Subscription.status == status)
        result = self._session.execute(stmt)
        return result.scalars().all()
