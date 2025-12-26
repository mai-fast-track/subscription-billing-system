from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clients.yookassa_client import YookassaClient
from app.database.repositories.payment_repository import PaymentRepository
from app.database.repositories.promo_repository import PromotionRepository
from app.database.repositories.refund_repository import RefundRepository
from app.database.repositories.subscription_plan_repository import SubscriptionPlanRepository
from app.database.repositories.subscription_repository import SubscriptionRepository
from app.database.repositories.user_promotion_usage_repository import UserPromotionUsageRepository
from app.database.repositories.user_repository import UserRepository


class UnitOfWork:
    """
    Async Unit of Work - управляет всеми репозиториями и транзакциями.

    Ключевое правило:
    - get_session() НЕ коммитит (это делает UoW)
    - UoW отвечает за commit/rollback
    - Используется как async with uow:
    """

    def __init__(self, session: AsyncSession, yookassa_client: YookassaClient):
        self._session = session
        self.yookassa_client = yookassa_client

        # Инициализируем все репозитории один раз
        self.users = UserRepository(session)
        self.subscriptions = SubscriptionRepository(session)
        self.subscription_plans = SubscriptionPlanRepository(session)
        self.payments = PaymentRepository(session, yookassa_client)
        self.promotions = PromotionRepository(session)
        self.refunds = RefundRepository(session)
        self.user_promotion_usage = UserPromotionUsageRepository(session)

    @property
    def session(self) -> AsyncSession:
        """Получить сессию БД (для использования в задачах)"""
        return self._session

    async def commit(self) -> None:
        """Коммитим транзакцию"""
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            # TODO logs
            raise

    async def rollback(self) -> None:
        """Откатываем транзакцию"""
        try:
            await self._session.rollback()
        except Exception:
            # TODO logs
            pass

    async def close(self) -> None:
        """Закрываем сессию"""
        try:
            await self._session.close()
        except Exception:
            pass

    async def __aenter__(self):
        """Вход в контекстный менеджер"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера"""
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                # Если всё ок - коммитим
                await self.commit()
        finally:
            # Всегда закрываем сессию
            await self.close()
