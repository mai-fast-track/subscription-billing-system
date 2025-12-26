# repository/refund_sync.py
from typing import Optional

from sqlalchemy import select

from app.core.exceptions import RefundNotFound
from app.database.base_repository_sync import BaseRepositorySync
from app.models import Refund


class RefundRepositorySync(BaseRepositorySync[Refund]):
    """Синхронный Repository для управления возвратами (для Celery)"""

    def _get_model(self) -> type[Refund]:
        return Refund

    def _get_not_found_exception(self, id_):
        return RefundNotFound(id_)

    def get_by_payment_id(self, payment_id: int) -> Optional[Refund]:
        """Получить возврат по ID платежа"""
        return self.get_by(payment_id=payment_id)

    def get_by_yookassa_id(self, yookassa_refund_id: str) -> Optional[Refund]:
        """Получить возврат по ID Юкассы"""
        return self.get_by(yookassa_refund_id=yookassa_refund_id)

    def get_payment_refunds(self, payment_id: int) -> list[Refund]:
        """Получить все возвраты для платежа"""
        stmt = select(Refund).where(Refund.payment_id == payment_id)
        result = self._session.execute(stmt)
        return list(result.scalars().all())
