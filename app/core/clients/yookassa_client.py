import time
import uuid
from typing import Optional

from yookassa import Payment, Refund
from yookassa.domain.exceptions import ApiError
from yookassa.domain.response import PaymentResponse, RefundResponse

from app.schemas.yookassa import YookassaPaymentRequest


class YookassaClient:
    """
    Клиент для работы с API Юкассы.
    Поддерживает одностадийные и двухстадийные платежи.
    """

    MAX_RETRIES = 5
    BASE_DELAY = 1.0
    RETRYABLE_STATUS_CODES = {429, 500}

    def _retry_request(self, func, *args, **kwargs):
        """Общая логика повторных попыток для запросов к Юкассе"""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except ApiError as e:
                if attempt == self.MAX_RETRIES or e.HTTP_CODE not in self.RETRYABLE_STATUS_CODES:
                    raise RuntimeError(
                        f"Ошибка при запросе к ЮKассе: {str(e)} (статус: {getattr(e, 'HTTP_CODE', 'неизвестно')})"
                    )
                delay = self.BASE_DELAY * (2**attempt) + (time.time() % 1.0)
                time.sleep(delay)
            except Exception as e:
                if attempt == self.MAX_RETRIES:
                    raise RuntimeError(f"Ошибка при запросе к ЮKассе: {str(e)}")
                time.sleep(self.BASE_DELAY)
        raise RuntimeError("Достигнут лимит ретраев")

    def create_payment(self, request: YookassaPaymentRequest, idempotency_key: str) -> PaymentResponse:
        """
        Создать одностадийный платеж в Юкассе (старый метод).
        Платеж сразу списывается после подтверждения.

        Если передан payment_method_id, используется сохраненный платежный метод для автоплатежа.
        """
        params = {
            "amount": {
                "value": request.amount_value,
                "currency": request.currency,
            },
            "confirmation": {
                "type": request.type,
                "return_url": request.return_url,
            },
            "capture": True,  # Одностадийный платеж
            "description": request.description,
        }

        # Если передан сохраненный платежный метод - используем его для автоплатежа
        if request.payment_method_id:
            params["payment_method_id"] = request.payment_method_id

        return self._retry_request(Payment.create, params=params, idempotency_key=idempotency_key)

    def create_payment_two_stage(self, request: YookassaPaymentRequest, idempotency_key: str) -> PaymentResponse:
        """
        Создать двухстадийный платеж в Юкассе (новый метод).
        Платеж сначала авторизуется, затем нужно вызвать capture_payment для списания.
        """
        params = {
            "amount": {
                "value": request.amount_value,
                "currency": request.currency,
            },
            "confirmation": {
                "type": request.type,
                "return_url": request.return_url,
            },
            "capture": False,  # Двухстадийный платеж
            "description": request.description,
        }

        return self._retry_request(Payment.create, params=params, idempotency_key=idempotency_key)

    def capture_payment(self, payment_id: str, idempotency_key: Optional[str] = None) -> PaymentResponse:
        """
        Провести (capture) двухстадийный платеж.
        Списывает ранее авторизованные средства.

        Args:
            payment_id: ID платежа в Юкассе
            idempotency_key: Ключ идемпотентности (опционально)

        Returns:
            PaymentResponse: Обновленная информация о платеже
        """
        return self._retry_request(Payment.capture, payment_id=payment_id, idempotency_key=idempotency_key)

    def cancel_payment(self, payment_id: str, idempotency_key: Optional[str] = None) -> PaymentResponse:
        """
        Отменить платеж.
        Отменяет авторизованные средства для двухстадийного платежа.

        Args:
            payment_id: ID платежа в Юкассе
            idempotency_key: Ключ идемпотентности (опционально)

        Returns:
            PaymentResponse: Обновленная информация о платеже
        """
        return self._retry_request(Payment.cancel, payment_id=payment_id, idempotency_key=idempotency_key)

    def get_payment(self, payment_id: str) -> PaymentResponse:
        """
        Получить информацию о платеже.

        Args:
            payment_id: ID платежа в Юкассе

        Returns:
            PaymentResponse: Информация о платеже
        """
        return self._retry_request(Payment.find_one, payment_id)

    def create_refund(
        self, payment_id: str, amount: Optional[float] = None, idempotency_key: Optional[str] = None
    ) -> RefundResponse:
        """
        Создать возврат платежа в Юкассе.

        Args:
            payment_id: ID платежа в Юкассе
            amount: Сумма возврата (если None - полный возврат)
            idempotency_key: Ключ идемпотентности (опционально, генерируется автоматически если не указан)

        Returns:
            RefundResponse: Информация о возврате
        """
        params = {"payment_id": payment_id}

        if amount is not None:
            params["amount"] = {"value": amount, "currency": "RUB"}

        if idempotency_key is None:
            idempotency_key = str(uuid.uuid4())

        return self._retry_request(Refund.create, params=params, idempotency_key=idempotency_key)


yookassa_client = YookassaClient()
