"""
Subscription service - бизнес-логика для работы с подписками
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.enums import PaymentStatus, SubscriptionStatus
from app.core.logger import logger
from app.models import Subscription
from app.schemas.subscription import (
    SubscriptionCreateRequestSchema,
    SubscriptionDetailResponse,
    SubscriptionPlanResponse,
    SubscriptionResponse,
    SubscriptionSchema,
    UserSubscriptionInfo,
)
from app.services.base_service import BaseService


class SubscriptionService(BaseService):
    """Сервис для управления подписками"""

    async def create_new_subscription(
        self, subscription_create_request_schema: SubscriptionCreateRequestSchema
    ) -> SubscriptionResponse:
        """
        Создать новую подписку

        Args:
            subscription_create_request_schema: Данные для создания подписки

        Returns:
            SubscriptionResponse: Созданная подписка
        """
        # Проверяем, что пользователь существует
        await self.uow.users.get_by_id_or_raise(subscription_create_request_schema.user_id)

        # Получаем план подписки
        plan = await self.uow.subscription_plans.get_by_id_or_raise(subscription_create_request_schema.plan_id)

        # Определяем даты
        start_date = subscription_create_request_schema.start_date or datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=plan.duration_days)

        # Создаем подписку
        subscription = Subscription(
            user_id=subscription_create_request_schema.user_id,
            plan_id=subscription_create_request_schema.plan_id,
            start_date=start_date,
            end_date=end_date,
            status=(
                subscription_create_request_schema.status.value
                if subscription_create_request_schema.status
                else SubscriptionStatus.pending_payment.value
            ),
        )

        created = await self.uow.subscriptions.create(subscription)
        return SubscriptionResponse.model_validate(created)

    async def get_all_user_subscriptions(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[SubscriptionSchema]:
        """
        Получить все подписки пользователя

        Args:
            user_id: ID пользователя
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            List[SubscriptionSchema]: Список подписок
        """
        await self.uow.users.get_by_id_or_raise(user_id)
        subscriptions = await self.uow.subscriptions.get_all_user_subscriptions(user_id=user_id, skip=skip, limit=limit)
        return [SubscriptionSchema.model_validate(sub) for sub in subscriptions]

    async def get_active_user_subscription(self, user_id: int) -> Optional[SubscriptionSchema]:
        """
        Получить активную подписку пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Optional[SubscriptionSchema]: Активная подписка или None
        """
        await self.uow.users.get_by_id_or_raise(user_id)
        subscription = await self.uow.subscriptions.get_active_subscription(user_id)

        if not subscription:
            return None

        return SubscriptionSchema.model_validate(subscription)

    async def get_subscription_by_id(self, subscription_id: int) -> Optional[SubscriptionSchema]:
        """
        Получить подписку по ID

        Args:
            subscription_id: ID подписки

        Returns:
            Optional[SubscriptionSchema]: Подписка или None
        """
        subscription = await self.uow.subscriptions.get_subscription_by_id(subscription_id)

        if not subscription:
            return None

        return SubscriptionSchema.model_validate(subscription)

    async def cancel_subscription(self, subscription_id: int, with_refund: bool = False) -> SubscriptionResponse:
        """
        Отменить подписку

        Два сценария отмены:
        1. with_refund=False (по умолчанию):
           - Статус: cancelled
           - end_date НЕ изменяется - подписка активна до конца периода
           - Возврат НЕ выполняется
           - Пользователь сохраняет доступ до end_date

        2. with_refund=True:
           - Статус: cancelled
           - end_date устанавливается в текущую дату
           - Выполняется возврат за неиспользованную часть (синхронно)
           - Доступ прекращается сразу

        Важно: cancelled_waiting используется только для автоплатежей,
        при отмене пользователем всегда ставится cancelled.

        Args:
            subscription_id: ID подписки
            with_refund: Выполнить возврат средств (отменить сразу)

        Returns:
            SubscriptionResponse: Отмененная подписка

        Raises:
            ValueError: Если подписка уже отменена
            RuntimeError: Если не удалось создать возврат (только при with_refund=True)
        """
        subscription = await self.uow.subscriptions.get_subscription_by_id_or_raise(subscription_id)

        # Проверяем, можно ли отменить (не отменена ли уже)
        # cancelled_waiting тоже считается отмененной (может быть от автоплатежей)
        if subscription.status in [
            SubscriptionStatus.cancelled.value,
            SubscriptionStatus.cancelled_waiting.value,
        ]:
            raise ValueError(f"Подписка {subscription_id} уже отменена (статус: {subscription.status})")

        if with_refund:
            # Сценарий 2: Отмена с возвратом
            # Сначала обрабатываем возвраты (используя оригинальный end_date для расчета)
            # Затем устанавливаем end_date в текущую дату
            logger.info(f"Processing refund for subscription {subscription_id} cancellation")
            try:
                await self._process_refunds_for_cancellation(subscription)
                logger.info(f"Refund processed successfully for subscription {subscription_id}")
            except ValueError as e:
                # ValueError означает, что возврат уже создан или платеж не подходит для возврата
                # Это не критическая ошибка, продолжаем отмену
                logger.warning(
                    f"Refund validation error for subscription {subscription_id}: {str(e)}. "
                    "Subscription cancellation continues."
                )
            except Exception as e:
                # Другие ошибки (например, YooKassa API недоступен) - критическая ошибка
                logger.error(
                    f"Error processing refunds for subscription {subscription_id}: {str(e)}. "
                    "Subscription cancellation continues, but refund was not created.",
                    exc_info=True,
                )
                # Пробрасываем ошибку, чтобы пользователь знал о проблеме
                raise RuntimeError(
                    f"Не удалось создать возврат средств при отмене подписки: {str(e)}. "
                    "Подписка отменена, но возврат средств не выполнен. Обратитесь в поддержку."
                ) from e

            # После расчета возврата устанавливаем статус и end_date
            subscription.status = SubscriptionStatus.cancelled.value
            subscription.end_date = datetime.now(timezone.utc)

            logger.info(
                f"Subscription {subscription_id} cancelled with refund (status: cancelled, end_date set to now)"
            )
        else:
            # Сценарий 1: Отмена без возврата
            # Подписка активна до end_date, возврат не делаем
            # Ставим cancelled (не cancelled_waiting, т.к. это только для автоплатежей)
            subscription.status = SubscriptionStatus.cancelled.value
            # end_date НЕ изменяем - подписка активна до end_date

            logger.info(
                f"Subscription {subscription_id} cancelled without refund "
                f"(status: cancelled, end_date remains: {subscription.end_date})"
            )

        updated = await self.uow.subscriptions.update(subscription)

        # Очищаем сохраненный платежный метод пользователя
        # Это предотвращает автоплатежи для отмененной подписки
        try:
            await self.uow.users.clear_saved_payment_method(subscription.user_id)
            logger.info(
                f"Cleared saved_payment_method_id for user {subscription.user_id} "
                f"after cancelling subscription {subscription_id}"
            )
        except Exception as e:
            logger.error(
                f"Error clearing saved_payment_method_id for user {subscription.user_id} "
                f"after cancelling subscription {subscription_id}: {str(e)}"
            )
            # Не прерываем выполнение - отмена подписки важнее

        # Обновляем объект из БД, чтобы загрузить все атрибуты (включая updated_at)
        await self.uow.session.refresh(updated)

        return SubscriptionResponse.model_validate(updated)

    async def _process_refunds_for_cancellation(self, subscription: Subscription) -> None:
        """
        Обработать возвраты при отмене подписки (синхронно, сразу при запросе).

        Политика возврата:
        - Полный возврат последнего успешного платежа, если отмена в течение 14 дней с момента платежа
        - Частичный возврат (пропорционально неиспользованному периоду), если отмена после 14 дней
        - Триал-платежи не возвращаются

        Args:
            subscription: Подписка для обработки возвратов

        Raises:
            ValueError: Если нет платежей для возврата, только триал-платежи, или возврат уже создан
            Exception: При ошибках создания возврата (например, YooKassa API недоступен)
        """
        logger.info(f"[REFUND] Starting refund processing for subscription {subscription.id}")

        from app.services.payment_service import PaymentService

        payment_service = PaymentService(self.uow)

        # Получаем все успешные платежи для подписки
        payments = await self.uow.payments.get_subscription_payments(subscription.id)
        logger.info(f"[REFUND] Found {len(payments)} total payments for subscription {subscription.id}")

        succeeded_payments = [p for p in payments if p.status == PaymentStatus.succeeded.value]
        logger.info(f"[REFUND] Found {len(succeeded_payments)} succeeded payments for subscription {subscription.id}")

        if not succeeded_payments:
            error_msg = f"No succeeded payments found for subscription {subscription.id}, no refund needed"
            logger.warning(f"[REFUND] {error_msg}")
            raise ValueError(error_msg)

        # Берем последний успешный платеж (не триал)
        last_payment = None
        for payment in sorted(succeeded_payments, key=lambda p: p.created_at, reverse=True):
            if payment.yookassa_payment_id != "trial_period":
                last_payment = payment
                break

        if not last_payment:
            error_msg = f"Only trial payments found for subscription {subscription.id}, no refund needed"
            logger.warning(f"[REFUND] {error_msg}")
            raise ValueError(error_msg)

        logger.info(
            f"[REFUND] Processing refund for payment {last_payment.id} "
            f"(amount: {last_payment.amount} RUB, yookassa_payment_id: {last_payment.yookassa_payment_id})"
        )

        # Проверяем, не был ли уже возврат для этого платежа
        existing_refund = await self.uow.refunds.get_by_payment_id(last_payment.id)
        if existing_refund:
            error_msg = f"Refund already exists for payment {last_payment.id} (refund_id={existing_refund.id})"
            logger.warning(f"[REFUND] {error_msg}")
            raise ValueError(error_msg)

        # Вычисляем сумму возврата
        refund_amount = await payment_service.calculate_refund_amount(last_payment, subscription)
        logger.info(
            f"[REFUND] Calculated refund amount: {refund_amount} RUB for payment {last_payment.id} "
            f"(subscription {subscription.id})"
        )

        if refund_amount <= 0:
            error_msg = f"Refund amount is {refund_amount} for payment {last_payment.id}, cannot create refund"
            logger.warning(f"[REFUND] {error_msg}")
            raise ValueError(error_msg)

        # Создаем возврат синхронно (сразу при запросе)
        logger.info(f"[REFUND] Creating refund for payment {last_payment.id}, amount: {refund_amount} RUB")
        refund = await payment_service.create_refund(
            payment_id=last_payment.id,
            amount=refund_amount,
            reason="Отмена подписки",
        )
        logger.info(
            f"[REFUND] Successfully created refund {refund.id} for subscription {subscription.id}: "
            f"payment_id={last_payment.id}, amount={refund_amount} RUB, "
            f"yookassa_refund_id={refund.yookassa_refund_id}, status={refund.status}"
        )

    async def get_user_subscription_info(self, user_id: int) -> UserSubscriptionInfo:
        """
        Получить полную информацию о подписках пользователя

        Args:
            user_id: ID пользователя

        Returns:
            UserSubscriptionInfo: Информация о подписках
        """
        await self.uow.users.get_by_id_or_raise(user_id)

        # Получаем активную подписку
        active_subscription = await self.uow.subscriptions.get_active_subscription(user_id)

        # Получаем все подписки
        all_subscriptions = await self.uow.subscriptions.get_all_user_subscriptions(user_id)

        # Формируем ответ
        active_subscription_detail = None
        if active_subscription:
            plan = await self.uow.subscription_plans.get_by_id_or_raise(active_subscription.plan_id)
            active_subscription_detail = SubscriptionDetailResponse(
                id=active_subscription.id,
                user_id=active_subscription.user_id,
                plan_id=active_subscription.plan_id,
                status=active_subscription.status,
                start_date=active_subscription.start_date,
                end_date=active_subscription.end_date,
                created_at=active_subscription.created_at,
                updated_at=active_subscription.updated_at,
                plan=SubscriptionPlanResponse.model_validate(plan),
            )

        subscription_history = [SubscriptionResponse.model_validate(sub) for sub in all_subscriptions]

        return UserSubscriptionInfo(
            active_subscription=active_subscription_detail,
            subscription_history=subscription_history,
        )

    async def get_all_subscriptions(self, skip: int = 0, limit: int = 100) -> list[SubscriptionResponse]:
        """
        Получить все подписки в системе

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            List[SubscriptionResponse]: Список подписок
        """
        subscriptions = await self.uow.subscriptions.get_all(skip=skip, limit=limit)
        return [SubscriptionResponse.model_validate(sub) for sub in subscriptions]
