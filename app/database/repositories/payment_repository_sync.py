# repository/payment_sync.py
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clients.yookassa_client import YookassaClient
from app.core.exceptions import PaymentNotFound
from app.database.base_repository_sync import BaseRepositorySync
from app.models import Payment


class PaymentRepositorySync(BaseRepositorySync[Payment]):
    """Синхронный Repository для управления платежами (для Celery)"""

    def __init__(self, session: Session, yookassa_client: YookassaClient):
        super().__init__(session)
        self.yookassa_client = yookassa_client

    def _get_model(self) -> type[Payment]:
        return Payment

    def _get_not_found_exception(self, id_):
        return PaymentNotFound(id_)

    def get_by_id_or_raise(self, payment_id: int) -> Payment:
        """Получить платеж по ID или выбросить исключение"""
        payment = self.get_by_id(payment_id)
        if not payment:
            raise PaymentNotFound(payment_id)
        return payment

    def get_for_processing_with_lock(self, payment_id: int) -> Optional[Payment]:
        """
        Получить платеж с блокировкой строки для безопасной обработки.
        SELECT ... FOR UPDATE.

        Это предотвращает гонки при параллельной обработке одного платежа
        (например, webhook и retry_auto_payment_attempt одновременно).
        """
        stmt = select(Payment).where(Payment.id == payment_id).with_for_update()
        result = self._session.execute(stmt)
        return result.scalars().first()

    def create_payment(self, payment: Payment) -> Payment:
        """Создать платеж"""
        return self.create(payment)

    def update_payment(self, payment: Payment) -> Payment:
        """Обновить платеж"""
        payment.updated_at = datetime.utcnow()
        return self.update(payment)

    def get_failed_payments_for_retry(self) -> Sequence[Payment]:
        """
        Получить неудачные платежи, которые можно повторить.

        ПРИМЕЧАНИЕ: В новой архитектуре автосписаний этот метод не используется,
        так как попытки обрабатываются через отдельные задачи retry_auto_payment_attempt.
        Метод оставлен для совместимости и возможного использования в других целях.

        Включает:
        - Платежи с payment_method="auto_payment" (автосписания)
        - Платежи с payment_method="manual", созданные автоматически для автоплатежей
          (когда нет сохраненного метода, но платеж создан автоматически)
        """
        from sqlalchemy import and_, or_

        from app.core.enums import PaymentStatus

        # Платежи, созданные сегодня для автоплатежей (по idempotency_key)
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        auto_payment_idempotency_pattern = f"auto_payment_%_{today_str}"

        stmt = select(Payment).where(
            and_(
                Payment.status.in_([PaymentStatus.failed.value, PaymentStatus.pending.value]),
                # Включаем auto_payment И manual платежи с idempotency_key для автоплатежей
                or_(
                    Payment.payment_method == "auto_payment",
                    and_(
                        Payment.payment_method == "manual",
                        Payment.idempotency_key.like(auto_payment_idempotency_pattern),
                    ),
                ),
                Payment.attempt_number < 3,
                ((Payment.next_retry_at.is_(None)) | (Payment.next_retry_at <= datetime.utcnow())),
            )
        )
        result = self._session.execute(stmt)
        return result.scalars().all()

    def get_payments_for_final_processing(self) -> Sequence[Payment]:
        """
        Получить платежи, которые исчерпали все попытки и требуют финальной обработки.
        Используется для отправки финальных уведомлений и обновления статуса подписки.

        Включает:
        - Платежи с attempt_number >= MAX_RETRY_ATTEMPTS (3)
        - Платежи со статусом failed или pending (не succeeded)
        - Платежи для автоплатежей (auto_payment или manual с idempotency_key)
        - Платежи, созданные не более 7 дней назад (чтобы не обрабатывать старые платежи)
        """
        from sqlalchemy import and_, or_

        from app.core.enums import PaymentStatus

        # Платежи, созданные сегодня для автоплатежей (по idempotency_key)
        datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Платежи, созданные не более 7 дней назад
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        stmt = select(Payment).where(
            and_(
                Payment.status.in_([PaymentStatus.failed.value, PaymentStatus.pending.value]),
                # Включаем auto_payment И manual платежи с idempotency_key для автоплатежей
                or_(
                    Payment.payment_method == "auto_payment",
                    and_(Payment.payment_method == "manual", Payment.idempotency_key.like("auto_payment_%")),
                ),
                Payment.attempt_number >= 3,  # Исчерпаны все попытки
                Payment.created_at >= seven_days_ago,  # Не старше 7 дней
            )
        )
        result = self._session.execute(stmt)
        return result.scalars().all()

    def get_pending_or_succeeded_payments_for_subscription(self, subscription_id: int) -> Sequence[Payment]:
        """
        Получить pending или succeeded платежи для подписки.
        Используется для проверки идемпотентности - предотвращает двойные платежи.

        Включает:
        - Платежи с payment_method="auto_payment" (автосписания)
        - Платежи с payment_method="manual", созданные автоматически для автоплатежей
          (определяется по idempotency_key вида "auto_payment_{subscription_id}_{date}")
        """
        from sqlalchemy import and_, or_

        from app.core.enums import PaymentStatus

        # Паттерн для manual платежей, созданных автоматически
        datetime.utcnow().strftime("%Y-%m-%d")

        stmt = (
            select(Payment)
            .where(
                and_(
                    Payment.subscription_id == subscription_id,
                    Payment.status.in_(
                        [
                            PaymentStatus.pending.value,
                            PaymentStatus.succeeded.value,
                            PaymentStatus.waiting_for_capture.value,
                        ]
                    ),
                    # Включаем auto_payment И manual платежи с idempotency_key для автоплатежей
                    or_(
                        Payment.payment_method == "auto_payment",
                        and_(
                            Payment.payment_method == "manual",
                            Payment.idempotency_key.like(f"auto_payment_{subscription_id}_%"),
                        ),
                    ),
                )
            )
            .order_by(Payment.created_at.desc())
        )

        result = self._session.execute(stmt)
        return result.scalars().all()

    def get_payment_by_idempotency_key(self, idempotency_key: str) -> Optional[Payment]:
        """
        Получить платеж по idempotency_key.
        Используется для проверки, не был ли уже создан платеж с таким ключом.
        """
        return self.get_by(idempotency_key=idempotency_key)
