# repository/payment.py
from collections.abc import Sequence
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clients.yookassa_client import YookassaClient
from app.core.exceptions import PaymentNotFound
from app.database.base_repository import BaseRepository
from app.models import Payment


class PaymentRepository(BaseRepository[Payment]):
    """Repository для управления платежами"""

    def __init__(self, session: AsyncSession, yookassa_client: YookassaClient):
        super().__init__(session)
        self.yookassa_client = yookassa_client

    def _get_model(self) -> type[Payment]:
        return Payment

    def _get_not_found_exception(self, id_):
        return PaymentNotFound(id_)

    async def get_payment_by_yookassa_id(self, yookassa_payment_id: str) -> Optional[Payment]:
        """Получить платеж по ID Юкассы"""
        return await self.get_by(yookassa_payment_id=yookassa_payment_id)

    async def get_user_payments(self, user_id: int) -> Sequence[Payment]:
        """Получить все платежи пользователя"""
        return await self.get_all_by(user_id=user_id)

    async def get_user_waiting_for_capture_payments(self, user_id: int) -> Sequence[Payment]:
        """Получить все платежи пользователя в статусе waiting_for_capture"""
        stmt = select(Payment).where(
            Payment.user_id == user_id,
            Payment.status == "waiting_for_capture",
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_user_pending_payments(self, user_id: int) -> Sequence[Payment]:
        """Получить все платежи пользователя в статусе pending"""
        stmt = select(Payment).where(
            Payment.user_id == user_id,
            Payment.status == "pending",
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_user_completed_payments(self, user_id: int, skip: int = 0, limit: int = 100) -> Sequence[Payment]:
        """
        Получить платежи пользователя в конечных статусах (succeeded, cancelled, failed)

        Args:
            user_id: ID пользователя
            skip: Количество пропущенных записей
            limit: Максимальное количество записей

        Returns:
            Список платежей в конечных статусах, отсортированных по дате создания (новые сначала)
        """
        stmt = (
            select(Payment)
            .where(
                Payment.user_id == user_id,
                Payment.status.in_(["succeeded", "cancelled", "failed"]),
            )
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    # async def get_subscription_payments(
    #         self, subscription_id: int
    # ) -> Sequence[Payment]:
    #     """Получить все платежи подписки"""
    #     return await self.get_all_by(subscription_id=subscription_id)

    async def create_payment(self):
        pass

    async def create_pending_payment(
        self,
        user_id: int,
        subscription_id: int,
        amount: float,
    ) -> Payment:
        """Создать платеж в статусе pending"""

        if amount <= 0:
            raise ValueError("Сумма должна быть больше 0")

        idempotency_key = str(uuid4())

        payment = Payment(
            user_id=user_id,
            subscription_id=subscription_id,
            yookassa_payment_id="temp",
            amount=amount,
            currency="RUB",
            status="pending",
            attempt_number=1,
            idempotency_key=idempotency_key,
        )

        return await self.create(payment)

    async def update_payment_with_yookassa_id(self, payment_id: int, yookassa_payment_id: str) -> Payment:
        """Обновить платеж с ID от Юкассы"""
        payment = await self.get_by_id(payment_id)
        if not payment:
            raise ValueError(f"Платеж {payment_id} не найден")

        payment.yookassa_payment_id = yookassa_payment_id
        return await self.update(payment)

    async def mark_payment_succeeded(self, payment_id: int) -> Payment:
        """Отметить платеж как успешный"""
        payment = await self.get_by_id(payment_id)
        if not payment:
            raise ValueError(f"Платеж {payment_id} не найден")

        payment.status = "succeeded"
        payment.updated_at = datetime.utcnow()
        return await self.update(payment)

    async def mark_payment_failed(self, payment_id: int, attempt_number: int = 1) -> Payment:
        """Отметить платеж как неудачный"""
        payment = await self.get_by_id(payment_id)
        if not payment:
            raise ValueError(f"Платеж {payment_id} не найден")

        payment.status = "failed"
        payment.attempt_number = attempt_number
        payment.updated_at = datetime.utcnow()
        return await self.update(payment)

    async def get_subscription_payments(self, subscription_id: int) -> Sequence[Payment]:
        """Получить все платежи для подписки"""
        return await self.get_all_by(subscription_id=subscription_id)

    async def get_last_successful_payment_for_subscription(self, subscription_id: int) -> Optional[Payment]:
        """Получить последний успешный платеж для подписки"""
        stmt = (
            select(Payment)
            .where(Payment.subscription_id == subscription_id, Payment.status == "succeeded")
            .order_by(Payment.created_at.desc())
        )
        result = await self._session.execute(stmt)
        payments = result.scalars().all()
        return payments[0] if payments else None

    async def has_user_successful_payment(self, user_id: int) -> bool:
        """
        Проверить, был ли у пользователя хотя бы один успешный платеж по подписке.

        ВАЖНО: Включает ВСЕ успешные платежи, включая триал-платежи (yookassa_payment_id="trial_period").
        Триал-платежи учитываются, так как триал доступен только один раз для пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            bool: True если у пользователя был хотя бы один успешный платеж (включая триал), False иначе
        """
        stmt = select(Payment).where(Payment.user_id == user_id, Payment.status == "succeeded").limit(1)
        result = await self._session.execute(stmt)
        payment = result.scalar_one_or_none()
        return payment is not None

    async def has_user_used_trial(self, user_id: int) -> bool:
        """
        Проверить, использовал ли пользователь промопериод.

        Промопериод определяется платежом со статусом succeeded и yookassa_payment_id="trial_period".

        Args:
            user_id: ID пользователя

        Returns:
            bool: True если пользователь уже использовал промопериод, False иначе
        """
        stmt = (
            select(Payment)
            .where(
                Payment.user_id == user_id,
                Payment.status == "succeeded",
                Payment.yookassa_payment_id == "trial_period",
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        payment = result.scalar_one_or_none()
        return payment is not None

    async def create_auto_payment(
        self, user_id: int, subscription_id: int, amount: float, yookassa_payment_id: str, attempt_number: int = 1
    ) -> Payment:
        """Создать запись об автоплатеже"""
        idempotency_key = str(uuid4())
        payment = Payment(
            user_id=user_id,
            subscription_id=subscription_id,
            yookassa_payment_id=yookassa_payment_id,
            amount=amount,
            currency="RUB",
            status="pending",
            attempt_number=attempt_number,
            idempotency_key=idempotency_key,
            payment_method="auto_payment",
        )
        return await self.create(payment)
