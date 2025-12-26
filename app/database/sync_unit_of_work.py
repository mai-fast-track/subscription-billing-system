"""
Синхронный Unit of Work для Celery задач.
Использует синхронные репозитории и Session вместо AsyncSession.
"""

from sqlalchemy.orm import Session

from app.core.clients.yookassa_client import YookassaClient
from app.database.repositories.payment_repository_sync import PaymentRepositorySync
from app.database.repositories.promo_repository_sync import PromotionRepositorySync
from app.database.repositories.refund_repository_sync import RefundRepositorySync
from app.database.repositories.subscription_plan_repository_sync import SubscriptionPlanRepositorySync
from app.database.repositories.subscription_repository_sync import SubscriptionRepositorySync
from app.database.repositories.user_repository_sync import UserRepositorySync


class SyncUnitOfWork:
    """
    Синхронный Unit of Work - управляет всеми репозиториями и транзакциями для Celery.

    Ключевое правило:
    - get_session() НЕ коммитит (это делает UoW)
    - UoW отвечает за commit/rollback
    - Используется как with uow:
    """

    def __init__(self, session: Session, yookassa_client: YookassaClient):
        self._session = session
        self.yookassa_client = yookassa_client

        # Инициализируем все репозитории один раз
        self.users = UserRepositorySync(session)
        self.subscriptions = SubscriptionRepositorySync(session)
        self.subscription_plans = SubscriptionPlanRepositorySync(session)
        self.payments = PaymentRepositorySync(session, yookassa_client)
        self.promotions = PromotionRepositorySync(session)
        self.refunds = RefundRepositorySync(session)

    @property
    def session(self) -> Session:
        """Получить сессию БД"""
        return self._session

    def commit(self) -> None:
        """Коммитим транзакцию"""
        try:
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

    def rollback(self) -> None:
        """Откатываем транзакцию"""
        try:
            self._session.rollback()
        except Exception:
            pass

    def close(self) -> None:
        """Закрываем сессию"""
        try:
            self._session.close()
        except Exception:
            pass

    def __enter__(self):
        """Вход в контекстный менеджер"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера"""
        try:
            if exc_type is not None:
                self.rollback()
            else:
                # Если всё ок - коммитим
                self.commit()
        finally:
            # Всегда закрываем сессию
            self.close()
