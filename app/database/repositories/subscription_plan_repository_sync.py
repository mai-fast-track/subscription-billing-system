from app.core.exceptions import SubscriptionPlanNotFound
from app.database.base_repository_sync import BaseRepositorySync
from app.models import SubscriptionPlan


class SubscriptionPlanRepositorySync(BaseRepositorySync[SubscriptionPlan]):
    """Синхронный Repository для управления планами подписок (для Celery)"""

    def _get_not_found_exception(self, id_):
        return SubscriptionPlanNotFound(id_)

    def _get_model(self) -> type[SubscriptionPlan]:
        return SubscriptionPlan

    def get_by_id_or_raise(self, plan_id: int) -> SubscriptionPlan:
        """Получить план подписки по ID или выбросить исключение"""
        plan = self.get_by_id(plan_id)
        if not plan:
            raise SubscriptionPlanNotFound(plan_id)
        return plan
