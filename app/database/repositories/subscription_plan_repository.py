from datetime import datetime
from typing import Optional

from sqlalchemy import and_, select

from app.core.exceptions import SubscriptionPlanNotFound
from app.database.base_repository import BaseRepository
from app.models import Subscription, SubscriptionPlan, SubscriptionStatus


class SubscriptionPlanRepository(BaseRepository[SubscriptionPlan]):
    """Repository для управления планами подписок"""

    def _get_not_found_exception(self, id_):
        return SubscriptionPlanNotFound(id_)

    def _get_model(self) -> type[SubscriptionPlan]:
        return SubscriptionPlan

    async def get_plan_by_id(self, plan_id: int) -> Optional[SubscriptionPlan]:
        """Получить план подписки по ID"""
        return await self.get_by_id(plan_id)

    async def get_plan_by_name(self, name: str) -> Optional[SubscriptionPlan]:
        """Получить план подписки по названию"""
        return await self.get_by(name=name)

    async def create_plan(
        self,
        name: str,
        price: float,
        duration_days: int,
        features: Optional[str] = None,
    ) -> SubscriptionPlan:
        """Создать новый план подписки"""

        if price < 0:
            raise ValueError("Цена не может быть отрицательной")

        if duration_days <= 0:
            raise ValueError("Продолжительность должна быть больше 0")

        existing = await self.get_plan_by_name(name)
        if existing:
            raise ValueError(f"План подписки с названием '{name}' уже существует")

        plan = SubscriptionPlan(
            name=name,
            price=price,
            duration_days=duration_days,
            features=features,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        return await self.create(plan)

    async def update_plan(
        self,
        plan_id: int,
        name: Optional[str] = None,
        price: Optional[float] = None,
        duration_days: Optional[int] = None,
        features: Optional[str] = None,
    ) -> SubscriptionPlan:
        """Обновить план подписки"""

        plan = await self.get_plan_by_id(plan_id)
        if not plan:
            raise ValueError(f"План подписки с ID {plan_id} не найден")

        # Валидация цены
        if price is not None and price < 0:
            raise ValueError("Цена не может быть отрицательной")

        # Валидация длительности
        if duration_days is not None and duration_days <= 0:
            raise ValueError("Продолжительность должна быть больше 0")

        # Проверить дубликат имени
        if name and name != plan.name:
            existing = await self.get_plan_by_name(name)
            if existing:
                raise ValueError(f"План подписки с названием '{name}' уже существует")

        # Обновить поля
        if name is not None:
            plan.name = name
        if price is not None:
            plan.price = price
        if duration_days is not None:
            plan.duration_days = duration_days
        if features is not None:
            plan.features = features

        plan.updated_at = datetime.utcnow()

        return await self.update(plan)

    async def delete_plan(self, plan_id: int) -> None:
        """Удалить план подписки"""

        plan = await self.get_plan_by_id(plan_id)
        if not plan:
            raise ValueError(f"План подписки с ID {plan_id} не найден")

        # Проверить активные подписки
        stmt = select(Subscription).where(
            and_(
                Subscription.plan_id == plan_id,
                Subscription.status == SubscriptionStatus.active,
            )
        )
        result = await self._session.execute(stmt)
        active_subscriptions = result.scalars().all()

        if active_subscriptions:
            raise ValueError(f"Невозможно удалить план: есть {len(active_subscriptions)} активных подписок")

        await self.delete(plan)
