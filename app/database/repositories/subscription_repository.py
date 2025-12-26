from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import Row, RowMapping, and_, select

from app.core.enums import SubscriptionStatus
from app.core.exceptions import SubscriptionNotFound
from app.database.base_repository import BaseRepository
from app.models import Subscription


class SubscriptionRepository(BaseRepository[Subscription]):
    """Repository для управления подписками"""

    def _get_model(self) -> type[Subscription]:
        return Subscription

    def _get_not_found_exception(self, id_):
        return SubscriptionNotFound(id_)

    async def get_subscription_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Получить подписку по ID"""
        return await self.get_by_id(subscription_id)

    async def get_subscription_by_id_or_raise(self, subscription_id: int) -> Subscription:
        """Получить подписку по ID или выбросить исключение"""
        return await self.get_by_id_or_raise(subscription_id)

    async def get_for_update(self, subscription_id: int) -> Optional[Subscription]:
        """Получить подписку с блокировкой FOR UPDATE для предотвращения race conditions"""
        stmt = select(Subscription).where(Subscription.id == subscription_id).with_for_update()
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_for_update_or_raise(self, subscription_id: int) -> Subscription:
        """Получить подписку с блокировкой FOR UPDATE или выбросить исключение"""
        subscription = await self.get_for_update(subscription_id)
        if not subscription:
            raise SubscriptionNotFound(subscription_id)
        return subscription

    async def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        """Получить активную подписку пользователя"""
        active_subs = await self.get_user_active_subscriptions(user_id)
        return active_subs[0] if active_subs else None

    async def get_all_user_subscriptions(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[Row | RowMapping | Any]:
        """Получить все подписки пользователя"""
        return await self.get_all_by(user_id=user_id)

    async def get_all_user_subscriptions_in_status(
        self, user_id: int, status: SubscriptionStatus, skip: int = 0, limit: int = 100
    ) -> Sequence[Row | RowMapping | Any]:
        """Получить все подписки пользователя с заданным статусом"""
        return await self.get_all_by(user_id=user_id, status=status.value)

    async def get_user_pending_subscriptions(self, user_id: int) -> Sequence[Subscription]:
        """Получить все pending подписки пользователя"""
        stmt = select(Subscription).where(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.pending_payment.value,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_user_active_subscriptions(self, user_id: int) -> Sequence[Subscription]:
        """Получить все активные подписки пользователя"""
        stmt = select(Subscription).where(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.active.value,
                Subscription.end_date > datetime.now(timezone.utc),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_user_inactive_subscriptions(self, user_id: int) -> Sequence[Subscription]:
        """Получить все неактивные подписки пользователя"""
        stmt = select(Subscription).where(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "inactive",
            )
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_active_subscriptions_by_plan(self, plan_id: int) -> Sequence[Subscription]:
        """Получить все активные подписки на определенный план"""
        stmt = select(Subscription).where(
            and_(
                Subscription.plan_id == plan_id,
                Subscription.status == SubscriptionStatus.active.value,
                Subscription.end_date > datetime.now(timezone.utc),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create_subscription_with_status(
        self, user_id: int, plan_id: int, duration_days: int, status: str
    ) -> Subscription:
        """Создать новую подписку"""

        # Валидация
        if duration_days <= 0:
            raise ValueError("Длительность подписки должна быть > 0")

        # Вычислить даты
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=duration_days)

        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
        )

        return await self.create(subscription)

    # ========== UPDATE методы ==========

    async def activate_subscription(self, subscription_id: int) -> Subscription:
        """Активировать подписку"""
        subscription = await self.get_subscription_by_id_or_raise(subscription_id)

        subscription.status = SubscriptionStatus.active.value
        subscription.start_date = datetime.now(timezone.utc)
        subscription.updated_at = datetime.now(timezone.utc)

        return await self.update(subscription)

    async def deactivate_subscription(self, subscription_id: int) -> Subscription:
        """Деактивировать подписку"""
        subscription = await self.get_subscription_by_id_or_raise(subscription_id)

        subscription.status = SubscriptionStatus.cancelled.value
        subscription.end_date = datetime.now(timezone.utc)
        subscription.updated_at = datetime.now(timezone.utc)

        return await self.update(subscription)

    async def extend_subscription(self, subscription_id: int, additional_days: int) -> Subscription:
        """Продлить подписку на дополнительные дни"""

        if additional_days <= 0:
            raise ValueError("Количество дополнительных дней должно быть > 0")

        subscription = await self.get_subscription_by_id_or_raise(subscription_id)

        # Если подписка уже истекла, начинаем с сегодня
        now = datetime.now(timezone.utc)
        if subscription.end_date <= now:
            new_end_date = now + timedelta(days=additional_days)
        else:
            # Иначе добавляем к существующей дате
            new_end_date = subscription.end_date + timedelta(days=additional_days)

        subscription.end_date = new_end_date
        subscription.updated_at = now

        return await self.update(subscription)

    async def update_subscription_status(self, subscription_id: int, new_status: str) -> Subscription:
        """Обновить статус подписки"""

        subscription = await self.get_subscription_by_id_or_raise(subscription_id)

        subscription.status = new_status
        subscription.updated_at = datetime.now(timezone.utc)

        return await self.update(subscription)

    # ========== DELETE методы ==========

    async def cancel_subscription(self, subscription_id: int) -> None:
        """Отменить (удалить) подписку"""
        subscription = await self.get_subscription_by_id_or_raise(subscription_id)
        await self.delete(subscription)

    # ========== UTILITY методы ==========

    async def subscription_exists(self, subscription_id: int) -> bool:
        """Проверить существование подписки"""
        subscription = await self.get_subscription_by_id(subscription_id)
        return subscription is not None

    async def user_has_active_subscription(self, user_id: int) -> bool:
        """Проверить имеет ли пользователь активную подписку"""
        subscription = await self.get_active_subscription(user_id)
        return subscription is not None

    async def count_user_subscriptions(self, user_id: int) -> int:
        """Получить количество подписок пользователя"""
        return await self.count(user_id=user_id)

    async def count_active_subscriptions_for_plan(self, plan_id: int) -> int:
        """Получить количество активных подписок на план"""
        stmt = select(Subscription).where(
            and_(
                Subscription.plan_id == plan_id,
                Subscription.status == SubscriptionStatus.active.value,
                Subscription.end_date > datetime.now(timezone.utc),
            )
        )
        result = await self._session.execute(stmt)
        return len(result.scalars().all())

    async def is_subscription_active(self, subscription_id: int) -> bool:
        """Проверить активна ли подписка"""
        subscription = await self.get_subscription_by_id(subscription_id)
        if not subscription:
            return False

        return subscription.status == SubscriptionStatus.active.value and subscription.end_date > datetime.now(
            timezone.utc
        )

    async def get_subscriptions_ending_today(self) -> Sequence[Subscription]:
        """Получить все активные подписки, которые заканчиваются сегодня"""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        stmt = select(Subscription).where(
            and_(
                Subscription.status == SubscriptionStatus.active.value,
                Subscription.end_date >= today_start,
                Subscription.end_date < today_end,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_subscriptions_ending_tomorrow(self) -> Sequence[Subscription]:
        """Получить все активные подписки, которые заканчиваются завтра"""
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
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_last_successful_payment_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """Получить последнюю успешную подписку для определения условий продления"""
        # Получаем все подписки пользователя, отсортированные по дате создания
        subscription = await self.get_subscription_by_id(subscription_id)
        if not subscription:
            return None

        # Получаем все подписки пользователя с таким же plan_id
        stmt = (
            select(Subscription)
            .where(
                and_(
                    Subscription.user_id == subscription.user_id,
                    Subscription.plan_id == subscription.plan_id,
                    Subscription.status.in_(
                        [
                            SubscriptionStatus.active.value,
                            SubscriptionStatus.expired.value,
                        ]
                    ),
                )
            )
            .order_by(Subscription.created_at.desc())
        )

        result = await self._session.execute(stmt)
        subscriptions = result.scalars().all()
        return subscriptions[0] if subscriptions else None


# async def get_expired_subscriptions(self) -> Sequence[Subscription]:
#     """Получить все истекшие подписки"""
#     stmt = select(Subscription).where(
#         and_(
#             Subscription.status == SubscriptionStatus.active,
#             Subscription.end_date <= datetime.utcnow(),
#         )
#     )
#     result = await self._session.execute(stmt)
#     return result.scalars().all()
#
# async def get_subscriptions_by_plan(
#         self, plan_id: int, skip: int = 0, limit: int = 100
# ) -> Sequence[Subscription]:
#     """Получить все подписки на определенный план"""
#     stmt = (
#         select(Subscription)
#         .where(Subscription.plan_id == plan_id)
#         .offset(skip)
#         .limit(limit)
#     )
#     result = await self._session.execute(stmt)
#     return result.scalars().all()
