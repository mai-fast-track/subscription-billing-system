"""
Subscription Orchestrator Service - оркестрация создания подписки с платежом
"""

import uuid
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.enums import PaymentStatus, SubscriptionStatus
from app.core.exceptions import SubscriptionAlreadyActive, TrialPeriodNotAvailable
from app.models import Payment, Subscription
from app.schemas.subscription import (
    CreateTrialRequest,
    CreateTrialResponse,
    SubscriptionWithPaymentRequest,
    SubscriptionWithPaymentResponse,
    TrialEligibilityResponse,
)
from app.schemas.yookassa import YookassaPaymentRequest
from app.services.base_service import BaseService


class SubscriptionOrchestratorService(BaseService):
    """
    Сервис-оркестратор для управления несколькими сервисами.
    Используется когда нужно координировать работу нескольких сервисов в одной транзакции.
    """

    async def create_subscription_with_payment(
        self, request: SubscriptionWithPaymentRequest
    ) -> SubscriptionWithPaymentResponse:
        """
        Создать подписку-заглушку и платеж-заглушку в одной транзакции,
        затем создать запрос в Юкассу на оплату.

        Логика:
        1. Проверяем, что у пользователя нет активной подписки
        2. Отменяем все pending_payment подписки и pending платежи пользователя
        3. Получаем план подписки для расчета суммы и длительности
        4. Создаем подписку со статусом pending_payment
        5. Создаем платеж со статусом pending
        6. Создаем запрос в Юкассу (одностадийный платеж)
        7. Обновляем платеж с ID от Юкассы, статус остается pending
        8. Все в одной транзакции - либо создаются обе заглушки, либо ни одна

        Args:
            request: Данные для создания подписки с платежом

        Returns:
            SubscriptionWithPaymentResponse: Результат создания подписки и платежа

        Raises:
            SubscriptionAlreadyActive: Если у пользователя уже есть активная подписка
        """
        # 1. Проверяем, что пользователь существует
        await self.uow.users.get_by_id_or_raise(request.user_id)

        # 2. Проверяем, что у пользователя нет активной подписки
        # Разрешаем создание новой подписки, если текущая отменена (cancelled_waiting или cancelled)
        active_subscription = await self.uow.subscriptions.get_active_subscription(request.user_id)
        if active_subscription and active_subscription.status == SubscriptionStatus.active.value:
            # Только если подписка действительно active - запрещаем
            # Если cancelled_waiting - разрешаем создание новой
            raise SubscriptionAlreadyActive(user_id=request.user_id, subscription_id=active_subscription.id)

        # 2.5. Отменяем все pending_payment подписки и pending платежи пользователя
        await self._cancel_pending_subscriptions_and_payments(request.user_id)

        # 3. Получаем план подписки для расчета суммы и длительности
        plan = await self.uow.subscription_plans.get_by_id_or_raise(request.plan_id)

        # 4. Создаем подписку (обычное оформление без промопериода)
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=plan.duration_days)

        # Обычное оформление - всегда pending_payment
        subscription_status = SubscriptionStatus.pending_payment.value

        subscription = Subscription(
            user_id=request.user_id,
            plan_id=request.plan_id,
            status=subscription_status,
            start_date=start_date,
            end_date=end_date,
        )
        created_subscription = await self.uow.subscriptions.create(subscription)

        # Явно делаем flush, чтобы подписка была сохранена в БД с ID
        await self.uow.session.flush()

        from app.core.logger import logger

        logger.info(f"Created subscription {created_subscription.id} with status {created_subscription.status}")

        # 5. Создаем платеж
        idempotency_key = str(uuid.uuid4())
        payment = Payment(
            user_id=request.user_id,
            subscription_id=created_subscription.id,
            yookassa_payment_id="temp",
            amount=plan.price,
            currency="RUB",
            status=PaymentStatus.pending.value,
            payment_method="manual",
            attempt_number=1,
            idempotency_key=idempotency_key,
        )
        created_payment = await self.uow.payments.create(payment)

        # Явно делаем flush, чтобы платеж был сохранен в БД с ID
        await self.uow.session.flush()

        logger.info(f"Created payment {created_payment.id} for subscription {created_subscription.id}")

        # 6. Создаем запрос в Юкассу на оплату (одностадийный платеж)
        description = f"Подписка на план '{plan.name}' для пользователя {request.user_id}"
        yookassa_request = YookassaPaymentRequest(
            amount_value=str(plan.price), description=description, return_url=request.return_url
        )

        yookassa_payment = self.uow.yookassa_client.create_payment(
            request=yookassa_request, idempotency_key=idempotency_key
        )

        # 7. Обновляем платеж с ID от Юкассы, статус остается pending
        created_payment.yookassa_payment_id = yookassa_payment.id
        updated_payment = await self.uow.payments.update(created_payment)

        # Явно делаем flush, чтобы обновление было сохранено в БД
        await self.uow.session.flush()

        # Обновляем объект из БД для получения актуальных данных
        await self.uow.session.refresh(updated_payment)

        confirmation_url = yookassa_payment.confirmation.confirmation_url
        yookassa_payment_id = yookassa_payment.id

        logger.info(
            f"Updated payment {updated_payment.id} with yookassa_payment_id {updated_payment.yookassa_payment_id} "
            f"and status {updated_payment.status}. Subscription {created_subscription.id} status: {created_subscription.status}"
        )

        # Все операции выполнены в одной транзакции через UnitOfWork
        # Если что-то пошло не так, UnitOfWork откатит все изменения

        return SubscriptionWithPaymentResponse(
            subscription_id=created_subscription.id,
            payment_id=created_payment.id,
            confirmation_url=confirmation_url,
            yookassa_payment_id=yookassa_payment_id,
            message="Подписка и платеж созданы. Перейдите по ссылке для оплаты.",
            is_trial=False,
        )

    async def check_trial_eligibility(self, user_id: int) -> TrialEligibilityResponse:
        """
        Проверить, доступен ли промопериод для пользователя.

        Промопериод доступен только если:
        1. У пользователя нет успешных платежей
        2. Пользователь еще не использовал промопериод

        Args:
            user_id: ID пользователя

        Returns:
            TrialEligibilityResponse: Результат проверки доступности промопериода
        """
        # Проверяем, что пользователь существует
        await self.uow.users.get_by_id_or_raise(user_id)

        # Проверяем, есть ли у пользователя успешные платежи
        has_successful_payment = await self.uow.payments.has_user_successful_payment(user_id)
        if has_successful_payment:
            return TrialEligibilityResponse(
                is_eligible=False,
                reason="У вас уже были успешные платежи. Промопериод доступен только для новых пользователей.",
            )

        # Проверяем, использовал ли пользователь промопериод
        has_used_trial = await self.uow.payments.has_user_used_trial(user_id)
        if has_used_trial:
            return TrialEligibilityResponse(
                is_eligible=False, reason="Вы уже использовали промопериод. Промопериод доступен только один раз."
            )

        return TrialEligibilityResponse(is_eligible=True)

    async def create_trial_subscription(self, request: CreateTrialRequest) -> CreateTrialResponse:
        """
        Создать подписку с промопериодом.

        Логика:
        1. Проверяем, что у пользователя нет активной подписки
        2. Проверяем доступность промопериода
        3. Отменяем все pending подписки и платежи
        4. Создаем подписку со статусом active и end_date = start_date + TRIAL_PERIOD_DAYS
        5. Создаем платеж со статусом succeeded и yookassa_payment_id="trial_period"

        Args:
            request: Данные для создания промопериода

        Returns:
            CreateTrialResponse: Результат создания промопериода

        Raises:
            SubscriptionAlreadyActive: Если у пользователя уже есть активная подписка
            TrialPeriodNotAvailable: Если промопериод недоступен
        """
        from app.core.logger import logger

        # 1. Проверяем, что пользователь существует
        await self.uow.users.get_by_id_or_raise(request.user_id)

        # 2. Проверяем, что у пользователя нет активной подписки
        # Разрешаем создание новой подписки, если текущая отменена (cancelled_waiting или cancelled)
        active_subscription = await self.uow.subscriptions.get_active_subscription(request.user_id)
        if active_subscription and active_subscription.status == SubscriptionStatus.active.value:
            # Только если подписка действительно active - запрещаем
            # Если cancelled_waiting - разрешаем создание новой
            raise SubscriptionAlreadyActive(user_id=request.user_id, subscription_id=active_subscription.id)

        # 3. Проверяем доступность промопериода
        eligibility = await self.check_trial_eligibility(request.user_id)
        if not eligibility.is_eligible:
            raise TrialPeriodNotAvailable(eligibility.reason or "Промопериод недоступен")

        # 4. Отменяем все pending подписки и платежи
        await self._cancel_pending_subscriptions_and_payments(request.user_id)

        # 5. Получаем план подписки
        plan = await self.uow.subscription_plans.get_by_id_or_raise(request.plan_id)

        # 6. Создаем подписку с промопериодом
        start_date = datetime.now(timezone.utc)
        trial_days = settings.TRIAL_PERIOD_DAYS
        end_date = start_date + timedelta(days=trial_days)

        subscription = Subscription(
            user_id=request.user_id,
            plan_id=request.plan_id,
            status=SubscriptionStatus.active.value,
            start_date=start_date,
            end_date=end_date,
        )
        created_subscription = await self.uow.subscriptions.create(subscription)

        # Явно делаем flush, чтобы подписка была сохранена в БД с ID
        await self.uow.session.flush()

        logger.info(f"Created trial subscription {created_subscription.id} with end_date {end_date}")

        # 7. Создаем платеж со статусом succeeded
        idempotency_key = str(uuid.uuid4())
        payment = Payment(
            user_id=request.user_id,
            subscription_id=created_subscription.id,
            yookassa_payment_id="trial_period",
            amount=plan.price,
            currency="RUB",
            status=PaymentStatus.succeeded.value,
            payment_method="manual",
            attempt_number=1,
            idempotency_key=idempotency_key,
        )
        created_payment = await self.uow.payments.create(payment)

        # Явно делаем flush, чтобы платеж был сохранен в БД с ID
        await self.uow.session.flush()

        logger.info(
            f"Created trial payment {created_payment.id} for subscription {created_subscription.id} "
            f"(status: succeeded, yookassa_payment_id: trial_period)"
        )

        return CreateTrialResponse(
            subscription_id=created_subscription.id,
            payment_id=created_payment.id,
            end_date=end_date,
            message=f"Промопериод активирован. Подписка активна до {end_date.strftime('%d.%m.%Y')}. Платеж будет создан автоматически при окончании периода.",
        )

    async def prepare_subscription_terms(self):
        pass

    async def cancellation_subscription(self):
        pass

    async def _cancel_pending_subscriptions_and_payments(self, user_id: int) -> None:
        """
        Отменить все pending_payment подписки и pending платежи пользователя.
        Отправляет запросы в Юкассу на отмену платежей (если есть yookassa_payment_id) и обновляет статусы в БД.

        Args:
            user_id: ID пользователя
        """
        from app.core.logger import logger
        from app.services.payment_service import PaymentService

        payment_service = PaymentService(self.uow)

        # Получаем все pending подписки пользователя
        pending_subscriptions = await self.uow.subscriptions.get_user_pending_subscriptions(user_id)

        # Получаем все pending платежи пользователя
        pending_payments = await self.uow.payments.get_user_pending_payments(user_id)

        # Собираем ID платежей, которые нужно отменить
        payments_to_cancel = set()

        # Обрабатываем pending подписки и их платежи
        for subscription in pending_subscriptions:
            try:
                # Получаем платежи для этой подписки
                subscription_payments = await self.uow.payments.get_subscription_payments(subscription.id)

                # Собираем pending платежи для этой подписки
                for payment in subscription_payments:
                    if payment.status == PaymentStatus.pending.value:
                        payments_to_cancel.add(payment.id)

                # Отменяем подписку
                subscription.status = SubscriptionStatus.cancelled.value
                subscription.end_date = datetime.now(timezone.utc)
                await self.uow.subscriptions.update(subscription)
                logger.info(f"Cancelled pending subscription {subscription.id}")
            except Exception as e:
                logger.error(f"Error cancelling pending subscription {subscription.id}: {str(e)}")

        # Добавляем оставшиеся pending платежи (которые не связаны с pending подписками)
        for payment in pending_payments:
            if payment.id not in payments_to_cancel:
                subscription = await self.uow.subscriptions.get_by_id(payment.subscription_id)
                # Отменяем только если подписка не pending (или не существует)
                if not subscription or subscription.status != SubscriptionStatus.pending_payment.value:
                    payments_to_cancel.add(payment.id)

        # Отменяем все собранные платежи
        for payment_id in payments_to_cancel:
            try:
                payment = await self.uow.payments.get_by_id(payment_id)
                if not payment:
                    continue

                # Отменяем платеж в Юкассе только если есть валидный yookassa_payment_id
                if payment.yookassa_payment_id and payment.yookassa_payment_id != "temp":
                    try:
                        await payment_service.cancel_payment(payment_id)
                        logger.info(f"Cancelled pending payment {payment_id} in Yookassa")
                    except Exception as e:
                        logger.warning(f"Could not cancel payment {payment_id} in Yookassa: {str(e)}")
                        # Даже если не удалось отменить в Юкассе, обновляем статус в БД

                # Обновляем статус платежа на cancelled в БД
                payment.status = PaymentStatus.cancelled.value
                await self.uow.payments.update(payment)
                logger.info(f"Marked payment {payment_id} as cancelled in DB")
            except Exception as e:
                logger.error(f"Error cancelling payment {payment_id}: {str(e)}")
