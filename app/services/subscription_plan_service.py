"""
Subscription plan service - бизнес-логика для работы с планами подписок
"""

from typing import Optional

from app.schemas.subscription import (
    SubscriptionPlanCreateRequest,
    SubscriptionPlanResponse,
    SubscriptionPlanUpdate,
)
from app.services.base_service import BaseService


class SubscriptionPlanService(BaseService):
    """Сервис для управления планами подписок"""

    async def get_plan_by_id(self, plan_id: int) -> Optional[SubscriptionPlanResponse]:
        """
        Получить план подписки по ID

        Args:
            plan_id: ID плана

        Returns:
            Optional[SubscriptionPlanResponse]: План подписки или None
        """
        plan = await self.uow.subscription_plans.get_by_id(plan_id)

        if not plan:
            return None

        return SubscriptionPlanResponse.model_validate(plan)

    async def get_all_plans(self, skip: int = 0, limit: int = 100) -> list[SubscriptionPlanResponse]:
        """
        Получить все планы подписок

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            List[SubscriptionPlanResponse]: Список планов
        """
        plans = await self.uow.subscription_plans.get_all(skip=skip, limit=limit)
        return [SubscriptionPlanResponse.model_validate(plan) for plan in plans]

    async def create_plan(self, plan_data: SubscriptionPlanCreateRequest) -> SubscriptionPlanResponse:
        """
        Создать новый план подписки

        Args:
            plan_data: Данные для создания плана

        Returns:
            SubscriptionPlanResponse: Созданный план
        """
        plan = await self.uow.subscription_plans.create_plan(
            name=plan_data.name,
            price=plan_data.price,
            duration_days=plan_data.duration_days,
            features=plan_data.features,
        )

        return SubscriptionPlanResponse.model_validate(plan)

    async def update_plan(self, plan_id: int, plan_update: SubscriptionPlanUpdate) -> SubscriptionPlanResponse:
        """
        Обновить план подписки

        Args:
            plan_id: ID плана
            plan_update: Данные для обновления

        Returns:
            SubscriptionPlanResponse: Обновленный план
        """
        plan = await self.uow.subscription_plans.update_plan(
            plan_id=plan_id,
            name=plan_update.name,
            price=plan_update.price,
            duration_days=plan_update.duration_days,
            features=plan_update.features,
        )

        return SubscriptionPlanResponse.model_validate(plan)

    async def delete_plan(self, plan_id: int) -> None:
        """
        Удалить план подписки

        Args:
            plan_id: ID плана
        """
        await self.uow.subscription_plans.delete_plan(plan_id)
