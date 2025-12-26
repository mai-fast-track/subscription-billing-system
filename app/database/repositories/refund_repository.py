# repository/refund.py
from typing import Optional

from sqlalchemy import select

from app.core.exceptions import RefundNotFound
from app.database.base_repository import BaseRepository
from app.models import Refund


class RefundRepository(BaseRepository[Refund]):
    """Repository для управления возвратами"""

    def _get_model(self) -> type[Refund]:
        return Refund

    def _get_not_found_exception(self, id_):
        return RefundNotFound(id_)

    async def get_by_payment_id(self, payment_id: int) -> Optional[Refund]:
        """Получить возврат по ID платежа"""
        return await self.get_by(payment_id=payment_id)

    async def get_by_yookassa_id(self, yookassa_refund_id: str) -> Optional[Refund]:
        """Получить возврат по ID Юкассы"""
        return await self.get_by(yookassa_refund_id=yookassa_refund_id)

    async def get_payment_refunds(self, payment_id: int) -> list[Refund]:
        """Получить все возвраты для платежа"""
        stmt = select(Refund).where(Refund.payment_id == payment_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
